# -*- coding: utf-8 -*-
# FMovies crawler for fmoviesto.cc
import re
import sys
import json
import base64
from urllib.parse import quote_plus, urlparse, parse_qs
import requests
from pyquery import PyQuery as pq
sys.path.append('..')
from base.spider import Spider


class Spider(Spider):

    def init(self, extend=""):
        self.site_url = 'https://fmoviesto.cc'
        self.site_name = 'FMovies'
        self.img_prefix = 'https://f.woowoowoowoo.net/resize/250x400'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.7103.48 Safari/537.36',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="136", "Google Chrome";v="136"',
            'origin': self.site_url,
            'referer': self.site_url,
        }
        
    def getName(self):
        return "FMovies"
        
    def homeContent(self, filter):
        result = {}
        cate = {
            "电影": "movie",
            "剧集": "tv-show"
        }
        classes = []
        filters = {}
        for k, v in cate.items():
            classes.append({
                'type_name': k,
                'type_id': v
            })
        
        # Add genres as filters
        genre_list = ['action', 'adventure', 'animation', 'comedy', 'crime',
                    'documentary', 'drama', 'family', 'fantasy', 'history',
                    'horror', 'music', 'mystery', 'romance', 'sci-fi',
                    'thriller', 'war', 'western']
        
        genre_options = []
        for genre in genre_list:
            genre_options.append({
                "n": genre.capitalize(),
                "v": genre
            })
        
        # Add countries and sort options
        filters.update({
            "movie": [
                {"key": "genre", "name": "类型", "value": genre_options},
            ],
            "tv-show": [
                {"key": "genre", "name": "类型", "value": genre_options},
            ]
        })
        
        result['class'] = classes
        result['filters'] = filters
        return result

    def homeVideoContent(self):
        url = f"{self.site_url}/movie"  # Using movie page as home since it shows latest movies
        print(f"Fetching URL: {url}")
        html = self.fetch(url, headers=self.headers).text
        doc = pq(html)
        videos = []
        
        print("Looking for movie items in general structure")
        
        # General approach to find movies
        for item in doc('a[href*="/movie/"]').items():
            vod_id = item.attr('href')
            
            # Skip items that aren't direct movie links or are duplicates
            if not vod_id or 'javascript' in vod_id:
                continue
            
            # Try to get parent container to extract more info
            parent_div = item.closest('div')
            
            # Try to extract title
            vod_name = ""
            heading = parent_div.find('h2')
            if heading:
                vod_name = heading.text().strip()
            if not vod_name:
                vod_name = item.text().strip()
            
            # Skip if no valid name
            if not vod_name:
                continue
            
            # Try to extract image
            vod_pic = ""
            img_elem = parent_div.find('img')
            if img_elem:
                vod_pic = img_elem.attr('data-src') or img_elem.attr('src')
            
            # Try to extract remarks
            vod_remarks = ""
            info_div = parent_div.find('.fd-infor')
            if info_div:
                vod_remarks = info_div.text().strip()
            
            # Add to videos list
            if vod_id not in [v['vod_id'] for v in videos]:  # Avoid duplicates
                videos.append({
                    "vod_id": vod_id,
                    "vod_name": vod_name,
                    "vod_pic": vod_pic,
                    "vod_remarks": vod_remarks
                })
        
        print(f"Found {len(videos)} videos")
        return {'list': videos}

    def categoryContent(self, tid, pg, filter, extend):
        result = {}
        url = f"{self.site_url}/{tid}"
        if pg != '1':
            url = f"{url}?page={pg}"
        
        # Add filters if provided
        if extend.get('genre', ''):
            url = f"{self.site_url}/genre/{extend['genre']}?page={pg}"
        
        print(f"Fetching category: {url}")
        html = self.fetch(url, headers=self.headers).text
        doc = pq(html)
        videos = []
        
        # General approach to find movies/shows based on tid
        link_pattern = '/movie/' if tid == 'movie' else '/tv/'
        
        for item in doc(f'a[href*="{link_pattern}"]').items():
            vod_id = item.attr('href')
            
            # Skip items that aren't direct movie/show links or are duplicates
            if not vod_id or 'javascript' in vod_id:
                continue
            
            # Try to get parent container to extract more info
            parent_div = item.closest('div')
            
            # Try to extract title
            vod_name = ""
            heading = parent_div.find('h2')
            if heading:
                vod_name = heading.text().strip()
            if not vod_name:
                vod_name = item.text().strip()
            
            # Skip if no valid name
            if not vod_name:
                continue
            
            # Try to extract image
            vod_pic = ""
            img_elem = parent_div.find('img')
            if img_elem:
                vod_pic = img_elem.attr('data-src') or img_elem.attr('src')
            
            # Try to extract remarks
            vod_remarks = ""
            info_div = parent_div.find('.fd-infor')
            if info_div:
                vod_remarks = info_div.text().strip()
            
            # Add to videos list if not duplicate
            if vod_id not in [v['vod_id'] for v in videos]:  # Avoid duplicates
                videos.append({
                    "vod_id": vod_id,
                    "vod_name": vod_name,
                    "vod_pic": vod_pic,
                    "vod_remarks": vod_remarks
                })
        
        result['list'] = videos
        result['page'] = pg
        result['pagecount'] = 999
        result['limit'] = 90
        result['total'] = 999999
        
        return result

    def detailContent(self, ids):
        url = self.site_url + ids[0]
        print(f"Fetching detail: {url}")
        html = self.fetch(url, headers=self.headers).text
        doc = pq(html)
        
        # Extract movie/show information
        title = doc('h2.film-name, h1, .film-detail h2').text()
        
        # Find cover image
        cover = None
        img_elems = doc('img')
        for img in img_elems.items():
            src = img.attr('src')
            if src and ('poster' in src.lower() or 'cover' in src.lower()):
                cover = src
                break
        
        if not cover:
            cover_div = doc('.film-poster')
            if cover_div:
                img = cover_div.find('img')
                if img:
                    cover = img.attr('src')
        
        # Extract other metadata
        year = ""
        duration = ""
        category = ""
        genre = ""
        description = ""
        
        # Try to find description
        desc_div = doc('.film-description, .description')
        if desc_div:
            description = desc_div.text()
        
        # Try to find metadata from various potential locations
        info_items = doc('.fd-infor .fdi-item')
        if info_items.length > 0:
            year = info_items.eq(0).text()
        if info_items.length > 1:
            duration = info_items.eq(1).text()
        if info_items.length > 2:
            category = info_items.eq(2).text()
        
        # Get genre links
        genre_links = doc('a[href*="genre"]')
        if genre_links:
            genres = []
            for link in genre_links.items():
                genres.append(link.text())
            genre = ', '.join(genres)
        
        # Handle play URLs
        play_url = ""
        
        # Find watch button
        watch_url = None
        watch_links = doc('a[href*="watch-"]')
        if watch_links:
            for link in watch_links.items():
                href = link.attr('href')
                if href:
                    watch_url = href
                    break
        
        if 'tv' in ids[0]:  # TV Show
            episodes = []
            
            if watch_url:
                # Navigate to watch page to extract episodes
                watch_page_url = self.site_url + watch_url
                print(f"Fetching watch page: {watch_page_url}")
                watch_html = self.fetch(watch_page_url, headers=self.headers).text
                watch_doc = pq(watch_html)
                
                # Find all server tabs
                server_links = watch_doc('.server-select-switch a')
                
                if server_links.length > 0:
                    for server in server_links.items():
                        server_url = server.attr('href')
                        if server_url:
                            # Fetch server page
                            server_html = self.fetch(self.site_url + server_url, headers=self.headers).text
                            server_doc = pq(server_html)
                            
                            # Find episode links
                            ep_links = server_doc('.episodes-list a, .episode-list a, .episode a')
                            for ep_link in ep_links.items():
                                ep_name = ep_link.text().strip()
                                ep_url = ep_link.attr('href')
                                if ep_url:
                                    episodes.append(f"{ep_name}${ep_url}")
                else:
                    # Direct episodes on watch page
                    ep_links = watch_doc('.episodes-list a, .episode-list a, .episode a')
                    for ep_link in ep_links.items():
                        ep_name = ep_link.text().strip()
                        ep_url = ep_link.attr('href')
                        if ep_url:
                            episodes.append(f"{ep_name}${ep_url}")
                
                if episodes:
                    play_url = "播放列表#" + "#".join(episodes)
                else:
                    play_url = "暂无链接$"
            else:
                play_url = "暂无链接$"
        else:  # Movie
            if watch_url:
                play_url = f"播放链接${watch_url}"
            else:
                play_url = "暂无链接$"
        
        vod = {
            "vod_id": ids[0],
            "vod_name": title,
            "vod_pic": cover,
            "type_name": category or ('TV Show' if 'tv' in ids[0] else 'Movie'),
            "vod_year": year,
            "vod_area": "",
            "vod_remarks": duration,
            "vod_actor": "",
            "vod_director": "",
            "vod_content": description,
            "vod_play_from": "FMovies",
            "vod_play_url": play_url
        }
        
        result = {
            'list': [vod]
        }
        return result

    def searchContent(self, key, quick):
        return self.searchContentPage(key, quick, 1)
        
    def searchContentPage(self, key, quick, pg=1):
        search_url = f"{self.site_url}/search/{quote_plus(key)}"
        if int(pg) > 1:
            search_url = f"{search_url}?page={pg}"
        
        print(f"Searching: {search_url}")
        html = self.fetch(search_url, headers=self.headers).text
        doc = pq(html)
        videos = []
        
        # Look for movie/tv links in search results
        for item in doc('a[href*="/movie/"], a[href*="/tv/"]').items():
            vod_id = item.attr('href')
            
            # Skip invalid links
            if not vod_id or 'javascript' in vod_id:
                continue
            
            # Try to get parent container to extract more info
            parent_div = item.closest('div')
            
            # Try to extract title
            vod_name = ""
            heading = parent_div.find('h2')
            if heading:
                vod_name = heading.text().strip()
            if not vod_name:
                vod_name = item.text().strip()
            
            # Skip if no valid name
            if not vod_name:
                continue
            
            # Try to extract image
            vod_pic = ""
            img_elem = parent_div.find('img')
            if img_elem:
                vod_pic = img_elem.attr('data-src') or img_elem.attr('src')
            
            # Try to extract remarks
            vod_remarks = ""
            info_div = parent_div.find('.fd-infor')
            if info_div:
                vod_remarks = info_div.text().strip()
            
            # Add to videos list if not duplicate
            if vod_id not in [v['vod_id'] for v in videos]:  # Avoid duplicates
                videos.append({
                    "vod_id": vod_id,
                    "vod_name": vod_name,
                    "vod_pic": vod_pic,
                    "vod_remarks": vod_remarks
                })
        
        result = {
            'list': videos,
            'page': pg,
            'pagecount': 10,
            'limit': 90,
            'total': 999999
        }
        return result

    def playerContent(self, flag, id, vipFlags):
        result = {}
        url = self.site_url + id
        
        print(f"Fetching player: {url}")
        html = self.fetch(url, headers=self.headers).text
        doc = pq(html)
        
        # Extract iframe source
        iframe = doc('iframe')
        if iframe:
            iframe_src = iframe.attr('src')
            if iframe_src:
                if not iframe_src.startswith('http'):
                    iframe_src = f"https:{iframe_src}" if iframe_src.startswith('//') else f"{self.site_url}{iframe_src}"
                
                print(f"Found iframe: {iframe_src}")
                
                # Check if we need to use proxy
                if self.need_proxy(iframe_src):
                    return {
                        "parse": 0,
                        "playUrl": "",
                        "url": self.create_proxy_url(iframe_src, "iframe"),
                        "header": self.headers
                    }
                
                # Access the iframe content
                iframe_headers = self.headers.copy()
                iframe_headers['referer'] = url
                
                result["parse"] = 0
                result["url"] = iframe_src
                result["header"] = iframe_headers
                
                return result
        
        # If no iframe, look for other possible player sources
        script_content = ""
        for script in doc('script').items():
            script_text = script.text()
            if 'sources:' in script_text:
                script_content = script_text
                break
        
        if script_content:
            # Extract video sources
            sources_match = re.search(r'sources:\s*(\[.*?\])', script_content, re.DOTALL)
            if sources_match:
                try:
                    sources = json.loads(sources_match.group(1))
                    print(f"Found sources: {sources}")
                    if sources and len(sources) > 0:
                        max_quality = sources[0]
                        for source in sources:
                            if source.get('label') and '1080' in source.get('label'):
                                max_quality = source
                                break
                        
                        video_url = max_quality.get('file')
                        
                        # Check if we need to use proxy
                        if self.need_proxy(video_url):
                            return {
                                "parse": 0,
                                "playUrl": "",
                                "url": self.create_proxy_url(video_url, "video"),
                                "header": self.headers
                            }
                        
                        result["parse"] = 0
                        result["url"] = video_url
                        result["header"] = self.headers
                        
                        return result
                except Exception as e:
                    print(f"Error parsing sources: {e}")
                    pass
        
        # Fallback: try to find any video source
        video_elem = doc('video')
        if video_elem:
            video_src = video_elem.attr('src')
            if video_src:
                print(f"Found video element: {video_src}")
                
                # Check if we need to use proxy
                if self.need_proxy(video_src):
                    return {
                        "parse": 0,
                        "playUrl": "",
                        "url": self.create_proxy_url(video_src, "video"),
                        "header": self.headers
                    }
                
                result["parse"] = 0
                result["url"] = video_src
                result["header"] = self.headers
                
                return result
        
        # If all else fails, return the original URL
        result["parse"] = 1  # Let the player handle it
        result["url"] = url
        result["header"] = self.headers
        
        return result

    def isVideoFormat(self, url):
        return url.endswith('.m3u8') or url.endswith('.mp4') or '.m3u8' in url or '.mp4' in url
    
    def manualVideoCheck(self):
        return True
    
    def need_proxy(self, url):
        """检查是否需要代理"""
        blocked_domains = ['cloudfront.net', 'googleapis.com', 'akamaized.net']
        return any(domain in url for domain in blocked_domains)
    
    def create_proxy_url(self, url, type_name):
        """创建代理URL"""
        return f"http://127.0.0.1:9978/proxy?do=py&type=fmovies&url={quote_plus(url)}&media_type={type_name}"
        
    def localProxy(self, params):
        """处理本地代理请求"""
        action = ''
        
        if params.get('type') == 'fmovies':
            url = params.get('url')
            media_type = params.get('media_type', '')
            
            if not url:
                return [404, "text/plain", "Missing URL parameter", {}]
            
            headers = self.headers.copy()
            
            try:
                if media_type == 'iframe':
                    # 处理iframe内容
                    resp = requests.get(url, headers=headers)
                    content = resp.text
                    
                    # 尝试从iframe中提取真实视频地址
                    video_url = self.extract_video_from_iframe(content)
                    if video_url:
                        if video_url.startswith('//'):
                            video_url = 'https:' + video_url
                            
                        # 如果找到视频URL，重定向到它
                        redirect_headers = {"Location": video_url}
                        return [302, "video/MP2T", None, redirect_headers]
                    
                    # 如果无法提取视频，返回原始内容
                    return [200, "text/html", content, {}]
                    
                elif media_type == 'video' or self.isVideoFormat(url):
                    # 直接代理视频流
                    resp = requests.get(url, headers=headers, stream=True)
                    content_type = resp.headers.get('Content-Type', 'application/octet-stream')
                    
                    # 对于m3u8文件，可能需要修改内容
                    if '.m3u8' in url:
                        content = resp.text
                        # 处理m3u8内容，替换可能被屏蔽的域名
                        return [200, "application/vnd.apple.mpegurl", content, {}]
                    else:
                        # 对于直接视频流，使用206部分内容响应
                        return [206, content_type, resp.content, {}]
                else:
                    # 默认处理
                    resp = requests.get(url, headers=headers)
                    return [200, resp.headers.get('Content-Type', 'text/html'), resp.content, {}]
                    
            except Exception as e:
                print(f"Proxy error: {str(e)}")
                return [500, "text/plain", f"Proxy error: {str(e)}", {}]
        
        # 默认返回
        return [200, "video/MP2T", action, {}]
    
    def extract_video_from_iframe(self, content):
        """从iframe内容中提取视频URL"""
        try:
            # 尝试找到sources数组
            sources_match = re.search(r'sources:\s*(\[.*?\])', content, re.DOTALL)
            if sources_match:
                sources = json.loads(sources_match.group(1))
                if sources and len(sources) > 0:
                    # 优先选择高质量视频
                    for source in sources:
                        if source.get('label') and '1080' in source.get('label'):
                            return source.get('file')
                    # 如果没有1080p，返回第一个
                    return sources[0].get('file')
            
            # 尝试找到video标签
            video_match = re.search(r'<video[^>]*src=["\']([^"\']+)["\']', content)
            if video_match:
                return video_match.group(1)
                
            # 尝试找到iframe
            iframe_match = re.search(r'<iframe[^>]*src=["\']([^"\']+)["\']', content)
            if iframe_match:
                return iframe_match.group(1)
                
        except Exception as e:
            print(f"Error extracting video: {str(e)}")
        
        return None


