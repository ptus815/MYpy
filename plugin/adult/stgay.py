# coding: utf-8
# !/usr/bin/env python
import re
from base.spider import Spider

class Spider(Spider):
    def get_name(self):
        return "STGay"

    def init(self, extend=""):
        super().init(extend)
        self.site_url = "https://stgay.com"
        # 使用stgay.com的logo作为图标
        self.ico = "https://stgay.com/wp-content/uploads/2023/12/cropped-1-1-192x192.png"

    def home_content(self, filter):
        """
        获取首页内容，主要是分类列表。
        """
        result = {}
        classes = []
        try:
            html = self.fetch(self.site_url)
            # 使用PyQuery解析HTML
            doc = self.pq(html)
            # 定位到导航菜单
            menu_items = doc('ul.nav-menu > li.menu-item-has-children')
            
            for item in menu_items.items():
                # 寻找子菜单的分类
                sub_items = item('ul.sub-menu > li > a')
                for sub_item in sub_items.items():
                    type_name = sub_item.text()
                    # 过滤掉不需要的分类
                    if type_name and type_name not in ["SUBBED", "TRENDING", "HOME"]:
                        # 从链接中提取分类ID
                        type_id = sub_item.attr('href').replace(self.site_url, '')
                        classes.append({'type_name': type_name, 'type_id': type_id})

            result['class'] = classes
            if filter:
                result['filters'] = self.config['filter']

        except Exception as e:
            self.log(f"获取首页分类失败: {e}")
        return result

    def category_content(self, tid, pg, filter, extend):
        """
        获取分类页面的视频列表。
        tid: 分类ID (e.g., /category/uncensored/)
        pg: 页码
        """
        result = {}
        videos = []
        # 构造分类页面URL，支持翻页
        url = self.site_url + tid + f'page/{pg}/'
        
        try:
            html = self.fetch(url)
            doc = self.pq(html)
            # 定位到视频列表项
            video_items = doc('div.videos-list > article.video-item').items()
            
            for item in video_items:
                video_box = item('a.video-box')
                # 视频ID就是其详情页的相对路径
                vod_id = video_box.attr('href').replace(self.site_url, '')
                # 视频标题
                vod_name = video_box.attr('title')
                # 视频封面图片，使用data-src属性以支持懒加载
                vod_pic = item('img').attr('data-src')
                # 视频备注，如时长
                vod_remarks = item('span.duration').text()
                videos.append({
                    "vod_id": vod_id,
                    "vod_name": vod_name,
                    "vod_pic": vod_pic,
                    "vod_remarks": vod_remarks
                })

            result['list'] = videos
            result['page'] = pg
            result['pagecount'] = 999  # 网站没有明确的总页数，设置为一个较大的值
            result['limit'] = len(videos)
            result['total'] = float('inf')

        except Exception as e:
            self.log(f"获取分类内容失败: {e}")
            
        return result

    def detail_content(self, array):
        """
        获取视频详情。
        array: 包含视频ID的列表 (e.g., ['/view/xxxx/'])
        """
        try:
            tid = array[0]
            url = self.site_url + tid
            html = self.fetch(url)
            doc = self.pq(html)

            # 视频标题
            title = doc('h1.video-title').text()
            # 视频封面，从播放器脚本中提取
            pic_match = re.search(r"poster:\s*'([^']+)'", html)
            pic = pic_match.group(1) if pic_match else ''
            
            # 演员信息
            actors = [a.text() for a in doc('div.video-meta-details a[rel="tag"]').items()]
            actor = ','.join(actors)
            
            # 分类信息
            category = doc('div.video-meta-details a[rel="category tag"]').text()
            
            # 视频简介
            description = doc('div.video-description p').text()

            vod = {
                "vod_id": tid,
                "vod_name": title,
                "vod_pic": pic,
                "type_name": category,
                "vod_actor": actor,
                "vod_content": description
            }
            
            # 关键：从页面脚本中提取m3u8播放链接
            m3u8_match = re.search(r"url:\s*'([^']+\.m3u8)'", html)
            if m3u8_match:
                play_url = m3u8_match.group(1)
                # 格式化播放列表
                vod['vod_play_from'] = 'STGay'
                vod['vod_play_url'] = f'播放${play_url}'
            else:
                 vod['vod_play_from'] = 'STGay'
                 vod['vod_play_url'] = '播放$error' #如果未找到m3u8

            result = {'list': [vod]}
            return result

        except Exception as e:
            self.log(f"获取详情内容失败: {e}")
        
        return {'list': []}

    def search_content(self, key, quick):
        """
        处理搜索请求。
        key: 搜索关键词
        """
        # 搜索页的URL结构与分类页类似，只是页码处理稍有不同
        return self.category_content(f'/?s={key}', '1', {}, {})

    def player_content(self, flag, id, vip_flags):
        """
        解析并返回最终的播放地址。
        flag: 播放源标识 (e.g., 'STGay')
        id: 视频播放URL (即m3u8链接)
        """
        result = {}
        try:
            result = {
                'parse': 0,        # 0表示不使用webview解析，直接播放
                'playUrl': '',     # 如果需要，可以在这里指定备用播放器
                'url': id,         # 直接返回m3u8链接进行播放
                'header': {        # 添加Referer头，模拟浏览器访问，提高成功率
                    "Referer": self.site_url
                }
            }
        except Exception as e:
            self.log(f"解析播放地址失败: {e}")
            
        return result

    def local_proxy(self, params):
        """
        如果需要本地代理，可以在此实现。
        """
        return super().local_proxy(params)
