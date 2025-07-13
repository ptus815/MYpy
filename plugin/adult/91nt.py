# -*- coding: utf-8 -*-
# 91nt.com 网站爬虫
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
        self.site = extend.get('site', 'https://91nt.com')
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
            'Referer': self.site,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }

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
            "调教SM": "/videos/category/tjsm",
        }
        classes = []
        for k in cateManual:
            classes.append({
                'type_name': k,
                'type_id': cateManual[k]
            })
        result['class'] = classes
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
        
        # 获取视频列表
        items = root.xpath('//div[contains(@class, "list")]/div[contains(@class, "listitem")]')
        
        for item in items:
            try:
                # 视频链接和ID
                href = item.xpath('.//a[contains(@href, "/videos/vd-")]/@href')[0]
                vid = href.split('/')[-1]
                
                # 视频标题
                title = item.xpath('.//a[contains(@href, "/videos/vd-")]/@title')[0] if item.xpath('.//a[contains(@href, "/videos/vd-")]/@title') else item.xpath('.//a[contains(@href, "/videos/vd-")]//text()')[0]
                
                # 视频封面
                img = item.xpath('.//img/@src')[0]
                if img.startswith('//'):
                    img = 'https:' + img
                
                # 视频时长
                duration = item.xpath('.//div[contains(@class, "generic")]/text()')[0].strip() if item.xpath('.//div[contains(@class, "generic")]/text()') else ""
                
                # 标签
                tags = item.xpath('.//strong/text()')
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
        
        # 获取视频标题
        title = root.xpath('//h1/text()')[0] if root.xpath('//h1/text()') else vid
        
        # 获取视频封面
        pic = root.xpath('//meta[@property="og:image"]/@content')[0] if root.xpath('//meta[@property="og:image"]/@content') else ""
        
        # 获取视频描述
        desc = root.xpath('//meta[@property="og:description"]/@content')[0] if root.xpath('//meta[@property="og:description"]/@content') else ""
        
        # 获取视频标签
        tags = root.xpath('//a[contains(@href, "/videos/tag/")]/strong/text()')
        tag = '、'.join(tags) if tags else ""
        
        # 视频播放源和播放地址
        # 注意：此处需要分析网页源码找到真实的视频地址
        # 这里使用一个通用的方法尝试提取视频地址
        play_url = self.extractVideoUrl(rsp.text)
        
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
        # 尝试从HTML中提取视频地址
        # 方法1：查找video标签
        video_url = re.search(r'<video[^>]*src=[\'"]([^\'"]+)[\'"]', html_content)
        if video_url:
            return video_url.group(1)
        
        # 方法2：查找常见的视频参数
        video_url = re.search(r'source\s*src=[\'"]([^\'"]+)[\'"]', html_content)
        if video_url:
            return video_url.group(1)
        
        # 方法3：查找可能包含视频URL的JavaScript变量
        video_url = re.search(r'videoUrl\s*=\s*[\'"]([^\'"]+)[\'"]', html_content)
        if video_url:
            return video_url.group(1)
        
        # 方法4：查找m3u8地址
        video_url = re.search(r'[\'"]([^\'"]*.m3u8[^\'"]*)[\'"]', html_content)
        if video_url:
            return video_url.group(1)
        
        # 如果无法找到视频地址，返回空字符串
        return ""

    def searchContent(self, key, quick, pg="1"):
        url = f"{self.site}/search?page={pg}&wd={urllib.parse.quote(key)}"
        return self.fetchVideoContent(url)

    def playerContent(self, flag, id, vipFlags):
        # 如果在detailContent中已经提取了真实播放地址，这里直接返回
        if id.startswith('http'):
            return {
                'parse': 0,
                'url': id,
                'header': self.headers
            }
        
        # 否则，需要进一步处理获取真实播放地址
        # 这里可能需要使用playwright或其他方法来获取实际的视频URL
        return {
            'parse': 1,  # 使用系统解析
            'url': id,
            'header': self.headers
        }

    def localProxy(self, param):
        # 本地代理，用于处理一些特殊的视频格式
        return None