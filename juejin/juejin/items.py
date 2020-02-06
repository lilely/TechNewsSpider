# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class JuejinItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class Author(scrapy.Item):
    ID = scrapy.Field()
    role = scrapy.Field()
    avatarHd = scrapy.Field()
    avatarLarge = scrapy.Field()
    username = scrapy.Field()

    def toDic(self):
        dic = {
            'ID': self['ID'],
            'role': self['role'],
            'avatarHd': self['avatarHd'],
            'avatarLarge': self['avatarLarge'],
            'username': self['username']
        }
        return dic

class FeedItem(scrapy.Item):
    feedID = scrapy.Field()
    tagName = scrapy.Field()
    original = scrapy.Field()
    originalUrl = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    # Author field
    user = scrapy.Field() 
    createdAt = scrapy.Field()
    updatedAt = scrapy.Field()

    @classmethod
    def formatFeedItem(cls,dic,tagName):
        feedItem = cls()
        feedItem['feedID'] = dic['id']
        feedItem['tagName'] = tagName
        feedItem['original'] = dic['original']
        feedItem['originalUrl'] = dic['originalUrl']
        feedItem['title'] = dic['title']
        feedItem['createdAt'] = dic['createdAt']
        feedItem['updatedAt'] = dic['updatedAt']
        feedItem['content'] = dic.get('content',None)
        author = Author()
        author['ID'] = dic['user']['id']
        author['role'] = dic['user']['role']
        author['username'] = dic['user']['username']
        author['avatarHd'] = dic['user'].get('avatarHd',None)
        author['avatarLarge'] = dic['user'].get('avatarLarge',None)
        feedItem['user'] = author
        return feedItem

    def toDic(self):
        dic = {
            'feedID': self['feedID'],
            'tagName': self['tagName'],
            'original': self['original'],
            'originalUrl': self['originalUrl'],
            'title': self['title'],
            'author': self['author'].toDic(),
            'createdAt': self['createdAt'],
            'updatedAt': self['updatedAt'],
            'content': self['content'],
        }
        return dic

class FeedDetail(scrapy.Item):
    feedID = scrapy.Field()
    title = scrapy.Field()
    author = scrapy.Field()
    tagName = scrapy.Field()
    contentItems = scrapy.Field()

    @classmethod
    def formatFeedDetail(cls,dic):
        feedDetail = FeedDetail()
        author = Author()
        author['ID'] = dic['author']['id']
        author['role'] = dic['author']['role']
        author['username'] = dic['author']['username']
        author['avatarHd'] = dic['author'].get('avatarHd',None)
        author['avatarLarge'] = dic['author'].get('avatarLarge',None)
        feedDetail['author'] = author
        feedDetail['feedID'] = dic['id']
        feedDetail['title'] = dic['title']
        feedDetail['tagName'] = dic['tagName']
        feedDetail['contentItems'] = dic['contentItems']

        return feedDetail

class FeedContentItem(scrapy.Item):
    ID = scrapy.Field()
    contentType = scrapy.Field()
    imageUrl = scrapy.Field()
    text = scrapy.Field()
    
    def toDic(self):
        dic = {
            "contentType" : self['contentType'],
            "imageUrl" : self.get('imageUrl'),
            "text" : self.get('text')
        }
        dic.setdefault('imageUrl',"")
        dic.setdefault('text',"")
        return dic


