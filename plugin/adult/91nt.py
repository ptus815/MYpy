
import sys
import re
import json
import time
import urllib.parse
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from base.spider import Spider


class Spider(Spider):
    def init(self, extend=""):
        # 兼容盒子传入 list 的情况
        if not isinstance(extend, dict):
            extend = {}
        self.site = extend.get('site', 'https://91nt.com')
        # --- MODIFICATION START ---
        # 根据您提供的最新截图更新请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0', #
            'Accept': '*/*', #
            'Accept-Encoding': 'gzip, deflate, br', #
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Origin': self.site,
            'Referer': self.site,
        }
        # --- MODIFICATION END ---

    def getName(self):
        return "91nt"

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    def homeContent(self, filter):
        result = {}
        cateManual = {
            "精选G片": "/videos/all/watchings",
            "男同黑料": "/posts/category/all",
            "鲜肉薄肌": "/videos/category/xrbj",
            "无套内射": "/videos/category/wtns",
            "制服诱惑": "/videos/category/zfyh",
            "耽美天菜": "/videos/category/dmfj",
            "肌肉猛男": "/videos/category/jrmn",
            "日韩GV": "/videos/category/rhgv",
            "欧美巨屌": "/videos/category/omjd",
            "多人群交": "/videos/category/drqp",
            "口交颜射": "/videos/category/kjys",
            "调教SM": "/videos/category/tjsm"
        }
        classes = []
        for k in cateManual:
            classes.append({
                'type_name': k,
                'type_id': cateManual[k]
            })
        result['class'] = classes
        # 一些盒子首页需要同时返回推荐视频列表
        try:
            hv = self.fetchVideoContent(f"{self.site}/videos/all/popular")
            result['list'] = hv.get('list', [])
        except Exception:
            result['list'] = []
        return result

    def homeVideoContent(self):
        url = f"{self.site}/videos/all/popular"
        return self.fetchVideoContent(url)

    def categoryContent(self, tid, pg, filter, extend):
        if pg == '':
            pg = '1'
        url = f"{self.site}{tid}?page={pg}"
        return self.fetchVideoContent(url)

    def fetchVideoContent(self, url):
        rsp = self.fetch(url, headers=self.headers)
        root = self.html(rsp.text)
        videos = []
        
        # 获取视频列表（统一使用首页/分类/搜索的结构）
        items = root.xpath('//ul[contains(@class, "video-items")]//div[contains(@class, "video-item")]')
        
        for item in items:
            try:
                # 视频链接和ID
                href_nodes = item.xpath('.//a[contains(@href, "/videos/vd-")]/@href')
                if not href_nodes:
                    continue
                href = href_nodes[0]
                vid = href.rstrip('/').split('/')[-1]
                
                # 视频标题
                title = item.xpath('.//a[contains(@href, "/videos/vd-")]/@title')[0] if item.xpath('.//a[contains(@href, "/videos/vd-")]/@title') else ''.join(item.xpath('.//a[contains(@href, "/videos/vd-")]//text()')).strip()
                
                # 视频封面
                img = ''
                poster_div = item.xpath('.//div[contains(@class, "poster")]')
                if poster_div:
                    ds = poster_div[0].xpath('.//img/@data-src')
                    if ds:
                        img = ds[0]
                    else:
                        ss = poster_div[0].xpath('.//img/@src')
                        img = ss[0] if ss else ''
                if img.startswith('//'):
                    img = 'https:' + img
                
                # 视频时长
                duration = ''
                duration_nodes = item.xpath('.//div[contains(@class, "poster")]//div[contains(@class, "text-white") or contains(@class, "text-sm")]/text()')
                if duration_nodes:
                    duration = duration_nodes[0].strip()
                
                # 标签
                tags = item.xpath('.//div[contains(@class, "dx-subtitle")]//strong/text()')
                tag = '、'.join(tags) if tags else ""
                
                videos.append({
                    "vod_id": vid,
                    "vod_name": title,
                    "vod_pic": img,
                    "vod_remarks": duration,
                    "vod_tag": tag,
                    "style": {"type": "rect", "ratio": 1.33}
                })
            except Exception as e:
                print(f"解析视频项时出错: {e}")
                continue
        
        result = {
            'list': videos,
            'page': 1,
            'pagecount': 9999,
            'limit': 90,
            'total': 999999
        }
        return result

    def detailContent(self, ids):
        vid = ids[0]
        url = f"{self.site}/videos/{vid}"
        
        rsp = self.fetch(url, headers=self.headers)
        root = self.html(rsp.text)
        
        # 根据您的需求，我们优先从 <div id="mse"> 中提取封面和播放地址
        play_info_element = root.xpath('//div[@id="mse"]')
        
        if play_info_element:
            # 成功找到关键信息元素
            play_url = play_info_element[0].xpath('./@data-url')[0]
            pic = play_info_element[0].xpath('./@data-poster')[0]
        else:
            # 如果没有找到，使用备用方案
            play_url = self.extractVideoUrl(rsp.text)
            pic = root.xpath('//meta[@property="og:image"]/@content')[0] if root.xpath('//meta[@property="og:image"]/@content') else ""

        # 获取视频标题
        title = root.xpath('//h1/text()')[0] if root.xpath('//h1/text()') else vid
        
        # 获取视频描述
        desc = root.xpath('//meta[@property="og:description"]/@content')[0] if root.xpath('//meta[@property="og:description"]/@content') else ""
        # 获取视频标签
        tags = root.xpath('//a[contains(@href, "/videos/tag/")]/strong/text()')
        tag = '、'.join(tags) if tags else ""
        
        vod = {
            "vod_id": vid,
            "vod_name": title,
            "vod_pic": pic,
            "type_name": tag,
            "vod_year": "",
            "vod_area": "",
            "vod_remarks": "",
            "vod_actor": "",
            "vod_director": "",
            "vod_content": desc,
            "vod_play_from": "91nt",
            "vod_play_url": "播放$" + play_url
        }
        
        result = {
            'list': [vod]
        }
        return result

    def extractVideoUrl(self, html_content):
        # 这是一个备用方法，当新的提取逻辑失败时可能会被调用
        video_url = re.search(r'<video[^>]*src=[\'"]([^\'"]+)[\'"]', html_content)
        if video_url:
            return video_url.group(1)
        
        video_url = re.search(r'source\s*src=[\'"]([^\'"]+)[\'"]', html_content)
        if video_url:
            return video_url.group(1)
        
        video_url = re.search(r'videoUrl\s*=\s*[\'"]([^\'"]+)[\'"]', html_content)
        if video_url:
            return video_url.group(1)
        
        video_url = re.search(r'[\'"]([^\'"]*.m3u8[^\'"]*)[\'"]', html_content)
        if video_url:
            return video_url.group(1)
        
        return ""

    def searchContent(self, key, quick, pg="1"):
        url = f"{self.site}/videos/search/{urllib.parse.quote(key)}?page={pg}"
        return self.fetchVideoContent(url)

    def playerContent(self, flag, id, vipFlags):
        if id.startswith('http'):
            return {
                'parse': 0,
                'url': id,
                'header': self.headers
            }
        
        return {
            'parse': 1,
            'url': id,
            'header': self.headers
        }

    def localProxy(self, param):
        return None
