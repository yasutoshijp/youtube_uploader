# 🚀 GitHub Actions移行 - 実装完了サマリー

## 📦 実装内容

ローカルで動作している`youtube_uploader.py`をGitHub Actions上で完全自動実行できる環境に移行しました。

---

## ✅ 実装したファイル一覧

### 1. **ワークフロー定義** (`.github/workflows/main.yml`)

```yaml
on:
  schedule:
    - cron: '0 23 * * *'    # 毎日09:00 JSTに自動実行
  workflow_dispatch:         # 手動実行も可能
```

**このファイルの役割:**
- スケジュール実行（毎日09:00 JST）または手動実行
- Python環境のセットアップ
- ffmpeg、日本語フォントのインストール
- 認証情報の復元
- メインスクリプトの実行

---

### 2. **認証情報復元スクリプト** (`.github/scripts/restore_auth.py`)

```python
# GitHub Secretsから Base64エンコードされた認証情報を受け取り、
# 複号化して client_secrets.json と token.pickle に復元
```

**このファイルの役割:**
- Base64で複号化
- `client_secrets.json` を復元（Google OAuth設定）
- `token.pickle` を復元（YouTubeアクセストークン）
- エラーハンドリング

---

### 3. **メインスクリプト修正** (`youtube_uploader.py`)

**追加された機能:**
- コマンドライン引数対応（`--limit`, `--test`）
- GitHub Actions環境自動検出
- 環境変数からR2設定を読み込み

```python
# 使用例
python youtube_uploader.py --limit 2          # 2本処理
python youtube_uploader.py --limit 1 --test   # 1本テスト実行
```

---

### 4. **ヘルパースクリプト** (`encode_for_github.py`)

```bash
python encode_for_github.py
# → GitHub Secretsに登録すべき Base64エンコード値を出力
```

**このファイルの役割:**
- ローカルの認証情報をBase64エンコード
- GitHub Secretsへの登録手順をガイド

---

### 5. **セットアップガイド** (2つのドキュメント)

| ファイル | 対象 | 内容 |
|---------|------|------|
| `GITHUB_ACTIONS_SETUP.md` | 初心者向け | 簡潔な手順（5ステップ） |
| `GITHUB_ACTIONS_DETAILS.md` | 詳細解説向け | 技術詳細とトラブルシューティング |

---

## 🔐 認証フロー（新方式）

### 従来方式（ローカル）
```
ユーザー操作
    ↓
ブラウザで Google OAuth ログイン
    ↓
認証コードをコピーして貼り付け
    ↓
token.pickle 生成
```

### 新方式（GitHub Actions）
```
ステップ1: ローカルで一度認証
  python youtube_uploader.py --test
  → ブラウザでログイン、認証コード入力
  → token.pickle & client_secrets.json 生成

ステップ2: Base64エンコード
  python encode_for_github.py
  → Base64文字列を出力

ステップ3: GitHub Secretsに登録
  Settings → Secrets → New repository secret
  → GOOGLE_SECRETS_BASE64 登録
  → GOOGLE_TOKEN_BASE64 登録

ステップ4: 自動実行開始
  毎日09:00 JSTに GitHub Actions が実行
  → 認証情報を自動復元
  → YouTube自動アップロード実行
```

---

## 🛠️ セットアップ手順（クイックスタート）

### 前提条件
- `client_secrets.json` がローカルに存在すること
- `token.pickle` がローカルに生成済みであること

### 3ステップで完了

**1️⃣ ローカルで初期認証**
```bash
python youtube_uploader.py --test
# ブラウザでログイン → 認証コードを入力
```

**2️⃣ 認証情報をエンコード**
```bash
python encode_for_github.py
# → Base64値を表示
```

**3️⃣ GitHub Secretsに登録**
```
Settings → Secrets and variables → Actions
→ New repository secret

登録内容:
- GOOGLE_SECRETS_BASE64: [encode_for_github.py の出力]
- GOOGLE_TOKEN_BASE64: [encode_for_github.py の出力]
- R2_ACCOUNT_ID: [既存値]
- R2_ACCESS_KEY_ID: [既存値]
- R2_SECRET_ACCESS_KEY: [既存値]
- R2_BUCKET_NAME: mukashimukashi-audio
- R2_ENDPOINT_URL: https://9122fb0f...
```

完了！毎日09:00 JSTに自動実行が開始されます。

---

## 📊 実行仕様

### 自動実行
```
毎日09:00 JST（23:00 UTC）
処理内容: 2本の動画をアップロード
```

