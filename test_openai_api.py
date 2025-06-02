#!/usr/bin/env python3
"""
OpenAI 兼容 API 测试脚本
测试 /v1/audio/transcriptions 端点
"""

import asyncio
import aiohttp
import json


async def test_openai_transcription_json():
    """测试OpenAI兼容的转录接口（JSON格式）"""
    print("🎤 测试OpenAI兼容转录接口（JSON格式）...")
    
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
            # 准备表单数据（OpenAI格式）
            data = aiohttp.FormData()
            data.add_field('file', wav_data, 
                           filename='test_audio.wav', 
                           content_type='audio/wav')
            data.add_field('model', 'whisper-1')
            data.add_field('response_format', 'json')
            data.add_field('language', 'zh')
            
            async with session.post("http://localhost:8087/v1/audio/transcriptions", 
                                    data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ OpenAI转录成功（JSON格式）:")
                    print(f"   转录文本: '{result['text']}'")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ OpenAI转录失败: {response.status}")
                    print(f"   错误信息: {error_text}")
                    return False
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return False


async def test_openai_transcription_text():
    """测试OpenAI兼容的转录接口（文本格式）"""
    print("\n📝 测试OpenAI兼容转录接口（文本格式）...")
    
    # 使用相同的测试音频
    sample_rate = 16000
    duration = 1
    samples = sample_rate * duration
    
    wav_header = bytearray([
        0x52, 0x49, 0x46, 0x46, 0x00, 0x00, 0x00, 0x00,
        0x57, 0x41, 0x56, 0x45, 0x66, 0x6D, 0x74, 0x20,
        0x10, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00,
        0x80, 0x3E, 0x00, 0x00, 0x00, 0x7D, 0x00, 0x00,
        0x02, 0x00, 0x10, 0x00, 0x64, 0x61, 0x74, 0x61,
        0x00, 0x00, 0x00, 0x00,
    ])
    
    audio_data = bytearray([0x00, 0x00] * samples)
    total_size = len(wav_header) + len(audio_data) - 8
    wav_header[4:8] = total_size.to_bytes(4, 'little')
    wav_header[40:44] = len(audio_data).to_bytes(4, 'little')
    wav_data = wav_header + audio_data
    
    async with aiohttp.ClientSession() as session:
        try:
            data = aiohttp.FormData()
            data.add_field('file', wav_data, 
                           filename='test_audio.wav', 
                           content_type='audio/wav')
            data.add_field('model', 'whisper-1')
            data.add_field('response_format', 'text')
            
            async with session.post("http://localhost:8087/v1/audio/transcriptions", 
                                    data=data) as response:
                if response.status == 200:
                    result = await response.text()
                    print("✅ OpenAI转录成功（文本格式）:")
                    print(f"   转录文本: '{result}'")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ OpenAI转录失败: {response.status}")
                    print(f"   错误信息: {error_text}")
                    return False
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return False


async def test_openai_transcription_verbose():
    """测试OpenAI兼容的转录接口（详细JSON格式）"""
    print("\n📊 测试OpenAI兼容转录接口（详细JSON格式）...")
    
    # 使用相同的测试音频
    sample_rate = 16000
    duration = 1
    samples = sample_rate * duration
    
    wav_header = bytearray([
        0x52, 0x49, 0x46, 0x46, 0x00, 0x00, 0x00, 0x00,
        0x57, 0x41, 0x56, 0x45, 0x66, 0x6D, 0x74, 0x20,
        0x10, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00,
        0x80, 0x3E, 0x00, 0x00, 0x00, 0x7D, 0x00, 0x00,
        0x02, 0x00, 0x10, 0x00, 0x64, 0x61, 0x74, 0x61,
        0x00, 0x00, 0x00, 0x00,
    ])
    
    audio_data = bytearray([0x00, 0x00] * samples)
    total_size = len(wav_header) + len(audio_data) - 8
    wav_header[4:8] = total_size.to_bytes(4, 'little')
    wav_header[40:44] = len(audio_data).to_bytes(4, 'little')
    wav_data = wav_header + audio_data
    
    async with aiohttp.ClientSession() as session:
        try:
            data = aiohttp.FormData()
            data.add_field('file', wav_data, 
                           filename='test_audio.wav', 
                           content_type='audio/wav')
            data.add_field('model', 'whisper-1')
            data.add_field('response_format', 'verbose_json')
            
            async with session.post("http://localhost:8087/v1/audio/transcriptions", 
                                    data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ OpenAI转录成功（详细JSON格式）:")
                    print(f"   任务类型: {result['task']}")
                    print(f"   语言: {result['language']}")
                    print(f"   时长: {result['duration']:.2f}秒")
                    print(f"   转录文本: '{result['text']}'")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ OpenAI转录失败: {response.status}")
                    print(f"   错误信息: {error_text}")
                    return False
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return False


async def test_openai_error_handling():
    """测试OpenAI API错误处理"""
    print("\n🚫 测试OpenAI API错误处理...")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 测试无效模型
            data = aiohttp.FormData()
            data.add_field('file', b'invalid audio data', 
                           filename='test.wav', 
                           content_type='audio/wav')
            data.add_field('model', 'invalid-model')
            
            async with session.post("http://localhost:8087/v1/audio/transcriptions", 
                                    data=data) as response:
                if response.status == 400:
                    error_data = await response.json()
                    print(f"✅ 正确处理无效模型: {response.status}")
                    print(f"   错误类型: {error_data['error']['type']}")
                    print(f"   错误消息: {error_data['error']['message']}")
                    return True
                else:
                    print(f"❌ 应该返回400错误，但返回了: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return False


async def test_curl_compatibility():
    """测试与curl命令的兼容性"""
    print("\n🌐 测试curl命令兼容性...")
    print("可以使用以下curl命令测试API:")
    print()
    print("# JSON格式响应")
    print('curl -X POST "http://localhost:8087/v1/audio/transcriptions" \\')
    print('  -H "Content-Type: multipart/form-data" \\')
    print('  -F "file=@your_audio_file.wav" \\')
    print('  -F "model=whisper-1" \\')
    print('  -F "response_format=json"')
    print()
    print("# 文本格式响应")
    print('curl -X POST "http://localhost:8087/v1/audio/transcriptions" \\')
    print('  -H "Content-Type: multipart/form-data" \\')
    print('  -F "file=@your_audio_file.wav" \\')
    print('  -F "model=whisper-1" \\')
    print('  -F "response_format=text"')
    print()
    print("# 详细JSON格式响应")
    print('curl -X POST "http://localhost:8087/v1/audio/transcriptions" \\')
    print('  -H "Content-Type: multipart/form-data" \\')
    print('  -F "file=@your_audio_file.wav" \\')
    print('  -F "model=whisper-1" \\')
    print('  -F "response_format=verbose_json"')
    print()


async def main():
    """主测试函数"""
    print("🚀 开始测试OpenAI兼容音频转录API")
    print("=" * 60)
    
    # 测试各种格式
    json_ok = await test_openai_transcription_json()
    text_ok = await test_openai_transcription_text()
    verbose_ok = await test_openai_transcription_verbose()
    error_ok = await test_openai_error_handling()
    
    # 显示curl示例
    await test_curl_compatibility()
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    print(f"   JSON格式: {'✅' if json_ok else '❌'}")
    print(f"   文本格式: {'✅' if text_ok else '❌'}")
    print(f"   详细JSON: {'✅' if verbose_ok else '❌'}")
    print(f"   错误处理: {'✅' if error_ok else '❌'}")
    
    if all([json_ok, text_ok, verbose_ok, error_ok]):
        print("\n🎉 所有测试通过！OpenAI兼容API工作正常")
        print("\n🔗 API端点: http://localhost:8087/v1/audio/transcriptions")
        print("📚 API文档: http://localhost:8087/docs")
    else:
        print("\n⚠️  部分测试失败，请检查服务配置")


if __name__ == "__main__":
    asyncio.run(main()) 