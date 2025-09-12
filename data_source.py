import asyncio
import datetime
import re
import json
import cloudscraper25
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class GameMapsDownloader:
    def __init__(self):
        self.session = cloudscraper25.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        self.timeout = 30
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        })
        self.base_url = 'https://www.gamemaps.com'
        self.download_buttons_info = []
        self.external_scripts = []
        self.inline_scripts = []

    def _check_cloudflare_challenge(self):
        response = self.session.get(self.base_url, allow_redirects=True, timeout=self.timeout)
        if 'cloudflare' in response.text.lower() and '/cdn-cgi/challenge-platform/' in response.text.lower():
            logger.info('检测到Cloudflare验证，正在尝试通过...')
            if hasattr(self.session, 'solve_cf_challenge'):
                solved = self.session.solve_cf_challenge(response)
                if solved:
                    logger.info('成功通过Cloudflare验证')
                    return True
                else:
                    logger.error('无法通过Cloudflare验证')
                    return False
            else:
                logger.warning('cloudscraper不支持自动解决Cloudflare验证')
                return False
        else:
            logger.info('未检测到Cloudflare验证或已通过')
            return True

    def _analyze_download_buttons(self, soup):
        logger.info('开始检测下载按钮...')
        download_buttons = []
        a_download = soup.find_all('a', href=lambda href: href and 'download' in href.lower())
        a_download = [btn for btn in a_download if btn.text.strip()]
        download_buttons.extend(a_download)
        button_text = soup.find_all('button', text=lambda text: text and ('download' in text.lower() or '下载' in text.lower()))
        download_buttons.extend(button_text)
        class_download = soup.find_all('div', class_=lambda c: c and 'download' in c.lower())
        class_download = [btn for btn in class_download if btn.text.strip() and len(btn.text.strip()) < 100]
        download_buttons.extend(class_download)
        download_buttons = list(set(download_buttons))
        filtered_buttons = [btn for btn in download_buttons if btn.text.strip() and len(btn.text.strip()) <= 100 and not (btn.name == 'a' and btn.get('href') == '/downloads')]
        self.download_buttons_count = len(filtered_buttons)
        logger.info(f'找到{self.download_buttons_count}个下载按钮')
        self.download_buttons_info = [
            {
                'index': i,
                'tag': button.name,
                'text': button.text.strip()[:100],
                'href': button.get('href', ''),
                'class': button.get('class', []),
                'id': button.get('id', '')
            }
            for i, button in enumerate(filtered_buttons)
        ]
        return filtered_buttons

    def _analyze_javascript(self, soup):
        script_tags = soup.find_all('script')
        logger.info(f'页面中找到{len(script_tags)}个script标签')
        self.inline_scripts = [
            {'index': i, 'content': script.string.strip()}
            for i, script in enumerate(script_tags)
            if script.string and script.string.strip()
        ]
        self.external_scripts = [
            {'index': i, 'url': (script.get('src') if script.get('src').startswith('http') else f"{self.base_url}{script.get('src')}")}
            for i, script in enumerate(script_tags)
            if script.get('src')
        ]

    def get_download_info(self, map_id: str) -> dict | None:
        if not self._check_cloudflare_challenge():
            logger.error('无法通过CF挑战，分析终止')
            return None

        map_detail_url = f'{self.base_url}/details/{map_id}'
        logger.info(f'访问地图详情页: {map_detail_url}')
        response = self.session.get(map_detail_url, allow_redirects=True, timeout=self.timeout)
        logger.info(f'地图详情页响应状态码: {response.status_code}')
        soup = BeautifulSoup(response.text, 'html.parser')
        self._analyze_download_buttons(soup)
        self._analyze_javascript(soup)

        download_url = f'{self.base_url}/downloads/download'
        data = {'ids[]': map_id, 'noqueue': 'true', 'direct': 'true'}
        headers = {**self.session.headers, 'Content-Type': 'application/x-www-form-urlencoded', 'Origin': self.base_url, 'Referer': map_detail_url}
        response = self.session.post(download_url, data=data, headers=headers, allow_redirects=True, timeout=self.timeout)
        final_url = response.url
        logger.info(f'最终URL: {final_url}')

        if response.status_code == 200 and 'Content-Disposition' in response.headers:
            cd = response.headers['Content-Disposition']
            filename = re.search(r'filename="?([^"]+)"?', cd).group(1) if re.search(r'filename="?([^"]+)"?', cd) else final_url.split('/')[-1] or f'l4d2_map_{map_id}.zip'
            content_length = int(response.headers.get('Content-Length', 0))
            logger.info(f'文件名: {filename}, 大小: {content_length} 字节')

            analysis_result = {
                'timestamp': datetime.datetime.now().isoformat(),
                'map_id': map_id,
                'map_detail_url': map_detail_url,
                'external_scripts_count': len(self.external_scripts),
                'inline_scripts_count': len(self.inline_scripts),
                'download_buttons_count': self.download_buttons_count,
                'download_buttons_info': self.download_buttons_info,
                'final_download_url': str(final_url),
                'response_status_code': response.status_code
            }
            try:
                with open(f'download_analysis_{map_id}.json', 'w', encoding='utf-8') as f:
                    json.dump(analysis_result, f, ensure_ascii=False, indent=2)
                logger.info(f'分析结果已保存到download_analysis_{map_id}.json')
            except Exception as e:
                logger.warning(f'保存分析结果失败: {e}')

            return {
                'file_name': filename,
                'content_length': content_length,
                'download_url': str(final_url),
                'status': 'success'
            }
        elif response.status_code in (301, 302):
            redirect_response = self.session.get(final_url, allow_redirects=True, timeout=self.timeout)
            if 'Content-Disposition' in redirect_response.headers:
                cd = redirect_response.headers['Content-Disposition']
                filename = re.search(r'filename="?([^"]+)"?', cd).group(1) if re.search(r'filename="?([^"]+)"?', cd) else final_url.split('/')[-1] or f'l4d2_map_{map_id}.zip'
                return {
                    'file_name': filename,
                    'content_length': int(redirect_response.headers.get('Content-Length', 0)),
                    'download_url': str(final_url),
                    'status': 'success'
                }
            else:
                logger.warning('重定向后没有Content-Disposition头')
                return None
        else:
            logger.error(f'下载请求失败，状态码: {response.status_code}')
            return None
