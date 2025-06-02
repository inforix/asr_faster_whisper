#!/usr/bin/env python3
"""
WebSocket音频日志测试脚本
"""

import asyncio
import websockets
import json
import struct

async def test_websocket_audio_logging():
    """测试WebSocket音频日志功能"""
    print("🔌 开始测试WebSocket音频日志功能...")
    
    try:
        # 连接到WebSocket
        uri = "ws://localhost:8087/api/voice/ws"
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket连接成功")
            
            # 接收连接确认消息
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📨 收到连接消息: {data['message']}")
            
            # 发送测试音频数据（模拟16位PCM音频）
            print("🎵 发送测试音频数据...")
            
            # 创建一些测试音频数据块
            for i in range(3):
                # 生成1秒的静音音频数据 (16kHz, 16-bit, mono)
                sample_rate = 16000
                duration = 1.0  # 1秒
                samples = int(sample_rate * duration)
                
                # 生成16位PCM静音数据
                audio_data = b'\x00\x00' * samples
                
                print(f"📤 发送音频块 {i+1}: {len(audio_data)} bytes")
                await websocket.send(audio_data)
                
                # 等待一下再发送下一块
                await asyncio.sleep(0.5)
                
                # 尝试接收响应
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(response)
                    print(f"📨 收到响应: {data.get('type', 'unknown')} - {data.get('text', 'no text')}")
                except asyncio.TimeoutError:
                    print("⏰ 等待响应超时，继续发送下一块")
                except Exception as e:
                    print(f"❌ 接收响应失败: {e}")
            
            print("✅ 音频数据发送完成")
            
            # 发送ping消息测试
            ping_msg = {
                "type": "ping",
                "timestamp": "2025-06-02T14:30:00Z"
            }
            await websocket.send(json.dumps(ping_msg))
            print("📤 发送ping消息")
            
            # 接收pong响应
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                print(f"📨 收到pong响应: {data}")
            except asyncio.TimeoutError:
                print("⏰ 等待pong响应超时")
            
    except Exception as e:
        print(f"❌ WebSocket测试失败: {e}")
        return False
    
    print("🎉 WebSocket音频日志测试完成")
    return True

async def main():
    """主函数"""
    print("🚀 开始WebSocket音频日志测试")
    print("=" * 50)
    
    success = await test_websocket_audio_logging()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ WebSocket音频日志测试成功")
        print("📁 请检查 logs/audio/ 目录查看保存的音频文件")
    else:
        print("❌ WebSocket音频日志测试失败")

if __name__ == "__main__":
    asyncio.run(main()) 