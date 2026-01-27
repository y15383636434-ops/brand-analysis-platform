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
import tempfile
import os
import time
import httpx
import json
import re

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
            data_summary: 数据摘要（包含情感分析、关键词、热门帖子等）
            analysis_type: 分析类型 (comprehensive, marketing_strategy, product_feedback, crisis_detection)
            
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
            # 优化正则：支持 ```json, ```JSON, 或无语言标记的 ```
            json_match = re.search(r'```(?:json|JSON)?\s*([\s\S]*?)\s*```', raw_result)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 如果没有代码块，尝试查找第一个 { 和最后一个 }
                first_brace = raw_result.find('{')
                last_brace = raw_result.rfind('}')
                if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                    json_str = raw_result[first_brace:last_brace+1]
                else:
                    json_str = raw_result
                
            try:
                result_json = json.loads(json_str)
            except:
                # 如果解析失败，返回原始文本作为 summary
                logger.warning(f"LLM输出非JSON格式，回退到纯文本. Raw result prefix: {raw_result[:100] if raw_result else 'EMPTY'}")
                result_json = {
                    "summary": raw_result if raw_result else "分析生成失败或返回内容为空",
                    "market_performance": {
                        "strengths": [],
                        "weaknesses": []
                    },
                    "user_perception": {
                        "positive_points": [],
                        "pain_points": []
                    },
                    "market_opportunities": [],
                    "marketing_suggestions": []
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
        
        # 基础数据展示
        base_data_info = f"""
## 数据摘要
- 数据总量: {data_summary.get('total_count', 0)}条
- 情感分布: 正面{data_summary.get('sentiment_distribution', {}).get('positive', 0)}%, 负面{data_summary.get('sentiment_distribution', {}).get('negative', 0)}%, 中性{data_summary.get('sentiment_distribution', {}).get('neutral', 0)}%
- 平均情感分数: {data_summary.get('avg_sentiment_score', 0.5)} (范围0-1，越高越好)
- 关键词: {', '.join([kw.get('keyword', '') for kw in data_summary.get('keywords', [])[:20]])}
"""

        # 添加热门帖子信息 (如果有)
        top_posts = data_summary.get('top_posts', [])
        if top_posts:
            base_data_info += "\n## 热门互动内容 (Top 5)\n"
            for i, post in enumerate(top_posts[:5]):
                title = post.get('title', '无标题')
                score = post.get('score', 0)
                content = post.get('content', '')[:50] + "..."
                base_data_info += f"{i+1}. [{title}] (互动分:{score}): {content}\n"

        # 根据不同分析类型构建特定指令
        if analysis_type == 'marketing_strategy':
            specific_instructions = """
## 输出要求 (JSON格式)
{
    "summary": "针对营销策略的总体评估（300字以内）",
    "channel_performance": {
        "effective_channels": ["表现好的渠道/内容类型"],
        "underperforming_areas": ["表现不佳的领域"]
    },
    "content_strategy": {
        "high_engagement_topics": ["高互动话题1", "高互动话题2"],
        "suggested_content_direction": ["建议内容方向1", "建议内容方向2"]
    },
    "audience_insights": {
        "user_interests": ["用户感兴趣的点"],
        "engagement_drivers": ["驱动互动的因素"]
    },
    "marketing_suggestions": [
        "具体营销建议1",
        "具体营销建议2",
        "..."
    ]
}
"""
        elif analysis_type == 'product_feedback':
            specific_instructions = """
## 输出要求 (JSON格式)
{
    "summary": "针对产品反馈的总体评估（300字以内）",
    "product_perception": {
        "pros": ["用户称赞的功能/特点1", "用户称赞的功能/特点2"],
        "cons": ["用户抱怨的功能/特点1", "用户抱怨的功能/特点2"]
    },
    "user_scenarios": [
        "用户使用场景1",
        "用户使用场景2"
    ],
    "improvement_suggestions": [
        "产品改进建议1",
        "产品改进建议2"
    ],
    "feature_requests": [
        "用户期望的功能1",
        "..."
    ]
}
"""
        elif analysis_type == 'crisis_detection':
            specific_instructions = """
## 输出要求 (JSON格式)
{
    "summary": "舆情风险总体评估（300字以内），判断当前风险等级",
    "risk_analysis": {
        "risk_level": "High/Medium/Low",
        "negative_topics": ["负面话题1", "负面话题2"],
        "triggers": ["引发负面的原因1", "引发负面的原因2"]
    },
    "sentiment_trend": {
        "trend_description": "情感变化趋势描述",
        "key_turning_points": ["关键转折点或事件"]
    },
    "response_suggestions": [
        "公关应对建议1",
        "公关应对建议2"
    ]
}
"""
        else:  # comprehensive (default)
            specific_instructions = """
## 输出要求 (JSON格式)
{
    "summary": "总体评价（300字以内），涵盖品牌目前的市场表现、用户情感倾向和核心关注点",
    "market_performance": {
        "strengths": ["品牌优势1", "品牌优势2", "..."],
        "weaknesses": ["品牌劣势1", "品牌劣势2", "..."]
    },
    "user_perception": {
        "positive_points": ["用户夸赞点1", "用户夸赞点2"],
        "pain_points": ["用户痛点/吐槽点1", "用户痛点2"]
    },
    "content_strategy": {
        "engaging_topics": ["高互动话题/内容类型"],
        "content_recommendations": ["内容创作建议"]
    },
    "market_opportunities": [
        "潜在市场机会1",
        "..."
    ],
    "marketing_suggestions": [
        "营销策略建议1",
        "..."
    ]
}
"""

        final_prompt = f"""作为专业的品牌分析师，请对品牌"{brand_name}"进行{analysis_type}类型的深度分析。
请务必以标准的 JSON 格式输出，不要包含 Markdown 格式之外的多余文本。

{base_data_info}

{specific_instructions}

请确保分析深入且具体，不要使用通用套话。请结合提供的关键词、情感分布和热门内容进行推断。
"""
        return final_prompt
    
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
                max_tokens=4000,
                timeout=60.0  # 添加60秒超时设置
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
                max_tokens=2000,
                timeout=60.0  # 添加60秒超时设置
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
                        max_output_tokens=4000,
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
                max_tokens=4000,
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
                        "max_tokens": 4000
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

    async def analyze_image_sequence(self, image_paths: List[str], prompt: str = None) -> Dict[str, Any]:
        """分析图片序列（用于图文笔记）"""
        try:
            import base64
            import cv2
            import numpy as np
            from openai import AsyncOpenAI
            
            if not image_paths:
                return {"success": False, "error": "图片列表为空"}
                
            # 读取图片并转base64
            base64_frames = []
            # 限制图片数量，避免API报错 (例如 max allowed 16)
            # 将限制降低到 5 张，并压缩图片
            limit_count = 5

            logger.info(f"开始处理图片序列，共 {len(image_paths)} 张，选取前 {limit_count} 张处理")
            
            # 使用均匀采样策略，而不是简单的 [:limit_count]
            selected_paths = []
            if len(image_paths) <= limit_count:
                selected_paths = image_paths
            else:
                # 总是保留第一张和最后一张
                step = (len(image_paths) - 1) / (limit_count - 1)
                selected_indices = [int(i * step) for i in range(limit_count)]
                selected_indices = sorted(list(set(selected_indices))) # 去重并排序
                selected_paths = [image_paths[i] for i in selected_indices]
            
            for img_path in selected_paths:
                if os.path.exists(img_path):
                    try:
                        # 使用 cv2 读取以支持图片压缩
                        # 注意：Windows路径包含中文时 cv2.imread 可能失败，使用 imdecode
                        img_array = np.fromfile(img_path, np.uint8)
                        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                        
                        if img is None:
                            logger.warning(f"无法读取图片: {img_path}")
                            continue
                            
                        # 调整尺寸以减少 Token 消耗 (最大边长 1024)
                        h, w = img.shape[:2]
                        max_size = 1024
                        if max(h, w) > max_size:
                            scale = max_size / max(h, w)
                            img = cv2.resize(img, (int(w * scale), int(h * scale)))
                        
                        # 压缩质量 80
                        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
                        _, buffer = cv2.imencode(".jpg", img, encode_param)
                        base64_frames.append(base64.b64encode(buffer).decode("utf-8"))
                        
                    except Exception as img_err:
                        logger.warning(f"处理图片失败 {img_path}: {img_err}")
                        # Fallback to direct read if cv2 fails
                        with open(img_path, "rb") as f:
                            base64_frames.append(base64.b64encode(f.read()).decode("utf-8"))
            
            if not base64_frames:
                return {"success": False, "error": "未能读取到有效图片"}

            logger.info(f"图片处理完成，有效图片 {len(base64_frames)} 张，准备调用 LLM")

            # 检查配置
            if not (settings.LLM_API_KEY and settings.LLM_API_BASE):
                 return {"success": False, "error": "未配置 LLM_API_KEY/LLM_API_BASE，无法分析图片"}

            # 调用 OpenAI 兼容接口
            client = AsyncOpenAI(
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_API_BASE
            )
            
            if not prompt:
                # 稍微修改一下提示词以适应图片
                prompt = """
                请详细分析这一系列图片的内容（这是一篇图文笔记的图片）。包含以下几个方面：
                1. 图片的主要画面描述（发生了什么，场景，人物等）。
                2. 图片中的文字信息（如果可见，非常重要）。
                3. 整体的情感倾向和氛围。
                4. 总结内容的核心主题。
                
                请以 JSON 格式输出，包含以下字段：
                - summary: 内容综述
                - visual_description: 视觉画面描述
                - text_content: 图片中的文字内容提取
                - sentiment: 情感分析
                - key_information: 关键信息提取
                """

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        *map(lambda x: {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{x}"}}, base64_frames),
                    ],
                }
            ]

            model_name = settings.LLM_MODEL_NAME or "gpt-4o-mini"
            logger.info(f"正在调用 LLM ({model_name}) 分析图片序列...")

            response = await client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=2000,
                temperature=0.7
            )
            
            result_text = response.choices[0].message.content
            return self._parse_video_analysis_result(result_text, f"Image-Sequence ({model_name})")

        except Exception as e:
            logger.error(f"图片序列分析失败: {e}")
            return {"success": False, "error": str(e)}

    async def analyze_video_content(self, video_source: str, prompt: str = None) -> Dict[str, Any]:
        """
        分析视频内容（包括画面和语音）
        支持两种模式：
        1. Gemini Native: 使用 Google File API 上传视频分析 (需要 GEMINI_API_KEY)
        2. OpenAI Compatible: 使用抽帧 + GPT-4o-Vision 分析 (需要 LLM_API_KEY)

        Args:
            video_source: 视频URL或本地路径
            prompt: 分析提示词

        Returns:
            分析结果
        """
        # 模式选择逻辑
        if settings.GEMINI_API_KEY:
            return await self._analyze_video_with_gemini(video_source, prompt)
        elif settings.LLM_API_KEY and settings.LLM_API_BASE:
            return await self._analyze_video_with_openai_compatible(video_source, prompt)
        else:
            return {
                "success": False,
                "error": "未配置 AI API Key。请配置 GEMINI_API_KEY (推荐) 或 LLM_API_KEY/LLM_API_BASE。"
            }

    def _get_common_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.douyin.com/",
        }

    async def _analyze_video_with_gemini(self, video_source: str, prompt: str = None) -> Dict[str, Any]:
        """使用 Gemini 原生 File API 分析视频"""
        temp_file_path = None
        try:
            import google.generativeai as genai
            import asyncio
            
            # 配置API密钥
            genai.configure(api_key=settings.GEMINI_API_KEY)

            # 1. 获取视频文件
            if video_source.startswith(('http://', 'https://')):
                # 下载视频
                logger.info(f"正在下载视频(Gemini模式): {video_source}")
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                temp_file.close()
                temp_file_path = temp_file.name
                
                async with httpx.AsyncClient(verify=False) as client:
                    # 增加超时时间，视频下载可能较慢
                    # 添加 Headers 解决 403 问题
                    resp = await client.get(
                        video_source, 
                        timeout=300.0, 
                        follow_redirects=True,
                        headers=self._get_common_headers()
                    )
                    if resp.status_code != 200:
                         return {"success": False, "error": f"下载视频失败: HTTP {resp.status_code}"}
                    
                    with open(temp_file_path, "wb") as f:
                        f.write(resp.content)
            else:
                # 本地文件
                temp_file_path = video_source
                if not os.path.exists(temp_file_path):
                     return {"success": False, "error": f"本地视频文件不存在: {temp_file_path}"}

            # 2. 上传到 Gemini
            logger.info(f"正在上传视频到 Gemini: {temp_file_path}")
            
            def _upload_and_wait():
                video_file = genai.upload_file(path=temp_file_path)
                
                # 等待处理完成
                while video_file.state.name == "PROCESSING":
                    time.sleep(2)
                    video_file = genai.get_file(video_file.name)
                
                if video_file.state.name == "FAILED":
                    raise Exception(f"视频处理失败: {video_file.state.name}")
                    
                return video_file

            video_file = await asyncio.to_thread(_upload_and_wait)
            logger.info(f"视频上传完成: {video_file.name}")

            # 3. 生成分析内容
            if not prompt:
                prompt = self._get_default_video_prompt()

            model_name = settings.GEMINI_MODEL or "gemini-1.5-flash"
            model = genai.GenerativeModel(model_name)
            
            logger.info(f"正在使用模型 {model_name} 分析视频...")
            
            def _generate():
                response = model.generate_content(
                    [video_file, prompt],
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7
                    )
                )
                return response.text

            result_text = await asyncio.to_thread(_generate)
            
            return self._parse_video_analysis_result(result_text, model_name)

        except Exception as e:
            logger.error(f"Gemini视频分析失败: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if temp_file_path and video_source.startswith(('http://', 'https://')):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass

    async def _analyze_video_with_openai_compatible(self, video_source: str, prompt: str = None) -> Dict[str, Any]:
        """使用 OpenAI 兼容接口 (Vision) 分析视频 - 采用均匀抽帧策略"""
        temp_file_path = None
        try:
            import cv2
            import base64
            import asyncio
            from openai import AsyncOpenAI

            # 1. 下载视频
            if video_source.startswith(('http://', 'https://')):
                logger.info(f"正在下载视频(OpenAI兼容模式): {video_source}")
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                temp_file.close()
                temp_file_path = temp_file.name
                
                async with httpx.AsyncClient(verify=False) as client:
                    resp = await client.get(
                        video_source, 
                        timeout=300.0, 
                        follow_redirects=True,
                        headers=self._get_common_headers()
                    )
                    if resp.status_code != 200:
                         return {"success": False, "error": f"下载视频失败: HTTP {resp.status_code}"}
                    
                    with open(temp_file_path, "wb") as f:
                        f.write(resp.content)
            else:
                temp_file_path = video_source
                if not os.path.exists(temp_file_path):
                     return {"success": False, "error": f"本地视频文件不存在: {temp_file_path}"}

            # 2. 均匀抽帧 (高密度模式)
            logger.info(f"正在对视频进行高密度抽帧处理: {temp_file_path}")
            
            def _extract_frames(video_path, max_frames=8): # 降低到8帧，避免 Error code: 500 - too many images
                cap = cv2.VideoCapture(video_path)
                if not cap.isOpened():
                    raise Exception("无法打开视频文件")
                
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                if total_frames <= 0:
                    # 尝试读取一些帧来估算或直接按顺序读取
                    total_frames = 1000 # Fallback
                
                frames = []
                # 计算步长，确保均匀覆盖整个视频
                # 即使视频很短，也尽量多采几帧；如果视频很长，则均匀稀疏采样
                step = max(1, total_frames // max_frames)
                
                for i in range(max_frames):
                    frame_idx = i * step
                    if frame_idx >= total_frames:
                        break
                        
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                    ret, frame = cap.read()
                    if ret:
                        # 调整尺寸以减少 Token 消耗 (例如最大边长 512)
                        h, w = frame.shape[:2]
                        if max(h, w) > 512:
                            scale = 512 / max(h, w)
                            frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
                        
                        _, buffer = cv2.imencode(".jpg", frame)
                        base64_frame = base64.b64encode(buffer).decode("utf-8")
                        frames.append(base64_frame)
                    else:
                        break
                
                cap.release()
                return frames

            # 在线程池中运行抽帧，避免阻塞
            try:
                base64_frames = await asyncio.to_thread(_extract_frames, temp_file_path)
            except ImportError:
                return {"success": False, "error": "未安装 opencv-python-headless，无法进行视频抽帧。请运行 `pip install opencv-python-headless`"}
            except Exception as e:
                return {"success": False, "error": f"视频抽帧失败: {str(e)}"}

            if not base64_frames:
                return {"success": False, "error": "未能提取到视频帧"}

            logger.info(f"抽帧完成，共提取 {len(base64_frames)} 帧")

            # 3. 调用 OpenAI 兼容接口
            client = AsyncOpenAI(
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_API_BASE
            )
            
            if not prompt:
                prompt = self._get_default_video_prompt()

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        *map(lambda x: {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{x}"}}, base64_frames),
                    ],
                }
            ]

            model_name = settings.LLM_MODEL_NAME or "gpt-4o-mini" # 确保模型支持 Vision
            logger.info(f"正在调用 LLM ({model_name}) 分析视频帧...")

            response = await client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=2000,
                temperature=0.7
            )
            
            result_text = response.choices[0].message.content
            return self._parse_video_analysis_result(result_text, f"OpenAI-Compatible ({model_name})")

        except Exception as e:
            logger.error(f"OpenAI兼容模式视频分析失败: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if temp_file_path and video_source.startswith(('http://', 'https://')):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass

    def _get_default_video_prompt(self) -> str:
        return """
        请详细分析这个视频的内容（这是一系列从视频中均匀抽取的关键帧）。包含以下几个方面：
        1. 视频的主要画面描述（发生了什么，场景，人物等）。
        2. 视频中的文字信息（如果可见）。
        3. 视频的情感倾向和氛围。
        4. 总结视频的核心主题。
        
        请以 JSON 格式输出，包含以下字段：
        - summary: 视频内容综述
        - visual_description: 视觉画面描述
        - audio_content: 语音/音频内容摘要 (如果无法获取音频，请根据画面推测或留空)
        - sentiment: 情感分析
        - key_information: 关键信息提取
        """

    def _parse_video_analysis_result(self, result_text: str, model_name: str) -> Dict[str, Any]:
        """解析 LLM 返回的 JSON 结果"""
        import json
        import re
        
        analysis_data = {"raw_text": result_text}
        
        # 尝试提取 JSON
        json_match = re.search(r'```(?:json|JSON)?\s*([\s\S]*?)\s*```', result_text)
        json_str = ""
        if json_match:
            json_str = json_match.group(1)
        else:
            first_brace = result_text.find('{')
            last_brace = result_text.rfind('}')
            if first_brace != -1 and last_brace != -1:
                json_str = result_text[first_brace:last_brace+1]
        
        if json_str:
            try:
                analysis_data = json.loads(json_str)
            except:
                pass

        return {
            "success": True,
            "data": analysis_data,
            "model": model_name
        }


# 创建全局实例
ai_service = AIService()





