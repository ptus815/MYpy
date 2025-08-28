# -*- coding: utf-8 -*-
# by @ao (修复版)
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

# -------------------------
# JS P.A.C.K.E.R. 解包器（常见 eval(function(p,a,c,k,e,d)...）实现）
# 参考多种开源实现，做了一个较为通用的 Python 解包函数
# -------------------------
def detect_packed_js(source):
    """检测是否为p.a.c.k.e.r. 打包代码"""
    if not source:
        return False
    # 常见的 pattern：eval(function(p,a,c,k,e,d)...
    return re.search(r'eval\(function\(p,a,c,k,e,(?:r|d)\)', source) is not None or re.search(r"p,a,c,k,e,(?:r|d)\)\)", source) is not None

def unpack_packed_js(source):
    """
    尝试解包 P.A.C.K.E.R. 风格的 JS。返回解包后的字符串或原始字符串（若解包失败）。
    说明：这个解包器覆盖常见的 p.a.c.k.e.r. 模式；并不是运行 JS，只是模拟解包逻辑。
    """
    try:
        # 找到 eval(function(p,a,c,k,e,d)... 包裹体
        payload_match = re.search(r"eval\(function\(p,a,c,k,e,(?:r|d)\).*?\)\)", source, re.S)
        if not payload_match:
            # 也可能直接是 'function(p,a,c,k,e,d){...}(...'
            payload_match = re.search(r"function\(p,a,c,k,e,(?:r|d)\).*?}\((?:'|\")", source, re.S)
            if not payload_match:
                return source
        payload = payload_match.group(0)

        # 提取 p, a, c, k 部分：寻找最后一对括号内的参数（通常为 '...string...', radix, count, 'k'.split('|')）
        args_match = re.search(r"\}\((?P<args>.*)\)\s*;?\s*$", payload, re.S)
        if not args_match:
            # 尝试更宽松匹配
            args_match = re.search(r"\}\((?P<args>.*)\)\)", payload, re.S)
            if not args_match:
                return source
        args = args_match.group('args')

        # 分割参数（注意参数内可能含有逗号，需要精确解析——我们用简单策略：先提取第一个字符串常量作为 p）
        # 提取第一个引号包裹的字符串作为 p
        p_match = re.match(r"\s*(['\"])(?P<p>.*?)(?<!\\)\1\s*,\s*(?P<rest>.*)$", args, re.S)
        if not p_match:
            return source
        p = p_match.group('p')
        rest = p_match.group('rest')

        # rest 通常是: base,a,c,'k'.split('|'),0,{}
        # 取 a 和 c
        rest_parts = rest.split(',', 3)
        if len(rest_parts) < 2:
            return source
        try:
            a = int(re.sub(r"[^\d]", "", rest_parts[0]))
        except:
            # 可能是 '0x1a' 形式
            try:
                a = int(rest_parts[0], 0)
            except:
                a = 62
        try:
            c = int(re.sub(r"[^\d]", "", rest_parts[1]))
        except:
            try:
                c = int(rest_parts[1], 0)
            except:
                c = 0

        # 提取 k array: 查找 .split('|') 之前的字符串
        k_match = re.search(r"(['\"])(?P<k>.*?)\1\.split\('\|'\)", rest, re.S)
        if k_match:
            k = k_match.group('k').split('|')
        else:
            k = []

        # 模拟解包（经典算法）
        def baseN(num, radix):
            # 将 num 转为 radix 进制字符串（小写）
            if num == 0:
                return '0'
            digits = []
            while num:
                d = num % radix
                if d < 10:
                    digits.append(chr(ord('0') + d))
                else:
                    digits.append(chr(ord('a') + d - 10))
                num //= radix
            return ''.join(reversed(digits))

        # 构建字典
        repl = {}
        for i in range(len(k)):
            repl[baseN(i, a)] = k[i]

        # 替换 p 中的词汇
        # p 内的词边界是 \b，但 p 可能包含数字和下划线等，使用较严格的替换
        def replace_token(match):
            token = match.group(0)
            return repl.get(token, token)

        if a and k:
            pattern = r'\b[0-9a-zA-Z]+\b'
            decoded = re.sub(pattern, replace_token, p)
            return decoded
        else:
            return p
    except Exception as e:
        # 解包失败时返回原始
        return source

