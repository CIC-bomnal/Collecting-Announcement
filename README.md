# 공고 수집 시스템

마감일 2주 이상 남은 공고를 나라장터와 K-Startup API에서 수집하여 Google Sheets에 증분 업데이트하는 시스템입니다.
GitHub Actions로 평일 매일 09:00(KST)에 자동 실행됩니다.

## 주요 기능

- **나라장터 + K-Startup** 공고 수집 (API)
- **키워드/마감일 필터링** (2주 이상 남은 공고만)
- **증분 업데이트**: 신규 공고는 추가, 기존 공고는 최종수정일시만 갱신
- **중복 제거**: 공고ID 기준 자동 중복 정리
- **K-Startup 부가정보**: 발주기관(형태소분석), 예산(웹 스크래핑) 자동 추출
- **GitHub Actions**: 평일 09:00 KST 자동 실행

## 사전 준비

### 1. Python 환경
```bash
python3 --version  # 3.8 이상
```

### 2. credentials.json 생성

Google Cloud Console에서 서비스 계정 키 발급:

1. https://console.cloud.google.com/ 접속
2. 프로젝트 생성
3. **Google Sheets API** + **Google Drive API** 활성화
4. **서비스 계정 생성** → 키 추가 → JSON 다운로드
5. 파일명을 `credentials.json`으로 변경 후 프로젝트 루트에 저장

### 3. 스프레드시트 공유

1. Google Sheets에서 대상 시트 열기
2. `credentials.json`의 `client_email`을 **편집자** 권한으로 공유

### 4. .env 파일 설정

`.env.example`을 참고하여 `.env` 파일 생성:

```bash
cp .env.example .env
# .env 파일에 실제 값 입력
```

## 로컬 실행

### 1. 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. 설정 확인
```bash
python3 -c "import config; config.validate_config()"
```

### 3. 실행
```bash
python3 main.py
```

### 실행 결과 예시
```
============================================================
✓ 공고 데이터 수집 완료!
  - 나라장터: 신규 3건, 갱신 16건
  - K-Startup: 신규 5건, 갱신 48건
  - 총 신규 8건, 갱신 64건
  - 소요 시간: 45.3초
============================================================
```

## GitHub Actions 자동 실행

### 필요한 Repository Secrets

| Secret | 설명 |
|--------|------|
| `NARA_API_KEY` | 나라장터 API 키 |
| `KSTARTUP_API_KEY` | K-Startup API 키 |
| `GOOGLE_SHEET_ID` | 스프레드시트 ID |
| `GOOGLE_CREDENTIALS_JSON` | credentials.json 전체 내용 |
| `KEYWORDS` | 키워드 (쉼표 구분) |

### 실행 스케줄
- **자동**: 평일(월~금) 09:00 KST
- **수동**: Actions 탭 → "공고 수집" → Run workflow

## 스프레드시트 구조

### 나라장터 탭 (8열)
| 공고명 | 공고ID | 발주기관 | 마감일 | 남은일수 | 예산 | 등록일시 | 최종수정일시 |

### K-Startup 탭 (10열)
| 공고명 | 공고ID | 발주기관 | 마감일 | 남은일수 | 예산 | 과업개요 | 요약 | 등록일시 | 최종수정일시 |

- 공고명은 클릭 가능한 하이퍼링크
- 남은일수는 `=마감일-TODAY()` 수식으로 자동 계산

## 프로젝트 구조

```
Collecting-Announcement/
├── main.py                    # 메인 실행
├── config.py                  # 설정 (.env 로드)
├── requirements.txt           # Python 패키지
├── .env                       # 환경변수 (git 미추적)
├── .env.example               # 환경변수 템플릿
├── credentials.json           # Google 서비스 계정 키 (git 미추적)
├── .github/
│   └── workflows/
│       └── collect.yml        # GitHub Actions 워크플로우
├── src/
│   ├── __init__.py
│   ├── api_client.py          # API 클라이언트 + 웹 스크래핑
│   ├── filter.py              # 키워드/마감일 필터링
│   ├── spreadsheet.py         # Google Sheets 연동 (증분 업데이트)
│   └── logger.py              # 로깅 설정
└── logs/                      # 로그 파일 (자동 생성, git 미추적)
```

## 문제 해결

### credentials.json 파일이 없습니다
```
✗ 환경변수 오류: Google 서비스 계정 키 파일이 존재하지 않습니다
```
→ credentials.json 파일 생성 후 프로젝트 루트에 저장

### 스프레드시트 인증 실패
→ credentials.json의 `client_email`을 스프레드시트에 편집자 권한으로 공유했는지 확인

### API 호출 실패
→ .env 파일의 API 키 확인 (NARA_API_KEY_DECODED, KSTARTUP_API_KEY_DECODED)
