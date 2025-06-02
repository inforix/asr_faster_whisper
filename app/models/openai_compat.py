"""
OpenAI API 兼容性数据模型
"""

from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field


class OpenAITranscriptionRequest(BaseModel):
    """OpenAI 音频转录请求模型"""
    model: str = Field(..., description="使用的模型", example="whisper-1")
    prompt: Optional[str] = Field(None, description="可选的提示文本")
    response_format: Optional[str] = Field("json", description="响应格式", pattern="^(json|text|srt|verbose_json|vtt)$")
    temperature: Optional[float] = Field(0, description="采样温度", ge=0, le=1)
    language: Optional[str] = Field(None, description="输入音频的语言")


class OpenAITranscriptionResponse(BaseModel):
    """OpenAI 音频转录响应模型（JSON格式）"""
    text: str = Field(..., description="转录的文本")


class OpenAIVerboseTranscriptionResponse(BaseModel):
    """OpenAI 详细音频转录响应模型"""
    task: str = Field("transcribe", description="任务类型")
    language: str = Field(..., description="检测到的语言")
    duration: float = Field(..., description="音频时长")
    text: str = Field(..., description="转录的文本")
    segments: Optional[list] = Field(None, description="音频段落信息")
    
    
class OpenAIErrorResponse(BaseModel):
    """OpenAI 错误响应模型"""
    error: Dict[str, Any] = Field(..., description="错误详情")
    

class OpenAIError(BaseModel):
    """OpenAI 错误详情模型"""
    message: str = Field(..., description="错误消息")
    type: str = Field(..., description="错误类型")
    param: Optional[str] = Field(None, description="错误参数")
    code: Optional[str] = Field(None, description="错误代码") 