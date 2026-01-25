#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube自動アップローダー - ひさこばあばのむかしむかし
GitHub Actions対応版
"""

import os
import sys
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import re
import argparse
import boto3
from botocore.exceptions import ClientError
from PIL import Image, ImageDraw, ImageFont
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload

# ========================================
# 設定
# ========================================

# GitHub ActionsのSecret、または環境変数から読み込み
R2_CONFIG = {
    'account_id': os.environ.get('R2_ACCOUNT_ID', '9122fb0f2c086a09610f7e86a874f232'),
    'access_key_id': os.environ.get('R2_ACCESS_KEY_ID', 'fafa4cfb6ea0938c8300cdba723bb790'),
    'secret_access_key': os.environ.get('R2_SECRET_ACCESS_KEY', 'f816a46eba22879ad19c1d544e794a05572a8a220251417a6e54cc7d279dca14'),
    'bucket_name': os.environ.get('R2_BUCKET_NAME', 'mukashimukashi-audio'),
    'endpoint_url': os.environ.get('R2_ENDPOINT_URL', 'https://9122fb0f2c086a09610f7e86a874f232.r2.cloudflarestorage.com')
}

# YouTube設定
YOUTUBE_CONFIG = {
    'client_secrets_file': 'client_secrets.json',
    'scopes': ['https://www.googleapis.com/auth/youtube.upload'],
    'category_id': '24',
    'privacy_status': 'private',
    'tags': ['昔話', '民話', '日本の昔話', '読み聞かせ', 'ひさこばあば'],
}

# サムネイル設定
THUMBNAIL_CONFIG = {
    'template_image': 'thumbnail_template.jpg',
    'font_path': '/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc',
    'text_color': 'white',
}

# 概要欄テンプレート
DESCRIPTION_TEMPLATE = """昔話「{title}」をお届けします。

昭和6年（1931年）生まれ、ひさこばあばが語る日本の民話です。

🎙️ ブログ「90代万歳」
https://hisakobaab.exblog.jp/

📚 全863話を毎日配信中

🎧 Podcastでも配信中
https://pub-b419a653b80e45909d7db83acfedce2c.r2.dev/podcast.xml

