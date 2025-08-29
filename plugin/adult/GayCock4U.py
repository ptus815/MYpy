import re
import json
import sys
import time
import random
import string
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
                'vod_id': self.e64(vod_url),
                'vod_name': vod_name,
                'vod_pic': vod_pic,
                'vod_year': vod_year,
                'vod_remarks': vod_remarks,
                'style': {'ratio': 1.33, 'type': 'rect'}
            })
        except Exception as e:
            try:
                self.log(f"解析视频失败: {str(e)}")
            except:
                pass
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
        try:
            self.log(f"获取分类内容失败: {str(e)}")
        except:
            pass
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
            'vod_play_from': 'Push',
            'vod_play_url': f'播放${vod_play_url}'
        }
        return {'list': [vod]}
    except Exception as e:
        try:
            self.log(f"获取视频详情失败: {str(e)}")
        except:
            pass
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
        try:
            self.log(f"搜索失败: {str(e)}")
        except:
            pass
        return {'list': []}

def playerContent(self, flag, id, vipFlags):
    """
    支持 iframe XHR 嗅探：
    1. 如果 Push 解析失败，尝试从 iframe src 获取真实视频链接（d-s.io 流程）。
    2. 支持 mp4 / m3u8 自动解析。
    """
    url = self.d64(id)
    headers = {
        'User-Agent': self.headers['User-Agent'],
        'Referer': self.host,
        'Accept': '*/*',
        'X-Requested-With': 'XMLHttpRequest'
    }

    # d-s.io 链接处理
    if 'd-s.io' in url:
        try:
            # 1) 请求 iframe 页面以获取 cookie 和页面 JS
            page_headers = {
                'User-Agent': self.headers['User-Agent'],
                'Referer': self.host,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            resp = self.session.get(url, headers=page_headers, timeout=30)
            resp.raise_for_status()
            text = resp.text

            # 2) 尝试提取 pass_md5 链接（可能是相对或绝对）
            m_pass = re.search(r'(https?://d-s\.io/pass_md5/[^\s\'"]+|/pass_md5/[^\s\'"]+)', text)
            if not m_pass:
                # 备选：有时JS里写成 $.get('/pass_md5/....'
                m_pass = re.search(r"/pass_md5/[^'\"\s)]+", text)
            if not m_pass:
                
                return {'parse': 1, 'url': url, 'header': headers}

            pass_md5_url = m_pass.group(0)
            if pass_md5_url.startswith('/'):
                pass_md5_url = urljoin('https://d-s.io', pass_md5_url)

            # 3) 从页面或 pass_md5 链接中提取 token（取最后一个路径段为 token）
            token_val = None
            m_token = re.search(r'token=([A-Za-z0-9_\-]+)', text)
            if m_token:
                token_val = m_token.group(1)
            else:
                # 从 pass_md5 url 末尾取 token
                try:
                    token_val = pass_md5_url.rstrip('/').split('/')[-1]
                except:
                    token_val = None

            if not token_val:
                # 没有 token，回退
                return {'parse': 1, 'url': url, 'header': headers}

            # 4) 请求 pass_md5（XHR 风格）拿到 CDN base
            ajax_headers = {
                'User-Agent': self.headers['User-Agent'],
                'Accept': '*/*',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': url,
            }
            r = self.session.get(pass_md5_url, headers=ajax_headers, timeout=30)
            r.raise_for_status()
            base = r.text.strip().strip('\'" \r\n')
            if not base:
                # 未取得正确 base，回退
                return {'parse': 1, 'url': url, 'header': headers}

            # 5) 构造 final_url：base + 10 随机字符 + ?token=...&expiry=Date.now()
            rand10 = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))
            expiry_ms = int(time.time() * 1000)
            final_url = f"{base}{rand10}?token={token_val}&expiry={expiry_ms}"

            # 6) 请求 final_url（保持同一 session），使用接近浏览器的视频请求头
            video_headers = {
                'User-Agent': self.headers['User-Agent'],
                'Referer': 'https://d-s.io/',
                'Accept': 'video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5',
                'Accept-Encoding': 'identity',
                'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.3,en;q=0.2',
                'Connection': 'keep-alive',
                'Range': 'bytes=0-',
                'Sec-Fetch-Dest': 'video',
                'Sec-Fetch-Mode': 'no-cors',
                'Sec-Fetch-Site': 'cross-site',
            }
            r2 = self.session.get(final_url, headers=video_headers, stream=True, allow_redirects=True, timeout=30)

           
            ct = (r2.headers.get('content-type') or '').lower()
            final_requested_url = r2.url
            if 'video' in ct or final_requested_url.endswith('.mp4') or '.mp4' in final_requested_url:
                return {'parse': 0, 'url': final_url, 'header': video_headers}
        
            if 'mpegurl' in ct or '.m3u8' in final_requested_url:
                return {'parse': 0, 'url': final_url, 'header': video_headers}

        
            return {'parse': 0, 'url': final_url, 'header': video_headers}
        except Exception as e:
            try:
                self.log(f"d-s.io 播放链接解析失败: {str(e)}")
            except:
                pass
            return {'parse': 1, 'url': url, 'header': headers}

    # 非 d-s.io 链接：直接返回原始 url
    return {'parse': 1, 'url': url, 'header': headers}
