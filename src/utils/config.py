"""
設定ファイル管理

機能:
  - config.yaml読み込み
  - 設定値の取得
  - バリデーション
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

from .logger import get_logger

logger = get_logger(__name__)


class Config:
    """
    設定管理クラス

    config.yamlを読み込み、設定値を提供

    Example:
        >>> config = Config()
        >>> max_words = config.get("script.max_words_shorts")
        >>> api_url = config.get("cartesia.ws_url")
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初期化

        Args:
            config_path: 設定ファイルパス（デフォルト: config.yaml）
        """
        if config_path is None:
            # デフォルトパス: プロジェクトルート/config.yaml
            config_path = self._find_config_file()

        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.load()

    def _find_config_file(self) -> str:
        """
        config.yamlファイルを検索

        Returns:
            config.yamlのパス

        Raises:
            FileNotFoundError: ファイルが見つからない
        """
        # 現在のディレクトリから上位階層を検索
        current_dir = Path.cwd()

        for _ in range(5):  # 最大5階層まで
            config_file = current_dir / "config.yaml"
            if config_file.exists():
                return str(config_file)
            current_dir = current_dir.parent

        # 見つからない場合はデフォルトパス
        return "config.yaml"

    def load(self) -> None:
        """
        設定ファイルを読み込み

        Raises:
            FileNotFoundError: ファイルが存在しない
            yaml.YAMLError: YAML解析エラー
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)

            logger.info(f"設定ファイル読み込み成功: {self.config_path}")

        except FileNotFoundError:
            logger.error(f"設定ファイルが見つかりません: {self.config_path}")
            # デフォルト設定を使用
            self.config = self._get_default_config()
            logger.warning("デフォルト設定を使用します")

        except yaml.YAMLError as e:
            logger.error(f"YAML解析エラー: {e}")
            raise

    def _get_default_config(self) -> Dict[str, Any]:
        """
        デフォルト設定を取得

        Returns:
            デフォルト設定辞書
        """
        return {
            "app": {
                "name": "AIアバター動画生成",
                "version": "1.0.0"
            },
            "script": {
                "max_words_shorts": 150,
                "max_words_long": 500,
                "min_words": 10
            },
            "cartesia": {
                "ws_url": "wss://api.cartesia.ai/tts/websocket",
                "model": "sonic-japanese",
                "default_speed": 1.0
            },
            "did": {
                "api_url": "https://api.d-id.com",
                "poll_interval_seconds": 5,
                "poll_timeout_seconds": 300
            },
            "logging": {
                "level": "INFO"
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        設定値を取得

        Args:
            key: 設定キー（ドット記法: "script.max_words_shorts"）
            default: デフォルト値

        Returns:
            設定値

        Example:
            >>> config = Config()
            >>> max_words = config.get("script.max_words_shorts", 150)
        """
        # ドット記法をパース
        keys = key.split('.')
        value = self.config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            logger.debug(f"設定キー '{key}' が見つかりません。デフォルト値を使用: {default}")
            return default

    def get_all(self) -> Dict[str, Any]:
        """
        すべての設定を取得

        Returns:
            設定辞書
        """
        return self.config.copy()


# グローバル設定インスタンス（シングルトン）
_global_config: Optional[Config] = None


def load_config(config_path: Optional[str] = None) -> Config:
    """
    グローバル設定を読み込み

    Args:
        config_path: 設定ファイルパス

    Returns:
        Configインスタンス

    Example:
        >>> config = load_config()
        >>> max_words = config.get("script.max_words_shorts")
    """
    global _global_config

    if _global_config is None:
        _global_config = Config(config_path)

    return _global_config


def get_config() -> Config:
    """
    グローバル設定を取得

    Returns:
        Configインスタンス

    Raises:
        RuntimeError: load_config()が呼ばれていない
    """
    if _global_config is None:
        return load_config()

    return _global_config
