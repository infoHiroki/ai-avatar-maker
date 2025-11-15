"""
ElevenLabs API - 音声生成（声クローン）

機能:
  - 音声生成（声クローン使用）
  - Cloudinaryアップロード
  - エラーハンドリング

参考: resources/声のクローニング実装ガイド.md
"""

import tempfile
import os
from typing import Tuple, Optional
from pathlib import Path

from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
import cloudinary
import cloudinary.uploader
from mutagen import File as MutagenFile

from ..models.schemas import GeneratedAudio, CloudinaryConfig
from ..utils.errors import AudioGenerationError, CloudinaryError
from ..utils.logger import get_logger
from ..utils.config import get_config

logger = get_logger(__name__)


class ElevenLabsClient:
    """
    ElevenLabs API クライアント

    音声を生成し、Cloudinaryにアップロード

    Example:
        >>> client = ElevenLabsClient(
        ...     api_key="sk_xxxxx",
        ...     voice_id="voice_xxxxx"
        ... )
        >>> audio, err = client.generate("こんにちは")
        >>> if not err:
        ...     print(f"音声URL: {audio.audio_url}")
    """

    def __init__(
        self,
        api_key: str,
        voice_id: str,
        cloudinary_config: Optional[CloudinaryConfig] = None
    ):
        """
        初期化

        Args:
            api_key: ElevenLabs APIキー
            voice_id: 声クローンID
            cloudinary_config: Cloudinary設定
        """
        self.api_key = api_key
        self.voice_id = voice_id
        self.cloudinary_config = cloudinary_config

        # ElevenLabsクライアント初期化
        self.client = ElevenLabs(api_key=api_key)

        # Cloudinary設定
        if cloudinary_config:
            cloudinary.config(
                cloud_name=cloudinary_config.cloud_name,
                api_key=cloudinary_config.api_key,
                api_secret=cloudinary_config.api_secret
            )

    def generate(
        self,
        text: str,
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        use_speaker_boost: bool = True
    ) -> Tuple[Optional[GeneratedAudio], Optional[Exception]]:
        """
        音声生成

        Args:
            text: 生成するテキスト
            stability: 安定性 (0.0-1.0)
            similarity_boost: 類似度ブースト (0.0-1.0)
            style: スタイル (0.0-1.0)
            use_speaker_boost: スピーカーブースト

        Returns:
            (audio, error):
                - 成功: (GeneratedAudio, None)
                - 失敗: (None, Exception)

        Example:
            >>> audio, err = client.generate("こんにちは、テストです")
            >>> if not err:
            ...     print(f"音声URL: {audio.audio_url}")
        """
        try:
            logger.info(f"音声生成開始: {len(text)}文字")

            # 音声生成
            response = self.client.text_to_speech.convert(
                voice_id=self.voice_id,
                text=text,
                model_id="eleven_multilingual_v2",  # 日本語対応
                voice_settings=VoiceSettings(
                    stability=stability,
                    similarity_boost=similarity_boost,
                    style=style,
                    use_speaker_boost=use_speaker_boost
                )
            )

            # 一時ファイルに保存
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".mp3"
            )

            # ストリーミングレスポンスを保存
            for chunk in response:
                temp_file.write(chunk)

            temp_file.close()
            audio_path = temp_file.name

            logger.info("音声生成完了")

            # 音声時間を取得
            duration = self._get_audio_duration(audio_path)
            logger.info(f"音声時間（実測）: {duration:.2f}秒")

            # Cloudinaryにアップロード
            logger.info("Cloudinaryにアップロード開始")
            audio_url, err = self._upload_to_cloudinary(audio_path)

            if err:
                # 一時ファイル削除
                try:
                    os.unlink(audio_path)
                except:
                    pass
                return (None, err)

            logger.info(f"Cloudinaryアップロード完了: {audio_url}")

            # 一時ファイル削除
            try:
                os.unlink(audio_path)
            except Exception as e:
                logger.warning(f"一時ファイル削除失敗: {e}")

            # GeneratedAudioオブジェクト作成
            audio = GeneratedAudio(
                audio_url=audio_url,
                duration_seconds=duration,
                file_size_bytes=None  # ElevenLabsはサイズ情報を返さない
            )

            logger.info(f"音声生成成功: {audio_url} ({duration:.2f}秒)")
            return (audio, None)

        except Exception as e:
            logger.error(f"音声生成エラー: {e}", exc_info=True)
            return (None, AudioGenerationError(f"ElevenLabs error: {e}"))

    def _get_audio_duration(self, file_path: str) -> float:
        """
        音声ファイルの時間を取得

        Args:
            file_path: 音声ファイルパス

        Returns:
            時間（秒）
        """
        try:
            audio = MutagenFile(file_path)
            if audio and audio.info:
                return audio.info.length
            return 0.0
        except Exception as e:
            logger.warning(f"音声時間取得失敗: {e}")
            return 0.0

    def _upload_to_cloudinary(
        self,
        audio_path: str
    ) -> Tuple[Optional[str], Optional[Exception]]:
        """
        Cloudinaryにアップロード

        Args:
            audio_path: 音声ファイルパス

        Returns:
            (url, error): URLまたはエラー
        """
        try:
            # 設定読み込み
            config = get_config()
            folder = config.get("cloudinary.folder", "ai-avatar/audio")

            result = cloudinary.uploader.upload(
                audio_path,
                resource_type="video",  # 音声も"video"
                format="mp3",
                folder=folder,
                overwrite=True,
                eager=[{"format": "mp3"}],  # MP3変換を強制
                eager_async=False  # 変換完了まで待機
            )

            url = result["secure_url"]
            return (url, None)

        except Exception as e:
            logger.error(f"Cloudinaryアップロードエラー: {e}", exc_info=True)
            return (None, CloudinaryError(f"Upload failed: {e}"))
