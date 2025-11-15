# YouTube Data API統合の実装可能性調査

**調査日**: 2025年11月15日
**調査目的**: Streamlit Community Cloudで動作するPythonアプリから、YouTube Data APIを使って動画を自動投稿する機能の実現可能性を評価する

---

## 📊 結論サマリー

### 総合評価: ⚠️ **実装は可能だが、非エンジニア運用には課題が多い**

| 項目 | 評価 | 詳細 |
|------|------|------|
| **技術的実装可能性** | ✅ 可能 | API自体は問題なく動作 |
| **非エンジニア運用** | ⚠️ 困難 | 初期設定が複雑、トラブル対応が難しい |
| **Streamlit Cloud対応** | ⚠️ 制約あり | ファイルシステム、OAuth認証に課題 |
| **本番運用の実用性** | ❌ 非推奨 | 代替案のほうが現実的 |

### 推奨アプローチ

```
🎯 推奨度: Zapier/Make.com ⭐⭐⭐⭐⭐
理由:
  ✅ ノーコードで実装可能
  ✅ 非エンジニアが運用可能
  ✅ OAuth認証が簡単
  ✅ エラーハンドリングが自動
  ✅ メンテナンスフリー
```

---

## 1. OAuth 2.0認証の実装難易度

### 1.1 基本的な認証フロー

YouTube Data APIは**OAuth 2.0認証が必須**です。APIキーでは動画アップロードができません。

**標準的な実装フロー:**

```python
# 公式サンプルコード（youtube/api-samples）より
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_authenticated_service():
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secret.json',
        SCOPES
    )
    credentials = flow.run_console()  # ← ここが問題
    return build('youtube', 'v3', credentials=credentials)
```

**問題点:**
- `run_console()` はローカル環境でブラウザを開く前提
- Streamlit Cloudのようなサーバーレス環境では動作しない

### 1.2 Streamlit Cloud環境での課題

#### 課題A: リダイレクトURLの設定

**ローカル開発時:**
```
http://localhost:8501/oauth2callback
```

**Streamlit Cloud:**
```
https://your-app-name.streamlit.io/oauth2callback
```

- デプロイ後にURLが確定するため、事前設定が必要
- Google Cloud Consoleでの設定変更が必須
- アプリ名変更時に再設定が必要

#### 課題B: トークンの保存

**Streamlit Cloudの制約:**
- ファイルシステムへの書き込みは**一時的**のみ
- セッションが切れると保存データが消失
- Pickleファイル（credentials.pkl）の永続化は不可

**公式ドキュメントより:**
> "On free cloud platforms like Streamlit Community Cloud, writing to the file system is generally restricted. You can write files to the local session in Streamlit Cloud, but they'll be lost when the user starts a new session."

**解決策:**
- Streamlit Secrets（`st.secrets`）を使う
- 外部ストレージ（GCS, S3, Deta）に保存
- ただし、どちらも追加の実装コストが発生

#### 課題C: Refresh Tokenの管理

**トークンの種類:**

| トークン | 有効期限 | 用途 |
|---------|---------|------|
| Access Token | 1時間 | API呼び出しに使用 |
| Refresh Token | 永続的* | Access Token再取得に使用 |

**重要な制限事項（StackOverflowより）:**
> "Unverified apps using sensitive scopes will have refresh tokens that expire in about 1 week."

**本番運用の要件:**
- Googleの検証申請が必須
- 検証なしでは、refresh tokenが**約1週間で失効**
- 毎週再認証が必要 → 自動化の意味がない

### 1.3 Streamlit OAuth実装パターン

#### パターンA: streamlit-oauth コンポーネント

**GitHub: dnplus/streamlit-oauth**

```python
import streamlit as st
from streamlit_oauth import OAuth2Component

oauth2 = OAuth2Component(
    client_id=st.secrets["GOOGLE_CLIENT_ID"],
    client_secret=st.secrets["GOOGLE_CLIENT_SECRET"],
    authorize_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
    token_endpoint="https://oauth2.googleapis.com/token",
    refresh_token_endpoint="https://oauth2.googleapis.com/token",
    revoke_token_endpoint="https://oauth2.googleapis.com/revoke",
)

result = oauth2.authorize_button(
    "Authorize",
    redirect_uri="https://your-app.streamlit.io/oauth2callback",
    scope="https://www.googleapis.com/auth/youtube.upload",
    extras_params={"access_type": "offline", "prompt": "consent"},
)

if result and 'token' in result:
    st.session_state.token = result['token']
```

**メリット:**
- Streamlit環境に最適化
- セッション状態管理が容易
- 自動トークンリフレッシュ対応

**デメリット:**
- YouTube API固有のドキュメントなし
- 実装事例が少ない
- トラブル時のサポートが限定的

#### パターンB: Streamlit 1.42+のビルトインOAuth

**Streamlit公式ドキュメント（2024年11月更新）より:**

```python
import streamlit as st

# secrets.toml:
# [auth]
# redirect_uri = "https://your-app.streamlit.io/oauth2callback"
# cookie_secret = "xxx"
# client_id = "xxx"
# client_secret = "xxx"
# server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

if not st.user.is_logged_in:
    st.button("Log in with Google", on_click=st.login)
else:
    st.write(f"Welcome, {st.user.name}!")
```

**重要な注意:**
- これは**OIDC（OpenID Connect）** for **ユーザー認証**
- YouTube API統合には**追加実装**が必要
- 標準スコープにYouTube uploadは含まれない

### 1.4 非エンジニアが初回認証を完了できるか

**難易度評価: ⚠️ 困難**

