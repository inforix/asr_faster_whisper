"""
Faster-Whisper语音识别服务
"""

import io
import logging
from typing import Any, Dict, Optional

import numpy as np
from faster_whisper import WhisperModel
from pydub import AudioSegment

logger = logging.getLogger(__name__)


class WhisperService:
    """Faster-Whisper语音识别服务"""
    
    def __init__(self):
        """初始化Whisper服务"""
        self.model: Optional[WhisperModel] = None
        self.is_initialized = False
        self.model_size = "large-v3"  # 升级到base模型提高精度
        self.device = "auto"  # 自动检测GPU/CPU
        self.compute_type = "auto"  # 自动选择合适的计算类型
    
    async def initialize(self) -> None:
        """初始化Whisper服务"""
        try:
            logger.info("初始化Faster-Whisper服务...")
            logger.info(f"模型大小: {self.model_size}, 设备: {self.device}")
            
            # 尝试初始化Faster-Whisper模型
            try:
                self.model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                    download_root="./models",  # 模型下载目录
                    local_files_only=False  # 允许下载模型
                )
            except Exception as download_error:
                logger.warning(f"下载模型失败，尝试使用更小的模型: {download_error}")
                # 如果下载失败，尝试使用tiny模型
                self.model_size = "tiny"
                logger.info(f"回退到更小的模型: {self.model_size}")
                self.model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                    download_root="./models",
                    local_files_only=False
                )
            
            self.is_initialized = True
            logger.info("Faster-Whisper服务初始化完成")
            
            # 测试模型
            await self._test_model()
            
        except Exception as e:
            logger.error(f"Faster-Whisper服务初始化失败: {e}")
            self.is_initialized = False
            raise
    
    async def _test_model(self) -> None:
        """测试模型是否正常工作"""
        try:
            # 创建一个简短的静音测试音频
            test_audio = np.zeros(16000, dtype=np.float32)  # 1秒静音
            segments, info = self.model.transcribe(test_audio, language="zh")
            logger.info(f"模型测试成功，检测语言: {info.language}")
        except Exception as e:
            logger.warning(f"模型测试失败: {e}")
    
    async def cleanup(self) -> None:
        """清理资源"""
        try:
            logger.info("清理Whisper服务资源...")
            if self.model:
                # Faster-Whisper会自动清理资源
                self.model = None
            self.is_initialized = False
            logger.info("Whisper服务资源清理完成")
        except Exception as e:
            logger.error(f"Whisper服务资源清理失败: {e}")
    
    async def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            "service": "whisper",
            "status": "ready" if self.is_initialized else "not_ready",
            "model_loaded": self.model is not None,
            "model_size": self.model_size,
            "device": self.device,
            "compute_type": self.compute_type,
        }
    
    async def transcribe(self, audio_data: bytes, realtime_mode: bool = True) -> Dict[str, Any]:
        """转录音频"""
        if not self.is_initialized or not self.model:
            raise RuntimeError("Whisper服务未初始化")
        
        try:
            # 检查音频数据大小
            if len(audio_data) < 100:  # 太小的音频块直接跳过
                logger.debug(f"音频数据太小，跳过处理: {len(audio_data)} bytes")
                return {
                    "text": "",
                    "confidence": 0.0,
                    "language": "zh",
                    "duration": 0.0
                }
            
            # 处理音频数据
            audio_array = await self._process_audio(audio_data)
            
            if audio_array is None or len(audio_array) == 0:
                return {
                    "text": "",
                    "confidence": 0.0,
                    "language": "zh",
                    "duration": 0.0
                }
            
            # 检查音频长度（至少需要0.1秒的音频）
            min_samples = int(0.1 * 16000)  # 0.1秒 * 16000Hz
            if len(audio_array) < min_samples:
                logger.debug(f"音频太短，跳过处理: {len(audio_array)} samples")
                return {
                    "text": "",
                    "confidence": 0.0,
                    "language": "zh",
                    "duration": len(audio_array) / 16000
                }
            
            # 计算音频统计信息用于调试
            audio_max = np.max(np.abs(audio_array))
            audio_rms = np.sqrt(np.mean(audio_array ** 2))
            logger.debug(f"音频统计: 长度={len(audio_array)}, 最大值={audio_max:.3f}, RMS={audio_rms:.3f}")
            
            # 根据模式选择VAD参数
            if realtime_mode:
                # 实时模式：非常宽松的VAD参数，主要过滤明显的静音
                vad_params = dict(
                    min_silence_duration_ms=2000,  # 2秒静音才认为是静音段
                    speech_pad_ms=1000,            # 1秒的语音填充
                    threshold=0.05,                # 非常低的阈值
                    min_speech_duration_ms=30      # 30ms最小语音时长
                )
                # 对于实时模式，根据音频能量决定是否使用VAD
                if audio_max < 0.001:  # 音频信号极弱
                    logger.debug("音频信号极弱，禁用VAD过滤")
                    use_vad = False
                elif audio_max < 0.01:  # 音频信号较弱，使用宽松VAD
                    logger.debug("音频信号较弱，使用宽松VAD")
                    use_vad = True
                else:
                    # 音频信号正常，使用标准VAD
                    logger.debug("音频信号正常，使用标准VAD")
                    use_vad = True
            else:
                # 文件模式：稍微严格一些的VAD参数
                vad_params = dict(
                    min_silence_duration_ms=1500,  # 1.5秒静音检测
                    speech_pad_ms=800,             # 800ms填充
                    threshold=0.1,                 # 较低的阈值
                    min_speech_duration_ms=50      # 50ms最小语音时长
                )
                # 文件模式根据音频特征决定VAD使用
                if audio_max < 0.001:
                    logger.debug("文件音频信号极弱，禁用VAD")
                    use_vad = False
                else:
                    logger.debug("文件模式使用VAD")
                    use_vad = True
            
            logger.debug(f"VAD配置: enabled={use_vad}, params={vad_params}")
            
            # 使用Faster-Whisper进行转录
            segments, info = self.model.transcribe(
                audio_array,
                language="zh",  # 指定中文
                beam_size=5,
                best_of=5,
                temperature=0.0,
                condition_on_previous_text=False,
                vad_filter=use_vad,  # 根据条件启用/禁用VAD
                vad_parameters=vad_params if use_vad else None
            )
            
            # 收集所有转录片段
            transcription_text = ""
            total_confidence = 0.0
            segment_count = 0
            
            for segment in segments:
                transcription_text += segment.text
                total_confidence += segment.avg_logprob
                segment_count += 1
                logger.debug(f"片段: {segment.text} (置信度: {segment.avg_logprob:.3f})")
            
            # 计算平均置信度
            avg_confidence = total_confidence / segment_count if segment_count > 0 else 0.0
            
            # 转换置信度到0-1范围
            confidence = max(0.0, min(1.0, (avg_confidence + 1.0) / 2.0))
            
            result = {
                "text": transcription_text.strip(),
                "confidence": confidence,
                "language": info.language,
                "duration": info.duration,
                "segments": segment_count,
                "audio_stats": {
                    "max_amplitude": float(audio_max),
                    "rms": float(audio_rms),
                    "samples": len(audio_array)
                }
            }
            
            if transcription_text.strip():  # 只有非空结果才记录
                logger.info(f"转录完成: '{result['text'][:50]}...' (置信度: {confidence:.3f}, VAD: {use_vad})")
            else:
                logger.debug(f"无语音内容，时长: {info.duration:.2f}秒, VAD: {use_vad}, 音频统计: max={audio_max:.3f}, rms={audio_rms:.3f}")
            
            return result
            
        except Exception as e:
            logger.error(f"音频转录失败: {e}")
            raise RuntimeError(f"音频转录失败: {e}")
    
    async def _process_audio(self, audio_data: bytes) -> Optional[np.ndarray]:
        """处理音频数据，转换为Whisper需要的格式"""
        try:
            # 使用pydub处理音频
            audio_io = io.BytesIO(audio_data)
            
            # 尝试不同的音频格式，包括M4A
            audio_segment = None
            formats_to_try = ['webm', 'ogg', 'wav', 'mp3', 'm4a', 'mp4', 'aac', 'flac']
            
            for format_name in formats_to_try:
                try:
                    audio_io.seek(0)
                    audio_segment = AudioSegment.from_file(audio_io, format=format_name)
                    logger.debug(f"成功解析音频格式: {format_name}")
                    break
                except Exception as e:
                    logger.debug(f"尝试格式 {format_name} 失败: {e}")
                    continue
            
            if audio_segment is None:
                # 如果所有格式都失败，可能是音频片段，尝试作为原始PCM数据处理
                logger.debug("尝试作为原始PCM数据处理")
                return await self._process_raw_audio(audio_data)
            
            # 获取原始音频信息
            duration = len(audio_segment) / 1000
            logger.debug(f"原始音频: {audio_segment.frame_rate}Hz, "
                        f"{audio_segment.channels}声道, {duration:.2f}秒")
            
            # 转换为16kHz单声道
            audio_segment = audio_segment.set_frame_rate(16000).set_channels(1)
            
            # 转换为numpy数组
            audio_array = np.array(audio_segment.get_array_of_samples(), dtype=np.float32)
            
            # 归一化到[-1, 1]范围
            if audio_segment.sample_width == 1:  # 8-bit
                audio_array = (audio_array - 128) / 128.0
            elif audio_segment.sample_width == 2:  # 16-bit
                audio_array = audio_array / 32768.0
            elif audio_segment.sample_width == 4:  # 32-bit
                audio_array = audio_array / 2147483648.0
            else:
                # 自动归一化
                max_val = np.max(np.abs(audio_array))
                if max_val > 0:
                    audio_array = audio_array / max_val
            
            logger.debug(f"音频处理完成: 长度={len(audio_array)}, "
                        f"范围=[{np.min(audio_array):.3f}, {np.max(audio_array):.3f}]")
            return audio_array
            
        except Exception as e:
            logger.error(f"音频处理失败: {e}")
            return None
    
    async def _process_raw_audio(self, audio_data: bytes) -> Optional[np.ndarray]:
        """处理原始音频数据（当无法识别格式时的备用方案）"""
        try:
            # 尝试作为16位PCM数据处理
            if len(audio_data) % 2 != 0:
                # 如果字节数是奇数，去掉最后一个字节
                audio_data = audio_data[:-1]
            
            # 转换为16位整数数组
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
            
            # 归一化到[-1, 1]范围
            audio_array = audio_array / 32768.0
            
            logger.debug(f"原始PCM处理: 长度={len(audio_array)}, "
                        f"范围=[{np.min(audio_array):.3f}, {np.max(audio_array):.3f}]")
            
            return audio_array
            
        except Exception as e:
            logger.debug(f"原始PCM处理失败: {e}")
            return None


# 全局服务实例
whisper_service = WhisperService() 
