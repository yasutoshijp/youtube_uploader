# GitHub Actions 移行 - クイックリファレンス

## 🚀 30秒で分かる変更点

| 項目 | 従来 | GitHub Actions |
|------|------|---|
| **実行場所** | ローカルマシン | GitHub サーバー |
| **実行タイミング** | 手動実行のみ | 毎日09:00 JST自動実行 |
| **認証方法** | ブラウザでログイン | 事前トークン + Secrets |
| **24時間運用** | 不可（PC起動必要） | 可能（完全自動） |

---

## 📋 セットアップフロー（全体像）

```
┌─────────────────────────────────────────┐
│ 1️⃣ ローカルで初期認証（1回限り）      │
│  $ python youtube_uploader.py --test   │
│  → ブラウザ認可 → token.pickle 生成   │
└─────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ 2️⃣ 認証情報を Base64 エンコード      │
│  $ python encode_for_github.py         │
│  → Base64 文字列をコピー               │
└─────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ 3️⃣ GitHub Secrets に登録（1回限り）  │
│  Settings → Secrets → Register         │
│  - GOOGLE_SECRETS_BASE64               │
│  - GOOGLE_TOKEN_BASE64                 │
│  - R2_ACCOUNT_ID 他                    │
└─────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ 4️⃣ 自動実行開始 🎉                   │
│  毎日09:00 JSTに自動実行開始          │
│  手動実行も可能（Actions タブから）   │
└─────────────────────────────────────────┘
```

---

## 🔑 GitHub Secrets 登録項目

| Secret Name | 値の取得方法 | 例 |
|---|---|---|
| **GOOGLE_SECRETS_BASE64** | `encode_for_github.py` で出力 | `eyJpbnN0YWxs...` |
| **GOOGLE_TOKEN_BASE64** | `encode_for_github.py` で出力 | `gASVIgAAAH...` |
| **R2_ACCOUNT_ID** | 既存（Cloudflare R2 ダッシュボード） | `9122fb0f2c...` |
| **R2_ACCESS_KEY_ID** | 既存 | `fafa4cfb6e...` |
| **R2_SECRET_ACCESS_KEY** | 既存 | `f816a46eba...` |
| **R2_BUCKET_NAME** | 既存 | `mukashimukashi-audio` |
| **R2_ENDPOINT_URL** | 既存 | `https://9122...r2.cloudflarestorage.com` |

**登録確認:**
```
GitHub → Settings → Secrets and variables → Actions
→ ✓ が7個表示されれば成功
```

---

## 📅 実行スケジュール

### 自動実行（デフォルト）
```
毎日 09:00 JST に 2本のビデオをアップロード
（23:00 UTC にトリガー）
```

### スケジュール変更方法
`.github/workflows/main.yml` の `cron` を編集：

```yaml
schedule:
  - cron: '0 9 * * *'   # 18:00 JST
  - cron: '0 23 * * *'  # 09:00 JST（デフォルト）
  - cron: '0 12 * * 5'  # 金曜21:00 JST
```

