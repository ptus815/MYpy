# -*- coding: utf-8 -*-
import re
import json
import sys
import requests
from urllib.parse import urljoin
from base64 import b64encode, b64decode
from pyquery import PyQuery as pq
sys.path.append('..')
from base.spider import Spider

class Spider(Spider):

    def __init__(self, extend=""):
        try:
            self.extend = json.loads(extend) if extend else {}
        except:
            self.extend = {}

        self.host = "https://gaycock4u.com"
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0',
        }

        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def e64(self, text: str) -> str:
        """ Base64 编码 """
        try:
            return b64encode(text.encode('utf-8')).decode('utf-8')
        except Exception as e:
            self.log(f"Base64 编码失败: {str(e)}")
            return ''

    def d64(self, text: str) -> str:
        """ Base64 解码 """
        try:
            return b64decode(text.encode('utf-8')).decode('utf-8')
        except Exception as e:
            self.log(f"Base64 解码失败: {str(e)}")
            return ''

    def getName(self):
        return "GayCock4U"

    def isVideoFormat(self, url):
        return any(ext in url for ext in ['.m3u8', '.mp4', '.ts'])

    def homeContent(self, filter):
        cateManual = [
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
        return {'class': cateManual, 'filters': {}}

    def getlist(self, articles):
        vlist = []
        for article in articles.items():
            try:
                link_elem = article('a').eq(0)
                vod_url = link_elem.attr('href') or ''
                vod_name = link_elem.text().strip() or article('img').attr('alt') or ''
                if not vod_url or not vod_name:
                    continue

                img_elem = article('img')
                vod_pic = img_elem.attr('src') or img_elem.attr('data-src') or img_elem.attr('data-lazy-src') or ''
                if not vod_pic and img_elem.attr('srcset'):
                    vod_pic = img_elem.attr('srcset').split(' ')[0]
                if vod_pic and not vod_pic.startswith('http'):
                    vod_pic = urljoin(self.host, vod_pic)

                # 视频时长 / 分类信息
                vod_remarks = article('.video-info, .video-duration, [class*="duration"]').text().strip() or ''
                vod_year = ''

                vlist.append({
                    'vod_id': self.e64(vod_url),
                    'vod_name': vod_name,
                    'vod_pic': vod_pic,
                    'vod_year': vod_year,
                    'vod_remarks': vod_remarks,
                    'style': {'ratio': 1.33, 'type': 'rect'}
                })
            except Exception as e:
                self.log(f"解析视频失败: {str(e)}")
        return vlist

    def homeVideoContent(self):
        return self.categoryContent('', '1', False, {})

    def categoryContent(self, tid, pg, filter, extend):
        result = {'page': pg, 'pagecount': 9999, 'limit': 90, 'total': 999999}
        if tid:
            url = tid if tid.startswith('http') else f"{self.host}{tid}"
            if pg != '1':
                url = f"{url}page/{pg}/" if url.endswith('/') else f"{url}/page/{pg}/"
            else:
                url = f"{self.host}/page/{pg}/" if pg != '1' else self.host

        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            doc = pq(resp.text)
            articles = doc('article')
            vlist = self.getlist(articles)
            result['list'] = vlist
        except Exception as e:
            self.log(f"获取分类内容失败: {str(e)}")
            result['list'] = []

        return result

    def detailContent(self, ids):
        try:
            url = self.d64(ids[0])
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            doc = pq(resp.text)

            # 标题
            title = doc('meta[property="og:title"]').attr('content') or doc('h1').text().strip() or 'GayCock4U视频'

            # 封面图
            vod_pic = doc('meta[property="og:image"]').attr('content') or ''
            if not vod_pic:
                img_elem = doc('img[src*="cover"], img[src*="poster"], img[src*="thumb"]').eq(0)
                vod_pic = img_elem.attr('src') or img_elem.attr('data-src') or ''

            # 标签
            tags = [t.text().strip() for t in doc('.entry-tags a, .post-tags a, a[href*="/tag/"]').items() if t.text().strip()]

            # 简介
            info_text = doc('.entry-meta, .post-meta').text().strip() or ''

            # iframe 播放源
            iframe_src = None
            matches = re.findall(r'<iframe[^>]*src=["\'](https?://d-s\.io/[^"\']+)["\']', resp.text, re.IGNORECASE)
            if matches:
                iframe_src = matches[0]
            if iframe_src and not iframe_src.startswith('http'):
                iframe_src = urljoin(self.host, iframe_src)

            vod_play_url = self.e64(iframe_src or url)
            vod_content = ' | '.join(filter(None, [info_text]))
            vod = {
                'vod_name': title,
                'vod_pic': vod_pic,
                'vod_content': vod_content,
                'vod_tag': ', '.join(tags) if tags else "GayCock4U",
                'vod_play_from': 'Push',
                'vod_play_url': f'播放${vod_play_url}'
            }
            return {'list': [vod]}
        except Exception as e:
            self.log(f"获取视频详情失败: {str(e)}")
            return {'list': []}

    def searchContent(self, key, quick, pg="1"):
        try:
            url = self.host
            resp = self.session.get(url, params={'s': key}, timeout=30)
            resp.raise_for_status()
            doc = pq(resp.text)
            articles = doc('article')
            vlist = self.getlist(articles)
            return {'list': vlist, 'page': pg, 'pagecount': 9999, 'limit': 90, 'total': 999999}
        except Exception as e:
            self.log(f"搜索失败: {str(e)}
            return {'list': [], 'page': pg, 'pagecount': 0, 'limit': 90, 'total': 0}
            def fetch_html(self, url):
        """ 获取网页 HTML 内容 """
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            return resp.text
        except requests.exceptions.RequestException as e:
            self.log(f"请求失败: {str(e)}")
            return ''

    def clean_url(self, url):
        """ 清理并返回一个有效的 URL """
        if url and not url.startswith('http'):
            return urljoin(self.host, url)
        return url

    def extract_video_url(self, html_content):
        """ 提取视频播放链接 """
        video_url = None
        iframe_matches = re.findall(r'<iframe[^>]*src=["\'](https?://d-s\.io/[^"\']+)["\']', html_content, re.IGNORECASE)
        if iframe_matches:
            video_url = iframe_matches[0]
        return video_url

    def extract_video_details(self, html_content):
        """ 从视频详情页提取信息 """
        doc = pq(html_content)

        # 获取视频标题
        title = doc('meta[property="og:title"]').attr('content') or doc('h1').text().strip() or '无标题'

        # 获取视频封面
        vod_pic = doc('meta[property="og:image"]').attr('content') or ''
        if not vod_pic:
            img_elem = doc('img[src*="cover"], img[src*="poster"], img[src*="thumb"]').eq(0)
            vod_pic = img_elem.attr('src') or img_elem.attr('data-src') or ''

        # 获取视频简介
        info_text = doc('.entry-meta, .post-meta').text().strip() or ''

        # 获取标签
        tags = [t.text().strip() for t in doc('.entry-tags a, .post-tags a').items() if t.text().strip()]

        # 提取 iframe 播放链接
        iframe_src = self.extract_video_url(html_content)
        if iframe_src:
            iframe_src = self.clean_url(iframe_src)

        return {
            'vod_name': title,
            'vod_pic': vod_pic,
            'vod_content': info_text,
            'vod_tag': ', '.join(tags),
            'vod_play_url': self.e64(iframe_src) if iframe_src else ''
        }

    def searchContent(self, key, quick, pg="1"):
        """ 搜索视频 """
        try:
            url = f"{self.host}/search"
            resp = self.session.get(url, params={'s': key, 'page': pg}, timeout=30)
            resp.raise_for_status()

            doc = pq(resp.text)
            articles = doc('article')
            vlist = self.getlist(articles)

            return {
                'list': vlist,
                'page': pg,
                'pagecount': 9999,  # 假定无限页数
                'limit': 90,
                'total': len(vlist)
            }

        except Exception as e:
            self.log(f"搜索失败: {str(e)}")
            return {'list': [], 'page': pg, 'pagecount': 0, 'limit': 90, 'total': 0}

    def get_video_play_url(self, video_page_url):
        """ 获取视频的播放链接 """
        html_content = self.fetch_html(video_page_url)
        video_details = self.extract_video_details(html_content)

        # 提取视频播放地址
        video_play_url = video_details.get('vod_play_url')
        if video_play_url:
            return {
                'vod_name': video_details['vod_name'],
                'vod_pic': video_details['vod_pic'],
                'vod_play_url': video_play_url,
            }

        return {}

    def fetch_category_page(self, category_url, pg=1):
        """ 获取分类页面并提取视频列表 """
        try:
            url = f"{self.host}{category_url}page/{pg}/"
            html_content = self.fetch_html(url)
            doc = pq(html_content)

            articles = doc('article')
            video_list = self.getlist(articles)

            return {'list': video_list, 'page': pg, 'pagecount': 9999, 'total': len(video_list)}
        except Exception as e:
            self.log(f"分类页面加载失败: {str(e)}")
            return {'list': [], 'page': pg, 'pagecount': 0, 'total': 0}
            
