# -*- coding: utf-8 -*-
#author🍑
import re
import json
import sys
import time
from urllib.parse import urljoin, urlparse
import requests
from pyquery import PyQuery as pq
sys.path.append('..')
from base.spider import Spider
class Spider(Spider):
    def init(self, extend=""):
        try: self.extend = json.loads(extend) if extend else {}
        except: self.extend = {}
        self.host = "https://www.javboys.tv/"
        self.headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'zh-CN,zh;q=0.8', 'Connection': 'keep-alive', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0'}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    def getName(self): return "javboys.tv"
    def isVideoFormat(self, url): return any(ext in url for ext in ['.m3u8', '.mp4', '.ts'])
    def manualVideoCheck(self): return False
    def destroy(self): pass
    def homeContent(self, filter):
        cateManual = [{'type_name': 'OnlyFans', 'type_id': '/category/onlyfans/'}, {'type_name': '动漫', 'type_id': '/category/yaoi/'}, {'type_name': 'trance', 'type_id': '/category/trance-video/'},{'type_name': 'west', 'type_id': '/category/western-gay-porn-hd/'},{'type_name': 'non', 'type_id': '/category/nonkeproject/'}]
        return {'class': cateManual, 'filters': {}}
    def _collect_posts(self, doc: pq):
        def normalize(href: str) -> str:
            if not href: return ''
            href = href.strip()
            if href.startswith('//'): href = 'https:' + href
            if href.startswith('/'): href = urljoin(self.host, href)
            return href
        candidates = {}
        for a in doc('a').items():
            raw = a.attr('href') or ''
            href = normalize(raw)
            if not href: continue
            try: u = urlparse(href)
            except Exception: continue
            if not (u.scheme in ('http', 'https') and u.netloc.endswith('javboys.tv')): continue
            if not re.search(r'/20\d{2}/\d{2}/', u.path): continue
            if any(x in u.path for x in ['/tag/', '/category/', '/page/']) or ('?s=' in href): continue
            text = (a.text() or '').strip()
            if href not in candidates or (text and len(text) > len(candidates[href]['vod_name'])): candidates[href] = {'vod_id': href, 'vod_name': text}
        vlist = []
        for href, item in candidates.items():
            title = item['vod_name'] or href.strip('/').split('/')[-1].replace('-', ' ').title()
            vod_pic = ''
            img = doc(f'a[href="{href}"] img').eq(0)
            if img:
                vod_pic = img.attr('src') or img.attr('data-src') or img.attr('data-lazy-src') or img.attr('data-original') or ''
                if not vod_pic and img.attr('srcset'): vod_pic = (img.attr('srcset') or '').split(' ')[0]
            if not vod_pic:
                nodes = doc(f'a[href="{href}"]')
                if nodes:
                    parent = nodes.parents().eq(0)
                    for _ in range(3):
                        if not parent: break
                        im = parent.find('img').eq(0)
                        if im and (im.attr('src') or im.attr('data-src') or im.attr('data-lazy-src') or im.attr('data-original') or im.attr('srcset')):
                            vod_pic = im.attr('src') or im.attr('data-src') or im.attr('data-lazy-src') or im.attr('data-original') or ''
                            if not vod_pic and im.attr('srcset'): vod_pic = (im.attr('srcset') or '').split(' ')[0]
                            break
                        parent = parent.parents().eq(0)
            if vod_pic and not vod_pic.startswith('http'): vod_pic = urljoin(self.host, vod_pic)
            vod_remarks = next((t.text().strip() for t in doc(f'a[href="{href}"]').items() if re.search(r'\b\d{1,2}:\d{2}\b', t.text().strip()) or 'HD' in t.text().strip()), '')
            vlist.append({'vod_id': href, 'vod_name': title, 'vod_pic': vod_pic, 'vod_year': '', 'vod_remarks': vod_remarks, 'style': {'ratio': 1.33, 'type': 'rect'}})
        return vlist
    def homeVideoContent(self): return self.categoryContent('', '1', False, {})
    def categoryContent(self, tid, pg, filter, extend):
        result = {'page': pg, 'pagecount': 9999, 'limit': 90, 'total': 999999}
        base = tid if tid and str(tid).startswith('http') else urljoin(self.host, str(tid).lstrip('/')) if tid else self.host
        if not base.endswith('/'): base += '/'
        url = urljoin(base, f'page/{pg}/') if pg != '1' else base
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            doc = pq(resp.text)
            result['list'] = self._collect_posts(doc)
        except Exception: result['list'] = []
        return result
    def detailContent(self, ids):
        try:
            url = ids[0]
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            html = resp.text
            doc = pq(html)
            title = doc('meta[property="og:title"]').attr('content') or doc('h1').text().strip() or 'Javboys视频'
            vod_pic = doc('meta[property="og:image"]').attr('content') or (doc('img[src*="cover"], img[src*="poster"], img[src*="thumb"]').eq(0).attr('src') or doc('img[src*="cover"], img[src*="poster"], img[src*="thumb"]').eq(0).attr('data-src') or (doc('img[src*="cover"], img[src*="poster"], img[src*="thumb"]').eq(0).attr('srcset') or '').split(' ')[0])
            tags = [t.text().strip() for t in doc('a[href*="/tag/"]').items() if t.text().strip()]
            info_text = doc('.entry-meta, .post-meta').text().strip() or ''
            candidate_urls = []
            for node in doc('#player .video-player').items():
                src = (node.attr('data-src') or '').strip()
                if not src: continue
                if src.startswith('//'): src = 'https:' + src
                if src.startswith('/'): src = urljoin(self.host, src)
                src = src.replace('https://vide0.net/', 'https://d-s.io/').replace('http://vide0.net/', 'https://d-s.io/')
                candidate_urls.append(src)
            seen, uniq = set(), []
            for u in candidate_urls:
                if u and u not in seen:
                    seen.add(u)
                    uniq.append(u)
            d_s_urls = [u for u in uniq if 'd-s.io' in u]
            push_urls = [u for u in uniq if 'd-s.io' not in u]
            play_from, play_urls = [], []
            if d_s_urls:
                play_from.append('d-s.io')
                if len(d_s_urls) == 1: play_urls.append(f'播放${d_s_urls[0]}')
                else: play_urls.append('#'.join([f'播放{i+1}${u}' for i, u in enumerate(d_s_urls)]))
            if push_urls:
                play_from.append('Push')
                if len(push_urls) == 1: play_urls.append(f'播放${push_urls[0]}')
                else: play_urls.append('#'.join([f'播放{i+1}${u}' for i, u in enumerate(push_urls)]))
            if not play_from: return {'list': []}
            vod = {'vod_name': title, 'vod_pic': vod_pic, 'vod_content': ' | '.join(filter(None, [info_text])), 'vod_tag': ', '.join(tags) if tags else "Javboys", 'vod_play_from': '$$$'.join(play_from), 'vod_play_url': '$$$'.join(play_urls)}
            return {'list': [vod]}
        except Exception: return {'list': []}
    def _resolve_d_s_io(self, url: str, referer: str):
        headers_iframe = {'User-Agent': self.headers['User-Agent'], 'Referer': referer}
        resp_iframe = self.session.get(url, headers=headers_iframe, timeout=30)
        resp_iframe.raise_for_status()
        match = re.search(r"\$\.get\([\"'](/pass_md5/[^\"']+)[\"']", resp_iframe.text)
        pass_md5_url = f"https://d-s.io{match.group(1)}" if match else ''
        headers_pass_md5 = {'User-Agent': self.headers['User-Agent'], 'Referer': url, 'Origin': 'https://d-s.io', 'Accept': '*/*', 'X-Requested-With': 'XMLHttpRequest', 'Accept-Encoding': 'gzip, deflate'}
        resp_base_url = self.session.get(pass_md5_url, headers=headers_pass_md5, timeout=30)
        resp_base_url.raise_for_status()
        video_url_base = resp_base_url.text.strip().rstrip('~')
        token = match.group(1).split('/')[-1] if match else ''
        expiry_time = int(time.time() * 1000) + 3600000
        final_video_url = f"{video_url_base}?token={token}&expiry={expiry_time}"
        headers_final_video = {'User-Agent': self.headers['User-Agent'], 'Referer': 'https://d-s.io/', 'Range': 'bytes=0-', 'Accept': 'video/*;q=0.9,*/*;q=0.5', 'Accept-Encoding': 'identity', 'Connection': 'keep-alive'}
        return {'parse': 0, 'url': final_video_url, 'header': headers_final_video}
    def playerContent(self, flag, id, vipFlags):
        url = id
        try:
            if flag == 'vide0.net': url = url.replace('https://vide0.net/', 'https://d-s.io/')
            if flag in ['vide0.net', 'd-s.io']: return self._resolve_d_s_io(url, referer=self.host)
            if flag == 'Push':
                headers = {'User-Agent': self.headers['User-Agent'],'Referer': self.host}
                return {'parse': 1, 'url': url, 'header': headers}
        except Exception: pass
        return {'parse': 0, 'url': '', 'header': {}}
    def searchContent(self, key, quick, pg="1"):
        try:
            resp = self.session.get(self.host, params={'s': key}, timeout=30)
            resp.raise_for_status()
            doc = pq(resp.text)
            vlist = self._collect_posts(doc)
            return {'list': vlist, 'page': pg, 'pagecount': 9999, 'limit': 90, 'total': 999999}
        except Exception: return {'list': []}
