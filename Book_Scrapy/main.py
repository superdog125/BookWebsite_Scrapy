# --utf8--
# author: 宇宙无敌小超人
# 1.从总分类中获取所有分类及其所有子分类名字及其对应的链接 ====》 字典型 一一对应
# 2.循环所有子链接，获取其孙子页
# 3.拿到孙子页，翻页获取每一本书的详情页
# 4.解析详情页，拿到每本书的所有信息
# 5.存入数据库 [{big_cata_name:[{small_cata_name:small_url1},{small2:url2}...]},{},{}]
from selenium import webdriver
import time
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import re
import pymongo
import json

class Book_Scrapy(object):

    def __init__(self):
        self.ua = UserAgent()
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument(
            'user-agent= ' + self.ua.random
        )
        self.chrome_options.add_argument('--headless')
        self.browser = webdriver.Chrome(executable_path='driver/chromedriver.exe', options=self.chrome_options)
        self.s_num = 1 # 大分类迭代个数
        self.b_num = 1 # 小分类迭代个数
        self.num = 1
        self.small_url = ''
        self.small_cata_name = ''
        self.cata = {}
        self.small_cata = []
        self.big_cata_name = ''
        self.big_cata = {}
        self.all_cata = []

        self.big_cata_name_list = []
        self.small_cata_name_url_list = []
        self.all_items = []

        self.client = pymongo.MongoClient(host='127.0.0.1', port=27017)
        self.db = self.client['books']

    def get_cata_list_url(self):
        start_url = 'http://book.ly.superlib.net/book.do?go=guideindex'
        self.browser.get(start_url)
        # 大类目
        try:
            while self.browser.find_element_by_css_selector('#enfenlei > li:nth-child({b_num}) > dl > dt > a'.format(b_num=self.b_num)):
                self.b_cata = self.browser.find_element_by_css_selector(
                    '#enfenlei > li:nth-child({b_num}) > dl > dt > a'.format(b_num=self.b_num))
                # 得到一个大类目名字
                # print('这里无验证码')
                self.big_cata_name = self.b_cata.text
                print(self.big_cata_name)
                self.big_cata_name_list.append(self.big_cata_name)
                js = "document.getElementById(\"mfl{num}\").style.display='block';".format(num=self.num)
                self.browser.execute_script(js)
                time.sleep(1)
                # 小类目
                try:
                    while self.browser.find_element_by_css_selector('#mfl{num} > ul > li:nth-child({s_num}) > a'.format(num=str(int(self.num)),s_num=self.s_num)):
                        self.s_cata = self.browser.find_element_by_css_selector('#mfl{num} > ul > li:nth-child({s_num}) > a'.format(num=self.num,s_num=self.s_num))
                        # self.small_cata_name = self.s_cata.text
                        # mfl23 > ul > li:nth-child(3) > a
                        self.small_url = self.s_cata.get_attribute('href')
                        self.small_cata_name = self.s_cata.get_attribute('title')
                        print(self.small_cata_name)
                        print(self.s_num)
                        print(self.small_url)
                        self.small_cata_name_url_json = {self.small_cata_name:self.small_url}
                        self.small_cata_name_url_list.append(self.small_cata_name_url_json)
                        self.s_num += 1
                except Exception as e:
                    self.s_num = 1
                    print('该大分类爬完，继续下一分类，当前大分类是第{}个'.format(self.num))
                    print('本大类数据整理格式中....')
                    self.per_item = {self.big_cata_name:self.small_cata_name_url_list}
                    print(self.per_item)
                    self.all_items.append(self.per_item)
                    self.small_cata_name_url_list = []

                # 1 3 6 8 11 13
                js = "document.getElementById(\"mfl{num}\").style.display='none';".format(num=self.num)
                self.browser.execute_script(js)
                time.sleep(1)
                if int(self.num) % 2 == 0:
                    self.b_num = self.b_num + 3
                    self.num += 1
                    time.sleep(1)
                else:
                    self.b_num = self.b_num + 2
                    self.num += 1
                    time.sleep(1)
        except Exception as e:
            # print(e)
            print('全网所有图书分类数据均已爬取完毕...5s后开始爬取图书具体信息')
            print('大分类一共有%d个' % len(self.big_cata_name_list))
            self.data_json = self.read_json()  # 从txt中读取上面存入的图书网站分类Json数据,为了让后续程序的处理更加健壮
            self.data_json = json.dumps(self.data_json,ensure_ascii=False)
            self.all_items = json.loads(self.data_json)
            # print(self.all_items)
            # print(type(self.all_items))
            ######## self.save_json(self.all_items) # 先将全网站的分类数据保存到本地
            # 获取单个大分类
            for self.per_item in self.all_items:
                # self.per_item.values() 单个大分类对应的所有小分类名称和Url 是个数组
                # self.per 迭代每个小分类名称和Url
                # print(self.per_item)  # 单个大分类
                # print(type(self.per_item))  # {'马列主义、毛泽东思想、邓小平理论': [{'马克思、恩格斯著作': 'http://book.ly.superlib.net/book.do?go=guidesearch&flid=0101'}
                time.sleep(1)
                for self.per in self.per_item.values(): # 循环单个大分类的每个小分类
                    # print(self.per)
                    # print(type(self.per))
                    time.sleep(2)
                    for self.i in self.per:
                        # self.i = json.dumps(self.i)
                        # self.i = json.loads(self.i)
                        # print(self.i)
                        # print(type(self.i)) # 单个小分类
                        print('正在解析的是%s分类图书' % (self.i))
                        # print(list(self.i.values()))  # 获得单个小分类对于的链接
                        self.result_list = self.parse_url(list(self.i.values())[0]) # 获得此小分类中的所有图书链接
                        print(len(self.result_list))

                        try:
                            self.page_all_url = self.read_txt()   # 从txt中读取上面存入的图书网站分类Json数据,为了让后续程序的处理更加健壮
                            self.i = 1
                            for per_url in self.page_all_url:
                                print("当前正在解析第%d本书" % i)
                                self.parse_data(per_url)
                                time.sleep(1)
                                self.i += 1
                        except Exception as e:
                            print("当前解析指定页面数据的详细信息出错")
        self.browser.close()


    def save_json(self,data):
        with open("book_cata_info.txt", "w+", encoding='utf-8') as fp:
            fp.write(json.dumps(data, indent=4, ensure_ascii=False))
        fp.close()


    def save_txt(self, data):
        with open("small_cata_book_info.txt", "w+", encoding='utf-8') as fp:
            fp.write(data)
        fp.close()


    def read_txt(self):
        with open("small_cata_book_info.txt", "r", encoding='utf-8') as fp:
            data = fp.readlines()
        fp.close()
        return data


    def read_json(self):
        with open("book_cata_info.txt", "r", encoding='utf-8') as fp:
            data = json.load(fp)
        fp.close()
        return data


    def save_mongo(self, data):
        try:
            if not self.db['book'].find_one({'tryReadLink': data['tryReadLink']}):
                self.db['book'].insert(data)
                print('存储到MongoDB成功', data)
        except Exception:
            print('存储到MongoDb失败', data)


    def parse_url(self, url):
        # self.start_url = 'http://book.ly.superlib.net/book.do?go=guidesearch&unitid=0&Field=0&flid=0101'
        print('进入parse_url函数' + url)
        self.start_url = url
        self.now_page = 1
        self.now_num = 1
        self.item_url_list = []
        while True:
            time.sleep(2)
            self.start_url = self.start_url + '&pages={n}&sw=&isort=0&ptype='.format(n=self.now_page) + '&ishow=1'
            self.browser.get(self.start_url)
            # 获取该分类对应的总页数
            self.total_page = self.browser.find_element_by_xpath('//*[@id="wrap2"]/div/div[3]/div[1]/div[1]/span[3]').text
            print(self.total_page)
            # 获得该类目下的每一页的所有图书内容链接
            try:
                if int(self.now_page) <= int(self.total_page):
                    while int(self.now_num) <= 10:
                        time.sleep(2)
                        try:
                            self.item_url = self.browser.find_element_by_xpath('//*[@id="wrap2"]/div/div[3]/div[1]/ul/li[{n}]/a'.format(n=self.now_num)).get_attribute('href')
                            self.item_url_list.append(self.item_url)
                            self.now_num = str(int(self.now_num)+1)
                            print(self.item_url)
                            self.save_txt(self.item_url)
                            time.sleep(1)
                        except Exception as e:
                            print('这里出错啦')
                            print(e)
                            self.item_url = self.browser.find_element_by_xpath(
                                '//*[@id="wrap2"]/div/div[3]/div[1]/ul/li[{n}]/a[1]'.format(n=self.now_num)).get_attribute(
                                'href')
                            self.item_url_list.append(self.item_url)
                            self.now_num = str(int(self.now_num) + 1)
                            print(self.item_url)
                            self.save_txt(self.item_url)
                            time.sleep(1)
                    print('第%d页获取完毕,将自动获取下一页' % self.now_page)
                    print(len(self.item_url_list))
                    self.now_num = 1
                    self.now_page = int(self.now_page)+1
                    time.sleep(1)
            except Exception as e:
                print('爬取速度过快，出现了验证码，请在10s内手动验证')
                time.sleep(10)
                if int(self.now_page) <= int(self.total_page):
                    while int(self.now_num) <= 10:
                        time.sleep(2)
                        try:
                            self.item_url = self.browser.find_element_by_xpath('//*[@id="wrap2"]/div/div[3]/div[1]/ul/li[{n}]/a'.format(n=self.now_num)).get_attribute('href')
                            self.item_url_list.append(self.item_url)
                            self.now_num = str(int(self.now_num)+1)
                            print(self.item_url)
                            self.save_txt(self.item_url)
                            time.sleep(1)
                        except Exception as e:
                            print('这里出错啦')
                            print(e)
                            self.item_url = self.browser.find_element_by_xpath(
                                '//*[@id="wrap2"]/div/div[3]/div[1]/ul/li[{n}]/a[1]'.format(n=self.now_num)).get_attribute(
                                'href')
                            self.item_url_list.append(self.item_url)
                            self.now_num = str(int(self.now_num) + 1)
                            print(self.item_url)
                            self.save_txt(self.item_url)
                            time.sleep(1)
                    print('第%d页获取完毕,将自动获取下一页' % self.now_page)
                    print(len(self.item_url_list))
                    self.now_num = 1
                    self.now_page = int(self.now_page)+1
        print('该分类的所有页中的图书详情页链接已经获取完毕...总图书量为%d' % len(self.item_url_list))
        return self.item_url_list



    def parse_data(self, url):
        js = "window.open('" + url + "')"
        self.browser.execute_script(js)
        # start_url = 'http://book.ly.superlib.net/views/specific/2929/bookDetail.jsp?dxNumber=000016954516&d=F2327A550A44812B71010856F2D9F37D'
        # self.browser.get(start_url)
        html = self.browser.page_source
        soup = BeautifulSoup(html, 'html.parser')
        try:
            try:
                bookName = soup.find('div', class_='tutilte').get_text()
            except Exception as e:
                print('请求太过频繁 再来一次')
                time.sleep(5)
                return self.parse_data()
            try:
                dds = soup.find_all('div', class_='tubox')[0]('dl')[0]('dd').strip()
            except Exception as e:
                dds = '无'
            try:
                author = str(dds[0].get_text()).split('】')[-1]
            except Exception as e:
                print('请求太过频繁 再来一次')
                time.sleep(5)
                return self.parse_data()
            try:
                subBookName = str(dds[1].get_text()).split('】')[-1].strip()
            except Exception as e:
                subBookName = '无'
            try:
                shapeNum = str(dds[2].get_text()).split('】')[-1].strip()
                print(shapeNum)
            except Exception as e:
                shapeNum = '无'
            try:
                publishName = str(dds[3].get_text()).split('】')[-1].strip()
                print(publishName)
            except Exception as e:
                publishName = '无'
            try:
                ISBN = str(dds[4].get_text()).split('】')[-1].strip()
            except Exception as e:
                ISBN = '无'
            try:
                cataNum = str(dds[5].get_text()).split('】')[-1].strip()
            except Exception as e:
                cataNum = '无'
            try:
                keyWords = str(dds[6].get_text()).split('】')[-1].strip()
            except Exception as e:
                keyWords = '无'
            try:
                reference = str(dds[7].get_text()).split('】')[-1].strip()
            except Exception as e:
                reference = '无'
            try:
                tryReadLink = soup.find_all('div', class_='testimg')[0]('a')[0]['href'].strip()
            except Exception as e:
                tryReadLink = '无'
            try:
                ssn = str(soup).split('ssn=')[-1].split('&')[0].strip()
            except Exception as e:
                ssn = '无'
            try:
                dxid = soup.find_all('input', attrs={'name':'dxid'})[0]['value'].strip()
            except Exception as e:
                dxid = '无'
            try:
                isbn = soup.find_all('input', attrs={'name':'isbn'})[0]['value'].strip()
            except Exception as e:
                isbn = '无'
            data = {'author':author,'subBookName':subBookName,'shapeNum':shapeNum,'publishName':publishName,'ISBN':ISBN,'cataNum':cataNum,'keyWords':keyWords,'reference':reference,'tryReadLink':tryReadLink,'ssn':ssn,'dxid':dxid,'isbn':isbn}
            self.save_mongo(data=data)
            print(data)
            self.browser.close()
        except Exception as e:
            print('请求太过频繁 再来一次')
            time.sleep(5)
            return self.parse_data()



if __name__ == '__main__':
    book = Book_Scrapy()
    book.get_cata_list_url()