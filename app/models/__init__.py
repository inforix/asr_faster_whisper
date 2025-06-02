"""
数据模型包
"""

from .voice import *
from .openai_compat import *

__all__ = [
    "VoiceRecognitionResponse",
    "VoiceServiceStatus", 
    "ErrorResponse",
    "OpenAITranscriptionRequest",
    "OpenAITranscriptionResponse",
] 