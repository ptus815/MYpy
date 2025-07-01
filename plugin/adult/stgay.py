# coding=utf-8
# !/usr/bin/python
import json
import sys
import re
import time
import random
import urllib.parse
from base64 import b64decode, b64encode
from pyquery import PyQuery as pq
from requests import Session
import requests
sys.path.append('..')
from base.spider import Spider


class Spider(Spider):

    def init(self, extend=""):
        try:
            print("正在初始化stgay爬虫...")
            self.host = self.gethost()
            self.headers['referer'] = f'{self.host}/'
            
            # 设置更多的请求头，增强模拟真实浏览器
            self.session = Session()
            self.session.headers.update(self.headers)
            
            # 设置请求超时和重试次数
            self.timeout = 15
            self.retry_count = 3
            self.retry_delay = 2
            
            # 写入请求和爬取相关配置
            self.cacheTime = 86400  # 缓存过期时间，单位：秒
            
            print(f"初始化完成，使用主机地址: {self.host}")
        except Exception as e:
            print(f"初始化失败: {str(e)}")
        pass

    def getName(self):
        return "Stgay"

    def isVideoFormat(self, url):
        if re.match(r'.*(\.mp4|\.m3u8|\.flv).*', url):
            return True
        return False

    def manualVideoCheck(self):
        return True

    def destroy(self):
        try:
            self.session.close()
        except:
            pass

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
    }

    def fetch(self, url, headers=None):
        """
        获取网页内容，带有重试和随机延迟
        """
        print(f"开始请求页面: {url}")
        _headers = headers or self.headers
        
        # 重试逻辑
        for i in range(self.retry_count):
            try:
                # 随机延迟，避免请求过快
                if i > 0:
                    delay = self.retry_delay + random.uniform(0, 1)
                    print(f"第{i+1}次重试，延迟 {delay:.2f} 秒")
                    time.sleep(delay)
                
                # 发送请求
                response = self.session.get(url, headers=_headers, timeout=self.timeout)
                
                # 检查响应状态
                if response.status_code == 200:
                    html = response.text
                    print(f"请求成功，获取内容长度: {len(html)} 字符")
                    return html, response
                else:
                    print(f"请求返回错误状态码: {response.status_code}")
            except Exception as e:
                print(f"请求异常: {str(e)}")
        
        # 如果所有重试都失败
        print(f"所有重试都失败，无法获取页面: {url}")
        return "", None

    def homeContent(self, filter):
        result = {}
        cateManual = {
            "正在播放": "/视频/正在播放",
            "当前最热": "/视频/当前最热",
            "最近更新": "/视频/最近更新",
            "小蓝原创": "/视频/小蓝原创",
            "本月最热": "/视频/本月最热",
            "10分钟以上": "/视频/10分钟以上",
            "20分钟以上": "/视频/20分钟以上",
            "体育生": "/视频/search/体育生",
            "直男": "/视频/search/直男",
            "白袜": "/视频/search/白袜",
            "口交": "/视频/search/口交",
            "乱伦": "/视频/search/乱伦",
            "迷奸": "/视频/search/迷奸",
            "开火车": "/视频/search/开火车",
            "厕所": "/视频/search/厕所",
            "澡堂": "/视频/search/澡堂",
            "网黄": "/视频/search/网黄",
            "明星": "/视频/search/明星"
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
        print(f"获取首页视频内容")
        try:
            response = self.fetch_with_retry(f"{self.host}/视频/正在播放")
            html_text = response.text
            data = pq(html_text)
            vlist = self.getlist(data, html_text)
            if len(vlist) == 0:
                print("首页没有找到视频，尝试其他方法")
                # 尝试加载其他分类
                for cat in ["/视频/当前最热", "/视频/最近更新"]:
                    print(f"尝试获取分类: {cat}")
                    try:
                        response = self.fetch_with_retry(f"{self.host}{cat}")
                        html_text = response.text
                        data = pq(html_text)
                        vlist = self.getlist(data, html_text)
                        if len(vlist) > 0:
                            print(f"在分类{cat}中找到 {len(vlist)} 个视频")
                            break
                    except Exception as e:
                        print(f"加载分类{cat}失败: {str(e)}")
            
            print(f"首页找到 {len(vlist)} 个视频")
            return {'list': vlist}
        except Exception as e:
            print(f"加载首页内容失败: {str(e)}")
            return {'list': []}

    def categoryContent(self, tid, pg, filter, extend):
        """
        获取分类内容
        """
        print(f"获取分类内容: {tid}, 第{pg}页")
        result = {}
        
        # 处理页码，确保页码有效
        page = int(pg)
        if page < 1:
            page = 1
            
        # 构建分类页面URL
        url = f'{self.host}{tid}'
        if page > 1:
            url = f'{self.host}{tid}/{page}'
        
        print(f"访问分类页面: {url}")
        
        try:
            # 获取页面内容
            html_text, response = self.fetch(url)
            
            if not html_text:
                print("获取分类页面失败")
                return {"list": []}
                
            # 解析页面内容
            doc = pq(html_text)
            videos = self.getlist(doc, html_text)
            
            # 获取总页数
            total_page = 1
            try:
                # 查找分页信息
                page_info = doc('.pagination strong:contains("/")')
                if page_info:
                    page_text = page_info.text()
                    match = re.search(r'/\s*(\d+)', page_text)
                    if match:
                        total_page = int(match.group(1))
                # 如果没找到分页信息，尝试从URL查找
                else:
                    page_links = []
                    for a in doc('a').items():
                        href = a.attr('href')
                        if href and re.search(rf'{re.escape(tid)}/\d+$', href):
                            page_num_match = re.search(r'/(\d+)$', href)
                            if page_num_match:
                                page_links.append(int(page_num_match.group(1)))
                    if page_links:
                        total_page = max(page_links)
            except Exception as e:
                print(f"获取总页数时出错: {str(e)}")
            
            print(f"分类 {tid} 共有 {total_page} 页, 当前第 {page} 页, 找到 {len(videos)} 个视频")
            
            # 构建结果
            result['list'] = videos
            result['page'] = page
            result['pagecount'] = total_page
            result['limit'] = 20
            result['total'] = total_page * 20
            
        except Exception as e:
            print(f"处理分类内容时出错: {str(e)}")
            result = {"list": []}
            
        return result

    def detailContent(self, ids):
        """
        获取视频详情
        """
        print(f"获取视频详情: {ids[0]}")
        vod = {}
        aid = ids[0]
        
        # 构建详情页URL
        url = f'{self.host}{aid}'
        print(f"访问视频详情页: {url}")
        
        try:
            # 获取详情页内容
            html_text, response = self.fetch(url)
            
            if not html_text:
                print("获取视频详情页失败")
                return {}
                
            # 解析页面内容
            doc = pq(html_text)
            
            # 获取视频标题
            vod_name = ''
            title_elem = doc('h1.video-title')
            if title_elem:
                vod_name = title_elem.text().strip()
            
            # 如果没找到标题，尝试从URL提取
            if not vod_name:
                try:
                    parts = urllib.parse.unquote(aid).strip('/').split('/')
                    if len(parts) >= 2:
                        vod_name = parts[-2]  # 倒数第二个部分通常是标题
                except:
                    pass
            
            # 获取视频封面
            vod_pic = ''
            # 尝试多个可能的封面元素
            for img_selector in ['video-poster img', '.video-thumb img', '.video-cover img', '.video-image img', '.player-container img', 'video']:
                img = doc(img_selector)
                if img:
                    # 尝试获取src或poster属性
                    for attr in ['src', 'data-src', 'data-original', 'poster']:
                        pic = img.attr(attr)
                        if pic and not pic.endswith('poster_loading.png'):
                            vod_pic = pic
                            break
                    if vod_pic:
                        break
                        
            # 如果仍没找到封面，尝试从源代码中提取
            if not vod_pic:
                img_matches = re.finditer(r'<img[^>]*?(?:src|data-src|data-original|poster)=["\']([^"\']+\.(?:jpg|jpeg|png|gif|webp))["\']', html_text)
                for match in img_matches:
                    pic = match.group(1)
                    if pic and not ('logo' in pic.lower() or 'icon' in pic.lower() or pic.endswith('poster_loading.png')):
                        vod_pic = pic
                        break
            
            # 获取视频简介
            vod_content = ''
            desc_elem = doc('.video-description, .video-intro, .video-text')
            if desc_elem:
                vod_content = desc_elem.text().strip()
            
            # 获取视频标签
            vod_tags = []
            # 尝试获取标签元素
            for tag in doc('.video-tags a, .tag-list a, strong').items():
                tag_text = tag.text().strip()
                if tag_text and not tag_text.isdigit() and len(tag_text) < 10:
                    vod_tags.append(tag_text)
            
            # 获取播放地址
            play_url = self.extract_play_url(doc, html_text)
            
            # 如果没有找到播放地址，使用当前页面URL
            if not play_url:
                play_url = url
                
            # 使用base64编码处理播放地址
            play_url_enc = self.e64(play_url)
            
            # 构建详细信息
            vod = {
                "vod_id": aid,
                "vod_name": vod_name,
                "vod_pic": vod_pic,
                "type_name": "成人视频",
                "vod_year": "",
                "vod_area": "",
                "vod_remarks": "",
                "vod_actor": ", ".join(vod_tags) if vod_tags else "",
                "vod_director": "",
                "vod_content": vod_content
            }
            
            vod['vod_play_from'] = 'Stgay'
            vod['vod_play_url'] = f'播放$${play_url_enc}'
            
            print(f"成功获取视频详情: {vod_name}")
            
        except Exception as e:
            print(f"获取视频详情时出错: {str(e)}")
            return {}
            
        result = {
            'list': [vod]
        }
        return result

    def searchContent(self, key, quick, pg="1"):
        """
        搜索视频内容
        """
        print(f"搜索: {key}, 第{pg}页")
        result = {}
        
        # 构建搜索URL
        page = int(pg)
        if page < 1:
            page = 1
            
        search_url = f"{self.host}/视频/search/{urllib.parse.quote(key)}"
        if page > 1:
            search_url = f"{self.host}/视频/search/{urllib.parse.quote(key)}/{page}"
            
        print(f"搜索URL: {search_url}")
        
        try:
            # 获取搜索结果页面
            html_text, response = self.fetch(search_url)
            
            if not html_text:
                print("获取搜索页面失败")
                return {"list": []}
                
            # 解析搜索结果
            doc = pq(html_text)
            videos = self.getlist(doc, html_text)
            
            # 获取总页数
            total_page = 1
            try:
                # 查找分页信息
                page_info = doc('.pagination strong:contains("/")')
                if page_info:
                    page_text = page_info.text()
                    match = re.search(r'/\s*(\d+)', page_text)
                    if match:
                        total_page = int(match.group(1))
            except Exception as e:
                print(f"获取搜索总页数时出错: {str(e)}")
                
            print(f"搜索'{key}'共找到 {len(videos)} 个结果, 共 {total_page} 页")
            
            # 构建结果
            result['list'] = videos
            result['page'] = page
            result['pagecount'] = total_page
            result['limit'] = 20
            result['total'] = total_page * 20
        except Exception as e:
            print(f"搜索出错: {str(e)}")
            result = {"list": []}
            
        return result

    def playerContent(self, flag, id, vipFlags):
        """
        解析视频播放地址
        """
        print(f"解析播放地址: {id}")
        
        result = {}
        
        try:
            # 解码播放地址
            content = self.d64(id)
            
            # 如果是完整URL，直接返回
            if content.startswith('http'):
                url = content
                print(f"直接使用URL: {url}")
                
                # 构建结果
                result["parse"] = 0
                result["url"] = url
                result["header"] = self.headers
                
                return result
            
            # 如果是页面链接，需要进一步处理
            if content.startswith('/'):
                url = f"{self.host}{content}"
                print(f"页面链接: {url}")
                
                # 获取页面内容
                html_text, response = self.fetch(url)
                
                if not html_text:
                    print("获取视频页面失败")
                    return {}
                    
                # 解析视频源
                doc = pq(html_text)
                play_url = self.extract_play_url(doc, html_text)
                
                if play_url:
                    print(f"提取到播放地址: {play_url}")
                    result["parse"] = 0
                    result["url"] = play_url
                    result["header"] = self.headers
                else:
                    # 如果未找到视频源，尝试iframe方式播放
                    print("未找到直接播放源，使用页面方式播放")
                    result["parse"] = 1
                    result["url"] = url
                    result["header"] = self.headers
                
                return result
        
        except Exception as e:
            print(f"解析播放地址出错: {str(e)}")
            
        # 兜底返回，使用iframe播放
        print("使用默认解析播放")
        url = f"{self.host}{id}" if id.startswith('/') else id
        result["parse"] = 1
        result["url"] = url
        result["header"] = self.headers
        
        return result

    def localProxy(self, param):
        pass

    def gethost(self, source=''):
        """
        获取主机地址，支持从配置或环境中获取
        """
        if not source:
            source = 'https://stgay.com'
        return source.rstrip('/')

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
            encoded_bytes = encoded_text.encode('utf-8')
            decoded_bytes = b64decode(encoded_bytes)
            return decoded_bytes.decode('utf-8')
        except Exception as e:
            print(f"Base64解码错误: {str(e)}")
            return ""
            
    def extract_play_url(self, data, html_text):
        """
        从页面提取视频播放地址
        """
        print("尝试提取视频播放源")
        
        # 方法1: 从video元素提取
        video_element = data('video')
        if video_element:
            print("找到video元素")
            # 尝试从src属性获取
            video_src = video_element.attr('src')
            if video_src:
                print(f"从video.src获取播放源: {video_src}")
                return video_src
            
            # 尝试从source元素获取
            source = video_element.find('source')
            if source:
                src = source.attr('src')
                if src:
                    print(f"从video > source获取播放源: {src}")
                    return src
        
        # 方法2: 从JavaScript变量中提取
        print("尝试从JavaScript代码中提取URL")
        
        # 常见的视频URL变量模式
        url_patterns = [
            r'url\s*:\s*[\'"]([^\'"]+\.(?:mp4|m3u8).*?)[\'"]',
            r'src\s*:\s*[\'"]([^\'"]+\.(?:mp4|m3u8).*?)[\'"]',
            r'videoUrl\s*=\s*[\'"]([^\'"]+\.(?:mp4|m3u8).*?)[\'"]',
            r'video_url\s*=\s*[\'"]([^\'"]+\.(?:mp4|m3u8).*?)[\'"]',
            r'videoURL\s*=\s*[\'"]([^\'"]+\.(?:mp4|m3u8).*?)[\'"]',
            r'playbackURL\s*=\s*[\'"]([^\'"]+\.(?:mp4|m3u8).*?)[\'"]',
            r'playUrl\s*=\s*[\'"]([^\'"]+\.(?:mp4|m3u8).*?)[\'"]',
            r'play_url\s*=\s*[\'"]([^\'"]+\.(?:mp4|m3u8).*?)[\'"]'
        ]
        
        for pattern in url_patterns:
            match = re.search(pattern, html_text)
            if match:
                video_url = match.group(1)
                print(f"从JS变量中提取到URL: {video_url}")
                return video_url
        
        # 方法3: 搜索整个HTML中的媒体URL
        print("搜索HTML中的媒体URL")
        media_patterns = [
            r'[\'"]([^\'"\s]+\.mp4(?:\?[^\'"]*)?)[\'"]',
            r'[\'"]([^\'"\s]+\.m3u8(?:\?[^\'"]*)?)[\'"]',
            r'[\'"]([^\'"\s]+/m3u8/[^\'"]*)[\'"]',
            r'[\'"]([^\'"\s]+/mp4/[^\'"]*)[\'"]',
            r'[\'"]([^\'"\s]+/video/[^\'"]*\.(?:mp4|m3u8)(?:\?[^\'"]*)?)[\'"]'
        ]
        
        for pattern in media_patterns:
            matches = re.finditer(pattern, html_text)
            for match in matches:
                url = match.group(1)
                # 排除常见的非视频URL
                if 'logo' in url.lower() or 'thumbnail' in url.lower() or 'poster' in url.lower():
                    continue
                print(f"在HTML中找到媒体URL: {url}")
                return url
        
        # 方法4: 尝试从iframe中提取
        print("尝试从iframe中获取视频源")
        iframe = data('iframe')
        if iframe:
            iframe_src = iframe.attr('src')
            if iframe_src:
                print(f"找到iframe源: {iframe_src}")
                # 如果iframe源是相对路径，添加主机名
                if iframe_src.startswith('/'):
                    iframe_src = f"{self.host}{iframe_src}"
                return iframe_src
        
        # 方法5: 尝试解析加密的视频URL
        print("尝试解析可能的加密视频URL")
        try:
            # 查找可能包含加密URL的JavaScript代码
            crypto_patterns = [
                r'decodeURIComponent\(([^\)]+)\)',
                r'atob\(([^\)]+)\)',
                r'decode\([\'"]([^\'"]+)[\'"]\)',
                r'decrypt\([\'"]([^\'"]+)[\'"]\)'
            ]
            
            for pattern in crypto_patterns:
                match = re.search(pattern, html_text)
                if match:
                    encrypted = match.group(1).strip('\'"')
                    try:
                        # 尝试解码
                        if 'atob' in pattern:
                            import base64
                            decoded = base64.b64decode(encrypted).decode('utf-8')
                        else:
                            decoded = urllib.parse.unquote(encrypted)
                        
                        # 检查解码后的内容是否包含媒体URL
                        for media_pattern in media_patterns:
                            media_match = re.search(media_pattern, decoded)
                            if media_match:
                                url = media_match.group(1)
                                print(f"从加密数据中提取到URL: {url}")
                                return url
                    except:
                        pass
        except Exception as e:
            print(f"解析加密URL时出错: {str(e)}")
        
        # 如果所有方法都失败，返回页面URL作为兜底方案
        print("未找到视频源，将使用页面URL")
        return None
        
    def get_video_pic(self, data, html_text, url):
        """
        尝试多种方法获取视频封面
        """
        # 方法1: 从视频播放器获取封面
        video_img = data('.video-detail-player img').attr('src')
        if video_img and not video_img.endswith('poster_loading.png'):
            return video_img
            
        # 方法2: 从视频元素的poster属性获取
        video_poster = data('video').attr('poster')
        if video_poster:
            return video_poster
            
        # 方法3: 从页面中查找视频ID的图片
        try:
            video_id = url.split('/')[-1]
            for item in data('a[href*="' + video_id + '"]').items():
                img = item.find('img')
                if img:
                    img_src = img.attr('src') or img.attr('data-src')
                    if img_src and not img_src.endswith('poster_loading.png'):
                        return img_src
        except:
            pass
            
        # 方法4: 查找任意内容图片
        for img in data('img').items():
            img_src = img.attr('src')
            if img_src and not img_src.endswith('poster_loading.png') and not img_src.endswith('.svg'):
                if not img_src.startswith('data:'):
                    return img_src
                    
        # 方法5: 从og:image元数据获取
        og_image = data('meta[property="og:image"]').attr('content')
        if og_image:
            return og_image
            
        return ""

    def getlist(self, doc, html_text=""):
        """
        从页面解析视频列表
        """
        print("开始解析视频列表")
        vlist = []
        
        # 直接根据stgay.com网站的精确DOM结构提取视频
        # 从浏览器分析可见，视频位于 "list [ref=e225] > listitem > generic > link" 结构中
        try:
            # 查找main > generic > list > listitem包含视频的元素
            videos = []
            for list_item in doc('main ul > li').items():
                # 排除导航菜单等非视频项
                if not list_item.find('a[href*="/视频/"]').length:
                    continue
                    
                # 排除分类菜单（只有简短文本，没有时长和图片）
                if list_item.text() in ["正在播放", "当前最热", "最近更新", "本月最热", "高清", "每月最热"]:
                    continue
                    
                # 检查是否包含时长格式文本（视频项的特征）
                has_time = False
                for el in list_item.find('*').items():
                    if re.match(r'^\d+:\d+$', el.text().strip()):
                        has_time = True
                        break
                        
                # 检查是否包含图片元素（视频项特征）
                has_img = list_item.find('img').length > 0
                
                # 如果同时包含视频链接、时长和图片，则认为是视频项
                if has_time and has_img:
                    videos.append(list_item)
            
            print(f"找到 {len(videos)} 个视频项")
            
            # 处理每个视频项
            for video_item in videos:
                try:
                    # 视频页面链接 - 查找包含完整视频路径的a标签
                    link = None
                    for a in video_item.find('a').items():
                        href = a.attr('href')
                        if href and "/视频/" in href and not href.endswith("正在播放") and not href.endswith("当前最热"):
                            if len(href.split('/')) >= 4:  # 确保格式为 /视频/标题/ID
                                link = a
                                break
                    
                    if not link:
                        continue
                        
                    # 视频ID（链接）
                    vod_id = link.attr('href')
                    
                    # 视频封面
                    vod_pic = ""
                    img = video_item.find('img')
                    if img:
                        # 尝试多个可能的属性
                        for attr in ['src', 'data-src', 'data-original']:
                            pic = img.attr(attr)
                            if pic and not pic.endswith('poster_loading.png'):
                                vod_pic = pic
                                break
                    
                    # 视频标题
                    vod_name = ""
                    
                    # 查找不包含时长的链接文本（标题）
                    for a in video_item.find('a').items():
                        if a.attr('href') == vod_id:
                            text = a.text().strip()
                            if text and not re.match(r'^\d+:\d+$', text):
                                # 去除可能包含的时长
                                vod_name = re.sub(r'\s*\d+:\d+\s*$', '', text).strip()
                                break
                    
                    # 如果没找到标题，从URL提取
                    if not vod_name:
                        try:
                            path_parts = urllib.parse.unquote(vod_id).split('/')
                            if len(path_parts) >= 3:
                                vod_name = path_parts[-2]  # 倒数第二个部分通常是标题
                        except:
                            pass
                    
                    # 视频时长
                    vod_remarks = ""
                    # 查找时长格式文本
                    for el in video_item.find('*').items():
                        if re.match(r'^\d+:\d+$', el.text().strip()):
                            vod_remarks = el.text().strip()
                            break
                    
                    # 如果没找到时长但标题包含时长，从标题提取
                    if not vod_remarks:
                        time_match = re.search(r'(\d+:\d+)', video_item.text())
                        if time_match:
                            vod_remarks = time_match.group(1)
                    
                    # 添加视频信息到列表
                    vlist.append({
                        'vod_id': vod_id,
                        'vod_name': vod_name,
                        'vod_pic': vod_pic,
                        'vod_remarks': vod_remarks,
                        'style': {'ratio': 1.33, 'type': 'rect'}
                    })
                    print(f"成功提取视频: {vod_name}")
                except Exception as e:
                    print(f"处理视频项时出错: {str(e)}")
                    continue
        except Exception as e:
            print(f"解析视频列表时出错: {str(e)}")
        
        # 如果上面的方法没找到视频，尝试分析HTML源代码
        if not vlist and html_text:
            print("尝试从HTML源码直接解析视频")
            
            # 查找视频元素的特征模式
            pattern = r'<a[^>]*href=["\'](\/视频\/[^"\']+?\/[^"\'\/]+)["\'][^>]*>.*?<img[^>]*src=["\']([^"\']+?)["\'][^>]*>.*?(\d+:\d+)'
            matches = re.finditer(pattern, html_text, re.DOTALL)
            
            for match in matches:
                try:
                    vod_id = match.group(1)
                    vod_pic = match.group(2)
                    vod_remarks = match.group(3)
                    
                    # 从URL提取标题
                    vod_name = ""
                    try:
                        path_parts = urllib.parse.unquote(vod_id).split('/')
                        if len(path_parts) >= 3:
                            vod_name = path_parts[-2]
                    except:
                        pass
                    
                    # 确保链接不是菜单项
                    if vod_id.endswith("正在播放") or vod_id.endswith("当前最热"):
                        continue
                    
                    # 添加视频信息
                    vlist.append({
                        'vod_id': vod_id,
                        'vod_name': vod_name,
                        'vod_pic': vod_pic,
                        'vod_remarks': vod_remarks,
                        'style': {'ratio': 1.33, 'type': 'rect'}
                    })
                    print(f"从HTML源码提取视频: {vod_name}")
                except Exception as e:
                    print(f"处理HTML视频项时出错: {str(e)}")
                    continue
        
        # 如果仍然没找到视频，尝试最后一种模式匹配
        if not vlist and html_text:
            print("尝试最后的模式匹配提取视频")
            
            # 匹配特定结构的视频卡片
            pattern = r'<li[^>]*>.*?<a[^>]*href=["\'](\/视频\/[^"\'\/]+\/[^"\'\/]+)["\'][^>]*>.*?<img[^>]*?(?:src|data-src)=["\']([^"\']+)["\'].*?<\/a>.*?<\/li>'
            matches = re.finditer(pattern, html_text, re.DOTALL)
            
            for match in matches:
                try:
                    vod_id = match.group(1)
                    vod_pic = match.group(2)
                    
                    # 提取标题
                    vod_name = ""
                    try:
                        path_parts = urllib.parse.unquote(vod_id).split('/')
                        if len(path_parts) >= 3:
                            vod_name = path_parts[-2]
                    except:
                        pass
                    
                    # 查找时长
                    vod_remarks = ""
                    time_match = re.search(r'(\d+:\d+)', match.group(0))
                    if time_match:
                        vod_remarks = time_match.group(1)
                    
                    # 添加视频信息
                    vlist.append({
                        'vod_id': vod_id,
                        'vod_name': vod_name,
                        'vod_pic': vod_pic,
                        'vod_remarks': vod_remarks,
                        'style': {'ratio': 1.33, 'type': 'rect'}
                    })
                    print(f"通过模式匹配提取视频: {vod_name}")
                except Exception as e:
                    print(f"处理模式匹配视频项时出错: {str(e)}")
                    continue
        
        print(f"总共找到 {len(vlist)} 个视频")
        
        # 检查视频列表是否为空
        if len(vlist) > 0:
            print(f"第一个视频: {vlist[0]['vod_name']}, 封面: {vlist[0]['vod_pic']}")
        else:
            print("警告: 没有找到任何视频")
        
        return vlist
