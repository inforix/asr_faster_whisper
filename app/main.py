"""
海螺智能语音交互助手 - 后端主应用
基于FastAPI + Faster-Whisper + Coqui TTS
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from app.api.tts import tts_router
from app.api.voice import voice_router
from app.api.openai_compat import openai_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.services.tts.tts_service import tts_service
from app.services.whisper.whisper_service import whisper_service
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

# 配置结构化日志
setup_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理"""
    logger.info("🚀 启动海螺语音助手后端服务")
    
    try:
        # 初始化Whisper服务
        logger.info("初始化Faster-Whisper服务...")
        await whisper_service.initialize()
        
        # 初始化TTS服务
        logger.info("初始化Coqui TTS服务...")
        await tts_service.initialize()
        
        logger.info("✅ 所有服务初始化完成")
        
        yield
        
    except Exception as e:
        logger.error("❌ 服务初始化失败", error=str(e))
        raise
    finally:
        # 清理资源
        logger.info("🔄 清理服务资源...")
        await whisper_service.cleanup()
        await tts_service.cleanup()
        logger.info("✅ 服务清理完成")


# 创建FastAPI应用
app = FastAPI(
    title="海螺智能语音交互助手",
    description="基于Faster-Whisper和Coqui TTS的智能语音交互系统，兼容OpenAI Audio API",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan,
)

# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.add_middleware(
#     TrustedHostMiddleware,
#     allowed_hosts=settings.ALLOWED_HOSTS,
# )

# 添加Prometheus监控端点
if settings.ENABLE_METRICS:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

# 注册路由
app.include_router(voice_router, prefix="/api/voice", tags=["语音识别"])
app.include_router(tts_router, prefix="/api/tts", tags=["语音合成"])
app.include_router(openai_router, tags=["OpenAI 兼容"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "海螺智能语音交互助手",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs" if settings.ENVIRONMENT == "development" else None,
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    try:
        # 检查Whisper服务状态
        whisper_status = await whisper_service.get_status()
        
        # 检查TTS服务状态
        tts_status = await tts_service.get_status()
        
        return {
            "status": "healthy",
            "timestamp": structlog.get_logger().info("health_check"),
            "services": {
                "whisper": whisper_status,
                "tts": tts_status,
            },
            "environment": settings.ENVIRONMENT,
        }
    except Exception as e:
        logger.error("健康检查失败", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": structlog.get_logger().info("health_check_failed"),
            }
        )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(
        "未处理的异常",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "内部服务器错误",
            "message": "服务器遇到了一个错误，请稍后重试",
            "timestamp": structlog.get_logger().info("global_exception"),
        }
    )


if __name__ == "__main__":
    import uvicorn

    # 在生产环境中，host应该通过配置文件设置
    host = settings.HOST if settings.is_production else "127.0.0.1"
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level="info",
        access_log=True,
    ) 