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
    
    def is_valid_video_url(self, url):
        """检查URL是否是有效的视频链接"""
        if not url:
            return False
        
        # 检查是否是广告域名
        ad_domains = ['cam4.com', 'landers.cam4.com', 'juicyads.com', 'adultfriendfinder.com', 
                     'livejasmin.com', 'chaturbate.com', 'myfreecams.com', 'stripchat.com']
        if any(domain in url.lower() for domain in ad_domains):
            return False
        
        # 检查是否是广告路径
        ad_paths = ['/ads/', '/ad/', '/banner/', '/sponsor/', '/promo/', '/affiliate/', 
                   '/click/', '/track/', '/redirect/']
        if any(path in url.lower() for path in ad_paths):
            return False
        
        # 检查是否是外部链接（非本站）
        if url.startswith('http') and self.host not in url:
            # 允许一些可信的外部视频域名
            trusted_domains = ['youtube.com', 'vimeo.com', 'dailymotion.com']
            if not any(domain in url.lower() for domain in trusted_domains):
                return False
        
        return True

    def getlist(self, selector):
        vlist = []
        for i in selector.items():
            try:
                # 过滤广告元素
                if i('iframe').length > 0 or 'Ad' in i.text() or 'ad' in i.text():
                    continue
                
                # 获取视频链接和标题
                link_elem = i('a').eq(0)
                if not link_elem:
                    continue
                vod_url = link_elem.attr('href').strip()
                vod_name = link_elem.text().strip()
                if not vod_url or not vod_name:
                    continue
                
                # 验证视频URL
                if not self.is_valid_video_url(vod_url):
                    continue
                
                # 过滤掉过短的标题（可能是广告）
                if len(vod_name) < 5:
                    continue
                
                # 过滤掉包含广告关键词的标题
                ad_keywords = ['ad', 'advertisement', 'sponsored', 'promo', 'banner', 'click here', 'visit now']
                if any(keyword in vod_name.lower() for keyword in ad_keywords):
                    continue
                
                # 获取图片
                img_elem = i('img').eq(0)
                vod_pic = img_elem.attr('src') or img_elem.attr('data-src') or img_elem.attr('data-original') or img_elem.attr('data-thumb') or img_elem.attr('data-lazy-src') or ''
                if not vod_pic and img_elem.attr('srcset'):
                    vod_pic = img_elem.attr('srcset').split(',')[0].split(' ')[0]
                if vod_pic and not vod_pic.startswith('http'):
                    vod_pic = urljoin(self.host, vod_pic)
                
                # 验证图片URL
                if vod_pic and not self.is_valid_video_url(vod_pic):
                    vod_pic = ''
                
                # 获取时长和评分
                duration_elem = i('div').filter(lambda idx, elem: ':' in pq(elem).text() and len(pq(elem).text().strip()) <= 10).eq(0)
                vod_remarks = duration_elem.text().strip() if duration_elem else ''
                
                # 获取评分
                rating_elem = i('div').filter(lambda idx, elem: pq(elem).text().strip().isdigit() and len(pq(elem).text().strip()) <= 5).eq(0)
                vod_year = rating_elem.text().strip() if rating_elem else ''
                
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
        # 根据截图中的实际分类信息
        cateManual = {
            "最新": "/", 
            "推荐": "/?filtre=popular",
            "Lucast": "/category/589476/",
            "Asian": "/category/asian-guys-porn/",
            "MEN": "/category/286935/",
            "MAP": "/category/742158/",
            "OF": "/category/621397/",
            "Full Movies": "/category/porn-movies-214660/",
            "Outdoor": "/category/outdoor/",
            "Big Dicks": "/category/big-dicks/"
        }
        classes = [{'type_name': k, 'type_id': v} for k, v in cateManual.items()]
        
        # 获取首页视频列表 - 只选择特定区域的视频
        data = self.getpq('/')
        # 选择 "Latest videos" 和 "Latest Movies" 区域的视频，排除广告
        latest_videos = data('div:contains("Latest videos")').next('ul li').not_(':contains("Ad")').not_(':contains("ad")')
        latest_movies = data('div:contains("Latest Movies")').next('ul li').not_(':contains("Ad")').not_(':contains("ad")')
        
        vlist = []
        vlist.extend(self.getlist(latest_videos))
        vlist.extend(self.getlist(latest_movies))
        
        return {'class': classes, 'filters': {}, 'list': vlist}

    def categoryContent(self, tid, pg, filter, extend):
        url = tid if pg == 1 else f"{tid}page/{pg}/"
        data = self.getpq(url)
        # 选择主要内容区域的视频列表
        vlist = self.getlist(data('ul li').not_(':contains("Ad")').not_(':contains("ad")'))
        return {'page': pg, 'pagecount': 9999, 'limit': 90, 'total': 999999, 'list': vlist}

    def searchContent(self, key, quick, pg="1"):
        url = f"/?s={key}" if pg == "1" else f"/page/{pg}/?s={key}"
        data = self.getpq(url)
        # 选择搜索结果区域的视频列表，排除广告
        vlist = self.getlist(data('ul li').not_(':contains("Ad")').not_(':contains("ad")'))
        return {'list': vlist, 'page': pg}

    def detailContent(self, ids):
        url = b64decode(ids[0]).decode('utf-8')
        data = self.getpq(url)
        
        title = data('h1').text().strip()
        
        # 获取标签
        tags = [tag.text().strip() for tag in data('a[href*="/category/"]').items() if tag.text().strip()]

        # 获取iframe播放器
        iframe_src = data('iframe').attr('src') or ''
        if not iframe_src:
            for attr in ['data-src', 'data-frame', 'data-iframe']:
                iframe_src = data(f'[{attr}]').attr(attr) or ''
                if iframe_src:
                    break
        
        if not iframe_src.startswith('http'):
            iframe_src = urljoin(self.host, iframe_src)

        vod_play_url = b64encode(iframe_src.encode('utf-8')).decode('utf-8')
        vod_content = f"标签: {', '.join(tags)}" if tags else "GayXTapes"

        vod = {
            'vod_name': title,
            'vod_content': vod_content,
            'vod_tag': ', '.join(tags) if tags else "GayXTapes",
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
