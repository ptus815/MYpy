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
                if not vod_pic and img_elem.attr('srcset'):
                    vod_pic = img_elem.attr('srcset').split(' ')[0]
                if vod_pic and not vod_pic.startswith('http'):
                    vod_pic = urljoin(self.host, vod_pic)

                vod_remarks = article('.video-info, .video-duration, [class*="duration"]').text().strip() or ''
                vod_year = ''

                vlist.append({
                    'vod_id': vod_url,  # 不进行base64编码，直接使用原始URL
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
            url = ids[0]  # 直接使用URL，不需要base64解码
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            doc = pq(resp.text)

            title = doc('meta[property="og:title"]').attr('content') or doc('h1').text().strip() or 'GayCock4U视频'
            vod_pic = doc('meta[property="og:image"]').attr('content') or ''
            if not vod_pic:
                img_elem = doc('img[src*="cover"], img[src*="poster"], img[src*="thumb"]').eq(0)
                vod_pic = img_elem.attr('src') or img_elem.attr('data-src') or ''
                if not vod_pic and img_elem.attr('srcset'):
                    vod_pic = img_elem.attr('srcset').split(' ')[0]

            tags = [t.text().strip() for t in doc('.entry-tags a, .post-tags a, a[href*="/tag/"]').items() if t.text().strip()]
            info_text = doc('.entry-meta, .post-meta').text().strip() or ''

            iframe_src = None
            # 首先尝试查找vide0.net的iframe（这是主要的播放器）
            vide0_patterns = [
                r'<iframe[^>]*src=["\'](https?://vide0\.net/[^"\']+)["\']',
                r'iframe.*?src=["\'](https?://vide0\.net/[^"\']+)["\']'
            ]
            
            for pattern in vide0_patterns:
                matches = re.findall(pattern, resp.text, re.IGNORECASE)
                if matches:
                    iframe_src = matches[0]
                    self.log(f"找到vide0.net iframe: {iframe_src}")
                    break
            
            # 如果没有找到vide0.net，尝试查找filemoon.to的iframe
            if not iframe_src:
                filemoon_patterns = [
                    r'<iframe[^>]*src=["\'](https?://filemoon\.to/[^"\']+)["\']',
                    r'iframe.*?src=["\'](https?://filemoon\.to/[^"\']+)["\']'
                ]
                
                for pattern in filemoon_patterns:
                    matches = re.findall(pattern, resp.text, re.IGNORECASE)
                    if matches:
                        iframe_src = matches[0]
                        self.log(f"找到filemoon.to iframe: {iframe_src}")
                        break
            
            # 如果没有找到filemoon.to，尝试查找d-s.io的iframe
            if not iframe_src:
                d_s_patterns = [
                    r'<iframe[^>]*src=["\'](https?://d-s\.io/[^"\']+)["\']',
                    r'iframe.*?src=["\'](https?://d-s\.io/[^"\']+)["\']'
                ]
                
                for pattern in d_s_patterns:
                    matches = re.findall(pattern, resp.text, re.IGNORECASE)
                    if matches:
                        iframe_src = matches[0]
                        self.log(f"找到d-s.io iframe: {iframe_src}")
                        break
            
            # 如果还是没有找到，尝试查找其他可能的播放器iframe
            if not iframe_src:
                other_iframes = re.findall(r'<iframe[^>]*src=["\'](https?://[^"\']+)["\']', resp.text, re.IGNORECASE)
                if other_iframes:
                    # 过滤掉广告iframe
                    for iframe in other_iframes:
                        if not any(ad_domain in iframe.lower() for ad_domain in ['adserver', 'juicyads', 'ads', 'chaseherbalpasty']):
                            iframe_src = iframe
                            self.log(f"找到其他播放器iframe: {iframe_src}")
                            break
            
            # 如果还是没有找到，记录错误
            if not iframe_src:
                self.log(f"未找到iframe src，使用详情页URL: {url}")
                iframe_src = url

            # 不对iframe src进行base64编码，直接传递给playerContent方法
            vod_play_url = iframe_src
            vod_content = ' | '.join(filter(None, [info_text]))
            
            # 根据iframe来源设置播放路线
            if 'vide0.net' in iframe_src:
                vod_play_from = 'vide0.net'
            elif 'filemoon.to' in iframe_src:
                vod_play_from = 'filemoon.to'
            elif 'd-s.io' in iframe_src:
                vod_play_from = 'd-s.io'
            else:
                vod_play_from = 'iframe'
            
            vod = {
                'vod_name': title,
                'vod_pic': vod_pic,
                'vod_content': vod_content,
                'vod_tag': ', '.join(tags) if tags else "GayCock4U",
                'vod_play_from': vod_play_from,
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
        url = id  # 直接使用URL，不需要base64解码
        
        if flag == 'vide0.net':
            try:
                # vide0.net 使用 dood 系统，需要特殊处理
                self.log(f"处理 vide0.net iframe: {url}")
                
                # 设置请求头
                headers_iframe = {
                    'User-Agent': self.headers['User-Agent'],
                    'Referer': self.host
                }
                
                # 直接返回 iframe URL，让播放器处理
                headers_final = {
                    'User-Agent': self.headers['User-Agent'],
                    'Referer': 'https://vide0.net/'
                }
                return {'parse': 1, 'url': url, 'header': headers_final}
                
            except Exception as e:
                self.log(f"vide0.net 解析失败: {str(e)}")
                return {'parse': 0, 'url': '', 'header': {}}
        
        elif flag == 'filemoon.to':
            try:
                # filemoon.to 直接返回 iframe URL
                self.log(f"处理 filemoon.to iframe: {url}")
                
                headers_final = {
                    'User-Agent': self.headers['User-Agent'],
                    'Referer': 'https://filemoon.to/'
                }
                return {'parse': 1, 'url': url, 'header': headers_final}
                
            except Exception as e:
                self.log(f"filemoon.to 解析失败: {str(e)}")
                return {'parse': 0, 'url': '', 'header': {}}
        
        elif flag == 'd-s.io':
            try:
                # 步骤 1: 请求 iframe 页面，动态提取 pass_md5 路径和 token
                headers_iframe = {
                    'User-Agent': self.headers['User-Agent'],
                    'Referer': self.host
                }
                resp_iframe = self.session.get(url, headers=headers_iframe, timeout=30)
                resp_iframe.raise_for_status()
                html_content = resp_iframe.text
                
                match = re.search(r"\$\.get\('(/pass_md5/[^']+)'", html_content)
                if not match:
                    raise ValueError("未在 iframe 页面源代码中找到 pass_md5 路径。")
                pass_md5_path = match.group(1)
                token = pass_md5_path.split('/')[-1]
                self.log(f"成功提取 pass_md5 路径: {pass_md5_path} 和 token: {token}")

                # 步骤 2: 发送 pass_md5 请求，获取视频基础链接
                pass_md5_url = f"https://d-s.io{pass_md5_path}"
                headers_pass_md5 = {
                    'User-Agent': self.headers['User-Agent'],
                    'Referer': url, # Referer 必须是 iframe URL
                    'Accept': '*/*',
                    'X-Requested-With': 'XMLHttpRequest'
                }
                resp_base_url = self.session.get(pass_md5_url, headers=headers_pass_md5, timeout=30)
                resp_base_url.raise_for_status()
                video_url_base = resp_base_url.text.strip()
                if not video_url_base:
                    raise ValueError("pass_md5 请求响应为空。")
                self.log(f"成功获取视频基础链接: {video_url_base}")

                # 步骤 3: 拼接最终链接并返回
                expiry_time = int(time.time() * 1000) + 3600000  # 转换为毫秒并加上一个小时
                if video_url_base.endswith('~'):
                    video_url_base = video_url_base[:-1]

                final_video_url = f"{video_url_base}?token={token}&expiry={expiry_time}"
                self.log(f"拼接最终链接: {final_video_url}")
                
                # 最终播放请求头
                headers_final_video = {
                    'User-Agent': self.headers['User-Agent'],
                    'Referer': 'https://d-s.io/', # Referer 必须是主域
                    'Range': 'bytes=0-',
                    'Accept': 'video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5',
                    'Accept-Encoding': 'identity',
                    'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
                    'Connection': 'keep-alive',
                    'Host': 'lo559mk.cloudatacdn.com',
                    'Referer': 'https://d-s.io/',
                    'Sec-Fetch-Dest': 'video',
                    'Sec-Fetch-Mode': 'no-cors',
                    'Sec-Fetch-Site': 'cross-site',
                    'Sec-GPC': '1'
                }
                return {'parse': 0, 'url': final_video_url, 'header': headers_final_video}

            except Exception as e:
                self.log(f"d-s.io 解析失败: {str(e)}")
                return {'parse': 0, 'url': '', 'header': {}}
        
        else:
            # 通用的默认处理逻辑，用于其他 iframe 源
            self.log(f"处理通用 iframe: {url}")
            headers = {
                'User-Agent': self.headers['User-Agent']
            }
            return {'parse': 1, 'url': url, 'header': headers}

