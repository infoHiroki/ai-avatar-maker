# Cartesia + D-ID 実装ガイド（完全版）

**作成日**: 2025年11月15日
**対象**: YouTube動画制作（週2本、5分想定）
**月額コスト**: $56 (¥8,000) または $12.9 (¥1,800) - Shorts

---

## 📋 目次

1. [概要](#概要)
2. [必要なもの](#必要なもの)
3. [セットアップ（Week 1）](#セットアップweek-1)
4. [音声クローン作成](#音声クローン作成)
5. [Python実装](#python実装)
6. [D-IDとの統合](#d-idとの統合)
7. [完全なワークフロー](#完全なワークフロー)
8. [コスト管理](#コスト管理)
9. [トラブルシューティング](#トラブルシューティング)
10. [品質評価とElevenLabsへの移行](#品質評価とelevenlabsへの移行)

---

## 概要

### この構成を選んだ理由

```yaml
目的: ブログ記事をYouTube動画に自動変換
必須要件:
  ✅ 声のクローニング（本人の声）
  ✅ APIベース（ローカルGPU不使用）
  ✅ リップシンク
  ✅ 自動化可能
  ✅ コスト効率

選定結果: Cartesia + D-ID
理由:
  ✅ 年間$204（¥30,000）のコスト削減
  ✅ わずか5秒のサンプルで開始可能
  ✅ 100,000文字/月の余裕
  ✅ 読み間違いが少ない
  ✅ 移行リスクが低い（ダメならElevenLabsへ）
```

### 処理フロー

```
ブログ記事
  ↓ ChatGPT API
スクリプト（テキスト）
  ↓ Cartesia API
音声ファイル（本人の声、5秒サンプルから生成）
  ↓ Cloudinary
音声URL
  ↓ D-ID API
リップシンク動画
  ↓ YouTube API
YouTube投稿
```

### コスト内訳

```yaml
5分動画（週2本）:
  Cartesia Pro: $5/月
  D-ID Pro: $49/月
  ChatGPT API: $2/月
  合計: $56/月 (¥8,000)

60秒Shorts（週2本）⭐推奨開始:
  Cartesia Pro: $5/月
  D-ID Lite: $5.9/月
  ChatGPT API: $2/月
  合計: $12.9/月 (¥1,800)
```

---

## 必要なもの

### アカウント

- [ ] **Cartesia** - https://cartesia.ai/
  - 無料プラン: 20,000クレジット（音声クローン不可）
  - Pro プラン: $5/月（100,000文字、音声クローン可能）

- [ ] **D-ID** - https://studio.d-id.com/
  - Lite: $5.9/月（5分/月）
  - Pro: $49/月（15分/月）

- [ ] **Cloudinary**（音声ファイルホスティング用）
  - 無料プラン: 25クレジット/月

- [ ] **OpenAI**（スクリプト生成用）
  - 従量課金

### 準備するもの

- [ ] Python 3.8以上
- [ ] 静かな環境（音声録音用）
- [ ] マイク（スマホでもOK）
- [ ] 自分の顔写真（1024x1024px推奨）

### 開発環境

```bash
pip install requests
pip install openai
pip install cloudinary
pip install python-dotenv
```

---

## セットアップ（Week 1）

### Day 1: Cartesiaアカウント作成

#### ステップ1: サインアップ

1. https://cartesia.ai/ にアクセス
2. 「Sign Up」をクリック
3. メールアドレスで登録
4. メール認証を完了

#### ステップ2: APIキー取得

1. ダッシュボードにログイン
2. 「API Keys」セクションへ移動
3. 「Create New API Key」をクリック
4. APIキーをコピーして安全に保存

```bash
# .env ファイルに保存
CARTESIA_API_KEY=your_api_key_here
```

#### ステップ3: プラン選択

**まずは無料プランで開始**（音声クローン機能を試すため）

```yaml
無料プラン（初回テスト用）:
  - 20,000クレジット
  - 音声クローン不可（プリセット音声のみ）
  - 商用利用不可

目的:
  1. API接続テスト
  2. インターフェース確認
  3. 基本的な音声生成テスト
```

**テスト完了後、Pro プランにアップグレード**

```yaml
Pro プラン（本番用）:
  月額: $5
  文字数: 100,000クレジット
  音声クローン: 可能
  商用利用: 可能
  並列リクエスト: 3
```

---

### Day 2: 音声サンプル録音

#### 録音準備

```yaml
環境:
  ✅ 静かな部屋
  ✅ 窓を閉める
  ✅ エアコン・扇風機OFF
  ✅ 通知音OFF

機材:
  ✅ スマホのボイスメモでOK
  ✅ パソコンのマイクでもOK
  ✅ 外付けマイク（推奨だが必須ではない）

時間:
  わずか5秒でOK！
```

#### 録音スクリプト例（5秒）

**パターンA: 自己紹介系**
```
こんにちは。[あなたの名前]です。
今日も良い一日にしましょう。
```

**パターンB: 解説系**
```
本日は、AIアバターの活用方法について
お話しします。
```

**パターンC: 多様な音素を含む**
```
あいうえお、かきくけこ。
ラ行、ワ行も含めて、自然に発音します。
```

#### 録音のコツ

```yaml
音量:
  - 大きすぎず、小さすぎず
  - 通常の会話レベル

発音:
  - クリアに、はっきりと
  - 早口にならない
  - 感情は自然に

品質:
  - ノイズなし
  - エコーなし
  - クリッピングなし
```

#### ファイル形式

```
推奨: MP3, WAV, M4A
サイズ: 制限なし（5秒なら数百KB）
ビットレート: 128kbps以上推奨
```

#### 録音後の確認

```bash
# 録音を再生して確認
✅ ノイズがないか
✅ 声が明瞭か
✅ 音量が適切か
✅ 途中で途切れていないか

問題があれば録り直す（5秒なので簡単）
```

---

## 音声クローン作成

### ステップ1: Pro プランにアップグレード

```
1. Cartesiaダッシュボード → Billing
2. 「Upgrade to Pro」をクリック
3. 支払い情報入力（$5/月）
4. アップグレード完了
```

### ステップ2: 音声クローンAPI実行

#### Pythonスクリプト

```python
import requests
import os
from dotenv import load_dotenv

load_dotenv()

CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY")

def create_voice_clone(audio_file_path, voice_name, language="ja"):
    """
    Cartesiaで音声クローンを作成

    Args:
        audio_file_path: 音声サンプルファイルのパス
        voice_name: 音声の名前（例: "MyVoice"）
        language: 言語コード（"ja" = 日本語）

    Returns:
        voice_id: 作成された音声のID
    """
    url = "https://api.cartesia.ai/voices/clone"

    headers = {
        "Authorization": f"Bearer {CARTESIA_API_KEY}",
        "Cartesia-Version": "2025-04-16"
    }

    # 音声ファイルを開く
    with open(audio_file_path, "rb") as audio_file:
        files = {
            "clip": audio_file
        }

        data = {
            "name": voice_name,
            "language": language,
            "description": "My cloned voice for YouTube videos"
        }

        response = requests.post(url, headers=headers, files=files, data=data)

    if response.status_code == 200:
        result = response.json()
        voice_id = result["id"]
        print(f"✅ 音声クローン作成成功！")
        print(f"Voice ID: {voice_id}")
        print(f"Voice Name: {result['name']}")
        return voice_id
    else:
        print(f"❌ エラー: {response.status_code}")
        print(f"詳細: {response.text}")
        return None

# 実行例
if __name__ == "__main__":
    audio_path = "my_voice_sample.mp3"  # あなたの5秒音声ファイル
    voice_id = create_voice_clone(audio_path, "MyYouTubeVoice", "ja")

    # voice_idを保存（後で使用）
    if voice_id:
        with open(".env", "a") as f:
            f.write(f"\nCARTESIA_VOICE_ID={voice_id}\n")
```

#### 実行

```bash
python create_voice_clone.py
```

#### 期待される出力

```
✅ 音声クローン作成成功！
Voice ID: vc_abc123def456ghi789
Voice Name: MyYouTubeVoice
```

### ステップ3: Voice IDの保存

```bash
# .env ファイルに追加
CARTESIA_API_KEY=your_api_key_here
CARTESIA_VOICE_ID=vc_abc123def456ghi789
```

---

## Python実装

### 完全な統合スクリプト

```python
import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

# API Keys
CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY")
CARTESIA_VOICE_ID = os.getenv("CARTESIA_VOICE_ID")
D_ID_API_KEY = os.getenv("D_ID_API_KEY")
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

# ========================================
# ステップ1: Cartesiaで音声生成
# ========================================

def generate_audio_cartesia(text, output_path="output_audio.mp3"):
    """
    Cartesia APIで音声生成

    Args:
        text: テキスト（日本語）
        output_path: 出力ファイルパス

    Returns:
        output_path: 生成された音声ファイルのパス
    """
    url = f"https://api.cartesia.ai/tts/bytes"

    headers = {
        "Authorization": f"Bearer {CARTESIA_API_KEY}",
        "Cartesia-Version": "2025-04-16",
        "Content-Type": "application/json"
    }

    payload = {
        "model_id": "sonic-english",  # または "sonic-multilingual"
        "voice": {
            "mode": "id",
            "id": CARTESIA_VOICE_ID
        },
        "transcript": text,
        "language": "ja",
        "output_format": {
            "container": "mp3",
            "encoding": "mp3",
            "sample_rate": 44100
        }
    }

    print(f"🎤 音声生成中... (文字数: {len(text)})")

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"✅ 音声生成完了: {output_path}")
        return output_path
    else:
        print(f"❌ エラー: {response.status_code}")
        print(f"詳細: {response.text}")
        return None

# ========================================
# ステップ2: Cloudinaryにアップロード
# ========================================

def upload_to_cloudinary(file_path):
    """
    CloudinaryにファイルをアップロードしてURLを取得

    Args:
        file_path: ローカルファイルパス

    Returns:
        url: CloudinaryのURL
    """
    import cloudinary
    import cloudinary.uploader

    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET
    )

    print(f"☁️ Cloudinaryにアップロード中...")

    result = cloudinary.uploader.upload(
        file_path,
        resource_type="auto"
    )

    audio_url = result["secure_url"]
    print(f"✅ アップロード完了: {audio_url}")

    return audio_url

# ========================================
# ステップ3: D-IDで動画生成
# ========================================

def generate_video_did(audio_url, avatar_image_url):
    """
    D-ID APIで動画生成

    Args:
        audio_url: 音声ファイルのURL
        avatar_image_url: アバター画像のURL

    Returns:
        video_url: 生成された動画のURL
    """
    headers = {
        "Authorization": f"Basic {D_ID_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "source_url": avatar_image_url,
        "script": {
            "type": "audio",
            "audio_url": audio_url
        },
        "config": {
            "stitch": True  # 複数クリップを結合
        }
    }

    print(f"🎬 D-IDで動画生成中...")

    # 動画生成リクエスト
    response = requests.post(
        "https://api.d-id.com/talks",
        headers=headers,
        json=payload
    )

    if response.status_code != 201:
        print(f"❌ エラー: {response.status_code}")
        print(f"詳細: {response.text}")
        return None

    talk_id = response.json()["id"]
    print(f"Talk ID: {talk_id}")

    # 完了待ち
    while True:
        status_response = requests.get(
            f"https://api.d-id.com/talks/{talk_id}",
            headers=headers
        )

        status_data = status_response.json()
        status = status_data["status"]

        print(f"ステータス: {status}")

        if status == "done":
            video_url = status_data["result_url"]
            print(f"✅ 動画生成完了！")
            print(f"動画URL: {video_url}")
            return video_url
        elif status == "error":
            print(f"❌ エラー発生")
            print(f"詳細: {status_data}")
            return None

        time.sleep(10)  # 10秒待機

# ========================================
# メイン処理
# ========================================

def create_video_from_text(text, avatar_image_url):
    """
    テキストからAIアバター動画を生成

    Args:
        text: スクリプトテキスト
        avatar_image_url: アバター画像のURL

    Returns:
        video_url: 完成した動画のURL
    """
    print("=" * 50)
    print("AIアバター動画生成開始")
    print("=" * 50)

    # ステップ1: 音声生成
    audio_path = generate_audio_cartesia(text)
    if not audio_path:
        return None

    # ステップ2: 音声アップロード
    audio_url = upload_to_cloudinary(audio_path)

    # ステップ3: 動画生成
    video_url = generate_video_did(audio_url, avatar_image_url)

    print("=" * 50)
    print("完了！")
    print("=" * 50)

    return video_url

# ========================================
# 使用例
# ========================================

if __name__ == "__main__":
    # スクリプト
    script = """
    こんにちは。今日はAIアバターの活用方法についてお話しします。

    まず、AIアバターとは何かを説明します。
    AIアバターは、人工知能を使って作成された仮想的なキャラクターです。

    これにより、動画制作の効率が大幅に向上します。
    詳しく見ていきましょう。
    """

    # アバター画像URL（事前にCloudinaryなどにアップロード）
    avatar_url = "https://res.cloudinary.com/your-cloud/image/upload/your-avatar.jpg"

    # 動画生成
    video_url = create_video_from_text(script, avatar_url)

    if video_url:
        print(f"\n🎉 成功！動画URL: {video_url}")
```

---

## D-IDとの統合

### D-IDアカウント作成

#### ステップ1: サインアップ

1. https://studio.d-id.com/ にアクセス
2. 「Sign Up」をクリック
3. Google/Email で登録

#### ステップ2: APIキー取得

1. ダッシュボード → Settings → API Keys
2. 「Create API Key」をクリック
3. APIキーをコピー

```bash
# .env に追加
D_ID_API_KEY=your_d_id_api_key_here
```

#### ステップ3: プラン選択

**週2本 × 5分動画の場合:**
```yaml
D-ID Pro: $49/月
  - 15分/月
  - 週2本 × 5分 × 4週 = 40分必要
  - → 超過料金: $0.5/分 × 25分 = $12.5
  - 合計: $61.5/月
```

**週2本 × 60秒Shortsの場合（推奨）:**
```yaml
D-ID Lite: $5.9/月
  - 5分/月
  - 週2本 × 1分 × 4週 = 8分必要
  - → 超過料金: $0.3/分 × 3分 = $0.9
  - 合計: $6.8/月
```

### アバター画像準備

```yaml
推奨サイズ: 1024x1024px
形式: JPG, PNG
内容:
  ✅ 正面を向いた顔
  ✅ 明るい環境
  ✅ 背景はシンプル
  ✅ 表情は自然
  ✅ 高解像度

撮影のコツ:
  - スマホのポートレートモードでOK
  - 自然光が当たる場所
  - 背景は無地が理想
```

---

## 完全なワークフロー

### 準備（初回のみ）

```bash
# 1. 環境変数設定
cp .env.example .env
# .envファイルを編集してAPIキーを設定

# 2. 依存パッケージインストール
pip install -r requirements.txt

# 3. 音声クローン作成
python create_voice_clone.py
```

### 動画制作（毎回）

```python
# video_generator.py

from main import create_video_from_text

# ブログ記事からスクリプト生成（ChatGPT）
blog_post = """
[ブログ記事の内容]
"""

# ChatGPTでスクリプト変換（別途実装）
script = convert_blog_to_script(blog_post)

# アバター画像URL
avatar_url = "https://your-cloudinary-url/avatar.jpg"

# 動画生成
video_url = create_video_from_text(script, avatar_url)

# 動画ダウンロード（オプション）
download_video(video_url, "output_video.mp4")
```

### 週次ルーチン

```yaml
月曜日:
  - ブログ記事2本選定
  - ChatGPTでスクリプト生成
  - スクリプト確認・修正

火曜日:
  - 動画1本目生成
  - 品質確認

水曜日:
  - 動画2本目生成
  - 品質確認

木曜日:
  - サムネイル作成
  - 説明文作成

金曜日:
  - YouTube投稿
```

---

## コスト管理

### 文字数カウント

```python
def count_characters(text):
    """
    Cartesiaで消費するクレジット数を計算
    """
    char_count = len(text)
    credits = char_count  # 1文字 = 1クレジット

    print(f"文字数: {char_count}")
    print(f"消費クレジット: {credits}")
    print(f"残りクレジット: {100000 - credits} (Pro プラン)")

    return credits

# 使用例
script = "こんにちは。今日はAIについて説明します。"
count_characters(script)
```

### 月次コスト予測

```python
def calculate_monthly_cost(videos_per_week, video_length_seconds):
    """
    月次コストを計算

    Args:
        videos_per_week: 週あたりの動画本数
        video_length_seconds: 1本あたりの秒数
    """
    # Cartesia
    avg_chars_per_second = 8  # 日本語で約8文字/秒
    total_chars = videos_per_week * 4 * video_length_seconds * avg_chars_per_second
    cartesia_cost = 5  # Pro プラン

    # D-ID
    total_minutes = (videos_per_week * 4 * video_length_seconds) / 60

    if total_minutes <= 5:
        did_cost = 5.9  # Lite
    elif total_minutes <= 15:
        did_cost = 49  # Pro
    else:
        did_cost = 49 + (total_minutes - 15) * 0.5  # Pro + 超過料金

    # ChatGPT (推定)
    chatgpt_cost = 2

    total_cost = cartesia_cost + did_cost + chatgpt_cost

    print(f"=" * 50)
    print(f"月次コスト予測")
    print(f"=" * 50)
    print(f"動画本数: 週{videos_per_week}本 × 4週 = {videos_per_week * 4}本/月")
    print(f"動画長: {video_length_seconds}秒/本")
    print(f"総文字数: {total_chars:,}文字")
    print(f"-" * 50)
    print(f"Cartesia Pro: ${cartesia_cost}")
    print(f"D-ID: ${did_cost:.1f}")
    print(f"ChatGPT API: ${chatgpt_cost}")
    print(f"-" * 50)
    print(f"合計: ${total_cost:.1f}/月 (¥{total_cost * 150:.0f})")
    print(f"=" * 50)

# 使用例
calculate_monthly_cost(videos_per_week=2, video_length_seconds=300)  # 5分動画
calculate_monthly_cost(videos_per_week=2, video_length_seconds=60)   # 1分Shorts
```

---

## トラブルシューティング

### よくある問題と解決策

#### 1. 音声クローンが失敗する

```yaml
エラー: "Audio quality is insufficient"

原因:
  - 音声サンプルにノイズが多い
  - 音量が小さすぎる/大きすぎる

解決策:
  ✅ 静かな環境で録り直す
  ✅ 音量を調整して録り直す
  ✅ ノイズ除去ソフトを使用
```

#### 2. 音声が早口すぎる

```yaml
問題: Cartesiaの音声がやや早口

解決策A: テキストに句読点を多めに入れる
  例: 「今日は、AIアバターについて、お話しします。」

解決策B: 改行を入れて間を作る
  例:
    こんにちは。

    今日はAIアバターについてお話しします。

解決策C: それでもダメならElevenLabsに移行
  - 2-3日で切り替え可能
  - 月額+$17だが、品質向上
```

#### 3. D-ID APIエラー

```yaml
エラー: "Invalid audio URL"

原因:
  - Cloudinary URLが間違っている
  - URLが公開設定になっていない

解決策:
  ✅ Cloudinary URLを再確認
  ✅ URLをブラウザで開いて確認
  ✅ 公開設定を確認
```

#### 4. コストが予想より高い

```yaml
原因:
  - 文字数が多すぎる
  - D-IDの分数超過

解決策:
  ✅ スクリプトを簡潔にする
  ✅ Shortsから開始する（60秒）
  ✅ 月次レポートで使用量を確認
```

---

## 品質評価とElevenLabsへの移行

### 品質チェックリスト

```yaml
テスト動画3-5本作成後、以下を確認:

音声品質:
  [ ] 発音は明瞭か
  [ ] 読み間違いはないか
  [ ] 早口すぎないか
  [ ] イントネーションは自然か
  [ ] 聞き取りやすいか

リップシンク:
  [ ] 口の動きは自然か
  [ ] 音声とずれていないか

総合:
  [ ] 視聴者が違和感なく見られるか
  [ ] YouTube投稿レベルに達しているか
```

### 判断基準

```yaml
Cartesia継続を推奨:
  ✅ 上記チェックリストの80%以上がOK
  ✅ 視聴者から特にクレームなし
  ✅ コスト削減を優先したい

ElevenLabsへの移行を推奨:
  ❌ 早口が気になる
  ❌ 感情表現が不足
  ❌ 長編動画で違和感がある
  ❌ ブランドイメージを最優先
```

### ElevenLabsへの移行手順

**所要時間: 2-3日**

```yaml
Day 1:
  1. ElevenLabsアカウント作成
  2. Creator プラン登録 ($22/月)
  3. 1-2分の音声サンプル録音
  4. 音声クローン作成

Day 2:
  5. Python実装コード変更
     - Cartesia API → ElevenLabs API
     - 約30行のコード変更
  6. テスト動画1本作成

Day 3:
  7. 品質確認
  8. 本格運用開始
```

#### コード変更例

```python
# Cartesia版
def generate_audio_cartesia(text):
    url = "https://api.cartesia.ai/tts/bytes"
    # ... Cartesia固有の処理

# ↓ ElevenLabs版に変更

def generate_audio_elevenlabs(text):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    # ... ElevenLabs固有の処理

# メイン処理は変更不要
```

---

## まとめ

### 実装の流れ（再掲）

```
Week 1:
  Day 1: Cartesiaアカウント作成、APIキー取得
  Day 2: 5秒の音声サンプル録音
  Day 3: 音声クローン作成、D-IDアカウント作成
  Day 4: Python実装、テスト動画作成
  Day 5: 品質確認

Week 2:
  本格運用開始（週2本投稿）
```

### 最終コスト

```yaml
60秒Shorts（推奨開始）:
  月額: $12.9 (¥1,800)
  年額: $154.8 (¥23,000)

5分動画:
  月額: $56 (¥8,000)
  年額: $672 (¥100,000)

ElevenLabsとの比較:
  年間削減: $204 (¥30,000)
```

### 次のステップ

1. **今日**: Cartesiaアカウント作成
2. **今日**: 5秒の音声サンプル録音
3. **明日**: 音声クローン作成
4. **明日**: テスト動画1本作成
5. **今週中**: 品質確認・判断

### サポートリソース

- Cartesia公式ドキュメント: https://docs.cartesia.ai/
- D-ID公式ドキュメント: https://docs.d-id.com/
- このプロジェクトの比較資料: `resources/ElevenLabs_vs_Cartesia比較.md`

---

**作成日**: 2025年11月15日
**最終更新**: 2025年11月15日
**次回レビュー**: テスト動画作成後
