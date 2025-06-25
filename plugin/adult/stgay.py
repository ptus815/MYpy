# coding=utf-8
# !/usr/bin/python
# by嗷呜 

import sys
from base64 import b64decode, b64encode
from pyquery import PyQuery as pq
from requests import Session
from urllib.parse import quote
import re
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
        return "stgay"

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

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

    def homeContent(self):
        result = {}
        cateManual = {
            "当前最热": "/视频/当前最热",
            "最近更新": "/视频/最近更新",
            "体育生": "/视频/search/体育生",
            "直男": "/视频/search/直男",
            "白袜": "/视频/search/白袜",
            "开火车": "/视频/search/开火车",
            "口交": "/视频/search/口交",
            "乱伦": "/视频/search/乱伦",
            "迷奸": "/视频/search/迷奸",
            "主奴": "/视频/search/主奴",
            "网黄": "/视频/search/网黄",
            "厕所": "/视频/search/厕所"
        }
        classes = []
        for k in cateManual:
            classes.append({
                'type_name': k,
                'type_id': cateManual[k]
            })
        result['class'] = classes
        result['list'] = self.homeVideoContent()['list']
        return result

    def categoryContent(self, tid, pg, filter, extend):
        vdata = []
        result = {}
        result['page'] = pg
        result['pagecount'] = 9999
        result['limit'] = 90
        result['total'] = 999999

        url = ""
        if tid == "/视频/当前最热" or tid == "/视频/最近更新":
            url = f'{tid}/page/{pg}'
        elif tid.startswith("/视频/search/"):
            url = f'{tid}/{pg}'
        else:
            # Fallback or error handling for unrecognised tid
            print(f"未知分类ID: {tid}")
            result['list'] = []
            return result

        data = self.getpq(url)
        vdata = self.getlist(data("main > generic:nth-child(2) > list > listitem"))

        result['list'] = vdata
        return result

    def detailContent(self, ids):
        data = self.getpq(ids[0])
        vn = data('meta[property="og:title"]').attr('content')
        vod = {
            'vod_name': vn,
            'vod_director': '',
            'vod_remarks': data('.duration').text(),
            'vod_play_from': 'stgay',
            'vod_play_url': ''
        }
        plist = []

        # 尝试从video标签中直接获取m3u8链接
        video_src = data('video').attr('src')
        if video_src and ('.m3u8' in video_src or '.mp4' in video_src):
            encoded = self.e64(f'{0}@@@@{video_src}')
            plist.append(f"自动选择${encoded}")
        else:
            # 如果video标签中没有，尝试从script中查找m3u8链接
            scripts = data('script')
            for script in scripts.items():
                script_text = script.text()
                # 查找m3u8或mp4链接
                match = re.search(r'(https?://[\w./%-]+\.(?:m3u8|mp4)(?:\?[\w=&%-]+)?)', script_text)
                if match:
                    video_url = match.group(1)
                    encoded = self.e64(f'{0}@@@@{video_url}')
                    plist.append(f"自动选择${encoded}")
                    break # 找到一个就够了

        if not plist:
            # 如果还是找不到， fallback到原始链接
            plist = [f"{vn}${self.e64(f'{1}@@@@{ids[0]}')}"]
            print(f"未找到视频源，使用原始链接: {ids[0]}")

        vod['vod_play_url'] = '#'.join(plist)
        return {'list': [vod]}

    def searchContent(self, key, quick, pg="1"):
        data = self.getpq(f'/视频/search/{quote(key)}/{pg}')
        return {'list': self.getlist(data("main > generic:nth-child(2) > list > listitem")), 'page': pg}

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
        return {'parse': int(ids[0]), 'url': ids[1], 'header': headers}

    def localProxy(self, param):
        pass

    def gethost(self):
        try:
            response = self.fetch('https://stgay.com/', headers=self.headers, allow_redirects=False)
            return response.url
        except Exception as e:
            print(f"获取主页失败: {str(e)}")
            return "https://stgay.com/"

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
            vod_id = i('link').eq(1).attr('href') if i('link').length > 1 else i('link').attr('href')
            vod_name = i('link').eq(1).text() if i('link').length > 1 else i('link').text()
            vod_pic = i('img').attr('src')
            vod_remarks = i('link').eq(0).find('generic:last-child').text() if i('link').length > 0 else '' # 尝试从第一个链接的最后一个generic子元素中获取时长

            vlist.append({
                'vod_id': vod_id,
                'vod_name': vod_name,
                'vod_pic': vod_pic,
                'vod_remarks': vod_remarks
            })
        return vlist

    def getpq(self, path=''):
        h = '' if path.startswith('http') else self.host
        response = self.session.get(f'{h}{path}').text
        try:
            return pq(response)
        except Exception as e:
            print(f"{str(e)}")
            return pq(response.encode('utf-8'))

    def homeVideoContent(self):
        data = self.getpq('/')
        return {'list': self.getlist(data("main > generic:nth-child(2) > list > listitem"))}

    # def getjsdata(self, data):
    #     vhtml = data("script[id='initials-script']").text()
    #     jst = json.loads(vhtml.split('initials=')[-1][:-1])
    #     return jst 
