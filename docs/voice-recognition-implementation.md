# 语音识别功能实现文档

## 概述

本文档详细说明了海螺智能语音交互助手中语音识别功能的实现。该功能基于 Faster-Whisper 模型，提供了高精度的中英文语音识别能力。

## 功能特性

### ✅ 已实现功能

1. **文件上传识别**
   - 支持多种音频格式：WAV, MP3, M4A, AAC, FLAC, OGG, WEBM
   - 最大文件大小：50MB
   - 自动音频格式检测和转换
   - 完整的错误处理和验证

2. **实时 WebSocket 识别**
   - 流式音频处理
   - 实时转录结果返回
   - 连接状态管理和心跳检测
   - 音频缓冲区优化

3. **服务状态监控**
   - 健康检查端点
   - Whisper 模型状态查询
   - 详细的服务信息返回

4. **高级特性**
   - 语音活动检测 (VAD)
   - 多语言支持（中文、英文、自动检测）
   - 置信度评估
   - 结构化日志记录
   - Prometheus 监控集成

## 技术架构

### 核心组件

```
app/
├── api/voice/           # 语音识别 API 路由
│   └── __init__.py     # 主要端点实现
├── models/voice.py     # Pydantic 数据模型
├── services/whisper/   # Whisper 服务封装
│   └── whisper_service.py
└── main.py            # FastAPI 应用入口
```

### 数据流

1. **文件上传流程**:
   ```
   客户端 → FastAPI → 文件验证 → Whisper服务 → 音频处理 → 模型推理 → 结果返回
   ```

2. **WebSocket 流程**:
   ```
   客户端 → WebSocket连接 → 音频缓冲 → 实时处理 → 流式结果 → 客户端
   ```

## API 端点详情

### 1. POST /api/voice/recognize

**功能**: 上传音频文件进行语音识别

**参数**:
- `audio_file`: 音频文件（必需）
- `language`: 语言代码（可选，默认 "zh"）

**响应模型**: `VoiceRecognitionResponse`

**特性**:
- 文件大小限制：50MB
- 支持格式自动检测
- 详细的错误信息
- 处理时间记录

### 2. GET /api/voice/status

**功能**: 获取语音识别服务状态

**响应模型**: `VoiceServiceStatus`

**返回信息**:
- 服务运行状态
- Whisper 模型信息
- 设备和计算类型

### 3. WebSocket /api/voice/ws

**功能**: 实时语音识别

**消息类型**:
- `connection`: 连接状态
- `transcript`: 识别结果
- `error`: 错误信息
- `heartbeat`: 心跳检测

## 实现细节

### 音频处理优化

1. **格式支持**:
   ```python
   supported_types = {
       "audio/wav", "audio/wave", "audio/x-wav",
       "audio/mpeg", "audio/mp3",
       "audio/mp4", "audio/m4a", "audio/x-m4a",
       "audio/aac", "audio/x-aac",
       "audio/flac", "audio/x-flac",
       "audio/ogg", "audio/x-ogg",
       "audio/webm", "video/webm",
       "application/octet-stream"
   }
   ```

2. **音频预处理**:
   - 自动转换为 16kHz 单声道
   - 音频归一化到 [-1, 1] 范围
   - 最小音频长度检查（0.1秒）

3. **VAD 参数优化**:
   ```python
   vad_parameters=dict(
       min_silence_duration_ms=100,
       speech_pad_ms=200,
       threshold=0.3,
       min_speech_duration_ms=100
   )
   ```

### 错误处理策略

1. **输入验证**:
   - 文件存在性检查
   - 文件大小限制
   - MIME 类型验证
   - 服务状态检查

2. **处理异常**:
   - 音频解码失败
   - 模型推理错误
   - 网络连接问题
   - 资源不足

3. **优雅降级**:
   - 格式检测失败时尝试原始 PCM
   - 部分识别结果返回
   - 详细错误信息记录

### 性能优化

1. **模型配置**:
   - 使用 `large-v3` 模型提高精度
   - 自动设备检测（GPU/CPU）
   - 计算类型自动选择

2. **内存管理**:
   - 音频缓冲区管理
   - 及时资源清理
   - 连接池复用

