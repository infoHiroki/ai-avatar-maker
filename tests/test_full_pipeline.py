"""
D-ID 完全テストスクリプト

Cartesiaで音声生成 → Cloudinaryにアップロード → D-IDで動画生成
のフルフローをテストします。
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import time
import toml
import cloudinary
import cloudinary.uploader

from src.modules.cartesia import CartesiaClient
from src.modules.did import DIDClient
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """
    メイン処理
    """
    print("=" * 60)
    print("D-ID 完全テスト（音声生成 → 動画生成）")
    print("=" * 60)
    print()

    # 設定読み込み
    secrets_path = project_root / ".streamlit" / "secrets.toml"

    if not secrets_path.exists():
        print("❌ エラー: .streamlit/secrets.toml が見つかりません")
        return

    secrets = toml.load(secrets_path)

    # Cloudinary初期化
    cloudinary.config(
        cloud_name=secrets["cloudinary"]["cloud_name"],
        api_key=secrets["cloudinary"]["api_key"],
        api_secret=secrets["cloudinary"]["api_secret"]
    )

    # ステップ1: テキスト入力
    print("ステップ1: テキスト入力")
    print("-" * 60)
    print("短いテキストを入力してください（例: こんにちは、テストです）")
    text = input("テキスト: ").strip()

    if not text:
        print("❌ テキストが入力されませんでした")
        return

    print()

    # ステップ2: 音声生成（Cartesia）
    print("ステップ2: 音声生成（Cartesia）")
    print("-" * 60)

    cartesia = CartesiaClient(
        api_key=secrets["cartesia"]["api_key"],
        voice_id=secrets["cartesia"]["voice_id"]
    )

    output_path = project_root / "test_output.wav"

    print(f"音声生成中: {text}")
    audio_path, duration, err = cartesia.generate(text, str(output_path))

    if err:
        print(f"❌ 音声生成エラー: {err}")
        return

    print(f"✅ 音声生成成功: {audio_path}")
    print(f"   時間: {duration:.1f}秒")
    print()

    # ステップ3: 音声アップロード（Cloudinary）
    print("ステップ3: 音声アップロード（Cloudinary）")
    print("-" * 60)

    print("Cloudinaryにアップロード中...")

    result = cloudinary.uploader.upload(
        audio_path,
        resource_type="video",
        format="mp3",
        folder="ai-avatar/test",
        overwrite=True,
        eager=[{"format": "mp3"}],
        eager_async=False
    )

    audio_url = result["secure_url"]
    print(f"✅ アップロード成功: {audio_url}")
    print()

    # ステップ4: アバター画像URL
    print("ステップ4: アバター画像URL")
    print("-" * 60)

    print("アバター画像URLを選択してください：")
    print()
    print("1. D-ID公式サンプル（Alice）")
    print("2. カスタムURL（自分の画像）")
    print()

    choice = input("選択 (1 or 2): ").strip()

    if choice == "1":
        avatar_url = "https://d-id-public-bucket.s3.amazonaws.com/alice.jpg"
        print(f"使用する画像: {avatar_url}")
    elif choice == "2":
        avatar_url = input("画像URL: ").strip()
        if not avatar_url:
            print("❌ URLが入力されませんでした")
            return
    else:
        print("❌ 無効な選択です")
        return

    print()

    # ステップ5: 動画生成（D-ID）
    print("ステップ5: 動画生成（D-ID）")
    print("-" * 60)

    did = DIDClient(api_key=secrets["did"]["api_key"])

    print("動画生成リクエスト送信中...")
    print("（最大5分かかる場合があります）")
    print()

    start_time = time.time()
    video, err = did.generate(
        audio_url=audio_url,
        avatar_url=avatar_url
    )
    elapsed = time.time() - start_time

    if err:
        print(f"❌ 動画生成エラー: {err}")
        print(f"   エラータイプ: {type(err).__name__}")

        if hasattr(err, 'status_code'):
            print(f"   HTTPステータス: {err.status_code}")
        if hasattr(err, 'response'):
            print(f"   レスポンス: {err.response}")

        return

    print()
    print("=" * 60)
    print("✅ 完全成功！")
    print("=" * 60)
    print()
    print(f"動画URL: {video.video_url}")
    print(f"動画時間: {video.duration_seconds}秒")
    print(f"解像度: {video.resolution}")
    print()
    print(f"総処理時間: {elapsed:.1f}秒")
    print()
    print("動画URLをブラウザで開いて確認してください")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n中断されました")
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
