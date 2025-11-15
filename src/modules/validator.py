"""
スクリプトバリデーション

機能:
  - スクリプトの文字数チェック
  - フォーマット検証
  - 予想音声時間の計算
"""

from typing import Tuple, Optional
from ..models.schemas import ScriptValidation, VideoLength
from ..utils.errors import ValidationError
from ..utils.logger import get_logger

logger = get_logger(__name__)


def validate_script(
    script: str,
    video_length: VideoLength = VideoLength.SHORTS
) -> Tuple[Optional[ScriptValidation], Optional[Exception]]:
    """
    スクリプトをバリデーション

    Args:
        script: 入力スクリプト
        video_length: 動画の長さ

    Returns:
        (validation_result, error):
            - 成功: (ScriptValidation, None)
            - 失敗: (None, Exception)

    Example:
        >>> validation, err = validate_script("今日は〇〇について...", VideoLength.SHORTS)
        >>> if err:
        >>>     print(f"エラー: {err}")
        >>> else:
        >>>     print(f"単語数: {validation.word_count}")
    """
    try:
        # 空チェック
        if not script or not script.strip():
            return (None, ValidationError("スクリプトを入力してください"))

        # 単語数カウント
        word_count = count_words(script)

        # 最大単語数取得
        max_words = get_max_words(video_length)

        # 文字数チェック
        if word_count > max_words:
            return (
                None,
                ValidationError(
                    f"スクリプトが長すぎます（{word_count}単語 / 最大{max_words}単語）"
                )
            )

        # 最小文字数チェック
        min_words = 10
        if word_count < min_words:
            return (
                None,
                ValidationError(
                    f"スクリプトが短すぎます（{word_count}単語 / 最低{min_words}単語必要）"
                )
            )

        # 予想音声時間を計算
        estimated_duration = estimate_duration(script)

        # バリデーション成功
        validation = ScriptValidation(
            is_valid=True,
            word_count=word_count,
            estimated_duration_seconds=estimated_duration,
            error_message=None
        )

        logger.info(
            f"スクリプトバリデーション成功: {word_count}単語、"
            f"予想{estimated_duration}秒"
        )

        return (validation, None)

    except Exception as e:
        logger.error(f"バリデーションエラー: {e}")
        return (None, e)


def count_words(text: str) -> int:
    """
    単語数をカウント

    日本語の場合は文字数、英語の場合は単語数

    Args:
        text: テキスト

    Returns:
        単語数

    Example:
        >>> count = count_words("今日は良い天気です")
        >>> print(count)  # 8
    """
    # 空白で分割
    words = text.split()

    # 日本語が含まれる場合は文字数で計算
    # （簡易実装：全角文字が含まれているか）
    if any(ord(c) > 127 for c in text):
        # 日本語: 空白と改行を除いた文字数
        char_count = sum(1 for c in text if c not in [' ', '\n', '\t'])
        return char_count
    else:
        # 英語: 単語数
        return len(words)


def estimate_duration(
    text: str,
    words_per_minute: int = 150
) -> int:
    """
    予想音声時間を計算（秒）

    Args:
        text: テキスト
        words_per_minute: 1分あたりの単語数（デフォルト: 150）

    Returns:
        予想時間（秒）

    Example:
        >>> duration = estimate_duration("今日は〇〇について解説します...")
        >>> print(f"{duration}秒")
    """
    word_count = count_words(text)

    # 日本語の場合は調整（文字数→単語数換算）
    if any(ord(c) > 127 for c in text):
        # 日本語: 約2.5文字 = 1単語
        word_count = word_count / 2.5

    # 分を計算
    minutes = word_count / words_per_minute

    # 秒に変換
    seconds = int(minutes * 60)

    return seconds


def get_max_words(video_length: VideoLength) -> int:
    """
    動画の長さから最大単語数を取得

    Args:
        video_length: 動画の長さ

    Returns:
        最大単語数

    Example:
        >>> max_words = get_max_words(VideoLength.SHORTS)
        >>> print(max_words)  # 150
    """
    if video_length == VideoLength.SHORTS:
        return 150  # 60秒
    else:  # VideoLength.LONG
        return 500  # 5分
