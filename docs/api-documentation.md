# API 文档

## 语音识别 API

### 概述

海螺智能语音交互助手提供了强大的语音识别功能，基于 Faster-Whisper 模型实现。支持多种音频格式的实时转录和文件上传转录。

### 基础信息

- **基础URL**: `http://localhost:8087/api/voice`
- **支持格式**: WAV, MP3, M4A, AAC, FLAC, OGG, WEBM
- **最大文件大小**: 50MB
- **推荐音频参数**: 16kHz 采样率，单声道

---

## OpenAI 兼容 API

### 概述

为了方便集成，我们提供了与 OpenAI Audio API 完全兼容的接口。您可以直接使用 OpenAI 的客户端库或工具来访问我们的语音识别服务。

### 基础信息

- **基础URL**: `http://localhost:8087/v1/audio`
- **兼容版本**: OpenAI Audio API v1
- **支持格式**: mp3, mp4, mpeg, mpga, m4a, wav, webm
- **最大文件大小**: 25MB（符合 OpenAI 标准）
- **支持模型**: whisper-1

---

### 音频转录

将音频转录为输入语言的文本，完全兼容 OpenAI Audio API。

**端点**: `POST /v1/audio/transcriptions`

**请求参数**:
- `file` (文件，必需): 要转录的音频文件，最大 25MB
- `model` (字符串，必需): 使用的模型 ID，目前支持 "whisper-1"
- `prompt` (字符串，可选): 可选的提示文本，用于指导模型风格
- `response_format` (字符串，可选): 响应格式，默认 "json"
  - `json`: JSON 格式响应
  - `text`: 纯文本响应
  - `srt`: SRT 字幕格式
  - `verbose_json`: 详细 JSON 格式（包含时长、语言等）
  - `vtt`: WebVTT 字幕格式
- `temperature` (数字，可选): 采样温度，0-1 之间，默认 0
- `language` (字符串，可选): 输入音频的语言，ISO-639-1 格式

**请求示例** (curl):
```bash
# JSON 格式响应
curl -X POST "http://localhost:8087/v1/audio/transcriptions" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.wav" \
  -F "model=whisper-1" \
  -F "response_format=json"

# 文本格式响应
curl -X POST "http://localhost:8087/v1/audio/transcriptions" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.wav" \
  -F "model=whisper-1" \
  -F "response_format=text"

# 详细 JSON 格式
curl -X POST "http://localhost:8087/v1/audio/transcriptions" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.wav" \
  -F "model=whisper-1" \
  -F "response_format=verbose_json" \
  -F "language=zh"
```

**响应示例**:

#### JSON 格式 (`response_format=json`)
```json
{
  "text": "你好，这是一段测试语音。"
}
```

#### 详细 JSON 格式 (`response_format=verbose_json`)
```json
{
  "task": "transcribe",
  "language": "zh",
  "duration": 3.2,
  "text": "你好，这是一段测试语音。",
  "segments": null
}
```

#### 文本格式 (`response_format=text`)
```
你好，这是一段测试语音。
```

#### SRT 字幕格式 (`response_format=srt`)
```
1
00:00:00,000 --> 00:00:03,200
你好，这是一段测试语音。

```

#### WebVTT 字幕格式 (`response_format=vtt`)
```
WEBVTT

00:00:00.000 --> 00:00:03.200
你好，这是一段测试语音。

```

**错误响应格式**:
```json
{
  "error": {
    "message": "Invalid model: 'gpt-4'. Currently only 'whisper-1' is supported.",
    "type": "invalid_request_error",
    "param": "model",
    "code": null
  }
}
```

**状态码**:
- `200`: 转录成功
- `400`: 请求参数错误
- `413`: 文件过大（超过 25MB）
- `503`: 服务不可用

### OpenAI 客户端库使用示例

#### Python (openai 库)
```python
import openai

# 配置客户端指向本地服务
client = openai.OpenAI(
    api_key="dummy-key",  # 本地服务不需要真实 API key
    base_url="http://localhost:8087/v1"
)

# 转录音频文件
with open("audio.wav", "rb") as audio_file:
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="json"
    )
    print(transcript.text)

# 详细格式
with open("audio.wav", "rb") as audio_file:
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="verbose_json",
        language="zh"
    )
    print(f"语言: {transcript.language}")
    print(f"时长: {transcript.duration}秒")
    print(f"文本: {transcript.text}")
```

#### JavaScript/Node.js
```javascript
import OpenAI from 'openai';
import fs from 'fs';

const openai = new OpenAI({
  apiKey: 'dummy-key',  // 本地服务不需要真实 API key
  baseURL: 'http://localhost:8087/v1'
});

async function transcribeAudio() {
  const transcription = await openai.audio.transcriptions.create({
    file: fs.createReadStream('audio.wav'),
    model: 'whisper-1',
    response_format: 'json'
  });
  
  console.log(transcription.text);
}

transcribeAudio();
```

---

## 端点详情

### 1. 获取服务状态

获取语音识别服务的当前状态和健康信息。

**端点**: `GET /api/voice/status`

**响应示例**:
```json
{
  "status": "active",
  "service": "voice_recognition", 
  "message": "语音识别服务正常运行",
  "whisper_service": {
    "service": "whisper",
    "status": "ready",
    "model_loaded": true,
    "model_size": "large-v3",
    "device": "cuda",
    "compute_type": "auto"
  }
}
```

