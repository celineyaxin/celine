# -*- coding: UTF-8 -*-
import csv
import os
import requests
from openpyxl import Workbook
os.environ['http_proxy'] = 'http://localhost'

workbook = Workbook()
sheet = workbook.active
head_row = ["商家名", "投诉量", "已回复", "已完成", "满意度"]
sheet.append(head_row)


headers = {
    "authority": "tvax2.sinaimg.cn",
    "accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "accept-language": "zh-CN,zh;q=0.9",
    "referer": "https://tousu.sina.com.cn/",
    "sec-ch-ua": "^\\^Not",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "^\\^Windows^^",
    "sec-fetch-dest": "image",
    "sec-fetch-mode": "no-cors",
    "sec-fetch-site": "cross-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
    "Referer": "https://tousu.sina.com.cn/",
}


def get_data(page):
    url = "https://tousu.sina.com.cn/api/company/main_search"
    params = {
        "sort_col": "1",
        "sort_ord": "2",
        "page_size": "10",
        "page": page
    }
    response = requests.get(url, headers=headers, params=params)
    json_data = response.json()
    data_list = json_data.get('result').get('data').get('lists', [])
    if not data_list:
        print('----done----')
    for row in data_list:
        title = row.get('title')
        valid_amt = row.get('valid_amt')
        replied_amt = row.get('replied_amt')
        completed_amt = row.get('completed_amt')
        eval_points = row.get('eval_points')
        item = [title, valid_amt, replied_amt, completed_amt, eval_points]
        sheet.append(item)
        # csv_writer.writerow(item)
        print(item)


# f = open('data.csv', 'w', encoding='utf-8', newline='')
# csv_writer = csv.writer(f)



for i in range(100):
    print(f'---start----{i + 1}')
    get_data(str(i + 1))

workbook.save(filename="data.xlsx")

