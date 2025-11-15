"""
D-ID API - リップシンク動画生成

機能:
  - 動画生成リクエスト
  - ポーリング（完了待機）
  - 動画URL取得
  - エラーハンドリング
"""

import time
import requests
from typing import Tuple, Optional

from ..models.schemas import GeneratedVideo, DIDConfig
from ..utils.errors import VideoCreationError, TimeoutError, APIError
from ..utils.logger import get_logger
from ..utils.config import get_config

logger = get_logger(__name__)


class DIDClient:
    """
    D-ID API クライアント

    音声URLとアバター画像からリップシンク動画を生成

    Example:
        >>> client = DIDClient(api_key="did_xxxxx")
        >>> video, err = client.generate(
        ...     audio_url="https://...",
        ...     avatar_url="https://..."
        ... )
    """

    def __init__(self, api_key: str):
        """
        初期化

        Args:
            api_key: D-ID APIキー
        """
        self.api_key = api_key

        # 設定読み込み
        config = get_config()
        self.base_url = config.get("did.api_url", "https://api.d-id.com")
        self.poll_interval = config.get("did.poll_interval_seconds", 5)
        self.poll_timeout = config.get("did.poll_timeout_seconds", 300)

    def generate(
        self,
        audio_url: str,
        avatar_url: str
    ) -> Tuple[Optional[GeneratedVideo], Optional[Exception]]:
        """
        リップシンク動画を生成

        Args:
            audio_url: 音声ファイルURL
            avatar_url: アバター画像URL

        Returns:
            (video, error):
                - 成功: (GeneratedVideo, None)
                - 失敗: (None, Exception)

        Example:
            >>> video, err = client.generate(
            ...     audio_url="https://res.cloudinary.com/.../audio.mp3",
            ...     avatar_url="https://example.com/avatar.jpg"
            ... )
        """
        try:
            logger.info("動画生成リクエスト開始")

            # 動画生成リクエスト
            talk_id, err = self._create_talk(audio_url, avatar_url)
            if err:
                return (None, err)

            logger.info(f"Talk ID取得: {talk_id}")

            # ポーリング（完了待機）
            video_url, duration, err = self._poll_status(talk_id)
            if err:
                return (None, err)

            # GeneratedVideoオブジェクト作成
            video = GeneratedVideo(
                video_url=video_url,
                duration_seconds=duration or 0.0,
                resolution="1920x1080"  # D-IDのデフォルト解像度
            )

            logger.info(f"動画生成成功: {video_url}")
            return (video, None)

        except Exception as e:
            logger.error(f"動画生成エラー: {e}", exc_info=True)
            return (None, e)

    def _create_talk(
        self,
        audio_url: str,
        avatar_url: str
    ) -> Tuple[Optional[str], Optional[Exception]]:
        """
        動画生成リクエスト

        Args:
            audio_url: 音声ファイルURL
            avatar_url: アバター画像URL

        Returns:
            (talk_id, error): Talk IDまたはエラー
        """
        try:
            url = f"{self.base_url}/talks"

            headers = {
                "Authorization": f"Basic {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "script": {
                    "type": "audio",
                    "audio_url": audio_url
                },
                "source_url": avatar_url,
                "config": {
                    "stitch": True,
                    "result_format": "mp4"
                }
            }

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code != 201:
                error_msg = response.text
                logger.error(f"D-ID API error ({response.status_code}): {error_msg}")
                return (
                    None,
                    APIError(
                        f"動画生成リクエスト失敗",
                        status_code=response.status_code,
                        response=error_msg
                    )
                )

            data = response.json()
            talk_id = data.get("id")

            if not talk_id:
                return (None, VideoCreationError("Talk IDが取得できませんでした"))

            return (talk_id, None)

        except requests.Timeout:
            return (None, TimeoutError("動画生成リクエストタイムアウト（30秒）"))

        except requests.RequestException as e:
            return (None, APIError(f"HTTP error: {e}"))

        except Exception as e:
            return (None, e)

    def _poll_status(
        self,
        talk_id: str
    ) -> Tuple[Optional[str], Optional[float], Optional[Exception]]:
        """
        ステータスポーリング

        Args:
            talk_id: Talk ID

        Returns:
            (video_url, duration, error): 動画URL、時間、またはエラー
        """
        start_time = time.time()
        attempt = 0

        logger.info(f"ポーリング開始（最大{self.poll_timeout}秒）")

        while time.time() - start_time < self.poll_timeout:
            attempt += 1

            try:
                url = f"{self.base_url}/talks/{talk_id}"

                headers = {
                    "Authorization": f"Basic {self.api_key}"
                }

                response = requests.get(
                    url,
                    headers=headers,
                    timeout=10
                )

                if response.status_code != 200:
                    logger.warning(f"ステータス確認エラー ({response.status_code})")
                    time.sleep(self.poll_interval)
                    continue

                data = response.json()
                status = data.get("status")

                logger.debug(f"ポーリング {attempt}回目: status={status}")

                if status == "done":
                    # 完了
                    video_url = data.get("result_url")
                    duration = data.get("duration")

                    if not video_url:
                        return (None, None, VideoCreationError("動画URLが取得できませんでした"))

                    elapsed = time.time() - start_time
                    logger.info(f"動画生成完了（{elapsed:.1f}秒）")
                    return (video_url, duration, None)

                elif status == "error":
                    # エラー
                    error_info = data.get("error", {})
                    error_desc = error_info.get("description", "Unknown error")
                    return (None, None, VideoCreationError(f"D-ID error: {error_desc}"))

                elif status in ["created", "started", "processing"]:
                    # 処理中 - 待機して再試行
                    time.sleep(self.poll_interval)

                else:
                    # 不明なステータス
                    logger.warning(f"不明なステータス: {status}")
                    time.sleep(self.poll_interval)

            except requests.Timeout:
                logger.warning("ステータス確認タイムアウト、リトライします")
                time.sleep(self.poll_interval)

            except requests.RequestException as e:
                logger.warning(f"ステータス確認エラー: {e}、リトライします")
                time.sleep(self.poll_interval)

        # タイムアウト
        elapsed = time.time() - start_time
        return (
            None,
            None,
            TimeoutError(f"動画生成タイムアウト（{elapsed:.1f}秒 / 最大{self.poll_timeout}秒）")
        )
