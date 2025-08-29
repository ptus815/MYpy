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
            'Referer': 'https://gay.xtapes.in/',
        }

        self.host = "https://gay.xtapes.in"
        self.session = Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(self.proxies)

    def getName(self):
        return "GayXTapes"

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
                # 查找视频链接和标题
                link_elem = i('a').eq(0)
                if not link_elem:
                    continue
                vod_url = link_elem.attr('href').strip()
                vod_name = link_elem.text().strip()
                if not vod_url or not vod_name:
                    continue
                
                # 查找图片
                img_elem = i('img').eq(0)
                vod_pic = img_elem.attr('src') or img_elem.attr('data-src') or img_elem.attr('data-original') or img_elem.attr('data-thumb') or img_elem.attr('data-lazy-src') or ''
                if not vod_pic and img_elem.attr('srcset'):
                    vod_pic = img_elem.attr('srcset').split(',')[0].split(' ')[0]
                if vod_pic and not vod_pic.startswith('http'):
                    vod_pic = urljoin(self.host, vod_pic)
                
                # 查找时长和评分
                duration_elem = i('text:contains(":")').parent()
                vod_remarks = ''
                if duration_elem:
                    duration_text = duration_elem.text().strip()
                    if ':' in duration_text:
                        vod_remarks = duration_text
                
                # 查找评分
                rating_elem = i('text:contains("%")').parent()
                vod_year = ''
                if rating_elem:
                    rating_text = rating_elem.text().strip()
                    if '%' in rating_text:
                        vod_year = rating_text
                
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
        # 基于网站分析，创建分类
        cateManual = {
            "最新": "/",
            "Lucas": "/category/589476/",
            "MEN": "/category/286935/",
            "MAP": "/category/742158/",
            "Asian": "/category/asian-guys-porn/",
            "OnlyFans": "/category/621397/",
            "Full Movies": "/category/porn-movies-214660/"
          
        }
        classes = [{'type_name': k, 'type_id': v} for k, v in cateManual.items()]
        
        # 获取首页视频列表
        data = self.getpq('/')
        vlist = self.getlist(data('li'))
        
        # 如果没有找到视频，尝试其他选择器
        if not vlist:
            vlist = self.getlist(data('article'))
        if not vlist:
            vlist = self.getlist(data('.list li'))
        
        return {'class': classes, 'filters': {}, 'list': vlist}

    def categoryContent(self, tid, pg, filter, extend):
        url = tid if pg == 1 else f"{tid}page/{pg}/"
        data = self.getpq(url)
        vlist = self.getlist(data('li'))
        
        # 如果没有找到视频，尝试其他选择器
        if not vlist:
            vlist = self.getlist(data('article'))
        if not vlist:
            vlist = self.getlist(data('.list li'))
        
        return {'page': pg, 'pagecount': 9999, 'limit': 90, 'total': 999999, 'list': vlist}

    def searchContent(self, key, quick, pg="1"):
        url = f"/?s={key}" if pg == "1" else f"/page/{pg}/?s={key}"
        data = self.getpq(url)
        vlist = self.getlist(data('li'))
        
        # 如果没有找到视频，尝试其他选择器
        if not vlist:
            vlist = self.getlist(data('article'))
        if not vlist:
            vlist = self.getlist(data('.list li'))
        
        return {'list': vlist, 'page': pg}

    def detailContent(self, ids):
        url = b64decode(ids[0]).decode('utf-8')
        data = self.getpq(url)
        
        # 获取标题
        title = data('h1').text().strip()
        if not title:
            title = data('title').text().strip().split(' - ')[0]
        
        # 获取视频信息
        info_text = data('.entry-meta, .post-meta').text().strip() or ''
        views_text = data('text:contains("views")').parent().text().strip() or ''
        
        # 获取标签
        tags = [tag.text().strip() for tag in data('a[href*="/category/"]').items() if tag.text().strip()]
        
        # 查找iframe播放器
        iframe_src = data('iframe').attr('src') or ''
        if not iframe_src:
            for attr in ['data-src', 'data-frame', 'data-iframe']:
                iframe_src = data(f'[{attr}]').attr(attr) or ''
                if iframe_src:
                    break
        
        # 如果没有找到iframe，尝试从脚本中提取
        if not iframe_src:
            scripts = data('script')
            for script in scripts.items():
                script_text = script.text()
                if script_text and 'iframe' in script_text and 'src' in script_text:
                    iframe_match = re.search(r'iframe.*?src=["\'](https?://[^"\']+)["\']', script_text, re.I)
                    if iframe_match:
                        iframe_src = iframe_match.group(1)
                        break
        
        # 确保URL是完整的
        if iframe_src and not iframe_src.startswith('http'):
            iframe_src = urljoin(self.host, iframe_src)
        
        vod_play_url = b64encode(iframe_src.encode('utf-8')).decode('utf-8') if iframe_src else ''
        vod_content = ' | '.join(filter(None, [f"信息: {info_text}" if info_text else '', f"观看: {views_text}" if views_text else '', f"标签: {', '.join(tags)}" if tags else '']))

        vod = {
            'vod_name': title,
            'vod_content': vod_content,
            'vod_tag': ', '.join(tags) if tags else "GayXTapes",
            'vod_play_from': 'Push',
            'vod_play_url': f'播放${vod_play_url}' if vod_play_url else ''
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