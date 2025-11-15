"""
テストファイルアップロードスクリプト

ローカルの音声・画像ファイルをCloudinaryにアップロードしてURLを取得します。
D-IDテストで使用するためのヘルパースクリプトです。
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import cloudinary
import cloudinary.uploader
import toml


def upload_audio(file_path: str) -> str:
    """
    音声ファイルをCloudinaryにアップロード

    Args:
        file_path: ローカルファイルパス（MP3, WAV等）

    Returns:
        アップロードされたファイルのURL
    """
    print(f"音声ファイルをアップロード中: {file_path}")

    result = cloudinary.uploader.upload(
        file_path,
        resource_type="video",  # 音声も"video"
        format="mp3",  # MP3に変換
        folder="ai-avatar/test",
        overwrite=True,
        eager=[{"format": "mp3"}],  # MP3変換を強制
        eager_async=False  # 変換完了まで待機
    )

    url = result["secure_url"]
    print(f"✅ アップロード完了: {url}")

    return url


def upload_image(file_path: str) -> str:
    """
    画像ファイルをCloudinaryにアップロード

    Args:
        file_path: ローカルファイルパス（JPG, PNG等）

    Returns:
        アップロードされたファイルのURL
    """
    print(f"画像ファイルをアップロード中: {file_path}")

    result = cloudinary.uploader.upload(
        file_path,
        resource_type="image",
        folder="ai-avatar/test",
        overwrite=True
    )

    url = result["secure_url"]
    print(f"✅ アップロード完了: {url}")

    return url


def main():
    """
    メイン処理
    """
    # Cloudinary設定読み込み
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

    print("=" * 60)
    print("テストファイル アップロードツール")
    print("=" * 60)
    print()

    print("アップロードするファイルを選択してください：")
    print()
    print("1. 音声ファイル（MP3, WAV等）")
    print("2. 画像ファイル（JPG, PNG等）")
    print("3. 両方")
    print()

    choice = input("選択 (1/2/3): ").strip()

    audio_url = None
    image_url = None

    if choice in ["1", "3"]:
        print()
        audio_path = input("音声ファイルのパス: ").strip()
        if audio_path:
            audio_path = audio_path.strip('"')  # ダブルクォート削除
            if Path(audio_path).exists():
                audio_url = upload_audio(audio_path)
            else:
                print(f"❌ ファイルが見つかりません: {audio_path}")

    if choice in ["2", "3"]:
        print()
        image_path = input("画像ファイルのパス: ").strip()
        if image_path:
            image_path = image_path.strip('"')  # ダブルクォート削除
            if Path(image_path).exists():
                image_url = upload_image(image_path)
            else:
                print(f"❌ ファイルが見つかりません: {image_path}")

    print()
    print("=" * 60)
    print("アップロード完了")
    print("=" * 60)
    print()

    if audio_url:
        print(f"音声URL: {audio_url}")
        print()

    if image_url:
        print(f"画像URL: {image_url}")
        print()

    if audio_url or image_url:
        print("これらのURLを test_did_standalone.py で使用できます")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n中断されました")
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
