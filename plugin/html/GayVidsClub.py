# -*- coding: utf-8 -*-
import sys
from pyquery import PyQuery as pq
sys.path.append('..')
from base.spider import Spider


class Spider(Spider):

    def init(self, extend=""):
        pass

    def getName(self):
        return "GayVidsClub"

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    }

    host = "https://gayvidsclub.com"

    def homeContent(self, filter):
        result = {}
        classes = []
        # Main category
        classes.append({
            'type_name': '全部',
            'type_id': '/all-gay-porn/'
        })
        result['class'] = classes
        
        # Get latest videos from homepage
        data = self.getpq('/')
        result['list'] = self.getlist(data('.video-listing.videos-list-with-ads .video-card'))
        return result

    def homeVideoContent(self):
        pass

    def categoryContent(self, tid, pg, filter, extend):
        url = f"{self.host}{tid}"
        if pg > 1:
            url = f"{self.host}/page/{pg}/" if tid == '/' else f"{self.host}{tid}page/{pg}/"
        
        data = self.getpq(url)
        result = {}
        result['list'] = self.getlist(data('.video-listing.videos-list-with-ads .video-card'))
        result['page'] = pg
        result['pagecount'] = 9999 # Placeholder, can be improved later
        result['limit'] = 90
        result['total'] = 999999 # Placeholder, can be improved later
        return result

    def detailContent(self, ids):
        data = self.getpq(ids[0])
        vod = {
            'vod_name': data('h1.page-title').text().strip(),
            'vod_pic': data('.single-video-player img').attr('src') if data('.single-video-player img') else '',
            'vod_remarks': data('.video-info .meta-title span').text().strip() if data('.video-info .meta-title span') else '',
            'vod_content': data('.video-description p').text().strip() if data('.video-description p') else '',
            'vod_play_from': 'GayVidsClub',
            'vod_play_url': ''
        }
        
        # Extracting video URL - this might be tricky and require further inspection
        # For now, let's assume it's in a source tag within the player or a direct link
        video_url = data('video source').attr('src')
        if not video_url:
            # Try to find if it's in an iframe or script
            iframe_src = data('iframe').attr('src')
            if iframe_src and 'youtube.com' not in iframe_src: # Exclude YouTube if it's not the primary player
                video_url = iframe_src
            else:
                # Look for potential direct video links in script tags or a specific player element
                # This will likely require a deeper dive if the above doesn't work
                pass 
        
        vod['vod_play_url'] = f"播放${video_url}" if video_url else f"播放${ids[0]}" # Fallback to original ID if no direct video url found

        return {'list': [vod]}

    def searchContent(self, key, quick, pg="1"):
        search_url = f"{self.host}/page/{pg}/?s={key}"
        data = self.getpq(search_url)
        result = {}
        result['list'] = self.getlist(data('.video-listing.videos-list-with-ads .video-card'))
        return result

    def playerContent(self, flag, id, vipFlags):
        # The 'id' here is expected to be the actual video URL from detailContent
        return {'parse': 0, 'url': id, 'header': self.headers}

    def localProxy(self, param):
        pass

    def liveContent(self, url):
        pass

    def getlist(self, data):
        videos = []
        for i in data.items():
            vod_id = i('a').attr('href')
            vod_name = i('.video-card-title').text().strip()
            vod_pic = i('.video-card-image img').attr('src')
            vod_remarks = i('.video-card-meta-category').text().strip() # Using category as remarks
            
            videos.append({
                'vod_id': vod_id,
                'vod_name': vod_name,
                'vod_pic': vod_pic,
                'vod_remarks': vod_remarks
            })
        return videos

    def getpq(self, path=''):
        url = f"{self.host}{path}" if not path.startswith('http') else path
        rsp = self.fetch(url, headers=self.headers)
        data = rsp.text
        try:
            return pq(data)
        except Exception as e:
            self.log(f"Error parsing HTML with PyQuery: {e}")
            return pq(data.encode('utf-8'))