#昔話 #民話 #日本の昔話 #読み聞かせ #ひさこばあば
"""

# アップロード設定
UPLOAD_CONFIG = {
    'start_date': '2025-12-27',
    'videos_per_day': 2,
    'publish_time': '09:00:00',
}

# ★除外ファイルリスト（履歴になくても強制的にスキップするファイル）
IGNORE_FILES = [
    "‗学徒動員のころ.m4a",
    "0806‗学徒動員のころ.m4a",
    "学徒動員のころ.m4a"
]


class YouTubeUploader:
    def __init__(self):
        """初期化"""
        # 進捗管理ファイル名（R2上のファイル名）
        self.remote_progress_file = 'youtube_published.txt'
        
        self.s3_client = self._init_r2_client()
        self.youtube = None
        self.published_list = self._load_published()

    def _init_r2_client(self):
        """R2クライアント初期化"""
        return boto3.client(
            's3',
            endpoint_url=R2_CONFIG['endpoint_url'],
            aws_access_key_id=R2_CONFIG['access_key_id'],
            aws_secret_access_key=R2_CONFIG['secret_access_key'],
            region_name='auto'
        )

    def _load_published(self):
        """R2からアップロード済みリスト読み込み"""
        print("📂 アップロード済みリストをクラウドから取得中...")
        try:
            # R2からオブジェクトを取得
            response = self.s3_client.get_object(
                Bucket=R2_CONFIG['bucket_name'],
                Key=self.remote_progress_file
            )
            # 中身を読み込んでセットにする
            content = response['Body'].read().decode('utf-8')
            published = set(line.strip() for line in content.splitlines() if line.strip())
            print(f"  ✓ 履歴取得完了: {len(published)}件")
            return published

        except ClientError as e:
            # ファイルがまだない場合（初回など）は404エラーになるので無視して空セットを返す
            if e.response['Error']['Code'] == "NoSuchKey":
                print("  ℹ️ 履歴ファイルがありません。新規作成します。")
                return set()
            else:
                # その他のエラーは表示
                print(f"  ❌ 履歴取得エラー: {e}")
                raise e

    def _save_published(self, filename):
        """アップロード済みリストを更新してR2に保存"""
        # メモリ上のリストに追加
        self.published_list.add(filename)
        
        try:
            # リストを改行区切りの文字列に変換
            content = "\n".join(sorted(list(self.published_list)))
            
            # R2にアップロード（上書き保存）
            self.s3_client.put_object(
                Bucket=R2_CONFIG['bucket_name'],
                Key=self.remote_progress_file,
                Body=content.encode('utf-8'),
                ContentType='text/plain'
            )
            print(f"  💾 クラウド上の履歴を更新しました")
            
        except Exception as e:
            print(f"  ❌ 履歴保存エラー: {e}")
            # クリティカルではないが、次回重複する可能性があるので警告










    def authenticate_youtube(self):
        """YouTube API認証 (JSON対応版)"""
        import json
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow

        self.credentials = None
        # GitHub Actionsに合わせて json を優先
        token_file = "token.json"

        # 1. token.json (最新の形式) を探す
        if os.path.exists(token_file):
            try:
                self.credentials = Credentials.from_authorized_user_file(token_file, YOUTUBE_CONFIG['scopes'])
                print("✓ token.json を読み込みました")
            except ValueError:
                print("❌ token.json の形式が不正です")

        # 2. token.pickle (古い形式) があれば救済措置として読み込む
        elif os.path.exists("token.pickle"):
            import pickle
            print("⚠️ 古い token.pickle を検出しました")
            with open("token.pickle", "rb") as token:
                self.credentials = pickle.load(token)

        # 3. トークンの有効期限切れチェック & リフレッシュ
        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                print("🔄 トークンをリフレッシュします...")
                try:
                    self.credentials.refresh(Request())
                    # リフレッシュ成功したら json で保存し直す
                    with open(token_file, "w") as token:
                        token.write(self.credentials.to_json())
                    print("✓ 新しいトークンを token.json に保存しました")
                except Exception as e:
                    print(f"❌ リフレッシュ失敗: {e}")
                    self.credentials = None

        # 4. それでも認証できない場合
        if not self.credentials:
            # GitHub Actions環境かどうかを判定
            is_github_actions = os.environ.get('GITHUB_ACTIONS') == 'true'
            
            if is_github_actions:
                # クラウド上ではブラウザを開けないので、ここで終了させる
                print("❌ GitHub Actions環境で有効なトークンが見つかりません。")
                print("   Secretsの GOOGLE_TOKEN_JSON が正しいか確認してください。")
                sys.exit(1)
            
            # ローカル環境ならブラウザ認証を開始
            print("🔐 新規認証を開始します（ブラウザが起動します）...")
            flow = InstalledAppFlow.from_client_secrets_file(
                YOUTUBE_CONFIG["client_secrets_file"],
                YOUTUBE_CONFIG["scopes"]
            )
            # localhostで受け取る（新しい方式）
            self.credentials = flow.run_local_server(port=0)
            
            # 新しい json 形式で保存
            with open(token_file, "w") as token:
                token.write(self.credentials.to_json())
            print("✓ 認証情報を token.json に保存しました")

        self.youtube = googleapiclient.discovery.build(
            "youtube", "v3", credentials=self.credentials
        )
        print("✅ YouTube認証完了")









    def get_audio_files_from_r2(self):
        """R2から未処理の音声ファイル一覧取得"""
        print("📂 R2からファイル一覧取得中...")
        response = self.s3_client.list_objects_v2(Bucket=R2_CONFIG['bucket_name'])
        audio_files = []

        if 'Contents' in response:
            for obj in response['Contents']:
                key = obj['Key']
                # 音声ファイルかつ、履歴ファイル自体ではないものを対象にする
                if key.lower().endswith(('.m4a', '.mp3')):
                    
                    # ★ここで除外チェックを行う
                    if key in IGNORE_FILES:
                        print(f"  ℹ️ 除外リスト設定によりスキップ: {key}")
                        continue
                    
                    if key not in self.published_list:
                        audio_files.append(key)

        return sorted(audio_files)

    def download_audio_from_r2(self, key, local_path):
        """R2から音声ファイルダウンロード"""
        self.s3_client.download_file(R2_CONFIG['bucket_name'], key, local_path)
        print(f"  ✓ ダウンロード完了: {key}")

    def extract_title_from_filename(self, filename):
        """ファイル名からタイトル抽出（改良版）"""
        title = filename.rsplit('.', 1)[0]
        
        match = re.search(r'「(.+?)」', title)
        if match:
            return match.group(1).strip()
        
        title = re.sub(r'^\d{4,6}[-_]?', '', title)
        title = re.sub(r'^(語り|朗読|新規録音)\s*(　|#\d+)?', '', title)
        title = re.sub(r'(新規録音.*|#\d+.*|\(\d+\)|\(重複\)|【.*】)$', '', title)
        title = title.strip().replace('　', '')
        
        return title

    def generate_thumbnail(self, title, output_path):
        """サムネイル画像生成（自動サイズ調整付き）"""
        img = Image.open(THUMBNAIL_CONFIG['template_image']).convert('RGB')
        draw = ImageDraw.Draw(img)
        
        band_center_x = 640
        max_width = 760
        font_size = 90
        font_path = THUMBNAIL_CONFIG['font_path']
        
        try:
            font = ImageFont.truetype(font_path, font_size)
        except:
            font = ImageFont.load_default()
            max_width = 999999
        
        bbox = draw.textbbox((0, 0), title, font=font)
        text_width = bbox[2] - bbox[0]
        
        while text_width > max_width and font_size > 35:
            font_size -= 5
            try:
                font = ImageFont.truetype(font_path, font_size)
                bbox = draw.textbbox((0, 0), title, font=font)
                text_width = bbox[2] - bbox[0]
            except:
                break
        
        if font_size >= 85:
            band_center_y = 438
        elif font_size >= 75:
            band_center_y = 443
        elif font_size >= 65:
            band_center_y = 448
        elif font_size >= 55:
            band_center_y = 452
        else:
            band_center_y = 455
        
        text_height = bbox[3] - bbox[1]
        x = band_center_x - text_width / 2
        y = band_center_y - text_height / 2
        
        for offset_x in [-3, 0, 3]:
            for offset_y in [-3, 0, 3]:
                if offset_x != 0 or offset_y != 0:
                    draw.text((x + offset_x, y + offset_y), title, font=font, fill='black')
        
        draw.text((x, y), title, font=font, fill=THUMBNAIL_CONFIG['text_color'])
        img.save(output_path, quality=95)
        print(f"  ✓ サムネイル生成完了 (font: {font_size}px)")

    def convert_audio_to_video(self, audio_path, thumbnail_path, output_path):
        """音声ファイルを静止画付き動画に変換"""
        cmd = [
            'ffmpeg',
            '-loop', '1',
            '-i', thumbnail_path,
            '-i', audio_path,
            '-c:v', 'libx264',
            '-b:v', '1M',
            '-r', '1',
            '-af', 'volume=2.0',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-pix_fmt', 'yuv420p',
            '-shortest',
            '-y',
            output_path
        ]

        print(f"  🎬 動画変換中...")
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            print(f"  ✓ 動画変換完了")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ 動画変換エラー: {e}")
            print(f"  stderr: {e.stderr.decode()}")
            raise

    def create_description(self, title):
        """概要欄生成"""
        return DESCRIPTION_TEMPLATE.format(title=title)

    def calculate_publish_date(self, index):
        """公開日時計算"""
        start = datetime.strptime(UPLOAD_CONFIG['start_date'], "%Y-%m-%d")
        days_offset = index // UPLOAD_CONFIG['videos_per_day']
        publish_date = start + timedelta(days=days_offset)

        time_parts = UPLOAD_CONFIG['publish_time'].split(':')
        publish_date = publish_date.replace(
            hour=int(time_parts[0]),
            minute=int(time_parts[1]),
            second=int(time_parts[2])
        )

        return publish_date

    def upload_to_youtube(self, video_path, thumbnail_path, title, description, publish_date):
        """YouTubeにアップロード"""
        publish_at = publish_date.strftime("%Y-%m-%dT%H:%M:%S+09:00")

        body = {
            'snippet': {
                'title': f'昔話【{title}】',
                'description': description,
                'tags': YOUTUBE_CONFIG['tags'],
                'categoryId': YOUTUBE_CONFIG['category_id']
            },
            'status': {
                'privacyStatus': YOUTUBE_CONFIG['privacy_status'],
                'publishAt': publish_at,
                'selfDeclaredMadeForKids': False
            }
        }

        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

        try:
            print(f"  📤 YouTubeにアップロード中...")
            request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    print(f"  ... {progress}%", end='\r')

            video_id = response['id']
            print(f"\n  ✓ 動画アップロード完了: https://youtube.com/watch?v={video_id}")

            print(f"  🖼️ サムネイル設定中...")
            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()
            print(f"  ✓ サムネイル設定完了")

            return video_id

        except googleapiclient.errors.HttpError as e:
            print(f"  ❌ YouTubeエラー: {e}")
            return None

    def process_batch(self, limit=None):
        """バッチ処理実行"""
        audio_files = self.get_audio_files_from_r2()

        if limit:
            audio_files = audio_files[:limit]

        total = len(audio_files)
        print(f"\n📊 処理対象: {total}ファイル")
        print(f"📊 既に公開済み: {len(self.published_list)}ファイル")
        print("=" * 60)

        for index, audio_key in enumerate(audio_files):
            print(f"\n[{index + 1}/{total}] 処理中: {audio_key}")

            title = self.extract_title_from_filename(audio_key)

            with tempfile.TemporaryDirectory() as tmpdir:
                audio_path = os.path.join(tmpdir, audio_key)
                thumbnail_path = os.path.join(tmpdir, 'thumbnail.png')
                video_path = os.path.join(tmpdir, 'video.mp4')

                try:
                    self.download_audio_from_r2(audio_key, audio_path)
                    self.generate_thumbnail(title, thumbnail_path)
                    self.convert_audio_to_video(audio_path, thumbnail_path, video_path)
                    
                    description = self.create_description(title)
                    current_published_count = len(self.published_list)
                    publish_date = self.calculate_publish_date(current_published_count)

                    print(f"  📅 公開予定: {publish_date.strftime('%Y-%m-%d %H:%M')}")

                    video_id = self.upload_to_youtube(
                        video_path,
                        thumbnail_path,
                        title,
                        description,
                        publish_date
                    )

                    if video_id:
                        self._save_published(audio_key)
                        print(f"  ✅ 完了")
                    else:
                        print(f"  ❌ アップロード失敗")

                except Exception as e:
                    print(f"  ❌ エラー: {e}")
                    import traceback
                    traceback.print_exc()
                    continue

        print("\n" + "=" * 60)
        print(f"🎉 バッチ処理完了！")
        print(f"📊 今回処理: {total}ファイル")
        print(f"📊 累計公開: {len(self.published_list)}ファイル")


def main():
    """メイン処理"""
    # コマンドラインパラメータをパース
    parser = argparse.ArgumentParser(description='YouTube自動アップローダー')
    parser.add_argument('--limit', type=int, default=2, 
                       help='処理する動画数（デフォルト: 2）')
    parser.add_argument('--test', action='store_true',
                       help='テストモード（実際にはアップロードしない）')
    args = parser.parse_args()
    
    print("🎙️ YouTube自動アップローダー起動")
    print("=" * 60)
    
    # 環境検出
    is_github_actions = os.environ.get('GITHUB_ACTIONS') == 'true'
    if is_github_actions:
        print("🔧 GitHub Actions環境で実行中")
    else:
        print("💻 ローカル環境で実行中")
    
    print(f"📊 処理数: {args.limit}本")
    if args.test:
        print("⚠️ テストモード（アップロードしません）")
    
    print("=" * 60 + "\n")

    try:
        uploader = YouTubeUploader()
        uploader.authenticate_youtube()
        
        if args.test:
            print("🧪 テストモード: ファイル取得確認のみ")
            audio_files = uploader.get_audio_files_from_r2()
            if audio_files:
                print(f"\n✓ 処理対象ファイル一覧:")
                for i, f in enumerate(audio_files[:args.limit], 1):
                    print(f"  {i}. {f}")
            else:
                print("\n⚠️ 処理対象のファイルがありません")
        else:
            uploader.process_batch(limit=args.limit)
        
        print("\n✅ 処理完了")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ 致命的エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
