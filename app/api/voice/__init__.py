"""
语音识别API路由
"""

import asyncio
import json
from typing import Optional, Union
from datetime import datetime

from app.services.whisper.whisper_service import whisper_service
from app.models.voice import (
    VoiceRecognitionResponse, 
    VoiceServiceStatus, 
    ErrorResponse
)
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
import structlog

voice_router = APIRouter()
logger = structlog.get_logger(__name__)

# 全局音频缓冲区管理
audio_buffers = {}


@voice_router.get("/status", response_model=VoiceServiceStatus)
async def get_voice_status() -> Union[VoiceServiceStatus, JSONResponse]:
    """获取语音识别服务状态"""
    try:
        status = await whisper_service.get_status()
        return VoiceServiceStatus(
            status="active",
            service="voice_recognition",
            message="语音识别服务正常运行",
            whisper_service=status
        )
    except Exception as e:
        logger.error("获取语音识别服务状态失败", error=str(e))
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                error="service_unavailable",
                message=f"语音识别服务异常: {str(e)}"
            ).dict()
        )


@voice_router.post("/recognize", response_model=VoiceRecognitionResponse)
async def recognize_audio(
    audio_file: UploadFile = File(..., description="音频文件"),
    language: Optional[str] = Form(default="zh", description="语言代码，默认为中文(zh)")
) -> VoiceRecognitionResponse:
    """
    语音识别接口
    
    支持的音频格式：
    - WAV, MP3, M4A, AAC, FLAC, OGG, WEBM
    - 建议采样率：16kHz
    - 建议声道：单声道
    
    Args:
        audio_file: 上传的音频文件
        language: 语言代码，支持 zh(中文), en(英文), auto(自动检测)
    
    Returns:
        VoiceRecognitionResponse: 包含识别结果、置信度、语言等信息
    
    Raises:
        HTTPException: 当服务不可用、文件格式不支持或处理失败时
    """
    try:
        # 验证服务状态
        if not whisper_service.is_initialized:
            raise HTTPException(
                status_code=503,
                detail="语音识别服务未初始化，请稍后重试"
            )
        
        # 验证文件类型
        if not audio_file.content_type:
            raise HTTPException(
                status_code=400,
                detail="无法确定文件类型"
            )
        
        # 支持的音频MIME类型
        supported_types = {
            "audio/wav", "audio/wave", "audio/x-wav",
            "audio/mpeg", "audio/mp3",
            "audio/mp4", "audio/m4a", "audio/x-m4a",
            "audio/aac", "audio/x-aac",
            "audio/flac", "audio/x-flac",
            "audio/ogg", "audio/x-ogg",
            "audio/webm",
            "video/webm",  # WebM可能包含音频
            "application/octet-stream"  # 通用二进制类型
        }
        
        if audio_file.content_type not in supported_types:
            logger.warning(f"不支持的文件类型: {audio_file.content_type}")
            # 不直接拒绝，尝试处理，因为有些浏览器可能发送错误的MIME类型
        
        # 验证文件大小（限制为50MB）
        max_size = 50 * 1024 * 1024  # 50MB
        audio_data = await audio_file.read()
        
        if len(audio_data) == 0:
            raise HTTPException(
                status_code=400,
                detail="上传的文件为空"
            )
        
        if len(audio_data) > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"文件过大，最大支持 {max_size // (1024*1024)}MB"
            )
        
        logger.info(
            "开始处理语音识别请求",
            filename=audio_file.filename,
            content_type=audio_file.content_type,
            file_size=len(audio_data),
            language=language
        )
        
        # 调用Whisper服务进行识别
        try:
            result = await whisper_service.transcribe(audio_data)
            
            # 构建响应
            response_data = VoiceRecognitionResponse(
                success=True,
                text=result["text"],
                confidence=result["confidence"],
                language=result["language"],
                duration=result["duration"],
                file_info={
                    "filename": audio_file.filename,
                    "content_type": audio_file.content_type,
                    "size_bytes": len(audio_data)
                },
                processing_info={
                    "segments": result.get("segments", 0),
                    "requested_language": language,
                    "processing_time": datetime.utcnow().isoformat()
                }
            )
            
            # 记录成功日志
            if result["text"].strip():
                logger.info(
                    "语音识别成功",
                    text_preview=result["text"][:100] + "..." if len(result["text"]) > 100 else result["text"],
                    confidence=result["confidence"],
                    duration=result["duration"],
                    language=result["language"]
                )
            else:
                logger.info(
                    "语音识别完成，但未检测到语音内容",
                    duration=result["duration"],
                    language=result["language"]
                )
            
            return response_data
            
        except Exception as transcribe_error:
            logger.error(
                "语音识别处理失败",
                error=str(transcribe_error),
                filename=audio_file.filename,
                file_size=len(audio_data)
            )
            raise HTTPException(
                status_code=500,
                detail=f"语音识别处理失败: {str(transcribe_error)}"
            )
    
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(
            "语音识别接口异常",
            error=str(e),
            filename=getattr(audio_file, 'filename', 'unknown'),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"服务器内部错误: {str(e)}"
        )


