# YouTube自動アップローダー - ひさこばあばのむかしむかし

## 概要
Cloudflare R2の音声ファイルを自動的にYouTubeに動画としてアップロードするシステム

---

## 🚀 環境構築（新規セットアップ）

### 1. 必要パッケージインストール
```bash
sudo apt update
sudo apt install -y python3-venv python3-pip ffmpeg fonts-noto-cjk
```

### 2. プロジェクトディレクトリ作成
```bash
mkdir -p /home/yasutoshi/projects/08.youtube_updater
cd /home/yasutoshi/projects/08.youtube_updater
```

### 3. 仮想環境作成
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Pythonパッケージインストール
```bash
pip install --break-system-packages boto3 pillow google-auth-oauthlib google-api-python-client
```

### 5. 必要ファイル配置
以下のファイルが必要です:
- `client_secrets.json` - Google Cloud Consoleから取得（後述）
- `thumbnail_template.jpg` - サムネイルテンプレート画像（1024x572px）
- `youtube_uploader.py` - メインスクリプト（後述）

---

## 📁 設定ファイル

### client_secrets.json の作成
```bash
cat > client_secrets.json << 'EOF'
{"installed":{"client_id":"1072628703968-hc8o4d3ode3ndqc6cue3sjg10pt3rrj7.apps.googleusercontent.com","project_id":"noted-ability-482803-n8","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"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","redirect_uris":["http://localhost"]}}
EOF
```

### thumbnail_template.jpg の取得
OneDriveまたはUSBメモリから転送:
```
C:\Users\yasut\OneDrive\ドキュメント\ひさこばあば\thumbnail_template.jpg
```

PowerShellから転送:
```powershell
scp "C:\Users\yasut\OneDrive\ドキュメント\ひさこばあば\thumbnail_template.jpg" yasutoshi@192.168.4.119:/home/yasutoshi/projects/08.youtube_updater/
```

---

## ⚙️ 設定内容

### R2設定（youtube_uploader.py内）
```python
R2_CONFIG = {
    'account_id': '9122fb0f2c086a09610f7e86a874f232',
    'access_key_id': 'fafa4cfb6ea0938c8300cdba723bb790',
    'secret_access_key': 'f816a46eba22879ad19c1d544e794a05572a8a220251417a6e54cc7d279dca14',
    'bucket_name': 'mukashimukashi-audio',
    'endpoint_url': 'https://9122fb0f2c086a09610f7e86a874f232.r2.cloudflarestorage.com'
}
```

### YouTube設定
- **アカウント**: hisakobaa@gmail.com
- **カテゴリ**: Entertainment (24)
- **初期状態**: private（予約投稿）
- **1日のアップロード数**: 2本
- **公開時刻**: 毎日09:00 JST
- **開始日**: 2025-12-27

### Google Cloud Console設定
- **プロジェクト**: noted-ability-482803-n8
- **OAuth 2.0 クライアントID**: 1072628703968-hc8o4d3ode3ndqc6cue3sjg10pt3rrj7
- **タイプ**: デスクトップアプリ
- **テストユーザー**: hisakobaa@gmail.com

---

## 🎬 実行方法

### 手動実行（初回）
```bash
cd /home/yasutoshi/projects/08.youtube_updater
source venv/bin/activate
python youtube_uploader.py
```

### 初回認証手順
1. スクリプトを実行するとURLが表示される
2. ブラウザでURLを開く
3. **hisakobaa@gmail.com** でログイン
4. 「許可」をクリック
5. 表示された**認証コード**をコピー
6. ターミナルに戻って認証コードを貼り付け
7. `token.pickle` が作成され、以降は認証不要

### 認証コードの場所
ブラウザに表示されるURL:
```
https://accounts.google.com/o/oauth2/approval/v2/approvalnativeapp?...&approvalCode=4/1ATX87...
```
この `approvalCode=` の後ろの文字列が認証コード

---

## ⏰ cron設定（自動実行）

### cron設定手順
```bash
# crontabを開く
crontab -e

# エディタで以下を追加
0 1 * * * cd /home/yasutoshi/projects/08.youtube_updater && /home/yasutoshi/projects/08.youtube_updater/venv/bin/python youtube_uploader.py >> /home/yasutoshi/projects/08.youtube_updater/cron.log 2>&1

# 保存して終了（nano: Ctrl+O → Enter → Ctrl+X）
```

### cron設定の意味
```
0 1 * * *     毎日午前1時に実行
cd ...        作業ディレクトリに移動
venv/bin/python  仮想環境のPythonで実行
>> cron.log   ログをファイルに記録
2>&1          エラーもログに記録
```

