"""
Cartesia API - 音声生成

機能:
  - WebSocket接続管理
  - 音声生成（声クローン使用）
  - Cloudinaryアップロード
  - エラーハンドリング

参考: resources/Cartesia実装ガイド.md
"""

import asyncio
import websockets
import json
import base64
import tempfile
import os
from typing import Tuple, Optional
from pathlib import Path

import cloudinary
import cloudinary.uploader
from pydub import AudioSegment

from ..models.schemas import GeneratedAudio, CartesiaConfig, CloudinaryConfig
from ..utils.errors import AudioGenerationError, CloudinaryError, TimeoutError
from ..utils.logger import get_logger
from ..utils.config import get_config

logger = get_logger(__name__)


class CartesiaClient:
    """
    Cartesia API クライアント

    WebSocket接続で音声を生成し、Cloudinaryにアップロード

    Example:
        >>> client = CartesiaClient(
        ...     api_key="cart_xxxxx",
        ...     voice_id="voice_xxxxx"
        ... )
        >>> audio, err = await client.generate("こんにちは")
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
            api_key: Cartesia APIキー
            voice_id: 声クローンID
            cloudinary_config: Cloudinary設定
        """
        self.api_key = api_key
        self.voice_id = voice_id
        self.cloudinary_config = cloudinary_config

        # 設定読み込み
        config = get_config()
        self.ws_url = config.get("cartesia.ws_url")
        self.model = config.get("cartesia.model", "sonic-japanese")
        self.timeout = config.get("cartesia.timeout_seconds", 60)

        # Cloudinary設定
        if cloudinary_config:
            cloudinary.config(
                cloud_name=cloudinary_config.cloud_name,
                api_key=cloudinary_config.api_key,
                api_secret=cloudinary_config.api_secret
            )

    async def generate(
        self,
        text: str,
        speed: float = 1.0
    ) -> Tuple[Optional[GeneratedAudio], Optional[Exception]]:
        """
        音声生成

        Args:
            text: 生成するテキスト
            speed: 再生速度（0.5-2.0）

        Returns:
            (audio, error):
                - 成功: (GeneratedAudio, None)
                - 失敗: (None, Exception)

        Example:
            >>> audio, err = await client.generate("こんにちは", speed=1.0)
        """
        try:
            logger.info(f"音声生成開始: {len(text)}文字")

            # WebSocket接続
            uri = f"{self.ws_url}?api_key={self.api_key}&cartesia_version=2024-06-10"

            async with websockets.connect(uri, timeout=self.timeout) as websocket:
                # 初期化メッセージ送信
                init_message = {
                    "context_id": "temp",
                    "model_id": self.model,
                    "voice": {
                        "mode": "id",
                        "id": self.voice_id
                    },
                    "output_format": {
                        "container": "mp3",
                        "encoding": "mp3",
                        "sample_rate": 44100
                    },
                    "language": "ja"
                }

                await websocket.send(json.dumps(init_message))
                logger.debug("初期化メッセージ送信完了")

                # テキスト送信
                text_message = {
                    "context_id": "temp",
                    "transcript": text,
                    "continue": False,
                    "duration": None,
                    "voice": {
                        "mode": "id",
                        "id": self.voice_id
                    },
                    "speed": speed
                }

                await websocket.send(json.dumps(text_message))
                logger.debug("テキスト送信完了")

                # 音声データ受信
                audio_chunks = []
                while True:
                    try:
                        message = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=self.timeout
                        )

                        data = json.loads(message)

                        if data.get("type") == "chunk":
                            # Base64デコードして音声データを保存
                            audio_data = base64.b64decode(data["data"])
                            audio_chunks.append(audio_data)
                            logger.debug(f"音声チャンク受信: {len(audio_data)}バイト")

                        elif data.get("type") == "done":
                            logger.info("音声生成完了")
                            break

                        elif data.get("type") == "error":
                            error_msg = data.get("error", "Unknown error")
                            return (None, AudioGenerationError(f"Cartesia error: {error_msg}"))

                    except asyncio.TimeoutError:
                        return (None, TimeoutError(f"音声生成タイムアウト（{self.timeout}秒）"))

            # 音声データを結合
            audio_bytes = b"".join(audio_chunks)

            if not audio_bytes:
                return (None, AudioGenerationError("音声データが空です"))

            logger.info(f"音声データ生成完了: {len(audio_bytes)}バイト")

            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_path = tmp_file.name

            try:
                # pydubで実際の音声時間を測定
                audio_segment = AudioSegment.from_file(tmp_path)
                actual_duration = audio_segment.duration_seconds
                logger.info(f"音声時間（実測）: {actual_duration:.2f}秒")

                # Cloudinaryにアップロード
                audio_url, err = self._upload_to_cloudinary(tmp_path)
                if err:
                    return (None, err)

                # GeneratedAudioオブジェクト作成
                audio = GeneratedAudio(
                    audio_url=audio_url,
                    duration_seconds=actual_duration,  # pydubで実測した値
                    file_size_bytes=len(audio_bytes)
                )

                logger.info(f"音声生成成功: {audio_url} ({actual_duration:.2f}秒)")
                return (audio, None)

            finally:
                # 一時ファイル削除
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except websockets.exceptions.WebSocketException as e:
            logger.error(f"WebSocket error: {e}")
            return (None, AudioGenerationError(f"WebSocket接続エラー: {e}"))

        except Exception as e:
            logger.error(f"音声生成エラー: {e}", exc_info=True)
            return (None, e)

    def _upload_to_cloudinary(
        self,
        audio_file_path: str
    ) -> Tuple[Optional[str], Optional[Exception]]:
        """
        Cloudinaryにアップロード

        Args:
            audio_file_path: 音声ファイルパス

        Returns:
            (url, error): CloudinaryのURLまたはエラー
        """
        try:
            logger.info("Cloudinaryにアップロード開始")

            # アップロード
            result = cloudinary.uploader.upload(
                audio_file_path,
                resource_type="video",  # 音声も"video"
                folder="ai-avatar/audio",
                overwrite=True,
                unique_filename=True
            )

            url = result.get("secure_url")

            if not url:
                return (None, CloudinaryError("URLが取得できませんでした"))

            logger.info(f"Cloudinaryアップロード成功: {url}")
            return (url, None)

        except cloudinary.exceptions.Error as e:
            logger.error(f"Cloudinaryエラー: {e}")
            return (None, CloudinaryError(f"アップロード失敗: {e}"))

        except Exception as e:
            logger.error(f"予期しないエラー: {e}")
            return (None, e)


# 同期ラッパー関数（Streamlitで使いやすくするため）
def generate_audio_sync(
    text: str,
    api_key: str,
    voice_id: str,
    cloudinary_config: CloudinaryConfig,
    speed: float = 1.0
) -> Tuple[Optional[GeneratedAudio], Optional[Exception]]:
    """
    音声生成（同期版）

    Streamlitから呼び出しやすいように同期的にラップ

    Args:
        text: 生成するテキスト
        api_key: Cartesia APIキー
        voice_id: 声クローンID
        cloudinary_config: Cloudinary設定
        speed: 再生速度

    Returns:
        (audio, error): GeneratedAudioまたはエラー

    Example:
        >>> audio, err = generate_audio_sync(
        ...     "こんにちは",
        ...     api_key="cart_xxxxx",
        ...     voice_id="voice_xxxxx",
        ...     cloudinary_config=config
        ... )
    """
    client = CartesiaClient(api_key, voice_id, cloudinary_config)

    # イベントループで実行
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(client.generate(text, speed))
        return result
    finally:
        loop.close()
