# -*- coding: utf-8 -*-
import re
import json
import sys
import time
from urllib.parse import urljoin
from base64 import b64encode, b64decode

import requests
from pyquery import PyQuery as pq
sys.path.append('..')
from base.spider import Spider


class Spider(Spider):

    def init(self, extend=""):
        try:
            self.extend = json.loads(extend) if extend else {}
        except:
            self.extend = {}

        self.host = "https://gaycock4u.com"
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0',
        }

        self.session = requests.Session()
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
        return any(ext in url for ext in ['.m3u8', '.mp4', '.ts'])

    def manualVideoCheck(self):
        return False

    def destroy(self):
        pass

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
                if vod_pic and not vod_pic.startswith('http'):
                    vod_pic = urljoin(self.host, vod_pic)

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

            title = doc('meta[property="og:title"]').attr('content') or doc('h1').text().strip() or 'GayCock4U视频'
            vod_pic = doc('meta[property="og:image"]').attr('content') or ''
            if not vod_pic:
                img_elem = doc('img[src*="cover"], img[src*="poster"], img[src*="thumb"]').eq(0)
                vod_pic = img_elem.attr('src') or img_elem.attr('data-src') or ''

            tags = [t.text().strip() for t in doc('.entry-tags a, .post-tags a, a[href*="/tag/"]').items() if t.text().strip()]
            info_text = doc('.entry-meta, .post-meta').text().strip() or ''

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
                'vod_play_from': 'd-s.io',  # 播放路线标识
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
            self.log(f"搜索失败: {str(e)}")
            return {'list': []}

    def playerContent(self, flag, id, vipFlags):
        url = self.d64(id)
        
        # d-s.io 路线的解析逻辑
        if flag == 'd-s.io':
            try:
                resp_iframe = self.session.get(url, timeout=30)
                resp_iframe.raise_for_status()
                html_content = resp_iframe.text

                match = re.search(r"\$\.get\('(/pass_md5/[^']+)'", html_content)
                if not match:
                    raise ValueError("未在 iframe 页面源代码中找到 pass_md5 路径。")
                pass_md5_path = match.group(1)
                token = pass_md5_path.split('/')[-1]

                pass_md5_url = f"https://d-s.io{pass_md5_path}"
                resp_base_url = self.session.get(pass_md5_url, headers={'Referer': url}, timeout=30)
                resp_base_url.raise_for_status()
                video_url_base = resp_base_url.text.strip()
                if not video_url_base:
                    raise ValueError("pass_md5 请求响应为空。")

                expiry_time = int(time.time() * 1000) + 3600000  # 转换为毫秒并加上一个小时
                if video_url_base.endswith('~'):
                    video_url_base = video_url_base[:-1]

                final_video_url = f"{video_url_base}?token={token}&expiry={expiry_time}"
                
                headers = {
                    'User-Agent': self.headers['User-Agent'],
                    'Referer': url,
                    'Range': 'bytes=0-'
                }
                return {'parse': 0, 'url': final_video_url, 'header': headers}

            except Exception as e:
                self.log(f"d-s.io 解析失败: {str(e)}")
                return {'parse': 0, 'url': '', 'header': ''}
        
        # 通用的默认处理逻辑，用于其他非 d-s.io 的链接
        headers = {
            'User-Agent': self.headers['User-Agent']
        }
        return {'parse': 1, 'url': url, 'header': headers}
