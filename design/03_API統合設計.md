# API統合設計書

**プロジェクト名**: ブログ記事→YouTube動画自動生成システム
**バージョン**: 1.0.0
**作成日**: 2025年11月15日

---

## 📋 目次

1. [API一覧](#api一覧)
2. [OpenAI API (ChatGPT)](#openai-api-chatgpt)
3. [Cartesia API](#cartesia-api)
4. [D-ID API](#d-id-api)
5. [Cloudinary API](#cloudinary-api)
6. [YouTube Data API](#youtube-data-api)
7. [共通設計](#共通設計)

---

## API一覧

| API | 用途 | 認証方式 | プロトコル |
|-----|------|---------|-----------|
| OpenAI API | スクリプト生成 | Bearer Token | HTTPS/REST |
| Cartesia API | 音声生成 | API Key | WebSocket |
| D-ID API | 動画生成 | API Key | HTTPS/REST |
| Cloudinary API | 音声ホスティング | API Key/Secret | HTTPS/REST |
| YouTube Data API | 動画投稿 | OAuth 2.0 | HTTPS/REST |

---

## OpenAI API (ChatGPT)

### 基本情報

```yaml
ベースURL: https://api.openai.com/v1
ドキュメント: https://platform.openai.com/docs/
推奨モデル: gpt-4o-mini
月額コスト: $2程度（週2本想定）
```

### 認証

```python
import requests

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
```

### エンドポイント

#### POST /chat/completions

**用途**: チャット補完（スクリプト生成）

**リクエスト**:
```python
{
    "model": "gpt-4o-mini",
    "messages": [
        {
            "role": "system",
            "content": "YouTubeスクリプト生成アシスタント"
        },
        {
            "role": "user",
            "content": "以下のブログ記事を150単語のYouTubeスクリプトに変換:\n{blog_content}"
        }
    ],
    "max_tokens": 500,
    "temperature": 0.7
}
```

**レスポンス（成功）**:
```python
{
    "id": "chatcmpl-xxx",
    "object": "chat.completion",
    "created": 1234567890,
    "model": "gpt-4o-mini",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "今日は〜について解説します..."
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 100,
        "completion_tokens": 150,
        "total_tokens": 250
    }
}
```

**エラーレスポンス**:
```python
{
    "error": {
        "message": "Invalid API key",
        "type": "invalid_request_error",
        "code": "invalid_api_key"
    }
}
```

### エラーハンドリング

```python
def call_chatgpt(prompt: str, api_key: str) -> Tuple[Optional[str], Optional[Exception]]:
    """ChatGPT API呼び出し"""
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "YouTubeスクリプト生成"},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.7
            },
            timeout=30
        )

        if response.status_code != 200:
            return (None, Exception(f"API error: {response.status_code} - {response.text}"))

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return (content, None)

    except requests.Timeout:
        return (None, Exception("APIタイムアウト（30秒）"))
    except requests.RequestException as e:
        return (None, e)
    except KeyError as e:
        return (None, Exception(f"レスポンス解析エラー: {e}"))
```

### レート制限

```yaml
制限:
  - gpt-4o-mini: 200 requests/min
  - トークン: 10,000,000 tokens/min

対策:
  - リトライ（指数バックオフ）
  - レート制限エラー（429）時は60秒待機
```

---

## Cartesia API

### 基本情報

```yaml
ベースURL: wss://api.cartesia.ai/v1
ドキュメント: https://docs.cartesia.ai/
プラン: Pro（$5/月、100,000文字）
```

### 認証

```python
# WebSocket接続時にAPI Keyを送信
ws_url = f"wss://api.cartesia.ai/v1/audio/stream?api_key={api_key}"
```

### WebSocket通信

#### 接続

```python
import websockets
import json

async def connect_cartesia(api_key: str, voice_id: str):
    uri = f"wss://api.cartesia.ai/v1/audio/stream?api_key={api_key}"

    async with websockets.connect(uri) as websocket:
        # 初期化メッセージ送信
        init_message = {
            "type": "init",
            "voice_id": voice_id,
            "model": "sonic-japanese",
            "output_format": {
                "container": "mp3",
                "encoding": "mp3",
                "sample_rate": 44100
            }
        }
        await websocket.send(json.dumps(init_message))

        # 応答受信
        response = await websocket.recv()
        # ...
```

#### 音声生成リクエスト

```python
# テキスト送信
text_message = {
    "type": "text",
    "text": "こんにちは、世界",
    "speed": 1.0,
    "emotion": "neutral"
}
await websocket.send(json.dumps(text_message))

# ストリーミング受信
audio_chunks = []
while True:
    message = await websocket.recv()
    data = json.loads(message)

    if data["type"] == "audio":
        # Base64デコードして音声データを保存
        audio_data = base64.b64decode(data["data"])
        audio_chunks.append(audio_data)
    elif data["type"] == "done":
        break
```

### エラーハンドリング

```python
async def generate_audio_cartesia(
    text: str,
    api_key: str,
    voice_id: str
) -> Tuple[Optional[bytes], Optional[Exception]]:
    """Cartesia音声生成"""
    try:
        uri = f"wss://api.cartesia.ai/v1/audio/stream?api_key={api_key}"

        async with websockets.connect(uri, timeout=60) as websocket:
            # 初期化
            await websocket.send(json.dumps({
                "type": "init",
                "voice_id": voice_id,
                "model": "sonic-japanese",
                "output_format": {"container": "mp3", "sample_rate": 44100}
            }))

            # テキスト送信
            await websocket.send(json.dumps({
                "type": "text",
                "text": text,
                "speed": 1.0
            }))

            # 音声データ受信
            audio_chunks = []
            while True:
                message = await websocket.recv()
                data = json.loads(message)

                if data["type"] == "audio":
                    audio_data = base64.b64decode(data["data"])
                    audio_chunks.append(audio_data)
                elif data["type"] == "done":
                    break
                elif data["type"] == "error":
                    return (None, Exception(f"Cartesia error: {data['message']}"))

            audio = b"".join(audio_chunks)
            return (audio, None)

    except websockets.exceptions.WebSocketException as e:
        return (None, Exception(f"WebSocket error: {e}"))
    except Exception as e:
        return (None, e)
```

### レート制限

```yaml
制限:
  - 100,000文字/月（Pro）
  - 同時接続: 10

対策:
  - 文字数カウンター実装
  - 月次使用量トラッキング
```

---

## D-ID API

### 基本情報

```yaml
ベースURL: https://api.d-id.com
ドキュメント: https://docs.d-id.com/
プラン: Lite ($5.9/月、5分) or Pro ($49/月、15分)
```

### 認証

```python
headers = {
    "Authorization": f"Basic {api_key}",
    "Content-Type": "application/json"
}
```

### エンドポイント

#### POST /talks

**用途**: リップシンク動画生成

**リクエスト**:
```python
{
    "script": {
        "type": "audio",
        "audio_url": "https://res.cloudinary.com/.../audio.mp3"
    },
    "source_url": "https://res.cloudinary.com/.../avatar.jpg",
    "config": {
        "stitch": true,
        "result_format": "mp4"
    }
}
```

**レスポンス（成功）**:
```python
{
    "id": "tlk_xyz123",
    "object": "talk",
    "created_at": "2025-01-15T10:00:00.000Z",
    "status": "created"
}
```

#### GET /talks/{id}

**用途**: 動画生成ステータス確認

**レスポンス（処理中）**:
```python
{
    "id": "tlk_xyz123",
    "status": "started",  # or "created", "processing"
    "created_at": "...",
    "started_at": "..."
}
```

**レスポンス（完了）**:
```python
{
    "id": "tlk_xyz123",
    "status": "done",
    "result_url": "https://d-id-talks-prod.s3.amazonaws.com/.../video.mp4",
    "duration": 60.5,
    "created_at": "...",
    "started_at": "...",
    "completed_at": "..."
}
```

**レスポンス（エラー）**:
```python
{
    "id": "tlk_xyz123",
    "status": "error",
    "error": {
        "kind": "InvalidInput",
        "description": "Audio URL is invalid"
    }
}
```

### 実装例

```python
import requests
import time

class DIDClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.d-id.com"

    def create_talk(
        self,
        audio_url: str,
        avatar_url: str
    ) -> Tuple[Optional[str], Optional[Exception]]:
        """動画生成リクエスト"""
        try:
            response = requests.post(
                f"{self.base_url}/talks",
                headers={
                    "Authorization": f"Basic {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "script": {"type": "audio", "audio_url": audio_url},
                    "source_url": avatar_url,
                    "config": {"stitch": True, "result_format": "mp4"}
                },
                timeout=30
            )

            if response.status_code != 201:
                return (None, Exception(f"API error: {response.status_code}"))

            data = response.json()
            talk_id = data["id"]
            return (talk_id, None)

        except Exception as e:
            return (None, e)

    def poll_status(
        self,
        talk_id: str,
        timeout_seconds: int = 300
    ) -> Tuple[Optional[str], Optional[Exception]]:
        """ステータスポーリング"""
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            try:
                response = requests.get(
                    f"{self.base_url}/talks/{talk_id}",
                    headers={"Authorization": f"Basic {self.api_key}"},
                    timeout=10
                )

                if response.status_code != 200:
                    return (None, Exception(f"API error: {response.status_code}"))

                data = response.json()
                status = data["status"]

                if status == "done":
                    return (data["result_url"], None)
                elif status == "error":
                    error_msg = data.get("error", {}).get("description", "Unknown error")
                    return (None, Exception(f"D-ID error: {error_msg}"))

                # 処理中 - 5秒待機
                time.sleep(5)

            except Exception as e:
                return (None, e)

        return (None, Exception(f"タイムアウト（{timeout_seconds}秒）"))
```

### レート制限

```yaml
制限:
  - Lite: 5分/月
  - Pro: 15分/月
  - リクエスト: 60 requests/min

対策:
  - 動画長トラッキング
  - 月次使用量監視
```

---

## Cloudinary API

### 基本情報

```yaml
用途: 音声ファイルホスティング
プラン: 無料（25GB）
ドキュメント: https://cloudinary.com/documentation
```

### 認証

```python
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name="your_cloud_name",
    api_key="your_api_key",
    api_secret="your_api_secret"
)
```

### アップロード

```python
def upload_audio_to_cloudinary(
    file_path: str,
    public_id: Optional[str] = None
) -> Tuple[Optional[str], Optional[Exception]]:
    """音声ファイルをCloudinaryにアップロード"""
    try:
        result = cloudinary.uploader.upload(
            file_path,
            resource_type="video",  # 音声も"video"
            public_id=public_id,
            folder="blog-to-youtube/audio",
            overwrite=True
        )

        url = result["secure_url"]
        return (url, None)

    except cloudinary.exceptions.Error as e:
        return (None, e)
```

---

## YouTube Data API

### 基本情報

```yaml
ベースURL: https://www.googleapis.com/youtube/v3
ドキュメント: https://developers.google.com/youtube/v3
認証: OAuth 2.0
```

### 認証フロー

```python
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def authenticate_youtube(credentials_path: str):
    """YouTube OAuth認証"""
    flow = InstalledAppFlow.from_client_secrets_file(
        credentials_path,
        SCOPES
    )
    credentials = flow.run_local_server(port=0)
    youtube = build("youtube", "v3", credentials=credentials)
    return youtube
```

### 動画アップロード

```python
from googleapiclient.http import MediaFileUpload

def upload_to_youtube(
    youtube,
    video_path: str,
    title: str,
    description: str
) -> Tuple[Optional[str], Optional[Exception]]:
    """YouTube動画投稿"""
    try:
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "categoryId": "22"  # People & Blogs
                },
                "status": {
                    "privacyStatus": "private",  # 下書き
                    "selfDeclaredMadeForKids": False
                }
            },
            media_body=MediaFileUpload(
                video_path,
                chunksize=-1,
                resumable=True
            )
        )

        response = request.execute()
        video_id = response["id"]
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        return (youtube_url, None)

    except Exception as e:
        return (None, e)
```

---

## 共通設計

### リトライロジック

```python
from typing import Callable, TypeVar
import time

T = TypeVar('T')

def retry_with_backoff(
    func: Callable[[], Tuple[Optional[T], Optional[Exception]]],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0
) -> Tuple[Optional[T], Optional[Exception]]:
    """
    指数バックオフでリトライ

    Args:
        func: 実行する関数
        max_retries: 最大リトライ回数
        initial_delay: 初期遅延（秒）
        backoff_factor: バックオフ係数

    Returns:
        (result, error): 結果またはエラー
    """
    delay = initial_delay

    for attempt in range(max_retries):
        result, err = func()

        if err is None:
            return (result, None)

        # 最後の試行以外はリトライ
        if attempt < max_retries - 1:
            logger.warning(f"リトライ {attempt + 1}/{max_retries}: {delay}秒待機")
            time.sleep(delay)
            delay *= backoff_factor

    return (None, Exception(f"{max_retries}回リトライしましたが失敗"))
```

### タイムアウト処理

```python
DEFAULT_TIMEOUT = 30  # 秒

# requests使用時
response = requests.get(url, timeout=DEFAULT_TIMEOUT)

# WebSocket使用時
async with websockets.connect(uri, timeout=60) as ws:
    pass
```

### ログ記録

```python
import logging

logger = logging.getLogger(__name__)

def api_call_with_logging(api_name: str, func: Callable):
    """API呼び出しをログ記録"""
    logger.info(f"{api_name} API呼び出し開始")
    start_time = time.time()

    result, err = func()

    elapsed = time.time() - start_time
    if err:
        logger.error(f"{api_name} API失敗 ({elapsed:.2f}秒): {err}")
    else:
        logger.info(f"{api_name} API成功 ({elapsed:.2f}秒)")

    return (result, err)
```

---

**最終更新**: 2025年11月15日
**次回レビュー**: API実装時
