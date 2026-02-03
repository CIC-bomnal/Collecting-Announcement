# 공고 수집 시스템 - Phase 1

2026-02-01 기준 마감일 2주 이상 남은 공고를 나라장터와 K-Startup API에서 수집하여 Google Sheets에 저장하는 시스템입니다.

## 사전 준비

### 1. Python 환경
```bash
python3 --version  # 3.8 이상 확인
```

### 2. credentials.json 생성 (필수!)

Google Cloud Console에서 서비스 계정 키 발급:

1. https://console.cloud.google.com/ 접속
2. 프로젝트 생성: "공고수집시스템"
3. **Google Sheets API 활성화**
   - API 및 서비스 → 라이브러리 → "Google Sheets API" 검색 → 활성화
4. **서비스 계정 생성** (⚠️ OAuth 클라이언트 ID가 아님!)
   - API 및 서비스 → 사용자 인증 정보 → "서비스 계정 만들기"
   - 서비스 계정 이름: `announcement-collector`
5. **키 추가 → JSON 선택 → 다운로드**
6. 다운로드한 파일을 `credentials.json`으로 이름 변경 후 이 디렉토리에 저장

### 3. 스프레드시트 공유

1. Google Sheets에서 대상 시트 열기
   - 스프레드시트 ID: `1VnDGOedtJVRtkcGvlAPEGp7RUmWXXY3KFFeO8ftwl2w`
   - URL: https://docs.google.com/spreadsheets/d/1VnDGOedtJVRtkcGvlAPEGp7RUmWXXY3KFFeO8ftwl2w
2. "공유" 버튼 클릭
3. `credentials.json`의 `client_email` 복사 (예: `announcement-collector@프로젝트ID.iam.gserviceaccount.com`)
4. 해당 이메일을 **편집자** 권한으로 공유

## 설치 및 실행

### 1. 패키지 설치
```bash
cd /Users/han-yeonji/개인pj/Collecting_announcement
pip install -r requirements.txt
```

### 2. 설정 확인
```bash
python3 -c "import config; config.validate_config()"
```

예상 출력:
```
✓ 환경변수 검증 완료
  - 나라장터 API 키: nSIGtAxP7Ypd8V9IZHRJ...
  - K-Startup API 키: nSIGtAxP7Ypd8V9IZHRJ...
  - 스프레드시트 ID: 1VnDGOedtJVRtkcGvlAPEGp7RUmWXXY3KFFeO8ftwl2w
  - 키워드 개수: 18개
  - 최소 남은 일수: 14일
  - Phase 1 기준일: 2026-02-01
```

### 3. 프로그램 실행
```bash
python3 main.py
```

## 실행 결과 확인

### 1. 콘솔 출력
```
============================================================
공고 수집 시스템 - Phase 1: 초기 데이터 수집
============================================================

✓ 환경변수 검증 완료
...

============================================================
✓ Phase 1 초기 데이터 수집 완료!
  - 나라장터: 15건
  - K-Startup: 8건
  - 총 23건 추가
  - 소요 시간: 45.3초
============================================================

스프레드시트 확인: https://docs.google.com/spreadsheets/d/1VnDGOedtJVRtkcGvlAPEGp7RUmWXXY3KFFeO8ftwl2w
```

### 2. 스프레드시트 확인

브라우저에서 스프레드시트를 열어 확인:
- ✅ "나라장터" 탭 존재
- ✅ "K-Startup" 탭 존재
- ✅ 공고명이 클릭 가능한 링크로 표시
- ✅ 남은일수가 자동으로 계산됨 (=D2-TODAY())
- ✅ 마감일이 2026-02-15 이후인 공고만 있음

### 3. 로그 파일
```bash
cat logs/공고수집_20260201.log
```

## 문제 해결

### credentials.json 파일이 없습니다
```
✗ 환경변수 오류: Google 서비스 계정 키 파일이 존재하지 않습니다: ./credentials.json
```
→ credentials.json 파일을 생성하고 올바른 위치에 저장했는지 확인

### 스프레드시트 인증 실패
```
✗ 스프레드시트 인증 실패: ...
```
→ credentials.json의 `client_email`을 스프레드시트에 편집자 권한으로 공유했는지 확인

### API 호출 실패
```
✗ 나라장터 API 요청 실패: ...
```
→ .env 파일의 API 키가 올바른지 확인 (NARA_API_KEY_DECODED, KSTARTUP_API_KEY_DECODED 사용)

## 프로젝트 구조

```
Collecting_announcement/
├── main.py                   # 메인 실행 파일
├── config.py                 # 설정 관리
├── requirements.txt          # Python 패키지
├── credentials.json          # Google 서비스 계정 키 (직접 생성 필요)
├── src/
│   ├── __init__.py
│   ├── api_client.py         # API 클라이언트
│   ├── filter.py             # 필터링 로직
│   ├── spreadsheet.py        # Google Sheets 연동
│   └── logger.py             # 로깅 설정
└── logs/                     # 로그 파일 (자동 생성)
    └── 공고수집_YYYYMMDD.log
```

## 다음 단계 (Phase 2)

Phase 1 완료 후 Phase 2 (일일 자동 업데이트) 구현 필요:
- 중복 처리 로직 (공고ID 기준으로 업데이트)
- 동적 기준일 (실행 당일)
- Apps Script 또는 crontab으로 자동화
