"""
语音识别相关数据模型
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")


class VoiceServiceStatus(BaseModel):
    """语音服务状态模型"""
    status: str = Field(..., description="服务状态")
    service: str = Field(..., description="服务名称")
    message: str = Field(..., description="状态描述")
    whisper_service: Optional[Dict[str, Any]] = Field(None, description="Whisper服务详情")


class FileInfo(BaseModel):
    """文件信息模型"""
    filename: Optional[str] = Field(None, description="文件名")
    content_type: Optional[str] = Field(None, description="内容类型")
    size_bytes: int = Field(..., description="文件大小(字节)")


class ProcessingInfo(BaseModel):
    """处理信息模型"""
    segments: int = Field(..., description="音频段数")
    requested_language: Optional[str] = Field(None, description="请求的语言")
    processing_time: str = Field(..., description="处理时间")


class VoiceRecognitionResponse(BaseModel):
    """语音识别响应模型"""
    success: bool = Field(..., description="识别是否成功")
    text: str = Field(..., description="识别的文本")
    confidence: float = Field(..., description="置信度", ge=0.0, le=1.0)
    language: str = Field(..., description="检测到的语言")
    duration: float = Field(..., description="音频时长(秒)")
    file_info: Optional[FileInfo] = Field(None, description="文件信息")
    processing_info: Optional[ProcessingInfo] = Field(None, description="处理信息") 