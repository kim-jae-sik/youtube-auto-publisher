# ☁️ PC가 꺼져 있어도 24시간 무인 작동하는 유튜브 롱폼 자동 발행 시스템 가이드

> **대상 채널**: [이심전심 이야기 (@MrKimjaesik)](https://www.youtube.com/@MrKimjaesik)  
> **영상 규격**: 10분 이상 (10m 20s+), 16:9 와이드스크린 (1080p), 한국어 나눔고딕 자막/슬라이드, 앰비언트 BGM  
> **공개 범위**: 전체 공개 (`public`)  
> **운영 방식**: PC 전원 OFF 상태에서도 100% 클라우드(GitHub Actions)에서 자율 기획·렌더링·업로드

---

## 📌 왜 PC가 꺼져 있으면 클라우드가 필요한가요?

컴퓨터의 전원을 끄면 로컬 CPU와 메모리가 완전히 정지하므로 PC 내부의 파이썬 스크립트나 윈도우 작업 스케줄러가 작동할 수 없습니다.  
따라서 **마이크로소프트와 깃허브가 제공하는 24시간 가상 클라우드 서버(GitHub Actions Runner)**를 활용하여, **내 PC는 꺼져 있어도 클라우드 컴퓨터가 알아서 10분 풀영상을 렌더링하고 내 유튜브 채널로 자동 전송**하도록 설계되었습니다.

---

## ⚠️ 유튜브 API 쿼터 및 발행 주기 핵심 주의사항

- **구글 공식 유튜브 Data API v3 기본 일일 무료 쿼터**: `10,000 유닛 / 1일`
- **동영상 1회 업로드 소모 쿼터**: `1,600 유닛`
- **일일 최대 업로드 가능 수량**: **하루 최대 6편** (`10,000 ÷ 1,600 = 6.25회`)
- 🚨 **주의**: 만약 '1시간마다(하루 24편)' 업로드를 시도하면, 6번째 영상 이후 구글에서 `quotaExceeded` 에러로 당일 업로드가 차단되며, 신생 채널의 경우 유튜브 알고리즘에서 스팸 채널로 분류될 위험이 있습니다.
- ✅ **최적 권장 주기**:
  - **4시간마다 1회 (하루 6편)**: 무료 일일 쿼터를 100% 한계치까지 알뜰하게 활용하는 최적 주기 (한국 시간 기준 09시, 13시, 17시, 21시, 01시, 05시)
  - **6시간마다 1회 (하루 4편)**: 채널 신뢰도와 알고리즘 노출을 안정적으로 유지하는 추천 주기

---

## 🛠️ 1회성 3분 세팅 가이드 (처음 한 번만 해주시면 끝!)

### 1단계: Google Cloud Console에서 YouTube API 활성화 (무료)
1. [Google Cloud Console](https://console.cloud.google.com/) 접속 및 로그인
2. 새 프로젝트 생성 (예: `YouTube-Auto-Publisher`)
3. **[API 및 서비스]** -> **[라이브러리]** -> **`YouTube Data API v3`** 검색 후 **[사용 설정]** 클릭
4. **[OAuth 동의 화면]** 이동:
   - User Type: **외부(External)** 선택
   - 앱 이름, 이메일 입력 후 저장
   - **테스트 사용자(Test users)**에 본인 유튜브 계정 이메일(`@MrKimjaesik` 소유 구글 계정) 추가
5. **[사용자 인증 정보]** -> **[+ 사용자 인증 정보 만들기]** -> **[OAuth 클라이언트 ID]**:
   - 애플리케이션 유형: **데스크톱 앱(Desktop App)**
   - 생성 완료 후 표시되는 **클라이언트 ID**와 **클라이언트 보안 비밀(Secret)**을 복사

---

### 2단계: 로컬에서 영구 토큰(Refresh Token) 발급받기
터미널에서 아래 명령을 1회 실행합니다:
```bash
python get_youtube_token.py
```
1. 복사해 둔 Client ID와 Client Secret을 입력합니다.
2. 브라우저가 열리면 채널 소유 구글 계정으로 로그인 후 **[허용]** 버튼을 누릅니다.
3. 화면에 출력되는 **`YT_REFRESH_TOKEN`** 값을 확인합니다.

---

### 3단계: GitHub에 비공개(Private) 저장소 생성 및 푸시
1. [GitHub](https://github.com/)에서 새 저장소를 **Private(비공개)**로 만듭니다 (예: `my-youtube-auto-engine`).
2. 로컬 터미널에서 저장소에 푸시합니다:
```bash
git remote add origin https://github.com/당신의깃허브아이디/my-youtube-auto-engine.git
git branch -M main
git push -u origin main
```

---

### 4단계: GitHub Secrets에 3대 비밀키 등록
1. 깃허브 저장소 페이지의 **[Settings]** -> **[Secrets and variables]** -> **[Actions]** 클릭
2. **[New repository secret]** 버튼을 눌러 다음 3개를 등록합니다:
   - `YT_CLIENT_ID`: 1단계에서 얻은 클라이언트 ID
   - `YT_CLIENT_SECRET`: 1단계에서 얻은 클라이언트 보안 비밀
   - `YT_REFRESH_TOKEN`: 2단계에서 얻은 리프레시 토큰

---

## 🚀 이제 모든 준비가 끝났습니다!

- **자동 실행**: 이제 **PC를 완전히 끄셔도**, 설정된 주기마다 깃허브 클라우드가 자동으로 새 주제를 선정하여 10분 이상의 영상을 렌더링하고, 16:9 썸네일과 제목/태그를 첨부하여 유튜브 채널에 **전체 공개(`public`)**로 업로드합니다.
- **수동 즉시 실행**: GitHub 저장소의 **[Actions]** 탭 -> **[24/7 Autonomous YouTube Long-form Publisher]** 클릭 -> **[Run workflow]** 버튼을 누르면 지금 당장 클라우드가 1편을 제작하여 업로드합니다.
- **제작 영상 확인**: 업로드된 영상은 [이심전심 이야기 채널](https://www.youtube.com/@MrKimjaesik)에서 즉시 확인하실 수 있습니다.