**必要な手順（11ステップ）:**

1. Google Cloud Consoleでプロジェクト作成
2. YouTube Data API v3を有効化
3. OAuth 2.0クライアントIDを作成
4. リダイレクトURIを設定
5. client_secret.jsonをダウンロード
6. Streamlitアプリにシークレット設定
7. アプリをデプロイ
8. デプロイ後のURLを確認
9. Google ConsoleでリダイレクトURI更新
10. アプリで認証ボタンをクリック
11. Google同意画面で承認

**非エンジニアにとっての課題:**

| 難易度 | 内容 |
|--------|------|
| ⭐⭐⭐⭐⭐ | Google Cloud Consoleの操作 |
| ⭐⭐⭐⭐ | OAuth 2.0の概念理解 |
| ⭐⭐⭐⭐ | リダイレクトURIの設定 |
| ⭐⭐⭐ | Streamlit Secretsの設定 |
| ⭐⭐⭐⭐⭐ | トラブルシューティング |

**実装事例の不足:**
- Streamlit + YouTube APIの完全な実装例が見つからない
- 公式ドキュメントもなし
- コミュニティサポートも限定的

---

## 2. YouTube Data API v3の制約

### 2.1 クォータ制限

**デフォルト割り当て:**
```
10,000 units/day
```

**主要な操作コスト:**

| 操作 | コスト | 詳細 |
|------|--------|------|
| **動画アップロード** | 1,600 units | 1日最大6本 |
| リスト取得 | 1 unit | 軽量 |
| 作成/更新/削除 | 50 units | 中程度 |
| 検索リクエスト | 100 units | やや重い |

**週2本投稿の場合:**
```
週2本 × 1,600 units = 3,200 units/週
月8本 × 1,600 units = 12,800 units/月

→ デフォルト10,000 units/dayで十分
→ クォータ超過の心配なし
```

### 2.2 ファイルサイズ制限

**公式制限:**
- 最大ファイルサイズ: **256GB**（通常プラン）
- 128GB（未確認アカウント）

**実用上の問題:**
```
週2本 × 5分動画（フルHD）
  ファイルサイズ: 約200-500MB/本
  合計: 約1GB/週

→ ファイルサイズは問題なし
```

### 2.3 Google Cloud Projectの審査プロセス

#### テストモード（デフォルト）

**制限:**
- 最大100ユーザーまで
- **未検証アプリの警告**が表示される
- **Refresh tokenの有効期限が約1週間** ← 致命的

**公式ドキュメントより:**
> "Unverified apps using sensitive scopes will have refresh tokens that expire in about 1 week."

#### 本番モード（検証済み）

**検証プロセス（YouTube API Services - Audit and Quota Extension Form）:**

1. **必須項目:**
   - アプリケーションの詳細説明
   - YouTubeポリシーへの準拠証明
   - プライバシーポリシーURL
   - 利用規約URL
   - デモビデオ（アプリの動作）

2. **審査期間:**
   - 通常3-5営業日
   - 追加情報が必要な場合は延長

3. **審査基準:**
   - YouTube API Services Terms of Serviceへの準拠
   - データの適切な取り扱い
   - ユーザープライバシーの保護

**非エンジニアにとっての課題:**
- 技術用語が多い英語フォーム
- プライバシーポリシー等のドキュメント準備
- デモビデオの作成
- 審査対応（追加質問への回答）

### 2.4 追加クォータの申請

**現在の割り当て（10,000 units/day）で不足する場合:**

**申請要件:**
- まず検証審査を完了する必要がある
- 追加クォータのビジネス理由を説明
- 現在の使用状況を報告

**週2本投稿では不要:**
```
3,200 units/週 ÷ 7日 = 約457 units/日
→ デフォルト10,000 units/dayの5%程度
→ 追加申請は不要
```

---

## 3. Streamlit Cloud環境での技術的課題

### 3.1 ファイルシステムへのアクセス

**制約:**
```python
# ❌ これは動作しない（永続化されない）
import pickle
with open('credentials.pkl', 'wb') as f:
    pickle.dump(credentials, f)

# セッション終了後、ファイルは消失
```

**公式ドキュメント（Streamlit Discuss）より:**
> "On free cloud platforms like Streamlit Community Cloud, writing to the file system is generally restricted. Files will be lost when the user starts a new session."

**推奨される解決策:**

#### 方法A: Streamlit Secrets

```python
# secrets.toml（ローカル）
[youtube]
refresh_token = "xxx"

# Streamlit Cloud: App Settings > Secrets
# 同じ内容をペースト

# アプリコード
refresh_token = st.secrets["youtube"]["refresh_token"]
```

**メリット:**
- 追加コストなし
- Streamlit環境に最適化

**デメリット:**
- 手動でトークンを設定する必要がある
- トークン更新時に手動更新が必要
- 自動化の意味が薄れる

#### 方法B: 外部ストレージ（GCS/S3）

```python
from google.cloud import storage

def save_credentials(credentials):
    client = storage.Client()
    bucket = client.bucket('your-bucket')
    blob = bucket.blob('credentials.pkl')
    blob.upload_from_string(pickle.dumps(credentials))

def load_credentials():
    client = storage.Client()
    bucket = client.bucket('your-bucket')
    blob = bucket.blob('credentials.pkl')
    return pickle.loads(blob.download_as_bytes())
```

**メリット:**
- 完全な永続化
- 自動トークンリフレッシュが可能

**デメリット:**
- 追加コスト（GCS: 約$0.02/GB/月）
- 実装の複雑化
- GCPアカウント・認証情報の追加設定