### 手動実行（テスト用）
```
GitHub → Actions → YouTube自動アップロード
→ Run workflow

実行例:
- limit: 1      # 1本のみ実行（テスト）
- limit: (空欄) # デフォルト 2本実行
```

### テストモード
```bash
# ローカルでテスト実行（アップロードしない）
python youtube_uploader.py --limit 1 --test
```

---

## 🔒 セキュリティ対策

### 実装済み
✅ 認証情報は `.gitignore` に登録済み  
✅ Base64エンコードで保護  
✅ GitHub Secretsで暗号化  
✅ ワークフログに認証情報は出力されない  

### 確認項目
```bash
# リポジトリに認証ファイルが含まれていないことを確認
git status
# (nothing to commit, working tree clean) と表示されるはず
```

---

## 🐛 よくあるトラブルと対処法

### トラブル1: 「認証情報が見つからない」エラー
```
❌ GOOGLE_SECRETS_BASE64 が設定されていません
```
→ GitHub Secretsの登録漏れ

**対処:** `encode_for_github.py` で出力した値をGitHub Secretsに登録

### トラブル2: トークン期限切れ
```
❌ YouTube認証エラー: 401 Unauthorized
```
→ トークンが無効化されている（6ヶ月未使用など）

**対処:** ローカルで再認証
```bash
rm token.pickle
python youtube_uploader.py --test
python encode_for_github.py
# GitHub Secret GOOGLE_TOKEN_BASE64 を更新
```

### トラブル3: ffmpeg が見つからない
```
❌ ffmpeg コマンドが見つかりません
```
→ 自動インストール失敗

**対処:** ワークフローを再実行（通常は自動で解決）

詳細は `GITHUB_ACTIONS_DETAILS.md` を参照

---

## 📈 処理フロー図

```
毎日09:00 JST
    ↓
GitHub Actions トリガー
    ↓
Python 3.11 環境構築
    ↓
ffmpeg, 日本語フォント インストール
    ↓
依存パッケージ インストール (pip)
    ↓
認証情報を Base64 から復元
    ↓
youtube_uploader.py 実行
    ↓
R2 から未処理音声ファイル取得
    ↓
サムネイル生成 + 動画変換
    ↓
YouTube にアップロード
    ↓
R2 の進捗ファイル更新
    ↓
完了 ✅
```

---

## 📝 ファイル構成

```
youtube_uploader/
│
├── .github/
│   ├── workflows/
│   │   └── main.yml              ← ワークフロー定義（毎日実行）
│   └── scripts/
│       └── restore_auth.py       ← 認証情報復元スクリプト
│
├── youtube_uploader.py           ← メインスクリプト（改良版）
├── encode_for_github.py          ← エンコード用ヘルパー
├── requirements.txt              ← Python 依存パッケージ
├── .gitignore                    ← 機密ファイル除外
├── GITHUB_ACTIONS_SETUP.md       ← セットアップガイド（簡潔版）
├── GITHUB_ACTIONS_DETAILS.md     ← 詳細解説ドキュメント
└── README.md                     ← 元々のドキュメント
```

---

## 💡 今後のメンテナンス

### 定期確認（月1回）
```bash
# ローカルでテスト実行
python youtube_uploader.py --limit 1 --test

# GitHub Actions の実行ログを確認
```

### トークン更新（6ヶ月ごと）
```bash
# トークンが無効化された場合
python youtube_uploader.py --test
python encode_for_github.py
# GitHub Secret を更新
```

### パッケージ更新
```bash
# 依存パッケージを最新化
pip install --upgrade -r requirements.txt
```

---

## 🎯 次のステップ

1. **今すぐできることシンプル版:** `GITHUB_ACTIONS_SETUP.md` を参照
2. **詳しく知りたい人向け:** `GITHUB_ACTIONS_DETAILS.md` を参照
3. **セットアップ開始:**
   - `python youtube_uploader.py --test` でローカル認証
   - `python encode_for_github.py` でエンコード
   - GitHub Secretsに登録
4. **動作確認:**
   - GitHub Actions で手動実行
   - または翌日09:00 JSTを待つ

---

## 🎉 完成！

これで、ローカル環境から完全に独立した自動実行環境が完成しました。

**実現できること:**
- ✅ ローカルマシンの起動不要
- ✅ 毎日自動でYouTubeにアップロード
- ✅ 手動実行でテスト可能
- ✅ セキュアな認証情報管理
- ✅ GitHub Actions の実行ログで進捗確認

Happy automated uploading! 🚀

---

**質問や問題が発生した場合:**
- ローカルで同じコマンドを実行して再現確認
- GitHub Actions の実行ログを確認
- `GITHUB_ACTIONS_DETAILS.md` のトラブルシューティングを参照
