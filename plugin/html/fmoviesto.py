# -*- coding: utf-8 -*-
# FMovies crawler for fmoviesto.cc
import re
import sys
import json
from urllib.parse import quote_plus, urlparse, parse_qs
from pyquery import PyQuery as pq
sys.path.append('..')
from base.spider import Spider
import requests

class Spider(Spider):

    def init(self, extend=""):
        self.site_url = 'https://fmoviesto.cc'
        self.site_name = 'FMovies'
        self.img_prefix = 'https://wsrv.nl?url='  # Use wsrv.nl to proxy images for faster loading
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            'origin': self.site_url,
            'referer': self.site_url,
        }

    def getName(self):
        return self.site_name

    def homeContent(self, filter):
        result = {}
        cate = {
            "电影": "movie",
            "剧集": "tv-show",
            "动漫": "anime",
            "热门": "trending",
        }
        classes = [{'type_name': k, 'type_id': v} for k, v in cate.items()]
        
        genre_list = ['action', 'adventure', 'animation', 'comedy', 'crime',
                      'documentary', 'drama', 'family', 'fantasy', 'history',
                      'horror', 'music', 'mystery', 'romance', 'sci-fi',
                      'thriller', 'war', 'western']
        genre_options = [{"n": genre.capitalize(), "v": genre} for genre in genre_list]

        filters = {
            "movie": [{"key": "genre", "name": "类型", "value": genre_options}],
            "tv-show": [{"key": "genre", "name": "类型", "value": genre_options}],
            "anime": [{"key": "genre", "name": "类型", "value": genre_options}],
        }
        
        result['class'] = classes
        result['filters'] = filters
        return result

    def homeVideoContent(self):
        # The /trending page has a different layout, use /movie for more consistent results
        return self.getMovieList(f"{self.site_url}/movie")

    def categoryContent(self, tid, pg, filter, extend):
        if extend.get('genre'):
            url = f"{self.site_url}/genre/{extend['genre']}"
        else:
            url = f"{self.site_url}/{tid}"

        if int(pg) > 1:
            url = f"{url}?page={pg}"
        
        return self.getMovieList(url, pg)

    def detailContent(self, ids):
        url = self.site_url + ids[0]
        try:
            html = self.fetch(url, headers=self.headers).text
            doc = pq(html)

            # A more precise selector for the title, based on its proximity to the poster
            title = doc('.film-poster').nextAll('h2.film-name').text().strip()
            if not title:
                # Fallback to previous selectors if the new one fails
                title = doc('.film-detail .film-name').text().strip()
            if not title:
                title = doc('h2.film-name').eq(0).text().strip()


            cover = doc('.film-poster-img').attr('data-src') or doc('.film-poster-img').attr('src')
            if cover and not cover.startswith('http'):
                cover = f"https:{cover}" if cover.startswith('//') else f"{self.site_url}{cover}"
            if cover:
                cover = f"{self.img_prefix}{cover}"

            description = doc('.film-detail .description').text().strip()
            if not description:
                # Fallback selector for description
                description = doc('.description').text().strip()

            info_items = doc('.film-detail .fd-infor .fdi-item')
            year = info_items.eq(0).text().strip() if info_items.length > 0 else ""
            duration = info_items.eq(1).text().strip() if info_items.length > 1 else ""
            
            genres = [a.text() for a in doc('.film-detail .fd-infor a[href*="genre"]').items()]
            category = ", ".join(genres)
            
            vod = {
                "vod_id": ids[0],
                "vod_name": title,
                "vod_pic": cover,
                "type_name": category,
                "vod_year": year,
                "vod_area": "", 
                "vod_remarks": duration,
                "vod_actor": self.get_detail_item(doc, 'Casts'),
                "vod_director": self.get_detail_item(doc, 'Director'),
                "vod_content": description,
            }

            play_from = []
            play_url = []

            if 'movie' in ids[0]:
                server_links = doc('.film-detail .server-select-switch a')
                for link in server_links.items():
                    server_name = link.text().strip()
                    if not server_name:
                        server_name = f"线路 {len(play_from) + 1}"
                    watch_url = link.attr('href')
                    if watch_url:
                        play_from.append(server_name)
                        play_url.append(f"播放${watch_url}")
            elif 'tv' in ids[0]:
                seasons = doc('.season-select .ss-item')
                all_server_episodes = {}

                for season in seasons.items():
                    s_id = season.attr('data-id')
                    s_name = season.text().strip()
                    
                    eps_url = f"{self.site_url}/ajax/v2/tv/episodes/{s_id}"
                    eps_html = self.fetch(eps_url, headers=self.headers).text
                    eps_doc = pq(eps_html)

                    for ep in eps_doc('.eps-item').items():
                        ep_id = ep.attr('data-id')
                        ep_name = ep.find('.episode-name').text().strip()
                        
                        servers_url = f"{self.site_url}/ajax/v2/episode/servers/{ep_id}"
                        
                        ajax_headers = self.headers.copy()
                        ajax_headers['referer'] = url
                        ajax_headers['x-requested-with'] = 'XMLHttpRequest'

                        servers_resp = self.post(servers_url, headers=ajax_headers)
                        
                        if servers_resp.status_code == 200:
                            servers_html = servers_resp.json().get('html', '')
                            servers_doc = pq(servers_html)
                            for server_link in servers_doc('a').items():
                                server_name = server_link.text().strip()
                                watch_url = server_link.attr('href')
                                if server_name and watch_url:
                                    if server_name not in all_server_episodes:
                                        all_server_episodes[server_name] = []
                                    all_server_episodes[server_name].append(f"{s_name} {ep_name}${watch_url}")

                for server_name, episodes in all_server_episodes.items():
                    play_from.append(server_name)
                    play_url.append("#".join(episodes))
            
            if play_from and play_url:
                vod['vod_play_from'] = "$$$".join(play_from)
                vod['vod_play_url'] = "$$$".join(play_url)

            return {'list': [vod]}
        except Exception as e:
            print(f"Error fetching detail content: {e}")
            return {'list': []}

    def get_detail_item(self, doc, label):
        row = doc(f'.elements .row:contains("{label}")')
        if row:
            return row.find('.col-md-10').text().strip()
        return ""

    def searchContent(self, key, quick):
        return self.searchContentPage(key, quick, 1)

    def searchContentPage(self, key, quick, pg=1):
        search_url = f"{self.site_url}/search/{quote_plus(key)}"
        if int(pg) > 1:
            search_url += f"?page={pg}"
        return self.getMovieList(search_url, pg)

    def playerContent(self, flag, id, vipFlags):
        url = self.site_url + id
        try:
            html = self.fetch(url, headers=self.headers).text
            doc = pq(html)
            
            iframe_src = doc('iframe#iframe-embed').attr('src')
            if iframe_src and not iframe_src.startswith('http'):
                iframe_src = f"https:{iframe_src}"

            iframe_html = self.fetch(iframe_src, headers={'Referer': url}).text
            
            sources_match = re.search(r'sources:\s*(\[.*?\])', iframe_html, re.DOTALL)
            if sources_match:
                sources_str = sources_match.group(1)
                sources = json.loads(sources_str)
                if sources:
                    # Find highest quality, assuming it's the first one or contains '1080'
                    video_url = sources[0].get('file')
                    for source in sources:
                        if '1080' in source.get('label', ''):
                            video_url = source.get('file')
                            break
                    
                    return {
                        'parse': 0,
                        'url': video_url,
                        'header': {'Referer': iframe_src}
                    }
            
            return {'parse': 1, 'url': url} # Fallback
        except Exception as e:
            print(f"Error fetching player content: {e}")
            return {'parse': 1, 'url': url}

    def getMovieList(self, url, pg='1'):
        print(f"Fetching list: {url}")
        html = self.fetch(url, headers=self.headers).text
        doc = pq(html)
        
        videos = []
        # Update selector based on current site structure
        for item in doc('div.flw-item').items():
            link = item.find('a.film-poster-ahref')
            vod_id = link.attr('href')
            if not vod_id:
                continue

            vod_name = item.find('.film-name a').attr('title')
            vod_pic = item.find('.film-poster-img').attr('data-src')
            if vod_pic and not vod_pic.startswith('http'):
                vod_pic = f"https:{vod_pic}"
            if vod_pic:
                vod_pic = f"{self.img_prefix}{vod_pic}"
            
            vod_remarks = item.find('.film-poster .quality').text().strip()

            if vod_id not in [v['vod_id'] for v in videos]:
                videos.append({
                    "vod_id": vod_id,
                    "vod_name": vod_name,
                    "vod_pic": vod_pic,
                    "vod_remarks": vod_remarks
                })
        
        pagecount = 0
        pagination_links = doc('.pagination a[href*="?page="]')
        if pagination_links:
            # Use .eq(-1) to get the last element instead of .last()
            last_page_href = pagination_links.eq(-1).attr('href')
            if last_page_href:
                qs = parse_qs(urlparse(last_page_href).query)
                pagecount = int(qs.get('page', [1])[0])
        
        return {
            'list': videos,
            'page': int(pg),
            'pagecount': pagecount or int(pg),
            'limit': len(videos),
            'total': pagecount * len(videos) if pagecount else len(videos)
        }
    
    def localProxy(self, params):
        return [200, "text/plain", "Not implemented", {}]


