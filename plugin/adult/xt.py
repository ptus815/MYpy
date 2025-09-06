# -*- coding: utf-8 -*-
# by @嗷嗷嗷fan
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
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh,zh-CN;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': "Android"
            
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
    
    def update_cookies(self):
        
        try:
            
            resp = self.session.get(self.host, timeout=15)
            if resp.status_code == 200:
                
                cf_cookie = resp.cookies.get('cf_clearance')
                if cf_cookie:
                    self.session.cookies.set('cf_clearance', cf_cookie)
                    print("Cookie更新成功")
                    return True
                else:
                    print("未找到cf_clearance cookie")
            else:
                print(f"获取Cookie失败，状态码: {resp.status_code}")
        except Exception as e:
            print(f"更新Cookie失败: {e}")
        return False

    def getpq(self, path=''):
        url = path if path.startswith('http') else self.host + path
        
        try:
            # 设置Referer
            headers = self.headers.copy()
            if path and not path.startswith('http'):
                if path == '/':
                    headers['Referer'] = self.host
                else:
                    headers['Referer'] = self.host + path
            
            
            self.session.headers.update(headers)
            
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
        
        
        ad_domains = ['cam4.com', 'landers.cam4.com', 'juicyads.com', 'adultfriendfinder.com', 
                     'livejasmin.com', 'chaturbate.com', 'myfreecams.com', 'stripchat.com',
                     'kimmy.faduz.xyz', 'kra.timbuk.online', 'ava.lazumi.online', 'wa.astorix.online']
        if any(domain in url.lower() for domain in ad_domains):
            return False
        
        
        ad_paths = ['/ads/', '/ad/', '/banner/', '/sponsor/', '/promo/', '/affiliate/', 
                   '/click/', '/track/', '/redirect/']
        if any(path in url.lower() for path in ad_paths):
            return False
        
        
        if url.startswith('http') and self.host not in url:
            
            trusted_domains = ['youtube.com', 'vimeo.com', 'dailymotion.com', '74k.io', '88z.io']
            if not any(domain in url.lower() for domain in trusted_domains):
                return False
        
        return True

    def getlist(self, selector):
        vlist = []
        for i in selector.items():
            try:
                
                if i('iframe').length > 0 or 'Ad' in i.text() or 'ad' in i.text():
                    continue
                
                
                if not i('img').length or not i('a').length:
                    continue
                
                
                link_elem = i('a').eq(0)
                if not link_elem:
                    continue
                vod_url = link_elem.attr('href').strip()
                vod_name = link_elem.text().strip()
                if not vod_url or not vod_name:
                    continue
                
                
                if not self.is_valid_video_url(vod_url):
                    continue
                
               
                if len(vod_name) < 5:
                    continue
                
                
                ad_keywords = ['ad', 'advertisement', 'sponsored', 'promo', 'banner', 'click here', 'visit now']
                if any(keyword in vod_name.lower() for keyword in ad_keywords):
                    continue
                
                
                img_elem = i('img').eq(0)
                if img_elem:
                    
                    vod_pic = (img_elem.attr('src') or 
                              img_elem.attr('data-src') or 
                              img_elem.attr('data-original') or 
                              img_elem.attr('data-thumb') or 
                              img_elem.attr('data-lazy-src') or 
                              img_elem.attr('data-srcset') or '')
                    
                    
                    if not vod_pic and img_elem.attr('srcset'):
                        srcset = img_elem.attr('srcset')
                        if srcset:
                            
                            vod_pic = srcset.split(',')[0].split(' ')[0].strip()
                    
                    
                    if vod_pic and not vod_pic.startswith('http'):
                        vod_pic = urljoin(self.host, vod_pic)
                    
                    
                    if vod_pic:
                        ad_domains = ['cam4.com', 'landers.cam4.com', 'juicyads.com', 'adultfriendfinder.com']
                        if any(domain in vod_pic.lower() for domain in ad_domains):
                            vod_pic = ''
                else:
                    vod_pic = ''
                
                
    
                duration_elem = i('div').filter(lambda idx, elem: 
                    ':' in pq(elem).text() and 
                    len(pq(elem).text().strip()) <= 10 and
                    pq(elem).text().strip().count(':') >= 2
                ).eq(0)
                vod_remarks = duration_elem.text().strip() if duration_elem else ''
                
                
                rating_elem = i('div').filter(lambda idx, elem: 
                    pq(elem).text().strip().isdigit() and 
                    len(pq(elem).text().strip()) <= 3 and
                    int(pq(elem).text().strip()) <= 100
                ).eq(0)
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
        
        cateManual = {
            "最新": "/", 
            "Lucast": "/category/589476/",
            "Asian": "/category/asian-guys-porn/",
            "MEN": "/category/286935/",
            "MAP": "/category/742158/",
            "OF": "/category/621397/",
            "Full Movies": "/category/porn-movies-214660/",
            "父子": "/category/491618/",
            "ND": "/category/675418/"
        }
        classes = [{'type_name': k, 'type_id': v} for k, v in cateManual.items()]
        
        
        data = self.getpq('/')
        
        
        latest_videos = data('div:contains("Latest videos")').next('ul li')
        latest_movies = data('div:contains("Latest Movies")').next('ul li')
        
        vlist = []
        vlist.extend(self.getlist(latest_videos))
        vlist.extend(self.getlist(latest_movies))
        
        return {'class': classes, 'filters': {}, 'list': vlist}

    def categoryContent(self, tid, pg, filter, extend):
        
        pg_int = int(pg) if isinstance(pg, str) else pg
        url = self.host + tid + f'page/{pg_int}/' if pg_int > 1 else self.host + tid
        data = self.getpq(url)
        
        
        vlist = self.getlist(data('ul li'))
        
        return {'list': vlist, 'page': pg}

    def searchContent(self, key, quick, pg="1"):
        url = self.host + f'/search/{key}/page/{pg}/'
        data = self.getpq(url)
        
        
        vlist = self.getlist(data('ul li'))
        
        return {'list': vlist, 'page': pg}

    def detailContent(self, ids):
        url = b64decode(ids[0]).decode('utf-8')
        data = self.getpq(url)
        
        title = data('h1').text().strip()
        
        
        tags = [tag.text().strip() for tag in data('a[href*="/category/"]').items() if tag.text().strip()]

        
        iframe_src = ''
        iframes = data('#video-code iframe')
        
        for iframe in iframes.items():
            src = iframe.attr('src') or ''
            if src and ('74k.io' in src or '88z.io' in src):
                iframe_src = src
                break
        
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


