"""
D-ID API 単体テストスクリプト

このスクリプトはStreamlitを使わずにD-ID APIを直接呼び出します。
音声URLと画像URLから動画を生成できるかテストします。
"""

import os
import sys
import time
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.modules.did import DIDClient
from src.utils.logger import get_logger

logger = get_logger(__name__)


def test_did_with_urls(audio_url: str, avatar_url: str, api_key: str):
    """
    D-ID APIをテストする

    Args:
        audio_url: 音声ファイルのURL（MP3形式）
        avatar_url: アバター画像のURL
        api_key: D-ID APIキー
    """
    print("=" * 60)
    print("D-ID API 単体テスト開始")
    print("=" * 60)
    print()

    print(f"音声URL: {audio_url}")
    print(f"画像URL: {avatar_url}")
    print()

    # D-IDクライアント初期化
    client = DIDClient(api_key=api_key)

    print("動画生成リクエスト送信中...")
    print()

    # 動画生成
    start_time = time.time()
    video, err = client.generate(
        audio_url=audio_url,
        avatar_url=avatar_url
    )
    elapsed = time.time() - start_time

    print("-" * 60)

    if err:
        print("❌ エラー発生")
        print(f"エラー内容: {err}")
        print(f"エラータイプ: {type(err).__name__}")

        # 詳細なエラー情報
        if hasattr(err, 'status_code'):
            print(f"HTTPステータス: {err.status_code}")
        if hasattr(err, 'response'):
            print(f"レスポンス: {err.response}")

        print()
        print(f"処理時間: {elapsed:.1f}秒")
        return False

    print("✅ 成功！")
    print()
    print(f"動画URL: {video.video_url}")
    print(f"動画時間: {video.duration_seconds}秒")
    print(f"解像度: {video.resolution}")
    print()
    print(f"処理時間: {elapsed:.1f}秒")
    print()
    print("=" * 60)
    print("動画URLをブラウザで開いて確認してください")
    print("=" * 60)

    return True


def main():
    """
    メイン処理
    """

    # 設定読み込み（.streamlit/secrets.toml）
    import toml
    secrets_path = project_root / ".streamlit" / "secrets.toml"

    if not secrets_path.exists():
        print("❌ エラー: .streamlit/secrets.toml が見つかりません")
        return

    secrets = toml.load(secrets_path)
    api_key = secrets["did"]["api_key"]

    print()
    print("テストモードを選択してください：")
    print()
    print("1. サンプルURL（公開サンプル音声・画像）でテスト")
    print("2. カスタムURL（自分の音声・画像URL）でテスト")
    print()

    choice = input("選択 (1 or 2): ").strip()

    if choice == "1":
        # サンプルURLでテスト（D-ID公式ドキュメントのサンプル）
        print()
        print("📌 サンプルURLでテストします")
        print()

        # D-IDのサンプルアバター
        avatar_url = "https://d-id-public-bucket.s3.amazonaws.com/alice.jpg"

        # サンプル音声（短いMP3）
        # Note: 実際のテストには有効な音声URLが必要です
        audio_url = input("音声URL（MP3）を入力してください: ").strip()

        if not audio_url:
            print("❌ 音声URLが入力されませんでした")
            return

        test_did_with_urls(audio_url, avatar_url, api_key)

    elif choice == "2":
        # カスタムURLでテスト
        print()
        print("📌 カスタムURLでテストします")
        print()

        audio_url = input("音声URL（MP3）: ").strip()
        avatar_url = input("画像URL: ").strip()

        if not audio_url or not avatar_url:
            print("❌ URLが入力されませんでした")
            return

        test_did_with_urls(audio_url, avatar_url, api_key)

    else:
        print("❌ 無効な選択です")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n中断されました")
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
