"""
カスタムエラー定義

動画生成プロセスで発生する各種エラーを定義
"""


class VideoGenerationError(Exception):
    """
    動画生成エラーの基底クラス

    すべてのカスタムエラーはこのクラスを継承
    """
    pass


class ValidationError(VideoGenerationError):
    """
    バリデーションエラー

    スクリプトの文字数、フォーマット等のバリデーションで発生

    Example:
        >>> raise ValidationError("スクリプトが長すぎます（200単語 / 最大150単語）")
    """
    pass


class AudioGenerationError(VideoGenerationError):
    """
    音声生成エラー

    Cartesia API関連のエラー

    Example:
        >>> raise AudioGenerationError("WebSocket接続失敗")
    """
    pass


class VideoCreationError(VideoGenerationError):
    """
    動画作成エラー

    D-ID API関連のエラー

    Example:
        >>> raise VideoCreationError("リップシンク動画生成失敗")
    """
    pass


class ConfigError(VideoGenerationError):
    """
    設定エラー

    config.yaml読み込み、設定値の不正等

    Example:
        >>> raise ConfigError("config.yamlが見つかりません")
    """
    pass


class APIError(VideoGenerationError):
    """
    API呼び出しエラー

    HTTP/WebSocket APIの汎用エラー

    Attributes:
        status_code: HTTPステータスコード
        response: レスポンス内容
    """

    def __init__(
        self,
        message: str,
        status_code: int = None,
        response: str = None
    ):
        """
        初期化

        Args:
            message: エラーメッセージ
            status_code: HTTPステータスコード
            response: レスポンス内容
        """
        super().__init__(message)
        self.status_code = status_code
        self.response = response

    def __str__(self) -> str:
        """文字列表現"""
        if self.status_code:
            return f"{super().__str__()} (Status: {self.status_code})"
        return super().__str__()


class TimeoutError(VideoGenerationError):
    """
    タイムアウトエラー

    API呼び出し、ポーリング等のタイムアウト

    Example:
        >>> raise TimeoutError("D-ID動画生成タイムアウト（5分）")
    """
    pass


class CloudinaryError(VideoGenerationError):
    """
    Cloudinaryエラー

    音声ファイルのアップロード関連エラー

    Example:
        >>> raise CloudinaryError("音声ファイルアップロード失敗")
    """
    pass
