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
sys.path.append('../../')
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

        self.host = "https://asiangaylove.com"
        self.session = Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(self.proxies)

    def getName(self):
        return "AsianGayLove"

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
                
                img_elem = i('img').eq(0)
                vod_pic = img_elem.attr('src') or img_elem.attr('data-src') or img_elem.attr('data-original') or img_elem.attr('data-thumb') or img_elem.attr('data-lazy-src') or ''
                if not vod_pic and img_elem.attr('srcset'):
                    vod_pic = img_elem.attr('srcset').split(',')[0].split(' ')[0]
                if vod_pic and not vod_pic.startswith('http'):
                    vod_pic = urljoin(self.host, vod_pic)
                
                # 提取时长信息
                duration_elem = i('.post-sign, .duration')
                vod_remarks = duration_elem.text().strip() if duration_elem else ''
                
                # 提取分类信息
                cat_elem = i('.cat a')
                vod_year = cat_elem.text().strip() if cat_elem else ''
                
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
            "Asian": "/tag/asian/",
            "China": "/tag/china/",
            "Japan": "/tag/japan/",
            "OnlyFans": "/category/onlyfans/"
        }
        classes = [{'type_name': k, 'type_id': v} for k, v in cateManual.items()]
        
        # 获取首页最新内容
        data = self.getpq('/')
        vlist = self.getlist(data('.post'))
        
        # 为OnlyFans分类生成筛选器
        filters = {}
        if 'OnlyFans' in cateManual:
            filters['OnlyFans'] = {
                'Country': {
                    'name': 'Country',
                    'key': 't',
                    'value': [
                        {'v': '', 'n': 'All'},
                        {'v': '9', 'n': 'Asian'},
                        {'v': '20', 'n': 'Brazil'},
                        {'v': '14', 'n': 'China'},
                        {'v': '24', 'n': 'Colombia'},
                        {'v': '22', 'n': 'Hong Kong'},
                        {'v': '17', 'n': 'India'},
                        {'v': '25', 'n': 'Italy'},
                        {'v': '12', 'n': 'Japan'},
                        {'v': '19', 'n': 'Malaysia'},
                        {'v': '23', 'n': 'Netherlands'},
                        {'v': '18', 'n': 'Philippines'},
                        {'v': '21', 'n': 'Singapore'},
                        {'v': '13', 'n': 'South Korea'},
                        {'v': '8', 'n': 'Taiwan'},
                        {'v': '11', 'n': 'Thailand'},
                        {'v': '16', 'n': 'United Kingdom'},
                        {'v': '15', 'n': 'United States'},
                        {'v': '10', 'n': 'Vietnam'}
                    ]
                },
                'Sort': {
                    'name': 'Sort',
                    'key': 'o',
                    'value': [
                        {'v': '', 'n': 'Newest'},
                        {'v': 'update', 'n': 'Updated'},
                        {'v': 'recommend', 'n': 'Recommend'},
                        {'v': 'download', 'n': 'Download'},
                        {'v': 'view', 'n': 'Views'},
                        {'v': 'comment', 'n': 'Comments'},
                        {'v': 'rand', 'n': 'Random'}
                    ]
                }
            }
        
        return {'class': classes, 'filters': filters, 'list': vlist}

    def categoryContent(self, tid, pg, filter, extend):
        url = tid
        if pg > 1:
            if '/tag/' in tid:
                url = f"{tid}page/{pg}/"
            elif '/category/' in tid:
                url = f"{tid}page/{pg}/"
        
        # 处理筛选参数
        if filter and extend:
            params = []
            for key, value in extend.items():
                if value and value != '':
                    if key == 't':  # Country
                        params.append(f't={value}')
                    elif key == 'o':  # Sort
                        params.append(f'o={value}')
            
            if params:
                url += '?' + '&'.join(params)
        
        data = self.getpq(url)
        vlist = self.getlist(data('.post'))
        return {'page': pg, 'pagecount': 9999, 'limit': 90, 'total': 999999, 'list': vlist}

    def searchContent(self, key, quick, pg="1"):
        url = f"/?s={key}" if pg == "1" else f"/page/{pg}/?s={key}"
        data = self.getpq(url)
        vlist = self.getlist(data('.post'))
        return {'list': vlist, 'page': pg}

    def detailContent(self, ids):
        url = b64decode(ids[0]).decode('utf-8')
        data = self.getpq(url)
        
        title = data('.article-title').text().strip()
        if not title:
            title = data('h1').text().strip()
        
        # 提取视频播放器iframe
        iframe_src = data('.article-video iframe').attr('src') or ''
        if not iframe_src:
            iframe_src = data('iframe').attr('src') or ''
        
        # 提取图片
        img_elem = data('.single-images img').eq(0)
        vod_pic = img_elem.attr('src') or img_elem.attr('data-src') or ''
        if vod_pic and not vod_pic.startswith('http'):
            vod_pic = urljoin(self.host, vod_pic)
        
        # 提取时长
        duration_elem = data('.post-sign, .duration')
        vod_remarks = duration_elem.text().strip() if duration_elem else ''
        
        # 提取分类
        cat_elem = data('.cat a, .article-meta .item-cats a')
        vod_year = cat_elem.text().strip() if cat_elem else ''
        
        # 提取标签
        tags = [tag.text().strip() for tag in data('.article-tags a, .tag a').items() if tag.text().strip()]
        
        # 提取描述
        excerpt_elem = data('.excerpt')
        vod_content = excerpt_elem.text().strip() if excerpt_elem else ''
        
        vod_play_url = b64encode(iframe_src.encode('utf-8')).decode('utf-8')
        
        vod = {
            'vod_name': title,
            'vod_pic': vod_pic,
            'vod_year': vod_year,
            'vod_remarks': vod_remarks,
            'vod_content': vod_content,
            'vod_tag': ', '.join(tags) if tags else "AsianGayLove",
            'vod_play_from': 'AsianGayLove',
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

