# -*- coding: utf-8 -*-

from get_news_urls import UrlProcess
from get_news_tags import NewsProcess
import multiprocessing
import sys
import re

__author__ = u'马浩翔'


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')

    # sys.exit(1)

    # 设置多进程参数
    process_num = 5
    manager = multiprocessing.Manager()
    media_queue = multiprocessing.Queue()   # 媒体id队列
    public_news_set = manager.list()        # 公共新闻url集合

    # 读取本地media id文件,将media id插入媒体id队列
    # media_id_file = open('medium.txt', 'r')
    # for line in media_id_file:
    #     media_id = re.findall('com/m(.+?)/', line)[0]
    #     media_queue.put(media_id)
    #     # print media_id
    # media_id_file.close()
    # print media_queue
    # sys.exit(1)

    media_queue.put(6493820122)

    # 启动多进程抓取新闻url,存储在public_news_set中,并插入public_url_queue
    process_pool = []
    for i in range(process_num):
        process = UrlProcess(media_queue, public_news_set)
        process.start()
        process_pool.append(process)    # 放入进程池
    for process in process_pool:
        process.join()  # 等待多进程任务结束

    print 'News Count:%d' % len(public_news_set)
    public_url_queue = manager.Queue()
    for each in public_news_set:
        public_url_queue.put(each)

    # 启动多进程抓取新闻标签
    process_pool = []
    for i in range(process_num):
        process = NewsProcess(public_url_queue)
        process.start()
        process_pool.append(process)
    for process in process_pool:
        process.join()

