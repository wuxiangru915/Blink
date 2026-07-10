"""
FastAPI 应用入口
Blink 后端服务 (v1.1 - 添加日志系统)
"""

import asyncio
import mimetypes
import sys
from pathlib import Path

# 确保 backend 目录在 Python 路径中
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse as _FileResponse
from fastapi.responses import JSONResponse

from app.api.v1.auth import router as auth_router
from app.api.v1.config import router as config_router
from app.api.v1.image import router as image_router
from app.api.v1.rag import router as rag_router
from app.api.v1.workflow import router as workflow_router
from app.core.config import settings
from app.core.db import close_db, init_db
from app.core.logger import app_logger, setup_logging
from app.core.middleware import RequestLoggingMiddleware
from app.core.utils import detect_image_format
from app.graph.utils import close_checkpointer, setup_checkpointer

# 初始化日志系统（在导入其他模块之前）
setup_logging(
    log_level=settings.log_level,
    log_target=settings.log_target,
    log_dir=settings.log_dir,
    json_logs=settings.log_json,
    console_output=settings.log_console,
    pii_anonymize=settings.log_pii_anonymize,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    应用生命周期管理

    启动时：
    - 初始化数据库连接
    - 初始化 LangGraph Checkpointer（创建必要的表）

    关闭时：
    - 关闭数据库连接
    - 关闭 Checkpointer 连接池
    """
    # 启动时执行
    app_logger.info(f"Starting {settings.app_name}...")

    try:
        # 初始化 SQLAlchemy 数据库
        app_logger.info("Initializing database connection...")
        await init_db()
        app_logger.db_connected(database_url=settings.database_url.split("@")[-1])  # 不记录密码

        # 初始化 LangGraph Checkpointer
        app_logger.info("Initializing LangGraph Checkpointer...")
        await setup_checkpointer()

        app_logger.service_started(
            app_name=settings.app_name,
            debug=settings.debug,
            log_level=settings.log_level,
            docs_url="http://localhost:8000/docs",
        )

        # 同时保留控制台输出，方便开发时查看
        app_logger.info(f"{settings.app_name} started successfully!")
        app_logger.info("API docs: http://localhost:8000/docs")
        app_logger.info(f"Log files: {settings.log_dir}/")

    except Exception as e:
        app_logger.error(f"Startup failed: {str(e)}", error=str(e))
        raise

    yield

    # 关闭时执行
    app_logger.info(f"Stopping {settings.app_name}...")

    try:
        await close_checkpointer()
        await close_db()
        app_logger.db_disconnected()
        app_logger.service_stopped(app_name=settings.app_name)
    except Exception as e:
        app_logger.warning(f"Error during shutdown: {str(e)}", error=str(e))


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.app_name,
    description="""
## Blink API

为教育培训公司提供的自动化内容生成工作流服务。

### 核心功能

- **选题生成**: AI 根据主题方向生成多个候选选题
- **文章撰写**: AI 根据选定选题生成技术文章
- **人工审核**: 支持通过/驳回机制，驳回后可重写
- **配图生成**: 自动提取视觉要点并生成配图

### 工作流程

1. 启动工作流，AI 生成候选选题
2. 人工选择一个选题
3. AI 生成文章草稿
4. 人工审核（通过/驳回）
5. 通过后自动生成配图
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# 配置中间件（注意顺序：先添加的后执行）
# 1. 请求日志中间件
app.add_middleware(RequestLoggingMiddleware)

# 2. CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理 - 捕获未处理的异常，返回通用 500 错误，不泄露堆栈
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    app_logger.error("unhandled exception", error=str(exc), exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "服务器内部错误"})


# 注册路由
app.include_router(auth_router, prefix="/api/v1")
app.include_router(workflow_router, prefix="/api/v1")
app.include_router(image_router, prefix="/api/v1")
app.include_router(rag_router, prefix="/api/v1")
app.include_router(config_router, prefix="/api/v1/config")

# 挂载静态文件目录（用于访问生成的图片）
static_dir = Path(__file__).parent.parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)

def _read_file_header(file_path: Path, num_bytes: int = 12) -> bytes:
    """同步读取文件头部字节"""
    with open(file_path, "rb") as f:
        return f.read(num_bytes)


@app.get("/static/images/generated/{filename:path}")
async def serve_generated_image(filename: str):
    """Serve generated images with correct MIME type detection"""
    file_path = static_dir / "images" / "generated" / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    # Detect actual MIME type from file content
    header = await asyncio.to_thread(_read_file_header, file_path)
    fmt = detect_image_format(header)
    media_type_map = {"png": "image/png", "jpg": "image/jpeg", "webp": "image/webp"}
    media_type = media_type_map.get(fmt) or mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    return await asyncio.to_thread(_FileResponse, str(file_path), media_type=media_type)


@app.get("/static/{file_path:path}")
async def serve_static(file_path: str):
    """Serve static files with correct MIME type for images"""
    full_path = static_dir / file_path
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    # For generated images, detect actual MIME type
    if "images/generated" in file_path:
        header = await asyncio.to_thread(_read_file_header, full_path)
        fmt = detect_image_format(header)
        media_type_map = {"png": "image/png", "jpg": "image/jpeg", "webp": "image/webp"}
        media_type = media_type_map.get(fmt) or mimetypes.guess_type(str(full_path))[0] or "application/octet-stream"
    else:
        media_type = mimetypes.guess_type(str(full_path))[0] or "application/octet-stream"
    return await asyncio.to_thread(_FileResponse, str(full_path), media_type=media_type)


@app.get("/")
async def root():
    """根路径 - 优先返回前端页面，无前端时返回健康检查"""
    index_file = static_dir / "dist" / "index.html"
    if index_file.exists():
        from fastapi.responses import FileResponse
        return FileResponse(str(index_file))
    return {"service": settings.app_name, "status": "running", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "service": settings.app_name}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
