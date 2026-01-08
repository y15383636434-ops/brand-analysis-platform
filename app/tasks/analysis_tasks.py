"""
分析任务Celery任务
"""
from celery import Task
from loguru import logger
from sqlalchemy.orm import Session
from datetime import datetime

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
        task.started_at = datetime.now()
        task.progress = 0
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
        
        # 提取文本数据（按平台和时间分组）
        texts = []
        texts_by_platform = {}
        texts_with_dates = []
        raw_items_for_analysis = []  # 用于热门内容分析的原始数据
        
        from app.services.data_processor import data_processor
        
        for item in crawl_data:
            platform = item.get("platform", "unknown")
            
            # 使用 data_processor 统一提取数据（包含互动数据）
            processed_item = data_processor.extract_text_from_item(item, platform)
            
            # 收集原始项用于热门分析
            raw_items_for_analysis.append(processed_item)
            
            # 收集文本用于NLP分析
            text_items = []
            if processed_item["title"]:
                text_items.append(processed_item["title"])
            if processed_item["content"]:
                text_items.append(processed_item["content"])
            if processed_item["comments"]:
                text_items.extend(processed_item["comments"])
            
            # 添加到总文本列表
            texts.extend(text_items)
            
            # 按平台分组
            if platform not in texts_by_platform:
                texts_by_platform[platform] = []
            texts_by_platform[platform].extend(text_items)
            
            # 添加带日期的文本
            publish_time = processed_item.get("date")
            for text_item in text_items:
                texts_with_dates.append({
                    "text": text_item,
                    "date": publish_time,
                    "platform": platform
                })
        
        if not texts:
            logger.warning(f"品牌 {task.brand_id} 没有可分析的文本数据")
            task.status = TaskStatus.FAILED
            task.error_message = "没有可分析的文本数据"
            db.commit()
            return {"error": "没有可分析的文本数据"}
        
        logger.info(f"提取到 {len(texts)} 条文本数据，涉及 {len(texts_by_platform)} 个平台")
        
        # 更新进度：数据准备完成 (10%)
        task.progress = 10
        db.commit()
        
        # 执行分析
        analysis_result = {}
        
        # 计算总步骤数，用于进度计算
        total_steps = 0
        if task.include_sentiment:
            total_steps += 1
        if task.include_keywords:
            total_steps += 1
        if task.include_topics:
            total_steps += 1
        if task.include_insights:
            total_steps += 1
        total_steps += 2  # 文本统计和平台统计
        
        current_step = 0
        base_progress = 10  # 从10%开始
        step_progress = 70 // total_steps if total_steps > 0 else 10  # 70%分配给各个步骤
        
        # 1. 情感分析（整体）
        if task.include_sentiment:
            logger.info("执行整体情感分析...")
            task.progress = base_progress + int(current_step * step_progress)
            db.commit()
            
            sentiment_result = ai_service.batch_analyze_sentiment(texts)
            analysis_result["sentiment"] = sentiment_result
            
            # 按平台的情感分析
            logger.info("执行按平台情感分析...")
            sentiment_by_platform = ai_service.analyze_sentiment_by_platform(texts_by_platform)
            analysis_result["sentiment"]["by_platform"] = sentiment_by_platform
            
            # 按时间的情感分析
            if texts_with_dates:
                logger.info("执行按时间情感分析...")
                sentiment_by_time = ai_service.analyze_sentiment_by_time(texts_with_dates)
                analysis_result["sentiment"]["by_time"] = sentiment_by_time
            
            current_step += 1
        
        # 2. 关键词提取
        if task.include_keywords:
            logger.info("执行关键词提取...")
            task.progress = base_progress + int(current_step * step_progress)
            db.commit()
            
            # 合并所有文本
            all_text = " ".join(texts)
            keywords = ai_service.extract_keywords(all_text, top_k=30, with_weight=True)
            analysis_result["keywords"] = keywords
            
            current_step += 1
        
        # 3. 主题提取
        if task.include_topics:
            logger.info("执行主题提取...")
            task.progress = base_progress + int(current_step * step_progress)
            db.commit()
            
            topics = ai_service.extract_topics(texts, num_topics=5)
            analysis_result["topics"] = topics
            
            current_step += 1
        
        # 4. 文本统计
        logger.info("执行文本统计分析...")
        task.progress = base_progress + int(current_step * step_progress)
        db.commit()
        
        text_stats = ai_service.analyze_text_statistics(texts)
        analysis_result["text_statistics"] = text_stats
        
        current_step += 1
        
        # 5. 平台统计
        task.progress = base_progress + int(current_step * step_progress)
        db.commit()
        
        platform_stats = {}
        for platform, platform_texts in texts_by_platform.items():
            platform_stats[platform] = {
                "total_texts": len(platform_texts),
                "total_chars": sum(len(t) for t in platform_texts)
            }
        analysis_result["platform_statistics"] = platform_stats
        
        current_step += 1
        
        # 6. 热门内容分析 (新增加)
        logger.info("执行热门内容分析...")
        top_posts = ai_service.analyze_top_posts(raw_items_for_analysis, top_k=20)
        analysis_result["top_posts"] = top_posts
        
        # 7. LLM深度分析
        if task.include_insights:
            logger.info("执行LLM深度分析...")
            task.progress = base_progress + int(current_step * step_progress)
            db.commit()
            
            try:
                # 准备数据摘要
                data_summary = {
                    "total_count": len(texts),
                    "sentiment_distribution": analysis_result.get("sentiment", {}).get("distribution", {}),
                    "avg_sentiment_score": analysis_result.get("sentiment", {}).get("avg_score", 0.5),
                    "keywords": analysis_result.get("keywords", []),
                    "top_posts_titles": [p["title"] for p in analysis_result.get("top_posts", [])[:5]]  # 提供热门标题辅助分析
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
            
            current_step += 1
        
        # 更新进度：分析完成，保存结果 (90%)
        task.progress = 90
        db.commit()
        
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
        task.completed_at = datetime.now()
        task.progress = 100
        if task.started_at:
            duration = (task.completed_at - task.started_at).total_seconds()
            task.duration = int(duration)
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
            task.completed_at = datetime.now()
            if task.started_at:
                duration = (task.completed_at - task.started_at).total_seconds()
                task.duration = int(duration)
            db.commit()
        
        return {"error": str(e)}
    
    finally:
        db.close()

