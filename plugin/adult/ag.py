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
                # 获取标题和链接
                title_elem = item('h3 a')
                vod_name = title_elem.text().strip()
                vod_url = title_elem.attr('href')
                
                if not vod_url or not vod_name:
                    continue
                
                # 改进图片获取逻辑
                vod_pic = ''
                
                # 方法1: 尝试获取 .img img 元素
                img_elem = item('.img img')
                if img_elem:
                    # 优先使用 data-src，因为它包含真实的图片URL（懒加载机制）
                    vod_pic = img_elem.attr('data-src') or img_elem.attr('src') or ''
                

                
                # 处理相对URL
                if vod_pic and not vod_pic.startswith('http'):
                    vod_pic = urljoin(self.host, vod_pic)
                
                # 过滤掉占位符图片
                if vod_pic and 'thumbnail.png' in vod_pic:
                    vod_pic = ''
                
                # 获取时长
                duration_elem = item('.post-sign')
                vod_remarks = duration_elem.text().strip() if duration_elem else ''
                
                # 获取分类或标签（优先显示分类，如果没有分类则显示标签）
                cat_elem = item('.cat a')
                tag_elem = item('.tag a')
                
                if cat_elem:
                    vod_year = cat_elem.text().strip()
                    vod_tag = ''  # 有分类时标签设为空
                elif tag_elem:
                    vod_year = ''  # 没有分类时分类设为空
                    vod_tag = tag_elem.text().strip()
                else:
                    vod_year = ''
                    vod_tag = ''
                

                
                # 提取视频ID
                vid = vod_url.split('/')[-2] if vod_url.endswith('/') else vod_url.split('/')[-1]
                
                vlist.append({
                    'vod_id': vid,
                    'vod_name': vod_name,
                    'vod_pic': vod_pic,
                    'vod_year': vod_year,
                    'vod_remarks': vod_remarks,
                    'vod_tag': vod_tag,
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
        
        # 获取首页最新内容
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
        
        # 获取标题
        title = data('.article-title').text().strip()
        if not title:
            title = data('h1').text().strip()
        
        # 获取图片
        img_elem = data('.single-images img').eq(0)
        vod_pic = img_elem.attr('src') or img_elem.attr('data-src') or ''
        if vod_pic and not vod_pic.startswith('http'):
            vod_pic = urljoin(self.host, vod_pic)
        
        # 获取时长
        duration_elem = data('.post-sign, .duration')
        vod_remarks = duration_elem.text().strip() if duration_elem else ''
        
        # 获取分类
        cat_elem = data('.cat a, .article-meta .item-cats a')
        if cat_elem:
            vod_year = cat_elem.text().strip()
        else:
            vod_year = ''
        
        # 获取标签
        tag_elem = data('.article-tags a, .tag a')
        if tag_elem:
            tags = [tag.text().strip() for tag in tag_elem.items() if tag.text().strip()]
        else:
            tags = []
        
        # 获取描述
        excerpt_elem = data('.excerpt')
        vod_content = excerpt_elem.text().strip() if excerpt_elem else ''
        
        # 获取播放器iframe的src链接
        iframe_src = data('.article-video iframe').attr('src') or data('iframe').attr('src') or url
        
        vod = {
            'vod_name': title,
            'vod_pic': vod_pic,
            'vod_year': vod_year,
            'vod_remarks': vod_remarks,
            'vod_content': vod_content,
            'vod_tag': ', '.join(tags) if tags else "",
            'vod_play_from': 'Push',
            'vod_play_url': f'播放${iframe_src}'
        }
        return {'list': [vod]}

    def playerContent(self, flag, id, vipFlags):
        # 如果id已经是URL，直接使用；如果是base64编码，则解码
        try:
            if id.startswith('http'):
                play_url = id
            else:
                play_url = b64decode(id.encode('utf-8')).decode('utf-8')
        except:
            play_url = id
        
        # 尝试解析混淆的JavaScript获取真实视频流
        m3u8_url = self.extract_m3u8_from_js(play_url)
        if m3u8_url:
            return {
                'parse': 0,  # 直接播放，不需要解析
                'url': m3u8_url,
                'header': {
                    'User-Agent': self.headers['User-Agent'],
                    'Referer': self.host
                }
            }
        
        return {
            'parse': 1,
            'url': play_url,
            'header': {
                'User-Agent': self.headers['User-Agent'],
                'Referer': self.host
            }
        }
    
    def extract_m3u8_from_js(self, iframe_url):
        """从混淆的JavaScript中提取.m3u8视频流地址"""
        try:
            # 获取iframe页面内容
            resp = self.session.get(iframe_url, timeout=15)
            if resp.status_code != 200:
                return None
            
            content = resp.text
            
            # 方法1: 直接查找.m3u8链接
            m3u8_pattern = r'https?://[^"\']*\.m3u8[^"\']*'
            m3u8_matches = re.findall(m3u8_pattern, content)
            
            if m3u8_matches:
                return m3u8_matches[0]
            
            # 方法2: 查找包含视频流信息的变量
            # 查找类似 "hls2": "..." 的模式
            hls_pattern = r'"hls\d+"\s*:\s*"([^"]*\.m3u8[^"]*)"'
            hls_match = re.search(hls_pattern, content)
            
            if hls_match:
                return hls_match.group(1)
            
            # 方法3: 查找混淆的JavaScript代码并尝试反混淆
            js_pattern = r'eval\(function\(p,a,c,k,e,d\)\{.*?\}\('
            js_match = re.search(js_pattern, content, re.DOTALL)
            
            if js_match:
                # 提取完整的混淆代码
                start_pos = js_match.start()
                # 查找eval函数的结束位置
                paren_count = 0
                end_pos = start_pos
                for i in range(start_pos, len(content)):
                    if content[i] == '(':
                        paren_count += 1
                    elif content[i] == ')':
                        paren_count -= 1
                        if paren_count == 0:
                            end_pos = i + 1
                            break
                
                if end_pos > start_pos:
                    obfuscated_js = content[start_pos:end_pos]
                    
                    # 尝试从混淆代码中提取.m3u8链接
                    m3u8_matches = re.findall(m3u8_pattern, obfuscated_js)
                    if m3u8_matches:
                        return m3u8_matches[0]
                    
                    # 尝试反混淆（基于您提供的模式）
                    # 查找包含premilkyway.com的链接
                    premilkyway_pattern = r'https?://[^"\']*premilkyway\.com[^"\']*\.m3u8[^"\']*'
                    premilkyway_match = re.search(premilkyway_pattern, obfuscated_js)
                    if premilkyway_match:
                        return premilkyway_match.group(0)
            
            # 方法4: 查找特定的视频流模式
            # 基于您提供的反混淆代码中的模式
            stream_patterns = [
                r'https?://[^"\']*\.premilkyway\.com[^"\']*\.m3u8[^"\']*',
                r'https?://[^"\']*\.dailyessence\.store[^"\']*\.m3u8[^"\']*',
                r'https?://[^"\']*62lcxnbxr456[^"\']*\.m3u8[^"\']*'
            ]
            
            for pattern in stream_patterns:
                match = re.search(pattern, content)
                if match:
                    return match.group(0)
            
            # 方法5: 尝试解析混淆代码中的links对象
            # 基于您提供的反混淆代码模式
            links_pattern = r'var\s+links\s*=\s*\{[^}]*"hls\d+"\s*:\s*"([^"]*\.m3u8[^"]*)"[^}]*\}'
            links_match = re.search(links_pattern, content, re.DOTALL)
            if links_match:
                return links_match.group(1)
            
            # 方法6: 查找包含特定参数的.m3u8链接
            # 基于您提供的反混淆代码中的参数模式
            param_pattern = r'https?://[^"\']*\.m3u8[^"\']*t=[^"\']*&s=[^"\']*&e=[^"\']*[^"\']*'
            param_match = re.search(param_pattern, content)
            if param_match:
                return param_match.group(0)
            
            return None
            
        except Exception as e:
            print(f"提取.m3u8链接失败: {e}")
            return None
