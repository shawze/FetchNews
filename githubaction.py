# -*- coding: utf-8 -*-
# ! /usr/bin/env python3
import base64
import json
import re
import sys
# import time
from datetime import datetime,timedelta
from pprint import pprint

import requests
from lxml import etree


class HotBrand():
    def __init__(self):
        self.fetch_time = ''
        self.fetch_date_xwlb = ''
        self.fetch_time_format()
        self.weibo_url = 'https://s.weibo.com/top/summary?cate=realtimehot'
        self.toutiao_url = 'https://i.snssdk.com/hot-event/hot-board/?origin=hot_board'
        # https://tv.cctv.com/lm/xwlb/day/20210930.shtml
        self.xwlb_url = 'https://tv.cctv.com/lm/xwlb/day/{}.shtml'.format(self.fetch_date_xwlb)
        self.cctv_news_url = 'https://news.cctv.com/2019/07/gaiban/cmsdatainterface/page/news_{}.jsonp?cb=news'
        self.financial_news_url = 'http://news.10jqka.com.cn/today_list/index_{}.shtml'

    def fetch_time_format(self):
        """
        时间设置
        :return: None
        """
        BJ_time = datetime.utcnow() + timedelta(hours=8)
        self.fetch_time = BJ_time.strftime('%m-%d %H:%M')

        # 新闻联播抓取时间
        # 20210930
        if BJ_time.hour >= 21:
            self.fetch_date_xwlb = BJ_time.strftime('%Y%m%d')
        else:
            self.fetch_date_xwlb = (BJ_time-timedelta(days=1)).strftime('%Y%m%d')


    def fetch(self):
        data = [
            self.parse_toutiao(),
            self.parse_weibo(),
            self.parse_cctv_news()[:50],
            self.parse_financial_news()[:50],
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
        html = html.replace('头条区域', data_html_text[0])
        html = html.replace('微博区域', data_html_text[1])
        html = html.replace('央视新闻区域', data_html_text[2])
        html = html.replace('财经新闻区域', data_html_text[3])
        html = html.replace('新闻联播区域', data_html_text[4])
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
            'Cookie': 'SUB=_2AkMWCTBqf8NxqwJRmP0dzGLmaolzzw3EieKgVcGxJRMxHRl-yT8XqmIitRB6PYkehQJbgKCcusIBKCMrPlXZW_0Qq9oF; SUBP=0033WrSXqPxfM72-Ws9jqgMF55529P9D9WWqv.W8UUACrx_BC4a1bScG; _s_tentry=passport.weibo.com; Apache=2762088243906.36.1633009501527; SINAGLOBAL=2762088243906.36.1633009501527; ULV=1633009501533:1:1:1:2762088243906.36.1633009501527:; WBStorage=6ff1c79b|undefined',
            'DNT': '1',
            'Host': 's.weibo.com',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        }
        resp = requests.get(self.weibo_url, headers=header)
        # resp = requests.get(self.weibo_url)
        # print(resp.text)
        resp_html = etree.HTML(resp.text)
        if resp_html != '':
            # selector_id = resp_html.xpath('//td[@class="td-01 ranktop"]/text()')
            selector_title = resp_html.xpath('//td[@class="td-02"]/a/text()')
            selector_url = resp_html.xpath('//td[@class="td-02"]/a/@href')
            selector_hot_value = resp_html.xpath('//td[@class="td-02"]/span/text()')
            selector_type = resp_html.xpath('//td[@class="td-03"]/i/text()')
            selector_id = max(len(selector_title), len(selector_url), len(selector_hot_value))

            data = zip(range(1, selector_id + 1), selector_title, selector_url, selector_hot_value)
            data = list(data)

            data_lite = []
            for item in data:
                if 'void(0)' not in item[2]:
                    temp = {
                        'Id': int(item[0]),
                        'Title': item[1],
                        'Url': 'https://s.weibo.com' + item[2],
                        'HotValue': item[3],
                        'Site': '微博',
                    }
                    data_lite.append(temp)
            return data_lite

    def parse_cctv_news(self):
        data_lite_total = []
        urls = [self.cctv_news_url.format(i) for i in range(1, 3)]
        for url in urls:
            resp = requests.get(url)
            resp.encoding = resp.apparent_encoding
            resp_text = re.sub('^news\(', '', resp.text)
            resp_text = re.sub('\)$', '', resp_text)
            data_resp = json.loads(resp_text)
            if data_resp['data']['total'] > 0:
                data = data_resp['data']['list']
                # print(len(data))
                data_lite = [{
                    'Id': i + 1,
                    'Title': item['title'],
                    'Url': item['url'],
                    'HotValue': item['count'],
                    # 'Type': '',
                    'Site': '央视新闻',
                }
                    for i, item in enumerate(data)]
                data_lite_total += data_lite
        return data_lite_total

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
            selector_id = range(1, max(len(selector_title), len(selector_url)) + 1)

            # print(len(selector_title))
            # print(len(selector_url))
            # print(len(selector_id))

            data = zip(selector_id, selector_title, selector_url)
            data = list(data)
            data_lite = []
            for item in data:
                temp = {
                    'Id': int(item[0]),
                    'Title': item[1].replace('[视频]', ''),
                    'Url': item[2],
                    'HotValue': 0,
                    'Site': '新闻联播',
                }
                data_lite.append(temp)
            # pprint.pprint(data_lite)
            # print(data_lite)
            return data_lite

    def parse_financial_news(self):
        data_lite_total = []
        header = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/85.0.4183.121 Mobile Safari/537.36',
        }
        urls = [self.financial_news_url.format(i) for i in range(1, 6)]
        for url in urls:
            resp = requests.get(url, headers=header)
            resp.encoding = resp.apparent_encoding
            resp_html = etree.HTML(resp.text)
            # print(resp.text)
            if resp_html != '':
                selector_title = resp_html.xpath('//li/span/a/@title')
                selector_url = resp_html.xpath('//li/span/a/@href')
                selector_id = range(1, max(len(selector_title), len(selector_url)) + 1)
                # print(len(selector_title))
                # print(len(selector_url))
                # print(len(selector_id))
                data = zip(selector_id, selector_title, selector_url)
                data = list(data)
                data_lite = []
                for item in data:
                    temp = {
                        'Id': int(item[0]),
                        'Title': item[1],
                        'Url': item[2],
                        'HotValue': 0,
                        'Site': '财经新闻',
                    }
                    data_lite.append(temp)
                data_lite_total += data_lite
        return data_lite_total

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
        with open('hot.html', 'w', encoding='utf-8') as fb:
            fb.write(html)

    # hot_brand = HotBrand()
    # data = hot_brand.parse_weibo()
    # pprint(data)
