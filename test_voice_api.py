#!/usr/bin/env python3
"""
语音识别API测试脚本
"""

import asyncio
import aiohttp


async def test_voice_status():
    """测试语音服务状态接口"""
    print("🔍 测试语音服务状态接口...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8087/api/voice/status") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 服务状态正常: {data['message']}")
                    print(f"   Whisper服务: {data.get('whisper_service', {}).get('status', 'unknown')}")
                    return True
                else:
                    print(f"❌ 服务状态异常: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False


async def test_voice_recognition_with_sample():
    """测试语音识别接口（使用示例音频）"""
    print("\n🎤 测试语音识别接口...")
    
    # 创建一个简单的WAV文件头（静音音频用于测试）
    sample_rate = 16000
    duration = 1  # 1秒
    samples = sample_rate * duration
    
    # WAV文件头
    wav_header = bytearray([
        0x52, 0x49, 0x46, 0x46,  # "RIFF"
        0x00, 0x00, 0x00, 0x00,  # 文件大小（稍后填充）
        0x57, 0x41, 0x56, 0x45,  # "WAVE"
        0x66, 0x6D, 0x74, 0x20,  # "fmt "
        0x10, 0x00, 0x00, 0x00,  # fmt chunk size (16)
        0x01, 0x00,              # audio format (PCM)
        0x01, 0x00,              # channels (1)
        0x80, 0x3E, 0x00, 0x00,  # sample rate (16000)
        0x00, 0x7D, 0x00, 0x00,  # byte rate
        0x02, 0x00,              # block align
        0x10, 0x00,              # bits per sample (16)
        0x64, 0x61, 0x74, 0x61,  # "data"
        0x00, 0x00, 0x00, 0x00,  # data size（稍后填充）
    ])
    
    # 添加静音数据（16位PCM）
    audio_data = bytearray([0x00, 0x00] * samples)  # 静音
    
    # 更新文件大小
    total_size = len(wav_header) + len(audio_data) - 8
    wav_header[4:8] = total_size.to_bytes(4, 'little')
    wav_header[40:44] = len(audio_data).to_bytes(4, 'little')
    
    # 合并WAV数据
    wav_data = wav_header + audio_data
    
    async with aiohttp.ClientSession() as session:
        try:
            # 准备表单数据
            data = aiohttp.FormData()
            data.add_field('audio_file', wav_data, 
                           filename='test_audio.wav', 
                           content_type='audio/wav')
            data.add_field('language', 'zh')
            
            async with session.post("http://localhost:8087/api/voice/recognize", 
                                    data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ 语音识别成功:")
                    print(f"   识别文本: '{result['text']}'")
                    print(f"   置信度: {result['confidence']:.3f}")
                    print(f"   语言: {result['language']}")
                    print(f"   时长: {result['duration']:.2f}秒")
                    print(f"   文件大小: {result['file_info']['size_bytes']} bytes")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ 语音识别失败: {response.status}")
                    print(f"   错误信息: {error_text}")
                    return False
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return False


async def test_voice_recognition_with_invalid_file():
    """测试无效文件处理"""
    print("\n🚫 测试无效文件处理...")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 发送无效数据
            data = aiohttp.FormData()
            data.add_field('audio_file', b'invalid audio data', 
                           filename='invalid.txt', 
                           content_type='text/plain')
            
            async with session.post("http://localhost:8087/api/voice/recognize", 
                                    data=data) as response:
                if response.status >= 400:
                    error_data = await response.json()
                    print(f"✅ 正确处理无效文件: {response.status}")
                    print(f"   错误信息: {error_data.get('detail', 'Unknown error')}")
                    return True
                else:
                    print(f"❌ 应该拒绝无效文件，但返回了: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return False


async def main():
    """主测试函数"""
    print("🚀 开始测试语音识别API")
    print("=" * 50)
    
    # 测试服务状态
    status_ok = await test_voice_status()
    if not status_ok:
        print("\n❌ 服务未启动或不可用，请先启动服务")
        return
    
    # 测试语音识别
    recognition_ok = await test_voice_recognition_with_sample()
    
    # 测试错误处理
    error_handling_ok = await test_voice_recognition_with_invalid_file()
    
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    print(f"   服务状态: {'✅' if status_ok else '❌'}")
    print(f"   语音识别: {'✅' if recognition_ok else '❌'}")
    print(f"   错误处理: {'✅' if error_handling_ok else '❌'}")
    
    if all([status_ok, recognition_ok, error_handling_ok]):
        print("\n🎉 所有测试通过！语音识别API工作正常")
    else:
        print("\n⚠️  部分测试失败，请检查服务配置")


if __name__ == "__main__":
    asyncio.run(main()) 