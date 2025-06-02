"""
应用配置管理
"""

from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""
    
    # 基础配置
    ENVIRONMENT: str = Field(default="development", description="运行环境")
    DEBUG: bool = Field(default=False, description="调试模式")
    SECRET_KEY: str = Field(default="your-secret-key", description="应用密钥")
    
    # OpenMP库冲突修复 (macOS)
    KMP_DUPLICATE_LIB_OK: str = Field(default="TRUE", description="OpenMP库冲突修复")
    
    # 服务器配置
    HOST: str = Field(default="127.0.0.1", description="服务器地址")
    PORT: int = Field(default=8000, description="服务器端口")
    WORKERS: int = Field(default=1, description="工作进程数")
    
    # CORS配置
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "https://hailuo.shmtu.edu.cn"],
        description="允许的跨域源"
    )
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "hailuo.shmtu.edu.cn"],
        description="允许的主机"
    )
    
    # Whisper配置
    WHISPER_MODEL_SIZE: str = Field(
        default="large-v3",
        description="Whisper模型大小"
    )
    WHISPER_DEVICE: str = Field(default="auto", description="Whisper设备")
    WHISPER_COMPUTE_TYPE: str = Field(
        default="float16",
        description="Whisper计算类型"
    )
    WHISPER_CPU_THREADS: int = Field(default=0, description="CPU线程数")
    WHISPER_NUM_WORKERS: int = Field(default=1, description="Whisper工作进程数")
    
    # TTS配置
    TTS_MODEL_NAME: str = Field(
        default="tts_models/multilingual/multi-dataset/xtts_v2",
        description="TTS模型名称"
    )
    TTS_DEVICE: str = Field(default="auto", description="TTS设备")
    TTS_USE_CUDA: bool = Field(default=True, description="是否使用CUDA")
    TTS_NUM_WORKERS: int = Field(default=1, description="TTS工作进程数")
    
    # 外部服务配置
    ASR_SERVICE_URL: str = Field(
        default="http://localhost:8001",
        description="ASR服务地址"
    )
    TTS_SERVICE_URL: str = Field(
        default="http://localhost:8002",
        description="TTS服务地址"
    )
    
    # 文件存储配置
    UPLOAD_DIR: str = Field(default="./uploads", description="上传目录")
    MODEL_CACHE_DIR: str = Field(default="./models", description="模型缓存目录")
    AUDIO_CACHE_DIR: str = Field(default="./audio_cache", description="音频缓存目录")
    MAX_FILE_SIZE: int = Field(default=50 * 1024 * 1024, description="最大文件大小")
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式"
    )
    LOG_FILE: Optional[str] = Field(default=None, description="日志文件")
    
    # 监控配置
    ENABLE_METRICS: bool = Field(default=True, description="启用监控")
    METRICS_PORT: int = Field(default=9090, description="监控端口")
    
    # 性能配置
    MAX_CONCURRENT_REQUESTS: int = Field(
        default=10,
        description="最大并发请求数"
    )
    REQUEST_TIMEOUT: int = Field(default=30, description="请求超时时间")
    WEBSOCKET_TIMEOUT: int = Field(default=300, description="WebSocket超时时间")
    
    # 安全配置
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60,
        description="每分钟请求限制"
    )
    ENABLE_RATE_LIMIT: bool = Field(default=True, description="启用限流")
    
    # 功能开关
    ENABLE_TTS: bool = Field(default=True, description="启用TTS功能")
    ENABLE_VOICE_CLONING: bool = Field(default=True, description="启用语音克隆")
    ENABLE_EMOTION_CONTROL: bool = Field(default=True, description="启用情感控制")
    ENABLE_MULTI_LANGUAGE: bool = Field(default=True, description="启用多语言")
    
    class Config:
        env_file = "config.env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # 设置OpenMP环境变量以避免库冲突
        import os
        os.environ['KMP_DUPLICATE_LIB_OK'] = self.KMP_DUPLICATE_LIB_OK
        
        # 自动检测设备
        if self.WHISPER_DEVICE == "auto":
            self.WHISPER_DEVICE = self._detect_device()
        
        if self.TTS_DEVICE == "auto":
            self.TTS_DEVICE = self._detect_device()
    
    def _detect_device(self) -> str:
        """自动检测可用设备"""
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return "mps"
            else:
                return "cpu"
        except ImportError:
            return "cpu"
    
    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def database_url(self) -> str:
        """数据库连接URL"""
        # 如果需要数据库，可以在这里配置
        return "sqlite:///./hailuo.db"


# 创建全局配置实例
settings = Settings() 