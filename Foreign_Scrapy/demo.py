import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

ua = UserAgent()

url = 'http://eng.ly.superlib.net/searchFBook?channel=searchFBook&sw=aA&Field=all&by=2008&ey=2008&Page=1'
headers = {'User-Agent': ua.random }
r = requests.get(url, headers=headers)
html = r.text
soup = BeautifulSoup(html, 'html.parser')
# 获取当前最后链接是否为下一页 若无 则说明已经到最后一页
tables = soup.find_all('table', class_='book1')
# page = soup.find_all('div', {'id': 'pageinfo'})[0]('a')[-1].text
# print(tables)
print(len(tables))
# print(page)