### 3.2 リダイレクトURL設定

**開発とデプロイの2段階設定が必要:**

| 環境 | リダイレクトURI |
|------|----------------|
| ローカル | `http://localhost:8501/oauth2callback` |
| Streamlit Cloud | `https://your-app-name.streamlit.io/oauth2callback` |

**課題:**
- アプリ名が確定するまでCloud側の設定ができない
- デプロイ後にGoogle Consoleで設定変更が必要
- アプリ名変更時に再設定が必要

**Streamlit公式ドキュメントより:**
> "When deploying to Streamlit Cloud, you must update the secrets in your app settings and change the redirect_uri to match your deployed app's URL."

### 3.3 環境変数・Secrets管理

**Streamlit Secretsの使い方:**

**ローカル（.streamlit/secrets.toml）:**
```toml
[youtube]
client_id = "xxx.apps.googleusercontent.com"
client_secret = "xxx"
refresh_token = "xxx"

# .gitignoreに追加必須
# .streamlit/secrets.toml
```

**Streamlit Cloud:**
1. アプリ設定を開く
2. "Secrets"タブをクリック
3. secrets.tomlの内容をペースト
4. 保存

**注意事項:**
- **絶対にGitにコミットしない**
- リポジトリにpushすると全世界に公開される
- client_secretが漏洩すると不正利用のリスク

### 3.4 実際に動作するのか

**調査結果:**

#### 動作確認されている事例:
- ❌ Streamlit + YouTube upload: 見つからず
- ✅ Streamlit + Google OAuth: あり（認証のみ）
- ✅ Python + YouTube upload: 多数あり（非Streamlit）

#### 推測される動作:
- **技術的には可能** だが、実装が複雑
- 実装事例がないため、トラブル時の参考情報が少ない
- 「誰も実装していない = 実用的でない」可能性

**GitHub検索結果:**
```
"streamlit youtube upload oauth example"
→ 完全な実装例: 0件
→ 部分的な実装: 数件（認証のみ、アップロードなし）
```

---

## 4. 実装事例・成功例の調査

### 4.1 Streamlit + YouTube API統合

**検索結果サマリー:**

| リポジトリ | 機能 | YouTube統合 |
|-----------|------|------------|
| dnplus/streamlit-oauth | Google OAuth認証 | ❌ アップロードなし |
| uiucanh/streamlit-google-oauth | Google OAuth実装例 | ❌ アップロードなし |
| okld/streamlit-player | YouTubeプレーヤー埋め込み | ❌ 視聴のみ |
| maxmarkov/streamlit-youtube | YouTube動画ダウンロード | ❌ 逆方向 |
| youtube/api-samples | YouTube公式サンプル | ⚠️ Streamlitなし |

**結論:**
- Streamlit + YouTube uploadの**完全な実装例は存在しない**
- 認証とアップロードを組み合わせた事例なし

### 4.2 YouTube API単体の実装事例

**YouTube公式サンプル（youtube/api-samples）:**

```python
# python/upload_video.py
def get_authenticated_service():
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secret.json',
        SCOPES
    )
    credentials = flow.run_console()
    return build('youtube', 'v3', credentials=credentials)

def initialize_upload(youtube, options):
    body = {
        'snippet': {
            'title': options.title,
            'description': options.description,
            'tags': options.keywords.split(','),
            'categoryId': options.category
        },
        'status': {
            'privacyStatus': options.privacyStatus
        }
    }

    insert_request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=MediaFileUpload(options.file, chunksize=-1, resumable=True)
    )

    resumable_upload(insert_request)
```

**特徴:**
- `run_console()` でローカル実行前提
- Streamlit環境では動作しない
- 改造が必要

### 4.3 本番運用されている例

**調査結果:**

#### 企業・商用サービス:
- 大半が**サーバーサイド実装**（Flask, Django, FastAPI）
- Streamlitは**プロトタイプ**や**内部ツール**のみ
- 本番環境での使用例は見つからず

#### 個人プロジェクト:
- YouTube **ダウンロード**アプリは多数
- YouTube **アップロード**アプリは極めて少数
- あっても非Streamlit（CLI、Webアプリ等）

**推測される理由:**
- OAuth認証の複雑さ
- Streamlit Cloudの制約
- トークン管理の難しさ
- より適切な代替案の存在（後述）

### 4.4 失敗事例・諦めた事例

**Stack Overflowの質問パターン:**

#### よくある質問:
1. "Streamlit OAuthのリダイレクトURIが動かない"
2. "YouTube API認証がStreamlitで失敗する"
3. "Refresh tokenが保存できない"
4. "デプロイ後に認証が切れる"

#### よくある回答:
- "Streamlitは認証に向いていない"
- "別のフレームワークを使うべき"
- "ノーコードツール（Zapier等）を検討して"

**実例（Stack Overflow）:**
> "I'm trying to implement YouTube upload in Streamlit but the OAuth flow keeps failing. Should I use a different framework?"

**回答:**
> "Streamlit is primarily designed for data apps, not OAuth-heavy integrations. Consider using Flask or FastAPI for better OAuth support."

---

## 5. 代替アプローチの検討

### 5.1 手動ダウンロード + 手動アップロード

**ワークフロー:**
```
Streamlitアプリ → 動画生成 → ダウンロードボタン
                ↓
         ユーザーがローカルに保存
                ↓
      YouTube Studioから手動アップロード
```

**実装例:**

