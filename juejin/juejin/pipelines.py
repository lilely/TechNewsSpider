# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import psycopg2 #PostgreSQL engine
import json
from juejin.items import FeedItem
from juejin.items import FeedDetail
from juejin.items import FeedContentItem
from juejin.items import Author

class JuejinPipeline(object):
    def process_item(self, item, spider):
        return item

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
            print('OK lo')
        return item

    # feedItem['feedID'] = dic['id']
    #     feedItem['hot'] = dic['hot']
    #     feedItem['hotIndex'] = dic['hotIndex']
    #     feedItem['original'] = dic['original']
    #     feedItem['originalUrl'] = dic['originalUrl']
    #     feedItem['title'] = dic['title']
    #     feedItem['createdAt'] = dic['createdAt']
    #     feedItem['updatedAt'] = dic['updatedAt']
    #     author = Author()
    #     author['ID'] = dic['user']['id']
    #     author['role'] = dic['user']['role']
    #     author['username'] = dic['user']['username']
    #     author['avatarHd'] = dic['user'].get('avatarHd',None)
    #     author['avatarLarge'] = dic['user'].get('avatarLarge',None)
    #     feedItem['user'] = author

    def process_feedItem(self,item,spider):
        insert_sql = """INSERT INTO public."FeedSimple"(feed_id,"from","tag_name",original,original_url,title,author,created_at,updated_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id;"""
        query_sql = """SELECT id FROM public."FeedSimple" 
                        WHERE feed_id=%s"""
        update_sql = """UPDATE public."FeedSimple" 
                        SET "from" = %s,"tag_name" =%s, original = %s, original_url = %s, title = %s, author = %s, created_at = %s, updated_at = %s 
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
                            json.dumps(item['user'].toDic()),
                            item['createdAt'],
                            item['updatedAt']))
            else:
                self.connection.rollback()
                cur.execute(update_sql,
                            ('juejin',
                            item['tagName'],
                            item['original'],
                            item['originalUrl'],
                            item['title'],
                            json.dumps(item['user'].toDic()),
                            item['createdAt'],
                            item['updatedAt'],
                            item['feedID']))
            self.connection.commit()
        except Exception as e:
            print('postgres insert failed with exception:{}'.format(e))
        finally:
            if cur != None:
                cur.close()
        return item