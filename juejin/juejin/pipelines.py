# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import psycopg2 #PostgreSQL engine
import json
import requests
import re
from juejin.items import FeedItem
from juejin.items import FeedDetail
from juejin.items import FeedContentItem
from juejin.items import Author

class JuejinPipeline(object):
    def process_item(self, item, spider):
        return item

class VaporServerPipeline(object):
    def __init__(self,host,port):
        self.host = host
        self.port = port

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            host = crawler.settings.get('VAPOR_SERVER_HOST'),
            port = crawler.settings.get('VAPOR_SERVER_PORT')
        )
    
    def open_spider(self,spider):
        pass

    def close_spider(self,spider):
        pass

    def process_item(self,item,spider):
        if isinstance(item,Author):
            self.process_author(item,spider)
            print('Author item processed')
        return item
    
    def process_author(self,item,spider):
        url = 'http://'+self.host+':'+self.port+'/author'
        print("url is {}".format(url))
        data = item.toDic()
        # data = {"role":"guest","avatar_hd":"hd","avatar_large":"large","username":"Jack"}
        print("data is {}".format(data))
        requests.post(url=url,data=data)
        # print(res.text)

class PostgresPipeline(object):
    def __init__(self,postgres_url,postgres_port,postgres_db,postgres_password):
        self.postgres_url = postgres_url
        self.postgres_port = postgres_port
        self.postgres_db = postgres_db
        self.postgres_password = postgres_password
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            postgres_url = crawler.settings.get('POSTGRES_URL'),
            postgres_port = crawler.settings.get('POSTGRES_PORT'),
            postgres_db = crawler.settings.get('POSTGRES_DATABASE'),
            postgres_password = crawler.settings.get('POSTGRES_PASSWORD')
        )

    def open_spider(self,spider):
        print('in open spider')
        print('self.postgres_db is {}'.format(self.postgres_db))
        print('self.postgres_url is {}'.format(self.postgres_url))
        print('self.postgres_port is {}'.format(self.postgres_port))
        print('self.postgres_password is {}'.format(self.postgres_password))
        conn = psycopg2.connect(
                host = self.postgres_url,
                port = self.postgres_port,
                user = self.postgres_db,
                password = self.postgres_password,
                database = "postgres"
                )
        self.connection = conn
        
    def close_spider(self,spider):
        print('in close spider')
        if self.connection != None:
            self.connection.close()

    def process_item(self,item,spider):
        if isinstance(item,FeedItem):
            self.process_feedItem(item,spider)
            print('Feed Simple item processed')
        if isinstance(item,FeedDetail):
            self.process_feedDetail(item,spider)
            print('Feed Detail item processed')
        if isinstance(item,Author):
            self.process_author(item,spider)
            print('Author item processed')
        return item

    def process_feedDetail(self,item,spider):
        insert_sql = """INSERT INTO public."FeedDetail"(feed_id,title,author,tag_name,content_items) VALUES(%s,%s,%s,%s,%s) RETURNING id;"""
        query_sql = """SELECT id FROM public."FeedDetail" 
                        WHERE feed_id = %s"""
        update_sql = """UPDATE public."FeedDetail" 
                        SET title = %s ,tag_name =%s ,author = %s ,content_items = %s
                        WHERE feed_id = %s;"""
        try:
            print('feed ID in detail is {}'.format(item['feedID']))
            cur = self.connection.cursor()
            self.connection.rollback()
            cur.execute(query_sql,(item['feedID'],))
            if cur.rowcount > 0:
                row = cur.fetchone()[0]
            else:
                row = 0
            print('row is {}'.format(row))
            if row < 1:
                itemsArray = []
                for contentItem in item['contentItems']:
                    itemsArray.append(contentItem.toDic())
                content_items_dic = {
                    'content_items' : itemsArray
                }
                self.connection.rollback()
                cur.execute(insert_sql,
                            (item['feedID'],
                            item['title'],
                            json.dumps(item['author'].toDic()),
                            item['tagName'],
                            json.dumps(content_items_dic)
                            )
                            )
            else:
                self.connection.rollback()
                itemsArray = []
                for item in item['contentItems']:
                    itemsArray.append(item.toDic())
                cur.execute(update_sql,
                            (item['title'],
                            item['tagName'],
                            json.dumps(item['author'].toDic()),
                            json.dumps(itemsArray),
                            item['feedID']))
            self.connection.commit()
        except Exception as e:
            print('FeedDetail insert or update failed with exception:{}'.format(e))
        finally:
            if cur != None:
                cur.close()
        return item

    def process_feedItem(self,item,spider):
        insert_sql = """INSERT INTO public."FeedSimple"(feed_id,"from","tag_name",original,original_url,title,author_name,created_at,updated_at,content) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id;"""
        query_sql = """SELECT id FROM public."FeedSimple" 
                        WHERE feed_id=%s"""
        update_sql = """UPDATE public."FeedSimple" 
                        SET "from" = %s,"tag_name" =%s, original = %s, original_url = %s, title = %s, author_name = %s, created_at = %s, updated_at = %s, content = %s
                        WHERE feed_id = %s;"""
        try:
            cur = self.connection.cursor()
            self.connection.rollback()
            cur.execute(query_sql,(item['feedID'],))
            if cur.rowcount > 0:
                row = cur.fetchone()[0]
            else:
                row = 0
            print('row is {}'.format(row))
            if row < 1:
                self.connection.rollback()
                cur.execute(insert_sql,
                            (item['feedID'],
                            'juejin',
                            item['tagName'],
                            item['original'],
                            item['originalUrl'],
                            item['title'],
                            item['user']['username'],
                            # json.dumps(item['user'].toDic()),
                            item['createdAt'],
                            item['updatedAt'],
                            item['content']))
            else:
                self.connection.rollback()
                cur.execute(update_sql,
                            ('juejin',
                            item['tagName'],
                            item['original'],
                            item['originalUrl'],
                            item['title'],
                            item['user']['username'],
                            # json.dumps(item['user'].toDic()),
                            item['createdAt'],
                            item['updatedAt'],
                            item['content'],
                            item['feedID']))
            self.connection.commit()
        except Exception as e:
            print('FeedSimple insert or update  insert failed with exception:{}'.format(e))
        finally:
            if cur != None:
                cur.close()
        return item

    def process_author(self,item,spider):
        insert_sql = """INSERT INTO public."Author"(role,avatar_hd,avatar_large,username) VALUES(%s,%s,%s,%s)"""
        query_sql = """SELECT id FROM public."Author" 
                        WHERE username=%s"""
        try:
            cur = self.connection.cursor()
            self.connection.rollback()
            cur.execute(query_sql,(item['username'],))
            if cur.rowcount > 0:
                row = cur.fetchone()[0]
            else:
                row = 0
            print('author row is {}'.format(row))
            print(item['role'])
            print(item['avatarHd'])
            print(item['avatarLarge'])
            print(item['username'])
            if row < 1:
                self.connection.rollback()
                # cur.execute(insert_sql,
                #             (item['role'],
                #             item['avatarHd'],
                #             item['avatarLarge'],
                #             item['username']))
                cur.execute(insert_sql,
                            ('guest',
                            '123',
                            '456',
                            '789'))
                print("has inserted")
        except Exception as e:
            print('Author insert or update  insert failed with exception:{}'.format(e))
        finally:
            if cur != None:
                cur.close()
        return item