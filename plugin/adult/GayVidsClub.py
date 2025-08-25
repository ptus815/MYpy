# -*- coding: utf-8 -*-
# by @Claude
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
            self.proxies = json.loads(extend)
        except:
            self.proxies = {}
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
        
        # 初始化嗅探解析器配置
        self.sniff_parsers = [
            {"name": "王", "url": "http://122.228.84.103:7777/api/?key=4Dk5tdayvY6NZufEMG&url="},
            {"name": "二", "url": "http://110.42.7.182:880/api/?key=7e84f07dc78fbb3406d64a1ab7d966b3&url="},
            {"name": "小", "url": "http://43.136.176.188:91/api/?key=4ef232e96172b0bda78d393c695fe7c4&url="},
            {"name": "帅", "url": "http://pan.qiaoji8.com/tvbox/neibu.php?url="}
        ]
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
        if not vlist:
            # Fallback: 用RSS
            try:
                rss = self.session.get(f'{self.host}/feed', timeout=15).text
                d = pq(rss)
                vlist = []
                for it in d('item').items():
                    link = it('link').text().strip()
                    title = it('title').text().strip()
                    thumb = ''
                    desc = it('description').text()
                    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', desc or '', re.I)
                    if m:
                        thumb = m.group(1)
                    if link and title:
                        vlist.append({
                            'vod_id': link,
                            'vod_name': title,
                            'vod_pic': thumb,
                            'vod_year': '',
                            'vod_remarks': '',
                            'style': {'ratio': 1.33, 'type': 'rect'}
                        })
            except Exception as e:
                print(f'RSS解析失败: {e}')
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
        iframe_src = data('iframe').attr('src')
        
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
        
        # 构建播放地址 - 支持多种播放方式
        if iframe_src:
            # 方式1: 直接播放iframe
            encoded_url = self.e64(f'{0}@@@@{iframe_src}')
            vod['vod_play_url'] = f"直接播放${encoded_url}"
            
            # 方式2: 使用嗅探路线
            sniff_urls = []
            
            for parser in self.sniff_parsers:
                sniff_url = f"{parser['url']}{iframe_src}"
                encoded_sniff_url = self.e64(f'{1}@@@@{sniff_url}')
                sniff_urls.append(f"{parser['name']}${encoded_sniff_url}")
            
            # 组合所有播放方式
            all_play_urls = [vod['vod_play_url']] + sniff_urls
            vod['vod_play_url'] = '#'.join(all_play_urls)
        
        return {'list': [vod]}

    def searchContent(self, key, quick, pg="1"):
        if pg == 1:
            url = f"/?s={key}"
        else:
            url = f"/page/{pg}/?s={key}"
        
        data = self.getpq(url)
        return {'list': self.getlist(data("article")), 'page': pg}

    def playerContent(self, flag, id, vipFlags):
        ids = self.d64(id).split('@@@@')
        parse_type = int(ids[0])
        url = ids[1]
        
        # 如果是嗅探路线 (parse_type == 1)
        if parse_type == 1:
            # 直接返回嗅探URL，让播放器处理
            return {'parse': 1, 'url': url, 'header': self.headers}
        
        # 如果是直接播放iframe (parse_type == 0)
        else:
            iframe_url = url
            
            # 获取iframe内容
            try:
                response = self.session.get(iframe_url, timeout=15)
                content = response.text
                
                # 查找m3u8地址
                m3u8_url = None
                
                # 方法1：从页面内容中查找m3u8链接
                m3u8_pattern = r'https://[^"\']*\.m3u8[^"\']*'
                m3u8_matches = re.findall(m3u8_pattern, content)
                if m3u8_matches:
                    m3u8_url = m3u8_matches[0]
                
                # 方法2：查找stream路径
                if not m3u8_url:
                    stream_pattern = r'https://[^"\']*stream[^"\']*master\.m3u8'
                    stream_matches = re.findall(stream_pattern, content)
                    if stream_matches:
                        m3u8_url = stream_matches[0]
                
                # 方法3：查找视频ID并构建m3u8地址
                if not m3u8_url:
                    video_id_match = re.search(r'embed/([a-zA-Z0-9]+)', iframe_url)
                    if video_id_match:
                        video_id = video_id_match.group(1)
                        # 尝试构建m3u8地址
                        m3u8_url = f"https://mivalyo.com/stream/{video_id}/master.m3u8"
                
                if m3u8_url:
                    return {'parse': 0, 'url': m3u8_url, 'header': self.headers}
                else:
                    # 如果找不到m3u8，返回iframe地址
                    return {'parse': 1, 'url': iframe_url, 'header': self.headers}
                    
            except Exception as e:
                print(f"获取播放地址失败: {str(e)}")
                return {'parse': 1, 'url': iframe_url, 'header': self.headers}

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
                
                # 发布时间（支持月份页、具体日期链接等）
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
