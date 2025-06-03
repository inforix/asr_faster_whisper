"""
语音识别API路由
"""

import asyncio
import json
import aiofiles
from pathlib import Path
from typing import Optional, Union
from datetime import datetime, UTC

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

# 音频处理配置
AUDIO_CONFIG = {
    "sample_rate": 16000,  # 16kHz
    "bytes_per_sample": 2,  # 16-bit
    "channels": 1,  # 单声道
    "bytes_per_second": 16000 * 2 * 1,  # 32KB/秒
    
    # 缓冲区阈值配置
    "min_buffer_size": 16000,   # 0.5秒 - 最小处理单位
    "optimal_buffer_size": 32000,  # 1.0秒 - 最佳处理单位  
    "max_buffer_size": 64000,   # 2.0秒 - 最大缓冲
    
    # 处理策略
    "enable_vad": True,  # 启用语音活动检测
    "silence_threshold": 0.1,  # 静音阈值
}

# 音频日志配置
AUDIO_LOG_CONFIG = {
    "enabled": True,  # 是否启用音频文件日志
    "log_dir": "logs/audio",  # 音频文件保存目录
    "max_files": 100,  # 最大保存文件数
    "file_prefix": "uploaded_audio",  # 文件名前缀
    "websocket_prefix": "websocket_audio",  # WebSocket音频文件前缀
}

async def save_audio_file_for_debug(
    audio_data: bytes, 
    original_filename: str, 
    content_type: str,
    client_info: Optional[str] = None
) -> Optional[str]:
    """
    保存上传的音频文件到logs目录用于调试
    
    Args:
        audio_data: 音频文件数据
        original_filename: 原始文件名
        content_type: 文件MIME类型
        client_info: 客户端信息（可选）
    
    Returns:
        str: 保存的文件路径，如果保存失败则返回None
    """
    if not AUDIO_LOG_CONFIG["enabled"]:
        return None
    
    try:
        # 创建日志目录
        log_dir = Path(AUDIO_LOG_CONFIG["log_dir"])
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成时间戳
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 精确到毫秒
        
        # 从原始文件名提取扩展名
        original_ext = ""
        if original_filename and "." in original_filename:
            original_ext = Path(original_filename).suffix.lower()
        
        # 根据content_type推断扩展名（如果原始文件名没有扩展名）
        if not original_ext:
            content_type_map = {
                "audio/wav": ".wav",
                "audio/wave": ".wav", 
                "audio/x-wav": ".wav",
                "audio/mpeg": ".mp3",
                "audio/mp3": ".mp3",
                "audio/mp4": ".m4a",
                "audio/m4a": ".m4a",
                "audio/x-m4a": ".m4a",
                "audio/aac": ".aac",
                "audio/x-aac": ".aac",
                "audio/flac": ".flac",
                "audio/x-flac": ".flac",
                "audio/ogg": ".ogg",
                "audio/x-ogg": ".ogg",
                "audio/webm": ".webm",
                "video/webm": ".webm",
            }
            original_ext = content_type_map.get(content_type, ".bin")
        
        # 构建文件名
        safe_original_name = "".join(
            c for c in (original_filename or "unknown") 
            if c.isalnum() or c in "._-"
        )[:50]
        filename = f"{AUDIO_LOG_CONFIG['file_prefix']}_{timestamp}_{safe_original_name}{original_ext}"
        file_path = log_dir / filename
        
        # 异步保存文件
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(audio_data)
        
        # 创建元数据文件
        metadata = {
            "timestamp": datetime.now(UTC).isoformat(),
            "original_filename": original_filename,
            "content_type": content_type,
            "file_size_bytes": len(audio_data),
            "client_info": client_info,
            "saved_filename": filename,
            "file_path": str(file_path)
        }
        
        metadata_path = file_path.with_suffix(f"{original_ext}.meta.json")
        async with aiofiles.open(metadata_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(metadata, indent=2, ensure_ascii=False))
        
        # 清理旧文件（保持文件数量在限制内）
        await cleanup_old_audio_logs()
        
        logger.info(
            "音频文件已保存用于调试",
            saved_path=str(file_path),
            original_filename=original_filename,
            file_size=len(audio_data),
            content_type=content_type
        )
        
        return str(file_path)
        
    except Exception as e:
        logger.error(
            "保存音频调试文件失败",
            error=str(e),
            original_filename=original_filename,
            exc_info=True
        )
        return None

