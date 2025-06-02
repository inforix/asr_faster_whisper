# OpenAI Audio API 兼容性指南

## 概述

海螺智能语音交互助手现在提供与 OpenAI Audio API 完全兼容的接口，让您可以无缝地将现有的 OpenAI 集成迁移到我们的本地服务。

## 主要特性

- ✅ **完全兼容**: 与 OpenAI Audio API v1 100% 兼容
- ✅ **多种格式**: 支持 JSON、文本、SRT、VTT 等多种响应格式
- ✅ **客户端库支持**: 可直接使用 OpenAI 官方客户端库
- ✅ **错误处理**: 完全兼容的错误响应格式
- ✅ **参数验证**: 严格的参数验证和错误提示

## 快速开始

### 1. 基本使用

```bash
curl -X POST "http://localhost:8087/v1/audio/transcriptions" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_audio.wav" \
  -F "model=whisper-1"
```

### 2. 使用 OpenAI Python 库

```python
import openai

# 配置客户端
client = openai.OpenAI(
    api_key="dummy-key",  # 本地服务不需要真实 API key
    base_url="http://localhost:8087/v1"
)

# 转录音频
with open("audio.wav", "rb") as audio_file:
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
    print(transcript.text)
```

## API 参考

### 端点

```
POST /v1/audio/transcriptions
```

### 请求参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `file` | 文件 | ✅ | 音频文件，最大 25MB |
| `model` | 字符串 | ✅ | 模型 ID，目前支持 "whisper-1" |
| `prompt` | 字符串 | ❌ | 可选的提示文本 |
| `response_format` | 字符串 | ❌ | 响应格式，默认 "json" |
| `temperature` | 数字 | ❌ | 采样温度，0-1 之间 |
| `language` | 字符串 | ❌ | 输入音频语言，ISO-639-1 格式 |

### 支持的响应格式

| 格式 | 描述 | 示例 |
|------|------|------|
| `json` | 标准 JSON 响应 | `{"text": "转录文本"}` |
| `text` | 纯文本响应 | `转录文本` |
| `verbose_json` | 详细 JSON，包含元数据 | `{"task": "transcribe", "language": "zh", ...}` |
| `srt` | SRT 字幕格式 | SubRip 字幕文件 |
| `vtt` | WebVTT 字幕格式 | WebVTT 字幕文件 |

### 支持的音频格式

- mp3, mp4, mpeg, mpga, m4a, wav, webm

## 迁移指南

### 从 OpenAI API 迁移

如果您已经在使用 OpenAI Audio API，迁移非常简单：

#### 1. 更改 base_url

**之前**:
```python
client = openai.OpenAI(api_key="your-openai-key")
```

**现在**:
```python
client = openai.OpenAI(
    api_key="dummy-key",
    base_url="http://localhost:8087/v1"
)
```

#### 2. 其他代码保持不变

所有其他代码都可以保持不变，包括：
- 方法调用
- 参数传递
- 响应处理
- 错误处理

### 环境变量配置

您也可以通过环境变量配置：

```bash
export OPENAI_API_KEY="dummy-key"
export OPENAI_BASE_URL="http://localhost:8087/v1"
```

然后在代码中：

```python
import openai
client = openai.OpenAI()  # 自动使用环境变量
```

## 高级用法

### 1. 批量处理

```python
import asyncio
import openai
from pathlib import Path

async def transcribe_files(file_paths):
    client = openai.OpenAI(
        api_key="dummy-key",
        base_url="http://localhost:8087/v1"
    )
    
    tasks = []
    for file_path in file_paths:
        with open(file_path, "rb") as audio_file:
            task = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json"
            )
            tasks.append(task)
    
    return await asyncio.gather(*tasks)
```

### 2. 字幕生成

```python
def generate_subtitles(audio_file_path, output_format="srt"):
    client = openai.OpenAI(
        api_key="dummy-key",
        base_url="http://localhost:8087/v1"
    )
    
    with open(audio_file_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format=output_format
        )
    
    # 保存字幕文件
    output_path = f"{audio_file_path.stem}.{output_format}"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(response)
    
    return output_path
```

