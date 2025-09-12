import asyncio
import argparse
import re
from pathlib import Path
from download import batch_download_map


def format_file_size(size_bytes):
    """将字节大小格式化为人类可读的形式"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def extract_map_id(input_str):
    """从输入中提取地图ID，支持直接ID或URL"""
    if input_str.isdigit():
        return input_str
    
    url_pattern = r'(?:gamemaps\.com/(?:details|download)/)(\d+)'
    match = re.search(url_pattern, input_str, re.IGNORECASE)
    if match:
        return match.group(1)
    
    return input_str


def main():
    parser = argparse.ArgumentParser(description="GameMaps.com 地图下载器")
    parser.add_argument("map_inputs", nargs="+", help="地图ID或URL列表")
    parser.add_argument("-o", "--output", type=Path, default=Path("./downloads"), help="保存目录")
    args = parser.parse_args()

    map_ids = []
    for input_str in args.map_inputs:
        map_id = extract_map_id(input_str.strip())
        if map_id.isdigit():
            map_ids.append(map_id)
        else:
            print(f"无效输入: {input_str}")
    
    if not map_ids:
        print("未找到有效地图ID")
        return

    print(f"地图ID: {', '.join(map_ids)}")
    
    args.output.mkdir(parents=True, exist_ok=True)

    async def run():
        print("开始下载...")
        results = await batch_download_map(map_ids, args.output)
        
        success_count = 0
        for res in results:
            if isinstance(res, Exception):
                print(f"异常: {res}")
            elif res.get("success"):
                elapsed_time = res.get('elapsed_time_ms', 0)
                info_time = res.get('info_elapsed_time_ms', 0)
                file_size = res.get('content_length', 0)
                formatted_size = format_file_size(file_size)
                print(f"已下载: {res['file_path']} ({formatted_size}, {info_time}ms, {elapsed_time}ms)")
                success_count += 1
            else:
                print(f"失败: {res['message']}")
        
        print(f"完成: {success_count}/{len(map_ids)}")

    asyncio.run(run())


if __name__ == "__main__":
    main()
