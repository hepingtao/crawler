# -*- coding: utf8 -*-

import StringIO
import pycurl
import time

import sys

import re
from scrapy.selector import Selector
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait


def init_curl():
    c = pycurl.Curl()
    c.setopt(pycurl.COOKIEFILE, "cookie_file_name")
    c.setopt(pycurl.COOKIEJAR, "cookie_file_name")
    c.setopt(pycurl.FOLLOWLOCATION, 1)
    c.setopt(pycurl.MAXREDIRS, 5)
    return c


def get_html(c, page_url):
    head = ['Accept:*/*',
            'User-Agent:Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.11 (KHTML, like Gecko) \
             Chrome/23.0.1271.97 Safari/537.11']
    buf = StringIO.StringIO()
    c.setopt(pycurl.WRITEFUNCTION, buf.write)
    c.setopt(pycurl.URL, page_url)
    c.setopt(pycurl.HTTPHEADER, head)
    c.perform()
    page_html = buf.getvalue()
    buf.close()
    return page_html

if __name__ == '__main__':
    print '---------------start------------------'

    start_page_url = "http://roll.sports.sina.com.cn/s/channel.php?ch=02#col=181&spec=&type=&ch=02&k=&offset_page=0&offset_num=0&num=60&asc=&page=19"
    argc = len(sys.argv)
    # print argc
    # print sys.argv
    start_page_url = ""
    url_list_xpath = ""
    tag_list_xpath = ""
    try:
        start_page_url = sys.argv[1]
        url_list_xpath = sys.argv[2]
        tag_list_xpath = sys.argv[3]
    except IndexError:
        pass

    print start_page_url
    print url_list_xpath
    print tag_list_xpath

    if (start_page_url and re.search(r'^(-h)|(help)$', start_page_url, re.I | re.M)) or\
            (not (start_page_url and url_list_xpath and tag_list_xpath)):
        print 'Usage: ' + sys.argv[0] + ' <start page url> <url_list_xpath> <tag_list_xpath>'
        sys.exit(1)

    curl = init_curl()
    dr = webdriver.PhantomJS('phantomjs')
    dr.get(start_page_url)
    time.sleep(1)

    # Current page source
    print "Your url: " + start_page_url
    # print "Page source: \n" + dr.page_source.encode('utf-8')
    if not Selector(text=dr.page_source).xpath("//body/*"):
        print "\nYour url is not found."
        sys.exit(1)

    # Start from the #1 page
    # cur_page_num = 0
    # try:
    #     cur_page_num = int(Selector(text=dr.page_source).xpath("//span[@class='pagebox_num_nonce']/text()").extract()[0])
    # except IndexError:
    #     pass
    #
    # if cur_page_num != 1:
    #     goto_first_page_js = Selector(text=dr.page_source).xpath("//span[@class='pagebox_num']/a/@onclick").extract()[0]
    #     # print goto_first_page_js
    #     dr.execute_script(goto_first_page_js)
    #     dr.refresh()
    #     time.sleep(1)
    #
    # btn_next_page_text = u'下一页'
    # goto_next_page_js = Selector(text=dr.page_source).xpath("//span[@class='pagebox_pre']/a/@onclick").extract()[0]
    # # print goto_next_page_js

    page_url_list = []
    # i = 0
    while True:
        try:
            element = WebDriverWait(dr, 10).until(
                ec.presence_of_element_located((By.XPATH, url_list_xpath))
                # ec.presence_of_element_located((By.XPATH, "//span[@class='c_tit']/a"))
            )
        finally:
            pass
        # print dr.page_source
        # print "Current page number: " + \
        #       Selector(text=dr.page_source).xpath("//span[@class='pagebox_num_nonce']/text()").extract()[0]

        cur_page_list = dr.find_elements_by_xpath(url_list_xpath)
        # cur_page_list = dr.find_elements_by_xpath("//span[@class='c_tit']/a")
        page_url_list.extend([[page.text, page.get_attribute("href")] for page in cur_page_list])
        # print len(cur_page_list)
        # print len(page_url_list)

        # nolink_text = ""
        # try:
        #     nolink_text = Selector(text=dr.page_source).xpath("//span[@class='pagebox_pre_nolink']/text()").extract()[0]
        # except IndexError:
        #     pass
        #
        # if nolink_text == btn_next_page_text:
        #     break

        # dr.execute_script(goto_next_page_js)
        # dr.refresh()
        # time.sleep(1)
        break

    print len(page_url_list)
    # exit(1)

    # page_set = set(page_list)
    for page in page_url_list:
        url = page[1]
        print page[0]
        print url
        html = get_html(curl, url)
        keyWords = Selector(text=html).xpath(tag_list_xpath).extract()
        # keyWords = Selector(text=html).xpath("//section[@class='article-a_keywords']/a/text()").extract()
        print ", ".join(keyWords)
        # for kw in keyWords:
        #     print kw

    dr.close()
    dr.quit()

    print '---------------end------------------'
