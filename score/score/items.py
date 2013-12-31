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
    penaltytimeshost = Field()
    ogtimeshost = Field()
    goalscorersvisitor = Field()
    goaltimesvisitor = Field()
    penaltytimesvisitor = Field()
    ogtimesvisitor = Field()
    referee = Field()
    stadium = Field()