async def save_websocket_audio_for_debug(
    audio_data: bytes,
    client_id: str,
    chunk_index: int = 0,
    is_combined: bool = False
) -> Optional[str]:
    """
    保存WebSocket接收的音频数据到logs目录用于调试
    
    Args:
        audio_data: 音频数据
        client_id: 客户端ID
        chunk_index: 音频块索引
        is_combined: 是否为合并后的音频数据
    
    Returns:
        str: 保存的文件路径，如果保存失败则返回None
    """
    if not AUDIO_LOG_CONFIG["enabled"]:
        return None
    
    try:
        # 创建日志目录
        log_dir = Path(AUDIO_LOG_CONFIG["log_dir"])
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成时间戳
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 精确到毫秒
        
        # 构建文件名
        safe_client_id = "".join(c for c in client_id if c.isalnum() or c in "._-")[:30]
        chunk_type = "combined" if is_combined else f"chunk_{chunk_index:04d}"
        filename = f"{AUDIO_LOG_CONFIG['websocket_prefix']}_{timestamp}_{safe_client_id}_{chunk_type}.bin"
        file_path = log_dir / filename
        
        # 异步保存文件
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(audio_data)
        
        # 创建元数据文件
        metadata = {
            "timestamp": datetime.now(UTC).isoformat(),
            "client_id": client_id,
            "chunk_index": chunk_index,
            "is_combined": is_combined,
            "file_size_bytes": len(audio_data),
            "saved_filename": filename,
            "file_path": str(file_path),
            "source": "websocket"
        }
        
        metadata_path = file_path.with_suffix(".meta.json")
        async with aiofiles.open(metadata_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(metadata, indent=2, ensure_ascii=False))
        
        # 清理旧文件（保持文件数量在限制内）
        await cleanup_old_audio_logs()
        
        logger.debug(
            "WebSocket音频数据已保存用于调试",
            saved_path=str(file_path),
            client_id=client_id,
            file_size=len(audio_data),
            chunk_index=chunk_index,
            is_combined=is_combined
        )
        
        return str(file_path)
        
    except Exception as e:
        logger.error(
            "保存WebSocket音频调试文件失败",
            error=str(e),
            client_id=client_id,
            exc_info=True
        )
        return None

async def cleanup_old_audio_logs():
    """清理旧的音频日志文件，保持文件数量在限制内"""
    try:
        log_dir = Path(AUDIO_LOG_CONFIG["log_dir"])
        if not log_dir.exists():
            return
        
        # 获取所有音频文件（排除元数据文件）
        audio_files = []
        for file_path in log_dir.iterdir():
            if (file_path.is_file() and 
                    (file_path.name.startswith(AUDIO_LOG_CONFIG["file_prefix"]) or
                     file_path.name.startswith(AUDIO_LOG_CONFIG["websocket_prefix"])) and
                    not file_path.name.endswith('.meta.json')):
                audio_files.append(file_path)
        
        # 按修改时间排序，最新的在前
        audio_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # 删除超出限制的文件
        max_files = AUDIO_LOG_CONFIG["max_files"]
        if len(audio_files) > max_files:
            files_to_delete = audio_files[max_files:]
            for file_path in files_to_delete:
                try:
                    # 删除音频文件
                    file_path.unlink()
                    # 删除对应的元数据文件
                    metadata_path = file_path.with_suffix(".meta.json")
                    if metadata_path.exists():
                        metadata_path.unlink()
                    logger.debug(f"已删除旧音频日志文件: {file_path.name}")
                except Exception as e:
                    logger.warning(f"删除旧音频日志文件失败: {file_path.name}, 错误: {e}")
        
    except Exception as e:
        logger.error(f"清理音频日志文件失败: {e}")

