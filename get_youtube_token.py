# -*- coding: utf-8 -*-
"""
유튜브 클라우드 무인 업로드용 OAuth2 영구 토큰 발급기 (Get YouTube Refresh Token)
내 채널: 이심전심 이야기 (@MrKimjaesik)
PC가 꺼져 있어도 24시간 클라우드가 유튜브에 전체공개로 업로드할 수 있도록 1회성 영구 토큰을 발급받습니다.
"""

import os
import sys
import json

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def main():
    print("==================================================================")
    print("🔑 유튜브 클라우드 24/7 무인 업로드용 영구 토큰(Refresh Token) 발급기")
    print("📺 채널: 이심전심 이야기 (@MrKimjaesik)")
    print("==================================================================")
    print("PC가 꺼져 있어도 클라우드 서버가 내 채널에 '전체 공개'로 영상을 올리려면")
    print("Google Cloud Console에서 발급받은 클라이언트 정보가 필요합니다.\n")

    client_id = input("1. Google Client ID를 입력하세요: ").strip()
    client_secret = input("2. Google Client Secret을 입력하세요: ").strip()

    if not client_id or not client_secret:
        print("❌ Client ID와 Secret이 입력되지 않았습니다. 종료합니다.")
        return

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow

        SCOPES = [
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube"
        ]

        client_config = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }

        print("\n🌐 웹 브라우저가 열리면 채널 계정(@MrKimjaesik)으로 로그인하여 권한을 허용해 주세요...")
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")

        refresh_token = creds.refresh_token

        token_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token
        }

        # 로컬 토큰 파일 저장
        token_path = os.path.join(os.path.dirname(__file__), "youtube_token.json")
        with open(token_path, "w", encoding="utf-8") as f:
            json.dump(token_data, f, indent=2)

        print("\n==================================================================")
        print("🎉 영구 인증 토큰(Refresh Token) 발급 대성공!")
        print("==================================================================")
        print(f"📁 저장된 로컬 설정: {token_path}")
        print("\n🔑 클라우드(GitHub Secrets 등)에 등록할 3대 비밀키:")
        print(f"1. YT_CLIENT_ID:     {client_id}")
        print(f"2. YT_CLIENT_SECRET: {client_secret}")
        print(f"3. YT_REFRESH_TOKEN: {refresh_token}")
        print("------------------------------------------------------------------")
        print("이제 PC를 끄셔도 클라우드 서버가 위 키를 통해 24시간 내 채널에 자동 업로드합니다!")
        print("==================================================================")

    except Exception as e:
        print(f"\n❌ 인증 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
