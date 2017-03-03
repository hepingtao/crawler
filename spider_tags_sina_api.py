# -*- coding: utf8 -*-
import json
import logging
import time

import requests

import spider_tags_2

# g_log_dir = "./"
# g_instance_id = 1
# g_mysql_conf = {'host': '192.168.31.49',
#                 'user': 'touchtv',
#                 'passwd': 'op@touchtv',
#                 'dbname': 'touchtv_dev',
#                 'port': 3306}

g_mysql_conf = spider_tags_2.g_mysql_conf

if __name__ == "__main__":
    # signal.signal(signal.SIGTERM, sighandler)
    # signal.signal(signal.SIGINT, sighandler)
    
    g_logger = logging.getLogger('tagsspider')
    # fileTimeHandler = TimedRotatingFileHandler(g_log_dir + './tagsspider.log', "MIDNIGHT", 1, 1000)
    # fileTimeHandler.suffix = "%Y%m%d"
    # g_logger.setLevel(logging.DEBUG)
    # formatter = logging.Formatter('%(asctime)s %(process)d [%(levelname)s] %(message)s')
    # fileTimeHandler.setFormatter(formatter)
    # g_logger.addHandler(fileTimeHandler)
    
    g_logger.info("spider tags start")
    
    # daemon()
    
    # try:
    #     g_spiderTags = spiderTags(g_mysql_conf)
    #     g_spiderTags.run(g_instance_id)
    # except Exception, e:
    #     g_logger.error(traceback.format_exc())

    mysql = spider_tags_2.mysqldb(g_mysql_conf)
    # g_spiderTags._mysql.conndb()

    # api_template_sohu = "http://apiv2.sohu.com/apiV2/re/tag/news?tagId=67040&pno={pno}&psize=100"
    api_template_sina_api = "http://api.roll.news.sina.com.cn/zt_list?channel=finance&cat_1=lc1&cat_2=lcgh&show_all=1&show_ext=1&tag=1&format=json&show_num=100&page={pno}"
    for p_no in range(1, 34):
        api_url = api_template_sina_api.format(pno=p_no)
        print "\nPage {pno}: ".format(pno=p_no) + api_url
        response = requests.get(api_url)
        response_json = json.loads(response.content)
        # print response_json
        news_data = response_json['result']['data']
        news_list = [(news['title'], news['url'], news['keywords'].split(",")) for news in news_data]
        for news_tuple in news_list:
            news_title = news_tuple[0]
            news_url = news_tuple[1]
            tag_list = news_tuple[2]
            news_tags = ", ".join(tag_list)
            print news_title
            print news_url
            print news_tags
            # break
            for tag_name in tag_list:
                # p_tag_pk, tag_name, root_tag_pk
                mysql.insertTag(13232, tag_name, 13054)

        time.sleep(1)  # 休眠,防止反爬虫机制
        # sys.exit(1)
        
    g_logger.info("spider tags exit")
