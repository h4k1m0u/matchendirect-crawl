#!/usr/bin/python
from scrapy.item import Item, Field


class ScoreItem(Item):
    id = Field()
    date = Field()
    time = Field()
    host = Field()
    visitor = Field()
    winner = Field()
    scorehost = Field()
    scorevisitor = Field()
    league = Field()
    country = Field()
    goalscorershost = Field()
    goaltimeshost = Field()
    goalscorersvisitor = Field()
    goaltimesvisitor = Field()
    referee = Field()
    stadium = Field()
