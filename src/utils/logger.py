"""
ロギング設定

機能:
  - ロガー設定
  - コンソール出力
  - ログレベル制御
  - 機密情報のマスキング
"""

import logging
import sys
import re
from typing import Optional


class SensitiveDataFilter(logging.Filter):
    """
    機密データをマスクするフィルター

    APIキー、パスワードなどの機密情報をログから除外
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        ログレコードをフィルタリング

        Args:
            record: ログレコード

        Returns:
            True（常に表示、ただし機密情報はマスク）
        """
        # ログメッセージ取得
        message = record.getMessage()

        # APIキーをマスク
        # sk-xxx, cart_xxx, did_xxx などのパターン
        message = re.sub(
            r'(sk-|cart_|did_)[a-zA-Z0-9]{20,}',
            r'\1***',
            message
        )

        # パスワードをマスク
        message = re.sub(
            r'(password[\'"]?\s*[:=]\s*[\'"]?)([^\'"]+)([\'"]?)',
            r'\1***\3',
            message,
            flags=re.IGNORECASE
        )

        # マスク後のメッセージを設定
        record.msg = message
        record.args = ()

        return True


def get_logger(
    name: str,
    level: Optional[str] = None
) -> logging.Logger:
    """
    ロガーを取得

    Args:
        name: ロガー名（通常は__name__）
        level: ログレベル（DEBUG, INFO, WARNING, ERROR）

    Returns:
        Loggerインスタンス

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("処理開始")
        >>> logger.error("エラー発生", exc_info=True)
    """
    # ロガー作成
    logger = logging.getLogger(name)

    # ログレベル設定
    if level:
        logger.setLevel(getattr(logging, level.upper()))
    else:
        logger.setLevel(logging.INFO)

    # 既存のハンドラーがあればスキップ（重複防止）
    if logger.handlers:
        return logger

    # コンソールハンドラー作成
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # フォーマッター作成
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    # 機密情報フィルター追加
    console_handler.addFilter(SensitiveDataFilter())

    # ハンドラー追加
    logger.addHandler(console_handler)

    # 親ロガーへの伝播を防ぐ（重複ログ防止）
    logger.propagate = False

    return logger


def setup_logger(level: str = "INFO") -> None:
    """
    グローバルロガー設定

    Args:
        level: ログレベル（DEBUG, INFO, WARNING, ERROR）

    Example:
        >>> setup_logger("DEBUG")
    """
    # ルートロガー取得
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # 既存のハンドラーをクリア
    root_logger.handlers.clear()

    # コンソールハンドラー作成
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # フォーマッター作成
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    # 機密情報フィルター追加
    console_handler.addFilter(SensitiveDataFilter())

    # ハンドラー追加
    root_logger.addHandler(console_handler)
