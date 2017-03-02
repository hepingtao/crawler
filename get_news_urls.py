# -*- coding: utf-8 -*-

import json
import requests
import re
import time
import multiprocessing

__author__ = u'马浩翔'


class UrlProcess(multiprocessing.Process):
    """
    获取URL进程类
    """
    def __init__(self, media_queue, public_news_set):
        multiprocessing.Process.__init__(self)
        self.media_queue = media_queue  # 媒体id队列
        self.public_news_set = public_news_set  # 新闻url集合
        self.basic_url = 'http://www.toutiao.com/pgc/ma/?media_id= &page_type=1&max_behot_time= &count=10&version=2&platform=pc&as=479BB4B7254C150&cp=7E0AC8874BB0985'

    # 重写run方法,取出media id,构造url
    def run(self):
        while not self.media_queue.empty():
            media_id = self.media_queue.get(block=False)
            current_time = int(time.time())
            media_url = re.sub('media_id=.*?&','media_id=%s&'%media_id,self.basic_url)
            media_url = re.sub('max_behot_time=.*?&','max_behot_time=%d&' % current_time, media_url)
            self.get_news_urls(media_url)

    # 访问媒体页面,获取返回的数据中的新闻url列表
    def get_news_urls(self, media_url):
        news_urls_list = []
        page = 10   # 向后抓取的页面数
        for i in range(page):
            response = requests.get(media_url)
            response_json = json.loads(response.content)
            news_data = response_json['data']
            news_urls = [news['source_url'] for news in news_data]
            news_titles = [news['title'] for news in news_data]
            news_urls_list.extend(news_urls)
            max_behot_time = response_json['next']['max_behot_time']    # 获取max_behot_time,用来构造新的url
            if max_behot_time == '0':
                break
            media_url = re.sub('max_behot_time=([\d]+?)&','max_behot_time=%s&'%max_behot_time, media_url)
            print media_url
            print "\n".join(news_titles)
            time.sleep(1)   # 休眠,防止反爬虫机制

        for each in news_urls_list: # 将新闻url插入公共的新闻url集合中
            self.public_news_set.append(each)

if __name__ == '__main__':
    pass