```python
import streamlit as st

# 動画生成後
video_path = "generated_video.mp4"

with open(video_path, "rb") as file:
    st.download_button(
        label="動画をダウンロード",
        data=file,
        file_name="youtube_video.mp4",
        mime="video/mp4"
    )

st.info("ダウンロード後、YouTube Studioから手動でアップロードしてください")
```

**メリット:**
- **実装が超簡単**（5行のコード）
- OAuth認証が不要
- Google審査が不要
- トラブルシューティングが容易
- 非エンジニアでも理解しやすい

**デメリット:**
- 完全自動化ではない
- 手動アップロードの手間（約1-2分/動画）
- スケジュール投稿には別途設定が必要

**評価: ⭐⭐⭐ 現実的な妥協案**

週2本なら手動でも許容範囲。完全自動化よりも安定性を優先。

### 5.2 Zapier/Make.com等のノーコードツール

#### Zapierを使った自動化

**ワークフロー:**
```
Google Drive（動画保存）
  ↓ Zapier監視
新しい動画を検出
  ↓ Zapier自動処理
YouTube APIでアップロード
  ↓
メタデータ設定（タイトル、説明、タグ）
  ↓
指定時刻に公開
```

**Zapierの設定手順（非エンジニア向け）:**

1. **Zapを作成**
   - トリガー: Google Drive "New File in Folder"
   - フォルダ: "YouTube動画"

2. **YouTube統合**
   - アクション: YouTube "Upload Video"
   - Google認証: Zapierが自動処理（ボタンクリックのみ）

3. **メタデータ設定**
   - Title: ファイル名から自動取得
   - Description: テンプレート使用
   - Privacy: "Private" → 後で公開設定

4. **スケジュール投稿（オプション）**
   - Delay機能を使って投稿時刻を制御

**公式ドキュメントより（2024年11月更新）:**
> "Zapier can automatically upload a video once you've saved it to a specific Google Drive or Dropbox folder."

**コスト:**
```
Zapier Starter: $19.99/月
  - 750 tasks/月
  - Premium apps（YouTube含む）

週2本 × 4週 = 8本/月
→ 8 tasks/月
→ Starterプランで十分
```

**メリット:**
- ✅ **OAuth認証が超簡単**（Zapierが処理）
- ✅ **非エンジニアでも設定可能**
- ✅ **エラーハンドリング自動**
- ✅ **Google審査不要**（Zapier経由）
- ✅ **トラブル時のサポートあり**
- ✅ **スケジュール投稿も簡単**
- ✅ **メンテナンスフリー**

**デメリット:**
- ⚠️ 月額コスト（$19.99）
- ⚠️ Zapierへの依存

**評価: ⭐⭐⭐⭐⭐ 最も現実的な選択肢**

コストはかかるが、開発工数・運用コストを考えると圧倒的に安い。

#### Make.com（旧Integromat）

**Zapierとの比較:**

| 項目 | Zapier | Make.com |
|------|--------|----------|
| 価格 | $19.99/月 | $9/月 |
| 無料枠 | 100 tasks/月 | 1,000 operations/月 |
| YouTube対応 | ✅ | ✅ |
| 日本語UI | ⚠️ 部分的 | ⚠️ 英語のみ |
| 学習コスト | 低 | やや高 |

**Make.comの特徴:**
- より高度な条件分岐が可能
- ビジュアルフローエディタ
- コストパフォーマンスが高い

**推奨:**
- 初心者: **Zapier**（簡単）
- コスト重視: **Make.com**（安い）

### 5.3 他のビデオホスティングサービス

#### Vimeo

**API統合:**
- OAuth 2.0対応
- アップロードAPIあり
- クォータ制限なし（プランによる）

**コスト:**
```
Vimeo Standard: $7/月
  - 5GB/週アップロード
  - 無制限視聴
```

**メリット:**
- YouTubeより簡単なAPI
- 審査なし
- プライバシー設定が豊富

**デメリット:**
- リーチがYouTubeより小さい
- 収益化が難しい
- SEO効果が低い

**評価: ⭐⭐ YouTube固執しないなら選択肢**

#### Cloudflare Stream

**API統合:**
- シンプルなREST API
- トークンベース認証（OAuthなし）
- 非常に簡単

**コスト:**
```
$1/1000分の視聴
$5/1000分の保存
```

**メリット:**
- API実装が最も簡単
- OAuth不要
- 高速配信（CDN）

**デメリット:**
- プラットフォームとしての機能なし
- コメント、いいね等の機能なし
- 埋め込み利用が前提

**評価: ⭐ 用途が異なる**

### 5.4 どれが最も現実的か

#### 比較表

| アプローチ | 実装難易度 | 運用難易度 | コスト | 自動化度 | 総合評価 |
|-----------|----------|----------|--------|---------|---------|
| **Streamlit + YouTube API** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 無料 | 70% | ⭐⭐ |
| **手動ダウンロード/アップロード** | ⭐ | ⭐⭐ | 無料 | 50% | ⭐⭐⭐ |
| **Zapier/Make.com** | ⭐ | ⭐ | $10-20/月 | 100% | ⭐⭐⭐⭐⭐ |
| **Vimeo API** | ⭐⭐ | ⭐⭐ | $7/月 | 80% | ⭐⭐⭐ |
| **Cloudflare Stream** | ⭐ | ⭐ | 従量課金 | 90% | ⭐⭐ |

#### 推奨順位

**1位: Zapier/Make.com ⭐⭐⭐⭐⭐**

**理由:**
```yaml
実装難易度: 最低（GUIで設定）
運用難易度: 最低（ノーコード）
非エンジニア対応: 最適
トラブル対応: 簡単（サポートあり）
拡張性: 高い（他のサービス連携も可能）
コスト: 妥当（$10-20/月）
```

