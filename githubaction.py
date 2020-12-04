# -*- coding: utf-8 -*-
# ! /usr/bin/env python3
import time
from datetime import datetime
import requests
from lxml import etree
import json
import base64
import sys


class HotBrand():
    def __init__(self):
        self.weibo_url = 'https://s.weibo.com/top/summary?cate=realtimehot'
        self.toutiao_url = 'https://i.snssdk.com/hot-event/hot-board/?origin=hot_board'

    def fetch(self):
        data = []
        data += self.parse_toutiao()
        data += self.parse_weibo()
        return self.html_format(data)

    def html_format(self, data):
        data_html = []
        for i, item in enumerate(data):
            text = f'''\
            <a href="{item['Url']}">
            <div class="card-v6-warpper" style="height: 52px;">
            <div class="card-index card-index-active">{i + 1}</div>
            <div class="card-title">{item['Title'][:14]}</div>
            <div class="card-hot">{item['Site']}</div>
            </div>
            </a>
            '''
            data_html.append(text)
        data_html_text = ''.join(data_html)
        # pprint.pprint(data_html)
        # print(data_html_text)
        # fetch_time = str(datetime.now().ctime())
        time_utc = time.gmtime()
        time_BJ = time.strptime(f"{time_utc.tm_hour + 8} {time_utc.tm_min} {time_utc.tm_sec}", "%H %M %S")
        fetch_time = time.strftime('%D') + ' ' + time.strftime('%X', time_BJ)


        with open('template.html', 'r', encoding='utf-8') as fb:
            html = fb.read()
        html = html.replace('内容区域', data_html_text)
        html = html.replace('更新时间', f'更新时间：{fetch_time}')
        # with open('hot.html','w',encoding='utf-8') as fb:
        #     fb.write(html)
        return html

    def parse_toutiao(self):
        resp = requests.get(self.toutiao_url)
        data_resp = resp.json()
        if data_resp['status'] == "success":
            data = data_resp['data']
            data_lite = [{
                'Id': i + 1,
                'Title': item['Title'],
                'Url': item['Url'],
                'HotValue': item['HotValue'],
                # 'Type': '',
                'Site': '头条',
            }
                for i, item in enumerate(data)]
            # pprint.pprint(data_lite)
        return data_lite

    def parse_weibo(self):
        header = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/85.0.4183.121 Mobile Safari/537.36',
            'Cookie': 's_tentry=-; Apache=8262693431174.124.1601098423930; SINAGLOBAL=8262693431174.124.1601098423930; '
                      'ULV=1601098423946:1:1:1:8262693431174.124.1601098423930:; UOR=,,localhost:63342; '
                      'WBStorage=70753a84f86f85ff|undefined',
            'DNT': '1',
            'Host': 's.weibo.com',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        }
        resp = requests.get(self.weibo_url, headers=header)
        resp = requests.get(self.weibo_url)
        resp_html = etree.HTML(resp.text)
        if resp_html != '':
            selector_id = resp_html.xpath('//td[@class="td-01 ranktop"]/text()')
            selector_title = resp_html.xpath('//td[@class="td-02"]/a/text()')
            selector_url = resp_html.xpath('//td[@class="td-02"]/a/@href')
            selector_hot_value = resp_html.xpath('//td[@class="td-02"]/span/text()')
            # selector_type = resp_html.xpath('//td[@class="td-03"]/i/text()')
            # print(len(selector_id))
            # print(len(selector_title))
            # print(len(selector_hot_value))
            # print(len(selector_type))

            data = zip(selector_id, selector_title, selector_url, selector_hot_value)
            data = list(data)
            data_lite = []
            for item in data:
                temp = {
                    'Id': int(item[0]),
                    'Title': item[1],
                    'Url': 'https://s.weibo.com' + item[2],
                    'HotValue': item[3],
                    'Site': '微博',
                }
                data_lite.append(temp)
            # pprint.pprint(data_lite)
        return data_lite

    def uploadGithub(self, token, html):
        file_name = 'hot.html'
        header = {"Accept": "application/vnd.github.v3+json",
                  "Authorization": 'token ' + token,
                  }
        url = 'https://api.github.com/repos/shawze/shawze.github.io/contents/hot/index.html'

        fileDate = base64.b64encode(html.encode('utf-8')).decode('utf-8')
        r = requests.get(url=url, headers=header)
        if r.status_code == 200:
            sha = r.json()['sha']
        else:
            sha = ''
        # print(r.json())
        param = {"message": str(datetime.today()),
                 "content": fileDate,
                 "committer":
                     {"name": "shawze",
                      "email": "xiaoze@live.com"
                      },
                 "sha": sha
                 }
        rtn = requests.put(url, data=json.dumps(param), headers=header)
        print('Github:', rtn.text)


if __name__ == '__main__':
    token = sys.argv[1]
    print(sys.argv)
    hot_brand = HotBrand()
    html = hot_brand.fetch()
    hot_brand.uploadGithub(token, html)
