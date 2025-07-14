#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 91nt.com爬虫 for OK影视

import re
import sys
import json
import time
import requests
import urllib.parse
from bs4 import BeautifulSoup

sys.path.append('..')
from base.spider import Spider


class Spider(Spider):
    def __init__(self):
        super(Spider, self).__init__()
        self.domain = 'https://91nt.com'
        self.header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
            "Referer": self.domain,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2"
        }
        self.config = {
            "player": {},
            "filter": {
                "xrbj": [
                    {
                        "key": "order",
                        "name": "排序",
                        "value": [
                            {"n": "最新", "v": "new"},
                            {"n": "最热", "v": "popular"}
                        ]
                    }
                ],
                "wtns": [
                    {
                        "key": "order",
                        "name": "排序",
                        "value": [
                            {"n": "最新", "v": "new"},
                            {"n": "最热", "v": "popular"}
                        ]
                    }
                ],
                "zfyh": [
                    {
                        "key": "order",
                        "name": "排序",
                        "value": [
                            {"n": "最新", "v": "new"},
                            {"n": "最热", "v": "popular"}
                        ]
                    }
                ],
                "dmfj": [
                    {
                        "key": "order",
                        "name": "排序",
                        "value": [
                            {"n": "最新", "v": "new"},
                            {"n": "最热", "v": "popular"}
                        ]
                    }
                ],
                "jrmn": [
                    {
                        "key": "order",
                        "name": "排序",
                        "value": [
                            {"n": "最新", "v": "new"},
                            {"n": "最热", "v": "popular"}
                        ]
                    }
                ],
                "rhgv": [
                    {
                        "key": "order",
                        "name": "排序",
                        "value": [
                            {"n": "最新", "v": "new"},
                            {"n": "最热", "v": "popular"}
                        ]
                    }
                ],
                "omjd": [
                    {
                        "key": "order",
                        "name": "排序",
                        "value": [
                            {"n": "最新", "v": "new"},
                            {"n": "最热", "v": "popular"}
                        ]
                    }
                ],
                "drqp": [
                    {
                        "key": "order",
                        "name": "排序",
                        "value": [
                            {"n": "最新", "v": "new"},
                            {"n": "最热", "v": "popular"}
                        ]
                    }
                ],
                "kjys": [
                    {
                        "key": "order",
                        "name": "排序",
                        "value": [
                            {"n": "最新", "v": "new"},
                            {"n": "最热", "v": "popular"}
                        ]
                    }
                ],
                "tjsm": [
                    {
                        "key": "order",
                        "name": "排序",
                        "value": [
                            {"n": "最新", "v": "new"},
                            {"n": "最热", "v": "popular"}
                        ]
                    }
                ]
            }
        }

    def init(self, extend=""):
        print("============{0}============".format(extend))
        return {}
        
    def isVideoFormat(self, url):
        pass
        
    def manualVideoCheck(self):
        pass
    
    def homeContent(self, filter):
        """首页内容"""
        result = {}
        try:
            url = self.domain
            response = self.fetch(url, headers=self.header)
            
            # 提取分类
            categories = []
            soup = BeautifulSoup(response.text, 'html.parser')
            nav_items = soup.select('.banner nav ul li')
            
            for item in nav_items:
                link = item.find('a')
                if link and 'category' in link.get('href', ''):
                    category_id = link.get('href').split('/')[-1]
                    category_name = link.text.strip()
                    categories.append({
                        "type_id": category_id,
                        "type_name": category_name
                    })
            
            result['class'] = categories
            
            # 如果需要筛选
            if filter:
                result['filters'] = self.config['filter']
            
            # 获取首页推荐视频
            videos = self.homeVideoContent()['list']
            result['list'] = videos
            
        except Exception as e:
            print('HomeContent发生错误: {0}'.format(str(e)))
        
        return result
    
    def homeVideoContent(self):
        """首页视频内容"""
        result = {}
        try:
            url = self.domain
            response = self.fetch(url, headers=self.header)
            
            # 提取首页推荐视频
            videos = []
            soup = BeautifulSoup(response.text, 'html.parser')
            video_items = soup.select('main .list-item')
            
            for item in video_items[:12]:  # 只取前12个
                link = item.select_one('a')
                if link:
                    vod_id = link.get('href')
                    vod_name = link.get('title') or item.select_one('a img').get('alt', '')
                    vod_pic = item.select_one('a img').get('src', '')
                    vod_remarks = item.select_one('a .duration').text.strip() if item.select_one('a .duration') else ""
                    
                    videos.append({
                        "vod_id": vod_id,
                        "vod_name": vod_name,
                        "vod_pic": vod_pic if vod_pic.startswith('http') else self.domain + vod_pic,
                        "vod_remarks": vod_remarks
                    })
            
            result['list'] = videos
            
        except Exception as e:
            print('HomeVideoContent发生错误: {0}'.format(str(e)))
        
        return result
    
    def categoryContent(self, tid, pg, filter, extend):
        """分类内容"""
        result = {}
        try:
            # 处理页码
            pg = int(pg)
            if pg <= 0:
                pg = 1
            
            # 构造URL
            order = "new"  # 默认排序
            if extend and 'order' in extend:
                order = extend['order']
            
            url = '{0}/videos/category/{1}/{2}'.format(self.domain, tid, pg)
            if order == "popular":
                url = '{0}/videos/category/{1}/popular/{2}'.format(self.domain, tid, pg)
            
            response = self.fetch(url, headers=self.header)
            
            # 提取视频列表
            videos = []
            soup = BeautifulSoup(response.text, 'html.parser')
            video_items = soup.select('main .list-item')
            
            for item in video_items:
                link = item.select_one('a')
                if link:
                    vod_id = link.get('href')
                    vod_name = link.get('title') or item.select_one('a img').get('alt', '')
                    vod_pic = item.select_one('a img').get('src', '')
                    vod_remarks = item.select_one('a .duration').text.strip() if item.select_one('a .duration') else ""
                    
                    videos.append({
                        "vod_id": vod_id,
                        "vod_name": vod_name,
                        "vod_pic": vod_pic if vod_pic.startswith('http') else self.domain + vod_pic,
                        "vod_remarks": vod_remarks
                    })
            
            result['list'] = videos
            
            # 获取总页数
            pagination = soup.select('main .pagination li')
            total_pg = pg
            if pagination:
                for page in pagination:
                    if page.text.strip().isdigit():
                        page_num = int(page.text.strip())
                        if page_num > total_pg:
                            total_pg = page_num
            
            result['page'] = pg
            result['pagecount'] = total_pg
            result['limit'] = 24
            result['total'] = total_pg * 24
            
        except Exception as e:
            print('CategoryContent发生错误: {0}'.format(str(e)))
        
        return result
    
    def detailContent(self, ids):
        """详情内容"""
        result = {}
        try:
            # 获取详情页
            url = ids[0] if ids[0].startswith('http') else '{0}{1}'.format(self.domain, ids[0])
            response = self.fetch(url, headers=self.header)
            
            # 提取详情信息
            soup = BeautifulSoup(response.text, 'html.parser')
            
            vod = {
                "vod_id": ids[0],
                "vod_name": soup.select_one('h1').text.strip() if soup.select_one('h1') else "",
                "vod_pic": "",
                "vod_year": "",
                "vod_area": "",
                "vod_remarks": "",
                "vod_actor": "",
                "vod_director": "",
                "vod_content": "",
                "vod_play_from": "91nt",
                "vod_play_url": ""
            }
            
            # 提取图片
            img = soup.select_one('main img')
            if img:
                vod["vod_pic"] = img.get('src', '')
                if not vod["vod_pic"].startswith('http'):
                    vod["vod_pic"] = self.domain + vod["vod_pic"]
            
            # 提取标签
            tags = soup.select('.tags a')
            tag_list = [tag.text.strip() for tag in tags if tag]
            vod["vod_content"] = "标签: " + ", ".join(tag_list) if tag_list else ""
            
            # 提取播放地址
            play_url = url
            vod["vod_play_url"] = "播放#" + play_url
            
            result = {
                'list': [vod]
            }
            
        except Exception as e:
            print('DetailContent发生错误: {0}'.format(str(e)))
        
        return result
    
    def searchContent(self, key, quick):
        """搜索内容"""
        result = {}
        try:
            url = '{0}/search?q={1}'.format(self.domain, urllib.parse.quote(key))
            response = self.fetch(url, headers=self.header)
            
            # 提取搜索结果
            videos = []
            soup = BeautifulSoup(response.text, 'html.parser')
            video_items = soup.select('main .list-item')
            
            for item in video_items:
                link = item.select_one('a')
                if link:
                    vod_id = link.get('href')
                    vod_name = link.get('title') or item.select_one('a img').get('alt', '')
                    vod_pic = item.select_one('a img').get('src', '')
                    vod_remarks = item.select_one('a .duration').text.strip() if item.select_one('a .duration') else ""
                    
                    videos.append({
                        "vod_id": vod_id,
                        "vod_name": vod_name,
                        "vod_pic": vod_pic if vod_pic.startswith('http') else self.domain + vod_pic,
                        "vod_remarks": vod_remarks
                    })
            
            result = {
                'list': videos
            }
            
        except Exception as e:
            print('SearchContent发生错误: {0}'.format(str(e)))
        
        return result
    
    def playerContent(self, flag, id, vipFlags):
        """播放内容"""
        result = {}
        try:
            # 获取播放页
            
            url = id if id.startswith('http') else '{0}{1}'.format(self.domain, id)
            
            # 直接返回播放页URL，依赖OK影视内置播放器处理
            result = {
                'parse': 1,  # 需要嗅探
                'playUrl': '',
                'url': url,
                'header': self.header
            }
            
        except Exception as e:
            print('PlayerContent发生错误: {0}'.format(str(e)))
        
        return result
    
    def localProxy(self, param):
        """本地代理"""
        return [200, "video/MP2T", {}, ""]


# 测试代码
if __name__ == "__main__":
    spider = Spider()
    # 测试首页内容
    home_content = spider.homeContent(True)
    print(json.dumps(home_content, ensure_ascii=False))
    
    # 测试分类内容
    # category_content = spider.categoryContent('xrbj', 1, True, {})
    # print(json.dumps(category_content, ensure_ascii=False))
    
    # 测试详情内容
    # detail_content = spider.detailContent(['/videos/vd-a43-d81a'])
    # print(json.dumps(detail_content, ensure_ascii=False))
    
    # 测试搜索
    # search_content = spider.searchContent('动漫', False)
    # print(json.dumps(search_content, ensure_ascii=False)) 
