import asyncio
import argparse
import os
from pathlib import Path
from download import batch_download_map


def format_file_size(size_bytes):
    """将字节大小格式化为人类可读的形式"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def main():
    parser = argparse.ArgumentParser(description="GameMaps.com 地图下载器（仅下载，不解压）")
    parser.add_argument("map_ids", nargs="+", help="地图ID列表，例如 12345 67890")
    parser.add_argument("-o", "--output", type=Path, default=Path("./downloads"), help="保存目录，默认为 ./downloads")
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)

    async def run():
        print(" 开始批量下载地图...")
        results = await batch_download_map(args.map_ids, args.output)
        for res in results:
            if isinstance(res, Exception):
                print(f" 异常: {res}")
            elif res.get("success"):
                elapsed_time = res.get('elapsed_time_ms', 0)
                info_time = res.get('info_elapsed_time_ms', 0)
                file_size = res.get('content_length', 0)
                formatted_size = format_file_size(file_size)
                print(f" 已下载: {res['file_path']} (大小: {formatted_size}, 获取信息耗时: {info_time} 毫秒, 总耗时: {elapsed_time} 毫秒)")
            else:
                print(f" 失败: {res['message']}")

    asyncio.run(run())

if __name__ == "__main__":
    main()