**推奨構成:**
```
Streamlitアプリ（動画生成）
  ↓ ダウンロードボタン or 自動保存
Google Drive（動画保存フォルダ）
  ↓ Zapier監視
YouTube自動アップロード
  ↓
スケジュール公開
```

**2位: 手動ダウンロード + 手動アップロード ⭐⭐⭐**

**理由:**
```yaml
実装難易度: 最低
運用難易度: 低（慣れれば1-2分/動画）
コスト: 無料
週2本なら許容範囲
```

**3位: Streamlit + YouTube API ⭐⭐**

**理由:**
```yaml
実装難易度: 非常に高い
運用難易度: 非常に高い
トラブルリスク: 高い
非エンジニアには不適
メリットが薄い（時間コスト考慮）
```

---

## 6. 具体的な実装パターン（参考）

### 6.1 Streamlit + YouTube API実装（非推奨）

**完全なコード例:**

```python
import streamlit as st
import pickle
import os
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

# YouTube API設定
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
CLIENT_SECRETS_FILE = 'client_secret.json'
CREDENTIALS_FILE = 'credentials.pkl'

def get_authenticated_service():
    """YouTube APIの認証済みサービスを取得"""
    credentials = None

    # 保存された認証情報を読み込む
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, 'rb') as f:
            credentials = pickle.load(f)

    # 認証情報が無効または存在しない場合
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            # リフレッシュトークンで更新
            credentials.refresh(Request())
        else:
            # OAuth2フローで新規取得
            flow = Flow.from_client_secrets_file(
                CLIENT_SECRETS_FILE,
                scopes=SCOPES,
                redirect_uri=st.secrets["auth"]["redirect_uri"]
            )

            # 認証URLを生成
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )

            st.markdown(f"[Google認証ページを開く]({auth_url})")
            auth_code = st.text_input("認証コードを入力してください")

            if auth_code:
                flow.fetch_token(code=auth_code)
                credentials = flow.credentials

                # 認証情報を保存
                with open(CREDENTIALS_FILE, 'wb') as f:
                    pickle.dump(credentials, f)

                st.success("認証が完了しました！")
                st.rerun()

    return build('youtube', 'v3', credentials=credentials)

def upload_video(youtube, file_path, title, description, category_id='22', privacy_status='private'):
    """YouTube動画をアップロード"""
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': ['AI', 'アバター'],
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': False
        }
    }

    # MediaFileUploadでアップロード
    media = MediaFileUpload(
        file_path,
        chunksize=-1,
        resumable=True,
        mimetype='video/mp4'
    )

    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )

    response = None
    with st.spinner('動画をアップロード中...'):
        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                st.progress(progress / 100)

    return response

# Streamlitアプリ
st.title("YouTube動画アップローダー")

# 認証
try:
    youtube = get_authenticated_service()
    st.success("YouTube APIに接続済み")
except Exception as e:
    st.error(f"認証エラー: {e}")
    st.stop()

# 動画アップロードUI
uploaded_file = st.file_uploader("動画ファイルを選択", type=['mp4', 'mov', 'avi'])
title = st.text_input("タイトル")
description = st.text_area("説明")
privacy = st.selectbox("公開設定", ['private', 'unlisted', 'public'])

if st.button("アップロード") and uploaded_file and title:
    # 一時ファイルに保存
    temp_file = f"/tmp/{uploaded_file.name}"
    with open(temp_file, "wb") as f:
        f.write(uploaded_file.getbuffer())

    try:
        response = upload_video(youtube, temp_file, title, description, privacy_status=privacy)
        video_id = response['id']
        st.success(f"アップロード完了！")
        st.markdown(f"[動画を見る](https://youtube.com/watch?v={video_id})")
    except Exception as e:
        st.error(f"アップロードエラー: {e}")
    finally:
        # 一時ファイル削除
        os.remove(temp_file)
```

**secrets.toml:**

```toml
[auth]
redirect_uri = "https://your-app.streamlit.io/oauth2callback"

[youtube]
client_id = "xxx.apps.googleusercontent.com"
client_secret = "xxx"
```

**問題点:**
1. `CREDENTIALS_FILE`がStreamlit Cloudで永続化されない
2. OAuth認証フローが複雑
3. エラーハンドリングが不十分
4. 非エンジニアには理解困難

### 6.2 Zapier実装（推奨）

**設定手順（スクリーンショット付きガイド想定）:**

#### ステップ1: Zapier登録

1. https://zapier.com/ にアクセス
2. "Sign Up Free" をクリック
3. メールアドレスで登録

#### ステップ2: 新しいZapを作成

1. "Create Zap" をクリック
2. Zap名を設定: "YouTube自動アップロード"

#### ステップ3: トリガー設定

1. "Choose App & Event"
2. Google Driveを選択
3. イベント: "New File in Folder"
4. "Continue" をクリック
5. Google Driveアカウントに接続
   - "Sign in with Google" をクリック
   - 権限を承認
6. フォルダを選択: "YouTube動画"
7. テスト実行: "Test trigger"

#### ステップ4: アクション設定

1. "Choose App & Event"
2. YouTubeを選択
3. イベント: "Upload Video"
4. "Continue" をクリック
5. YouTubeアカウントに接続
   - "Sign in with Google" をクリック
   - YouTube権限を承認（ここだけ）
6. フィールド設定:
   - **Title**: `{{1. Name}}` （ファイル名）
   - **File**: `{{1. File}}` （動画ファイル）
   - **Description**: テンプレート入力
   - **Privacy Status**: "Private"
   - **Category**: "People & Blogs"
