"""
OpenAI API 兼容性端点
提供与 OpenAI Audio API 兼容的接口
"""

import structlog
from typing import Optional, Union
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse

from app.services.whisper.whisper_service import whisper_service
from app.models.openai_compat import (
    OpenAITranscriptionResponse,
    OpenAIVerboseTranscriptionResponse,
    OpenAIErrorResponse
)

openai_router = APIRouter()
logger = structlog.get_logger(__name__)


@openai_router.post("/v1/audio/transcriptions")
async def create_transcription(
    file: UploadFile = File(..., description="要转录的音频文件"),
    model: str = Form(..., description="要使用的模型ID，目前支持 whisper-1"),
    prompt: Optional[str] = Form(None, description="可选的提示文本"),
    response_format: Optional[str] = Form("json", description="响应格式: json, text, srt, verbose_json, vtt"),
    temperature: Optional[float] = Form(0, description="采样温度，0到1之间"),
    language: Optional[str] = Form(None, description="输入音频的语言，ISO-639-1格式")
) -> Union[OpenAITranscriptionResponse, OpenAIVerboseTranscriptionResponse, PlainTextResponse, str]:
    """
    OpenAI 兼容的音频转录接口
    
    将音频转录为输入语言的文本。与 OpenAI Audio API 完全兼容。
    
    支持的音频格式：
    - mp3, mp4, mpeg, mpga, m4a, wav, webm
    
    Args:
        file: 音频文件，最大25MB
        model: 模型ID，目前只支持 "whisper-1"
        prompt: 可选的提示文本，用于指导模型风格
        response_format: 输出格式 (json, text, srt, verbose_json, vtt)
        temperature: 采样温度，0-1之间
        language: 输入音频语言代码
    
    Returns:
        根据 response_format 返回不同格式的转录结果
    """
    try:
        # 验证模型参数
        if model not in ["whisper-1"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "message": f"Invalid model: '{model}'. Currently only 'whisper-1' is supported.",
                        "type": "invalid_request_error",
                        "param": "model",
                        "code": None
                    }
                }
            )
        
        # 验证响应格式
        valid_formats = ["json", "text", "srt", "verbose_json", "vtt"]
        if response_format not in valid_formats:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "message": f"Invalid response_format: '{response_format}'. Must be one of {valid_formats}.",
                        "type": "invalid_request_error",
                        "param": "response_format",
                        "code": None
                    }
                }
            )
        
        # 验证温度参数
        if temperature is not None and (temperature < 0 or temperature > 1):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "message": f"Invalid temperature: {temperature}. Must be between 0 and 1.",
                        "type": "invalid_request_error",
                        "param": "temperature",
                        "code": None
                    }
                }
            )
        
        # 验证服务状态
        if not whisper_service.is_initialized:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": {
                        "message": "Whisper service is not initialized. Please try again later.",
                        "type": "service_unavailable_error",
                        "param": None,
                        "code": None
                    }
                }
            )
        
        # 验证文件
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "message": "No file provided.",
                        "type": "invalid_request_error",
                        "param": "file",
                        "code": None
                    }
                }
            )
        
        # 支持的音频MIME类型（与OpenAI兼容）
        supported_types = {
            "audio/mpeg", "audio/mp3",
            "audio/mp4", "audio/m4a", "audio/x-m4a",
            "audio/wav", "audio/wave", "audio/x-wav",
            "audio/webm",
            "video/mp4",  # MP4视频文件可能包含音频
            "video/webm",
            "application/octet-stream"  # 通用二进制类型
        }
        
        if file.content_type and file.content_type not in supported_types:
            logger.warning(f"Unsupported content type: {file.content_type}, but will try to process")
        
        # 读取音频数据
        audio_data = await file.read()
        
        if len(audio_data) == 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "message": "The uploaded file is empty.",
                        "type": "invalid_request_error",
                        "param": "file",
                        "code": None
                    }
                }
            )
        
        # OpenAI限制为25MB
        max_size = 25 * 1024 * 1024  # 25MB
        if len(audio_data) > max_size:
            raise HTTPException(
                status_code=413,
                detail={
                    "error": {
                        "message": f"File size {len(audio_data)} bytes exceeds the maximum allowed size of {max_size} bytes.",
                        "type": "invalid_request_error",
                        "param": "file",
                        "code": None
                    }
                }
            )
        
        logger.info(
            "Processing OpenAI transcription request",
            filename=file.filename,
            content_type=file.content_type,
            file_size=len(audio_data),
            model=model,
            response_format=response_format,
            language=language
        )
        
        # 调用Whisper服务进行转录
        try:
            result = await whisper_service.transcribe(audio_data)
            
            # 根据response_format返回不同格式
            if response_format == "text":
                return PlainTextResponse(content=result["text"])
            
            elif response_format == "json":
                return OpenAITranscriptionResponse(text=result["text"])
            
            elif response_format == "verbose_json":
                return OpenAIVerboseTranscriptionResponse(
                    task="transcribe",
                    language=result["language"],
                    duration=result["duration"],
                    text=result["text"],
                    segments=None  # 暂时不支持段落信息
                )
            
            elif response_format == "srt":
                # 生成SRT字幕格式
                srt_content = f"""1
00:00:00,000 --> {_format_srt_time(result["duration"])}
{result["text"]}

"""
                return PlainTextResponse(content=srt_content, media_type="text/plain")
            
            elif response_format == "vtt":
                # 生成WebVTT字幕格式
                vtt_content = f"""WEBVTT

00:00:00.000 --> {_format_vtt_time(result["duration"])}
{result["text"]}

"""
                return PlainTextResponse(content=vtt_content, media_type="text/vtt")
            
            else:
                # 默认返回JSON格式
                return OpenAITranscriptionResponse(text=result["text"])
                
        except Exception as transcribe_error:
            logger.error(
                "Transcription failed",
                error=str(transcribe_error),
                filename=file.filename,
                file_size=len(audio_data)
            )
            raise HTTPException(
                status_code=500,
                detail={
                    "error": {
                        "message": f"Transcription failed: {str(transcribe_error)}",
                        "type": "server_error",
                        "param": None,
                        "code": None
                    }
                }
            )
    
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(
            "Unexpected error in transcription endpoint",
            error=str(e),
            filename=getattr(file, 'filename', 'unknown'),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": f"Internal server error: {str(e)}",
                    "type": "server_error",
                    "param": None,
                    "code": None
                }
            }
        )


def _format_srt_time(seconds: float) -> str:
    """将秒数转换为SRT时间格式 (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def _format_vtt_time(seconds: float) -> str:
    """将秒数转换为WebVTT时间格式 (HH:MM:SS.mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}" 