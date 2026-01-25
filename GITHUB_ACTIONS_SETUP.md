# GitHub Actions自動実行セットアップガイド

## 概要

このドキュメントでは、ローカルで動作している `youtube_uploader.py` をGitHub Actions上で完全に自動実行できる環境に移行するための手順を説明します。

---

## 🎯 全体的なアプローチ

### 認証情報の安全な管理

ヘッドレス環境（GitHub Actions）では、ブラウザでのログイン操作ができません。そのため、以下の戦略を採用します：

1. **ローカルで一度認証を完了** → トークンを保存
2. **認証情報をBase64エンコード** → GitHubシークレットに登録
3. **実行時に複号化して復元** → そのまま使用

---

## 📋 準備手順

### 1️⃣ ローカルで初回認証を実施

GitHub Actionsに移行する前に、ローカルマシンで一度認証を完了してください。

```bash
# ローカルで実行
python youtube_uploader.py --test

# ブラウザが開き、Googleアカウントでログインするよう促されます
# 承認すると、以下のファイルが生成されます：
# - client_secrets.json
# - token.pickle
```

✅ これで認証情報が保存されました。

---

### 2️⃣ 認証情報をBase64エンコード

生成された認証情報をBase64にエンコードし、GitHub Secretsに登録します。

#### PowerShell（Windows）での実行：

```powershell
# client_secrets.json をBase64エンコード
$content = [System.IO.File]::ReadAllBytes(".\client_secrets.json")
$base64 = [Convert]::ToBase64String($content)
Write-Host $base64

# 出力をコピーして、GitHub Secret として登録します
```

#### Bash（Mac/Linux）での実行：

```bash
# client_secrets.json をBase64エンコード
cat client_secrets.json | base64 | tr -d '\n'

# token.pickle をBase64エンコード
cat token.pickle | base64 | tr -d '\n'
```

---

### 3️⃣ GitHub Secretsに登録

GitHub リポジトリ設定で、以下のシークレットを登録します：

**Settings → Secrets and Variables → Actions → New repository secret**

| シークレット名 | 値 | 説明 |
|---|---|---|
| `GOOGLE_SECRETS_BASE64` | client_secrets.jsonのBase64値 | Google OAuth設定情報 |
| `GOOGLE_TOKEN_BASE64` | token.pickleのBase64値 | YouTube APIのアクセストークン |
| `R2_ACCOUNT_ID` | Cloudflare R2アカウントID | 既存: `9122fb0f2c086a09610f7e86a874f232` |
| `R2_ACCESS_KEY_ID` | R2のアクセスキーID | 既存の値をコピー |
| `R2_SECRET_ACCESS_KEY` | R2のシークレットキー | 既存の値をコピー |
| `R2_BUCKET_NAME` | R2のバケット名 | 既存: `mukashimukashi-audio` |
| `R2_ENDPOINT_URL` | R2のエンドポイントURL | 既存: `https://9122fb0f2c086a09610f7e86a874f232.r2.cloudflarestorage.com` |

---

## ⚙️ ワークフロー設定

### 自動実行スケジュール

`.github/workflows/main.yml` では、以下のように設定しています：

```yaml
on:
  schedule:
    - cron: '0 23 * * *'  # 毎日23:00 UTC = 09:00 JST
  workflow_dispatch:       # 手動実行も可能
```

**調整方法:**

- 毎日09:00 JST実行：`cron: '0 23 * * *'`
- 毎日18:00 JST実行：`cron: '0 9 * * *'`
- 毎週金曜21:00 JST実行：`cron: '0 12 * * 5'`

---

## 🚀 実行方法

### 自動実行（スケジュール）

毎日09:00 JSTに自動的に2本の動画がアップロードされます。

実行状況は GitHub Actions タブで確認できます：  
**GitHub → Actions → YouTube自動アップロード**

### 手動実行（テスト用）

```
GitHub → Actions → YouTube自動アップロード → Run workflow

- "処理する動画数" に 1 を入力 → テスト実行
- 空欄 → デフォルト（2本）実行
```

---

## 🔧 認証情報のメンテナンス

