# -- anthor: 宇宙无敌小超人 --
import requests
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from fake_useragent import UserAgent
import pymongo
import json
import re
import os

class Foreign_Scrapy(object):

    def __init__(self):
        self.per_item_cata_list = [] # 每个关键字的所有分类信息
        self.all_item_cata_list = [] # 所有关键字的所有分类信息
        self.page_flag = 0
        self.curentKeywords = ''
        self.sigle_keywords = ['aA', 'bB', 'cC', 'dD', 'eE', 'fF', 'gG',
                               'hH', 'iI', 'jJ', 'kK', 'lL', 'mM', 'nN',
                               'oO', 'pP', 'qQ', 'rR', 'sS', 'tT',
                               'uU', 'vV', 'wW', 'xX', 'yY', 'zZ']

        self.curentPage = 1
        self.tables_contend = []

        self.client = pymongo.MongoClient(host='127.0.0.1', port=27017)
        self.db = self.client['fbooks']

        self.ua = UserAgent()
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument(
            'user-agent= '+self.ua.random
        )
        self.chrome_options.add_argument('--headless')
        self.browser = webdriver.Chrome(executable_path='driver/chromedriver.exe', options=self.chrome_options)

    # Step A: 根据关键字post到查询链接  获取到左侧所有年份分类的值及其对应的链接
    def get_cata_info(self, curentKeywords, flag):
        if flag==False: # 无异常进来的
            self.start_url = 'http://eng.ly.superlib.net/searchFBook?'
            for self.keywords in self.sigle_keywords:
                self.curentKeywords = self.keywords
                self.url = self.start_url + 'Pages=1&channelsearchFBook&Sort=&by=&ey=&type=2&Field=all&sw=' + self.keywords
                self.browser.get(self.url)
                html = self.browser.page_source
                soup = BeautifulSoup(html, 'html.parser')
                time.sleep(3)
                try:
                    js = "document.getElementById(\"moreyear\").style.display='block';"
                    self.browser.execute_script(js)
                    time.sleep(1)
                except Exception as e:
                    print('platformJs执行失败，再来一次')
                    time.sleep(2)
                    self.get_cata_info(curentKeywords=self.curentKeywords, flag=True)
                years_cata = soup.find_all('div',{'id':'leftcata'})[0].find_all('div',{'style':'padding-left:6PX;'})
                # {year : link}
                for i in range(len(years_cata)):
                    year = years_cata[i]('a')[0].text
                    link = years_cata[i]('a')[0]['href']
                    item_cata = {'year': year, 'link': link}
                    if item_cata['year'] != "隐藏":
                        self.per_item_cata_list.append(item_cata)
                self.per_item_cata_list.remove(self.per_item_cata_list[-1])
                print('关键词:%s的分类信息存储完毕...' % self.keywords)
                self.save_json(self.keywords,self.per_item_cata_list)
                self.per_item_cata_list.clear()
        else:
            print('本次是断点续爬...')
            self.start_url = 'http://eng.ly.superlib.net/searchFBook?'
            index = self.sigle_keywords.index(curentKeywords)
            self.new_keywords = self.sigle_keywords[index:]
            for self.keywords in self.new_keywords:
                self.curentKeywords = curentKeywords # 把上次异常时的关键词传入
                self.url = self.start_url + 'Pages=1&channelsearchFBook&Sort=&by=&ey=&type=2&Field=all&sw=' + self.keywords
                self.browser.get(self.url)
                html = self.browser.page_source
                soup = BeautifulSoup(html, 'html.parser')
                time.sleep(3)
                try:
                    js = "document.getElementById(\"moreyear\").style.display='block';"
                    self.browser.execute_script(js)
                    time.sleep(1)
                except Exception as e:
                    print('platformJs执行失败，再来一次')
                    self.get_cata_info(curentKeywords=self.curentKeywords, flag=True)
                years_cata = soup.find_all('div', {'id': 'leftcata'})[0].find_all('div', {'style': 'padding-left:6PX;'})
                # {year : link}
                for i in range(len(years_cata)):
                    year = years_cata[i]('a')[0].text
                    link = years_cata[i]('a')[0]['href']
                    item_cata = {'year': year, 'link': link}
                    if item_cata['year'] != "隐藏":
                        self.per_item_cata_list.append(item_cata)
                self.per_item_cata_list.remove(self.per_item_cata_list[-1])
                print('关键词:%s的分类信息存储完毕...' % self.keywords)
                self.save_json(self.keywords, self.per_item_cata_list)
                self.per_item_cata_list.clear()
