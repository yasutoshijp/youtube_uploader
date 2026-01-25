#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions環境で認証情報を復元するスクリプト
Base64エンコードされたシークレットを複号化して、必要なファイルを再構築します
"""

import os
import base64
import sys
from pathlib import Path

def restore_google_secrets():
    """Google認証情報を復元"""
    google_secrets_base64 = os.environ.get('GOOGLE_SECRETS_BASE64')
    google_token_base64 = os.environ.get('GOOGLE_TOKEN_BASE64')
    
    success = True
    
    # client_secrets.json の復元
    if google_secrets_base64:
        try:
            secrets_bytes = base64.b64decode(google_secrets_base64)
            with open('client_secrets.json', 'wb') as f:
                f.write(secrets_bytes)
            print("✓ client_secrets.json を復元しました")
        except Exception as e:
            print(f"❌ client_secrets.json の復元に失敗: {e}")
            success = False
    else:
        print("⚠️ GOOGLE_SECRETS_BASE64 が設定されていません")
        success = False
    
    # token.pickle の復元
    if google_token_base64:
        try:
            token_bytes = base64.b64decode(google_token_base64)
            with open('token.pickle', 'wb') as f:
                f.write(token_bytes)
            print("✓ token.pickle を復元しました")
        except Exception as e:
            print(f"❌ token.pickle の復元に失敗: {e}")
            success = False
    else:
        print("⚠️ GOOGLE_TOKEN_BASE64 が設定されていません")
        success = False
    
    return success

def main():
    print("🔐 GitHub Actions環境で認証情報を復元中...")
    print("=" * 60)
    
    if not restore_google_secrets():
        print("\n❌ 認証情報の復元に失敗しました")
        print("GitHub Secretsを正しく設定してください")
        sys.exit(1)
    
    print("\n✅ 認証情報の復元完了")

if __name__ == "__main__":
    main()