### 3. 多语言处理

```python
def transcribe_multilingual(audio_file_path):
    client = openai.OpenAI(
        api_key="dummy-key",
        base_url="http://localhost:8087/v1"
    )
    
    # 自动检测语言
    with open(audio_file_path, "rb") as audio_file:
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json"
        )
    
    print(f"检测到的语言: {result.language}")
    print(f"转录文本: {result.text}")
    print(f"音频时长: {result.duration}秒")
    
    return result
```

## 错误处理

### 常见错误类型

| 错误类型 | 描述 | 解决方案 |
|----------|------|----------|
| `invalid_request_error` | 请求参数错误 | 检查参数格式和值 |
| `service_unavailable_error` | 服务不可用 | 等待服务启动 |
| `server_error` | 服务器内部错误 | 检查日志，重试请求 |

### 错误处理示例

```python
import openai
from openai import OpenAIError

client = openai.OpenAI(
    api_key="dummy-key",
    base_url="http://localhost:8087/v1"
)

try:
    with open("audio.wav", "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        print(transcript.text)
        
except OpenAIError as e:
    print(f"OpenAI API 错误: {e}")
    if hasattr(e, 'response'):
        print(f"状态码: {e.response.status_code}")
        print(f"错误详情: {e.response.json()}")
        
except Exception as e:
    print(f"其他错误: {e}")
```

## 性能优化

### 1. 文件大小优化

```python
def optimize_audio_for_transcription(input_path, output_path):
    """优化音频文件以提高转录性能"""
    import subprocess
    
    # 使用 ffmpeg 优化音频
    cmd = [
        "ffmpeg", "-i", input_path,
        "-ar", "16000",  # 16kHz 采样率
        "-ac", "1",      # 单声道
        "-c:a", "pcm_s16le",  # 16位 PCM
        output_path
    ]
    
    subprocess.run(cmd, check=True)
    return output_path
```

### 2. 并发控制

```python
import asyncio
from asyncio import Semaphore

async def transcribe_with_concurrency_limit(file_paths, max_concurrent=3):
    semaphore = Semaphore(max_concurrent)
    
    async def transcribe_single(file_path):
        async with semaphore:
            # 转录逻辑
            pass
    
    tasks = [transcribe_single(path) for path in file_paths]
    return await asyncio.gather(*tasks)
```

## 监控和调试

### 1. 启用详细日志

```python
import logging
import openai

# 启用 OpenAI 库的调试日志
logging.basicConfig(level=logging.DEBUG)
openai.log = "debug"
```

### 2. 性能监控

```python
import time
import openai

def transcribe_with_timing(audio_file_path):
    client = openai.OpenAI(
        api_key="dummy-key",
        base_url="http://localhost:8087/v1"
    )
    
    start_time = time.time()
    
    with open(audio_file_path, "rb") as audio_file:
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json"
        )
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    print(f"音频时长: {result.duration}秒")
    print(f"处理时间: {processing_time:.2f}秒")
    print(f"实时率: {result.duration / processing_time:.2f}x")
    
    return result
```

## 常见问题

### Q: 为什么需要设置 api_key？
A: 虽然本地服务不需要真实的 API key，但 OpenAI 客户端库要求提供这个参数。您可以使用任何非空字符串。

### Q: 支持流式转录吗？
A: 目前不支持流式转录，但您可以使用我们的 WebSocket API 进行实时转录。

### Q: 文件大小限制是多少？
A: 为了与 OpenAI API 保持兼容，限制为 25MB。如需处理更大文件，请使用我们的原生 API。

### Q: 支持哪些语言？
A: 支持 Whisper 模型支持的所有语言，包括中文、英文、日文、韩文等 100+ 种语言。

## 技术支持

如果您在使用过程中遇到问题，请：

1. 检查服务是否正常运行：`curl http://localhost:8087/health`
2. 查看服务日志获取详细错误信息
3. 确认音频文件格式和大小符合要求
4. 验证网络连接和端口配置

更多技术支持，请参考项目文档或提交 Issue。 