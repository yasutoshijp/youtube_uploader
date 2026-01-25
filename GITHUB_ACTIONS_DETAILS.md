# GitHub Actions移行ガイド - 詳細解説

## 📋 目次

1. [全体構成](#全体構成)
2. [認証方法の選択肢と採用理由](#認証方法の選択肢と採用理由)
3. [セットアップ手順（詳細版）](#セットアップ手順詳細版)
4. [ワークフローの動作仕様](#ワークフローの動作仕様)
5. [トラブルシューティング](#トラブルシューティング)

---

## 全体構成

```
youtube_uploader/
├── .github/
│   ├── workflows/
│   │   └── main.yml                 ← GitHub Actions定義
│   └── scripts/
│       └── restore_auth.py          ← 認証情報復元スクリプト
│
├── youtube_uploader.py              ← メイン（改良版）
├── encode_for_github.py             ← エンコード用ヘルパー
├── requirements.txt                 ← 依存パッケージ
├── GITHUB_ACTIONS_SETUP.md          ← 簡易ガイド
└── GITHUB_ACTIONS_DETAILS.md        ← このファイル
```

---

## 認証方法の選択肢と採用理由

### ❌ 選択肢1: ローカル認証（OOB フロー）

```python
# ローカルではこれが動作します
flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
code = input("\n認証コード: ").strip()  # ← ユーザー入力待ち
```

**問題点:**
- GitHub Actionsはヘッドレス環境（ブラウザなし）
- ユーザーインタラクションができない
- 自動実行が不可能

### ❌ 選択肢2: OAuth 2.0 Client Credentials フロー

```python
# これはサービス間認証用
credentials = Credentials.from_service_account_file('service_account.json')
```

**問題点:**
- YouTube Data API v3は個人アカウント認証が必須
- サービスアカウント認証では不可能
- YouTubeチャンネルの概要欄操作などができない

### ✅ 採用: 事前トークン保存 + Base64復元方式

```python
# ステップ1: ローカルで一度認証（ブラウザを使用）
# ステップ2: token.pickle を生成・保存
# ステップ3: token.pickle を Base64エンコード
# ステップ4: GitHub Secretsに登録
# ステップ5: GitHub Actionsで自動複号化・復元
```

**利点:**
- ✅ YouTube個人認証をサポート
- ✅ 完全な自動化が可能
- ✅ セキュア（Secretsで暗号化）
- ✅ トークン自動リフレッシュ対応
- ✅ ユーザー操作不要

---

## セットアップ手順（詳細版）

### ステップ1: ローカルで初期認証を完了

```bash
# プロジェクトディレクトリに移動
cd youtube_uploader

# requirements.txt をインストール
pip install -r requirements.txt

# テスト実行（認証促されます）
python youtube_uploader.py --test
```

**実行時に何が起こるか:**

```
🎙️ YouTube自動アップローダー起動
============================================================
💻 ローカル環境で実行中
📊 処理数: 2本
============================================================

🧪 テストモード: ファイル取得確認のみ

1. このURLをブラウザで開いてください:
https://accounts.google.com/o/oauth2/auth?...

2. ログインして許可してください
3. 表示された認証コードをコピーしてください

認証コード: [← ここに認証コードをペーストして Enter]

✓ 認証情報を保存しました
✓ 保存済み認証情報を使用
✓ token.pickle を復元しました

✅ YouTube認証完了

✓ 処理対象ファイル一覧:
  1. file1.m4a
  2. file2.m4a
```

**この時点で生成されるファイル:**
- `client_secrets.json` - Google OAuth認証情報
- `token.pickle` - YouTube APIアクセストークン（有効期限あり）

### ステップ2: 認証情報をBase64エンコード

#### 方法A: ヘルパースクリプト使用（推奨）

```bash
# Pythonスクリプトでエンコード
python encode_for_github.py

# 出力例:
# 🔐 GitHub Secrets用 認証情報エンコード
# ============================================================
# 
# 1️⃣ client_secrets.json のエンコード
# ──────────────────────────────────────────────────────────
# ✓ 以下をGitHub Secret 'GOOGLE_SECRETS_BASE64' に登録してください:
# 
# eyJpbnN0YWxsZWQiOnsiY2xpZW50X2lkIjoiMTA3MjYyODcwMzk2OC1oYzg...（長い文字列）
```

#### 方法B: コマンドラインで直接実行（Windows PowerShell）

```powershell
# client_secrets.json をエンコード
$content = [System.IO.File]::ReadAllBytes(".\client_secrets.json")
$base64 = [Convert]::ToBase64String($content)
$base64 | Set-Clipboard  # クリップボードにコピー
Write-Host "✓ クリップボードにコピーしました"
```

#### 方法B: コマンドラインで直接実行（Mac/Linux）

```bash
# client_secrets.json をエンコード
base64 < client_secrets.json | tr -d '\n'

# token.pickle をエンコード
base64 < token.pickle | tr -d '\n'
```

### ステップ3: GitHub Secretsに登録

**重要: パブリックリポジトリの場合**

機密情報を扱うため、リポジトリは **Private** に設定してください。

**登録手順:**

1. GitHub のリポジトリページを開く
2. **Settings** → **Secrets and variables** → **Actions** をクリック
3. **New repository secret** をクリック
4. 以下を登録：

| Name | Value | 説明 |
|------|-------|------|
| `GOOGLE_SECRETS_BASE64` | `encode_for_github.py` の出力1 | Google OAuth設定 |
| `GOOGLE_TOKEN_BASE64` | `encode_for_github.py` の出力2 | YouTubeアクセストークン |
| `R2_ACCOUNT_ID` | `9122fb0f2c086a09610f7e86a874f232` | Cloudflare R2 |
| `R2_ACCESS_KEY_ID` | (既存値) | Cloudflare R2 |
| `R2_SECRET_ACCESS_KEY` | (既存値) | Cloudflare R2 |
| `R2_BUCKET_NAME` | `mukashimukashi-audio` | Cloudflare R2 |
| `R2_ENDPOINT_URL` | `https://9122fb0f2c086a09610f7e86a874f232.r2.cloudflarestorage.com` | Cloudflare R2 |

**登録確認:**

Settings画面で以下のように表示されれば成功：

```
✓ GOOGLE_SECRETS_BASE64
✓ GOOGLE_TOKEN_BASE64
✓ R2_ACCOUNT_ID
✓ R2_ACCESS_KEY_ID
✓ R2_SECRET_ACCESS_KEY
✓ R2_BUCKET_NAME
✓ R2_ENDPOINT_URL
```

---

## ワークフローの動作仕様

### ファイル: `.github/workflows/main.yml`

#### トリガー

```yaml
on:
  schedule:
    - cron: '0 23 * * *'  # 毎日 23:00 UTC = 09:00 JST
  workflow_dispatch:       # 手動実行ボタン
```

#### 実行ステップの詳細

```yaml
steps:
  - name: リポジトリをチェックアウト
    # ステップ目的: ソースコードを取得
    # 使用: actions/checkout@v4
    
  - name: Python 3.11をセットアップ
    # ステップ目的: Python環境を構築
    # 使用: actions/setup-python@v4
    # キャッシュ: pip (requirements.txt)
    
  - name: システムパッケージをインストール
    # ステップ目的: ffmpeg, 日本語フォント をインストール
    # 実行: sudo apt-get install -y ffmpeg fonts-noto-cjk
    
  - name: Pythonパッケージをインストール
    # ステップ目的: boto3, pillow, google-auth-oauthlib などをインストール
    # 実行: pip install -r requirements.txt
    # キャッシュにより初回のみダウンロード
    
  - name: Google認証情報を復元
    # ステップ目的: Base64エンコードされたシークレットを複号化
    # 実行スクリプト: .github/scripts/restore_auth.py
    # 処理:
    #   1. 環境変数 GOOGLE_SECRETS_BASE64 をBase64複号化
    #   2. client_secrets.json に書き込み
    #   3. 環境変数 GOOGLE_TOKEN_BASE64 をBase64複号化
    #   4. token.pickle に書き込み
    
  - name: YouTubeアップローダーを実行
    # ステップ目的: メイン処理を実行
    # 実行: python youtube_uploader.py --limit 2
    # 環境変数: R2の認証情報を注入
    # 処理流:
    #   1. token.pickle を読み込み（既に復元済み）
    #   2. YouTube APIで認証（トークンリフレッシュ）
    #   3. R2から音声ファイルを取得
    #   4. 動画変換・アップロード
```

---

## トラブルシューティング

### エラー1: 「GOOGLE_SECRETS_BASE64 が設定されていません」

```
⚠️ GOOGLE_SECRETS_BASE64 が設定されていません
❌ 認証情報の復元に失敗しました
```

**原因:** GitHub Secretsの登録漏れ

**対処:**
1. `encode_for_github.py` を実行
2. GitHub Settings → Secrets で登録

### エラー2: 「token.pickle の復元に失敗」

```
❌ token.pickle の復元に失敗: ...
```

**原因:**
- トークンの有効期限切れ
- Base64エンコードが不正
- ローカルの token.pickle が破損

**対処:**
```bash
# ローカルで再認証
rm token.pickle
python youtube_uploader.py --test

# 新しい token.pickle をエンコード
python encode_for_github.py

# GitHub Secret を更新
```

### エラー3: 「ffmpeg コマンドが見つからない」

```
❌ 動画変換エラー: ffmpeg not found
```

**原因:** システムパッケージのインストール失敗

**対処:** ワークフロー内で自動インストール（既に対応済み）

再実行すれば解決します。

### エラー4: 「YouTube API認証エラー」

```
❌ YouTube認証に失敗しました
googleapiclient.errors.HttpError: <HttpError 401: Unauthorized>
```

**原因:**
- トークンの有効期限切れ
- YouTubeアカウントで認可を取り消した
- トークンの権限が不足

**対処:**

```bash
# ローカルで再認証
python youtube_uploader.py --test

# ブラウザで認可画面が表示される
# 許可をクリック → 認証コードをコピペ

# 新しい token.pickle を GitHub Secretに登録
```

### エラー5: 「R2 接続エラー」

```
❌ R2からファイル取得エラー: NoCredentialsError
```

**原因:** R2の認証情報が間違っている

**対処:**
1. Cloudflare R2ダッシュボードで認証情報を確認
2. GitHub Secretsで正しい値に更新

```
R2_ACCOUNT_ID: 9122fb0f2c...
R2_ACCESS_KEY_ID: xxxxxxxx...
R2_SECRET_ACCESS_KEY: yyyyyyyy...
```

---

## 🔒 セキュリティチェックリスト

必ず以下を確認してください：

- [ ] `.gitignore` に `client_secrets.json` と `token.pickle` が含まれている
- [ ] リポジトリがプライベート（Private）である
- [ ] GitHub Secrets が適切に登録されている
- [ ] ローカルで `git status` を実行して、機密ファイルがコミット対象になっていないことを確認

```bash
# 確認方法
git status

# これは ❌ 危険
# new file:   client_secrets.json
# new file:   token.pickle

# これは ✅ 安全
# (nothing to commit, working tree clean)
```

---

## 📊 本番運用チェックリスト

初回セットアップ後、以下を確認：

- [ ] GitHub Actions が毎日09:00 JST に実行されている
- [ ] Actions ログに「✅ YouTubeアップロード完了」が表示されている
- [ ] 動画が YouTube に投稿されている
- [ ] R2 の `youtube_published.txt` が更新されている

---

## 💡 最適化のティップス

### キャッシュの活用

ワークフロー内で pip パッケージをキャッシュしているため、2回目以降は高速化：

```yaml
- uses: actions/setup-python@v4
  with:
    cache: 'pip'  # 自動的にキャッシュを有効化
```

効果: 約2分短縮

### 部分実行のテスト方法

本番前に1本だけテスト：

```
GitHub → Actions → YouTube自動アップロード
→ Run workflow → inputs: 1
```

### ログ出力の最適化

ワークフロー実行時間を把握：

```bash
# ローカルで --time オプション（実装可能）
time python youtube_uploader.py --limit 1
```

---

## 📞 よくある質問（FAQ）

**Q: トークンの有効期限は？**

A: Google OAuth 2.0のリフレッシュトークンは、以下の場合無効化されます：
- 6ヶ月間使用されない
- ユーザーがパスワードを変更
- ユーザーが連携アプリを削除

詳細: [Google OAuth2 ドキュメント](https://developers.google.com/identity/protocols/oauth2#expiration)

**Q: 複数チャンネルにアップロードできる？**

A: 現在は単一アカウント対応です。複数チャンネル対応は将来の拡張検討。

**Q: 手動実行の頻度に制限はある？**

A: GitHub Actions は月3,000分まで無料です。毎日1回なら約30日分で問題なし。

**Q: 失敗した場合の自動リトライはある？**

A: 現在なし。失敗時はGitHub Notificationsでメール通知。手動で再実行可能。

---

Happy uploading! 🚀
