"""
数据清洗服务
"""
import re
from typing import Dict, List
from loguru import logger


class DataCleaner:
    """数据清洗类"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        清洗文本数据
        
        Args:
            text: 原始文本
            
        Returns:
            清洗后的文本
        """
        if not text:
            return ""
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除特殊字符（保留中文、英文、数字、基本标点）
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s，。！？、；：""''（）【】]', '', text)
        
        # 去除首尾空白
        text = text.strip()
        
        return text
    
    @staticmethod
    def deduplicate_items(items: List[Dict], key_field: str = "id") -> List[Dict]:
        """
        去重数据项
        
        Args:
            items: 数据项列表
            key_field: 用于去重的字段
            
        Returns:
            去重后的数据列表
        """
        seen = set()
        unique_items = []
        
        for item in items:
            key = item.get(key_field)
            if key and key not in seen:
                seen.add(key)
                unique_items.append(item)
        
        logger.info(f"去重: {len(items)} -> {len(unique_items)}")
        return unique_items
    
    @staticmethod
    def validate_item(item: Dict) -> bool:
        """
        验证数据项
        
        Args:
            item: 数据项字典
            
        Returns:
            是否有效
        """
        # 基本字段检查
        required_fields = ["id", "platform", "content"]
        for field in required_fields:
            if field not in item or not item[field]:
                return False
        
        # 内容长度检查
        content = item.get("content", "")
        if len(content) < 5:  # 内容太短
            return False
        
        return True
    
    @staticmethod
    def clean_crawled_data(data: Dict) -> Dict:
        """
        清洗爬取的数据
        
        Args:
            data: 原始爬取数据
            
        Returns:
            清洗后的数据
        """
        items = data.get("items", [])
        cleaned_items = []
        
        for item in items:
            # 清洗文本字段
            if "content" in item:
                item["content"] = DataCleaner.clean_text(item["content"])
            if "title" in item:
                item["title"] = DataCleaner.clean_text(item["title"])
            
            # 验证数据
            if DataCleaner.validate_item(item):
                cleaned_items.append(item)
        
        # 去重
        cleaned_items = DataCleaner.deduplicate_items(cleaned_items)
        
        data["items"] = cleaned_items
        data["total_items"] = len(cleaned_items)
        
        return data






