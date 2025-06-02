#!/usr/bin/env python3
"""
真实音频测试脚本 - 生成包含信号的音频数据进行测试
"""

import asyncio
import aiohttp
import numpy as np
import struct
import math


def generate_test_audio(duration=2.0, sample_rate=16000, frequency=440.0, amplitude=0.1):
    """
    生成测试音频数据（正弦波）
    
    Args:
        duration: 音频时长（秒）
        sample_rate: 采样率
        frequency: 频率（Hz）
        amplitude: 振幅（0-1）
    
    Returns:
        bytes: WAV格式的音频数据
    """
    # 生成正弦波
    samples = int(duration * sample_rate)
    t = np.linspace(0, duration, samples, False)
    
    # 生成440Hz的正弦波（A音）
    audio_signal = amplitude * np.sin(2 * np.pi * frequency * t)
    
    # 转换为16位整数
    audio_int16 = (audio_signal * 32767).astype(np.int16)
    
    # 创建WAV文件头
    wav_header = bytearray([
        0x52, 0x49, 0x46, 0x46,  # "RIFF"
        0x00, 0x00, 0x00, 0x00,  # 文件大小（稍后填充）
        0x57, 0x41, 0x56, 0x45,  # "WAVE"
        0x66, 0x6D, 0x74, 0x20,  # "fmt "
        0x10, 0x00, 0x00, 0x00,  # fmt chunk size (16)
        0x01, 0x00,              # audio format (PCM)
        0x01, 0x00,              # channels (1)
        0x80, 0x3E, 0x00, 0x00,  # sample rate (16000)
        0x00, 0x7D, 0x00, 0x00,  # byte rate (16000 * 2 * 1)
        0x02, 0x00,              # block align (2)
        0x10, 0x00,              # bits per sample (16)
        0x64, 0x61, 0x74, 0x61,  # "data"
        0x00, 0x00, 0x00, 0x00,  # data size（稍后填充）
    ])
    
    # 转换为字节
    audio_bytes = audio_int16.tobytes()
    
    # 更新文件大小
    total_size = len(wav_header) + len(audio_bytes) - 8
    wav_header[4:8] = total_size.to_bytes(4, 'little')
    wav_header[40:44] = len(audio_bytes).to_bytes(4, 'little')
    
    return wav_header + audio_bytes


def generate_speech_like_audio(duration=2.0, sample_rate=16000):
    """
    生成类似语音的音频数据（多频率混合）
    """
    samples = int(duration * sample_rate)
    t = np.linspace(0, duration, samples, False)
    
    # 混合多个频率来模拟语音
    frequencies = [200, 400, 800, 1600]  # 语音的基本频率范围
    audio_signal = np.zeros(samples)
    
    for i, freq in enumerate(frequencies):
        amplitude = 0.1 / (i + 1)  # 递减的振幅
        audio_signal += amplitude * np.sin(2 * np.pi * freq * t)
    
    # 添加一些随机噪声来模拟语音的复杂性
    noise = np.random.normal(0, 0.01, samples)
    audio_signal += noise
    
    # 添加包络来模拟语音的动态变化
    envelope = np.exp(-t * 0.5) * (1 + 0.5 * np.sin(2 * np.pi * 2 * t))
    audio_signal *= envelope
    
    # 转换为16位整数
    audio_int16 = (audio_signal * 32767).astype(np.int16)
    
    # 创建WAV文件头
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
    
    # 转换为字节
    audio_bytes = audio_int16.tobytes()
    
    # 更新文件大小
    total_size = len(wav_header) + len(audio_bytes) - 8
    wav_header[4:8] = total_size.to_bytes(4, 'little')
    wav_header[40:44] = len(audio_bytes).to_bytes(4, 'little')
    
    return wav_header + audio_bytes


async def test_real_audio_recognition():
    """测试真实音频识别"""
    print("🎵 测试真实音频识别...")
    
    # 生成不同类型的测试音频
    test_cases = [
        ("正弦波音频", generate_test_audio(duration=2.0, frequency=440, amplitude=0.1)),
        ("类语音音频", generate_speech_like_audio(duration=2.0)),
        ("高振幅音频", generate_test_audio(duration=1.5, frequency=800, amplitude=0.3)),
    ]
    
    async with aiohttp.ClientSession() as session:
        for test_name, audio_data in test_cases:
            print(f"\n🔊 测试 {test_name}...")
            print(f"   音频大小: {len(audio_data)} bytes")
            
            try:
                # 准备表单数据
                data = aiohttp.FormData()
                data.add_field('audio_file', audio_data, 
                               filename=f'{test_name.replace(" ", "_")}.wav', 
                               content_type='audio/wav')
                data.add_field('language', 'zh')
                
                async with session.post("http://localhost:8087/api/voice/recognize", 
                                        data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ 识别成功:")
                        print(f"   识别文本: '{result['text']}'")
                        print(f"   置信度: {result['confidence']:.3f}")
                        print(f"   语言: {result['language']}")
                        print(f"   时长: {result['duration']:.2f}秒")
                        
                        # 显示音频统计信息
                        if 'processing_info' in result and 'audio_stats' in result['processing_info']:
                            stats = result['processing_info']['audio_stats']
                            print(f"   音频统计: max={stats.get('max_amplitude', 'N/A'):.3f}, "
                                  f"rms={stats.get('rms', 'N/A'):.3f}")
                        
                        if 'debug_saved_path' in result['file_info']:
                            print(f"   调试文件: {result['file_info']['debug_saved_path']}")
                    else:
                        error_text = await response.text()
                        print(f"❌ 识别失败: {response.status}")
                        print(f"   错误信息: {error_text}")
                        
            except Exception as e:
                print(f"❌ 请求失败: {e}")


async def main():
    """主函数"""
    print("🚀 开始真实音频测试")
    print("=" * 60)
    
    await test_real_audio_recognition()
    
    print("\n" + "=" * 60)
    print("📊 测试完成")
    print("📁 请检查 logs/audio/ 目录查看保存的音频文件")
    print("🔍 查看服务器日志了解详细的音频处理信息")


if __name__ == "__main__":
    asyncio.run(main()) 