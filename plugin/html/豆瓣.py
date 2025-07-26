     import json                                                                                            
│ │ import re                                                                                              │ │
│ │ from urllib.parse import urljoin                                                                       │ │
│ │ from spider import Spider                                                                              │ │
│ │                                                                                                        │ │
│ │ class DoubanSpider(Spider):                                                                            │ │
│ │                                                                                                        │ │
│ │     def init(self, extend=""):                                                                         │ │
│ │         self.extend = extend                                                                           │ │
│ │         self.base_url = "https://movie.douban.com"                                                     │ │
│ │         self.headers = {                                                                               │ │
│ │             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like   │ │
│ │ Gecko) Chrome/91.0.4472.124 Safari/537.36'                                                             │ │
│ │         }                                                                                              │ │
│ │                                                                                                        │ │
│ │     def getName(self):                                                                                 │ │
│ │         return "豆瓣电影"                                                                              │ │
│ │                                                                                                        │ │
│ │     def homeContent(self, filter):                                                                     │ │
│ │         result = {                                                                                     │ │
│ │             'class': [                                                                                 │ │
│ │                 {'type_id': 'hot', 'type_name': '热门'},                                               │ │
│ │                 {'type_id': 'new', 'type_name': '最新'},                                               │ │
│ │                 {'type_id': 'top250', 'type_name': 'Top250'},                                          │ │
│ │                 {'type_id': 'comedy', 'type_name': '喜剧'},                                            │ │
│ │                 {'type_id': 'action', 'type_name': '动作'},                                            │ │
│ │                 {'type_id': 'drama', 'type_name': '剧情'}                                              │ │
│ │             ],                                                                                         │ │
│ │             'filters': {                                                                               │ │
│ │                 'hot': [                                                                               │ │
│ │                     {'key': 'sort', 'name': '排序', 'value': [                                         │ │
│ │                         {'n': '热度', 'v': 'rank'},                                                    │ │
│ │                         {'n': '评分', 'v': 'score'},                                                   │ │
│ │                         {'n': '时间', 'v': 'time'}                                                     │ │
│ │                     ]}                                                                                 │ │
│ │                 ]                                                                                      │ │
│ │             }                                                                                          │ │
│ │         }                                                                                              │ │
│ │         return result                                                                                  │ │
│ │                                                                                                        │ │
│ │     def categoryContent(self, tid, pg, filter, extend):                                                │ │
│ │         page = int(pg)                                                                                 │ │
│ │         start = (page - 1) * 20                                                                        │ │
│ │                                                                                                        │ │
│ │         if tid == 'hot':                                                                               │ │
│ │             url = f"{self.base_url}/cinema/nowplaying/beijing/"                                        │ │
│ │         elif tid == 'top250':                                                                          │ │
│ │             url = f"{self.base_url}/top250?start={start}"                                              │ │
│ │         else:                                                                                          │ │
│ │             url = f"{self.base_url}/tag/{tid}?start={start}"                                           │ │
│ │                                                                                                        │ │
│ │         rsp = self.fetch(url, headers=self.headers)                                                    │ │
│ │         content = rsp.text                                                                             │ │
│ │                                                                                                        │ │
│ │         videos = []                                                                                    │ │
│ │         if tid == 'top250':                                                                            │ │
│ │             videos = self._parseTop250(content)                                                        │ │
│ │         else:                                                                                          │ │
│ │             videos = self._parseMovieList(content)                                                     │ │
│ │                                                                                                        │ │
│ │         return {                                                                                       │ │
│ │             'list': videos,                                                                            │ │
│ │             'page': page,                                                                              │ │
│ │             'pagecount': 10,                                                                           │ │
│ │             'limit': 20,                                                                               │ │
│ │             'total': 200                                                                               │ │
│ │         }                                                                                              │ │
│ │                                                                                                        │ │
│ │     def detailContent(self, ids):                                                                      │ │
│ │         movie_id = ids[0]                                                                              │ │
│ │         url = f"{self.base_url}/subject/{movie_id}/"                                                   │ │
│ │                                                                                                        │ │
│ │         rsp = self.fetch(url, headers=self.headers)                                                    │ │
│ │         content = rsp.text                                                                             │ │
│ │         doc = self.html(content)                                                                       │ │
│ │                                                                                                        │ │
│ │         title = doc.xpath('//h1/span[@property="v:itemreviewed"]/text()')[0] if                        │ │
│ │ doc.xpath('//h1/span[@property="v:itemreviewed"]/text()') else ""                                      │ │
│ │         pic = doc.xpath('//img[@rel="v:image"]/@src')[0] if doc.xpath('//img[@rel="v:image"]/@src')    │ │
│ │ else ""                                                                                                │ │
│ │         desc = doc.xpath('//span[@property="v:summary"]/text()')[0] if                                 │ │
│ │ doc.xpath('//span[@property="v:summary"]/text()') else ""                                              │ │
│ │         rating = doc.xpath('//strong[@property="v:average"]/text()')[0] if                             │ │
│ │ doc.xpath('//strong[@property="v:average"]/text()') else ""                                            │ │
│ │                                                                                                        │ │
│ │         info = doc.xpath('//div[@id="info"]//text()')                                                  │ │
│ │         director = self.regStr(r'导演.*?:(.*?)主演', ''.join(info))                                    │ │
│ │         actor = self.regStr(r'主演.*?:(.*?)类型', ''.join(info))                                       │ │
│ │         year = doc.xpath('//span[@property="v:initialReleaseDate"]/text()')[0] if                      │ │
│ │ doc.xpath('//span[@property="v:initialReleaseDate"]/text()') else ""                                   │ │
│ │                                                                                                        │ │
│ │         vod = {                                                                                        │ │
│ │             'vod_id': movie_id,                                                                        │ │
│ │             'vod_name': title,                                                                         │ │
│ │             'vod_pic': pic,                                                                            │ │
│ │             'vod_content': desc,                                                                       │ │
│ │             'vod_director': director,                                                                  │ │
│ │             'vod_actor': actor,                                                                        │ │
│ │             'vod_year': year,                                                                          │ │
│ │             'vod_score': rating,                                                                       │ │
│ │             'vod_play_from': '豆瓣',                                                                   │ │
│ │             'vod_play_url': f'播放${url}'                                                              │ │
│ │         }                                                                                              │ │
│ │                                                                                                        │ │
│ │         return {'list': [vod]}                                                                         │ │
│ │                                                                                                        │ │
│ │     def searchContent(self, key, quick, pg="1"):                                                       │ │
│ │         page = int(pg)                                                                                 │ │
│ │         start = (page - 1) * 15                                                                        │ │
│ │                                                                                                        │ │
│ │         url = f"{self.base_url}/search"                                                                │ │
│ │         params = {                                                                                     │ │
│ │             'q': key,                                                                                  │ │
│ │             'start': start,                                                                            │ │
│ │             'cat': '1002'                                                                              │ │
│ │         }                                                                                              │ │
│ │                                                                                                        │ │
│ │         rsp = self.fetch(url, params=params, headers=self.headers)                                     │ │
│ │         content = rsp.text                                                                             │ │
│ │                                                                                                        │ │
│ │         videos = self._parseSearchResults(content)                                                     │ │
│ │                                                                                                        │ │
│ │         return {                                                                                       │ │
│ │             'list': videos,                                                                            │ │
│ │             'page': page,                                                                              │ │
│ │             'pagecount': 5,                                                                            │ │
│ │             'limit': 15,                                                                               │ │
│ │             'total': 75                                                                                │ │
│ │         }                                                                                              │ │
│ │                                                                                                        │ │
│ │     def playerContent(self, flag, id, vipFlags):                                                       │ │
│ │         return {                                                                                       │ │
│ │             'parse': 0,                                                                                │ │
│ │             'playUrl': '',                                                                             │ │
│ │             'url': id                                                                                  │ │
│ │         }                                                                                              │ │
│ │                                                                                                        │ │
│ │     def _parseTop250(self, content):                                                                   │ │
│ │         doc = self.html(content)                                                                       │ │
│ │         videos = []                                                                                    │ │
│ │                                                                                                        │ │
│ │         items = doc.xpath('//ol[@class="grid_view"]/li')                                               │ │
│ │         for item in items:                                                                             │ │
│ │             title = item.xpath('.//span[@class="title"]/text()')[0] if                                 │ │
│ │ item.xpath('.//span[@class="title"]/text()') else ""                                                   │ │
│ │             pic = item.xpath('.//img/@src')[0] if item.xpath('.//img/@src') else ""                    │ │
│ │             rating = item.xpath('.//span[@class="rating_num"]/text()')[0] if                           │ │
│ │ item.xpath('.//span[@class="rating_num"]/text()') else ""                                              │ │
│ │             url = item.xpath('.//a/@href')[0] if item.xpath('.//a/@href') else ""                      │ │
│ │             movie_id = self.regStr(r'/subject/(\d+)/', url)                                            │ │
│ │                                                                                                        │ │
│ │             videos.append({                                                                            │ │
│ │                 'vod_id': movie_id,                                                                    │ │
│ │                 'vod_name': title,                                                                     │ │
│ │                 'vod_pic': pic,                                                                        │ │
│ │                 'vod_score': rating                                                                    │ │
│ │             })                                                                                         │ │
│ │                                                                                                        │ │
│ │         return videos                                                                                  │ │
│ │                                                                                                        │ │
│ │     def _parseMovieList(self, content):                                                                │ │
│ │         doc = self.html(content)                                                                       │ │
│ │         videos = []                                                                                    │ │
│ │                                                                                                        │ │
│ │         items = doc.xpath('//div[@class="item"]')                                                      │ │
│ │         for item in items:                                                                             │ │
│ │             title = item.xpath('.//span[@class="title"]/text()')[0] if                                 │ │
│ │ item.xpath('.//span[@class="title"]/text()') else ""                                                   │ │
│ │             pic = item.xpath('.//img/@src')[0] if item.xpath('.//img/@src') else ""                    │ │
│ │             url = item.xpath('.//a/@href')[0] if item.xpath('.//a/@href') else ""                      │ │
│ │             movie_id = self.regStr(r'/subject/(\d+)/', url)                                            │ │
│ │                                                                                                        │ │
│ │             videos.append({                                                                            │ │
│ │                 'vod_id': movie_id,                                                                    │ │
│ │                 'vod_name': title,                                                                     │ │
│ │                 'vod_pic': pic                                                                         │ │
│ │             })                                                                                         │ │
│ │                                                                                                        │ │
│ │         return videos                                                                                  │ │
│ │                                                                                                        │ │
│ │     def _parseSearchResults(self, content):                                                            │ │
│ │         doc = self.html(content)                                                                       │ │
│ │         videos = []                                                                                    │ │
│ │                                                                                                        │ │
│ │         items = doc.xpath('//div[@class="result"]')                                                    │ │
│ │         for item in items:                                                                             │ │
│ │             title_elem = item.xpath('.//h3/a')                                                         │ │
│ │             if title_elem:                                                                             │ │
│ │                 title = title_elem[0].text or ""                                                       │ │
│ │                 url = title_elem[0].get('href', '')                                                    │ │
│ │                 movie_id = self.regStr(r'/subject/(\d+)/', url)                                        │ │
│ │                                                                                                        │ │
│ │                 pic = item.xpath('.//img/@src')[0] if item.xpath('.//img/@src') else ""                │ │
│ │                                                                                                        │ │
│ │                 videos.append({                                                                        │ │
│ │                     'vod_id': movie_id,                                                                │ │
│ │                     'vod_name': title,                                                                 │ │
│ │                     'vod_pic': pic                                                                     │ │
│ │                 })                                                                                     │ │
│ │                                                                                                        │ │
│ │         return videos
