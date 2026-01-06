"""
数据展示Web界面API
"""
from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

router = APIRouter()

# 模板目录
templates_dir = project_root / "templates"
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))


@router.get("/data", response_class=HTMLResponse)
async def data_display_ui(
    request: Request,
    brand_id: Optional[int] = Query(None),
    platform: Optional[str] = Query(None),
    page: int = Query(1, ge=1)
):
    """数据展示界面"""
    return templates.TemplateResponse("data_display.html", {
        "request": request,
        "brand_id": brand_id,
        "platform": platform,
        "page": page
    })


@router.get("/brands/page", response_class=HTMLResponse)
@router.get("/brands/ui", response_class=HTMLResponse)
async def brands_list_ui(request: Request):
    """品牌列表界面 - HTML页面路由"""
    return templates.TemplateResponse("brands_list.html", {
        "request": request
    })