@voice_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket语音识别接口"""
    client_ip = websocket.client.host if websocket.client else "unknown"
    client_id = f"{client_ip}:{websocket.client.port}" if websocket.client else "unknown"
    logger.info(f"新的WebSocket连接请求来自: {client_id}")
    
    # 初始化客户端音频缓冲区
    audio_buffers[client_id] = {
        "chunks": [],
        "first_chunk_processed": False,
        "total_size": 0
    }
    
    try:
        await websocket.accept()
        logger.info(f"WebSocket连接已建立: {client_id}")
        
        # 发送连接成功消息
        await websocket.send_text(json.dumps({
            "type": "connection",
            "status": "connected",
            "message": "WebSocket连接成功",
            "timestamp": "2025-06-01T03:30:00Z"
        }))
        
        while True:
            try:
                # 接收数据，设置超时
                data = await asyncio.wait_for(websocket.receive(), timeout=30.0)
                
                if data["type"] == "websocket.receive":
                    if "bytes" in data:
                        # 处理音频数据
                        audio_data = data["bytes"]
                        logger.info(f"收到音频数据: {len(audio_data)} bytes from {client_id}")
                        
                        if len(audio_data) == 0:
                            logger.warning("收到空音频数据")
                            continue
                        
                        # 添加到缓冲区
                        buffer = audio_buffers[client_id]
                        buffer["chunks"].append(audio_data)
                        buffer["total_size"] += len(audio_data)
                        
                        try:
                            # 处理音频数据
                            if not buffer["first_chunk_processed"]:
                                # 第一个块，尝试作为完整文件处理
                                result = await whisper_service.transcribe(audio_data)
                                buffer["first_chunk_processed"] = True
                            else:
                                # 后续块，合并处理
                                if buffer["total_size"] >= 32000:  # 32KB阈值
                                    # 合并所有音频块
                                    combined_audio = b''.join(buffer["chunks"])
                                    result = await whisper_service.transcribe(combined_audio)
                                    
                                    # 清空缓冲区，保留最后一个块作为下次的起始
                                    last_chunk = buffer["chunks"][-1]
                                    buffer["chunks"] = [last_chunk]
                                    buffer["total_size"] = len(last_chunk)
                                else:
                                    # 缓冲区不够大，跳过处理
                                    continue
                            
                            # 发送识别结果
                            response = {
                                "type": "transcript",
                                "text": result["text"],
                                "confidence": result["confidence"],
                                "language": result["language"],
                                "duration": result["duration"],
                                "timestamp": "2025-06-01T03:30:00Z"
                            }
                            
                            await websocket.send_text(json.dumps(response))
                            
                            if result["text"].strip():
                                logger.info(f"语音识别完成: '{result['text'][:50]}...' (置信度: {result['confidence']:.3f})")
                            
                        except Exception as e:
                            logger.error(f"语音识别失败: {e}")
                            # 发送错误消息
                            error_response = {
                                "type": "error",
                                "message": f"语音识别失败: {str(e)}",
                                "timestamp": "2025-06-01T03:30:00Z"
                            }
                            
                            try:
                                await websocket.send_text(json.dumps(error_response))
                            except Exception as send_error:
                                logger.error(f"发送错误消息失败: {send_error}")
                                break
                        
                    elif "text" in data:
                        # 处理文本消息
                        try:
                            message = json.loads(data["text"])
                            logger.info(f"收到文本消息: {message} from {client_id}")
                            
                            if message.get("type") == "ping":
                                pong_response = {
                                    "type": "pong",
                                    "timestamp": message.get("timestamp")
                                }
                                await websocket.send_text(json.dumps(pong_response))
                                
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON解析失败: {e}")
                            
                elif data["type"] == "websocket.disconnect":
                    logger.info(f"客户端主动断开连接: {client_id}")
                    break
                    
            except asyncio.TimeoutError:
                # 发送心跳检测
                try:
                    await websocket.send_text(json.dumps({
                        "type": "heartbeat",
                        "timestamp": "2025-06-01T03:30:00Z"
                    }))
                except Exception:
                    logger.warning(f"心跳发送失败，连接可能已断开: {client_id}")
                    break
                    
            except Exception as e:
                logger.error(f"接收数据时发生错误: {e}")
                break
                        
    except WebSocketDisconnect:
        logger.info(f"WebSocket连接已断开: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket错误: {e} from {client_id}")
        try:
            await websocket.close(code=1011, reason=str(e))
        except Exception:
            pass  # 连接可能已经关闭
    finally:
        # 清理客户端缓冲区
        if client_id in audio_buffers:
            del audio_buffers[client_id]
        logger.info(f"WebSocket连接清理完成: {client_id}") 