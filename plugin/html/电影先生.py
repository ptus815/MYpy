#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 电影先生(dianyingxs)爬虫

import re
import sys
import json
import time
import base64
import requests
from urllib.parse import quote, unquote

sys.path.append('..')
from base.spider import Spider

class DianyingxsSpider(Spider):
    def __init__(self):
        super(DianyingxsSpider, self).__init__()
        self.name = "电影先生"
        self.domain = "https://www.dianyingxs.cc"
        self.header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
            "Referer": self.domain,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2"
        }
        
    def init(self, extend=""):
        print("============{0}============".format(extend))
        pass
    
    def isVideoFormat(self, url):
        """判断是否为视频格式"""
        pass
        
    def manualVideoCheck(self):
        """手动视频检查"""
        pass
    
    def homeContent(self, filter=True):
        """首页内容"""
        result = {}
        try:
            url = self.domain
            response = self.fetch(url, headers=self.header)
            
            # 提取分类
            categories = []
            pattern = r'<li class="nav-menu-item"><a href="(/type/\d+\.html)">([^<]+)</a></li>'
            categories_matches = re.findall(pattern, response.text)
            
            for path, name in categories_matches:
                categories.append({
                    "type_id": path,
                    "type_name": name
                })
            
            result['class'] = categories
            
            # 如果需要筛选
            if filter:
                result['filters'] = self.config['filter']
            
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
            pattern = r'<div class="module-item-pic">\s*<a href="([^"]+)" title="([^"]+)"[^>]*>\s*<img src="([^"]+)"'
            video_matches = re.findall(pattern, response.text)
            
            for idx, (path, name, pic) in enumerate(video_matches[:12]):  # 只取前12个
                videos.append({
                    "vod_id": path,
                    "vod_name": name,
                    "vod_pic": pic if pic.startswith('http') else self.domain + pic,
                    "vod_remarks": ""
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
            if pg <= 0:
                pg = 1
                
            # 构造URL
            if tid.startswith('/type/'):
                url = '{0}{1}'.format(self.domain, tid.replace('.html', '-{0}.html'.format(pg)))
            else:
                url = '{0}/type/{1}-{2}.html'.format(self.domain, tid, pg)
            
            response = self.fetch(url, headers=self.header)
            
            # 提取视频列表
            videos = []
            pattern = r'<div class="module-item-pic">\s*<a href="([^"]+)" title="([^"]+)"[^>]*>\s*<img src="([^"]+)"[^>]*>\s*</a>\s*</div>\s*<div[^>]*>\s*<div[^>]*>\s*<a[^>]*>([^<]*)</a>'
            video_matches = re.findall(pattern, response.text)
            
            for path, name, pic, remark in video_matches:
                videos.append({
                    "vod_id": path,
                    "vod_name": name,
                    "vod_pic": pic if pic.startswith('http') else self.domain + pic,
                    "vod_remarks": remark.strip()
                })
            
            result['list'] = videos
            
            # 获取总页数
            pattern_page = r'<a href="[^"]+">(\d+)</a>\s*<a href="[^"]+">下一页</a>'
            page_match = re.search(pattern_page, response.text)
            total_pg = int(page_match.group(1)) if page_match else pg
            
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
            if ids[0].startswith('/'):
                url = '{0}{1}'.format(self.domain, ids[0])
            else:
                url = '{0}/{1}'.format(self.domain, ids[0])
            
            response = self.fetch(url, headers=self.header)
            
            # 提取详情信息
            vod = {
                "vod_id": ids[0],
                "vod_name": "",
                "vod_pic": "",
                "vod_year": "",
                "vod_area": "",
                "vod_remarks": "",
                "vod_actor": "",
                "vod_director": "",
                "vod_content": "",
                "vod_play_from": "",
                "vod_play_url": ""
            }
            
            # 提取标题
            title_pattern = r'<h1 class="module-title">([^<]+)</h1>'
            title_match = re.search(title_pattern, response.text)
            if title_match:
                vod["vod_name"] = title_match.group(1).strip()
            
            # 提取图片
            pic_pattern = r'<div class="module-item-pic">\s*<img src="([^"]+)"'
            pic_match = re.search(pic_pattern, response.text)
            if pic_match:
                vod["vod_pic"] = pic_match.group(1)
                if not vod["vod_pic"].startswith('http'):
                    vod["vod_pic"] = self.domain + vod["vod_pic"]
            
            # 提取详情信息
            info_pattern = r'<div class="module-info-item">\s*<div[^>]*>([^<]+)</div>\s*<div[^>]*>(.*?)</div>\s*</div>'
            info_matches = re.findall(info_pattern, response.text)
            
            for label, content in info_matches:
                label = label.strip()
                content = re.sub(r'<[^>]+>', '', content).strip()
                
                if '导演' in label:
                    vod["vod_director"] = content
                elif '主演' in label:
                    vod["vod_actor"] = content
                elif '年份' in label:
                    vod["vod_year"] = content
                elif '地区' in label:
                    vod["vod_area"] = content
                elif '更新' in label:
                    vod["vod_remarks"] = content
            
            # 提取简介
            desc_pattern = r'<div class="module-info-introduction-content"[^>]*>(.*?)</div>'
            desc_match = re.search(desc_pattern, response.text, re.DOTALL)
            if desc_match:
                vod["vod_content"] = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip()
            
            # 提取播放列表
            play_from = []
            play_list = []
            
            # 提取播放源
            source_pattern = r'<div class="module-tab-item[^"]*" data-dropdown-value="([^"]+)">\s*<span>([^<]+)</span>'
            source_matches = re.findall(source_pattern, response.text)
            
            for source_id, source_name in source_matches:
                play_from.append(source_name)
                
                # 提取该播放源下的所有剧集
                episode_pattern = r'<div class="module-play-list-content" id="panel-{0}">(.*?)</div>'.format(source_id)
                episode_match = re.search(episode_pattern, response.text, re.DOTALL)
                
                if episode_match:
                    episodes = []
                    link_pattern = r'<a href="([^"]+)"[^>]*>([^<]+)</a>'
                    link_matches = re.findall(link_pattern, episode_match.group(1))
                    
                    for episode_link, episode_name in link_matches:
                        episodes.append('{0}${1}'.format(episode_name.strip(), episode_link))
                    
                    play_list.append('#'.join(episodes))
            
            vod["vod_play_from"] = "$$$".join(play_from)
            vod["vod_play_url"] = "$$$".join(play_list)
            
            result = {
                'list': [vod]
            }
            
        except Exception as e:
            print('DetailContent发生错误: {0}'.format(str(e)))
        
        return result
    
    def searchContent(self, key, quick=False):
        """搜索内容"""
        result = {}
        try:
            url = '{0}/search.html?wd={1}'.format(self.domain, quote(key))
            response = self.fetch(url, headers=self.header)
            
            # 提取搜索结果
            videos = []
            pattern = r'<div class="module-card-item-pic">\s*<a href="([^"]+)" title="([^"]+)"[^>]*>\s*<img src="([^"]+)"[^>]*>\s*</a>\s*</div>\s*<div[^>]*>\s*<div[^>]*>\s*<a[^>]*>([^<]*)</a>'
            video_matches = re.findall(pattern, response.text)
            
            for path, name, pic, remark in video_matches:
                videos.append({
                    "vod_id": path,
                    "vod_name": name,
                    "vod_pic": pic if pic.startswith('http') else self.domain + pic,
                    "vod_remarks": remark.strip()
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
            if id.startswith('/'):
                url = '{0}{1}'.format(self.domain, id)
            else:
                url = '{0}/{1}'.format(self.domain, id)
            
            response = self.fetch(url, headers=self.header)
            
            # 提取播放源
            play_url_pattern = r'var player_aaaa=({.*?})'
            play_url_match = re.search(play_url_pattern, response.text, re.DOTALL)
            
            if play_url_match:
                player_data = json.loads(play_url_match.group(1))
                
                # 提取真实播放地址
                if 'url' in player_data:
                    play_url = player_data['url']
                    
                    # 处理加密或特殊格式的URL
                    if play_url.startswith('http'):
                        real_url = play_url
                    else:
                        # 可能需要解密或其他处理
                        real_url = play_url
                    
                    result = {
                        'parse': 0,  # 0=直接播放，1=需要解析
                        'playUrl': '',
                        'url': real_url,
                        'header': self.header
                    }
            
        except Exception as e:
            print('PlayerContent发生错误: {0}'.format(str(e)))
        
        return result
    
    def fetch(self, url, headers=None):
        """统一请求方法，带重试和异常处理"""
        retry = 3
        while retry > 0:
            try:
                if headers is None:
                    headers = self.header
                response = requests.get(url, headers=headers, timeout=10)
                response.encoding = 'utf-8'
                return response
            except Exception as e:
                retry -= 1
                if retry == 0:
                    raise e
                time.sleep(1)
        return None

    def localProxy(self, param):
        """本地代理"""
        return [200, "video/MP2T", {}, ""]