if __name__ == "__main__":
    spider = Spider()
    spider.init()
    
    # Test various functionality
    import traceback
    try:
        print("====== Testing Home Content ======")
        home_content = spider.homeContent(True)
        print(json.dumps(home_content, indent=2))
        
        print("\n====== Testing Home Video Content ======")
        home_videos = spider.homeVideoContent()
        print(f"Found {len(home_videos['list'])} videos")
        # Print first 3 items only for brevity
        for i, video in enumerate(home_videos['list'][:3]):
            print(f"Video {i+1}: {video['vod_name']} - {video['vod_id']}")
        
        if home_videos['list']:
            print("\n====== Testing Detail Content ======")
            detail = spider.detailContent([home_videos['list'][0]['vod_id']])
            print(json.dumps(detail, indent=2))
            
            if 'list' in detail and detail['list']:
                play_url = detail['list'][0]['vod_play_url']
                if '$' in play_url:
                    vid_url = play_url.split('$')[1]
                    
                    print("\n====== Testing Player Content ======")
                    player = spider.playerContent('', vid_url, {})
                    print(json.dumps(player, indent=2))
        
        print("\n====== Testing Search Content ======")
        search = spider.searchContent("avengers", False)
        print(f"Found {len(search['list'])} search results")
        # Print first 3 items only for brevity
        for i, video in enumerate(search['list'][:3]):
            print(f"Result {i+1}: {video['vod_name']} - {video['vod_id']}")
        
        print("\n====== Testing Search Content Page 2 ======")
        search_page2 = spider.searchContentPage("avengers", False, 2)
        print(f"Found {len(search_page2['list'])} search results on page 2")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        traceback.print_exc() 