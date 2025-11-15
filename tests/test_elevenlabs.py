"""
ElevenLabs テストスクリプト

Cartesiaと同じテキストでElevenLabsの音声を生成してD-IDで動画化
音声品質を比較するためのスクリプト
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import time
import toml
import cloudinary
import cloudinary.uploader

from src.modules.elevenlabs import ElevenLabsClient
from src.modules.did import DIDClient

# 設定読み込み
secrets_path = project_root / ".streamlit" / "secrets.toml"
secrets = toml.load(secrets_path)

# Cloudinary初期化
cloudinary.config(
    cloud_name=secrets["cloudinary"]["cloud_name"],
    api_key=secrets["cloudinary"]["api_key"],
    api_secret=secrets["cloudinary"]["api_secret"]
)

print("=" * 60)
print("ElevenLabs + D-ID テスト")
print("=" * 60)
print()

# Cartesiaと同じテキストを使用
test_text = """
こんにちは、AIアバター動画生成システムのテストを行っています。
今回は、Cartesiaの音声生成とD-IDのリップシンク機能を組み合わせて、
本格的な動画を作成できるか検証しています。
このテキストは約20秒から30秒程度の長さを想定しており、
実際のブログ記事やYouTube動画に使用する際の
実用的なテストケースとなります。
音声の自然さとリップシンクの品質を確認してみましょう。
""".strip()

print(f"テストテキスト:")
print(f"  {test_text[:50]}...")
print(f"  文字数: {len(test_text)}文字")
print()

# ステップ1: 音声生成（ElevenLabs）
print("ステップ1: 音声生成（ElevenLabs）")
print("-" * 60)

elevenlabs = ElevenLabsClient(
    api_key=secrets["elevenlabs"]["api_key"],
    voice_id=secrets["elevenlabs"]["voice_id"]
)

print("音声生成中...")
audio, err = elevenlabs.generate(test_text)

if err:
    print(f"[ERROR] エラー: {err}")
    sys.exit(1)

print(f"[OK] 音声生成成功: {audio.duration_seconds:.1f}秒")
print()

# ステップ2: 音声URL取得
print("ステップ2: 音声URL取得")
print("-" * 60)

audio_url = str(audio.audio_url)
print(f"[OK] 音声URL: {audio_url}")
print()

# ステップ3: D-ID動画生成
print("ステップ3: D-ID 動画生成")
print("-" * 60)

# D-ID公式サンプル画像を使用（Cartesiaと同じ）
avatar_url = "https://d-id-public-bucket.s3.amazonaws.com/alice.jpg"

print(f"アバター: {avatar_url}")
print()
print("動画生成中...（最大5分かかります）")
print()

did = DIDClient(api_key=secrets["did"]["api_key"])

start_time = time.time()
video, err = did.generate(
    audio_url=audio_url,
    avatar_url=avatar_url
)
elapsed = time.time() - start_time

print()

if err:
    print("=" * 60)
    print("[ERROR] D-ID エラー")
    print("=" * 60)
    print()
    print(f"エラー: {err}")
    print(f"タイプ: {type(err).__name__}")

    if hasattr(err, 'status_code'):
        print(f"HTTPステータス: {err.status_code}")
    if hasattr(err, 'response'):
        print(f"レスポンス: {err.response}")

    print()
    print(f"音声URL: {audio_url}")
    print("-> ブラウザで開いて確認してください")

    sys.exit(1)

print("=" * 60)
print("[SUCCESS] 全ステップ成功！")
print("=" * 60)
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
print()
print("Cartesiaと比較して音声品質を確認してください！")
