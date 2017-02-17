# -*- encoding:utf-8 -*-

from threading import Thread
import Queue
import time as t
import requests
from bs4 import BeautifulSoup
import sys

public_queue = Queue.Queue()    # 公共url队列


class UrlThread(Thread):
    '''
    爬虫线程类,继承于标准库中的线程类
    '''
    def __init__(self):
        Thread.__init__(self)
        self.headers = {
        'Referer':'http://www.toutiao.com/',
        'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36',
        }

    # 重写run方法,当公共队列不为空时持续取出新闻url进行标签抓取
    def run(self):
        global public_queue
        while(public_queue.empty() == False):
            try:
                news_url = public_queue.get(block=False)    # 从公共url队列中取新闻url
                tags = self.get_news_tags(news_url)         # 提取页面中的标签
                t.sleep(2)

            except Exception,msg:
                print msg
                pass
            finally:
                public_queue.task_done()


    def get_news_tags(self, news_url):
        try:
            response = requests.get(url=news_url,headers=self.headers)
            soup = BeautifulSoup(response.content, "html.parser")
            tags = soup.find_all(name='a', class_='label-link')
            tags = [tag.get_text() for tag in tags]

            return tags

        except Exception, msg:

            print(msg)

            return None




if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')

    thread_num = 3  # 设置线程数
    thread_pool = []    # 设置线程池

    '''
        # 将多个新闻url插入公共队列
        for each in news_urls:
            public_queue.put(each)
    '''

    for i in range(thread_num):
        # 启动多线程
        thread_crawler = UrlThread()
        thread_crawler.start()
        thread_pool.append(thread_crawler)

    for thread_crawler in thread_pool:
        # 多线程放入线程池
        thread_crawler.join()