### トークンの更新が必要な場合

Google APIの認証トークンは自動的にリフレッシュされますが、以下の場合は再度ローカル認証が必要です：

1. **トークンの有効期限が切れた場合**
2. **YouTubeアカウント認可を取り消した場合**
3. **新しいスコープを追加した場合**

対処方法：
```bash
# ローカルで token.pickle を削除
rm token.pickle

# 再度認証を実施
python youtube_uploader.py --test

# 新しい token.pickle をBase64エンコード
cat token.pickle | base64 | tr -d '\n'

# GitHub Secretの GOOGLE_TOKEN_BASE64 を更新
```

---

## 📊 実行ログの確認

GitHub Actions上でのアップロード状況を確認できます：

1. **GitHub リポジトリ → Actions タブ**
2. **YouTube自動アップロード をクリック**
3. **最新の実行履歴を確認**

各ステップの詳細ログが表示されます：
- ✅ 環境構築
- ✅ 依存関係インストール
- ✅ 認証情報復元
- ✅ YouTubeアップロード

失敗時はエラーログが保存されます（7日間保持）。

---

## ⚠️ トラブルシューティング

### 「認証情報が無効」エラー

```
❌ YouTube認証に失敗しました
```

**原因:** token.pickleが正しく復元されていない

**対処:**
1. ローカルで `python youtube_uploader.py --test` を実行
2. 新しい token.pickle をBase64エンコード
3. GitHub Secret `GOOGLE_TOKEN_BASE64` を更新

### 「R2接続エラー」

```
❌ R2からファイル取得エラー
```

**原因:** R2の認証情報が間違っている

**対処:**
1. Cloudflare R2ダッシュボードで認証情報を確認
2. 正しい値で GitHub Secrets を更新

### 「ffmpegコマンドが見つからない」

```
❌ 動画変換エラー: ffmpeg not found
```

**原因:** Ubuntu環境でffmpegがインストールされていない

**解決:** ワークフロー内で自動インストール済み（.github/workflows/main.yml）

---

## 🔐 セキュリティベストプラクティス

✅ **実装済み:**
- 認証情報はBase64エンコード後、GitHub Secretsに登録
- 環境変数経由で安全に注入
- ローカルの client_secrets.json と token.pickle は .gitignore に追加すること
- ワークフロー実行ログには認証情報は表示されない

❌ **してはいけないこと:**
- クレデンシャルをリポジトリにコミットする
- Secretの値をログに出力する
- 公開リポジトリで機密情報を扱う

---

## 📝 定期メンテナンス

### 月1回の確認作業

```bash
# ローカルでテスト実行
python youtube_uploader.py --limit 1 --test

# ワークフローが正常に実行されているか確認
# GitHub Actions タブで最新の実行ログをチェック
```

### Pythonパッケージの更新

```bash
# requirements.txt を最新に更新
pip install --upgrade boto3 google-auth-oauthlib google-api-python-client pillow

# GitHub Actions環境も自動更新（キャッシュ使用）
```

---

## 📚 関連ファイル

```
.github/
├── workflows/
│   └── main.yml              # GitHub Actionsワークフロー定義
└── scripts/
    └── restore_auth.py       # 認証情報復元スクリプト

youtube_uploader.py           # メインスクリプト（改良版）
requirements.txt              # Python依存パッケージ
```

---

## 💡 Tips

### テスト実行の活用

本番前に1本だけテスト実行：

```
Actions → Run workflow → limit: 1
```

### スケジュールの調整

更新頻度を変更したい場合：

`.github/workflows/main.yml` の `cron` を編集

```yaml
schedule:
  - cron: '0 9 * * *'  # 毎日18:00 JST（9:00 UTC）
```

### 失敗時の自動通知

GitHub Notificationsで失敗時にメール通知を受け取ることができます。

**Settings → Notifications → Subscriptions を確認**

---

## 📞 サポート

問題が発生した場合：

1. GitHub Actions実行ログを確認
2. エラーメッセージをメモ
3. ローカルで同じスクリプトを実行して再現確認
4. トラブルシューティングを参照

Happy uploading! 🎉