### cron確認コマンド
```bash
# 設定内容確認
crontab -l

# ログ確認（リアルタイム）
tail -f /home/yasutoshi/projects/08.youtube_updater/cron.log

# ログ確認（最新50行）
tail -50 /home/yasutoshi/projects/08.youtube_updater/cron.log

# cronサービス状態確認
systemctl status cron

# システムログでcron実行を確認
grep CRON /var/log/syslog | tail -20
```

---

## 📂 ファイル構成
```
/home/yasutoshi/projects/08.youtube_updater/
├── venv/                      # Python仮想環境
├── client_secrets.json        # Google OAuth認証情報
├── token.pickle              # 保存された認証トークン（初回実行後に生成）
├── thumbnail_template.jpg     # サムネイルテンプレート（1024x572px）
├── youtube_uploader.py        # メインスクリプト
├── youtube_published.txt      # アップロード済みファイル管理
├── cron.log                  # cron実行ログ
├── requirements.txt          # Pythonパッケージリスト
└── README.md                 # このファイル
```

---

## 📝 タイトル抽出ルール

ファイル名から以下のルールでタイトルを抽出:

1. **「」内の文字列を優先抽出**
   - `0722「かまがみさまのはじまり」新規録音 #16.m4a` → `かまがみさまのはじまり`

2. **日付プレフィックス削除**
   - `0722`, `0806`, `200515-` などを削除

3. **接頭辞削除**
   - `語り　`, `朗読　`, `新規録音 #XX` を削除

4. **末尾のゴミ削除**
   - `#番号`, `(1)`, `(2)`, `(重複)`, `【】` を削除

5. **空白削除**
   - 全角・半角スペースを削除

### 抽出例
```
0722「かまがみさまのはじまり」新規録音 #16.m4a  → かまがみさまのはじまり
語り　供養を願う骸骨.m4a                      → 供養を願う骸骨
朗読　優しくなった坂東長者.m4a                → 優しくなった坂東長者
200515-娘狐の恩返し.MP3                       → 娘狐の恩返し
鬼の面.m4a                                   → 鬼の面
鬼の面(2).m4a                                → 鬼の面
```

**注意**: `鬼の面.m4a` と `鬼の面(2).m4a` は**別ファイル**として管理され、両方アップロードされます（タイトルは同じでもファイル名で重複管理）

---

## 🎨 サムネイル生成

### 仕様
- **ベース画像**: 1024x572px
- **フォント**: Noto Sans CJK Bold (`/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc`)
- **初期フォントサイズ**: 90px
- **自動縮小**: タイトルが760pxを超える場合、35pxまで5px刻みで縮小
- **Y座標調整**: フォントサイズに応じて自動調整
  - 85px以上: Y=438
  - 75-85px: Y=443
  - 65-75px: Y=448
  - 55-65px: Y=452
  - 55px以下: Y=455
- **縁取り**: 黒3px
- **テキスト色**: 白

---

## 🔧 トラブルシューティング

### 認証エラーが出る
```bash
# 認証情報を削除して再認証
cd /home/yasutoshi/projects/08.youtube_updater
rm token.pickle
source venv/bin/activate
python youtube_uploader.py
```

### フォントが見つからないエラー
```bash
# 日本語フォント再インストール
sudo apt install --reinstall fonts-noto-cjk

# フォントファイルの場所確認
ls -la /usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc
```

### ffmpegエラー
```bash
# ffmpeg再インストール
sudo apt install --reinstall ffmpeg

# ffmpeg動作確認
ffmpeg -version
```

### cronが動かない
```bash
# cronサービス状態確認
systemctl status cron

# cronサービス再起動
sudo systemctl restart cron

# cron設定確認
crontab -l

# システムログでcron実行を確認
grep CRON /var/log/syslog | tail -50

# 手動実行でエラー確認
cd /home/yasutoshi/projects/08.youtube_updater && /home/yasutoshi/projects/08.youtube_updater/venv/bin/python youtube_uploader.py
```

### R2接続エラー
```bash
# ネットワーク確認
ping 1.1.1.1

# R2エンドポイント確認
curl https://9122fb0f2c086a09610f7e86a874f232.r2.cloudflarestorage.com
```

### YouTube API エラー
- **アップロード上限**: 1日6本（通常アカウント）
- **テストユーザー**: hisakobaa@gmail.com が登録されているか確認
- **Google Cloud Console**: https://console.cloud.google.com/

---

## 📊 処理スケジュール