# http://eng.ly.superlib.net/searchFBook?channel=searchFBook&sw=aA&Field=all&by=2014&ey=2014&Page=2

    # 解析单个年份分类的所有页图书详情页链接
    def parse_info(self, year, link):
        self.curentPage = 1
        self.tables_contend = []
        self.per_cata_book_url_list = []    # 每个分类年份链接中所有书本详情页url
        while self.page_flag==0:
            time.sleep(2)
            parse_url = 'http://eng.ly.superlib.net/' + link + '&Page=' + str(self.curentPage)
            print(parse_url)
            headers = {'User-Agent': self.ua.random }
            r = requests.get(parse_url, headers=headers)
            html = r.text
            soup = BeautifulSoup(html, 'html.parser')
            tables = soup.find_all('table', class_='book1')
            print(str(year) + '本页面的tables个数为:' + str(len(tables)))
            if len(tables) != 15:
                self.page_flag = 1
            else:
                self.page_flag = 0
                for table in tables:
                    self.tables_contend.append(table)
                if self.curentPage > 1:
                    # 出现重复页面，更换Url链接
                    if self.tables_contend[0] == self.per_cata_book_url_list[0]:
                        self.tables_contend = []  # 比较完就清空代表当前页Url的list
                        print('有页面存在重复，重复页面为:' + parse_url)
                        time.sleep(2)
                        parse_url = 'http://eng.ly.superlib.net/' + link + '&Pages=' + str(self.curentPage)
                        print(parse_url)
                        headers = {'User-Agent': self.ua.random}
                        r = requests.get(parse_url, headers=headers)
                        html = r.text
                        soup = BeautifulSoup(html, 'html.parser')
                        tables = soup.find_all('table', class_='book1')
                        print(str(year) + '本页面的tables个数为:' + str(len(tables)))
                        if len(tables) != 15:
                            self.page_flag = 1
                        else:
                            self.page_flag = 0
                            for table in tables:
                                url = table.find_all('td', {'valign': 'top'})[2]('div')[0]('a')[0]['href']
                                self.per_cata_book_url_list.append(url)
                                self.tables_contend.append(url)
                                print(url)
                            print('当前%d页信息收集完毕' % self.curentPage)
                            self.curentPage += 1
                        # 得到一个年份分类下的所有书本详情页
                        print(str(year) + ':self.per_cata_book_url_list:' + str(self.per_cata_book_url_list))
                        self.page_flag = 0
                        return self.per_cata_book_url_list
            self.tables_contend = []
            for table in tables:
                time.sleep(1)
                url = table.find_all('td', {'valign': 'top'})[2]('div')[0]('a')[0]['href']
                self.per_cata_book_url_list.append(url)
                self.tables_contend.append(url)
                print(url)
            print('当前%d页信息收集完毕' % self.curentPage)
            self.curentPage += 1
        # 得到一个年份分类下的所有书本详情页
        print(str(year) + ':self.per_cata_book_url_list:'+ str(self.per_cata_book_url_list))
        self.page_flag = 0
        return self.per_cata_book_url_list



    # 大解析
    def parse(self):
        for name in self.sigle_keywords:  # 读取每个关键字对应的所有年份分类字段
            self.data_json = self.read_json(name)
            self.data_json = json.dumps(self.data_json, ensure_ascii=False)
            self.all_items = json.loads(self.data_json)
            for item in self.all_items:  # {year: year, link: link} 获取每年的分类字段
                print(item)
                time.sleep(1)
                cata_url = item['link']   # 获取每年的分类对应url
                year_url = item['year']
                try:
                    self.per_cata_book_url_list = self.parse_info(year_url,cata_url)  # 获取每年分对应的所有书本详情页url
                except Exception as e:
                    print(e)
                    print('parse_info出现错误,请检查程序...')
                    self.per_cata_book_url_list = self.parse_info(year_url,cata_url)
                for url in self.per_cata_book_url_list:
                    time.sleep(2)
                    try:
                        self.parse_detail('http://eng.ly.superlib.net/'+url)
                    except Exception as e:
                        print(e)
                        print('parse_detail出现错误,请检查程序...')


    # 解析图书详情页的各个字段：book_name , issn...
    def parse_detail(self, url):
        time.sleep(1)
        headers = {'User-Agent': self.ua.random}
        r = requests.get(url, headers=headers)
        if r.url == 'http://book.ly.superlib.net/antispiderShowVerify.ac':
            print('parse_detail遇到验证码')
            time.sleep(5)
            self.parse_detail(url)
        else:
            if r.status_code == 200:
                html = r.text
                print(r.url)
                soup = BeautifulSoup(html, 'html.parser')
                contends = soup.find_all('div',{'id':'i_text'})[0]('ul')[0]('li')
                if contends:
                    try:
                        bookName = soup.find_all('div',{'id':'m_namemin'})[0].text.strip()
                    except Exception as e:
                        bookName = ''
                    try:
                        ssn = soup.find_all('input', {'name': 'ssnumber'})[0]["value"]
                    except Exception as e:
                        ssn = ''
                    try:
                        author = contends[0].text.strip().split('】')[-1].strip()
                    except Exception as e:
                        author = ''
                    try:
                        publishName = contends[1].text.strip().split('】')[-1].strip()
                    except Exception as e:
                        publishName = ''
                    try:
                        publishTime = contends[2].text.strip().split('】')[-1].strip()
                    except Exception as e:
                        publishTime = ''
                    try:
                        dxid = soup.find_all('input', {'name': 'dxid'})[0]('value')
                    except Exception as e:
                        dxid = ''
                    try:
                        isbn = contends[3].text.strip().split('】')[-1].strip()
                    except Exception as e:
                        isbn = ''
                    data = {'author':author,'bookName':bookName,'ssn':ssn,'publishName':publishName,'publishTime':publishTime,'dxid':dxid,'isbn':isbn}
                    print(data)
                else:
                    print('这本书不存在')
                # self.save_mongo(data=data)

            else:
                print('遇到验证码')
                self.parse_detail(url)


    def save_json(self,name,data):
        with open("cata_info\\" +name+"_cata_info.txt", "w+", encoding='utf-8') as fp:
            fp.write(json.dumps(data, indent=4, ensure_ascii=False))
        fp.close()


    def read_json(self,name):
        with open("cata_info\\" +name+"_cata_info.txt", "r", encoding='utf-8') as fp:
            data = json.load(fp)
        fp.close()
        return data

    def save_mongo(self, data):
        try:
            if not self.db['fbook'].find_one({'isbn': data['isbn']}):
                self.db['fbook'].insert_one(data)
                print('存储到MongoDB成功', data)
        except Exception:
            print(e)
            print('存储到MongoDb失败', data)


if __name__ == '__main__':
    book = Foreign_Scrapy()
    try:
        book.get_cata_info(curentKeywords='', flag=False)
    except Exception as e:
        print(e)
        print('get_cata_info出现错误，请检查程序...')
    try:
        book.parse()
    except Exception as e:
        print(e)
        print('parse出现错误，请检查程序...')
