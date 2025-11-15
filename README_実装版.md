# AIアバター動画生成システム - 実装版

スクリプトからAIアバター動画を自動生成する Streamlit アプリケーション

---

## 📋 概要

このアプリケーションは、テキストスクリプトから音声とリップシンク動画を生成します。

**主な機能**:
- ✅ スクリプトから音声生成（Cartesia API）
- ✅ 音声からリップシンク動画生成（D-ID API）
- ✅ リアルタイム進捗表示
- ✅ 動画プレビュー＆ダウンロード
- ✅ ブラウザ完結（Streamlit UI）

**コスト**:
- 週2本 × 60秒Shorts: **¥1,800/月**
- 週2本 × 5分動画: **¥8,000/月**

---

## 🚀 クイックスタート

### 前提条件

- Python 3.9以上
- 各種APIキー（下記参照）

### 1. インストール

```bash
# リポジトリをクローン（既にある場合はスキップ）
cd C:\dev\AIアバター

# 仮想環境作成
python -m venv venv

# 仮想環境を有効化
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt
```

### 2. APIキーの設定

`.streamlit/secrets.toml` を作成:

```bash
# サンプルをコピー
copy .streamlit\secrets.toml.example .streamlit\secrets.toml
```

`secrets.toml` を編集して各APIキーを設定:

```toml
[cartesia]
api_key = "your-cartesia-api-key"
voice_id = "your-voice-id"

[did]
api_key = "your-did-api-key"

[cloudinary]
cloud_name = "your-cloud-name"
api_key = "your-api-key"
api_secret = "your-api-secret"
```

#### APIキーの取得方法

