"""
データモデル定義

Pydanticを使用した型安全なデータモデル
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from enum import Enum


class VideoLength(str, Enum):
    """動画の長さ"""
    SHORTS = "shorts"      # 60秒
    LONG = "long"          # 5分


class VideoGenerationRequest(BaseModel):
    """
    動画生成リクエスト

    Example:
        >>> request = VideoGenerationRequest(
        ...     script="今日は〇〇について解説します...",
        ...     avatar_image="avatar_1",
        ...     video_length=VideoLength.SHORTS
        ... )
    """
    script: str = Field(..., min_length=10, description="スクリプト")
    avatar_image: str = Field(..., description="アバター画像ID")
    voice_id: str = Field(..., description="Cartesia声クローンID")
    video_length: VideoLength = Field(VideoLength.SHORTS, description="動画の長さ")
    voice_speed: float = Field(1.0, ge=0.5, le=2.0, description="声の速度")


class GeneratedAudio(BaseModel):
    """
    生成された音声

    Example:
        >>> audio = GeneratedAudio(
        ...     audio_url="https://res.cloudinary.com/.../audio.mp3",
        ...     duration_seconds=45.5
        ... )
    """
    audio_url: HttpUrl = Field(..., description="音声ファイルURL")
    duration_seconds: float = Field(..., description="音声時間（秒）")
    file_size_bytes: Optional[int] = Field(None, description="ファイルサイズ（バイト）")


class GeneratedVideo(BaseModel):
    """
    生成された動画

    Example:
        >>> video = GeneratedVideo(
        ...     video_url="https://d-id-talks-prod.s3.amazonaws.com/.../video.mp4",
        ...     duration_seconds=60.0
        ... )
    """
    video_url: HttpUrl = Field(..., description="動画ファイルURL")
    duration_seconds: float = Field(..., description="動画時間（秒）")
    resolution: Optional[str] = Field(None, description="解像度（例: 1920x1080）")


class ScriptValidation(BaseModel):
    """
    スクリプトバリデーション結果

    Example:
        >>> validation = ScriptValidation(
        ...     is_valid=True,
        ...     word_count=127,
        ...     estimated_duration_seconds=51
        ... )
    """
    is_valid: bool = Field(..., description="バリデーション結果")
    word_count: int = Field(..., description="単語数")
    estimated_duration_seconds: int = Field(..., description="予想音声時間（秒）")
    error_message: Optional[str] = Field(None, description="エラーメッセージ")


class CartesiaConfig(BaseModel):
    """
    Cartesia API設定

    Example:
        >>> config = CartesiaConfig(
        ...     api_key="cart_xxxxx",
        ...     voice_id="voice_xxxxx",
        ...     model="sonic-japanese"
        ... )
    """
    api_key: str = Field(..., description="CartesiaAPIキー")
    voice_id: str = Field(..., description="声クローンID")
    model: str = Field("sonic-japanese", description="モデル名")
    speed: float = Field(1.0, ge=0.5, le=2.0, description="再生速度")


class DIDConfig(BaseModel):
    """
    D-ID API設定

    Example:
        >>> config = DIDConfig(
        ...     api_key="did_xxxxx"
        ... )
    """
    api_key: str = Field(..., description="D-ID APIキー")


class CloudinaryConfig(BaseModel):
    """
    Cloudinary設定

    Example:
        >>> config = CloudinaryConfig(
        ...     cloud_name="your_cloud",
        ...     api_key="123456",
        ...     api_secret="xxxxx"
        ... )
    """
    cloud_name: str = Field(..., description="クラウド名")
    api_key: str = Field(..., description="APIキー")
    api_secret: str = Field(..., description="APIシークレット")