def get_audio_duration_ms(data_size: int) -> float:
    """根据数据大小计算音频时长（毫秒）"""
    return (data_size / AUDIO_CONFIG["bytes_per_second"]) * 1000

def should_process_buffer(buffer_size: int, is_first_chunk: bool = False) -> bool:
    """判断是否应该处理缓冲区"""
    if is_first_chunk:
        # 第一个块，如果大于最小阈值就处理
        return buffer_size >= AUDIO_CONFIG["min_buffer_size"]
    else:
        # 后续块，达到最佳阈值或超过最大阈值时处理
        return (buffer_size >= AUDIO_CONFIG["optimal_buffer_size"] or 
                buffer_size >= AUDIO_CONFIG["max_buffer_size"])


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
        
        # 保存音频文件用于调试
        saved_path = await save_audio_file_for_debug(
            audio_data=audio_data,
            original_filename=audio_file.filename,
            content_type=audio_file.content_type,
            client_info=f"API_upload_{datetime.now(UTC).strftime('%H%M%S')}"
        )
        
        # 调用Whisper服务进行识别
        try:
            result = await whisper_service.transcribe(audio_data, realtime_mode=False)
            
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
                    "size_bytes": len(audio_data),
                    "debug_saved_path": saved_path  # 添加调试文件路径信息
                },
                processing_info={
                    "segments": result.get("segments", 0),
                    "requested_language": language,
                    "processing_time": datetime.now(UTC).isoformat()
                }
            )
            
            # 记录成功日志
            if result["text"].strip():
                logger.info(
                    "语音识别成功",
                    text_preview=result["text"][:100] + "..." if len(result["text"]) > 100 else result["text"],
                    confidence=result["confidence"],
                    duration=result["duration"],
                    language=result["language"],
                    debug_saved_path=saved_path
                )
            else:
                logger.info(
                    "语音识别完成，但未检测到语音内容",
                    duration=result["duration"],
                    language=result["language"],
                    debug_saved_path=saved_path
                )
            
            return response_data
            
        except Exception as transcribe_error:
            logger.error(
                "语音识别处理失败",
                error=str(transcribe_error),
                filename=audio_file.filename,
                file_size=len(audio_data),
                debug_saved_path=saved_path
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
        "total_size": 0,
        "chunk_counter": 0  # 添加音频块计数器
    }
    
    try:
        await websocket.accept()
        logger.info(f"WebSocket连接已建立: {client_id}")
        
        # 发送连接成功消息
        await websocket.send_text(json.dumps({
            "type": "connection",
            "status": "connected",
            "message": "WebSocket连接成功",
            "timestamp": datetime.now(UTC).isoformat() + "Z"
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
                        buffer["chunk_counter"] += 1
                        
                        # 保存WebSocket音频数据用于调试
                        saved_path = await save_websocket_audio_for_debug(
                            audio_data=audio_data,
                            client_id=client_id,
                            chunk_index=buffer["chunk_counter"],
                            is_combined=False
                        )
                        
                        try:
                            # 处理音频数据
                            buffer = audio_buffers[client_id]
                            duration_ms = get_audio_duration_ms(len(audio_data))
                            
                            # 添加音频数据验证和调试信息
                            audio_preview = audio_data[:16].hex() if len(audio_data) >= 16 else audio_data.hex()
                            logger.debug(f"音频块详情: {len(audio_data)} bytes, {duration_ms:.1f}ms, "
                                       f"前16字节: {audio_preview}, 来源: {client_id}")
                            
                            if not buffer["first_chunk_processed"]:
                                # 第一个块，如果足够大就直接处理
                                if should_process_buffer(len(audio_data), is_first_chunk=True):
                                    logger.info(f"处理首个音频块: {len(audio_data)} bytes")
                                    result = await whisper_service.transcribe(audio_data, realtime_mode=True)
                                    buffer["first_chunk_processed"] = True
                                    
                                    logger.info(f"首块处理完成: {len(audio_data)} bytes, "
                                              f"识别结果: '{result['text'][:30]}...', "
                                              f"音频统计: {result.get('audio_stats', {})}")
                                else:
                                    # 第一个块太小，跳过处理但标记为已处理
                                    buffer["first_chunk_processed"] = True
                                    min_size = AUDIO_CONFIG['min_buffer_size']
                                    logger.debug(f"首块太小跳过: {len(audio_data)} bytes < {min_size} bytes")
                                    continue
                            else:
                                # 后续块，根据缓冲区大小决定是否处理
                                if should_process_buffer(buffer["total_size"]):
                                    # 合并所有音频块
                                    combined_audio = b''.join(buffer["chunks"])
                                    total_duration_ms = get_audio_duration_ms(len(combined_audio))
                                    
                                    # 保存合并后的音频数据用于调试
                                    combined_saved_path = await save_websocket_audio_for_debug(
                                        audio_data=combined_audio,
                                        client_id=client_id,
                                        chunk_index=buffer["chunk_counter"],
                                        is_combined=True
                                    )
                                    
                                    logger.info(f"处理合并音频: {len(combined_audio)} bytes, "
                                              f"{total_duration_ms:.1f}ms, 包含 {len(buffer['chunks'])} 个块")
                                    
                                    result = await whisper_service.transcribe(combined_audio, realtime_mode=True)
                                    
                                    # 智能缓冲区管理：保留部分重叠以提高连续性
                                    overlap_size = AUDIO_CONFIG["min_buffer_size"] // 2  # 保留0.25秒重叠
                                    if len(combined_audio) > overlap_size:
                                        # 保留最后一部分作为下次的起始
                                        overlap_data = combined_audio[-overlap_size:]
                                        buffer["chunks"] = [overlap_data]
                                        buffer["total_size"] = len(overlap_data)
                                        logger.debug(f"保留重叠数据: {len(overlap_data)} bytes")
                                    else:
                                        # 如果数据太小，清空缓冲区
                                        buffer["chunks"] = []
                                        buffer["total_size"] = 0
                                        logger.debug("清空缓冲区")
                                    
                                    logger.info(f"合并音频处理完成: {total_duration_ms:.1f}ms, "
                                              f"识别: '{result['text'][:30]}...', "
                                              f"音频统计: {result.get('audio_stats', {})}")
                                else:
                                    # 缓冲区还不够大，继续积累
                                    current_duration = get_audio_duration_ms(buffer["total_size"])
                                    logger.debug(f"继续缓冲: {buffer['total_size']} bytes "
                                               f"({current_duration:.1f}ms), 共 {len(buffer['chunks'])} 块")
                                    continue
                            
                            # 发送识别结果
                            response = {
                                "type": "transcript",
                                "text": result["text"],
                                "confidence": result["confidence"],
                                "language": result["language"],
                                "duration": result["duration"],
                                "timestamp": datetime.now(UTC).isoformat() + "Z",
                                "debug_info": {
                                    "audio_stats": result.get("audio_stats", {}),
                                    "chunk_count": len(buffer["chunks"]) if "chunks" in buffer else 0
                                }
                            }
                            
                            await websocket.send_text(json.dumps(response))
                            
                            if result["text"].strip():
                                logger.info(f"WebSocket语音识别成功: '{result['text'][:50]}...' "
                                          f"(置信度: {result['confidence']:.3f})")
                            else:
                                logger.debug(f"WebSocket无语音内容: 时长={result['duration']:.2f}s, "
                                           f"统计={result.get('audio_stats', {})}")
                            
                        except Exception as e:
                            logger.error(f"语音识别失败: {e}, 调试文件: {saved_path}", exc_info=True)
                            # 发送错误消息
                            error_response = {
                                "type": "error",
                                "message": f"语音识别失败: {str(e)}",
                                "timestamp": datetime.now(UTC).isoformat() + "Z"
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
                        "timestamp": datetime.now(UTC).isoformat() + "Z"
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
            total_chunks = audio_buffers[client_id].get("chunk_counter", 0)
            del audio_buffers[client_id]
            logger.info(f"WebSocket连接清理完成: {client_id}, 总共处理了 {total_chunks} 个音频块")
        else:
            logger.info(f"WebSocket连接清理完成: {client_id}") 