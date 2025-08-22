# -*- coding: utf-8 -*-
# by @AI Assistant
'''
GayCock4U 爬虫插件
支持视频分类、搜索、播放等功能
视频托管平台：DoodStream
'''
import re
import json
import sys
from urllib.parse import urljoin, urlparse
from base64 import b64encode, b64decode

import requests
from pyquery import PyQuery as pq
sys.path.append('..')
from base.spider import Spider


class Spider(Spider):

    def init(self, extend=""):
        try:
            self.proxies = json.loads(extend) if extend else {}
        except:
            self.proxies = {}
        
        self.host = "https://gaycock4u.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        self.session = requests.Session()
        self.session.proxies.update(self.proxies)
        self.session.headers.update(self.headers)

    def e64(self, text: str) -> str:
        try:
            return b64encode(text.encode('utf-8')).decode('utf-8')
        except Exception:
            return ''

    def d64(self, text: str) -> str:
        try:
            return b64decode(text.encode('utf-8')).decode('utf-8')
        except Exception:
            return ''

    def getName(self):
        return "GayCock4U"

    def isVideoFormat(self, url):
        if '.m3u8' in url or '.mp4' in url or '.ts' in url:
            return True
        return False

    def manualVideoCheck(self):
        return False

    def destroy(self):
        pass

    def homeContent(self, filter):
        result = {}
        classes = [
            {'type_name': 'Amateur', 'type_id': '/category/amateur/'},
            {'type_name': 'Bareback', 'type_id': '/category/bareback/'},
            {'type_name': 'Bear', 'type_id': '/category/bear/'},
            {'type_name': 'Big Cock', 'type_id': '/category/bigcock/'},
            {'type_name': 'Bisexual', 'type_id': '/category/bisexual/'},
            {'type_name': 'Black', 'type_id': '/category/black/'},
            {'type_name': 'Cumshot', 'type_id': '/category/cumshot/'},
            {'type_name': 'Daddy', 'type_id': '/category/daddy/'},
            {'type_name': 'Drag Race', 'type_id': '/category/drag-race/'},
            {'type_name': 'Fetish', 'type_id': '/category/fetish/'},
            {'type_name': 'Group', 'type_id': '/category/group/'},
            {'type_name': 'Hardcore', 'type_id': '/category/hardcore/'},
            {'type_name': 'Interracial', 'type_id': '/category/interracial/'},
            {'type_name': 'Latino', 'type_id': '/category/latino/'},
            {'type_name': 'Muscle', 'type_id': '/category/muscle/'},
            {'type_name': 'POV', 'type_id': '/category/pov/'},
            {'type_name': 'Solo', 'type_id': '/category/solo/'},
            {'type_name': 'Trans', 'type_id': '/category/trans/'},
            {'type_name': 'Twink', 'type_id': '/category/twink/'},
            {'type_name': 'Uniform', 'type_id': '/category/uniform/'}
        ]
        result['class'] = classes
        return result

    def homeVideoContent(self):
        return self.categoryContent('', '1', False, {})

    def categoryContent(self, tid, pg, filter, extend):
        result = {}
        result['page'] = pg
        result['pagecount'] = 9999
        result['limit'] = 90
        result['total'] = 999999
        
        if tid:
            if tid.startswith('http'):
                url = tid
            elif tid.startswith('/'):
                url = f"{self.host}{tid}"
            else:
                url = f"{self.host}/category/{tid}/"
            if pg != '1':
                if url.endswith('/'):
                    url = f"{url}page/{pg}/"
                else:
                    url = f"{url}/page/{pg}/"
        else:
            url = f"{self.host}/page/{pg}/" if pg != '1' else self.host
        
        try:
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            html = response.text
            doc = pq(html)
            
            videos = []
            articles = doc('article')
            
            for article in articles.items():
                try:
                    # 链接与标题
                    link = article('a').attr('href') or ''
                    if not link:
                        continue
                    
                    title = article('a').eq(0).text().strip() or article('img').attr('alt') or ''
                    if not title:
                        continue
                    
                    # 图片懒加载兼容
                    img_elem = article('img')
                    pic = img_elem.attr('src') or img_elem.attr('data-src') or img_elem.attr('data-lazy-src') or ''
                    if not pic:
                        srcset = img_elem.attr('srcset') or ''
                        if srcset:
                            pic = srcset.split(' ')[0]
                    
                    # 时长信息（尽力而为）
                    info_elem = article('.video-info, .video-duration, [class*="duration"]')
                    duration = info_elem.text().strip() if info_elem else ''
                    
                    videos.append({
                        'vod_id': link,
                        'vod_name': title,
                        'vod_pic': pic,
                        'vod_remarks': duration,
                        'vod_year': '',
                        'style': {'ratio': 1.33, 'type': 'rect'}
                    })
                except Exception as e:
                    self.log(f"解析视频项失败: {str(e)}")
                    continue
            
            result['list'] = videos
            
        except Exception as e:
            self.log(f"获取分类内容失败: {str(e)}")
            result['list'] = []
        
        return result

    def detailContent(self, ids):
        try:
            url = ids[0]
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            html = response.text
            doc = pq(html)
            
            # 标题：优先 og:title
            title = ''
            og_title = doc('meta[property="og:title"]').attr('content')
            if og_title:
                title = og_title.strip()
            if not title:
                title = (doc('h1, h2, h3').eq(0).text() or '').strip()
            if not title:
                title = doc('title').text().replace(' - GayCock4U', '').strip()
            
            # 海报：优先 og:image
            poster = doc('meta[property="og:image"]').attr('content') or ''
            if not poster:
                img_elem = doc('img[src*="cover"], img[src*="poster"], img[src*="thumb"]').eq(0)
                poster = img_elem.attr('src') or img_elem.attr('data-src') or ''
            
            # 分类
            category = ''
            category_elem = doc('a[href*="/category/"]').eq(0)
            if category_elem:
                category = category_elem.text().strip()
            
            # 演员
            actors = []
            for actor in doc('a[href*="/tag/"]').items():
                actor_text = actor.text().strip()
                if actor_text and len(actor_text) > 1:
                    actors.append(actor_text)
            
            # 工作室
            studio = ''
            studio_elem = doc('a[href*="/studio/"]').eq(0)
            if studio_elem:
                studio = studio_elem.text().strip()
            
            # 播放器 iframe（只收集 iframe 源地址，不直接返回直链）
            video_urls = []
            for iframe in doc('iframe[src]').items():
                src = iframe.attr('src')
                if not src:
                    continue
                if 'd-s.io' in src or 'dood' in src:
                    video_urls.append(f"DoodStream${self.e64(src)}")
            
            # 源码兜底（同样存为 DoodStream 平台 + base64 iframe 源）
            if not video_urls:
                for pattern in [
                    r'https://d-s\.io/e/[a-zA-Z0-9]+' ,
                    r'https://[^"\']*\.doodcdn\.com/[^"\']*',
                    r'https://[^"\']*\.cloudatacdn\.com/[^"\']*'
                ]:
                    m = re.findall(pattern, html)
                    if m:
                        for match in m:
                            if 'd-s.io' in match or 'dood' in match:
                                video_urls.append(f"DoodStream${self.e64(match)}")
                            else:
                                video_urls.append(f"Direct${self.e64(match)}")
                        break
            
            if not video_urls:
                video_urls.append(f"Default${self.e64(url)}")
            
            vod = {
                'vod_name': title,
                'vod_pic': poster,
                'vod_content': f"分类: {category}\n演员: {', '.join(actors)}\n工作室: {studio}",
                'vod_play_from': 'GayCock4U',
                'vod_play_url': '#'.join(video_urls)
            }
            
            return {'list': [vod]}
            
        except Exception as e:
            self.log(f"获取视频详情失败: {str(e)}")
            return {'list': []}

    def searchContent(self, key, quick, pg="1"):
        try:
            url = f"{self.host}/"
            params = {'s': key}
            
            response = self.session.get(url, params=params, timeout=20)
            response.raise_for_status()
            html = response.text
            doc = pq(html)
            
            videos = []
            articles = doc('article')
            
            for article in articles.items():
                try:
                    link = article('a').attr('href') or ''
                    title = (article('a').eq(0).text() or article('img').attr('alt') or '').strip()
                    if not link or not title:
                        continue
                    img_elem = article('img')
                    pic = img_elem.attr('src') or img_elem.attr('data-src') or img_elem.attr('data-lazy-src') or ''
                    if not pic:
                        srcset = img_elem.attr('srcset') or ''
                        if srcset:
                            pic = srcset.split(' ')[0]
                    videos.append({
                        'vod_id': link,
                        'vod_name': title,
                        'vod_pic': pic,
                        'vod_remarks': '',
                        'style': {'ratio': 1.33, 'type': 'rect'}
                    })
                except Exception:
                    continue
            
            result = {}
            result['list'] = videos
            result['page'] = pg
            result['pagecount'] = 9999
            result['limit'] = 90
            result['total'] = 999999
            
            return result
            
        except Exception as e:
            self.log(f"搜索失败: {str(e)}")
            return {'list': []}

    def playerContent(self, flag, id, vipFlags):
        try:
            if '$' in id:
                platform, payload = id.split('$', 1)
            else:
                platform, payload = 'Default', id
            
            # 解码 payload（detailContent 中已 base64）
            decoded = self.d64(payload)
            video_id = decoded if decoded else payload
            
            if platform == 'DoodStream':
                return self.parseDoodStream(video_id)
            elif platform == 'Direct':
                headers = self.headers.copy()
                if flag:
                    headers['Referer'] = flag
                return {'parse': 0, 'url': video_id, 'header': headers}
            else:
                return self.parseDefaultVideo(video_id)
                
        except Exception as e:
            self.log(f"播放器内容获取失败: {str(e)}")
            return {'parse': 0, 'url': '', 'header': self.headers}

    def parseDoodStream(self, embed_url: str):
        """解析 DoodStream：从 iframe/embed 页面提取 pass_md5 跳转并拿直链（带 Referer）"""
        try:
            headers = self.headers.copy()
            headers['Referer'] = embed_url
            r = self.session.get(embed_url, headers=headers, timeout=20)
            r.raise_for_status()
            html = r.text

            # 1) 优先查找 pass_md5 跳转接口
            m = re.search(r"/pass_md5/[^\"']+", html)
            if m:
                pass_md5_path = m.group(0)
                # 补全域名（使用 embed_url 的域）
                parsed = urlparse(embed_url)
                jump_url = f"{parsed.scheme}://{parsed.netloc}{pass_md5_path}"
                r2 = self.session.get(jump_url, headers=headers, allow_redirects=False, timeout=20)
                if 'Location' in r2.headers:
                    final_url = r2.headers['Location']
                    return {'parse': 0, 'url': final_url, 'header': headers}

            # 2) 兼容：部分页面直接内嵌 doodcdn/cloudatacdn 直链
            for pattern in [
                r'https://[^"\']*\.cloudatacdn\.com/[^"\']*',
                r'https://[^"\']*\.doodcdn\.com/[^"\']*',
                r'https://[^"\']*\.dood\.stream/[^"\']*'
            ]:
                mm = re.findall(pattern, html)
                if mm:
                    return {'parse': 0, 'url': mm[0], 'header': headers}

            # 3) 兜底：返回 embed 地址，由上游解析
            return {'parse': 1, 'url': embed_url, 'header': headers}
        except Exception as e:
            self.log(f"DoodStream解析失败: {str(e)}")
            headers = self.headers.copy()
            headers['Referer'] = embed_url
            return {'parse': 1, 'url': embed_url, 'header': headers}

    def parseDefaultVideo(self, page_url: str):
        """解析默认页面中的视频：尝试发现 dood 或直链"""
        try:
            r = self.session.get(page_url, timeout=20)
            r.raise_for_status()
            html = r.text
            if 'd-s.io' in html or 'dood' in html:
                dood_match = re.search(r'https://d-s\.io/e/[a-zA-Z0-9]+', html)
                if dood_match:
                    return self.parseDoodStream(dood_match.group())
            for pattern in [
                r'https://[^"\']*\.cloudatacdn\.com/[^"\']*',
                r'https://[^"\']*\.doodcdn\.com/[^"\']*',
                r'https://[^"\']*\.mp4[^"\']*',
                r'https://[^"\']*\.m3u8[^"\']*'
            ]:
                matches = re.findall(pattern, html)
                if matches:
                    return {'parse': 0, 'url': matches[0], 'header': self.headers}
            return {'parse': 1, 'url': page_url, 'header': self.headers}
        except Exception as e:
            self.log(f"默认视频解析失败: {str(e)}")
            return {'parse': 1, 'url': page_url, 'header': self.headers}

    def localProxy(self, param):
        """本地代理，用于处理视频流"""
        try:
            url = param.get('url', '')
            proxy_type = param.get('type', '')
            if not url:
                return None
            if proxy_type == 'm3u8':
                return self.proxyM3u8(url)
            elif proxy_type == 'mp4':
                return self.proxyMp4(url)
            else:
                return self.proxyDefault(url)
        except Exception as e:
            self.log(f"本地代理失败: {str(e)}")
            return None

    def proxyM3u8(self, url):
        """代理M3U8文件"""
        try:
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            # 避免编码问题，直接用字节解码
            try:
                content = response.content.decode('utf-8', errors='ignore')
            except Exception:
                content = response.text
            base_url = url[:url.rfind('/') + 1]
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line and not line.startswith('#') and not line.startswith('http'):
                    lines[i] = base_url + line
            content = '\n'.join(lines)
            return [200, "application/vnd.apple.mpegurl", content]
        except Exception as e:
            self.log(f"M3U8代理失败: {str(e)}")
            return [500, "text/plain", f"Error: {str(e)}"]

    def proxyMp4(self, url):
        """代理MP4文件"""
        try:
            response = self.session.get(url, stream=True, timeout=20)
            response.raise_for_status()
            return [200, response.headers.get('Content-Type', 'video/mp4'), response.content]
        except Exception as e:
            self.log(f"MP4代理失败: {str(e)}")
            return [500, "text/plain", f"Error: {str(e)}"]

    def proxyDefault(self, url):
        """默认代理处理"""
        try:
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', 'application/octet-stream')
            return [200, content_type, response.content]
        except Exception as e:
            self.log(f"默认代理失败: {str(e)}")
            return [500, "text/plain", f"Error: {str(e)}"]


