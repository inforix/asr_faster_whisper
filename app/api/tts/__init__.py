"""
语音合成API路由
"""

from fastapi import APIRouter

tts_router = APIRouter()


@tts_router.get("/status")
async def get_tts_status():
    """获取语音合成服务状态"""
    return {
        "status": "active",
        "service": "text_to_speech",
        "message": "语音合成服务正常运行"
    }


@tts_router.post("/synthesize")
async def synthesize_text():
    """文本转语音接口"""
    # TODO: 实现语音合成逻辑
    return {
        "message": "语音合成功能开发中",
        "status": "not_implemented"
    } 