**状态码**:
- `200`: 服务正常
- `503`: 服务不可用

---

### 2. 语音识别（文件上传）

上传音频文件进行语音识别转录。

**端点**: `POST /api/voice/recognize`

**请求参数**:
- `audio_file` (文件，必需): 要识别的音频文件
- `language` (字符串，可选): 语言代码，默认为 "zh"
  - `zh`: 中文
  - `en`: 英文  
  - `auto`: 自动检测

**请求示例** (curl):
```bash
curl -X POST "http://localhost:8087/api/voice/recognize" \
  -F "audio_file=@example.wav" \
  -F "language=zh"
```

**响应示例**:
```json
{
  "success": true,
  "text": "你好，这是一段测试语音。",
  "confidence": 0.95,
  "language": "zh",
  "duration": 3.2,
  "file_info": {
    "filename": "example.wav",
    "content_type": "audio/wav",
    "size_bytes": 51200
  },
  "processing_info": {
    "segments": 1,
    "requested_language": "zh",
    "processing_time": "2024-01-01T12:00:00.000Z"
  }
}
```

**响应字段说明**:
- `success`: 识别是否成功
- `text`: 识别出的文本内容
- `confidence`: 识别置信度 (0-1)
- `language`: 检测到的语言代码
- `duration`: 音频时长（秒）
- `file_info`: 上传文件的信息
- `processing_info`: 处理过程信息

**状态码**:
- `200`: 识别成功
- `400`: 请求参数错误（文件为空、格式不支持等）
- `413`: 文件过大
- `500`: 服务器内部错误
- `503`: 服务不可用

---

### 3. WebSocket 实时语音识别

通过 WebSocket 连接进行实时语音识别。

**端点**: `WebSocket /api/voice/ws`

**连接示例** (JavaScript):
```javascript
const ws = new WebSocket('ws://localhost:8087/api/voice/ws');

ws.onopen = function() {
    console.log('WebSocket 连接已建立');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('收到消息:', data);
};

// 发送音频数据
ws.send(audioBlob);

// 发送心跳
ws.send(JSON.stringify({
    type: "ping",
    timestamp: new Date().toISOString()
}));
```

**消息类型**:

#### 连接消息
```json
{
  "type": "connection",
  "status": "connected", 
  "message": "WebSocket连接成功",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

#### 转录结果
```json
{
  "type": "transcript",
  "text": "识别的文本内容",
  "confidence": 0.95,
  "language": "zh",
  "duration": 2.1,
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

#### 错误消息
```json
{
  "type": "error",
  "message": "错误描述",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

#### 心跳消息
```json
{
  "type": "heartbeat",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

---

## 错误处理

### 常见错误码

| 状态码 | 错误类型 | 描述 | 解决方案 |
|--------|----------|------|----------|
| 400 | Bad Request | 请求参数错误 | 检查文件格式和参数 |
| 413 | Payload Too Large | 文件过大 | 压缩文件或分段上传 |
| 415 | Unsupported Media Type | 不支持的文件格式 | 使用支持的音频格式 |
| 503 | Service Unavailable | 服务不可用 | 等待服务启动或重启 |

### 错误响应格式

```json
{
  "detail": "具体错误信息"
}
```

---

## 使用示例

### Python 示例

```python
import aiohttp
import asyncio

async def recognize_audio(file_path):
    async with aiohttp.ClientSession() as session:
        with open(file_path, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('audio_file', f, 
                          filename='audio.wav',
                          content_type='audio/wav')
            data.add_field('language', 'zh')
            
            async with session.post(
                'http://localhost:8087/api/voice/recognize',
                data=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"识别结果: {result['text']}")
                    return result
                else:
                    print(f"错误: {response.status}")
                    return None

# 使用示例
asyncio.run(recognize_audio('example.wav'))
```

### JavaScript 示例

```javascript
async function recognizeAudio(audioFile) {
    const formData = new FormData();
    formData.append('audio_file', audioFile);
    formData.append('language', 'zh');
    
    try {
        const response = await fetch('http://localhost:8087/api/voice/recognize', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log('识别结果:', result.text);
            return result;
        } else {
            console.error('错误:', response.status);
            return null;
        }
    } catch (error) {
        console.error('请求失败:', error);
        return null;
    }
}
```

---

## 性能优化建议

### 音频文件优化
1. **采样率**: 推荐使用 16kHz，平衡质量和性能
2. **声道**: 单声道可减少处理时间
3. **格式**: WAV 格式处理最快，MP3 压缩率高
4. **时长**: 建议单次识别不超过 10 分钟

### 批量处理
- 对于大量文件，建议使用异步并发处理
- 控制并发数量避免服务器过载
- 实现重试机制处理临时错误

### WebSocket 使用
- 发送音频块大小建议 32KB-64KB
- 实现心跳机制保持连接
- 处理网络断线重连

---

## 监控和日志

### 日志级别
- `INFO`: 正常操作日志
- `WARNING`: 警告信息（如不支持的格式）
- `ERROR`: 错误信息（如识别失败）

### 监控指标
- 识别成功率
- 平均响应时间
- 并发连接数
- 错误率统计

可通过 `/metrics` 端点获取 Prometheus 格式的监控数据。 