# coding=utf-8
# !/usr/bin/python
import json
import sys
import re
from base64 import b64decode, b64encode
from pyquery import PyQuery as pq
from requests import Session
sys.path.append('..')
from base.spider import Spider


class Spider(Spider):

    def init(self, extend=""):
        self.host = self.gethost()
        self.headers['referer'] = f'{self.host}/'
        self.session = Session()
        self.session.headers.update(self.headers)
        pass

    def getName(self):
        return "Stgay"

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        return True

    def destroy(self):
        pass

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-full-version': '"133.0.6943.98"',
        'sec-ch-ua-arch': '"x86"',
        'sec-ch-ua-platform': '"Windows"',
        'sec-ch-ua-platform-version': '"19.0.0"',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-full-version-list': '"Not(A:Brand";v="99.0.0.0", "Google Chrome";v="133.0.6943.98", "Chromium";v="133.0.6943.98"',
        'dnt': '1',
        'upgrade-insecure-requests': '1',
        'sec-fetch-site': 'none',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'priority': 'u=0, i'
    }

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
        data = self.getpq("/视频/正在播放")
        return {'list': self.getlist(data(".video-list-area .video-list-item"))}

    def categoryContent(self, tid, pg, filter, extend):
        result = {}
        result['page'] = pg
        result['pagecount'] = 9999
        result['limit'] = 90
        result['total'] = 999999
        
        url = f'{tid}' if pg == '1' else f'{tid}/{pg}'
        data = self.getpq(url)
        vlist = self.getlist(data(".video-list-area .video-list-item"))
        result['list'] = vlist
        return result

    def detailContent(self, ids):
        data = self.getpq(ids[0])
        vod = {}
        
        # 获取视频标题
        vod['vod_id'] = ids[0]
        vod['vod_name'] = data('h1.video-detail-title').text().strip()
        
        # 获取视频封面
        vod_pic = ""
        try:
            # 尝试从视频播放器获取封面
            video_img = data('.video-detail-player img').attr('src')
            if video_img and not video_img.endswith('poster_loading.png'):
                vod_pic = video_img
            else:
                # 尝试从推荐视频中找到当前视频的封面
                video_id = ids[0].split('/')[-1]
                for item in data('.recommended-videos .video-list-item').items():
                    if video_id in item('a').attr('href'):
                        vod_pic = item('img').attr('src')
                        break
        except:
            pass
        
        vod['vod_pic'] = vod_pic
        
        # 获取视频标签
        tags = []
        for tag in data('.video-detail-tags .tag-item').items():
            tags.append(tag.text().strip())
        vod['vod_remarks'] = ','.join(tags) if tags else "无标签"
        
        # 获取视频简介
        vod['vod_content'] = data('h2.video-detail-desc').text().strip()
        
        # 播放列表
        play_url = None
        
        # 方法1：尝试从视频元素获取
        video_source = data('video source')
        if video_source:
            play_url = video_source.attr('src')
        
        # 方法2：尝试从页面JS中提取
        if not play_url:
            html_text = self.session.get(f'{self.host}{ids[0]}').text
            match = re.search(r'url:\s*[\'"]([^\'"]+)[\'"]', html_text)
            if match:
                play_url = match.group(1)
        
        if play_url:
            vod['vod_play_from'] = 'Stgay'
            vod['vod_play_url'] = f"{vod['vod_name']}${self.e64(f'{0}@@@@{play_url}')}"
        else:
            # 如果没有找到直接播放源，使用页面URL作为视频ID
            vod['vod_play_from'] = 'Stgay'
            vod['vod_play_url'] = f"{vod['vod_name']}${self.e64(f'{1}@@@@{ids[0]}')}"
            
        return {'list': [vod]}

    def searchContent(self, key, quick, pg="1"):
        url = f'/视频/search/{key}' if pg == '1' else f'/视频/search/{key}/{pg}'
        data = self.getpq(url)
        return {'list': self.getlist(data(".video-list-area .video-list-item")), 'page': pg, 'pagecount': 9999, 'limit': 90, 'total': 999999}

    def playerContent(self, flag, id, vipFlags):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.5410.0 Safari/537.36',
            'pragma': 'no-cache',
            'cache-control': 'no-cache',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            'dnt': '1',
            'sec-ch-ua-mobile': '?0',
            'origin': self.host,
            'sec-fetch-site': 'cross-site',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': f'{self.host}/',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'priority': 'u=1, i',
        }
        ids = self.d64(id).split('@@@@')
        
        # 如果是需要解析的URL
        if int(ids[0]) == 1:
            # 获取页面内容
            url = ids[1]
            if not url.startswith('http'):
                url = f'{self.host}{url}'
                
            html_text = self.session.get(url).text
            
            # 尝试从页面JS中提取真实视频URL
            match = re.search(r'url:\s*[\'"]([^\'"]+)[\'"]', html_text)
            if match:
                return {'parse': 0, 'url': match.group(1), 'header': headers}
            
            # 尝试从video元素获取
            doc = pq(html_text)
            video_source = doc('video source')
            if video_source:
                play_url = video_source.attr('src')
                if play_url:
                    return {'parse': 0, 'url': play_url, 'header': headers}
        
        # 直接播放
        return {'parse': int(ids[0]), 'url': ids[1], 'header': headers}

    def localProxy(self, param):
        pass

    def gethost(self):
        try:
            # 尝试获取主页
            response = self.fetch('https://stgay.com', headers=self.headers)
            if response.status_code == 200:
                return 'https://stgay.com'
            else:
                # 如果主域名不可访问，尝试使用备用域名
                return 'https://dizhi44.pages.dev'
        except Exception as e:
            print(f"获取主页失败: {str(e)}")
            return 'https://stgay.com'  # 默认主域名

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

    def getlist(self, items):
        vlist = []
        for i in items.items():
            vod_id = i('a').attr('href')
            if not vod_id:
                continue
                
            # 确保vod_id是相对路径
            if vod_id.startswith('http'):
                if vod_id.startswith(self.host):
                    vod_id = vod_id[len(self.host):]
                else:
                    continue  # 跳过外部链接
                    
            vod_name = i('.video-title').text().strip()
            if not vod_name:
                continue
                
            # 获取视频封面
            vod_pic = i('img').attr('src')
            if not vod_pic or vod_pic.endswith('poster_loading.png'):
                vod_pic = i('img').attr('data-src')
                
            # 获取视频时长
            vod_remarks = i('.duration').text().strip() if i('.duration') else ""
            
            # 观看次数
            views = i('.video-stats .views').text().strip() if i('.video-stats .views') else ""
            
            # 添加视频信息
            vlist.append({
                'vod_id': vod_id,
                'vod_name': vod_name,
                'vod_pic': vod_pic,
                'vod_remarks': vod_remarks,
                'vod_year': views,
                'style': {'ratio': 1.33, 'type': 'rect'}
            })
        return vlist

    def getpq(self, path=''):
        h = '' if path.startswith('http') else self.host
        url = f'{h}{path}'
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()  # 检查响应状态
            response_text = response.text
            return pq(response_text)
        except Exception as e:
            print(f"获取页面失败 {url}: {str(e)}")
            return pq("<html></html>") 
