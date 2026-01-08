"""
AI分析服务
提供情感分析、关键词提取、主题分析、LLM深度分析等功能
"""
from typing import List, Dict, Optional, Any
from collections import Counter
import jieba
import jieba.analyse
from snownlp import SnowNLP
from loguru import logger

from config import settings


class AIService:
    """AI分析服务"""
    
    def __init__(self):
        """初始化AI服务"""
        # 初始化jieba
        jieba.initialize()
        logger.info("AI分析服务初始化完成")
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        情感分析
        
        Args:
            text: 待分析文本
            
        Returns:
            情感分析结果，包含：
            - sentiment: 情感倾向（positive/negative/neutral）
            - score: 情感分数（0-1，越接近1越正面）
        """
        try:
            s = SnowNLP(text)
            score = s.sentiments
            
            # 判断情感倾向
            if score > 0.6:
                sentiment = "positive"
            elif score < 0.4:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            return {
                "sentiment": sentiment,
                "score": round(score, 4),
                "text_length": len(text)
            }
        except Exception as e:
            logger.error(f"情感分析失败: {e}")
            return {
                "sentiment": "neutral",
                "score": 0.5,
                "text_length": len(text),
                "error": str(e)
            }
    
    def extract_keywords(self, text: str, top_k: int = 10, with_weight: bool = False) -> List[Dict[str, Any]]:
        """
        关键词提取
        
        Args:
            text: 待分析文本
            top_k: 返回前k个关键词
            with_weight: 是否返回权重
            
        Returns:
            关键词列表，每个关键词包含：
            - keyword: 关键词
            - weight: 权重（如果with_weight=True）
        """
        try:
            if with_weight:
                # 使用TF-IDF提取关键词（带权重）
                keywords = jieba.analyse.extract_tags(text, topK=top_k, withWeight=True)
                return [
                    {"keyword": kw, "weight": round(weight, 4)}
                    for kw, weight in keywords
                ]
            else:
                # 只提取关键词
                keywords = jieba.analyse.extract_tags(text, topK=top_k, withWeight=False)
                return [{"keyword": kw} for kw in keywords]
        except Exception as e:
            logger.error(f"关键词提取失败: {e}")
            return []
    
    def analyze_text_statistics(self, texts: List[str]) -> Dict[str, Any]:
        """
        文本统计分析
        
        Args:
            texts: 文本列表
            
        Returns:
            统计结果，包含：
            - total_count: 总文本数
            - total_length: 总字符数
            - avg_length: 平均字符数
            - word_frequency: 词频统计
        """
        try:
            total_count = len(texts)
            total_length = sum(len(text) for text in texts)
            avg_length = total_length / total_count if total_count > 0 else 0
            
            # 词频统计
            all_words = []
            for text in texts:
                words = jieba.cut(text)
                all_words.extend([w for w in words if len(w.strip()) > 1])
            
            word_freq = Counter(all_words)
            top_words = word_freq.most_common(20)
            
            return {
                "total_count": total_count,
                "total_length": total_length,
                "avg_length": round(avg_length, 2),
                "word_frequency": [
                    {"word": word, "count": count}
                    for word, count in top_words
                ]
            }
        except Exception as e:
            logger.error(f"文本统计分析失败: {e}")
            return {
                "total_count": len(texts),
                "total_length": 0,
                "avg_length": 0,
                "word_frequency": [],
                "error": str(e)
            }
    
    def batch_analyze_sentiment(self, texts: List[str]) -> Dict[str, Any]:
        """
        批量情感分析
        
        Args:
            texts: 文本列表
            
        Returns:
            批量分析结果，包含：
            - total: 总文本数
            - positive_count: 正面数量
            - negative_count: 负面数量
            - neutral_count: 中性数量
            - avg_score: 平均情感分数
            - distribution: 情感分布
        """
        try:
            results = [self.analyze_sentiment(text) for text in texts]
            
            total = len(results)
            positive_count = sum(1 for r in results if r["sentiment"] == "positive")
            negative_count = sum(1 for r in results if r["sentiment"] == "negative")
            neutral_count = sum(1 for r in results if r["sentiment"] == "neutral")
            avg_score = sum(r["score"] for r in results) / total if total > 0 else 0.5
            
            return {
                "total": total,
                "positive_count": positive_count,
                "negative_count": negative_count,
                "neutral_count": neutral_count,
                "avg_score": round(avg_score, 4),
                "distribution": {
                    "positive": round(positive_count / total * 100, 2) if total > 0 else 0,
                    "negative": round(negative_count / total * 100, 2) if total > 0 else 0,
                    "neutral": round(neutral_count / total * 100, 2) if total > 0 else 0
                }
            }
        except Exception as e:
            logger.error(f"批量情感分析失败: {e}")
            return {
                "total": len(texts),
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": len(texts),
                "avg_score": 0.5,
                "distribution": {},
                "error": str(e)
            }
    
    def analyze_sentiment_by_platform(
        self,
        texts_by_platform: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        按平台进行情感分析
        
        Args:
            texts_by_platform: 按平台分组的文本字典，格式: {"xhs": [...], "douyin": [...]}
            
        Returns:
            按平台的情感分析结果
        """
        try:
            platform_results = {}
            for platform, texts in texts_by_platform.items():
                if texts:
                    platform_results[platform] = self.batch_analyze_sentiment(texts)
                else:
                    platform_results[platform] = {
                        "total": 0,
                        "positive_count": 0,
                        "negative_count": 0,
                        "neutral_count": 0,
                        "avg_score": 0.5,
                        "distribution": {"positive": 0, "negative": 0, "neutral": 0}
                    }
            return platform_results
        except Exception as e:
            logger.error(f"按平台情感分析失败: {e}")
            return {}
    
    def analyze_sentiment_by_time(
        self,
        texts_with_dates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        按时间进行情感分析
        
        Args:
            texts_with_dates: 带日期的文本列表，格式: [{"text": "...", "date": "2024-01-01"}, ...]
            
        Returns:
            按时间分布的情感分析结果
        """
        try:
            from collections import defaultdict
            from datetime import datetime
            
            # 按日期分组
            texts_by_date = defaultdict(list)
            for item in texts_with_dates:
                date_str = item.get("date")
                if date_str:
                    # 标准化日期格式（只保留日期部分）
                    try:
                        if isinstance(date_str, str):
                            # 尝试解析日期
                            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                            date_key = dt.strftime("%Y-%m-%d")
                        else:
                            date_key = str(date_str)[:10]
                        texts_by_date[date_key].append(item["text"])
                    except:
                        # 如果日期解析失败，使用原始字符串的前10个字符
                        date_key = str(date_str)[:10] if date_str else "unknown"
                        texts_by_date[date_key].append(item["text"])
            
            # 对每个日期进行情感分析
            time_distribution = []
            for date_key in sorted(texts_by_date.keys()):
                texts = texts_by_date[date_key]
                sentiment_result = self.batch_analyze_sentiment(texts)
                time_distribution.append({
                    "date": date_key,
                    "positive": sentiment_result["distribution"].get("positive", 0),
                    "negative": sentiment_result["distribution"].get("negative", 0),
                    "neutral": sentiment_result["distribution"].get("neutral", 0),
                    "total": sentiment_result["total"]
                })
            
            return {
                "distribution": time_distribution,
                "total_days": len(time_distribution)
            }
        except Exception as e:
            logger.error(f"按时间情感分析失败: {e}")
            return {"distribution": [], "total_days": 0, "error": str(e)}
    
    def extract_topics(self, texts: List[str], num_topics: int = 5) -> List[Dict[str, Any]]:
        """
        主题提取（使用关键词聚类模拟主题）
        
        Args:
            texts: 文本列表
            num_topics: 主题数量
            
        Returns:
            主题列表，每个主题包含：
            - topic: 主题名称（关键词）
            - weight: 权重
            - keywords: 相关关键词
            - sample_count: 样本数量
        """
        try:
            # 合并所有文本
            all_text = " ".join(texts)
            
            # 提取更多关键词作为主题候选
            keywords = jieba.analyse.extract_tags(all_text, topK=num_topics * 3, withWeight=True)
            
            # 对每个关键词，分析包含该关键词的文本
            topics = []
            for keyword, weight in keywords[:num_topics]:
                # 统计包含该关键词的文本数量
                sample_count = sum(1 for text in texts if keyword in text)
                
                # 获取相关关键词（包含该关键词的文本中的其他高频词）
                related_texts = [text for text in texts if keyword in text]
                if related_texts:
                    related_text = " ".join(related_texts)
                    related_keywords = jieba.analyse.extract_tags(
                        related_text, topK=5, withWeight=False
                    )
                    # 移除主关键词
                    related_keywords = [kw for kw in related_keywords if kw != keyword]
                else:
                    related_keywords = []
                
                topics.append({
                    "topic": keyword,
                    "weight": round(weight, 4),
                    "keywords": related_keywords[:5],
                    "sample_count": sample_count
                })
            
            return topics
        except Exception as e:
            logger.error(f"主题提取失败: {e}")
            return []
    
    def analyze_top_posts(
        self,
        items: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        分析热门帖子（按互动数排序）
        
        Args:
            items: 原始数据项列表
            top_k: 返回前k个热门帖子
            
        Returns:
            热门帖子列表
        """
        try:
            # 计算互动分数 (点赞 + 评论*2 + 分享*5)
            # 简单的加权计算，评论和分享通常更有价值
            def calculate_score(item):
                likes = item.get("likes", 0) or 0
                comments = item.get("comments_count", 0) or 0
                shares = item.get("shares", 0) or 0
                return likes + comments * 2 + shares * 5
            
            # 排序
            sorted_items = sorted(items, key=calculate_score, reverse=True)
            
            top_posts = []
            for item in sorted_items[:top_k]:
                top_posts.append({
                    "title": item.get("title") or (item.get("content", "")[:30] + "..."),
                    "content": item.get("content", "")[:100] + "...",
                    "platform": item.get("platform", ""),
                    "author": item.get("author", ""),
                    "likes": item.get("likes", 0),
                    "comments_count": item.get("comments_count", 0),
                    "url": item.get("url", ""),
                    "score": calculate_score(item),
                    "sentiment": self.analyze_sentiment(item.get("content", ""))
                })
                
            return top_posts
        except Exception as e:
            logger.error(f"热门帖子分析失败: {e}")
            return []

    async def analyze_with_llm(
        self,
        brand_name: str,
        data_summary: Dict[str, Any],
        analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        使用LLM进行深度分析
        
        Args:
            brand_name: 品牌名称
            data_summary: 数据摘要（包含情感分析、关键词等）
            analysis_type: 分析类型
            
        Returns:
            LLM分析结果 (结构化 JSON)
        """
        try:
            # 构建Prompt
            prompt = self._build_analysis_prompt(brand_name, data_summary, analysis_type)
            
            # 调用LLM
            raw_result = await self._call_llm(prompt)
            
            # 尝试解析JSON
            import json
            import re
            
            # 简单的清洗，提取 ```json ... ``` 内容
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', raw_result)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = raw_result
                
            try:
                result_json = json.loads(json_str)
            except:
                # 如果解析失败，返回原始文本作为 summary
                logger.warning("LLM输出非JSON格式，回退到纯文本")
                result_json = {
                    "summary": raw_result,
                    "pain_points": [],
                    "suggestions": []
                }
            
            return {
                "analysis_type": analysis_type,
                "insights": result_json,
                "model": self._get_llm_model()
            }
        except Exception as e:
            logger.error(f"LLM分析失败: {e}")
            return {
                "analysis_type": analysis_type,
                "insights": {
                    "summary": f"分析失败: {str(e)}",
                    "pain_points": [],
                    "suggestions": []
                },
                "model": None,
                "error": str(e)
            }
    
    def _build_analysis_prompt(
        self,
        brand_name: str,
        data_summary: Dict[str, Any],
        analysis_type: str
    ) -> str:
        """构建分析Prompt"""
        
        base_prompt = f"""作为专业的品牌分析师，请对品牌"{brand_name}"进行深度分析。
请务必以标准的 JSON 格式输出，不要包含 Markdown 格式之外的多余文本。

## 数据摘要
- 数据总量: {data_summary.get('total_count', 0)}条
- 情感分布: 正面{data_summary.get('sentiment_distribution', {}).get('positive', 0)}%, 负面{data_summary.get('sentiment_distribution', {}).get('negative', 0)}%, 中性{data_summary.get('sentiment_distribution', {}).get('neutral', 0)}%
- 平均情感分数: {data_summary.get('avg_sentiment_score', 0.5)} (范围0-1，越高越好)
- 关键词: {', '.join([kw.get('keyword', '') for kw in data_summary.get('keywords', [])[:15]])}

## 输出要求 (JSON格式)
{{
    "summary": "300字以内的总体评价，涵盖品牌形象和市场现状",
    "pain_points": [
        "用户痛点1：详细描述",
        "用户痛点2：详细描述",
        "..."
    ],
    "marketing_suggestions": [
        "营销建议1：针对当前数据的具体建议",
        "营销建议2",
        "..."
    ],
    "market_opportunities": [
        "潜在市场机会1",
        "..."
    ]
}}

请确保所有字段都存在，如果没有相关信息，请根据行业常识进行合理推断。
"""
        return base_prompt
    
    async def _call_llm(self, prompt: str) -> str:
        """调用LLM API"""
        # 优先使用LLM聚合网关（如果配置）
        if settings.LLM_API_KEY and settings.LLM_API_BASE:
            return await self._call_llm_gateway(prompt)
        # 其次使用OpenAI（直接调用）
        elif settings.OPENAI_API_KEY:
            return await self._call_openai(prompt)
        # 再次使用Gemini
        elif settings.GEMINI_API_KEY:
            return await self._call_gemini(prompt)
        # 再次使用Claude
        elif settings.ANTHROPIC_API_KEY:
            return await self._call_claude(prompt)
        # 最后使用本地LLM
        elif settings.LOCAL_LLM_URL:
            return await self._call_local_llm(prompt)
        else:
            logger.warning("未配置LLM API，返回模拟结果")
            return "未配置LLM API，请配置LLM聚合网关、OpenAI、Gemini、Claude或本地LLM服务。"
    
    async def _call_llm_gateway(self, prompt: str) -> str:
        """调用LLM聚合网关（OneAPI/NewAPI）"""
        try:
            from openai import AsyncOpenAI
            
            # 使用聚合网关的Base URL和API Key
            model_name = settings.LLM_MODEL_NAME or "gpt-4o-mini"
            
            client = AsyncOpenAI(
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_API_BASE
            )
            
            logger.info(f"使用LLM聚合网关: {settings.LLM_API_BASE}, 模型: {model_name}")
            
            response = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "你是一位专业的品牌分析师，擅长分析品牌形象、用户反馈和市场趋势。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM聚合网关调用失败: {e}")
            # 如果聚合网关失败，尝试降级到直接调用
            logger.info("尝试降级到直接调用OpenAI...")
            if settings.OPENAI_API_KEY:
                return await self._call_openai(prompt)
            raise
    
    async def _call_openai(self, prompt: str) -> str:
        """调用OpenAI API（直接调用）"""
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL
            )
            
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "你是一位专业的品牌分析师，擅长分析品牌形象、用户反馈和市场趋势。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
            raise
    
    async def _call_gemini(self, prompt: str) -> str:
        """调用Gemini API"""
        try:
            import asyncio
            import google.generativeai as genai
            
            # 配置API密钥
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # 创建模型实例
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            
            # 构建系统提示
            system_prompt = "你是一位专业的品牌分析师，擅长分析品牌形象、用户反馈和市场趋势。"
            full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # 使用asyncio.to_thread包装同步调用（google-generativeai可能不支持原生异步）
            def _generate():
                response = model.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7,
                        max_output_tokens=2000,
                    )
                )
                return response.text
            
            # 在线程池中执行同步调用
            result = await asyncio.to_thread(_generate)
            return result
        except Exception as e:
            logger.error(f"Gemini API调用失败: {e}")
            raise
    
    async def _call_claude(self, prompt: str) -> str:
        """调用Claude API"""
        try:
            from anthropic import AsyncAnthropic
            
            client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            
            message = await client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return message.content[0].text
        except Exception as e:
            logger.error(f"Claude API调用失败: {e}")
            raise
    
    async def _call_local_llm(self, prompt: str) -> str:
        """调用本地LLM"""
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.LOCAL_LLM_URL,
                    json={
                        "model": settings.LOCAL_LLM_MODEL,
                        "prompt": prompt,
                        "max_tokens": 2000
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                return response.json().get("text", "分析完成")
        except Exception as e:
            logger.error(f"本地LLM调用失败: {e}")
            raise
    
    def _get_llm_model(self) -> Optional[str]:
        """获取当前使用的LLM模型"""
        if settings.LLM_API_KEY and settings.LLM_API_BASE:
            model_name = settings.LLM_MODEL_NAME or "gpt-4o-mini"
            return f"Gateway-{model_name}"
        elif settings.OPENAI_API_KEY:
            return f"OpenAI-{settings.OPENAI_MODEL}"
        elif settings.GEMINI_API_KEY:
            return f"Gemini-{settings.GEMINI_MODEL}"
        elif settings.ANTHROPIC_API_KEY:
            return f"Claude-{settings.ANTHROPIC_MODEL}"
        elif settings.LOCAL_LLM_URL:
            return f"Local-{settings.LOCAL_LLM_MODEL}"
        else:
            return None


# 创建全局实例
ai_service = AIService()