[Cron 式ジェネレータ](https://crontab.guru/)

---

## 🧪 テスト実行手順

### ローカルで事前テスト
```bash
# 1本だけテスト実行（実際にはアップロードしない）
python youtube_uploader.py --limit 1 --test
```

### GitHub Actions でテスト実行
```
GitHub → Actions → YouTube自動アップロード
→ Run workflow
→ Limits: 1
→ Run workflow
```

出力:
```
🎙️ YouTube自動アップローダー起動
🔧 GitHub Actions環境で実行中
📊 処理数: 1本
⚠️ テストモード（アップロードしません）
```

---

## 🔄 トークン更新が必要な場合

Google トークンは以下の場合に無効化されます：
- 6ヶ月間使用されない
- ユーザーがパスワード変更
- 連携アプリを削除

**対処方法:**
```bash
# 1. ローカルでトークンを削除
rm token.pickle

# 2. 再認証実施
python youtube_uploader.py --test
# → ブラウザでログイン

# 3. 新しいトークンをエンコード
python encode_for_github.py

# 4. GitHub Secretを更新
# Settings → Secrets → GOOGLE_TOKEN_BASE64 を上書き
```

---

## 📊 実行ログの確認

### GitHub Actions のログ確認
```
GitHub リポジトリ
  → Actions タブ
    → YouTube自動アップロード
      → 最新の実行
        → ログ確認
```

### ログに表示される内容
```
✅ リポジトリをチェックアウト
✅ Python 3.11をセットアップ
✅ システムパッケージをインストール
✅ Pythonパッケージをインストール
✅ Google認証情報を復元
✅ YouTubeアップローダーを実行
  ├─ 📂 R2からファイル取得
  ├─ 🎬 動画変換
  ├─ 📤 YouTubeにアップロード
  └─ 💾 進捗を更新
✅ 実行成功
```

---

## ⚠️ よくあるエラーと対処法

### Error 1: 「GOOGLE_SECRETS_BASE64 が設定されていません」
```
❌ GitHub Secretsの登録漏れ
```
**対処:**
1. `python encode_for_github.py` を実行
2. GitHub Settings → Secrets に登録

### Error 2: 「YouTube認証エラー」
```
❌ 401 Unauthorized
```
**対処:**
1. `rm token.pickle` でローカルから削除
2. `python youtube_uploader.py --test` で再認証
3. `python encode_for_github.py` でエンコード
4. GitHub Secret を更新

### Error 3: 「ffmpeg not found」
```
❌ ffmpegがインストールされていない
```
**対処:** ワークフローを再実行（自動インストール）

詳細は `GITHUB_ACTIONS_DETAILS.md` を参照

---

## 📁 作成・修正されたファイル

| ファイル | 新規/修正 | 説明 |
|---------|---------|------|
| `.github/workflows/main.yml` | 新規 | GitHub Actionsワークフロー |
| `.github/scripts/restore_auth.py` | 新規 | 認証情報復元スクリプト |
| `youtube_uploader.py` | 修正 | CLI引数対応 + 環境変数対応 |
| `encode_for_github.py` | 新規 | Base64エンコード用ヘルパー |
| `GITHUB_ACTIONS_SETUP.md` | 新規 | セットアップガイド |
| `GITHUB_ACTIONS_DETAILS.md` | 新規 | 技術詳細ドキュメント |
| `GITHUB_ACTIONS_IMPLEMENTATION.md` | 新規 | 実装サマリー |
| `.gitignore` | 更新 | 認証情報除外確認済み |

---

## ✅ チェックリスト

セットアップ完了時に以下を確認：

- [ ] ローカルで `python youtube_uploader.py --test` が成功
- [ ] `python encode_for_github.py` が Base64値を出力
- [ ] GitHub Secrets に 7項目すべて登録済み
- [ ] `.github/workflows/main.yml` がリポジトリに含まれている
- [ ] `.gitignore` に `client_secrets.json` と `token.pickle` が含まれている
- [ ] `git status` で認証ファイルが含まれていないことを確認
- [ ] GitHub Actions タブで最新の実行ログを確認
- [ ] 動画が YouTube に投稿されている

---

## 🎯 実行パターン

### パターン1: 毎日自動実行
```
毎日09:00 JSTに自動実行（デフォルト）
↓
2本のビデオが自動アップロード
```

### パターン2: 手動テスト実行
```
Actions → Run workflow → limit: 1
↓
1本だけテスト実行
```

### パターン3: ローカルで動作確認
```bash
python youtube_uploader.py --limit 2
```

---

## 💡 Tips

**キャッシュの活用:**
- pip パッケージが自動キャッシュされます
- 2回目以降は高速化（約2分短縮）

**部分実行:**
```bash
# 1本だけテスト
python youtube_uploader.py --limit 1

# テストモード（実際にはアップロードしない）
python youtube_uploader.py --limit 1 --test
```

**スケジュール変更:**
- `.github/workflows/main.yml` の `cron` を編集
- [Cron 式ジェネレータ](https://crontab.guru/) で構文確認

---

## 📞 トラブル時の確認順序

1. **GitHub Actions ログを確認**
   - どのステップで失敗しているか？

2. **ローカルで同じコマンドを実行**
   ```bash
   python youtube_uploader.py --limit 1 --test
   ```

3. **GitHub Secrets を確認**
   - 登録漏れはないか？
   - 値は正しいか？

4. **ドキュメントを参照**
   - `GITHUB_ACTIONS_DETAILS.md` → トラブルシューティング

---

## 🎉 完成！

これで完全に自動実行される環境が完成しました。

**次: `GITHUB_ACTIONS_SETUP.md` でセットアップを開始 →**
