# -*- coding: utf8 -*-

import StringIO
import pycurl
import time

import sys
from scrapy.selector import Selector
from selenium import webdriver


# body = '<html><head><meta name="keywords" content="曝森林狼有意交易罗斯 心疼玫瑰!逃不脱的魔掌,罗斯,森林狼,尼克斯"></head><body><span>good</span><span>good1</span><div><span>good2</span></div></body></html>'
# span = Selector(text=body).xpath('//span/text()').extract()
# 
# print span
# 
# span = Selector(text=body).xpath('//meta[@name="keywords"]/@content').extract()
# print span.pop()

#sel.xpath('//ul[@class="directory-url"]/li')
#sel.xpath('//meta[@name="keywords"]/@content')


def init_curl():
    c = pycurl.Curl()
    c.setopt(pycurl.COOKIEFILE, "cookie_file_name")
    c.setopt(pycurl.COOKIEJAR, "cookie_file_name")
    c.setopt(pycurl.FOLLOWLOCATION, 1)
    c.setopt(pycurl.MAXREDIRS, 5)
    return c


def get_html(c, page_url):
    head = ['Accept:*/*',
          'User-Agent:Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.97 Safari/537.11']
    buf = StringIO.StringIO()
    c.setopt(pycurl.WRITEFUNCTION, buf.write)
    c.setopt(pycurl.URL, page_url)
    c.setopt(pycurl.HTTPHEADER, head)
    c.perform()
    page_html = buf.getvalue()
    buf.close()
    return page_html


# url = "http://sports.sina.com.cn/basketball/nba/2017-02-21/doc-ifyarrcf5173408.shtml"
# htmltext = GetDate(c, url)
# print htmltext
# 
# selector = Selector(text=htmltext)
# metaKeyWords = selector.xpath('//meta[@name="keywords"]/@content').extract()
# for m in metaKeyWords:
#     print m
# 
# descriptions = selector.xpath('//meta[@name="description"]/@content').extract()
# for d in descriptions:
#     print d
# 
# 
# keyWords = selector.xpath('//section/a/text()').extract()
# for kw in keyWords:
#     print kw

#-------------------------------
#listPage = "http://roll.sports.sina.com.cn/s/channel.php?ch=02#col=181&spec=&type=&ch=02&k=&offset_page=0&offset_num=0&num=60&asc=&page=1"
# listHtmlText = GetDate(c, listPage)
# #print listHtmlText
# selector = Selector(text=listHtmlText)
# listUrl = selector.xpath('//div/ul/li/span[@class="c_tit"]/a/@href').extract()
# for url in listUrl:
#     print url
    
# //div/ul/li/span[@class="c_tit"]/a/@href

if __name__ == '__main__':

    if len(sys.argv) <= 1:
        print 'Usage: ' + sys.argv[0] + ' <one url>'
        sys.exit(1)

    start_page_url = sys.argv[1]

    print '---------------start------------------'

    curl = init_curl()
    # start_page = "http://roll.sports.sina.com.cn/s/channel.php?ch=02#col=181&spec=&type=&ch=02&k=&offset_page=0&offset_num=0&num=60&asc=&page=19"
    dr = webdriver.PhantomJS('phantomjs')
    dr.get(start_page_url)

    # Current page source
    print dr.page_source

    # Start from the #1 page
    cur_page_num = 0
    try:
        cur_page_num = int(Selector(text=dr.page_source).xpath("//span[@class='pagebox_num_nonce']/text()").extract()[0])
    except IndexError:
        pass

    if cur_page_num != 1:
        goto_first_page_js = Selector(text=dr.page_source).xpath("//span[@class='pagebox_num']/a/@onclick").extract()[0]
        # print goto_first_page_js
        dr.execute_script(goto_first_page_js)
        dr.refresh()

    btn_next_page_text = u'下一页'
    goto_next_page_js = Selector(text=dr.page_source).xpath("//span[@class='pagebox_pre']/a/@onclick").extract()[0]
    print goto_next_page_js

    page_url_list = []
    # i = 0
    while True:
        # print dr.page_source
        print "Current page number: " + \
              Selector(text=dr.page_source).xpath("//span[@class='pagebox_num_nonce']/text()").extract()[0]

        cur_page_list = dr.find_elements_by_xpath("//span[@class='c_tit']/a")
        page_url_list.extend([[page.text, page.get_attribute("href")] for page in cur_page_list])
        # print len(cur_page_list)
        # print len(page_url_list)

        nolink_value = ""
        try:
            nolink_value = Selector(text=dr.page_source).xpath("//span[@class='pagebox_pre_nolink']/text()").extract()[0]
        except IndexError:
            pass

        if nolink_value == btn_next_page_text:
            break
        dr.execute_script(goto_next_page_js)
        dr.refresh()
        time.sleep(1)

    print len(page_url_list)
    # exit(1)

    # page_set = set(page_list)
    for page in page_url_list:
        url = page[1]
        print page[0]
        print url
        html = get_html(curl, url)
        keyWords = Selector(text=html).xpath("//section[@class='article-a_keywords']/a/text()").extract()
        for kw in keyWords:
            print kw

    print '---------------end------------------'

# print '---------------------------------'
# 
# alist = dr.find_elements_by_css_selector("span.c_tit a")
# 
# for a in alist:
#     #print a.text
#     print a.get_attribute("href")
# dr.quit()










