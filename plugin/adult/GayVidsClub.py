# -*- coding: utf-8 -*-
import json
from urllib.parse import urljoin
from base64 import b64encode, b64decode
from pyquery import PyQuery as pq
from requests import Session
from base.spider import Spider

class GayVidsPushSpider(Spider):
    def init(self, extend=""):
        self.host = "https://gayvidsclub.com"
        self.session = Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.proxies = {}
        try:
            self.proxies = json.loads(extend) if extend else {}
        except:
            pass
        if 'proxy' in self.proxies:
            self.proxies = self.proxies['proxy']

        # 静态分类
        self.cateManual = {
            "最新": "/all-gay-porn/",
            "COAT": "/all-gay-porn/coat/",
            "MEN'S RUSH.TV": "/all-gay-porn/mens-rush-tv/",
            "HUNK CHANNEL": "/all-gay-porn/hunk-channel/",
            "KO": "/all-gay-porn/ko/",
            "EXFEED": "/all-gay-porn/exfeed/",
            "BRAVO!": "/all-gay-porn/bravo/",
            "STR8BOYS": "/all-gay-porn/str8boys/",
            "G-BOT": "/all-gay-porn/g-bot/"
        }

    def getName(self):
        return "GayVidsClub-Push"

    def getpq(self, path=''):
        url = path if path.startswith('http') else self.host + path
        try:
            resp = self.session.get(url, timeout=15)
            resp.encoding = 'utf-8' if resp.encoding == 'ISO-8859-1' else resp.encoding
            return pq(resp.text)
        except Exception as e:
            print(f"获取页面失败: {e}")
            return pq("")

    # 视频列表解析，直接生成 Base64 ID
    def get_video_list(self, selector):
        vlist = []
        for i in selector.items():
            try:
                link_elem = i('h3 a, h2 a, h1 a, .entry-title a').eq(0)
                vod_url = link_elem.attr('href').strip()
                vod_name = link_elem.text().strip()
                if not vod_url or not vod_name:
                    continue
                img_elem = i('figure img').eq(0)
                vod_pic = img_elem.attr('src') or img_elem.attr('data-src') or ''
                if vod_pic and not vod_pic.startswith('http'):
                    vod_pic = urljoin(self.host, vod_pic)
                vod_year = next((line.strip() for line in i('figure').text().split('\n') if line.strip()), '')
                vod_remarks = i('time').eq(0).text().strip() or ''

                # Base64 ID，格式：video_url@@@@video_url
                vod_id = b64encode(f"{vod_url}@@@@{vod_url}".encode('utf-8')).decode('utf-8')

                vlist.append({
                    'vod_id': vod_id,
                    'vod_name': vod_name,
                    'vod_pic': vod_pic,
                    'vod_year': vod_year,
                    'vod_remarks': vod_remarks,
                    'style': {'ratio': 1.33, 'type': 'rect'}
                })
            except Exception as e:
                print(f"解析视频失败: {e}")
        return vlist

    # 提取 iframe src
    def extract_iframe_src(self, data):
        iframe_src = data('iframe').attr('src') or ''
        if not iframe_src:
            for attr in ['data-src', 'data-frame', 'data-iframe']:
                iframe_src = data(f'[{attr}]').attr(attr) or ''
                if iframe_src:
                    break
        if iframe_src and not iframe_src.startswith('http'):
            iframe_src = urljoin(self.host, iframe_src)
        return iframe_src

    # 调用 Push Spider
    def forward_to_push(self, video_url):
        try:
            from catvod_api import call_spider
            return call_spider('csp_Push', 'detailContent', [video_url])
        except Exception as e:
            print(f"调用 Push Spider 失败: {e}")
            return {
                "list": [{
                    "vod_name": "无法解析",
                    "vod_play_from": "直连",
                    "vod_play_url": video_url
                }]
            }

    # -------------------- Spider 接口 --------------------
    def homeContent(self, filter):
        classes = [{'type_name': k, 'type_id': v} for k, v in self.cateManual.items()]
        # 首页最新视频
        data = self.getpq('/all-gay-porn/')
        vlist = self.get_video_list(data('article'))
        return {'class': classes, 'filters': {}, 'list': vlist}

    def categoryContent(self, tid, pg, filter, extend):
        url = tid if pg == 1 else f"{tid}page/{pg}/"
        data = self.getpq(url)
        vlist = self.get_video_list(data('article'))
        return {'page': pg, 'pagecount': 9999, 'limit': 90, 'total': 999999, 'list': vlist}

    def detailContent(self, ids):
        video_url = b64decode(ids[0].encode('utf-8')).decode('utf-8').split('@@@@')[0]
        data = self.getpq(video_url)
        title = data('h1').text().strip() or '无标题'
        iframe_src = self.extract_iframe_src(data)
        play_url = iframe_src if iframe_src else video_url
        vod_json = self.forward_to_push(play_url)
        if 'list' in vod_json and len(vod_json['list']) > 0:
            vod_json['list'][0]['vod_name'] = title
        return vod_json

    def searchContent(self, key, quick, pg="1"):
        url = f"/?s={key}" if pg == "1" else f"/page/{pg}/?s={key}"
        data = self.getpq(url)
        vlist = self.get_video_list(data('article'))
        return {'list': vlist, 'page': pg}

    def playerContent(self, flag, id, vipFlags):
        try:
            ids = b64decode(id.encode('utf-8')).decode('utf-8').split('@@@@')
            play_url = ids[0]
            referer_url = ids[1] if len(ids) > 1 else ids[0]
            return {
                'parse': 1,
                'url': play_url,
                'header': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0',
                    'Referer': referer_url,
                    'Origin': self.host,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                    'Connection': 'keep-alive'
                }
            }
        except Exception as e:
            print(f"playerContent解析失败: {e}")
            return {'parse': 1, 'url': id, 'header': {}}
