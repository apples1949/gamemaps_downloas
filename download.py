import asyncio
import tempfile
from pathlib import Path
import logging
import time
from data_source import GameMapsDownloader

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

class GamemapsDownloadManager:
    def __init__(self):
        self.downloader = GameMapsDownloader()
        self.semaphore = asyncio.Semaphore(5)
        self.session = self.downloader.session

    def _download_with_cloudscraper(self, url: str, save_path: Path) -> str | None:
        try:
            logger.info(f"开始下载文件: {save_path.name}")
            # 使用流式下载提高大文件下载效率
            response = self.session.get(url, allow_redirects=True, timeout=30, stream=True)
            if response.status_code == 200:
                # 获取文件总大小
                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0
                with open(save_path, 'wb') as f:
                    # 分块写入文件
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            # 记录下载进度
                            if total_size > 0:
                                progress = (downloaded_size / total_size) * 100
                                logger.debug(f"下载进度: {progress:.1f}% ({downloaded_size}/{total_size} bytes)")
                logger.info(f"文件下载成功: {save_path}")
                return None
            else:
                error_msg = f"下载失败，HTTP状态码: {response.status_code}"
                logger.error(error_msg)
                return error_msg
        except Exception as e:
            error_msg = f"下载过程发生错误: {str(e)}"
            logger.error(error_msg)
            return error_msg

    async def download_map(self, map_id: str, save_path: Path, download_info: dict = None) -> dict:
        logger.info(f"开始处理地图ID: {map_id}，保存路径: {save_path}")
        try:
            info_start_time = time.perf_counter()
            if not download_info:
                loop = asyncio.get_running_loop()
                download_info = await loop.run_in_executor(
                    None,
                    lambda: self.downloader.get_download_info(map_id)
                )
            info_end_time = time.perf_counter()
            info_elapsed_time_ms = (info_end_time - info_start_time) * 1000
            logger.info(f"获取文件信息和下载地址耗时: {round(info_elapsed_time_ms, 2)} 毫秒")

            if not download_info or download_info.get('status') != 'success':
                error_msg = download_info.get('message', '未知错误') if download_info else '未获取到下载信息'
                logger.error(f"地图 {map_id} 处理失败: {error_msg}")
                return {
                    'map_id': map_id,
                    'success': False,
                    'message': error_msg
                }

            file_name = download_info['file_name']
            download_url = download_info['download_url']
            logger.info(f"成功获取地图 {map_id} 下载链接: {download_url}")

            async with self.semaphore:
                file_save_path = save_path / file_name
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: self._download_with_cloudscraper(download_url, file_save_path)
                )

                if result is None:
                    logger.info(f"地图 {map_id} 下载完成: {file_save_path}")
                    return {
                        'map_id': map_id,
                        'success': True,
                        'file_path': str(file_save_path),
                        'file_name': file_name,
                        'content_length': download_info.get('content_length', 0),
                        'info_elapsed_time_ms': round(info_elapsed_time_ms, 2)
                    }
                else:
                    logger.error(result)
                    return {
                        'map_id': map_id,
                        'success': False,
                        'message': result
                    }

        except Exception as e:
            logger.error(f"地图 {map_id} 处理异常: {e}")
            return {
                'map_id': map_id,
                'success': False,
                'message': str(e)
            }


# ------------- 对外接口 -------------
_download_manager = GamemapsDownloadManager()

async def download_map(map_id: str, save_path: Path, download_info: dict = None) -> dict:
    start_time = time.perf_counter()
    result = await _download_manager.download_map(map_id, save_path, download_info)
    end_time = time.perf_counter()
    elapsed_time_ms = (end_time - start_time) * 1000
    result['elapsed_time_ms'] = round(elapsed_time_ms, 2)
    return result

async def batch_download_map(map_ids: list, save_path: Path) -> list:
    start_time = time.perf_counter()
    tasks = [download_map(map_id, save_path) for map_id in map_ids]
    results = await asyncio.gather(*tasks)
    end_time = time.perf_counter()
    total_time_ms = (end_time - start_time) * 1000
    print(f" 批量下载完成，总耗时: {round(total_time_ms, 2)} 毫秒")
    return results
    return await asyncio.gather(*tasks, return_exceptions=True)
