"""
语音识别API路由
"""

import asyncio
import json
import logging

from app.services.whisper.whisper_service import whisper_service
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

voice_router = APIRouter()
logger = logging.getLogger(__name__)

# 全局音频缓冲区管理
audio_buffers = {}


@voice_router.get("/status")
async def get_voice_status():
    """获取语音识别服务状态"""
    return {
        "status": "active",
        "service": "voice_recognition",
        "message": "语音识别服务正常运行"
    }


@voice_router.post("/recognize")
async def recognize_audio():
    """语音识别接口"""
    # TODO: 实现语音识别逻辑
    return {
        "message": "语音识别功能开发中",
        "status": "not_implemented"
    }


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