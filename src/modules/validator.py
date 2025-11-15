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
from ..utils.config import get_config

logger = get_logger(__name__)


def validate_script(
    script: str
) -> Tuple[Optional[ScriptValidation], Optional[Exception]]:
    """
    スクリプトをバリデーション

    Args:
        script: 入力スクリプト

    Returns:
        (validation_result, error):
            - 成功: (ScriptValidation, None)
            - 失敗: (None, Exception)

    Example:
        >>> validation, err = validate_script("今日は〇〇について...")
        >>> if err:
        >>>     print(f"エラー: {err}")
        >>> else:
        >>>     print(f"文字数: {validation.word_count}")
    """
    try:
        # 空チェック
        if not script or not script.strip():
            return (None, ValidationError("スクリプトを入力してください"))

        # 文字数カウント
        char_count = count_chars(script)

        # 最大文字数取得（目安）
        max_chars = get_max_chars()

        # 文字数チェック（警告のみ、エラーにはしない）
        # 実際の制限は音声生成後の duration チェックで行う
        if char_count > max_chars:
            logger.warning(
                f"スクリプトが長い（{char_count}文字 / 推奨{max_chars}文字）"
                f"※ 実際の時間は音声生成後に確認されます"
            )

        # 最小文字数取得
        config = get_config()
        min_chars = config.get("script.min_chars", 30)
        if char_count < min_chars:
            return (
                None,
                ValidationError(
                    f"スクリプトが短すぎます（{char_count}文字 / 最低{min_chars}文字必要）"
                )
            )

        # 予想音声時間を計算
        estimated_duration = estimate_duration(script)

        # 推定時間チェック（明らかに長すぎる場合はブロック）
        # 余裕を持って350秒（推定は誤差があるため）
        max_estimated_duration = config.get("script.max_estimated_duration", 350)
        if estimated_duration > max_estimated_duration:
            return (
                None,
                ValidationError(
                    f"スクリプトが長すぎます（推定{estimated_duration}秒 / 最大約{max_estimated_duration}秒）\n"
                    f"※ スクリプトを短くするか、2つに分けてください"
                )
            )

        # バリデーション成功
        validation = ScriptValidation(
            is_valid=True,
            word_count=char_count,
            estimated_duration_seconds=estimated_duration,
            error_message=None
        )

        logger.info(
            f"スクリプトバリデーション成功: {char_count}文字、"
            f"予想{estimated_duration}秒"
        )

        return (validation, None)

    except Exception as e:
        logger.error(f"バリデーションエラー: {e}")
        return (None, e)


def count_chars(text: str) -> int:
    """
    文字数をカウント

    空白、改行、タブを除いた文字数を返す

    Args:
        text: テキスト

    Returns:
        文字数

    Example:
        >>> count = count_chars("今日は良い天気です")
        >>> print(count)  # 8
    """
    # 空白、改行、タブを除いた文字数
    char_count = sum(1 for c in text if c not in [' ', '\n', '\t'])
    return char_count


# 後方互換性のため
def count_words(text: str) -> int:
    """
    後方互換性のため残す（count_charsを呼び出す）
    """
    return count_chars(text)


def estimate_duration(text: str) -> int:
    """
    予想音声時間を計算（秒）

    日本語の文字数から概算時間を計算
    ※ あくまで目安。実際の時間はpydubで測定すること

    Args:
        text: テキスト

    Returns:
        予想時間（秒）

    Example:
        >>> duration = estimate_duration("今日は〇〇について解説します...")
        >>> print(f"{duration}秒")
    """
    # 設定から文字/分を取得
    config = get_config()
    chars_per_minute = config.get("script.chars_per_minute", 300)

    # 文字数カウント
    char_count = count_chars(text)

    # 秒に変換
    seconds = int((char_count / chars_per_minute) * 60)

    return seconds


def get_max_chars() -> int:
    """
    最大文字数を取得（目安）

    Returns:
        最大文字数

    Example:
        >>> max_chars = get_max_chars()
        >>> print(max_chars)  # 1500
    """
    config = get_config()
    return config.get("script.max_chars", 1500)
