# AIアバター動画生成システム

## 目的

ブログ記事をYouTube動画に自動変換

## 要件

- 週2本の動画投稿（5分またはShorts）
- 声のクローニング（本人の声）
- APIベース（ローカルGPU不使用）
- リップシンク対応

## 技術構成

Cartesia（音声生成）+ D-ID（動画生成）

```
スクリプト
  ↓ Cartesia API
音声（MP3）
  ↓ Cloudinary
音声URL
  ↓ D-ID API
リップシンク動画（MP4）
```

## コスト

- Shorts（60秒）週2本: $11/月
- 5分動画 週2本: $54/月

## 実装状況

- ✅ Streamlitアプリ完成
- ✅ Cartesia音声生成
- ✅ D-ID動画生成
- ✅ ElevenLabs（代替実装）
- ⬜ YouTube自動投稿（未実装）

## 参考

- セットアップ: README.md
- Cartesia実装: Docs/Cartesia実装ガイド.md
- YouTube API: Docs/YouTube_API統合_実装可能性調査.md
- デプロイ記録: Docs/デプロイ記録_2025-11-15.md
