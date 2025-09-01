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
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'document'
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
        for item in selector('.post.grid').items():
            try:
               
                title_elem = item('h3 a')
                vod_name = title_elem.text().strip()
                vod_url = title_elem.attr('href')
                
                if not vod_url or not vod_name:
                    continue
                
               
                vod_pic = ''
                
                
                img_elem = item('.img img')
                if img_elem:
                   
                    vod_pic = img_elem.attr('data-src') or img_elem.attr('src') or ''
                

                
                
                if vod_pic and not vod_pic.startswith('http'):
                    vod_pic = urljoin(self.host, vod_pic)
                
                
                if vod_pic and 'thumbnail.png' in vod_pic:
                    vod_pic = ''
                
                
                duration_elem = item('.post-sign')
                vod_remarks = duration_elem.text().strip() if duration_elem else ''
                
               
                cat_elem = item('.cat a')
                tag_elem = item('.tag a')
                
                if cat_elem:
                    vod_year = cat_elem.text().strip()
                    vod_tag = ''  
                elif tag_elem:
                    vod_year = ''  
                    vod_tag = tag_elem.text().strip()
                else:
                    vod_year = ''
                    vod_tag = ''
                
              
                time_elem = item('.time')
                vod_time = time_elem.text().strip() if time_elem else ''
                
                
                views_elem = item('.views')
                vod_views = views_elem.text().strip() if views_elem else ''
                
                downs_elem = item('.downs')
                vod_downs = downs_elem.text().strip() if downs_elem else ''
                
                
                vid = vod_url.split('/')[-2] if vod_url.endswith('/') else vod_url.split('/')[-1]
                
                vlist.append({
                    'vod_id': vid,
                    'vod_name': vod_name,
                    'vod_pic': vod_pic,
                    'vod_year': vod_year,
                    'vod_remarks': vod_remarks,
                    'vod_tag': vod_tag,
                    'vod_time': vod_time,
                    'vod_views': vod_views,
                    'vod_downs': vod_downs,
                    'style': {'ratio': 1.33, 'type': 'rect'}
                })
            except Exception as e:
                print(f"解析视频信息失败: {e}")
        return vlist

    def homeContent(self, filter):
        cateManual = {
            "首页": "/",
            "Asian": "/tag/asian/",
            "China": "/tag/china/",
            "Japan": "/tag/japan/",
            "OnlyFans": "/category/onlyfans/",
            "Gay Porn Video": "/category/gay-porn-video/",
            "Pornhub": "/category/pornhub/"
        }
        classes = [{'type_name': k, 'type_id': v} for k, v in cateManual.items()]
        
        
        data = self.getpq('/')
        vlist = self.getlist(data)
        
        return {'class': classes, 'list': vlist}

    def categoryContent(self, tid, pg, filter, extend):
        url = tid
        if int(pg) > 1:
            if '/tag/' in tid:
                url = f"{tid}page/{pg}/"
            elif '/category/' in tid:
                url = f"{tid}page/{pg}/"
        
        data = self.getpq(url)
        vlist = self.getlist(data)
        return {'page': pg, 'pagecount': 9999, 'limit': 90, 'total': 999999, 'list': vlist}

    def searchContent(self, key, quick, pg="1"):
        url = f"/?s={key}" if pg == "1" else f"/page/{pg}/?s={key}"
        data = self.getpq(url)
        vlist = self.getlist(data)
        return {'list': vlist, 'page': pg}

    def detailContent(self, ids):
        url = ids[0] if ids[0].startswith('http') else f"{self.host}/{ids[0]}/"
        data = self.getpq(url)
        
       
        title = data('.article-title').text().strip()
        if not title:
            title = data('h1').text().strip()
        
        
        img_elem = data('.single-images img').eq(0)
        vod_pic = img_elem.attr('src') or img_elem.attr('data-src') or ''
        if vod_pic and not vod_pic.startswith('http'):
            vod_pic = urljoin(self.host, vod_pic)
        
        
        duration_elem = data('.post-sign, .duration')
        vod_remarks = duration_elem.text().strip() if duration_elem else ''
        
       
        cat_elem = data('.cat a, .article-meta .item-cats a')
        tag_elem = data('.article-tags a, .tag a')
        
        if cat_elem:
            vod_year = cat_elem.text().strip()
            tags = []  
        elif tag_elem:
            vod_year = ''  
            tags = [tag.text().strip() for tag in tag_elem.items() if tag.text().strip()]
        else:
            vod_year = ''
            tags = []
        

        excerpt_elem = data('.excerpt')
        vod_content = excerpt_elem.text().strip() if excerpt_elem else ''
        
  
        iframe_src = data('.article-video iframe').attr('src') or ''
        if not iframe_src:
            iframe_src = data('iframe').attr('src') or ''
        if not iframe_src:
            
            iframe_src = data('.video-player iframe').attr('src') or ''
        if not iframe_src:
            iframe_src = data('.player iframe').attr('src') or ''
        
        
        if not iframe_src:
            play_btn = data('a[href*="player"], .play-btn, .watch-btn')
            if play_btn:
                iframe_src = play_btn.attr('href') or ''
        
       
        if not iframe_src:
            iframe_src = url
        
        vod = {
            'vod_name': title,
            'vod_pic': vod_pic,
            'vod_year': vod_year,
            'vod_remarks': vod_remarks,
            'vod_content': vod_content,
            'vod_tag': ', '.join(tags) if tags else "AsianGayLove",
            'vod_play_from': 'Push',
            'vod_play_url': f'播放${iframe_src}'
        }
        return {'list': [vod]}

    def playerContent(self, flag, id, vipFlags):
        
        try:
            if id.startswith('http'):
                play_url = id
            else:
                play_url = b64decode(id.encode('utf-8')).decode('utf-8')
        except:
            play_url = id
        
        return {
            'parse': 1,
            'url': play_url,
            'header': {
                'User-Agent': self.headers['User-Agent'],
                'Referer': self.host
            }
        }
