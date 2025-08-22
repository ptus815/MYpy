import re
import json
import sys
import time
import random
from urllib.parse import urljoin, urlparse, parse_qs
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
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        self.headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
        
        self.session = requests.Session()
        self.session.proxies.update(self.proxies)
        self.session.headers.update(self.headers)
        
        # 视频托管平台识别器
        self.video_platforms = {
            'dood': self.parseDoodStream,
            'streamtape': self.parseStreamtape,
            'streamsb': self.parseStreamSB,
            'streamlare': self.parseStreamlare,
            'vido': self.parseVido,
            'mp4upload': self.parseMp4Upload,
            'direct': self.parseDirect
        }

    def getRandomUserAgent(self):
        """获取随机User-Agent"""
        return random.choice(self.user_agents)

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
            # 模拟真实浏览器访问
            headers = self.headers.copy()
            headers['User-Agent'] = self.getRandomUserAgent()
            headers['Referer'] = self.host
            
            response = self.session.get(url, headers=headers, timeout=30)
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
                    
                    # 时长信息
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
            
            # 模拟真实浏览器访问
            headers = self.headers.copy()
            headers['User-Agent'] = self.getRandomUserAgent()
            headers['Referer'] = self.host
            
            response = self.session.get(url, headers=headers, timeout=30)
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
            
            # 只提取 iframe 地址（不直接拼 DoodStream 链接）
            video_urls = []
            
            # 方法1：PyQuery查找iframe
            for iframe in doc('iframe[src]').items():
                src = iframe.attr('src')
                if src and 'http' in src:
                    platform = self.identifyPlatform(src)
                    video_urls.append(f"{platform}${self.e64(src)}")
            
            # 方法2：正则匹配iframe（兜底）
            if not video_urls:
                iframe_pattern = r'<iframe[^>]*src=["\']([^"\']+)["\'][^>]*>'
                matches = re.findall(iframe_pattern, html, re.IGNORECASE)
                for match in matches:
                    if match and 'http' in match:
                        platform = self.identifyPlatform(match)
                        video_urls.append(f"{platform}${self.e64(match)}")
            
            # 方法3：查找其他视频嵌入（如embed标签）
            if not video_urls:
                embed_pattern = r'<embed[^>]*src=["\']([^"\']+)["\'][^>]*>'
                matches = re.findall(embed_pattern, html, re.IGNORECASE)
                for match in matches:
                    if match and 'http' in match:
                        platform = self.identifyPlatform(match)
                        video_urls.append(f"{platform}${self.e64(match)}")
            
            # 兜底：如果没有找到任何iframe，使用页面URL
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



    def identifyPlatform(self, url):
        """识别视频托管平台 - 使用精确的正向匹配规则"""
        url_lower = url.lower()
        
        # DoodStream 相关域名
        if any(domain in url_lower for domain in ['d-s.io', 'doodstream.com', 'dood.li', 'dood.wf', 'dood.pm', 'd000d.com']):
            return 'DoodStream'
        
        # Streamtape
        elif 'streamtape.com' in url_lower:
            return 'Streamtape'
        
        # StreamSB
        elif 'streamsb.net' in url_lower:
            return 'StreamSB'
        
        # Streamlare
        elif 'streamlare.com' in url_lower:
            return 'Streamlare'
        
        # Vido
        elif 'vido.co' in url_lower:
            return 'Vido'
        
        # Mp4Upload
        elif 'mp4upload.com' in url_lower:
            return 'Mp4Upload'
        
        # 直链视频文件
        elif any(ext in url_lower for ext in ['.mp4', '.m3u8', '.ts', '.avi', '.mkv']):
            return 'Direct'
        
        # 其他CDN直链
        elif any(cdn in url_lower for cdn in ['cloudatacdn.com', 'doodcdn.com', 'dood.stream']):
            return 'Direct'
        
        # 默认
        else:
            return 'Default'

    def searchContent(self, key, quick, pg="1"):
        try:
            url = f"{self.host}/"
            params = {'s': key}
            
            headers = self.headers.copy()
            headers['User-Agent'] = self.getRandomUserAgent()
            headers['Referer'] = self.host
            
            response = self.session.get(url, params=params, headers=headers, timeout=30)
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
            
            # 取出 iframe_url，传给对应的解析器
            if platform == 'DoodStream':
                return self.parseDoodStream(video_id, flag)
            elif platform == 'Streamtape':
                return self.parseStreamtape(video_id, flag)
            elif platform == 'StreamSB':
                return self.parseStreamSB(video_id, flag)
            elif platform == 'Streamlare':
                return self.parseStreamlare(video_id, flag)
            elif platform == 'Vido':
                return self.parseVido(video_id, flag)
            elif platform == 'Mp4Upload':
                return self.parseMp4Upload(video_id, flag)
            elif platform == 'Direct':
                return self.parseDirect(video_id, flag)
            else:
                return self.parseDefaultVideo(video_id, flag)
                
        except Exception as e:
            self.log(f"播放器内容获取失败: {str(e)}")
            return {'parse': 0, 'url': '', 'header': self.headers}

    def parseDoodStream(self, embed_url, referer=""):
        """解析 DoodStream - 完整处理 dood 的跳转链拿 mp4"""
        try:
            parsed = urlparse(embed_url)
            origin = f"{parsed.scheme}://{parsed.netloc}"
            
            # 构建完整的浏览器请求头
            headers = {
                'User-Agent': self.getRandomUserAgent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'cross-site',
                'Referer': referer or self.host,
                'Origin': self.host,
                'Cache-Control': 'max-age=0'
            }
            
            # 第一步：访问 embed 页面
            r0 = self.session.get(embed_url, headers=headers, timeout=30)
            r0.raise_for_status()
            html = r0.text
            
            # 提取视频代码
            code = ''
            mcode = re.search(r'/[ed]/([a-zA-Z0-9]+)', embed_url)
            if mcode:
                code = mcode.group(1)
            
            # 尝试多种方法获取直链（按优先级排序）
            methods = [
                lambda: self._tryPassMd5(origin, code, html, headers),
                lambda: self._tryDirectDownload(origin, code, html, headers),
                lambda: self._tryPageDirectLinks(html, headers),
                lambda: self._tryDomainFallback(code, headers),
                lambda: self._tryEmbedPageAnalysis(embed_url, html, headers)
            ]
            
            for method in methods:
                try:
                    result = method()
                    if result and result.get('parse') == 0:
                        self.log(f"DoodStream解析成功: {result['url']}")
                        return result
                except Exception as e:
                    self.log(f"DoodStream解析方法失败: {str(e)}")
                    continue
            
            # 兜底：返回 embed 让上游处理
            self.log(f"DoodStream解析失败，返回embed: {embed_url}")
            return {'parse': 1, 'url': embed_url, 'header': headers}
            
        except Exception as e:
            self.log(f"DoodStream解析失败: {str(e)}")
            headers = self.headers.copy()
            headers['Referer'] = referer or self.host
            return {'parse': 1, 'url': embed_url, 'header': headers}

    def _tryPassMd5(self, origin, code, html, headers):
        """尝试 pass_md5 方法"""
        if not code:
            return None
            
        # 查找 pass_md5 路径
        mpass = re.search(r"/pass_md5/([a-zA-Z0-9]+)", html)
        if not mpass:
            mpass = re.search(r"/pass_md5/" + re.escape(code), html)
        
        if mpass:
            pass_md5_path = mpass.group(0)
            jump_url = f"{origin}{pass_md5_path}"
            
            # 先尝试 HEAD 请求
            try:
                r1 = self.session.head(jump_url, headers=headers, allow_redirects=False, timeout=20)
                loc = r1.headers.get('Location')
                if loc:
                    return {'parse': 0, 'url': loc, 'header': headers}
            except:
                pass
            
            # 再尝试 GET 请求
            try:
                r1 = self.session.get(jump_url, headers=headers, allow_redirects=False, timeout=20)
                loc = r1.headers.get('Location')
                if loc:
                    return {'parse': 0, 'url': loc, 'header': headers}
            except:
                pass
            
            # 最后尝试跟随重定向
            try:
                r1 = self.session.get(jump_url, headers=headers, allow_redirects=True, timeout=20)
                if r1.url and r1.url != jump_url and 'http' in r1.url:
                    return {'parse': 0, 'url': r1.url, 'header': headers}
            except:
                pass
        
        return None

    def _tryDirectDownload(self, origin, code, html, headers):
        """尝试直接下载链接"""
        if not code:
            return None
            
        # 尝试 /d/<code>
        d_url = f"{origin}/d/{code}"
        try:
            r2 = self.session.get(d_url, headers=headers, allow_redirects=False, timeout=20)
            loc = r2.headers.get('Location')
            if loc:
                return {'parse': 0, 'url': loc, 'header': headers}
        except:
            pass
        
        # 尝试 /download/
        md = re.search(r"/download/[^\"']+", html)
        if md:
            durl = f"{origin}{md.group(0)}"
            try:
                r2a = self.session.head(durl, headers=headers, allow_redirects=False, timeout=20)
                loc = r2a.headers.get('Location')
                if loc:
                    return {'parse': 0, 'url': loc, 'header': headers}
            except:
                pass
        
        return None

    def _tryPageDirectLinks(self, html, headers):
        """尝试从页面源码提取直链"""
        patterns = [
            r'https://[^"\']*\.cloudatacdn\.com/[^"\']*',
            r'https://[^"\']*\.doodcdn\.com/[^"\']*',
            r'https://[^"\']*\.dood\.stream/[^"\']*'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html)
            if matches:
                return {'parse': 0, 'url': matches[0], 'header': headers}
        
        return None

    def _tryDomainFallback(self, code, headers):
        """尝试域名回退"""
        if not code:
            return None
            
        fallback_hosts = [
            'https://dood.li', 'https://dood.wf', 'https://dood.pm', 
            'https://doodstream.com', 'https://d000d.com'
        ]
        
        for host in fallback_hosts:
            try:
                r3 = self.session.get(f"{host}/d/{code}", headers=headers, allow_redirects=False, timeout=15)
                loc = r3.headers.get('Location')
                if loc:
                    return {'parse': 0, 'url': loc, 'header': headers}
            except:
                continue
        
        return None

    def _tryEmbedPageAnalysis(self, embed_url, html, headers):
        """分析 embed 页面，寻找隐藏的播放信息"""
        try:
            # 查找 JavaScript 中的播放信息
            js_patterns = [
                r'file\s*:\s*["\']([^"\']+)["\']',
                r'source\s*:\s*["\']([^"\']+)["\']',
                r'url\s*:\s*["\']([^"\']+)["\']'
            ]
            
            for pattern in js_patterns:
                matches = re.findall(pattern, html)
                for match in matches:
                    if match and ('http' in match) and any(ext in match.lower() for ext in ['.mp4', '.m3u8']):
                        return {'parse': 0, 'url': match, 'header': headers}
        except:
            pass
        
        return None

    def parseStreamtape(self, embed_url, referer=""):
        """解析 Streamtape"""
        try:
            # 提取视频ID
            video_id = re.search(r'/e/([a-zA-Z0-9]+)', embed_url)
            if video_id:
                video_id = video_id.group(1)
                # 构建直链
                direct_url = f"https://streamtape.com/get_video?id={video_id}"
                headers = self.headers.copy()
                headers['Referer'] = referer or self.host
                return {'parse': 0, 'url': direct_url, 'header': headers}
        except:
            pass
        
        return {'parse': 1, 'url': embed_url, 'header': self.headers}

    def parseStreamSB(self, embed_url, referer=""):
        """解析 StreamSB"""
        try:
            # 提取视频ID
            video_id = re.search(r'/e/([a-zA-Z0-9]+)', embed_url)
            if video_id:
                video_id = video_id.group(1)
                # 构建直链
                direct_url = f"https://streamsb.net/play/{video_id}/"
                headers = self.headers.copy()
                headers['Referer'] = referer or self.host
                return {'parse': 0, 'url': direct_url, 'header': headers}
        except:
            pass
        
        return {'parse': 1, 'url': embed_url, 'header': self.headers}

    def parseStreamlare(self, embed_url, referer=""):
        """解析 Streamlare"""
        try:
            # 提取视频ID
            video_id = re.search(r'/e/([a-zA-Z0-9]+)', embed_url)
            if video_id:
                video_id = video_id.group(1)
                # 构建直链
                direct_url = f"https://streamlare.com/e/{video_id}"
                headers = self.headers.copy()
                headers['Referer'] = referer or self.host
                return {'parse': 0, 'url': direct_url, 'header': headers}
        except:
            pass
        
        return {'parse': 1, 'url': embed_url, 'header': self.headers}

    def parseVido(self, embed_url, referer=""):
        """解析 Vido"""
        try:
            # 提取视频ID
            video_id = re.search(r'/v/([a-zA-Z0-9]+)', embed_url)
            if video_id:
                video_id = video_id.group(1)
                # 构建直链
                direct_url = f"https://vido.co/v/{video_id}"
                headers = self.headers.copy()
                headers['Referer'] = referer or self.host
                return {'parse': 0, 'url': direct_url, 'header': headers}
        except:
            pass
        
        return {'parse': 1, 'url': embed_url, 'header': self.headers}

    def parseMp4Upload(self, embed_url, referer=""):
        """解析 Mp4Upload"""
        try:
            # 提取视频ID
            video_id = re.search(r'/embed/([a-zA-Z0-9]+)', embed_url)
            if video_id:
                video_id = video_id.group(1)
                # 构建直链
                direct_url = f"https://mp4upload.com/embed/{video_id}"
                headers = self.headers.copy()
                headers['Referer'] = referer or self.host
                return {'parse': 0, 'url': direct_url, 'header': headers}
        except:
            pass
        
        return {'parse': 1, 'url': embed_url, 'header': self.headers}

    def parseDirect(self, url, referer=""):
        """解析直链"""
        headers = self.headers.copy()
        headers['Referer'] = referer or self.host
        return {'parse': 0, 'url': url, 'header': headers}

    def parseDefaultVideo(self, page_url, referer=""):
        """解析默认页面中的视频"""
        try:
            headers = self.headers.copy()
            headers['User-Agent'] = self.getRandomUserAgent()
            headers['Referer'] = referer or self.host
            
            r = self.session.get(page_url, headers=headers, timeout=30)
            r.raise_for_status()
            html = r.text
            
            # 尝试发现各种视频平台
            for platform_name, platform_parser in self.video_platforms.items():
                if platform_name == 'direct':
                    continue
                    
                # 查找对应的嵌入链接
                if platform_name == 'dood':
                    pattern = r'https://d-s\.io/e/[a-zA-Z0-9]+'
                elif platform_name == 'streamtape':
                    pattern = r'https://streamtape\.com/e/[a-zA-Z0-9]+'
                elif platform_name == 'streamsb':
                    pattern = r'https://streamsb\.net/e/[a-zA-Z0-9]+'
                elif platform_name == 'streamlare':
                    pattern = r'https://streamlare\.com/e/[a-zA-Z0-9]+'
                elif platform_name == 'vido':
                    pattern = r'https://vido\.co/v/[a-zA-Z0-9]+'
                elif platform_name == 'mp4upload':
                    pattern = r'https://mp4upload\.com/embed/[a-zA-Z0-9]+'
                else:
                    continue
                
                match = re.search(pattern, html)
                if match:
                    return platform_parser(match.group(), referer)
            
            # 查找直链
            for pattern in [
                r'https://[^"\']*\.cloudatacdn\.com/[^"\']*',
                r'https://[^"\']*\.doodcdn\.com/[^"\']*',
                r'https://[^"\']*\.mp4[^"\']*',
                r'https://[^"\']*\.m3u8[^"\']*'
            ]:
                matches = re.findall(pattern, html)
                if matches:
                    return self.parseDirect(matches[0], referer)
            
            return {'parse': 1, 'url': page_url, 'header': headers}
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
            headers = self.headers.copy()
            headers['User-Agent'] = self.getRandomUserAgent()
            
            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # 避免编码问题，直接用字节解码
            try:
                content = response.content.decode('utf-8', errors='ignore')
            except Exception:
                content = response.text
            
            # 处理相对路径
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
            headers = self.headers.copy()
            headers['User-Agent'] = self.getRandomUserAgent()
            
            response = self.session.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            return [200, response.headers.get('Content-Type', 'video/mp4'), response.content]
        except Exception as e:
            self.log(f"MP4代理失败: {str(e)}")
            return [500, "text/plain", f"Error: {str(e)}"]

    def proxyDefault(self, url):
        """默认代理处理"""
        try:
            headers = self.headers.copy()
            headers['User-Agent'] = self.getRandomUserAgent()
            
            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', 'application/octet-stream')
            return [200, content_type, response.content]
        except Exception as e:
            self.log(f"默认代理失败: {str(e)}")
            return [500, "text/plain", f"Error: {str(e)}"]


