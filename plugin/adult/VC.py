# -*- coding: utf-8 -*-
# by @ao
import json
import sys
import re
from base64 import b64decode, b64encode
from urllib.parse import urlparse, urljoin
import requests
from pyquery import PyQuery as pq
from requests import Session
sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    def init(self, extend=""):
        try:
            self.proxies = json.loads(extend) if extend else {}
        except:
            self.proxies = {}
        if isinstance(self.proxies, dict) and 'proxy' in self.proxies:
            self.proxies = self.proxies['proxy']
        self.proxies = {k: f'http://{v}' if isinstance(v, str) and not v.startswith('http') else v for k, v in self.proxies.items()}

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.3,en;q=0.2',
        }

        self.host = "https://gayvidsclub.com"
        self.session = Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(self.proxies)

    def getName(self):
        return "GayVidsClub"

    def isVideoFormat(self, url):
        return '.m3u8' in url or '.mp4' in url

    def manualVideoCheck(self):
        return True

    def destroy(self):
        pass

    def getpq(self, path=''):
        url = path if path.startswith('http') else self.host + path
        try:
            resp = self.session.get(url, timeout=15)
            resp.encoding = 'utf-8' if resp.encoding == 'ISO-8859-1' else resp.encoding
            return pq(resp.text)
        except Exception as e:
            print(f"获取页面失败: {e}")
            return pq("")

    def getlist(self, selector):
        vlist = []
        for i in selector.items():
            try:
                link_elem = i('h3 a, h2 a, h1 a, .entry-title a').eq(0)
                if not link_elem:
                    continue
                vod_url = link_elem.attr('href').strip()
                vod_name = link_elem.text().strip()
                if not vod_url or not vod_name:
                    continue
                
                img_elem = i('figure img').eq(0)
                vod_pic = img_elem.attr('src') or img_elem.attr('data-src') or img_elem.attr('data-original') or img_elem.attr('data-thumb') or img_elem.attr('data-lazy-src') or ''
                if not vod_pic and img_elem.attr('srcset'):
                    vod_pic = img_elem.attr('srcset').split(',')[0].split(' ')[0]
                if vod_pic and not vod_pic.startswith('http'):
                    vod_pic = urljoin(self.host, vod_pic)
                
                # Extracting series name (if available) and date
                vod_year = next((line.strip() for line in i('figure').text().strip().split('\n') if line.strip() and not line.startswith('▶') and len(line) > 1), '')
                vod_remarks = i('time, .entry-meta a[href*="/202"], a[href*="/202"]').eq(0).text().strip() or i('time').attr('datetime', '').split('T')[0]
                
                vlist.append({
                    'vod_id': b64encode(vod_url.encode('utf-8')).decode('utf-8'),
                    'vod_name': vod_name,
                    'vod_pic': vod_pic,
                    'vod_year': vod_year,
                    'vod_remarks': vod_remarks,
                    'style': {'ratio': 1.33, 'type': 'rect'}
                })
            except Exception as e:
                print(f"解析视频信息失败: {e}")
        return vlist

    def homeContent(self, filter):
        cateManual = {
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
        classes = [{'type_name': k, 'type_id': v} for k, v in cateManual.items()]
        data = self.getpq('/all-gay-porn/')
        vlist = self.getlist(data('article'))
        if not vlist:  # RSS fallback
            try:
                rss = self.session.get(f'{self.host}/feed', timeout=15).text
                d = pq(rss)
                vlist = [{'vod_id': b64encode(it('link').text().strip().encode('utf-8')).decode('utf-8'),
                          'vod_name': it('title').text().strip(),
                          'vod_pic': re.search(r'<img[^>]+src=["\']([^"\']+)["\']', it('description').text() or '', re.I).group(1) if re.search(r'<img[^>]+src=["\']([^"\']+)["\']', it('description').text() or '', re.I) else '',
                          'vod_year': '',
                          'vod_remarks': '',
                          'style': {'ratio': 1.33, 'type': 'rect'}} for it in d('item').items() if it('link').text().strip() and it('title').text().strip()]
            except Exception as e:
                print(f'RSS解析失败: {e}')
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

    def detailContent(self, ids):
        url = b64decode(ids[0]).decode('utf-8')
        data = self.getpq(url)
        
        title = data('h1').text().strip()
        info_text = data('.entry-meta, .post-meta').text().strip() or ''
        views_text = data('text:contains("views")').parent().text().strip() or ''
        tags = [tag.text().strip() for tag in data('.entry-tags a, .post-tags a, a[href*="/tag/"]').items() if tag.text().strip()]

        iframe_src = data('iframe').attr('src') or ''
        if not iframe_src:
            for attr in ['data-src', 'data-frame', 'data-iframe']:
                iframe_src = data(f'[{attr}]').attr(attr) or ''
                if iframe_src:
                    break
        if not iframe_src:
            scripts = data('script')
            for script in scripts.items():
                script_text = script.text()
                if script_text and 'iframe' in script_text and 'src' in script_text:
                    iframe_match = re.search(r'iframe.*?src=["\'](https?://[^"\']+mivalyo\.com[^"\']*)["\']', script_text, re.I)
                    if iframe_match:
                        iframe_src = iframe_match.group(1)
                        break
        if not iframe_src.startswith('http'):
            iframe_src = urljoin(self.host, iframe_src)

        vod_play_url = b64encode(iframe_src.encode('utf-8')).decode('utf-8')
        vod_content = ' | '.join(filter(None, [f"信息: {info_text}" if info_text else '', f"观看: {views_text}" if views_text else '', f"标签: {', '.join(tags)}" if tags else '']))

        vod = {
            'vod_name': title,
            'vod_content': vod_content,
            'vod_tag': ', '.join(tags) if tags else "GayVidsClub",
            'vod_play_from': 'Push',
            'vod_play_url': f'播放${vod_play_url}'
        }
        return {'list': [vod]}

    def playerContent(self, flag, id, vipFlags):
        play_url = b64decode(id.encode('utf-8')).decode('utf-8')
        return {
            'parse': 1,
            'url': play_url,
            'header': {
                'User-Agent': self.headers['User-Agent'],
                'Referer': self.host
            }
        }

