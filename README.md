# GameMaps Downloader

一个用于从 GameMaps.com 下载地图文件的 Python 工具。

## 功能
- 批量下载地图文件
- 异步并发下载
- 自动处理重定向和文件保存
- 支持进度监控

## 安装

1. 克隆仓库
```bash
git clone [你的仓库地址]
cd gamemaps
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

## 使用

### 基本用法
下载单个或多个地图：
```bash
python main.py 12345 67890 11111
```

### 指定输出目录
```bash
python main.py 12345 67890 -o ./my_maps
```

## 依赖
- requests
- beautifulsoup4
- cloudscraper
- aiohttp
- asyncio

## 注意事项
- 请确保你有权下载相关地图文件
- 下载的文件将保存在指定目录中
- 建议分批下载大量地图以避免被限制

## 许可证
MIT License