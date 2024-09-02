from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import datetime
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
import pymysql

def main(url):
    driver = webdriver.Chrome()
    driver.get(url)
    time.sleep(20)
    for i in range(150):
        js = "var q=document.documentElement.scrollTop=10000000"
        driver.execute_script(js)
        time.sleep(random.randint(3,5))
    # xpath2='//div[@class="blackcat-container"]'
    b = driver.find_element(By.XPATH, '//div[@class="myts-list"]')
    # b = driver.find_element_by_xpath(xpath2).get_attribute("innerHTML") 
    html_content = b.get_attribute('innerHTML')
    soup = BeautifulSoup(html_content, 'lxml')
    shuju = soup.find_all('div', class_='myts-item')
    df=pd.DataFrame(columns=['处理结果','用户名','发布时间','标题','内容','投诉对象','投诉要求'])
    for i in shuju:
        cljg = i.find_all('div')[0].text.strip()#处理结果
        yhm = i.find('span', class_='name').text.strip()  # 用户名
        fbsj = i.find('span', class_='time').text.strip()  # 发布时间
        bt = i.find('h1').text.strip()  # 标题
        nr = i.find('p').text.strip()  # 内容
        tsdx = i.find('ul', class_='list').find_all('li')[0].text.strip()  # 投诉对象
        txyq = i.find('ul', class_='list').find_all('li')[1].text.strip()  # 投诉要求
        add_data=[cljg,yhm,fbsj,bt,nr,tsdx,txyq]
        add_data = pd.DataFrame(add_data).T
        add_data.columns = df.columns
        df = pd.concat([df, add_data], ignore_index=True)
        # df = df.append(add_data, ignore_index=True)
    df.to_excel(r'/Users/chenyaxin/Desktop/comlistmt.xlsx')
if __name__ == '__main__':
    url = 'https://tousu.sina.com.cn/company/view/?couid=6185953288&sid=21101'
    main(url)
