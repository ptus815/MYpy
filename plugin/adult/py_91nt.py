# -*- coding: utf-8 -*-
import sys
sys.path.append('..')
from base.spider import Spider
import re
from playwright.sync_api import sync_playwright

class Spider(Spider):
    def getName(self):
        return "91男同"

    def init(self, extend=""):
        self.host = "https://91nt.com"
        # 从页面快照看，大部分分类链接都是相对路径
        self.categories = {
            '精选G片': '/videos/all/watchings',
            '男同黑料': '/posts/category/all',
            '热搜词': '/hot/1',
            '鲜肉薄肌': '/videos/category/xrbj',
            '无套内射': '/videos/category/wtns',
            '制服诱惑': '/videos/category/zfyh',
            '耽美天菜': '/videos/category/dmfj',
            '肌肉猛男': '/videos/category/jrmn',
            '日韩GV': '/videos/category/rhgv',
            '欧美巨屌': '/videos/category/omjd',
            '多人群交': '/videos/category/drqp',
            '口交颜射': '/videos/category/kjys',
            '调教SM': '/videos/category/tjsm',
        }
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        pass

    def destroy(self):
        self.browser.close()
        self.playwright.stop()
        pass

    def fetch_page(self, url, timeout=15000):
        page = self.browser.new_page()
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=timeout)
            # 等待网络空闲，这是一个更通用的等待方式
            page.wait_for_load_state('networkidle', timeout=10000)
            content = page.content()
            return content
        finally:
            page.close()

    def homeContent(self, filter):
        result = {}
        classes = []
        for key in self.categories:
            classes.append({'type_name': key, 'type_id': self.categories[key]})
        result['class'] = classes
        return result

    def homeVideoContent(self):
        # 首页推荐内容与分类重复，直接调用分类内容
        return self.categoryContent('/videos/all/popular', '1', False, {})

    def categoryContent(self, tid, pg, filter, extend):
        self.log(f"开始抓取分类: {tid}, 页码: {pg}")
        result = {}
        url = self.host + tid + '?page=' + pg
        self.log(f"请求URL: {url}")
        
        html_content = self.fetch_page(url)
        self.log(f"页面获取成功，内容长度: {len(html_content)}")

        root = self.html(html_content)
        videos = []
        
        # 根据页面快照分析，视频列表项在
        # <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4">
        # 下的 listitem 中
        # 但为了普适性，我们直接查找所有看起来像视频项的链接
        # a 标签包含'vd-'或者'/posts/'的链接
        xpath_query = "//li[.//a[contains(@href, 'vd-') or contains(@href, '/posts/')]]"
        video_items = root.xpath(xpath_query)
        self.log(f"找到 {len(video_items)} 个视频项(li)")

        # 使用集合来避免重复
        processed_urls = set()

        for item in video_items:
            # item 现在是 li 元素
            href_element = item.xpath(".//a[contains(@href, 'vd-') or contains(@href, '/posts/')]")
            if not href_element:
                continue
            
            # 通常第一个链接是主链接
            href = href_element[0].get('href')

            if not href or href in processed_urls:
                continue
            
            # 使用XPath的string()函数来获取所有子孙节点的文本内容
            name_elements = item.xpath(".//a[@title]")
            name = ''
            if name_elements:
                name = name_elements[0].get('title', '').strip()

            if not name:
                # 如果title属性没有，就用string()函数获取链接的所有文本
                name = item.xpath("string(.//a)").strip()

            pic_elements = item.xpath(".//img")
            pic = ''
            if pic_elements:
                pic = pic_elements[0].get('data-src') or pic_elements[0].get('src')

            if not name or not pic:
                self.log(f"跳过不完整的项: href={href}, name='{name}', pic='{pic}'")
                continue

            # 确保图片链接是完整的
            if pic.startswith('/'):
                pic = self.host + pic

            if href.startswith('/'):
                href = self.host + href
            
            if href in processed_urls:
                continue
            
            processed_urls.add(href)

            vod_id_match = re.search(r'/(vd-[^/]+|posts/[^/]+)', href)
            if not vod_id_match:
                continue
            
            vod_id = vod_id_match.group(1).replace('/','-')
            
            remarks_elements = item.xpath(".//*[re:match(text(), '\d{2}:\d{2}')]", namespaces={'re': 'http://exslt.org/regular-expressions'})
            remarks = remarks_elements[0].text.strip() if remarks_elements else ''

            video_info = {
                'vod_id': vod_id,
                'vod_name': name,
                'vod_pic': pic,
                'vod_remarks': remarks
            }
            videos.append(video_info)
            self.log(f"成功添加视频: {video_info}")

        result['list'] = videos
        result['page'] = pg
        result['pagecount'] = 99
        result['limit'] = len(videos)
        result['total'] = 9999
        return result


    def detailContent(self, ids):
        # ids 是一个列表，但我们只处理第一个
        vod_id = ids[0]
        # 将 vod_id 转换回 url 路径
        url_path = vod_id.replace('-', '/')
        
        url = self.host + '/' + url_path
        html_content = self.fetch_page(url)
        root = self.html(html_content)

        title_element = root.xpath("//h1")
        title = title_element[0].text.strip() if title_element and title_element[0].text else ''
        if not title and title_element:
            title = root.xpath("string(//h1)")

        pic_element = root.xpath("//img[contains(@class, 'object-cover')]")
        pic = pic_element[0].get('src') if pic_element else ''
        # 尝试获取更详细的信息
        content_box = root.xpath("//div[contains(@class, 'leading-6')]")
        desc = root.xpath("string(//div[contains(@class, 'leading-6')])")

        # 播放列表
        play_url = ""
        # 从已经获取的html_content中解析
        play_url_element = root.xpath("//a[contains(@href, '.m3u8')]")
        if play_url_element:
            play_url = play_url_element[0].get('href')

        vod = {
            'vod_id': vod_id,
            'vod_name': title,
            'vod_pic': pic,
            'vod_content': desc,
            'vod_play_from': '91男同-PW',
            'vod_play_url': f"播放${play_url}"
        }
        
        return {'list': [vod]}

    def searchContent(self, key, quick, pg="1"):
        search_url = f"{self.host}/search/{key}?page={pg}"
        return self.categoryContent(f'/search/{key}', pg, False, {})

    def playerContent(self, flag, id, vipFlags):
        # id 就是 detailContent 中 vod_play_url 里的播放地址
        return {
            'parse': 0,
            'url': id,
            'header': {"User-Agent": "Mozilla/5.0"}
        }

if __name__ == '__main__':
    try:
        print("--- 开始Playwright测试 ---")
        p = Spider()
        p.init()
        
        # 测试分类页
        cat = p.categoryContent('/videos/all/popular', '1', False, {})
        print("--- 分类内容 ---")
        print(cat)
        
        # 测试详情页
        if cat.get('list'):
            print("\n--- 开始详情测试 ---")
            detail = p.detailContent([cat['list'][0]['vod_id']])
            print(detail)

        p.destroy()
        print("--- 测试结束 ---")
    except Exception as e:
        import traceback
        traceback.print_exc() 