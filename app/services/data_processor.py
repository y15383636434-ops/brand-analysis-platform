"""
数据整理服务
将MediaCrawler的JSON数据整理为结构化格式，用于AI分析
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from app.services.data_cleaner import DataCleaner


class DataProcessor:
    """数据整理处理器"""
    
    def __init__(self):
        self.cleaner = DataCleaner()
    
    def load_json_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        加载JSON文件
        
        Args:
            file_path: JSON文件路径
            
        Returns:
            数据列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 确保返回列表格式
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # 如果是字典，尝试提取items字段
                if "items" in data:
                    return data["items"]
                elif "data" in data:
                    return data["data"]
                else:
                    return [data]
            else:
                logger.warning(f"未知的数据格式: {type(data)}")
                return []
        except Exception as e:
            logger.error(f"加载JSON文件失败: {e}")
            return []
    
    def extract_text_from_item(self, item: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """
        从数据项中提取文本信息和互动数据
        
        Args:
            item: 原始数据项
            platform: 平台代码
            
        Returns:
            提取的信息
        """
        text_info = {
            "content": "",
            "title": "",
            "author": "",
            "comments": [],
            "platform": platform,
            "url": "",
            "likes": 0,
            "comments_count": 0,
            "shares": 0,
            "date": ""
        }
        
        # 通用字段提取
        text_info["url"] = item.get("detail_url", "") or item.get("url", "")
        
        # 尝试提取互动数据（不同平台字段可能不同，这里做尽力尝试）
        # 点赞数
        for key in ["liked_count", "digg_count", "likes", "like_count"]:
            if key in item:
                try:
                    text_info["likes"] = int(item[key])
                    break
                except:
                    pass
                    
        # 评论数
        for key in ["comment_count", "comments_count"]:
            if key in item:
                try:
                    text_info["comments_count"] = int(item[key])
                    break
                except:
                    pass

        # 分享/收藏数
        for key in ["share_count", "collected_count", "collect_count"]:
            if key in item:
                try:
                    text_info["shares"] += int(item[key])
                except:
                    pass
        
        # 日期提取
        for key in ["create_time", "publish_time", "created_at", "date"]:
            if key in item:
                text_info["date"] = str(item[key])
                break

        # 根据平台提取特定文本数据
        if platform == "xhs":
            # 小红书格式
            text_info["content"] = item.get("note_desc", "") or item.get("desc", "") or item.get("content", "")
            text_info["title"] = item.get("title", "") or item.get("note_title", "")
            text_info["author"] = item.get("user_name", "") or item.get("author", "")
            
            # 提取评论
            if "comments" in item and isinstance(item["comments"], list):
                for comment in item["comments"]:
                    if isinstance(comment, dict):
                        comment_text = comment.get("content", "") or comment.get("comment", "")
                        if comment_text:
                            text_info["comments"].append(comment_text)
                    elif isinstance(comment, str):
                        text_info["comments"].append(comment)
        
        elif platform == "douyin":
            # 抖音格式
            text_info["content"] = item.get("desc", "") or item.get("content", "") or item.get("description", "")
            text_info["title"] = item.get("title", "")
            text_info["author"] = item.get("author", "") or item.get("nickname", "")
            
            # 提取评论
            if "comments" in item and isinstance(item["comments"], list):
                for comment in item["comments"]:
                    if isinstance(comment, dict):
                        comment_text = comment.get("text", "") or comment.get("content", "")
                        if comment_text:
                            text_info["comments"].append(comment_text)
                    elif isinstance(comment, str):
                        text_info["comments"].append(comment)
        
        elif platform == "weibo":
            # 微博格式
            text_info["content"] = item.get("text", "") or item.get("content", "")
            text_info["title"] = item.get("title", "")
            text_info["author"] = item.get("user", {}).get("screen_name", "") if isinstance(item.get("user"), dict) else ""
            
            # 提取评论
            if "comments" in item and isinstance(item["comments"], list):
                for comment in item["comments"]:
                    if isinstance(comment, dict):
                        comment_text = comment.get("text", "") or comment.get("content", "")
                        if comment_text:
                            text_info["comments"].append(comment_text)
                    elif isinstance(comment, str):
                        text_info["comments"].append(comment)
        
        elif platform == "zhihu":
            # 知乎格式
            text_info["content"] = item.get("content", "") or item.get("excerpt", "")
            text_info["title"] = item.get("title", "")
            text_info["author"] = item.get("author", {}).get("name", "") if isinstance(item.get("author"), dict) else ""
            
            # 提取评论
            if "comments" in item and isinstance(item["comments"], list):
                for comment in item["comments"]:
                    if isinstance(comment, dict):
                        comment_text = comment.get("content", "") or comment.get("text", "")
                        if comment_text:
                            text_info["comments"].append(comment_text)
                    elif isinstance(comment, str):
                        text_info["comments"].append(comment)
        
        else:
            # 通用格式
            text_info["content"] = item.get("content", "") or item.get("text", "") or item.get("desc", "")
            text_info["title"] = item.get("title", "")
            text_info["author"] = item.get("author", "") or item.get("user_name", "")
            
            # 提取评论
            if "comments" in item and isinstance(item["comments"], list):
                for comment in item["comments"]:
                    if isinstance(comment, dict):
                        comment_text = comment.get("content", "") or comment.get("text", "") or comment.get("comment", "")
                        if comment_text:
                            text_info["comments"].append(comment_text)
                    elif isinstance(comment, str):
                        text_info["comments"].append(comment)
        
        # 清洗文本
        text_info["content"] = self.cleaner.clean_text(text_info["content"])
        text_info["title"] = self.cleaner.clean_text(text_info["title"])
        text_info["comments"] = [self.cleaner.clean_text(c) for c in text_info["comments"]]
        
        return text_info
    
    def process_json_file(
        self,
        file_path: Path,
        platform: str,
        include_comments: bool = True
    ) -> Dict[str, Any]:
        """
        处理JSON文件，提取所有数据
        
        Args:
            file_path: JSON文件路径
            platform: 平台代码
            include_comments: 是否包含评论
            
        Returns:
            处理后的数据
        """
        # 加载数据
        items = self.load_json_file(file_path)
        
        if not items:
            logger.warning(f"文件 {file_path} 没有数据")
            return {
                "platform": platform,
                "total_items": 0,
                "texts": [],
                "comments": [],
                "raw_items": []
            }
        
        # 提取文本
        all_texts = []
        all_comments = []
        processed_items = []
        
        for item in items:
            text_info = self.extract_text_from_item(item, platform)
            
            # 添加标题和内容
            if text_info["title"]:
                all_texts.append(text_info["title"])
            if text_info["content"]:
                all_texts.append(text_info["content"])
            
            # 添加评论
            if include_comments and text_info["comments"]:
                all_comments.extend(text_info["comments"])
                
            processed_items.append(text_info)
        
        # 去重
        unique_texts = list(set(all_texts))
        unique_comments = list(set(all_comments))
        
        logger.info(f"处理完成: {len(items)}条数据, {len(unique_texts)}条文本, {len(unique_comments)}条评论")
        
        return {
            "platform": platform,
            "total_items": len(items),
            "texts": unique_texts,
            "comments": unique_comments,
            "all_texts": unique_texts + unique_comments if include_comments else unique_texts,
            "raw_items": processed_items,
            "file_path": str(file_path),
            "processed_at": datetime.now().isoformat()
        }
    
    def process_multiple_files(
        self,
        file_paths: List[Path],
        platform: str,
        include_comments: bool = True
    ) -> Dict[str, Any]:
        """
        处理多个JSON文件
        
        Args:
            file_paths: JSON文件路径列表
            platform: 平台代码
            include_comments: 是否包含评论
            
        Returns:
            合并后的数据
        """
        all_texts = []
        all_comments = []
        all_raw_items = []
        total_items = 0
        
        for file_path in file_paths:
            result = self.process_json_file(file_path, platform, include_comments)
            all_texts.extend(result["texts"])
            all_comments.extend(result["comments"])
            all_raw_items.extend(result.get("raw_items", []))
            total_items += result["total_items"]
        
        # 去重
        unique_texts = list(set(all_texts))
        unique_comments = list(set(all_comments))
        
        return {
            "platform": platform,
            "total_items": total_items,
            "texts": unique_texts,
            "comments": unique_comments,
            "all_texts": unique_texts + unique_comments if include_comments else unique_texts,
            "raw_items": all_raw_items,
            "file_count": len(file_paths),
            "processed_at": datetime.now().isoformat()
        }
    
    def process_cross_platform_files(
        self,
        files_by_platform: Dict[str, List[Path]],
        include_comments: bool = True
    ) -> Dict[str, Any]:
        """
        处理跨平台的多个文件，合并所有平台的数据
        
        Args:
            files_by_platform: 按平台分组的文件路径字典，格式: {platform: [file_paths]}
            include_comments: 是否包含评论
            
        Returns:
            合并后的跨平台数据
        """
        all_texts = []
        all_comments = []
        all_raw_items = []
        total_items = 0
        platform_stats = {}
        
        for platform, file_paths in files_by_platform.items():
            platform_texts = []
            platform_comments = []
            platform_raw_items = []
            platform_items = 0
            
            for file_path in file_paths:
                result = self.process_json_file(file_path, platform, include_comments)
                platform_texts.extend(result["texts"])
                platform_comments.extend(result["comments"])
                platform_raw_items.extend(result.get("raw_items", []))
                platform_items += result["total_items"]
            
            # 去重
            unique_p_texts = list(set(platform_texts))
            unique_p_comments = list(set(platform_comments))
            
            platform_stats[platform] = {
                "total_items": platform_items,
                "texts_count": len(unique_p_texts),
                "comments_count": len(unique_p_comments),
                "file_count": len(file_paths)
            }
            
            all_texts.extend(platform_texts)
            all_comments.extend(platform_comments)
            all_raw_items.extend(platform_raw_items)
            total_items += platform_items
        
        # 最终去重
        unique_texts = list(set(all_texts))
        unique_comments = list(set(all_comments))
        
        return {
            "platforms": list(files_by_platform.keys()),
            "total_items": total_items,
            "texts": unique_texts,
            "comments": unique_comments,
            "all_texts": unique_texts + unique_comments if include_comments else unique_texts,
            "raw_items": all_raw_items,
            "platform_stats": platform_stats,
            "file_count": sum(len(files) for files in files_by_platform.values()),
            "processed_at": datetime.now().isoformat()
        }


# 创建全局实例
data_processor = DataProcessor()



