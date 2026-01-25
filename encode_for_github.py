#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Secretsに登録するため、認証情報をBase64エンコードするヘルパースクリプト
このスクリプトは、ローカル環境でのセットアップ時に使用します
"""

import base64
import sys
from pathlib import Path


def encode_file_to_base64(file_path):
    """ファイルをBase64エンコード"""
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        return base64.b64encode(content).decode('utf-8')
    except FileNotFoundError:
        print(f"❌ ファイルが見つかりません: {file_path}")
        return None
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None


def main():
    print("🔐 GitHub Secrets用 認証情報エンコード")
    print("=" * 70)
    
    # client_secrets.json をエンコード
    print("\n1️⃣ client_secrets.json のエンコード")
    print("-" * 70)
    
    secrets_base64 = encode_file_to_base64('client_secrets.json')
    if secrets_base64:
        print("✓ 以下をGitHub Secret 'GOOGLE_SECRETS_BASE64' に登録してください:\n")
        print(secrets_base64)
        print("\n")
    else:
        print("⚠️ client_secrets.json が見つかりません")
        print("  ローカルで認証を完了してから実行してください\n")
        return False
    
    # token.pickle をエンコード
    print("2️⃣ token.pickle のエンコード")
    print("-" * 70)
    
    token_base64 = encode_file_to_base64('token.pickle')
    if token_base64:
        print("✓ 以下をGitHub Secret 'GOOGLE_TOKEN_BASE64' に登録してください:\n")
        print(token_base64)
        print("\n")
    else:
        print("⚠️ token.pickle が見つかりません")
        print("  ローカルで認証を完了してから実行してください\n")
        return False
    
    # R2設定
    print("3️⃣ Cloudflare R2 設定")
    print("-" * 70)
    print("以下の情報をGitHub Secretsに登録してください:\n")
    print("| 名前                  | 値                    |")
    print("|---|---|")
    print("| R2_ACCOUNT_ID         | (R2ダッシュボードから確認) |")
    print("| R2_ACCESS_KEY_ID      | (R2認証情報から確認)    |")
    print("| R2_SECRET_ACCESS_KEY  | (R2認証情報から確認)    |")
    print("| R2_BUCKET_NAME        | mukashimukashi-audio  |")
    print("| R2_ENDPOINT_URL       | https://[ACCOUNT_ID].r2.cloudflarestorage.com |")
    
    print("\n" + "=" * 70)
    print("✅ エンコード完了")
    print("\n📝 登録方法:")
    print("1. GitHub リポジトリ設定を開く")
    print("2. Settings → Secrets and variables → Actions")
    print("3. New repository secret をクリック")
    print("4. 上記の値をコピー＆ペーストして登録\n")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