7. テスト実行: "Test action"

#### ステップ5: 公開

1. "Publish Zap" をクリック
2. Zapが有効化される

#### 使い方

1. Streamlitアプリで動画を生成
2. ダウンロード
3. Google Drive の "YouTube動画" フォルダにドラッグ&ドロップ
4. **自動的にYouTubeにアップロード！**
5. YouTube Studioで公開設定を変更（Private → Public）

**所要時間:**
- 初回設定: 15-20分
- 2回目以降: 30秒（ファイルをドロップするだけ）

### 6.3 手動アップロード実装（シンプル版）

**Streamlitコード:**

```python
import streamlit as st
from datetime import datetime

st.title("YouTube動画ジェネレーター")

# 動画生成処理（既存のコード）
# ...

# 生成された動画のパス
video_path = "generated_video.mp4"

# ダウンロードボタン
with open(video_path, "rb") as file:
    video_bytes = file.read()

    # ファイル名に日時を追加
    filename = f"youtube_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

    st.download_button(
        label="📥 YouTube用動画をダウンロード",
        data=video_bytes,
        file_name=filename,
        mime="video/mp4",
        use_container_width=True
    )

# アップロード手順を表示
st.info("""
### 📤 YouTube アップロード手順

1. 上のボタンから動画をダウンロード
2. [YouTube Studio](https://studio.youtube.com/) を開く
3. 右上の「作成」→「動画をアップロード」
4. ダウンロードした動画を選択
5. タイトル・説明を入力
6. 公開設定を選択して「公開」

所要時間: 約2分
""")

# メタデータのコピー機能
st.subheader("📋 メタデータ（コピー用）")

title = st.text_input("タイトル", "AI生成動画タイトル")
description = st.text_area(
    "説明",
    """この動画はAIで自動生成されました。

#AI #アバター #YouTube
"""
)
tags = st.text_input("タグ（カンマ区切り）", "AI,アバター,自動生成")

# コピーボタン
if st.button("📋 メタデータをクリップボードにコピー"):
    metadata = f"""
タイトル: {title}

説明:
{description}

タグ: {tags}
"""
    st.code(metadata, language="text")
    st.success("上のテキストをコピーして、YouTube Studioに貼り付けてください")
```

**メリット:**
- コード量が少ない（20行程度）
- トラブルシューティング不要
- 誰でも理解できる

---

## 7. 総合推奨事項

### 7.1 結論: YouTube API統合は「やめたほうがいい」

**理由:**

#### 技術的課題
- ✅ 技術的には可能だが、実装が非常に複雑
- ❌ Streamlit Cloud環境での制約が多い
- ❌ OAuth認証フローの実装難易度が高い
- ❌ トークン管理が煩雑
- ❌ Google審査プロセスが必要（本番運用）

#### 運用上の課題
- ❌ 非エンジニアには実装・運用が困難
- ❌ トラブルシューティングが複雑
- ❌ 実装事例が少なく、参考情報が不足
- ❌ メンテナンスコストが高い

#### コスト対効果
- ⚠️ 開発工数: 20-40時間（エンジニア）
- ⚠️ 学習コスト: 高い（OAuth、YouTube API、Streamlit制約）
- ⚠️ 時給換算: $1,000-2,000相当
- ✅ Zapier年間コスト: $240
- **→ Zapierのほうが圧倒的に安い**

### 7.2 推奨アプローチ

#### フェーズ1: 即座に開始（推奨）⭐⭐⭐⭐⭐

**Zapier/Make.com + 手動トリガー**

```
Streamlitアプリ
  ↓ 動画生成
Google Driveに保存（手動 or 自動）
  ↓ Zapier監視
YouTube自動アップロード
```

**実装手順:**
1. Zapierアカウント作成（15分）
2. Zap設定（20分）
3. テスト実行（5分）
4. **合計: 40分で完成**

**コスト:**
- Zapier Starter: $19.99/月
- または Make.com: $9/月

**メリット:**
- 今日から使える
- 非エンジニアでも設定可能
- 安定動作
- サポートあり

#### フェーズ2: 完全自動化を目指す場合（オプション）

**n8n（セルフホスト版Zapier）**

```
n8nワークフロー:
  1. Streamlit API呼び出し（Webhook）
  2. 動画生成完了を検知
  3. YouTube API連携
  4. アップロード + メタデータ設定
  5. スケジュール公開
```

**コスト:**
- n8n Cloud: $20/月
- またはセルフホスト: 無料（VPSコスト別）

**メリット:**
- より高度な自動化
- カスタマイズ性が高い
- API連携が柔軟

**デメリット:**
- 学習コストがやや高い
- セルフホストは技術スキル必要

#### フェーズ3: 完全統合（非推奨）

**Streamlit + YouTube API直接実装**

上記「6.1 実装パターン」参照。

**推奨しない理由:**
- 実装コストが高すぎる
- メリットが薄い
- Zapier/n8nで十分

### 7.3 最終推奨構成

```yaml
推奨構成（週2本、5分動画）:

動画生成:
  - Streamlitアプリ
  - Cartesia + D-ID
  - コスト: $56/月

動画投稿:
  - Zapier/Make.com
  - コスト: $10-20/月

合計: $66-76/月 (¥9,500-11,000)

メリット:
  ✅ 完全ノーコード（YouTubeアップロード部分）
  ✅ 非エンジニア運用可能
  ✅ 安定動作
  ✅ スケーラブル
  ✅ メンテナンスフリー
```

### 7.4 よりシンプルな代替案（超低コスト版）

