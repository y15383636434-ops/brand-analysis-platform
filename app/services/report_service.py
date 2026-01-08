"""
报表生成服务
提供报表数据准备、图表生成、模板渲染等功能
"""
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import base64
import io
from loguru import logger

from jinja2 import Environment, FileSystemLoader, select_autoescape
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib import rcParams
import numpy as np

from config import settings

# 配置中文字体
try:
    # 尝试使用系统中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
except:
    pass


class ReportService:
    """报表生成服务"""
    
    def __init__(self):
        """初始化报表服务"""
        # 初始化Jinja2模板引擎
        template_dir = settings.REPORT_TEMPLATE_DIR
        template_dir.mkdir(parents=True, exist_ok=True)
        
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # 确保输出目录存在
        settings.REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        logger.info("报表生成服务初始化完成")
    
    def prepare_report_data(
        self,
        brand_name: str,
        analysis_result: Dict[str, Any],
        brand_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        准备报表数据
        
        Args:
            brand_name: 品牌名称
            analysis_result: 分析结果
            brand_info: 品牌信息（可选）
            
        Returns:
            报表数据字典
        """
        report_data = {
            "brand_name": brand_name,
            "brand_info": brand_info or {},
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "analysis_result": analysis_result,
            "summary": self._generate_summary(analysis_result)
        }
        
        return report_data
    
    def _generate_summary(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成报表摘要"""
        summary = {
            "total_texts": analysis_result.get("text_statistics", {}).get("total_count", 0),
            "sentiment_overview": {},
            "top_keywords": [],
            "top_topics": []
        }
        
        # 情感分析摘要
        sentiment = analysis_result.get("sentiment", {})
        if sentiment:
            summary["sentiment_overview"] = {
                "positive": sentiment.get("distribution", {}).get("positive", 0),
                "negative": sentiment.get("distribution", {}).get("negative", 0),
                "neutral": sentiment.get("distribution", {}).get("neutral", 0),
                "avg_score": sentiment.get("avg_score", 0.5)
            }
        
        # 关键词摘要
        keywords = analysis_result.get("keywords", [])
        if keywords:
            summary["top_keywords"] = [
                {"keyword": kw.get("keyword", ""), "weight": kw.get("weight", 0)}
                for kw in keywords[:10]
            ]
        
        # 主题摘要
        topics = analysis_result.get("topics", [])
        if topics:
            summary["top_topics"] = [
                {"topic": t.get("topic", ""), "weight": t.get("weight", 0)}
                for t in topics[:5]
            ]
        
        return summary
    
    def generate_charts(self, analysis_result: Dict[str, Any]) -> Dict[str, str]:
        """
        生成图表（返回base64编码的图片）
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            图表字典，key为图表名称，value为base64编码的图片
        """
        charts = {}
        
        try:
            # 1. 情感分析饼图
            sentiment = analysis_result.get("sentiment", {})
            if sentiment and sentiment.get("distribution"):
                charts["sentiment_pie"] = self._generate_sentiment_pie_chart(sentiment)
            
            # 2. 按平台情感分析柱状图
            sentiment_by_platform = sentiment.get("by_platform", {})
            if sentiment_by_platform:
                charts["sentiment_by_platform"] = self._generate_platform_sentiment_chart(sentiment_by_platform)
            
            # 3. 时间趋势图
            sentiment_by_time = sentiment.get("by_time", {})
            if sentiment_by_time and sentiment_by_time.get("distribution"):
                charts["sentiment_trend"] = self._generate_sentiment_trend_chart(sentiment_by_time)
            
            # 4. 关键词权重图
            keywords = analysis_result.get("keywords", [])
            if keywords:
                charts["keywords_bar"] = self._generate_keywords_chart(keywords[:15])
            
            # 5. 平台数据分布图
            platform_stats = analysis_result.get("platform_statistics", {})
            if platform_stats:
                charts["platform_distribution"] = self._generate_platform_distribution_chart(platform_stats)
            
        except Exception as e:
            logger.error(f"图表生成失败: {e}", exc_info=True)
        
        return charts
    
    def _generate_sentiment_pie_chart(self, sentiment: Dict[str, Any]) -> str:
        """生成情感分析饼图"""
        try:
            distribution = sentiment.get("distribution", {})
            if not distribution:
                return ""
            
            labels = ["正面", "负面", "中性"]
            sizes = [
                distribution.get("positive", 0),
                distribution.get("negative", 0),
                distribution.get("neutral", 0)
            ]
            
            # 如果所有值都为0，返回空字符串
            if sum(sizes) == 0:
                return ""
            
            colors = ['#4CAF50', '#F44336', '#FFC107']
            
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax.set_title('情感分析分布', fontsize=16, fontweight='bold', pad=20)
            
            return self._fig_to_base64(fig)
        except Exception as e:
            logger.error(f"生成情感分析饼图失败: {e}")
            return ""
    
    def _generate_platform_sentiment_chart(self, sentiment_by_platform: Dict[str, Any]) -> str:
        """生成按平台情感分析柱状图"""
        try:
            platforms = list(sentiment_by_platform.keys())
            platform_names = {
                "xhs": "小红书",
                "douyin": "抖音",
                "weibo": "微博",
                "zhihu": "知乎",
                "bilibili": "B站"
            }
            
            positive_data = []
            negative_data = []
            neutral_data = []
            
            for platform in platforms:
                dist = sentiment_by_platform[platform].get("distribution", {})
                positive_data.append(dist.get("positive", 0))
                negative_data.append(dist.get("negative", 0))
                neutral_data.append(dist.get("neutral", 0))
            
            x = np.arange(len(platforms))
            width = 0.25
            
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.bar(x - width, positive_data, width, label='正面', color='#4CAF50')
            ax.bar(x, neutral_data, width, label='中性', color='#FFC107')
            ax.bar(x + width, negative_data, width, label='负面', color='#F44336')
            
            ax.set_xlabel('平台', fontsize=12)
            ax.set_ylabel('比例 (%)', fontsize=12)
            ax.set_title('各平台情感分析对比', fontsize=16, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels([platform_names.get(p, p) for p in platforms])
            ax.legend()
            ax.grid(axis='y', alpha=0.3)
            
            plt.tight_layout()
            return self._fig_to_base64(fig)
        except Exception as e:
            logger.error(f"生成平台情感分析图失败: {e}")
            return ""
    
    def _generate_sentiment_trend_chart(self, sentiment_by_time: Dict[str, Any]) -> str:
        """生成情感趋势图"""
        try:
            distribution = sentiment_by_time.get("distribution", [])
            if not distribution:
                return ""
            
            dates = [item["date"] for item in distribution]
            positive = [item["positive"] for item in distribution]
            negative = [item["negative"] for item in distribution]
            neutral = [item["neutral"] for item in distribution]
            
            fig, ax = plt.subplots(figsize=(14, 6))
            ax.plot(dates, positive, marker='o', label='正面', color='#4CAF50', linewidth=2)
            ax.plot(dates, negative, marker='s', label='负面', color='#F44336', linewidth=2)
            ax.plot(dates, neutral, marker='^', label='中性', color='#FFC107', linewidth=2)
            
            ax.set_xlabel('日期', fontsize=12)
            ax.set_ylabel('比例 (%)', fontsize=12)
            ax.set_title('情感趋势分析', fontsize=16, fontweight='bold')
            ax.legend()
            ax.grid(alpha=0.3)
            
            # 旋转x轴标签
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            return self._fig_to_base64(fig)
        except Exception as e:
            logger.error(f"生成情感趋势图失败: {e}")
            return ""
    
    def _generate_keywords_chart(self, keywords: List[Dict[str, Any]]) -> str:
        """生成关键词权重柱状图"""
        try:
            if not keywords:
                return ""
            
            words = [kw.get("keyword", "") for kw in keywords]
            weights = [kw.get("weight", 0) for kw in keywords]
            
            fig, ax = plt.subplots(figsize=(12, 8))
            y_pos = np.arange(len(words))
            ax.barh(y_pos, weights, color='#2196F3')
            
            ax.set_yticks(y_pos)
            ax.set_yticklabels(words)
            ax.set_xlabel('权重', fontsize=12)
            ax.set_title('关键词权重分析（Top 15）', fontsize=16, fontweight='bold')
            ax.grid(axis='x', alpha=0.3)
            
            plt.tight_layout()
            return self._fig_to_base64(fig)
        except Exception as e:
            logger.error(f"生成关键词图失败: {e}")
            return ""
    
    def _generate_platform_distribution_chart(self, platform_stats: Dict[str, Any]) -> str:
        """生成平台数据分布图"""
        try:
            platforms = list(platform_stats.keys())
            platform_names = {
                "xhs": "小红书",
                "douyin": "抖音",
                "weibo": "微博",
                "zhihu": "知乎",
                "bilibili": "B站"
            }
            
            counts = [platform_stats[p].get("total_texts", 0) for p in platforms]
            
            fig, ax = plt.subplots(figsize=(10, 6))
            colors = ['#2196F3', '#4CAF50', '#FF9800', '#9C27B0', '#F44336']
            ax.bar([platform_names.get(p, p) for p in platforms], counts, color=colors[:len(platforms)])
            
            ax.set_xlabel('平台', fontsize=12)
            ax.set_ylabel('文本数量', fontsize=12)
            ax.set_title('各平台数据分布', fontsize=16, fontweight='bold')
            ax.grid(axis='y', alpha=0.3)
            
            # 添加数值标签
            for i, v in enumerate(counts):
                ax.text(i, v, str(v), ha='center', va='bottom')
            
            plt.tight_layout()
            return self._fig_to_base64(fig)
        except Exception as e:
            logger.error(f"生成平台分布图失败: {e}")
            return ""
    
    def _fig_to_base64(self, fig) -> str:
        """将matplotlib图形转换为base64编码的字符串"""
        try:
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)
            return img_base64
        except Exception as e:
            logger.error(f"图形转base64失败: {e}")
            plt.close(fig)
            return ""
    
    def render_html_report(
        self,
        report_data: Dict[str, Any],
        charts: Dict[str, str],
        template_name: str = "brand_report.html"
    ) -> str:
        """
        渲染HTML报表
        
        Args:
            report_data: 报表数据
            charts: 图表字典
            template_name: 模板名称
            
        Returns:
            HTML字符串
        """
        try:
            template = self.env.get_template(template_name)
            html = template.render(
                data=report_data,
                charts=charts
            )
            return html
        except Exception as e:
            logger.error(f"HTML报表渲染失败: {e}", exc_info=True)
            # 如果模板不存在，返回一个简单的HTML
            return self._generate_simple_html(report_data, charts)
    
    def _generate_simple_html(self, report_data: Dict[str, Any], charts: Dict[str, str]) -> str:
        """生成简单的HTML报表（备用方案）"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{report_data.get('brand_name', '品牌分析报告')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        img {{ max-width: 100%; height: auto; margin: 20px 0; }}
    </style>
</head>
<body>
    <h1>{report_data.get('brand_name', '品牌')}分析报告</h1>
    <p>生成时间: {report_data.get('generated_at', '')}</p>
    <h2>报告摘要</h2>
    <p>总文本数: {report_data.get('summary', {}).get('total_texts', 0)}</p>
    <!-- 这里可以添加更多内容 -->
</body>
</html>
"""
        return html
    
    def save_html_report(self, html: str, filename: str) -> Path:
        """
        保存HTML报表
        
        Args:
            html: HTML内容
            filename: 文件名
            
        Returns:
            文件路径
        """
        file_path = settings.REPORT_OUTPUT_DIR / filename
        file_path.write_text(html, encoding='utf-8')
        logger.info(f"HTML报表已保存: {file_path}")
        return file_path
    
    def html_to_pdf(self, html: str, output_path: Path) -> bool:
        """
        将HTML转换为PDF
        
        Args:
            html: HTML内容
            output_path: 输出PDF路径
            
        Returns:
            是否成功
        """
        try:
            # 尝试使用weasyprint
            try:
                from weasyprint import HTML
                HTML(string=html).write_pdf(output_path)
                logger.info(f"PDF报表已生成: {output_path}")
                return True
            except ImportError:
                logger.warning("weasyprint未安装，尝试使用pdfkit...")
            
            # 尝试使用pdfkit
            try:
                import pdfkit
                pdfkit.from_string(html, str(output_path))
                logger.info(f"PDF报表已生成: {output_path}")
                return True
            except ImportError:
                logger.warning("pdfkit未安装，PDF生成功能不可用")
                return False
            except Exception as e:
                logger.error(f"pdfkit转换失败: {e}")
                return False
        except Exception as e:
            logger.error(f"HTML转PDF失败: {e}", exc_info=True)
            return False


# 创建全局实例
report_service = ReportService()

