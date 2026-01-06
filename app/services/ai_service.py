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
            analysis_type: 分析类型（comprehensive/brand_image/user_feedback/trend）
            
        Returns:
            LLM分析结果
        """
        try:
            # 构建Prompt
            prompt = self._build_analysis_prompt(brand_name, data_summary, analysis_type)
            
            # 调用LLM（根据配置选择OpenAI、Claude或本地LLM）
            result = await self._call_llm(prompt)
            
            return {
                "analysis_type": analysis_type,
                "insights": result,
                "model": self._get_llm_model()
            }
        except Exception as e:
            logger.error(f"LLM分析失败: {e}")
            return {
                "analysis_type": analysis_type,
                "insights": f"分析失败: {str(e)}",
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

## 数据摘要
- 数据总量: {data_summary.get('total_count', 0)}条
- 情感分布: 正面{data_summary.get('sentiment_distribution', {}).get('positive', 0)}%, 负面{data_summary.get('sentiment_distribution', {}).get('negative', 0)}%, 中性{data_summary.get('sentiment_distribution', {}).get('neutral', 0)}%
- 平均情感分数: {data_summary.get('avg_sentiment_score', 0.5)}
- 关键词: {', '.join([kw.get('keyword', '') for kw in data_summary.get('keywords', [])[:10]])}

请提供专业的品牌分析报告，包括：
"""
        
        if analysis_type == "comprehensive":
            prompt = base_prompt + """
1. 品牌形象分析：品牌在用户心中的整体形象
2. 用户反馈分析：用户对品牌的主要评价和关注点
3. 优势分析：品牌的优势和亮点
4. 问题分析：品牌存在的问题和改进建议
5. 趋势预测：品牌未来发展趋势预测
"""
        elif analysis_type == "brand_image":
            prompt = base_prompt + """
1. 品牌形象定位
2. 品牌认知度分析
3. 品牌联想分析
4. 品牌差异化优势
"""
        elif analysis_type == "user_feedback":
            prompt = base_prompt + """
1. 用户满意度分析
2. 主要反馈内容
3. 用户痛点分析
4. 改进建议
"""
        elif analysis_type == "trend":
            prompt = base_prompt + """
1. 品牌热度趋势
2. 话题趋势分析
3. 用户关注度变化
4. 未来趋势预测
"""
        else:
            prompt = base_prompt + "请提供全面的品牌分析。"
        
        return prompt
    
    async def _call_llm(self, prompt: str) -> str:
        """调用LLM API"""
        # 优先使用OpenAI
        if settings.OPENAI_API_KEY:
            return await self._call_openai(prompt)
        # 其次使用Gemini
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
            return "未配置LLM API，请配置OpenAI、Gemini、Claude或本地LLM服务。"
    
    async def _call_openai(self, prompt: str) -> str:
        """调用OpenAI API"""
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
        if settings.OPENAI_API_KEY:
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





