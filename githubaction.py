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
        self.fetch_time = ''
        self.fetch_date_xwlb = ''
        self.fetch_time_format()
        self.weibo_url = 'https://s.weibo.com/top/summary?cate=realtimehot'
        self.toutiao_url = 'https://i.snssdk.com/hot-event/hot-board/?origin=hot_board'
        self.xwlb_url = 'https://tv.cctv.com/lm/xwlb/day/{}.shtml'.format(self.fetch_date_xwlb)

    def fetch_time_format(self):
        time_utc = time.gmtime()
        time_utc_hour_now = (time_utc.tm_hour + 8) % 24
        time_utc_month_now = time.strftime('%m')
        time_utc_year_now = time.strftime('%Y')
        # 当前北京日期
        if (time_utc.tm_hour + 8) // 24 == 1:
            time_utc_day_now = str(int(time.strftime('%d')) + 1)
        else:
            time_utc_day_now = time.strftime('%d')
        time_BJ = time.strptime(f"{time_utc_hour_now}:{time_utc.tm_min}", "%H:%M")
        self.fetch_time = f'{time_utc_month_now}-{time_utc_day_now}  {time.strftime("%X", time_BJ)}'
        # 新闻联播抓取时间
        if time_utc_hour_now < 21:
            time_utc_day_now = int(time_utc_day_now) - 1
        time_utc_day_now = '{:0>2d}'.format(int(time_utc_day_now))
        self.fetch_date_xwlb = f'{time_utc_year_now}{time_utc_month_now}{time_utc_day_now}'
        # print(self.fetch_date_xwlb)

    def fetch(self):
        data = [
            self.parse_toutiao(),
            self.parse_weibo(),
            self.parse_xwlb(),
        ]
        return self.html_format(data)

    def html_format(self, data):
        data_html_text = []
        for data_item in data:
            data_html = []
            for i, item in enumerate(data_item):
                text = f'''\
                        <div class="container-fluid justify-content-start" style="height: 45px;font-size:20px;">
                            <a class="text-dark text-decoration-none" href="{item['Url']}">
                            <div class="row">
                                <div class="col-1 text-danger">{i + 1}</div>
                                <div class="col-11 text-truncate">{item['Title']}</div>
                            </div>
                            </a>
                        </div>
                        '''
                data_html.append(text)
            data_html_text.append(''.join(data_html))

        with open('template.html', 'r', encoding='utf-8') as fb:
            html = fb.read()
        html = html.replace('头条区域',data_html_text[0])
        html = html.replace('微博区域',data_html_text[1])
        html = html.replace('新闻联播区域',data_html_text[2])
        html = html.replace('更新时间', f'更新时间：{self.fetch_time}')
        # with open('hot.html','w',encoding='utf-8') as fb:
            # fb.write(html)
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

    def parse_xwlb(self):
        header = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/85.0.4183.121 Mobile Safari/537.36',
            'Referer': 'https://tv.cctv.com/lm/xwlb/'
        }
        resp = requests.get(self.xwlb_url, headers=header)
        resp.encoding = resp.apparent_encoding
        resp_html = etree.HTML(resp.text)
        # print(resp.text)
        if resp_html != '':
            selector_title = resp_html.xpath('//div[@class="title"]/text()')
            selector_url = resp_html.xpath('//li/a/@href')
            selector_id = range(1,max(len(selector_title),len(selector_url))+1)

            # print(len(selector_title))
            # print(len(selector_url))
            # print(len(selector_id))

            data = zip(selector_id, selector_title, selector_url)
            data = list(data)
            data_lite = []
            for item in data:
                temp = {
                    'Id': int(item[0]),
                    'Title': item[1].replace('[视频]',''),
                    'Url': item[2],
                    'HotValue': 0,
                    'Site': '新闻联播',
                }
                data_lite.append(temp)
            # pprint.pprint(data_lite)
        # print(data_lite)
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
    try:
        token = sys.argv[1]
    except:
        token = None
    # print(sys.argv)
    hot_brand = HotBrand()
    html = hot_brand.fetch()
    if token != None:
        hot_brand.uploadGithub(token, html)
    else:
        with open('hot.html','w',encoding='utf-8') as fb:
            fb.write(html)