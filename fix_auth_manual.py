with open('youtube_uploader.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
found = False

for i, line in enumerate(lines):
    if 'def authenticate_youtube(self):' in line and not found:
        new_lines.append(line)
        new_lines.append('        """YouTube API認証"""\n')
        new_lines.append('        import pickle\n')
        new_lines.append('        \n')
        new_lines.append('        credentials = None\n')
        new_lines.append('        \n')
        new_lines.append('        if os.path.exists("token.pickle"):\n')
        new_lines.append('            with open("token.pickle", "rb") as token:\n')
        new_lines.append('                credentials = pickle.load(token)\n')
        new_lines.append('            print("✓ 保存済み認証情報を使用")\n')
        new_lines.append('        \n')
        new_lines.append('        if not credentials or not credentials.valid:\n')
        new_lines.append('            if credentials and credentials.expired and credentials.refresh_token:\n')
        new_lines.append('                from google.auth.transport.requests import Request\n')
        new_lines.append('                credentials.refresh(Request())\n')
        new_lines.append('                print("✓ 認証情報を更新しました")\n')
        new_lines.append('            else:\n')
        new_lines.append('                flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(\n')
        new_lines.append('                    YOUTUBE_CONFIG["client_secrets_file"],\n')
        new_lines.append('                    YOUTUBE_CONFIG["scopes"]\n')
        new_lines.append('                )\n')
        new_lines.append('                flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"\n')
        new_lines.append('                auth_url, _ = flow.authorization_url(prompt="consent")\n')
        new_lines.append('                print(f"\\n1. このURLをブラウザで開いてください:")\n')
        new_lines.append('                print(f"{auth_url}\\n")\n')
        new_lines.append('                print("2. ログインして許可してください")\n')
        new_lines.append('                print("3. 表示された認証コードをコピーしてください")\n')
        new_lines.append('                code = input("\\n認証コード: ").strip()\n')
        new_lines.append('                flow.fetch_token(code=code)\n')
        new_lines.append('                credentials = flow.credentials\n')
        new_lines.append('                with open("token.pickle", "wb") as token:\n')
        new_lines.append('                    pickle.dump(credentials, token)\n')
        new_lines.append('                print("✓ 認証情報を保存しました")\n')
        new_lines.append('        \n')
        new_lines.append('        self.youtube = googleapiclient.discovery.build(\n')
        new_lines.append('            "youtube", "v3", credentials=credentials\n')
        new_lines.append('        )\n')
        new_lines.append('        print("✅ YouTube認証完了")\n')
        new_lines.append('\n')
        skip = True
        found = True
    elif skip:
        if line.strip().startswith('def ') and 'authenticate_youtube' not in line:
            skip = False
            new_lines.append(line)
    else:
        new_lines.append(line)

with open('youtube_uploader.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('OK')
