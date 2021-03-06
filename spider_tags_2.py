# -*- coding: utf8 -*-

import sys
import os
import time
import traceback
import signal
import MySQLdb
import MySQLdb.cursors
import logging
from logging.handlers import TimedRotatingFileHandler
from scrapy.selector import Selector
from scrapy.http import HtmlResponse
from selenium import webdriver
import pycurl
import StringIO

g_log_dir = "./"
g_instance_id = 1
g_mysql_conf = {'host': '192.168.31.49', 'user': 'touchtv', 'passwd': 'op@touchtv', 'dbname': 'touchtv_dev',
                'port': 3306}
g_logger = logging.getLogger('tagsspider')

def daemon():
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError, e:
        sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
        sys.exit(1)

    # Decouple from parent environment
    os.setsid()
    os.umask(0)

    # Do second fork
    try:
        pid = os.fork()
        if pid > 0:
            # Exit from second parent
            sys.exit(0)
    except OSError, e:
        sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
        sys.exit(1)

    # Redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    si = file(os.devnull, 'r')
    so = file(os.devnull, 'a+')
    se = file(os.devnull, 'a+', 0)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())


# def sighandler(a, b):
#     g_spiderTags.stop()
#     g_logger.info("got a signal %d" % a)


class mysqldb():
    def __init__(self, dbconfig):
        self._dbconninterval = 30
        self._dbconfig = dbconfig
        self._dblastconntime = 0
        self._dbconn = None
        self._dbcursor = None
        self.conndb()

    def conndb(self):
        try:
            self._dbconn = MySQLdb.connect(host=self._dbconfig['host'], user=self._dbconfig['user'],
                                           passwd=self._dbconfig['passwd'], \
                                           db=self._dbconfig['dbname'], port=self._dbconfig['port'], charset="utf8")
            self._dbconn.autocommit(True)
            self._dbconn.ping(True)
            self._dbcursor = self._dbconn.cursor(MySQLdb.cursors.Cursor)
            self._dblastconntime = time.time()
        except Exception, e:
            g_logger.error(traceback.format_exc())
            raise Exception("conn mysql error")

    def reconndb(self):
        try:
            if time.time() > self._dblastconntime + self._dbconninterval:
                self._dblastconntime = time.time()
                # self.closedb()
                self.conndb()
            else:
                time.sleep(1)
        except Exception, e:
            g_logger.error(traceback.format_exc())

    def getSpiderSources(self, instanceid):
        self.conndb()

        sources = ()
        sql = 'select pk,tag_pk,url,url_list_xpath,url_list_css,url_list_selector_type,url_list_browser_engine,tag_xpath,tag_css,tag_selector_type,tag_browser_engine,multi_page,root_tag_pk from spider_tag_source where instance_id=%d and `status`=0 and UNIX_TIMESTAMP(CURRENT_TIMESTAMP()) - unix_timestamp(last_spider_time) > `interval`*60' % instanceid
        g_logger.info(sql)
        self._dbcursor.execute(sql)
        sources = self._dbcursor.fetchall()

        return sources

    # def insertTag(self, p_tag_pk, tag_name, root_tag_pk):
    #     try:
    #         sql = "insert into spider_tag (p_tag_pk, tag_name, root_tag_pk) values (%d,'%s', %d)" % (
    #         p_tag_pk, tag_name, root_tag_pk)
    #         print sql
    #         g_logger.debug(sql)
    #         self._dbcursor.execute(sql)
    #     except Exception, e:
    #         if e[0] != 1062:
    #             g_logger.error(traceback.format_exc())

    def get_tag_pk(self, root_tag_pk, p_tag_pk, tag_name):
        self.conndb()

        sql = '''
                 select t.pk
                   from touchtv_dev.spider_tag t
                  where t.root_tag_pk = {root_tag_pk}
                    and t.p_tag_pk = {p_tag_pk}
                    and t.tag_name = '{tag_name}'
              '''.format(root_tag_pk=root_tag_pk, p_tag_pk=p_tag_pk, tag_name=tag_name.encode('utf-8'))
        print sql
        g_logger.info(sql)
        self._dbcursor.execute(sql)
        pk = self._dbcursor.fetchone()

        return pk

    def insertTag(self, p_tag_pk, tag_name, root_tag_pk):
        try:
            ssql = "select pk from spider_tag where p_tag_pk=%d and tag_name='%s'" % (p_tag_pk, tag_name)
            self._dbcursor.execute(ssql)
            pk = self._dbcursor.fetchone()
            if pk is None:
                sql = "insert into spider_tag (p_tag_pk, tag_name, root_tag_pk) values (%d,'%s', %d)" % (
                p_tag_pk, tag_name, root_tag_pk)
                print sql
                self._dbcursor.execute(sql)
        except Exception, e:
            if e[0] != 1062:
                g_logger.error(traceback.format_exc())

    def updLastSpiderTime(self, sourceid):
        sql = "update spider_tag_source set last_spider_time=CURRENT_TIMESTAMP() where pk=%d" % sourceid
        self._dbcursor.execute(sql)

    def closedb(self):
        try:
            self._dbconn.close()
            self._dbcursor.close()
        except Exception, e:
            g_logger.error(traceback.format_exc())

    def __del__(self):
        self.closedb()


