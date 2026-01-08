"""
爬虫模块
"""
from .base_crawler import BaseCrawler
from .xhs_crawler import XHSCrawler
from .douyin_crawler import DouyinCrawler
from .weibo_crawler import WeiboCrawler
from .zhihu_crawler import ZhihuCrawler
from .bilibili_crawler import BilibiliCrawler
from .kuaishou_crawler import KuaishouCrawler

__all__ = [
    "BaseCrawler",
    "XHSCrawler",
    "DouyinCrawler",
    "WeiboCrawler",
    "ZhihuCrawler",
    "BilibiliCrawler",
    "KuaishouCrawler",
]