```yaml
推奨構成（週2本、60秒Shorts）:

動画生成:
  - Streamlitアプリ
  - Cartesia + D-ID Lite
  - コスト: $12.9/月

動画投稿:
  - 手動ダウンロード + 手動アップロード
  - コスト: 無料
  - 所要時間: 2分/動画 × 2本 = 4分/週

合計: $12.9/月 (¥1,800)

メリット:
  ✅ 超低コスト
  ✅ シンプル
  ✅ トラブルゼロ
  ✅ 非エンジニア対応

デメリット:
  ⚠️ 手動作業あり（週4分）
```

---

## 8. 実装チェックリスト

### 推奨アプローチ（Zapier）のチェックリスト

#### Phase 1: Zapier設定（初回のみ、40分）

- [ ] Zapierアカウント作成
- [ ] Starter プラン登録（$19.99/月）
- [ ] Google Driveアカウント接続
- [ ] YouTubeアカウント接続
- [ ] Zap作成: Google Drive → YouTube
- [ ] トリガー設定: "New File in Folder"
- [ ] フォルダ指定: "YouTube動画"
- [ ] アクション設定: "Upload Video"
- [ ] メタデータテンプレート作成
- [ ] テスト実行: 成功を確認
- [ ] Zap公開

#### Phase 2: Streamlit側の実装（30分）

- [ ] ダウンロードボタンの追加
- [ ] ファイル名に日時を追加
- [ ] メタデータのコピー機能
- [ ] アップロード手順の表示
- [ ] UIの調整

#### Phase 3: 運用フロー確立（初回のみ、15分）

- [ ] テスト動画を1本生成
- [ ] ダウンロード
- [ ] Google Driveにアップロード
- [ ] Zapier自動実行を確認
- [ ] YouTube Studioで動画を確認
- [ ] 問題なければ完了！

#### Phase 4: 定期運用（週2回、各5分）

- [ ] Streamlitアプリで動画生成
- [ ] ダウンロード
- [ ] Google Driveにアップロード
- [ ] 自動アップロードを待つ（1-2分）
- [ ] YouTube Studioで公開設定
- [ ] 完了！

**合計所要時間:**
- 初回セットアップ: 1.5時間
- 定期運用: 週10分（動画2本）

### 非推奨アプローチ（Streamlit + YouTube API）のチェックリスト

参考まで。**実装は推奨しません。**

#### Phase 1: Google Cloud設定（3-5時間）

- [ ] Google Cloudアカウント作成
- [ ] プロジェクト作成
- [ ] YouTube Data API v3を有効化
- [ ] OAuth 2.0クライアントID作成
- [ ] リダイレクトURI設定（ローカル）
- [ ] client_secret.jsonダウンロード
- [ ] Google審査申請（本番運用時）
- [ ] プライバシーポリシー作成
- [ ] 利用規約作成
- [ ] デモビデオ作成
- [ ] 審査完了を待つ（3-5日）

#### Phase 2: Streamlit実装（10-20時間）

- [ ] OAuth認証フロー実装
- [ ] トークン管理機能実装
- [ ] GCS連携（トークン保存）
- [ ] アップロード機能実装
- [ ] エラーハンドリング実装
- [ ] 進捗表示UI実装
- [ ] メタデータ設定UI実装
- [ ] テスト実装
- [ ] デバッグ

#### Phase 3: デプロイ（2-3時間）

- [ ] Streamlit Cloudにデプロイ
- [ ] デプロイURLを確認
- [ ] Google CloudでリダイレクトURI更新
- [ ] Streamlit Secretsを設定
- [ ] GCS認証情報を設定
- [ ] 本番環境でテスト
- [ ] トラブルシューティング

**合計所要時間: 15-28時間**
**時給$50換算: $750-1,400**

---

## 9. トラブルシューティングガイド

### Zapierでよくある問題

#### 問題1: Zapが動かない

**症状:**
- Google Driveに動画をアップロードしても、YouTubeにアップロードされない

**原因と対処:**

1. **Zapが無効になっている**
   - Zapier Dashboard → Zapを確認
   - ステータスが"On"になっているか確認
   - "Off"なら"Turn On"をクリック

2. **フォルダが間違っている**
   - Zap設定 → Trigger → Folder確認
   - 実際にアップロードしたフォルダと一致しているか確認

3. **ファイル形式が対応していない**
   - MP4, MOV, AVI等の動画形式か確認
   - ZIP等の圧縮ファイルは不可

4. **タスク上限に達した**
   - Zapier Dashboard → Usage確認
   - 無料プラン: 100 tasks/月
   - 上限到達なら有料プランにアップグレード

#### 問題2: YouTube認証エラー

**症状:**
- "Authentication failed" エラー

**対処:**

1. **再認証**
   - Zap設定 → Action → YouTube Account
   - "Reconnect" をクリック
   - Google認証をやり直し

2. **権限の確認**
   - YouTube APIの権限が正しく承認されているか確認
   - 必要に応じて再承認

#### 問題3: アップロードは成功するが、メタデータが反映されない

**症状:**
- タイトルが空白、説明が空白

**対処:**

1. **フィールドマッピング確認**
   - Zap設定 → Action → Customize Video
   - Title, Description等が正しくマッピングされているか

2. **テンプレート修正**
   - 動的フィールド（`{{1. Name}}`等）が正しいか確認

### Streamlit + YouTube APIでよくある問題（参考）

#### 問題1: OAuth認証失敗

**症状:**
- "Redirect URI mismatch" エラー

**対処:**

