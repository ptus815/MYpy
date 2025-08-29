# -*- coding: utf-8 -*-
import json
import sys
from base64 import b64encode, b64decode
from urllib.parse import urljoin
from pyquery import PyQuery as pq
from requests import Session
sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    def init(self, extend=""):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
        }
        self.host = "https://gayvidsclub.com"
        self.session = Session()
        self.session.headers.update(self.headers)
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
        except:
            return pq("")

    def getlist(self, selector):
        vlist = []
        for i in selector.items():
            link_elem = i('h3 a, h2 a, h1 a, .entry-title a').eq(0)
            if not link_elem:
                continue
            vod_url = link_elem.attr('href').strip()
            vod_name = link_elem.text().strip()
            if not vod_url or not vod_name:
                continue
            img_elem = i('figure img').eq(0)
            vod_pic = img_elem.attr('src') or img_elem.attr('data-src') or img_elem.attr('data-original') or ''
            if vod_pic and not vod_pic.startswith('http'):
                vod_pic = urljoin(self.host, vod_pic)
            vod_id = b64encode(vod_url.encode('utf-8')).decode('utf-8')
            vlist.append({
                'vod_id': vod_id,
                'vod_name': vod_name,
                'vod_pic': vod_pic,
                'vod_year': '',
                'vod_remarks': '',
                'style': {'ratio': 1.33, 'type': 'rect'}
            })
        return vlist

    def homeContent(self, filter):
        classes = [{'type_name': k, 'type_id': v} for k, v in self.cateManual.items()]
        data = self.getpq('/all-gay-porn/')
        vlist = self.getlist(data('article'))
        return {'class': classes, 'filters': {}, 'list': vlist}

    def categoryContent(self, tid, pg, filter, extend):
        url = tid if pg == 1 else f"{tid}page/{pg}/"
        data = self.getpq(url)
        vlist = self.getlist(data('article'))
        return {'page': pg, 'pagecount': 9999, 'limit': 90, 'total': 999999, 'list': vlist}

    def searchContent(self, key, quick, pg="1"):
        url = f"/?s={key}" if pg == "1" else f"/page/{pg}/?s={key}"
        data = self.getpq(url)
        vlist = self.getlist(data('article'))
        return {'list': vlist, 'page': pg}

    # 详情页直接拿 iframe src 或视频 URL，交给 Push Spider
    def detailContent(self, ids):
        url = b64decode(ids[0]).decode('utf-8')
        data = self.getpq(url)
        # 尝试多种 iframe 属性
        iframe_src = data('iframe').attr('src') or ''
        if not iframe_src:
            for attr in ['data-src', 'data-frame', 'data-iframe']:
                iframe_src = data(f'[{attr}]').attr(attr) or ''
                if iframe_src:
                    break
        if not iframe_src:
            iframe_src = url  # 没有找到 iframe，用页面 URL 本身
        if not iframe_src.startswith('http'):
            iframe_src = urljoin(self.host, iframe_src)

        vod = {
            'vod_name': data('h1').text().strip() or '无标题',
            'vod_tag': '',
            'vod_play_from': 'Push',
            'vod_play_url': f"播放${b64encode(iframe_src.encode('utf-8')).decode('utf-8')}"
        }
        return {'list':[vod]}

    # 播放页不解析，全部交给 Push Spider
    def playerContent(self, flag, id, vipFlags):
        play_url = b64decode(id.encode('utf-8')).decode('utf-8')
        return {'parse': 1, 'url': play_url, 'header': {'User-Agent': self.headers['User-Agent'], 'Referer': self.host}}
