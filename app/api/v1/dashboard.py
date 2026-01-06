"""
统一控制台主页面API
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
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


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """统一控制台主页面"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request
    })

