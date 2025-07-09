# -*- coding: utf-8 -*-
# FMovies crawler for fmoviesto.cc
import re
import sys
import json
import base64
from Crypto.Cipher import AES
from urllib.parse import quote_plus, urlparse, parse_qs, unquote_plus
from pyquery import PyQuery as pq
sys.path.append('..')
from base.spider import Spider
import requests

# From https://github.com/Ciarands/vidsrc-to-resolver/blob/main/vidsrc_to_resolver/llsc.py
def unpad(s):
    return s[:-ord(s[len(s)-1:])]

class Spider(Spider):

    def init(self, extend=""):
        self.site_url = 'https://fmoviesto.cc'
        self.site_name = 'FMovies'
        self.img_prefix = 'https://wsrv.nl?url='
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': self.site_url,
            'Referer': self.site_url + '/',
            'Sec-Ch-Ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
        self.vidsrc_key = "" # Will be fetched dynamically
        
    def getName(self):
        return self.site_name
        
    def homeContent(self, filter):
        result = {}
        cate = {
            "电影": "movie",
            "剧集": "tv-show",
            "高分": "top-imdb",
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
            "top-imdb": [],
        }
        
        result['class'] = classes
        result['filters'] = filters
        return result

    def homeVideoContent(self):
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
        try:
            # The 'ids' is now a JSON string containing all necessary info
            vod_info = json.loads(ids[0])
            url = self.site_url + vod_info['vod_id']
            
            html = self.fetch(url, headers=self.headers).text
            doc = pq(html)

            play_from = []
            play_url = []
            
            # The server list is loaded via AJAX
            movie_id = doc('#watch-iframe').attr('data-id') or re.search(r'get_movie_info\("([^"]+)"\)', html).group(1)
            
            # Determine if it's a movie or tv show from the vod_id
            if 'movie' in vod_info['vod_id']:
                ajax_url = f"{self.site_url}/ajax/v2/movie/servers/{movie_id}"
                servers_html = self.fetch(ajax_url, headers=self.headers).json().get('html', '')
                servers_doc = pq(servers_html)
                
                for link in servers_doc('.server-item').items():
                    server_name = link.find('a').text().strip()
                    s_id = link.attr('data-id')
                    if server_name and s_id:
                        play_from.append(server_name)
                        play_url.append(f"播放$/movie/{movie_id}/{s_id}")

            elif 'tv' in vod_info['vod_id']:
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
                        servers_html = self.fetch(servers_url, headers=self.headers).json().get('html', '')
                        servers_doc = pq(servers_html)
                        
                        for server_link in servers_doc('.server-item').items():
                            server_name = server_link.text().strip()
                            s_link_id = server_link.attr('data-id')
                            if server_name and s_link_id:
                                if server_name not in all_server_episodes:
                                    all_server_episodes[server_name] = []
                                all_server_episodes[server_name].append(f"{s_name} {ep_name}$/tv/{movie_id}/{s_link_id}/{ep_id}")
                
                for server_name, episodes in all_server_episodes.items():
                    play_from.append(server_name)
                    play_url.append("#".join(episodes))

            if play_from and play_url:
                vod_info['vod_play_from'] = "$$$".join(play_from)
                vod_info['vod_play_url'] = "$$$".join(play_url)

            return {'list': [vod_info]}
        except Exception as e:
            print(f"Error in detailContent: {e}")
            traceback.print_exc()
            return {'list': []}

    def get_detail_item(self, doc, label):
        row = doc(f'.elements .row:contains("{label}")')
        if row: return row.find('.col-md-10').text().strip()
        return ""

    def searchContent(self, key, quick):
        return self.searchContentPage(key, quick, 1)

    def searchContentPage(self, key, quick, pg=1):
        search_url = f"{self.site_url}/search/{quote_plus(key)}"
        if int(pg) > 1: search_url += f"?page={pg}"
        return self.getMovieList(search_url, pg)

    def _get_vidsrc_key(self):
        if self.vidsrc_key: return self.vidsrc_key
        try:
            # This key seems to be static for now, but we can make it dynamic if needed
            resp = self.fetch("https://raw.githubusercontent.com/Ciarands/vidsrc-keys/main/keys.json").json()
            self.vidsrc_key = resp[0]
            return self.vidsrc_key
        except:
            # Fallback key
            return "63V158927827493927426742635272"

    def _decode_source_url(self, encoded_url, key):
        encoded = base64.b64decode(encoded_url)
        
        # The last 16 bytes are the IV, the rest is the ciphertext
        iv = encoded[-16:]
        ciphertext = encoded[:-16]

        cipher = AES.new(key.encode(), AES.MODE_CBC, iv=iv)
        decrypted = cipher.decrypt(ciphertext)
        
        return unpad(decrypted).decode('utf-8')

    def playerContent(self, flag, id, vipFlags):
        try:
            # id is now a composite key like /movie/{movie_id}/{server_id} or /tv/{tv_id}/{server_id}/{episode_id}
            parts = id.strip('/').split('/')
            media_type, media_id, server_id = parts[0], parts[1], parts[2]
            episode_id = parts[3] if len(parts) > 3 else None

            # 1. Get the vidsrc.to embed URL
            ajax_url = f"{self.site_url}/ajax/v2/embed/servers?id={server_id}"
            embed_url_encrypted = self.fetch(ajax_url, headers=self.headers).json().get('url')
            
            # The embed URL is also encrypted with a key that we can find by analyzing the site's JS
            # For now, let's assume a static key or a simple decoding process
            # Let's decode it - it seems to be base64-encoded then reversed
            embed_url = base64.b64decode(embed_url_encrypted[::-1]).decode('utf-8')
            
            if not embed_url.startswith('http'):
                embed_url = "https:" + embed_url

            # 2. Get the subtitles and the encrypted source URL from vidsrc
            vidsrc_to_url = ""
            vidsrc_id = ""
            if "vidsrc.to" in embed_url:
                vidsrc_to_url = embed_url
                vidsrc_id = urlparse(vidsrc_to_url).path.split('/')[-1]
            else: # Sometimes it's a different domain like "https://rc.vidsrc.me/"
                # We need to follow redirects to find the final vidsrc.to URL
                resp = self.fetch(embed_url, headers=self.headers, allow_redirects=True)
                vidsrc_to_url = resp.url
                vidsrc_id = urlparse(vidsrc_to_url).path.split('/')[-1]
            
            # 3. Get the futoken to make the call to get the final source
            futoken_url = "https://vidsrc.to/futoken"
            futoken_resp = self.fetch(futoken_url, headers={'Referer': vidsrc_to_url}).text
            futoken = re.search(r'var\s+k\s*=\s*[\'"]([^\'"]+)', futoken_resp).group(1)

            # 4. Get the final encrypted source URL
            key = self._get_vidsrc_key()
            final_url_req_url = f"https://vidsrc.to/ajax/embed/source/{vidsrc_id}?token={futoken}"
            source_resp = self.fetch(final_url_req_url, headers={'Referer': vidsrc_to_url}).json()
            
            encoded_source = source_resp.get('result', {}).get('url')
            if not encoded_source:
                return {'parse': 1, 'url': vidsrc_to_url} # Fallback

            # 5. Decode the source URL
            decoded_url = self._decode_source_url(encoded_source, key)

            return {'parse': 0, 'url': decoded_url, 'header': {'Referer': 'https://vidsrc.to/'}}

        except Exception as e:
            print(f"Error in playerContent: {e}")
            traceback.print_exc()
            return {'parse': 1, 'url': id}

    def getMovieList(self, url, pg='1'):
        try:
            html = self.fetch(url, headers=self.headers).text
            doc = pq(html)
            
            videos = []
            for item in doc('div.flw-item').items():
                vod_id = item.find('a.film-poster-ahref').attr('href')
                if not vod_id: continue
                
                vod_name = item.find('.film-name a').attr('title')
                vod_pic = item.find('.film-poster-img').attr('data-src')
                if vod_pic and not vod_pic.startswith('http'):
                    vod_pic = f"https:{vod_pic}"
                if vod_pic: vod_pic = f"{self.img_prefix}{vod_pic}"
                
                vod_remarks = item.find('.film-poster .quality').text().strip()
                
                # Following naif.py's logic: pass all info directly
                vod_info = {
                    "vod_id": vod_id, "vod_name": vod_name,
                    "vod_pic": vod_pic, "vod_remarks": vod_remarks
                }

                # To pass this dict through the app, we must serialize it.
                # The 'id' field is the only one guaranteed to pass through, so we use it.
                videos.append({
                    "vod_id": json.dumps(vod_info, ensure_ascii=False),
                    "vod_name": vod_name,
                    "vod_pic": vod_pic,
                    "vod_remarks": vod_remarks
                })
            
            pagecount = 0
            pagination_links = doc('.pagination a[href*="?page="]')
            if pagination_links:
                last_page_href = pagination_links.eq(-1).attr('href')
                if last_page_href:
                    qs = parse_qs(urlparse(last_page_href).query)
                    pagecount = int(qs.get('page', [1])[0])
            
            return {
                'list': videos, 'page': int(pg), 'pagecount': pagecount or int(pg),
                'limit': len(videos), 'total': pagecount * len(videos) if pagecount else len(videos)
            }
        except Exception as e:
            print(f"Error in getMovieList: {e}")
            return {'list': []}
    
    def localProxy(self, params):
        return [200, "text/plain", "Not implemented", {}]

