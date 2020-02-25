# -*- coding: utf-8 -*-
import scrapy
import urllib
import urllib2
import json
import numpy
import sys
from juejin.items import FeedItem
from juejin.items import FeedDetail
from juejin.items import FeedContentItem
from juejin.items import Author
from requests_toolbelt import MultipartEncoder

class JuejinspiderSpider(scrapy.Spider):
    name = 'juejinSpider'
    allowed_domains = ['juejin.im']
    start_urls = ['https://juejin.im/']
    tag_dic = {-1 : "推荐",
                0  : "后端",
                1  : "前端",
                2  : "Android",
                3  : "iOS",
                4  : "人工智能",
                5  : "开发工具",
                6  : "代码人生"}

    def parse(self, response):
        print "XXXXXXXXXXXXXXX 0"
        print "XXXXXXXXXXXXXXX 1"
        extension_ids = ["21207e9ddb1de777adeaca7a2fb38030",
                         "653b587c5c7c8a00ddf67fc66f989d42"]

        category_ids = ["5562b419e4b00c57d9b94ae2", #后端
                    "5562b415e4b00c57d9b94ac8", #前端
                    "5562b410e4b00c57d9b94a92", #Android
                    "5562b405e4b00c57d9b94a41", #iOS
                    "57be7c18128fe1005fa902de", #人工智能
                    "5562b422e4b00c57d9b94b53", #开发工具
                    "5c9c7cca1b117f3c60fee548"] #代码人生

        numpy_categorys = numpy.array(category_ids)
        for index,category_id in numpy.ndenumerate(numpy_categorys):
            yield self.startRequestTab(categoryid = category_id,extensionid = extension_ids[1],tagID = index[0])
    
        yield self.startRequestTab(categoryid = "",extensionid = extension_ids[0], tagID = -1)
        
    def startRequestTab(self,categoryid,extensionid,tagID):
        print('tagID is {}'.format(tagID))
        url = 'https://web-api.juejin.im/query'
        headers = {
            'Host':	'web-api.juejin.im',
            'Accept': '*/*',
            'X-Legacy-Device-Id': '',
            'X-Agent': 'Juejin/Web',
            'Accept-Language': 'zh-cn',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type':	'application/json',
            'Origin': 'https://juejin.im',
            'Referer': 'https://juejin.im/welcome/recommended',
            'X-Legacy-Uid': '',
            'X-Legacy-Token': ''
        }
        data = self.formatTabPostBody(categoryid,extensionid)       
        meta = {'tagID' : tagID,
            'tagName' : self.tag_dic[tagID]}
        return scrapy.FormRequest(
            url = url,
            method = 'POST', 
            headers = headers, 
            cookies = '',
            body = json.dumps(data), 
            meta = meta,
            callback = self.parse_feed,
        )

    def formatTabPostBody(self,categoryid,extensionid):
        if len(categoryid) > 0:
            data = {
	            "operationName": "",
	            "query": "",
	            "variables": {
                    "category": categoryid,
		            "first": 20,
		            "after": "",
		            "order": "POPULAR"
	            },
	            "extensions": {
		            "query": {
			            "id": extensionid
		            }
	            }
            }
        else:
            data = {
	            "operationName": "",
	            "query": "",
	            "variables": {
		            "first": 20,
		            "after": "",
		            "order": "POPULAR"
	            },
	            "extensions": {
		            "query": {
			            "id": extensionid
		            }
	            }
            }
        return data

    def parse_feed(self, response):
        res_data = json.loads(response.body.decode('utf-8'))
        articleFeed = res_data['data']
        items = articleFeed['articleFeed']['items']
        edges = items['edges']
        for edge in edges:
            node = edge['node']
            if node['user']!= None:
                author = Author.formatAuthorItem(node['user'])
                yield author
            print "*****Node is :" + json.dumps(node)
            feedItem = FeedItem.formatFeedItem(node,response.meta['tagName'])
            print feedItem['feedID']
            yield feedItem 
        
        for edge in edges:
            node = edge['node']
            meta = response.meta
            meta['isDetail'] = True
            meta['author'] = node['user']
            meta['id'] = node['id']
            yield scrapy.FormRequest(
                            url = node['originalUrl'],
                            method = 'GET', 
                            meta = meta,
                            callback = self.parse_detail,
                        )


    def parse_detail(self, response):
        reload(sys)
        sys.setdefaultencoding('utf8')  
        dic = response.meta
        dic['title'] = response.xpath(u"//body/div[@id='juejin']/div[@class='view-container']//article//h1[@class='article-title']/text()").extract()
        text_list = response.xpath(u"//body/div[@id='juejin']/div[@class='view-container']//article//p/text()").extract()
        contentItems = []
        for text in text_list:
            feedContentItem = FeedContentItem()
            feedContentItem['contentType'] = '文本'
            feedContentItem['text'] = text
            contentItems.append(feedContentItem)
            # print("text in item is :{}".format(text))
        dic['contentItems'] = contentItems
        # print(dic)
        feedDetail = FeedDetail.formatFeedDetail(dic)

        yield feedDetail
        