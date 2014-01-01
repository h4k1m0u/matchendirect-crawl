#!/usr/bin/python
# -*- coding: utf-8 -*-
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import Selector
from score.items import ScoreItem
from sunburnt import SolrInterface


class ScoreSpider(CrawlSpider):
    name = 'score'
    allowed_domains = ['matchendirect.fr']
    start_urls = ['http://www.matchendirect.fr/hier/']
    rules = [Rule(SgmlLinkExtractor(allow=(r'/live-score/[a-z0-9\-]+\.html$', r'/foot-score/[a-z0-9\-]+\.html$')), 'parse_score')]

    # init solr instance
    def __init__(self, *args, **kwargs):
        super(ScoreSpider, self).__init__(*args, **kwargs)
        self.si = SolrInterface('http://localhost:8080/solr')

    # called on start urls
    # get host, visitor, scores
    def parse_start_url(self, response):
        sel = Selector(response)
        leagues = sel.xpath('//h3')
        docs = []
        for league in leagues:
            table = league.xpath('following-sibling::table[@class="tableau"][1]')
            rows = table.xpath('tr')
            for row in rows:
                # if match has has started & is finished
                scoring = row.xpath('td[@class="lm4"]/a[not(span)]/text()').extract()
                isPlaying = row.xpath('td[@class="lm2_1"]').extract()
                if scoring and not isPlaying:
                    score = ScoreItem()
                    score['id'] = 'http://www.matchendirect.fr' + row.xpath('td[@class="lm4"]/a/@href').extract().pop()
                    score['host'] = row.xpath('td[@class="lm3"]/a/text()').extract().pop()
                    score['visitor'] = row.xpath('td[@class="lm5"]/a/text()').extract().pop()

                    scoringArr = scoring.pop().split(' - ')
                    score['scorehost'] = int(scoringArr[0])
                    score['scorevisitor'] = int(scoringArr[1])
                    if score['scorehost'] > score['scorevisitor']:
                        score['winner'] = score['host']
                    elif score['scorehost'] < score['scorevisitor']:
                        score['winner'] = score['visitor']
                    
                    leagueArr = league.xpath('a[1]/text()').extract().pop().split(' : ')
                    score['country'] = leagueArr[0]
                    score['league'] = leagueArr[1]
                
                    docs.append(dict(score))

        # index crawled games
        self.si.add(docs)
        self.si.commit()

    # called on followed urls
    # get game details (goal scorer & time)
    def parse_score(self, response):
        sel = Selector(response)
        # if match has started & is finished
        scorehost = sel.xpath('//div[@id="match_score"]/div[@class="col2"]/text()').extract().pop().strip()
        scorevisitor = sel.xpath('//div[@id="match_score"]/div[@class="col3"]/text()').extract().pop().strip()
        isPlaying = sel.xpath('//div[@id="match_entete_2"]/img').extract()
        
        if scorehost and scorevisitor and not isPlaying:
            score = ScoreItem()

            # get already indexed data 
            solr_doc = self.si.query(id=response.url).execute()
            if list(solr_doc):
                doc = solr_doc[0]
            else:
                doc = {}
                score['id'] = response.url

            # get goals
            table = sel.xpath('//table[@class="tableau match_evenement"]')
            rows = table.xpath('tr')
            score['goalscorershost'], score['goalscorersvisitor'], score['goaltimeshost'], score['goaltimesvisitor'] = ([], [], [], [])
            score['penaltytimeshost'], score['penaltytimesvisitor'], score['ogtimeshost'], score['ogtimesvisitor'] = ([], [], [], [])
            for row in rows:
                tdgoalhost = row.xpath('td[@class="c1" and span[@class="ico_evenement1"]]')
                tdpenaltyhost = row.xpath('td[@class="c1" and span[@class="ico_evenement2"]]')
                tdowngoalhost = row.xpath('td[@class="c1" and span[@class="ico_evenement7"]]')
                tdgoalvisitor = row.xpath('td[@class="c3" and span[@class="ico_evenement1"]]')
                tdpenaltyvisitor = row.xpath('td[@class="c3" and span[@class="ico_evenement2"]]')
                tdowngoalvisitor = row.xpath('td[@class="c3" and span[@class="ico_evenement7"]]')
                tdgoalhost = tdgoalhost or tdpenaltyhost or tdowngoalhost
                tdgoalvisitor = tdgoalvisitor or tdpenaltyvisitor or tdowngoalvisitor
                if tdgoalhost:
                    time = tdgoalhost.xpath('following-sibling::td[@class="c2"][1]/text()').extract().pop().rstrip("'")
                    if tdpenaltyhost:
                        score['penaltytimeshost'].append(time)
                    elif tdowngoalhost:
                        score['ogtimeshost'].append(time)
                    score['goaltimeshost'].append(time)
                    score['goalscorershost'].append(tdgoalhost.xpath('a/text()').extract().pop())
                elif tdgoalvisitor:
                    time = tdgoalvisitor.xpath('preceding-sibling::td[@class="c2"][1]/text()').extract().pop().rstrip("'")
                    if tdpenaltyvisitor:
                        score['penaltytimesvisitor'].append(time)
                    elif tdowngoalvisitor:
                        score['ogtimesvisitor'].append(time)
                    score['goaltimesvisitor'].append(time)
                    score['goalscorersvisitor'].append(tdgoalvisitor.xpath('a/text()').extract().pop())
                
            # get time, refree & stadium
            matchinfos = sel.xpath('//table[@id="match_entete_1"]/tr/td[@class="info"]/text()').extract()
            matchinfos.pop()
            matchinfos = [x.lstrip('\n\t\r') for x in matchinfos]
            if u'Arbitre : - ' in matchinfos:
                matchinfos.remove(u'Arbitre : - ')
            date = format_date(matchinfos[0])
            time = matchinfos[1].split(' ')[-1].replace('h', ':') + ':00'
            score['date'] = "%sT%sZ" % (date, time)
            if len(matchinfos) >= 3:
                score['stadium'] = matchinfos[2]
                if len(matchinfos) == 4:
                    score['referee'] = matchinfos[3].split(' : ')[1]
                
            # index all datas
            doc = dict(doc.items() + dict(score).items())
            self.si.add(doc)
            self.si.commit()


def format_date(date):
    months = {
        u'janvier': '1',
        u'février': '2',
        u'mars': '3',
        u'avril': '4',
        u'mai': '5',
        u'juin': '6',
        u'juillet': '7',
        u'août': '8',
        u'septembre': '9',
        u'octobre': '10',
        u'novembre': '11',
        u'décembre': '12'
    }
    date_list = date.split(' ')[1:]
    date_list.reverse()
    date_list[1] = months[date_list[1]]
    formatted_date = '-'.join(date_list)

    return formatted_date