if __name__ == "__main__":
    spider = Spider()
    spider.init()
    
    # Test various functionality
    import traceback
    try:
        print("====== Testing Home Content ======")
        home_content = spider.homeContent(True)
        print(json.dumps(home_content, indent=2))
        
        print("\n====== Testing Home Video Content ======")
        home_videos = spider.homeVideoContent()
        print(f"Found {len(home_videos['list'])} videos")
        # Print first 3 items only for brevity
        for i, video in enumerate(home_videos['list'][:3]):
            print(f"Video {i+1}: {video['vod_name']} - {video['vod_id']}")
        
        if home_videos['list']:
            print("\n====== Testing Detail Content ======")
            detail = spider.detailContent([home_videos['list'][0]['vod_id']])
            print(json.dumps(detail, indent=2))
            
            if 'list' in detail and detail['list']:
                play_url = detail['list'][0]['vod_play_url']
                if '$' in play_url:
                    vid_url = play_url.split('$')[1]
                    
                    print("\n====== Testing Player Content ======")
                    player = spider.playerContent('', vid_url, {})
                    print(json.dumps(player, indent=2))
        
        print("\n====== Testing Search Content ======")
        search = spider.searchContent("avengers", False)
        print(f"Found {len(search['list'])} search results")
        # Print first 3 items only for brevity
        for i, video in enumerate(search['list'][:3]):
            print(f"Result {i+1}: {video['vod_name']} - {video['vod_id']}")
        
        print("\n====== Testing Search Content Page 2 ======")
        search_page2 = spider.searchContentPage("avengers", False, 2)
        print(f"Found {len(search_page2['list'])} search results on page 2")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        traceback.print_exc() 
