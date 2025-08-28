# -*- coding: utf-8 -*-
# by @ao
import json
import sys
import re
from base64 import b64decode, b64encode
from urllib.parse import urlparse, urljoin, quote, parse_qs
import requests
from pyquery import PyQuery as pq
from requests import Session
import execjs  # 需要安装: pip install pyexecjs
sys.path.append('..')
from base.spider import Spider

class Spider(Spider):

    def init(self, extend=""):
        try:
            self.proxies = json.loads(extend) if extend else {}
        except:
            self.proxies = {}
        # 支持 ext 传入 {"http":"...","https":"..."} 或 {"proxy": {"http":"...","https":"..."}}
        if isinstance(self.proxies, dict) and 'proxy' in self.proxies and isinstance(self.proxies['proxy'], dict):
            self.proxies = self.proxies['proxy']
        # 统一补全协议前缀
        fixed = {}
        for k, v in (self.proxies or {}).items():
            if isinstance(v, str) and not v.startswith('http'):
                fixed[k] = f'http://{v}'
            else:
                fixed[k] = v
        self.proxies = fixed
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.3,en;q=0.2',
            'Referer': 'https://gayvidsclub.com/',
        }
        self.host = "https://gayvidsclub.com"
        self.session = Session()
        # 更新headers中的origin和referer
        self.headers.update({
            'origin': self.host, 
            'referer': f'{self.host}/',
            'host': 'gayvidsclub.com'
        })
        self.session.proxies.update(self.proxies)
        self.session.headers.update(self.headers)
        
        # 初始化JavaScript执行环境
        try:
            self.ctx = execjs.compile("""
                function decodeBase64(str) {
                    return atob(str);
                }
                function encodeBase64(str) {
                    return btoa(str);
                }
            """)
        except:
            self.ctx = None
            print("JavaScript环境初始化失败，将使用纯Python解码")
        
        pass

    def getName(self):
        return "GayVidsClub"

    def isVideoFormat(self, url):
        return '.m3u8' in url or '.mp4' in url

    def manualVideoCheck(self):
        return True

    def destroy(self):
        pass

    def homeContent(self, filter):
        result = {}
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
        classes = []
        filters = {}
        for k in cateManual:
            classes.append({
                'type_name': k,
                'type_id': cateManual[k]
            })
        result['class'] = classes
        result['filters'] = filters
        return result

    def homeVideoContent(self):
        data = self.getpq()
        vlist = self.getlist(data("article"))
        if not vlist:
            # Fallback: 用分类页
            data = self.getpq('/all-gay-porn/')
            vlist = self.getlist(data("article"))
        return {'list': vlist}

    def categoryContent(self, tid, pg, filter, extend):
        vdata = []
        result = {}
        result['page'] = pg
        result['pagecount'] = 9999
        result['limit'] = 90
        result['total'] = 999999
        
        if pg == 1:
            url = tid
        else:
            url = f"{tid}page/{pg}/"
        
        data = self.getpq(url)
        vdata = self.getlist(data("article"))
        
        result['list'] = vdata
        return result

    def detailContent(self, ids):
        data = self.getpq(ids[0])
        
        # 获取视频标题
        title = data('h1').text().strip()
        
        # 获取视频信息
        info_text = ""
        meta_elem = data('.entry-meta, .post-meta')
        if meta_elem:
            info_text = meta_elem.text().strip()
        
        # 获取观看次数
        views_text = ""
        views_elem = data('text:contains("views")').parent()
        if views_elem:
            views_text = views_elem.text().strip()
        
        # 获取标签信息
        tags = []
        for tag in data('.entry-tags a, .post-tags a, a[href*="/tag/"]').items():
            tag_text = tag.text().strip()
            if tag_text and tag_text not in tags:
                tags.append(tag_text)
        
        # 获取iframe src
        iframe_src = ""
        iframe_elem = data('iframe')
        if iframe_elem:
            iframe_src = iframe_elem.attr('src') or ""
        
        # 如果没有找到iframe，尝试从JavaScript代码中提取
        if not iframe_src:
            scripts = data('script')
            for script in scripts.items():
                script_text = script.text()
                if script_text and 'iframe' in script_text:
                    # 尝试从JS中提取iframe URL
                    iframe_match = re.search(r'src=["\'](https?://[^"\']+mivalyo\.com[^"\']*)["\']', script_text, re.IGNORECASE)
                    if iframe_match:
                        iframe_src = iframe_match.group(1)
                        break
        
        # 确保URL完整
        if iframe_src and not iframe_src.startswith('http'):
            iframe_src = urljoin(self.host, iframe_src)
        
        # 构建详细信息
        content_parts = []
        if info_text:
            content_parts.append(f"信息: {info_text}")
        if views_text:
            content_parts.append(f"观看: {views_text}")
        if tags:
            content_parts.append(f"标签: {', '.join(tags)}")
        
        vod = {
            'vod_name': title,
            'vod_content': ' | '.join(content_parts) if content_parts else "GayVidsClub视频",
            'vod_tag': ', '.join(tags) if tags else "GayVidsClub",
            'vod_play_from': 'GayVidsClub',
            'vod_play_url': ''
        }
        
        # 构建播放地址
        play_urls = []
        if iframe_src:
            print(f"找到iframe URL: {iframe_src}")
            # 传递iframe URL给playerContent处理
            vod['vod_play_from'] = 'mivalyo'
            play_urls.append(f"播放${self.e64(iframe_src)}")
            vod['vod_play_url'] = '#'.join(play_urls)
        else:
            print("未找到iframe URL")
        
        return {'list': [vod]}

    def searchContent(self, key, quick, pg="1"):
        if pg == 1:
            url = f"/?s={key}"
        else:
            url = f"/page/{pg}/?s={key}"
        
        data = self.getpq(url)
        return {'list': self.getlist(data("article")), 'page': pg}

    def playerContent(self, flag, id, vipFlags):
        iframe_url = self.d64(id)
        
        # 请求iframe页面
        try:
            response = self.session.get(iframe_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0',
                'Referer': 'https://gayvidsclub.com/'
            }, timeout=15)
            
            iframe_html = response.text
            
            # 方法1: 直接搜索m3u8链接
            m3u8_matches = re.findall(r'https?://[^\s"\']+\.m3u8[^\s"\']*', iframe_html)
            if m3u8_matches:
                m3u8_url = m3u8_matches[0]
                print(f"直接找到m3u8 URL: {m3u8_url}")
                return self.return_m3u8(m3u8_url, iframe_url)
            
            # 方法2: 搜索base64编码的m3u8链接
            base64_matches = re.findall(r'["\']([A-Za-z0-9+/=]+)["\']', iframe_html)
            for match in base64_matches:
                try:
                    decoded = self.d64(match)
                    if '.m3u8' in decoded:
                        print(f"找到base64编码的m3u8 URL: {decoded}")
                        return self.return_m3u8(decoded, iframe_url)
                except:
                    continue
            
            # 方法3: 查找JavaScript变量中的m3u8链接
            js_matches = re.findall(r'(?:var|let|const)\s+[^=]+=\s*["\']([^"\']+\.m3u8[^"\']*)["\']', iframe_html)
            if js_matches:
                m3u8_url = js_matches[0]
                print(f"找到JS变量中的m3u8 URL: {m3u8_url}")
                return self.return_m3u8(m3u8_url, iframe_url)
            
            # 方法4: 尝试执行JavaScript代码提取链接
            script_matches = re.findall(r'<script[^>]*>(.*?)</script>', iframe_html, re.DOTALL)
            for script in script_matches:
                if '.m3u8' in script:
                    # 尝试提取JavaScript中的链接
                    url_matches = re.findall(r'https?://[^\s"\']+\.m3u8[^\s"\']*', script)
                    if url_matches:
                        m3u8_url = url_matches[0]
                        print(f"从JS脚本中找到m3u8 URL: {m3u8_url}")
                        return self.return_m3u8(m3u8_url, iframe_url)
                    
                    # 尝试提取base64编码的链接
                    base64_matches = re.findall(r'["\']([A-Za-z0-9+/=]{20,})["\']', script)
                    for match in base64_matches:
                        try:
                            decoded = self.d64(match)
                            if '.m3u8' in decoded:
                                print(f"从JS脚本中找到base64编码的m3u8 URL: {decoded}")
                                return self.return_m3u8(decoded, iframe_url)
                        except:
                            continue
            
            # 方法5: 尝试从常见的视频播放器配置中提取
            player_configs = re.findall(r'(?:player|video|source)[^=]+=[^\{]*(\{[^\}]+\})', iframe_html)
            for config in player_configs:
                if '.m3u8' in config:
                    url_matches = re.findall(r'"src"\s*:\s*"([^"]+\.m3u8[^"]*)"', config)
                    if url_matches:
                        m3u8_url = url_matches[0]
                        print(f"从播放器配置中找到m3u8 URL: {m3u8_url}")
                        return self.return_m3u8(m3u8_url, iframe_url)
        
        except Exception as e:
            print(f"解析iframe页面失败: {e}")
        
        # 如果所有方法都失败，返回空结果
        return {'parse': 0, 'url': ''}
    
    def return_m3u8(self, m3u8_url, iframe_url):
        """返回m3u8播放信息"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0',
            'Referer': iframe_url,
            'Origin': urlparse(iframe_url).netloc,
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        }
        
        return {'parse': 0, 'url': m3u8_url, 'header': headers}

    def localProxy(self, param):
        url = self.d64(param['url'])
        if param.get('type') == 'm3u8':
            return self.m3Proxy(url)
        else:
            return self.tsProxy(url)

    def e64(self, text):
        try:
            text_bytes = text.encode('utf-8')
            encoded_bytes = b64encode(text_bytes)
            return encoded_bytes.decode('utf-8')
        except Exception as e:
            print(f"Base64编码错误: {str(e)}")
            return ""

    def d64(self, encoded_text):
        try:
            # 如果使用JavaScript环境
            if self.ctx and len(encoded_text) % 4 == 0:  # 有效的base64长度
                try:
                    return self.ctx.call("decodeBase64", encoded_text)
                except:
                    pass
            
            # 回退到Python实现
            encoded_bytes = encoded_text.encode('utf-8')
            decoded_bytes = b64decode(encoded_bytes)
            return decoded_bytes.decode('utf-8')
        except Exception as e:
            print(f"Base64解码错误: {str(e)}")
            return ""

    def getlist(self, data):
        vlist = []
        for i in data.items():
            try:
                # 获取视频链接与标题
                link_elem = i('h3 a, h2 a, h1 a').eq(0)
                if not link_elem or len(link_elem) == 0:
                    # 某些卡片可能标题在 .entry-title
                    link_elem = i('.entry-title a').eq(0)
                if not link_elem:
                    continue
                vod_id = (link_elem.attr('href') or '').strip()
                if not vod_id:
                    continue
                vod_name = link_elem.text().strip()
                
                # 获取视频封面（兼容懒加载）
                img_elem = i('figure img').eq(0)
                vod_pic = ''
                if img_elem:
                    vod_pic = (img_elem.attr('src') or '').strip()
                    if not vod_pic:
                        for attr in ['data-src', 'data-original', 'data-thumb', 'data-lazy-src']:
                            vod_pic = (img_elem.attr(attr) or '').strip()
                            if vod_pic:
                                break
                    if not vod_pic:
                        # 从srcset取第一个url
                        srcset = (img_elem.attr('srcset') or '').strip()
                        if srcset:
                            vod_pic = srcset.split(',')[0].split(' ')[0]
                    if vod_pic and not vod_pic.startswith('http'):
                        vod_pic = urljoin(self.host, vod_pic)
                
                # 分类文本
                figure_text = i('figure').text()
                category_text = ''
                if figure_text:
                    lines = figure_text.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('▶') and len(line) > 1:
                            category_text = line
                            break
                vod_year = category_text
                
                # 发布时间
                vod_remarks = ''
                time_elem = i('time, .entry-meta a[href*="/202"], a[href*="/202"]').eq(0)
                if time_elem:
                    vod_remarks = (time_elem.text() or '').strip()
                if not vod_remarks:
                    # 尝试读取时间标签属性
                    t = i('time').attr('datetime')
                    if t:
                        vod_remarks = t.strip().split('T')[0]
                
                if vod_id and vod_name:
                    vlist.append({
                        'vod_id': vod_id,
                        'vod_name': vod_name,
                        'vod_pic': vod_pic,
                        'vod_year': vod_year,
                        'vod_remarks': vod_remarks,
                        'style': {'ratio': 1.33, 'type': 'rect'}
                    })
            except Exception as e:
                print(f"解析视频信息失败: {str(e)}")
                continue
        return vlist

    def getpq(self, path=''):
        h = '' if path.startswith('http') else self.host
        try:
            response = self.session.get(f'{h}{path}', timeout=15)
            # 自动处理编码
            if response.encoding == 'ISO-8859-1':
                response.encoding = 'utf-8'
            return pq(response.text)
        except Exception as e:
            print(f"获取页面失败: {str(e)}")
            return pq("")

    def m3Proxy(self, url):
        try:
            ydata = requests.get(url, headers=self.headers, proxies=self.proxies, allow_redirects=False, timeout=10)
            data = ydata.content.decode('utf-8')
            if ydata.headers.get('Location'):
                url = ydata.headers['Location']
                data = requests.get(url, headers=self.headers, proxies=self.proxies, timeout=10).content.decode('utf-8')
            
            lines = data.strip().split('\n')
            last_r = url[:url.rfind('/')]
            parsed_url = urlparse(url)
            durl = parsed_url.scheme + "://" + parsed_url.netloc
            
            for index, string in enumerate(lines):
                if '#EXT' not in string:
                    if 'http' not in string:
                        domain = last_r if string.count('/') < 2 else durl
                        string = domain + ('' if string.startswith('/') else '/') + string
                    lines[index] = self.proxy(string, string.split('.')[-1].split('?')[0])
            
            data = '\n'.join(lines)
            return [200, "application/vnd.apple.mpegurl", data]
        except Exception as e:
            print(f"M3U8代理失败: {str(e)}")
            return [500, "text/plain", f"Error: {str(e)}"]

    def tsProxy(self, url):
        try:
            data = requests.get(url, headers=self.headers, proxies=self.proxies, stream=True, timeout=10)
            return [200, data.headers.get('Content-Type', 'application/octet-stream'), data.content]
        except Exception as e:
            print(f"TS代理失败: {str(e)}")
            return [500, "text/plain", f"Error: {str(e)}"]

    def proxy(self, data, type='img'):
        if data and len(self.proxies):
            return f"{self.getProxyUrl()}&url={self.e64(data)}&type={type}"
        else:
            return data