# -------------------------
# 其它辅助提取函数
# -------------------------
def extract_urls_from_text(text):
    """从文本中提取可能的播放链接（m3u8, mp4, .ts, 其他视频源）"""
    urls = []
    if not text:
        return urls
    # common patterns
    patterns = [
        r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*',
        r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*',
        r'https?://[^\s"\'<>]+\.m3u[^\s"\'<>]*',  # catch similar
        r'https?://[^\s"\'<>]+/master[^"\']*',     # sometimes "master" file name
    ]
    for pat in patterns:
        for m in re.finditer(pat, text, re.I):
            urls.append(m.group(0))
    # 去重保持顺序
    seen = set()
    out = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out

def try_decode_atob_like(s):
    """尝试识别并解码 atob('...') / base64 字符串"""
    if not s:
        return None
    # 找 atob('....') 或 "atob(\"...\")"
    m = re.search(r'atob\(\s*["\']([A-Za-z0-9+/=]+)["\']\s*\)', s)
    if m:
        try:
            return b64decode(m.group(1)).decode('utf-8', errors='ignore')
        except:
            return None
    # 直接裸 base64 字符串可能出现在代码中
    m2 = re.search(r'["\']([A-Za-z0-9+/=]{40,})["\']', s)
    if m2:
        try:
            return b64decode(m2.group(1)).decode('utf-8', errors='ignore')
        except:
            return None
    return None