1. **リダイレクトURIの確認**
   - Google Cloud Console → OAuth 2.0クライアント
   - 登録されているURIを確認
   - Streamlitアプリの実際のURLと一致しているか

2. **Secrets設定確認**
   - `st.secrets["auth"]["redirect_uri"]` が正しいか

#### 問題2: Refresh Token失効

**症状:**
- 1週間後に再認証が必要になる

**原因:**
- アプリが未検証状態

**対処:**
- Google審査を申請
- 検証完了まで毎週再認証が必要

#### 問題3: ファイルアップロードエラー

**症状:**
- "File not found" エラー

**原因:**
- Streamlit Cloudの一時ファイルシステム制約

**対処:**

1. **一時ファイルの作成確認**
   ```python
   temp_file = f"/tmp/{uploaded_file.name}"
   with open(temp_file, "wb") as f:
       f.write(uploaded_file.getbuffer())
   ```

2. **ファイルパスの確認**
   ```python
   print(f"File exists: {os.path.exists(temp_file)}")
   ```

---

## 10. まとめ

### YouTube API統合は技術的に可能、しかし...

**技術的実装可能性: ✅ 可能**
- YouTube Data API v3は機能豊富
- Pythonクライアントライブラリあり
- Streamlit環境でも動作は可能

**しかし、実用性は ❌ 低い**

#### 主な理由

1. **OAuth認証の複雑さ**
   - ブラウザベースの認証フロー
   - リダイレクトURIの設定
   - トークン管理の煩雑さ

2. **Streamlit Cloud環境の制約**
   - ファイルシステムへの書き込み制限
   - トークンの永続化が困難
   - 外部ストレージ連携が必要

3. **Google審査プロセス**
   - 本番運用には検証が必須
   - 未検証状態では1週間でトークン失効
   - 審査には時間とドキュメントが必要

4. **実装事例の不足**
   - Streamlit + YouTube uploadの完全な実装例なし
   - トラブル時の参考情報が少ない
   - コミュニティサポートも限定的

5. **コスト対効果の問題**
   - 実装工数: 15-28時間
   - 時給換算: $750-1,400
   - Zapier年間コスト: $240
   - **→ Zapierのほうが圧倒的に安い**

### 推奨する代替案

#### 最優先推奨: Zapier/Make.com ⭐⭐⭐⭐⭐

**理由:**
```yaml
実装時間: 40分
運用難易度: 非常に低い
非エンジニア対応: 完璧
コスト: $10-20/月
安定性: 非常に高い
サポート: あり
```

**構成:**
```
Streamlitアプリ（動画生成）
  ↓
Google Drive（動画保存）
  ↓ Zapier監視
YouTube（自動アップロード）
```

#### 次点: 手動アップロード ⭐⭐⭐

**理由:**
```yaml
実装時間: 10分
コスト: 無料
週2本なら許容範囲（週4分の手間）
```

#### 非推奨: Streamlit + YouTube API直接実装 ⭐⭐

**理由:**
```yaml
実装時間: 15-28時間
運用難易度: 非常に高い
非エンジニア対応: 不可能
メリット: ほぼなし
```

### 最終推奨構成

**週2本、5分動画の場合:**

```yaml
動画生成:
  Streamlit + Cartesia + D-ID
  コスト: $56/月

動画投稿:
  Zapier
  コスト: $20/月

合計: $76/月 (¥11,000)

年間コスト削減（vs ElevenLabs構成）:
  $180 (¥26,000)
```

**週2本、60秒Shortsの場合（超低コスト版）:**

```yaml
動画生成:
  Streamlit + Cartesia + D-ID Lite
  コスト: $12.9/月

動画投稿:
  手動アップロード
  コスト: 無料
  時間: 週4分

合計: $12.9/月 (¥1,800)

年間コスト削減:
  $720 (¥105,000)
```

---

## 参考資料

### 公式ドキュメント

- [YouTube Data API v3 - Upload Video](https://developers.google.com/youtube/v3/guides/uploading_a_video)
- [YouTube Data API - Quota and Compliance Audits](https://developers.google.com/youtube/v3/guides/quota_and_compliance_audits)
- [Streamlit - Google OAuth Tutorial](https://docs.streamlit.io/develop/tutorials/authentication/google)
- [Streamlit - Secrets Management](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)
- [Zapier - YouTube Integration](https://zapier.com/apps/youtube/integrations)

### GitHubリポジトリ

- [youtube/api-samples](https://github.com/youtube/api-samples) - YouTube公式サンプル
- [dnplus/streamlit-oauth](https://github.com/dnplus/streamlit-oauth) - Streamlit OAuthコンポーネント
- [uiucanh/streamlit-google-oauth](https://github.com/uiucanh/streamlit-google-oauth) - Google OAuth実装例

### Stack Overflow

- [YouTube Data API v3: video upload from server without opening the browser](https://stackoverflow.com/questions/61851000/)
- [Upload video to Youtube through API without OAuth everytime](https://stackoverflow.com/questions/44672286/)
- [Youtube Data API v.3 - fully automated oAuth flow (Python)?](https://stackoverflow.com/questions/58073119/)

### ブログ記事

- [Zapier - 4 ways to automate YouTube (2024年11月更新)](https://zapier.com/blog/automate-youtube/)
- [OAuth in Streamlit is Now Built-In (2025年2月)](https://medium.com/@pranay.shah/oauth-in-streamlit-is-now-built-in-heres-how-to-use-it-c768b9f677ed)

---

**調査完了日**: 2025年11月15日
**次のアクション**: Zapier/Make.comのアカウント作成、またはStreamlitダウンロードボタンの実装