if __name__ == "__main__":
    spider = Spider()
    spider.init()
    
    import traceback
    try:
        # Test Home
        home_videos = spider.homeVideoContent()
        print(f"====== Found {len(home_videos.get('list', []))} videos on Home Page ======")
        
        # Test Movie Detail & Player
        if home_videos.get('list'):
            movie_id = home_videos['list'][0]['vod_id']
            print(f"\n====== Testing Movie: {movie_id} ======")
            detail = spider.detailContent([movie_id])
            
            if detail.get('list'):
                vod = detail['list'][0]
                print(f"  Title: {vod.get('vod_name')}")
                play_from = vod.get('vod_play_from', '')
                play_url = vod.get('vod_play_url', '')

                if play_from and play_url:
                    sources = play_from.split('$$$')
                    urls = play_url.split('$$$')
                    print(f"  Found {len(sources)} Playback Lines: {sources}")

                    # Test the first line
                    player_id = urls[0].split('$')[1]
                    print(f"  Testing Player for first line, ID: {player_id}")
                    player_content = spider.playerContent('', player_id, {})
                    print(f"  Player Content: {json.dumps(player_content)}")
                else:
                    print("  No playback lines found for this movie.")

        # Test TV Show Detail & Player
        tv_id = '/tv/fallout-2024-full-112291' # A known TV show
        print(f"\n====== Testing TV Show: {tv_id} ======")
        detail = spider.detailContent([tv_id])
        if detail.get('list'):
            vod = detail['list'][0]
            print(f"  Title: {vod.get('vod_name')}")
            play_from = vod.get('vod_play_from', '')
            play_url = vod.get('vod_play_url', '')

            if play_from and play_url:
                sources = play_from.split('$$$')
                urls = play_url.split('$$$')
                print(f"  Found {len(sources)} Playback Lines")
                
                # Test the first episode of the first line
                first_episode_url = urls[0].split('#')[0]
                player_id = first_episode_url.split('$')[1]
                print(f"  Testing Player for first episode, ID: {player_id}")
                player_content = spider.playerContent('', player_id, {})
                print(f"  Player Content: {json.dumps(player_content)}")
            else:
                print("  No playback lines found for this TV show.")

    except Exception as e:
        print(f"\n!!!!!! An error occurred during testing !!!!!!")
        traceback.print_exc() 
