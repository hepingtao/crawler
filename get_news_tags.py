# -*- coding: utf-8 -*-

import multiprocessing
import time
import requests
from bs4 import BeautifulSoup

__author__ = u'马浩翔'


class NewsProcess(multiprocessing.Process):
    """
    爬虫进程类,继承于进程类
    """
    def __init__(self, public_url_queue):
        multiprocessing.Process.__init__(self)
        self.headers = {
            'Referer': 'http://www.toutiao.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 \
                            (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36',
        }
        self.public_url_queue = public_url_queue    # 公共的新闻url队列

    # 重写run方法,当公共队列不为空时持续取出新闻url进行标签抓取
    def run(self):
        while not self.public_url_queue.empty():
            try:
                news_url = self.public_url_queue.get(block=False)    # 从公共url队列中取新闻url
                tags = self.get_news_tags(news_url)         # 提取页面中的标签
                print ",".join(tags)  # do something
                time.sleep(2)   # 休眠

            except Exception,msg:
                print msg
                pass

    # 抓取新闻页面的标签
    def get_news_tags(self, news_url):
        try:
            response = requests.get(url=news_url, headers=self.headers)
            soup = BeautifulSoup(response.content, "html.parser")
            news_title = soup.find(name='h1', class_='article-title')
            tags = soup.find_all(name='a', class_='label-link')
            tags = [tag.get_text() for tag in tags]
            print news_title.get_text()
            return tags

        except Exception,msg:
            print msg
            return None


if __name__ == '__main__':
    pass