# -------------------------
# Spider 类实现（修复版）
# -------------------------
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
        """
        解析视频详情页：仅负责获取页面信息和 iframe 链接（不再硬编码 m3u8）
        返回 vod_play_url 使用 base64 编码：iframe_url@@@@detail_url
        playerContent 会解码并继续解析 iframe 页面获取 m3u8
        """
        detail_url = ids[0]
        data = self.getpq(detail_url)

        # 获取视频标题
        title = data('h1').text().strip() or data('.entry-title').text().strip()

        # 获取视频信息
        info_text = ""
        meta_elem = data('.entry-meta, .post-meta')
        if meta_elem:
            info_text = meta_elem.text().strip()

        # 获取观看次数 (尝试多种选择)
        views_text = ""
        # 找包含 views 的文本
        v_elems = data(':contains("views"), :contains("Views"), :contains("观看")')
        if v_elems:
            # 找第一个可能包含 views 的父或自身
            for ve in v_elems.items():
                t = ve.text().strip()
                if 'views' in t.lower() or '观看' in t:
                    views_text = t
                    break

        # 获取标签信息
        tags = []
        for tag in data('.entry-tags a, .post-tags a, a[href*="/tag/"]').items():
            tag_text = tag.text().strip()
            if tag_text and tag_text not in tags:
                tags.append(tag_text)

        # 提取 iframe src
        iframe_src = ""
        # 方法1: 直接 iframe 标签
        iframe_elem = data('iframe').eq(0)
        if iframe_elem:
            iframe_src = iframe_elem.attr('src') or ""

        # 方法2: 正则从原始 html 中提取 <iframe ... src="...">
        if not iframe_src:
            raw_html = data.html()
            if raw_html:
                m = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', raw_html, re.I)
                if m:
                    iframe_src = m.group(1)

        # 完善相对地址
        if iframe_src and not iframe_src.startswith('http'):
            iframe_src = urljoin(self.host, iframe_src)

        # 构建 vod
        content_parts = []
        if info_text:
            content_parts.append(f"信息: {info_text}")
        if views_text:
            content_parts.append(f"观看: {views_text}")
        if tags:
            content_parts.append(f"标签: {', '.join(tags)}")

        vod = {
            'vod_name': title or "GayVidsClub视频",
            'vod_content': ' | '.join(content_parts) if content_parts else "GayVidsClub视频",
            'vod_tag': ', '.join(tags) if tags else "GayVidsClub",
            'vod_play_from': 'mivalyo',
            'vod_play_url': ''
        }

        play_urls = []
        if iframe_src:
            # 把 iframe URL 与 detail_url 一并编码传给 playerContent
            encoded = self.e64(f'{iframe_src}@@@@{detail_url}')
            play_urls.append(f"播放${encoded}")
            vod['vod_play_url'] = '#'.join(play_urls)
        else:
            # 没有 iframe，尝试从页面找直接的 m3u8/mp4 链接并返回
            raw = data.outerHtml() if hasattr(data, 'outerHtml') else data.html()
            found = extract_urls_from_text(raw or "")
            if found:
                # 直接使用第一个找出的链接
                encoded = self.e64(f'{found[0]}@@@@{detail_url}')
                play_urls.append(f"播放${encoded}")
                vod['vod_play_url'] = '#'.join(play_urls)

        return {'list': [vod]}

    def searchContent(self, key, quick, pg="1"):
        if pg == 1:
            url = f"/?s={quote(key)}"
        else:
            url = f"/page/{pg}/?s={quote(key)}"

        data = self.getpq(url)
        return {'list': self.getlist(data("article")), 'page': pg}

    def playerContent(self, flag, id, vipFlags):
        """
        id 是 base64 编码的 'iframe_url@@@@detail_url' 或者 'm3u8_url@@@@detail_url'
        本函数负责：
         - 解码 id
         - 如果是 iframe 链接，GET iframe 页面
         - 尝试从 iframe 页面或其内嵌脚本中解出真实播放地址（m3u8/mp4）
         - 支持：直接链接查找、JSON sources、P.A.C.K.E.R. 解包、atob/base64 解码等
        返回格式：
          {'parse': 0, 'url': m3u8_url, 'header': headers}
        """
        ids = self.d64(id).split('@@@@')
        if len(ids) >= 1:
            first = ids[0].strip()
        else:
            return {'parse': 0, 'url': ''}

        # 如果 first 已经是 m3u8 或 mp4，直接返回
        if re.search(r'\.m3u8($|[?/#])', first) or re.search(r'\.mp4($|[?/#])', first):
            headers = {
                'User-Agent': self.headers.get('User-Agent'),
                'Referer': ids[1] if len(ids) > 1 else self.host
            }
            return {'parse': 0, 'url': first, 'header': headers}

        iframe_url = first
        try:
            # 请求 iframe 页面
            resp = self.session.get(iframe_url, timeout=15, headers={
                'User-Agent': self.headers.get('User-Agent'),
                'Referer': ids[1] if len(ids) > 1 else self.host
            })
            html = resp.text or ""

            # 1) 直接在 HTML 中寻找 m3u8/mp4
            found = extract_urls_from_text(html)
            if found:
                url0 = found[0]
                headers = {
                    'User-Agent': self.headers.get('User-Agent'),
                    'Referer': iframe_url,
                    'Host': urlparse(url0).netloc
                }
                return {'parse': 0, 'url': url0, 'header': headers}

            # 2) 查找常见 JS 变量形式，例如 sources = [{file: "..."}]
            # pattern1: file:"...", src:"..."
            js_sources = re.findall(r'(?:file|src)\s*[:=]\s*["\']([^"\']+\.(?:m3u8|mp4)[^"\']*)["\']', html, re.I)
            if js_sources:
                url0 = js_sources[0]
                if not url0.startswith('http'):
                    url0 = urljoin(iframe_url, url0)
                headers = {
                    'User-Agent': self.headers.get('User-Agent'),
                    'Referer': iframe_url,
                    'Host': urlparse(url0).netloc
                }
                return {'parse': 0, 'url': url0, 'header': headers}

            # 3) 尝试解混淆 P.A.C.K.E.R. 风格的 JS
            scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.S | re.I)
            for s in scripts:
                if not s or len(s) < 20:
                    continue
                if detect_packed_js(s):
                    unpacked = unpack_packed_js(s)
                    # 解包后搜索
                    found2 = extract_urls_from_text(unpacked)
                    if found2:
                        url0 = found2[0]
                        if not url0.startswith('http'):
                            url0 = urljoin(iframe_url, url0)
                        headers = {
                            'User-Agent': self.headers.get('User-Agent'),
                            'Referer': iframe_url,
                            'Host': urlparse(url0).netloc
                        }
                        return {'parse': 0, 'url': url0, 'header': headers}
                    # 也尝试 atob 解码
                    at = try_decode_atob_like(unpacked)
                    if at:
                        ffound = extract_urls_from_text(at)
                        if ffound:
                            url0 = ffound[0]
                            if not url0.startswith('http'):
                                url0 = urljoin(iframe_url, url0)
                            headers = {
                                'User-Agent': self.headers.get('User-Agent'),
                                'Referer': iframe_url,
                                'Host': urlparse(url0).netloc
                            }
                            return {'parse': 0, 'url': url0, 'header': headers}

            # 4) 脚本未被 eval packer 包装，但可能包含 base64/atob
            for s in scripts:
                decoded = try_decode_atob_like(s)
                if decoded:
                    found3 = extract_urls_from_text(decoded)
                    if found3:
                        url0 = found3[0]
                        if not url0.startswith('http'):
                            url0 = urljoin(iframe_url, url0)
                        headers = {
                            'User-Agent': self.headers.get('User-Agent'),
                            'Referer': iframe_url,
                            'Host': urlparse(url0).netloc
                        }
                        return {'parse': 0, 'url': url0, 'header': headers}

            # 5) 有些页面通过 XHR 请求加载真正的播放地址，尝试寻找 xhr URL 或 token
            # 尝试寻找形如 fetch('https://.../get_source.php?hash=...') 或 "/get_source.php?hash=..."
            ajax_match = re.search(r'(https?://[^"\']*?get[_-]source[^"\']*)', html, re.I)
            if not ajax_match:
                ajax_match = re.search(r'(["\'])(/[^"\']*?get[_-]source[^"\']*)\1', html, re.I)
            if ajax_match:
                ajax_url = ajax_match.group(1) if ajax_match.group(1).startswith('http') else urljoin(iframe_url, ajax_match.group(2))
                try:
                    r2 = self.session.get(ajax_url, headers={'Referer': iframe_url, 'User-Agent': self.headers.get('User-Agent')}, timeout=10)
                    if r2 and r2.text:
                        ffs = extract_urls_from_text(r2.text)
                        if ffs:
                            url0 = ffs[0]
                            if not url0.startswith('http'):
                                url0 = urljoin(iframe_url, url0)
                            headers = {
                                'User-Agent': self.headers.get('User-Agent'),
                                'Referer': iframe_url,
                                'Host': urlparse(url0).netloc
                            }
                            return {'parse': 0, 'url': url0, 'header': headers}
                except Exception:
                    pass

            # 6) 最后尝试再次对所有 script 做更强力的解包/搜索（包含拼接形式）
            for s in scripts:
                # 合并字符串拼接，如 "https://" + "host" + "/path/master.m3u8"
                pieces = re.findall(r'(["\']https?://[^"\']+["\'](?:\s*\+\s*["\'][^"\']+["\'])+)', s)
                for p in pieces:
                    # 移除引号和加号
                    p_clean = re.sub(r'["\']\s*\+\s*["\']', '', p)
                    p_clean = p_clean.replace('"', '').replace("'", '').strip()
                    ffs = extract_urls_from_text(p_clean)
                    if ffs:
                        url0 = ffs[0]
                        if not url0.startswith('http'):
                            url0 = urljoin(iframe_url, url0)
                        headers = {
                            'User-Agent': self.headers.get('User-Agent'),
                            'Referer': iframe_url,
                            'Host': urlparse(url0).netloc
                        }
                        return {'parse': 0, 'url': url0, 'header': headers}

            # 如果以上全部失败，则无法在静态 HTML 中解析到 m3u8
            return {'parse': 0, 'url': ''}

        except Exception as e:
            print(f"playerContent 解析失败: {e}")
            return {'parse': 0, 'url': ''}

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