1. **Cartesia** (https://cartesia.ai/)
   - アカウント作成
   - Pro プラン登録（$5/月）
   - 音声クローン作成（5秒のサンプル）
   - APIキーと Voice ID をコピー

2. **D-ID** (https://studio.d-id.com/)
   - アカウント作成
   - Lite プラン登録（$5.9/月 - Shorts）または Pro（$49/月 - 5分動画）
   - APIキーをコピー

3. **Cloudinary** (https://cloudinary.com/)
   - アカウント作成（無料枠で十分）
   - Dashboard から cloud_name、api_key、api_secret をコピー

### 3. アプリケーション起動

```bash
streamlit run app.py
```

ブラウザで http://localhost:8501 にアクセス

---

## 📁 ディレクトリ構造

```
C:\dev\AIアバター/
├── app.py                        # Streamlitアプリ（メイン）
├── config.yaml                   # 設定ファイル
├── requirements.txt              # 依存関係
├── requirements-dev.txt          # 開発用依存関係
│
├── src/                          # ソースコード
│   ├── modules/                  # ビジネスロジック
│   │   ├── validator.py         # スクリプト検証
│   │   ├── cartesia.py          # 音声生成
│   │   └── did.py               # 動画生成
│   ├── utils/                    # ユーティリティ
│   │   ├── logger.py            # ロギング
│   │   ├── config.py            # 設定管理
│   │   └── errors.py            # エラー定義
│   └── models/                   # データモデル
│       └── schemas.py           # Pydanticモデル
│
├── .streamlit/                   # Streamlit設定
│   ├── config.toml              # UI設定
│   └── secrets.toml.example     # APIキーテンプレート
│
├── design/                       # 設計ドキュメント（7ファイル）
└── resources/                    # 参考資料
    ├── Cartesia実装ガイド.md
    └── YouTube_API統合_実装可能性調査.md
```

---

## 💻 使い方

### 基本フロー

1. **スクリプト入力**
   - テキストエリアにスクリプトを入力
   - リアルタイムで文字数・予想時間を表示

2. **設定**
   - 動画の長さ選択（60秒 or 5分）
   - 声の速度調整（0.5x - 2.0x）

3. **動画生成開始**
   - ボタンクリックで生成開始
   - 進捗バーでリアルタイム表示

4. **プレビュー＆ダウンロード**
   - 音声・動画をプレビュー
   - ダウンロードして YouTube にアップロード

### YouTube投稿

**手動アップロード**（推奨）:
1. アプリで動画をダウンロード
2. YouTube Studio で手動アップロード

**自動化オプション**:
- Zapier/Make.com を使った自動投稿
- 詳細: `resources/YouTube_API統合_実装可能性調査.md`

---

## ⚙️ 設定

### config.yaml

アプリケーション全体の設定:

```yaml
script:
  max_words_shorts: 150      # Shorts最大文字数
  max_words_long: 500        # 5分動画最大文字数

cartesia:
  ws_url: "wss://..."        # WebSocket URL
  model: "sonic-japanese"    # モデル名

did:
  api_url: "https://..."     # API URL
  poll_interval_seconds: 5   # ポーリング間隔
```

### ログレベル変更

`config.yaml` の `logging.level` を変更:

```yaml
logging:
  level: "DEBUG"  # DEBUG, INFO, WARNING, ERROR
```

---

## 🐛 トラブルシューティング

### 音声生成エラー

**症状**: "WebSocket接続エラー"

**対処**:
1. Cartesia APIキーを確認
2. Voice ID を確認
3. ネットワーク接続を確認

### 動画生成タイムアウト

**症状**: "動画生成タイムアウト（5分）"

**対処**:
1. D-ID のステータスページを確認
2. しばらく待ってから再試行
3. `config.yaml` の `poll_timeout_seconds` を増やす

### Cloudinaryアップロードエラー

**症状**: "アップロード失敗"

**対処**:
1. Cloudinary認証情報を確認
2. 無料枠の容量を確認（25GB）

---

## 🚢 デプロイ（Streamlit Cloud）

### 1. GitHubリポジトリ作成

```bash
# Git初期化
git init
git add .
git commit -m "feat: 初回コミット

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# GitHubリポジトリ作成（Private推奨）
gh repo create ai-avatar-app --private
git remote add origin https://github.com/your-username/ai-avatar-app.git
git push -u origin main
```

### 2. Streamlit Cloud設定

1. https://share.streamlit.io/ にアクセス
2. GitHubでサインイン
3. "New app" をクリック
4. リポジトリ選択
5. Main file path: `app.py`
6. "Deploy" をクリック

### 3. Secrets設定

Streamlit Cloud Dashboard:
- App settings → Secrets
- `secrets.toml` の内容をコピー＆ペースト

---

## 📊 コスト試算

### Shorts（60秒）週2本

```
Cartesia Pro: $5/月
D-ID Lite: $5.9/月
Cloudinary: 無料

合計: $10.9/月（¥1,600）
```

### 5分動画 週2本

```
Cartesia Pro: $5/月
D-ID Pro: $49/月
Cloudinary: 無料

合計: $54/月（¥7,800）
```

---

## 🧪 テスト

### ユニットテスト実行

```bash
# すべてのテスト
pytest

# カバレッジ付き
pytest --cov=src --cov-report=html
```

### コード品質チェック

```bash
# フォーマット
black src/

# Lint
flake8 src/

# 型チェック
mypy src/
```

---

## 📚 参考ドキュメント

### 設計書（design/）

1. `01_システム設計書.md` - アーキテクチャ全体像
2. `02_モジュール詳細設計.md` - コーディング規約・モジュール仕様
3. `03_API統合設計.md` - 各API の詳細仕様
4. `04_UI-UX設計書.md` - Streamlit UIの設計
5. `05_セキュリティ設計書.md` - セキュリティ対策
6. `06_デプロイ運用設計書.md` - デプロイ手順
7. `07_テスト計画書.md` - テスト戦略

### 実装ガイド（resources/）

- `Cartesia実装ガイド.md` - Cartesia詳細実装
- `YouTube_API統合_実装可能性調査.md` - YouTube投稿の実装可能性

---

## 🤝 貢献

プルリクエスト歓迎！

1. Fork
2. Feature ブランチ作成
3. Commit（コミットメッセージは日本語OK）
4. Push
5. Pull Request

---

## 📝 ライセンス

MIT License

---

## 🎯 次のステップ

### Phase 1（現在）: MVP完成 ✅

- ✅ スクリプト入力
- ✅ 音声生成（Cartesia）
- ✅ 動画生成（D-ID）
- ✅ ダウンロード

### Phase 2: 機能追加

- ⬜ アバター画像アップロード
- ⬜ 複数アバター選択
- ⬜ バッチ処理（複数動画）

### Phase 3: 自動化

- ⬜ Zapier統合（YouTube自動投稿）
- ⬜ ブログRSS監視
- ⬜ スケジュール投稿

---

**最終更新**: 2025年11月15日
**バージョン**: 1.0.0 (MVP)
