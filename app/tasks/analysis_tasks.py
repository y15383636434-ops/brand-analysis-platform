"""
分析任务Celery任务
"""
from celery import Task
from loguru import logger
from sqlalchemy.orm import Session

from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal, get_mongodb
from app.models.analysis_task import AnalysisTask
from app.models.crawl_task import TaskStatus
from app.services.ai_service import ai_service


@celery_app.task(bind=True, name="analyze_brand_task")
def analyze_brand_task(self: Task, analysis_task_id: int):
    """
    分析品牌任务
    
    Args:
        analysis_task_id: 分析任务ID
    """
    db: Session = SessionLocal()
    
    try:
        # 获取分析任务
        task = db.query(AnalysisTask).filter(AnalysisTask.id == analysis_task_id).first()
        if not task:
            logger.error(f"分析任务不存在: {analysis_task_id}")
            return {"error": "分析任务不存在"}
        
        # 更新任务状态为处理中
        task.status = TaskStatus.RUNNING
        task.celery_task_id = self.request.id
        db.commit()
        
        logger.info(f"开始分析任务: {analysis_task_id}, 品牌ID: {task.brand_id}")
        
        # 从MongoDB获取爬取的数据
        mongodb = get_mongodb()
        crawl_data = list(mongodb.raw_data.find({
            "brand_id": task.brand_id,
            "platform": {"$exists": True}
        }))
        
        if not crawl_data:
            logger.warning(f"品牌 {task.brand_id} 没有爬取数据")
            task.status = TaskStatus.FAILED
            task.error_message = "没有可分析的数据"
            db.commit()
            return {"error": "没有可分析的数据"}
        
        # 提取文本数据
        texts = []
        for item in crawl_data:
            # 提取标题、内容、评论等文本
            if "title" in item:
                texts.append(item["title"])
            if "content" in item:
                texts.append(item["content"])
            if "comments" in item and isinstance(item["comments"], list):
                for comment in item["comments"]:
                    if isinstance(comment, dict) and "content" in comment:
                        texts.append(comment["content"])
                    elif isinstance(comment, str):
                        texts.append(comment)
        
        if not texts:
            logger.warning(f"品牌 {task.brand_id} 没有可分析的文本数据")
            task.status = TaskStatus.FAILED
            task.error_message = "没有可分析的文本数据"
            db.commit()
            return {"error": "没有可分析的文本数据"}
        
        logger.info(f"提取到 {len(texts)} 条文本数据")
        
        # 执行分析
        analysis_result = {}
        
        # 1. 情感分析
        if task.include_sentiment:
            logger.info("执行情感分析...")
            sentiment_result = ai_service.batch_analyze_sentiment(texts)
            analysis_result["sentiment"] = sentiment_result
        
        # 2. 关键词提取
        if task.include_keywords:
            logger.info("执行关键词提取...")
            # 合并所有文本
            all_text = " ".join(texts)
            keywords = ai_service.extract_keywords(all_text, top_k=20, with_weight=True)
            analysis_result["keywords"] = keywords
        
        # 3. 文本统计
        logger.info("执行文本统计分析...")
        text_stats = ai_service.analyze_text_statistics(texts)
        analysis_result["text_statistics"] = text_stats
        
        # 4. LLM深度分析
        if task.include_insights:
            logger.info("执行LLM深度分析...")
            try:
                # 准备数据摘要
                data_summary = {
                    "total_count": len(texts),
                    "sentiment_distribution": analysis_result.get("sentiment", {}).get("distribution", {}),
                    "avg_sentiment_score": analysis_result.get("sentiment", {}).get("avg_score", 0.5),
                    "keywords": analysis_result.get("keywords", [])
                }
                
                # 获取品牌名称
                from app.models.brand import Brand
                brand = db.query(Brand).filter(Brand.id == task.brand_id).first()
                brand_name = brand.name if brand else f"品牌{task.brand_id}"
                
                # 调用LLM分析
                import asyncio
                llm_result = asyncio.run(
                    ai_service.analyze_with_llm(
                        brand_name=brand_name,
                        data_summary=data_summary,
                        analysis_type=task.analysis_type
                    )
                )
                analysis_result["llm_insights"] = llm_result
            except Exception as e:
                logger.error(f"LLM分析失败: {e}")
                analysis_result["llm_insights"] = {
                    "error": str(e),
                    "message": "LLM分析失败，请检查API配置"
                }
        
        # 保存分析结果到MongoDB
        result_doc = {
            "analysis_task_id": analysis_task_id,
            "brand_id": task.brand_id,
            "analysis_type": task.analysis_type,
            "result": analysis_result,
            "created_at": task.created_at.isoformat() if task.created_at else None
        }
        
        mongodb.analysis_results.insert_one(result_doc)
        logger.info(f"分析结果已保存到MongoDB: {analysis_task_id}")
        
        # 更新任务状态为完成
        task.status = TaskStatus.COMPLETED
        db.commit()
        
        logger.info(f"分析任务完成: {analysis_task_id}")
        
        return {
            "analysis_task_id": analysis_task_id,
            "status": "completed",
            "result_summary": {
                "total_texts": len(texts),
                "has_sentiment": "sentiment" in analysis_result,
                "has_keywords": "keywords" in analysis_result,
                "has_insights": "llm_insights" in analysis_result
            }
        }
        
    except Exception as e:
        logger.error(f"分析任务失败: {e}", exc_info=True)
        
        # 更新任务状态为失败
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            db.commit()
        
        return {"error": str(e)}
    
    finally:
        db.close()