class spiderTags():
    def __init__(self, mysqlconf):
        self._mysql = mysqldb(mysqlconf)
        self._stop = False
        self.initCurl()

    def __del__(self):
        if self.curl:
            self.curl.close()

    def stop(self):
        self._stop = True

    def initCurl(self):
        self.curl = pycurl.Curl()
        self.curl.setopt(pycurl.COOKIEFILE, "cookie_file_name")
        self.curl.setopt(pycurl.COOKIEJAR, "cookie_file_name")
        self.curl.setopt(pycurl.FOLLOWLOCATION, 1)
        self.curl.setopt(pycurl.MAXREDIRS, 5)

    def GetDate(self, url):
        head = ['Accept:*/*',
                'User-Agent:Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.97 Safari/537.11']
        buf = StringIO.StringIO()
        self.curl.setopt(pycurl.WRITEFUNCTION, buf.write)
        self.curl.setopt(pycurl.URL, url)
        self.curl.setopt(pycurl.HTTPHEADER, head)
        self.curl.perform()
        the_page = buf.getvalue()
        buf.close()
        return the_page

    def doSpiderUrlList(self, dr, list_page, url_list_selector_path):

        tag_url_list = []

        dr.get(list_page)
        url_list = dr.find_elements_by_xpath(url_list_selector_path)
        print len(url_list)
        for url in url_list:
            print url.text
            g_logger.debug(url.text)
            tag_page = url.get_attribute("href")
            print tag_page
            g_logger.debug(tag_page)
            tag_url_list.append(tag_page)

        return tag_url_list

    def spiderUrlList(self, list_page, url_list_selector_path, url_list_browser_engine, multipage):

        tag_url_list = []
        page_num = 2

        try:
            if url_list_browser_engine == 1:
                dr = webdriver.PhantomJS('phantomjs')
                dr.implicitly_wait(15)

                tag_url_list = self.doSpiderUrlList(dr, list_page, url_list_selector_path)

                if multipage == 1:

                    while True:
                        next_page = dr.find_element_by_link_text('下一页')
                        if not next_page:
                            break
                        print page_num, next_page
                        next_page_url = next_page.get_attribute("href")
                        if not next_page_url:
                            break

                        tag_url_list = tag_url_list + self.doSpiderUrlList(dr, next_page_url, url_list_selector_path)
                        print 'tag_url_list', len(tag_url_list)

                        page_num = page_num + 1

                dr.close()
                dr.quit()

        except Exception, e:
            g_logger.error("page number %d" % page_num)
            g_logger.error(traceback.format_exc())

        return tag_url_list

    def spiderTags(self, tag_url_list, tag_browser_engine, tag_selector_path):

        tags = set()

        for tag_url in tag_url_list:
            print tag_url
            g_logger.debug(tag_url)
            if tag_browser_engine == 0:
                htmltext = self.GetDate(tag_url)
                keyWords = Selector(text=htmltext).xpath(tag_selector_path).extract()
                for kw in keyWords:
                    # kw = kw.strip()
                    print kw
                    g_logger.debug(kw)
                    if len(kw) >= 2:
                        tags.add(kw)
        return tags

    def doSpider(self, source):
        print source
        sourceid = source[0]
        tagid = source[1]
        list_page = source[2]
        url_list_selector_path = 0
        if source[5] == 0:
            url_list_selector_path = source[3]
        else:
            url_list_selector_path = source[4]
        url_list_browser_engine = source[6]
        tag_selector_path = 0
        if source[9] == 0:
            tag_selector_path = source[7]
        else:
            tag_selector_path = source[8]
        tag_browser_engine = source[10]
        multipage = source[11]
        root_tag_pk = source[12]

        print 'url_list_selector_path:', url_list_selector_path
        print 'tag_selector_path:', tag_selector_path
        print 'tag_browser_engine:', tag_browser_engine

        tag_url_list = self.spiderUrlList(list_page, url_list_selector_path, url_list_browser_engine, multipage)

        print 'tag_url_list', len(tag_url_list)

        tags = self.spiderTags(tag_url_list, tag_browser_engine, tag_selector_path)

        for tag in tags:
            self._mysql.insertTag(tagid, tag, root_tag_pk)

        self._mysql.updLastSpiderTime(sourceid)

    def run(self, instanceid):

        while self._stop is not True:
            start_time = time.time()
            try:
                sources = self._mysql.getSpiderSources(g_instance_id)
                print "get sources nums:%d" % len(sources)

                if len(sources) > 0:
                    for source in sources:
                        self.doSpider(source)
            except Exception, e:
                g_logger.error(traceback.format_exc())

            if time.time() - start_time < 5:
                g_logger.info('sleep...')
                time.sleep(5)

        g_logger.info('do spider exit')


# if __name__ == "__main__":
#     signal.signal(signal.SIGTERM, sighandler)
#     signal.signal(signal.SIGINT, sighandler)
#
#     g_logger = logging.getLogger('tagsspider')
#     fileTimeHandler = TimedRotatingFileHandler(g_log_dir + './tagsspider.log', "MIDNIGHT", 1, 1000)
#     fileTimeHandler.suffix = "%Y%m%d"
#     g_logger.setLevel(logging.DEBUG)
#     formatter = logging.Formatter('%(asctime)s %(process)d [%(levelname)s] %(message)s')
#     fileTimeHandler.setFormatter(formatter)
#     g_logger.addHandler(fileTimeHandler)
#
#     g_logger.info("spider tags start")
#
#     daemon()
#
#     try:
#         g_spiderTags = spiderTags(g_mysql_conf)
#         g_spiderTags.run(g_instance_id)
#     except Exception, e:
#         g_logger.error(traceback.format_exc())
#
#     g_logger.info("spider tags exit")
