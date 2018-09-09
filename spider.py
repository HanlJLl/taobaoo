import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from pyquery import PyQuery as pq
from config import *
import pymongo

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]


browser = webdriver.Chrome()
wait = WebDriverWait(browser,10)

def search():
    try:
        browser.get ( 'https://www.taobao.com' )  # 打开请求的url
        input = wait.until (
            EC.presence_of_element_located ( (By.CSS_SELECTOR, '#q') ) )  # 等待搜索输入框加载完成
        input.send_keys ( "美食" )  # 输入框中输入“美食”
        sumbit = wait.until (
            EC.element_to_be_clickable ( (By.CSS_SELECTOR, '#J_TSearchForm > div.search-button > button') ) )
        sumbit.click ()
        total = wait.until (
            EC.presence_of_element_located ( (By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.total') ) )
        get_products ()
        return total.text
    except TimeoutException:
        return search ()

def get_products():
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item')))
    html=browser.page_source
    doc=pq(html)
    items = doc('#mainsrp-itemlist .items .item').items()#items 方法返回对象列表
    for item in items:
        product={
            'image':item.find('.pic .img').attr('src'),
            'price':item.find('.price').text(),
            'deal':item.find('.deal-cnt').text()[:-3],
            'title':item.find('.title').text(),
            'shop':item.find('.shop').text(),
            'location':item.find('.location').text()
        }
        print(product)
        save_to_mongo(product)

def next_page(page_number):
    try:
        input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.form > input')))
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit')))
        input.clear()
        input.send_keys(page_number)
        submit.click()
        wait.until (
            EC.text_to_be_present_in_element ((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > ul > li.item.active > span'),str ( page_number ) ) )  # 高亮
        get_products ()
    except TimeoutException:
        next_page(page_number)

def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('存储到MONGODB成功',result)
    except Exception:
        print('存储到MONGODB失败',result)


def main():
    total = search()
    total = int(re.compile('(\d+)').search(total).group(1))
    for i in range(2,total+1):
        next_page(i)

    browser.close()

if __name__ == '__main__':
    main()