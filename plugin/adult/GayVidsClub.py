# -*- coding: utf-8 -*-
# by @ao
import json
import sys
import re
from base64 import b64decode, b64encode
from urllib.parse import urlparse, urljoin, quote
import requests
from pyquery import PyQuery as pq
from requests import Session
sys.path.append('..')
from base.spider import Spider

# 可选：动态 JS 执行支持
try:
    import js2py
    _JS2PY_AVAILABLE = True
except Exception:
    _JS2PY_AVAILABLE = False

class Spider(Spider):

    def init(self, extend=""):
        try:
            self.proxies = json.loads(extend) if extend else {}
        except:
            self.proxies = {}
        # 支持 ext 传入 {"http":"...","https":"..."} 或 {"proxy": {"http":"...","https":"..."}}
        if isinstance(self.proxies, dict) and 'proxy' in self.proxies and isinstance(self.proxies['proxy'], dict):
            self.proxies = self.proxies['proxy']
        # 统一补全协议前缀
        fixed = {}
        for k, v in (self.proxies or {}).items():
            if isinstance(v, str) and not v.startswith('http'):
                fixed[k] = f'http://{v}'
            else:
                fixed[k] = v
        self.proxies = fixed
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
        iframe_src = ""
        iframe_elem = data('iframe')
        if iframe_elem:
            iframe_src = iframe_elem.attr('src') or ""
        if not iframe_src:
            for attr in ['data-src', 'data-frame', 'data-iframe']:
                iframe_src = data(f'[{attr}]').attr(attr) or ""
                if iframe_src:
                    break
        if not iframe_src:
            scripts = data('script')
            for script in scripts.items():
                script_text = script.text()
                if script_text and 'iframe' in script_text and 'src' in script_text:
                    iframe_match = re.search(r'iframe.*?src=["\'](https?://[^"\']+mivalyo\.com[^"\']*)["\']', script_text, re.IGNORECASE)
                    if iframe_match:
                        iframe_src = iframe_match.group(1)
                        break
        if iframe_src and not iframe_src.startswith('http'):
            iframe_src = urljoin(self.host, iframe_src)
        
        # 解析 iframe 页面，提取真实视频地址
        play_urls = []
        if iframe_src:
            real_list = self.extract_media_from_iframe(iframe_src)
            for u in real_list:
                label = '播放' if len(real_list) == 1 else f'播放{real_list.index(u)+1}'
                # 传递直链与其 referer
                play_urls.append(f"{label}${self.e64(f'{u}@@@@{iframe_src}')}" )
        
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
            'vod_play_from': 'mivalyo' if play_urls else 'GayVidsClub',
            'vod_play_url': '#'.join(play_urls)
        }
        
        return {'list': [vod]}

    def searchContent(self, key, quick, pg="1"):
        if pg == 1:
            url = f"/?s={key}"
        else:
            url = f"/page/{pg}/?s={key}"
        
        data = self.getpq(url)
        return {'list': self.getlist(data("article")), 'page': pg}

    def playerContent(self, flag, id, vipFlags):
        # id 携带 直链@@@@referer
        decoded = self.d64(id)
        parts = decoded.split('@@@@') if decoded else ['']
        real_url = parts[0]
        referer = parts[1] if len(parts) > 1 else 'https://mivalyo.com/'
        headers = {
            'User-Agent': self.headers['User-Agent'],
            'Referer': referer,
            'Origin': re.match(r'https?://[^/]+', referer).group(0) if re.match(r'https?://[^/]+', referer) else 'https://mivalyo.com',
            'Accept': '*/*'
        }
        return {'parse': 0, 'url': real_url, 'header': headers}

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

    # --------------------- 内部辅助：解混淆并提取媒体链接 ---------------------
    def _js_unescape(self, text):
        """处理常见的 \xNN、\uNNNN 等编码。"""
        try:
            # 处理 \\xNN 和 \\uNNNN
            def repl(m):
                seq = m.group(0)
                try:
                    return bytes(seq, 'utf-8').decode('unicode_escape')
                except Exception:
                    return seq
            return re.sub(r"\\x[0-9a-fA-F]{2}|\\u[0-9a-fA-F]{4}", repl, text)
        except Exception:
            return text

    def _p_a_c_k_e_r_unpack(self, source):
        """简易的 P.A.C.K.E.R 解包器，处理 eval(function(p,a,c,k,e,d)...)"""
        try:
            m = re.search(r"eval\(function\(p,a,c,k,e,d\).*", source, re.S)
            if not m:
                return None
            payload = m.group(0)
            # 粗暴提取 k 数组
            k_match = re.search(r"\}\('(.*)',\s*(\d+),\s*(\d+),\s*'(.*)'\.split\('\|'\)\)", payload, re.S)
            if not k_match:
                return None
            p_enc, a_base, c_count, k_list = k_match.groups()
            a_base = int(a_base)
            c_count = int(c_count)
            try:
                p_text = bytes(p_enc, 'utf-8').decode('unicode_escape')
            except Exception:
                p_text = p_enc
            k_array = k_list.split('|')
            # 基于字典替换
            def baseN(num, b):
                digits = "0123456789abcdefghijklmnopqrstuvwxyz"
                if num == 0:
                    return '0'
                res = ''
                while num:
                    num, rem = divmod(num, b)
                    res = digits[rem] + res
                return res
            for i in range(c_count-1, -1, -1):
                key = baseN(i, a_base)
                if i < len(k_array) and k_array[i]:
                    p_text = re.sub(r"\b" + re.escape(key) + r"\b", k_array[i], p_text)
            return self._js_unescape(p_text)
        except Exception as e:
            print(f"JS解包失败: {e}")
            return None

    def _extract_with_js_engine(self, html):
        """使用 js2py 执行脚本，拦截 jwplayer.setup 等拿 sources。"""
        if not _JS2PY_AVAILABLE:
            return []
        try:
            ctx = js2py.EvalJs()
            ctx.execute("var window = {}; var document = {}; var navigator = {};")
            # atob/escape/unescape polyfill
            ctx.execute("""
            function atob(i){var b=Buffer?Buffer.from(i,'base64').toString('binary'):String(java.util.Base64.getDecoder().decode(i));return b}
            function btoa(i){return i}
            """)
            captured = []
            # 模拟 jwplayer
            ctx.captured = captured
            ctx.execute("""
            function jwplayer(){
              return { setup: function(cfg){ if(cfg && cfg.sources){ captured.push(JSON.stringify(cfg.sources)); } return {}; } };
            }
            """)
            # 执行所有内联脚本
            d = pq(html)
            for s in d('script').items():
                code = s.text() or ''
                if not code.strip():
                    src = s.attr('src') or ''
                    if src and src.startswith('http'):
                        try:
                            resp = requests.get(src, timeout=8).text
                            code = resp
                        except Exception:
                            code = ''
                if code:
                    try:
                        ctx.execute(code)
                    except Exception:
                        continue
            urls = []
            for item in list(ctx.captured):
                try:
                    arr = json.loads(item)
                    for it in arr:
                        u = it.get('file') or ''
                        if u and ('.m3u8' in u or '.mp4' in u):
                            if u not in urls:
                                urls.append(u)
                except Exception:
                    continue
            return urls
        except Exception as e:
            print(f"js2py 执行失败: {e}")
            return []

    def extract_media_from_iframe(self, iframe_url):
        """请求 iframe 页面，解混淆 JS，返回媒体直链列表"""
        try:
            headers = {
                'User-Agent': self.headers['User-Agent'],
                'Accept': '*/*',
                'Referer': iframe_url
            }
            html = self.session.get(iframe_url, headers=headers, timeout=15).text
        except Exception as e:
            print(f"获取 iframe 页面失败: {e}")
            return []
        media_urls = []
        # 先直接搜 .m3u8/.mp4
        for pat in [r'https?://[^"\'\s>]+?\.m3u8[^"\'\s>]*', r'https?://[^"\'\s>]+?\.mp4[^"\'\s>]*']:
            for u in re.findall(pat, html):
                if u not in media_urls:
                    media_urls.append(u)
        if media_urls:
            return media_urls
        # 解 P.A.C.K.E.R
        unpacked = self._p_a_c_k_e_r_unpack(html)
        if unpacked:
            for pat in [r'https?://[^"\'\s>]+?\.m3u8[^"\'\s>]*', r'https?://[^"\'\s>]+?\.mp4[^"\'\s>]*']:
                for u in re.findall(pat, unpacked):
                    if u not in media_urls:
                        media_urls.append(u)
            if media_urls:
                return media_urls
        # 动态执行（可选）
        dyn = self._extract_with_js_engine(html)
        for u in dyn:
            if u not in media_urls:
                media_urls.append(u)
        return media_urls
