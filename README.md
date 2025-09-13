# GameMaps Downloader

从 GameMaps.com 下载地图文件的 Python 工具。

## 安装

```bash
pip install requests beautifulsoup4 cloudscraper aiohttp
git clone https://github.com/soloxiaoye2022/gamemaps_downloads.git
cd gamemaps_downloads
pip install -r requirements.txt
```

## 使用

**地图ID：**
```bash
python main.py 12345 67890
```

**URL：**
```bash
python main.py https://www.gamemaps.com/details/12345
```

**指定目录：**
```bash
python main.py 12345 -o ./maps
```

## 依赖
- requests
- beautifulsoup4
- cloudscraper
- aiohttp

## 许可证
MIT