3. **并发处理**:
   - 异步处理架构
   - WebSocket 连接管理
   - 请求队列优化

## 测试和验证

### 测试脚本

提供了完整的测试脚本 `test_voice_api.py`：

```bash
# 运行测试
python test_voice_api.py
```

**测试覆盖**:
- ✅ 服务状态检查
- ✅ 文件上传识别
- ✅ 错误处理验证
- ✅ 响应格式验证

### 手动测试

```bash
# 测试服务状态
curl http://localhost:8087/api/voice/status

# 测试文件上传
curl -X POST "http://localhost:8087/api/voice/recognize" \
  -F "audio_file=@example.wav" \
  -F "language=zh"
```

## 监控和日志

### 日志记录

使用 `structlog` 进行结构化日志记录：

```python
logger.info(
    "语音识别成功",
    text_preview=result["text"][:100],
    confidence=result["confidence"],
    duration=result["duration"],
    language=result["language"]
)
```

### 监控指标

通过 Prometheus 收集的关键指标：
- 请求处理时间
- 识别成功率
- 错误类型分布
- 并发连接数

## 部署说明

### 环境要求

- Python 3.8+
- FastAPI
- Faster-Whisper
- PyTorch (支持 CUDA)
- FFmpeg

### 配置参数

在 `config.env` 中配置：
```bash
# 服务端口
PORT=8087

# Whisper 模型配置
WHISPER_MODEL_SIZE=large-v3
WHISPER_DEVICE=auto
WHISPER_COMPUTE_TYPE=auto

# 文件上传限制
MAX_UPLOAD_SIZE=52428800  # 50MB
```

### 启动服务

```bash
# 开发环境
python -m uvicorn app.main:app --host 0.0.0.0 --port 8087 --reload

# 生产环境
python -m uvicorn app.main:app --host 0.0.0.0 --port 8087 --workers 4
```

## 故障排除

### 常见问题

1. **模型下载失败**
   - 检查网络连接
   - 确认 `models/` 目录权限
   - 手动下载模型文件

2. **音频格式不支持**
   - 安装 FFmpeg
   - 检查音频文件完整性
   - 尝试转换为 WAV 格式

3. **内存不足**
   - 减小模型大小（使用 `base` 或 `small`）
   - 限制并发请求数
   - 增加系统内存

4. **GPU 不可用**
   - 检查 CUDA 安装
   - 验证 PyTorch GPU 支持
   - 降级到 CPU 模式

### 调试技巧

1. **启用详细日志**:
   ```python
   import logging
   logging.getLogger("faster_whisper").setLevel(logging.DEBUG)
   ```

2. **检查模型状态**:
   ```bash
   curl http://localhost:8087/api/voice/status
   ```

3. **测试音频处理**:
   ```python
   from app.services.whisper.whisper_service import whisper_service
   result = await whisper_service.transcribe(audio_data)
   ```

## 未来改进

### 计划功能

1. **多模型支持**
   - 支持不同大小的 Whisper 模型
   - 动态模型切换
   - 模型性能对比

2. **高级特性**
   - 说话人分离
   - 情感识别
   - 语音增强

3. **性能优化**
   - 模型量化
   - 批处理支持
   - 缓存机制

4. **集成功能**
   - 实时翻译
   - 语音合成联动
   - 对话系统集成

### 技术债务

1. **代码重构**
   - 提取公共音频处理逻辑
   - 优化错误处理流程
   - 改进测试覆盖率

2. **文档完善**
   - API 文档自动生成
   - 性能基准测试
   - 部署最佳实践

## 总结

语音识别功能已成功实现并集成到海螺智能语音交互助手中。该实现具有以下优势：

- ✅ **功能完整**: 支持文件上传和实时识别
- ✅ **性能优秀**: 基于 Faster-Whisper 高性能模型
- ✅ **稳定可靠**: 完善的错误处理和监控
- ✅ **易于使用**: 简洁的 API 设计和详细文档
- ✅ **可扩展性**: 模块化架构便于功能扩展

该实现为后续的语音交互功能奠定了坚实的基础。 