### 自動処理の流れ
```
毎日午前1時: cronが起動
↓
1本目処理開始
├─ R2からダウンロード（1-2分）
├─ サムネイル生成（数秒）
├─ 動画変換（5-10分）
└─ YouTubeアップロード（2-5分）
↓
2本目処理開始
├─ R2からダウンロード（1-2分）
├─ サムネイル生成（数秒）
├─ 動画変換（5-10分）
└─ YouTubeアップロード（2-5分）
↓
処理完了（合計: 約20-40分）
```

### 公開スケジュール
- **開始日**: 2025-12-27 09:00
- **頻度**: 1日2本
- **総数**: 800本以上
- **完了予定**: 約400日後（2026年2月頃）

---

## ⚠️ 注意事項

### YouTube API
- **1日のアップロード上限**: 通常6本
- **現在の設定**: 1日2本（上限内）
- **テストユーザー**: hisakobaa@gmail.com として登録済み

### ストレージ
- **一時ファイル**: `/tmp` に音声・動画ファイルが一時保存される
- **必要容量**: 1本あたり最大50MB程度
- **自動削除**: 処理完了後に自動削除

### ネットワーク
- **R2ダウンロード**: 1本あたり数MB〜数十MB
- **YouTubeアップロード**: 1本あたり10-50MB
- **月間通信量**: 約3-6GB（2本/日の場合）

### Pi 5のリソース
- **CPU**: 動画変換時に高負荷
- **メモリ**: 1GB程度使用
- **ディスク**: 十分な空き容量が必要

---

## 🔐 セキュリティ

### 機密情報
以下のファイルには機密情報が含まれます。**絶対にGitHubにアップロードしないこと**:
- `client_secrets.json` - OAuth認証情報
- `token.pickle` - 認証トークン
- `cron.log` - 実行ログ（エラーメッセージが含まれる可能性）

### .gitignore
GitHubにアップロードする場合は、以下の `.gitignore` を作成:
```
venv/
*.pickle
token.pickle
client_secrets.json
youtube_published.txt
cron.log
*.pyc
__pycache__/
```

---

## 📜 変更履歴

- **2025-01-07**: 初回構築（新Raspberry Pi 5）
- Raspberry Pi 5で動作確認済み
- OS: Debian Trixie
- Python: 3.13

---

## 📞 サポート

### 関連リンク
- **ブログ**: https://hisakobaab.exblog.jp/
- **Podcast RSS**: https://pub-b419a653b80e45909d7db83acfedce2c.r2.dev/podcast.xml
- **Google Cloud Console**: https://console.cloud.google.com/

### トラブル時の確認項目
1. `token.pickle` が存在するか
2. `client_secrets.json` が正しいか
3. インターネット接続ができるか
4. cronが動作しているか
5. ログファイル `cron.log` の内容

---

## 🎯 まとめ

このシステムは:
- ✅ Cloudflare R2から自動で音声取得
- ✅ 自動でサムネイル生成
- ✅ 自動で動画変換
- ✅ 自動でYouTubeアップロード
- ✅ 予約投稿で毎日09:00に公開
- ✅ cronで毎日自動実行

**一度設定すれば、完全自動で800本以上の昔話が毎日YouTubeに公開されます** 🎉

---

## 🔧 重要な設定

### cron起動時の15秒遅延
ネットワーク接続が確立するまで待つため、cron設定に15秒の遅延を追加:
```bash
0 1 * * * /bin/sleep 15 && cd /home/yasutoshi/projects/08.youtube_updater && /home/yasutoshi/projects/08.youtube_updater/venv/bin/python youtube_uploader.py >> /home/yasutoshi/projects/08.youtube_updater/cron.log 2>&1
```

**理由**: Pi起動直後やネットワーク不安定時にcronが実行されると、R2接続やYouTube認証が失敗する可能性があるため。

### YouTube認証は手動入力モード
`youtube_uploader.py` の `authenticate_youtube()` メソッドは手動認証モード:
```python
# ブラウザが自動で開かない設定
flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
auth_url, _ = flow.authorization_url(prompt="consent")
print(f"\n1. このURLをブラウザで開いてください:")
print(f"{auth_url}\n")
code = input("\n認証コード: ").strip()
```

**理由**: Pi 5でブラウザが自動起動せず、認証コールバックを受け取れないため。手動でブラウザを開き、認証コードをコピー&ペーストする方式。

---

## 🔄 既存のcron設定を修正する場合
```bash
# crontabを開く
crontab -e

# 古い設定を削除して、以下に置き換え:
0 1 * * * /bin/sleep 15 && cd /home/yasutoshi/projects/08.youtube_updater && /home/yasutoshi/projects/08.youtube_updater/venv/bin/python youtube_uploader.py >> /home/yasutoshi/projects/08.youtube_updater/cron.log 2>&1
```

