import json
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# ファイル名
TOKEN_FILE = 'token.json'

def main():
    if not os.path.exists(TOKEN_FILE):
        print(f"❌ {TOKEN_FILE} が見つかりません。")
        return

    # 1. 期限切れのJSONを読み込む
    with open(TOKEN_FILE, 'r') as f:
        data = json.load(f)
    
    print(f"Old Expiry: {data.get('expiry')}")

    # 2. クレデンシャルオブジェクトを作成
    creds = Credentials.from_authorized_user_info(data)

    # 3. 強制的にリフレッシュ（Googleに問い合わせて新品にする）
    print("🔄 トークンをリフレッシュ中...")
    try:
        creds.refresh(Request())
        print("✅ リフレッシュ成功！")
    except Exception as e:
        print(f"❌ リフレッシュ失敗: {e}")
        print("インターネット接続を確認するか、client_secrets.jsonが正しいか確認してください。")
        return

    # 4. 新しい内容で上書き保存
    with open(TOKEN_FILE, 'w') as f:
        f.write(creds.to_json())
    
    print(f"💾 {TOKEN_FILE} を更新しました。")
    print(f"New Expiry: {json.loads(creds.to_json()).get('expiry')}")

if __name__ == '__main__':
    main()