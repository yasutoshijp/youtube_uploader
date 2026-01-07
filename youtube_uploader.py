#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube自動アップローダー - ひさこばあばのむかしむかし
"""

import os
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import re
import boto3
from PIL import Image, ImageDraw, ImageFont
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload

# ========================================
# 設定
# ========================================

# Cloudflare R2設定
R2_CONFIG = {
    'account_id': '9122fb0f2c086a09610f7e86a874f232',
    'access_key_id': 'fafa4cfb6ea0938c8300cdba723bb790',
    'secret_access_key': 'f816a46eba22879ad19c1d544e794a05572a8a220251417a6e54cc7d279dca14',
    'bucket_name': 'mukashimukashi-audio',
    'endpoint_url': 'https://9122fb0f2c086a09610f7e86a874f232.r2.cloudflarestorage.com'
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

# 進捗管理ファイル
PROGRESS_FILE = 'youtube_published.txt'


class YouTubeUploader:
    def __init__(self):
        """初期化"""
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
        """アップロード済みリスト読み込み"""
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return set(line.strip() for line in f)
        return set()

    def _save_published(self, filename):
        """アップロード済みリストに追加"""
        with open(PROGRESS_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{filename}\n")
        self.published_list.add(filename)

    def authenticate_youtube(self):
        """YouTube API認証"""
        import pickle
        
        credentials = None
        
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                credentials = pickle.load(token)
            print("✓ 保存済み認証情報を使用")
        
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                from google.auth.transport.requests import Request
                credentials.refresh(Request())
                print("✓ 認証情報を更新しました")
            else:
                flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                    YOUTUBE_CONFIG["client_secrets_file"],
                    YOUTUBE_CONFIG["scopes"]
                )
                flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
                auth_url, _ = flow.authorization_url(prompt="consent")
                print(f"\n1. このURLをブラウザで開いてください:")
                print(f"{auth_url}\n")
                print("2. ログインして許可してください")
                print("3. 表示された認証コードをコピーしてください")
                code = input("\n認証コード: ").strip()
                flow.fetch_token(code=code)
                credentials = flow.credentials
                with open("token.pickle", "wb") as token:
                    pickle.dump(credentials, token)
                print("✓ 認証情報を保存しました")
        
        self.youtube = googleapiclient.discovery.build(
            "youtube", "v3", credentials=credentials
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
                if key.lower().endswith(('.m4a', '.mp3')):
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
    print("🎙️ YouTube自動アップローダー起動")
    print("=" * 60)

    uploader = YouTubeUploader()
    uploader.authenticate_youtube()

    print("\n📊 本番実行: 1日2本処理します")
    uploader.process_batch(limit=2)


if __name__ == "__main__":
    main()
