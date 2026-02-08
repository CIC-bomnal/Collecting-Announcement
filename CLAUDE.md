# 공고 수집 시스템 — Claude Code 컨텍스트

## 프로젝트 목적
마감일 7일 이상 남은 공고를 나라장터·K-Startup API에서 수집하여 Google Sheets에 증분 업데이트.
GitHub Actions로 평일 09:00(KST) 자동 실행.

## 실행 플로우
```
1. 환경변수 검증 + 로거 초기화
2. [나라장터] API fetch (오늘~4개월 후) → 키워드 필터 → 마감일 7일 필터
3. [PDF] 안내서 파싱 → 509개 사업명 추출
4. [K-Startup] API fetch (전체) → 마감일 7일 필터 → (키워드 OR PDF 매칭) 합산
5. [금지어] 나라장터/K-Startup 각각 금지어 제외
6. [스프레드시트] 5개 탭 업데이트:
   ① 나라장터       ② K-Startup (PDF매칭 하이라이팅)
   ③ 2026 창업지원사업 (PDF 509개 사업)
   ④ 나라장터(필터)  ⑤ K-Startup(필터) (금지어 제외)
```

## 스프레드시트 탭 구조

### 나라장터 / 나라장터(필터) — 8열
공고명, 공고ID, 발주기관, 마감일, 남은일수, 예산, 등록일자, 업로드일자

### K-Startup / K-Startup(필터) — 8열
공고명, 공고ID, 발주기관, 마감일, 남은일수, 과업개요, 등록일자, 업로드일자
- PDF 매칭된 행: 연노랑 배경색 (rgb 255,255,204)

### 2026 창업지원사업 — 5열
사업명, 구분(주관), 구분(성격), 예정공고시기, 페이지

## 핵심 설정 (config.py)
- `MIN_DAYS_REMAINING`: 7 (마감일 최소 남은 일수)
- `MATCH_THRESHOLD`: 60 (rapidfuzz token_set_ratio 임계값)
- `KEYWORDS`: 쉼표 구분 키워드 22개
- `EXCLUSION_KEYWORDS`: 쉼표 구분 금지어 (육성기업 관점)

## 주요 기술 결정

### 나라장터 API 범위 최적화
- 기존: 1년 전체 (52주, 30분 초과)
- 현재: 오늘~4개월 후 (17주, 10분 이내)

### 증분 업데이트 방식
- 공고ID 기준으로 기존/신규 판별
- 기존 공고: 전체 필드 갱신 (등록일자만 기존 값 유지)
- 신규 공고: append
- 매 실행 전 deduplicate_sheet()로 ID 중복 제거

### PDF 매칭 (K-Startup)
- K-Startup API는 검색 파라미터 없음 → 전체 fetch 후 클라이언트 필터링
- rapidfuzz.fuzz.token_set_ratio: 토큰 분리 후 순서/공백 무시 유사도
- 60점 이상 → 매칭 (pdf_matched 플래그)
- 키워드 필터와 OR 합산

### PDF 파싱 (pdf_parser.py)
- 목차 p2~p17: 사업명 + 구분(주관/성격) + 페이지
- 상세 페이지: "사업공고" 라벨 → 예정공고시기
- 스마트 따옴표 (U+2019 → U+0027) 정규화 필요
- 509개 사업, 394개 날짜 추출 (69개는 비정형 텍스트)

### 금지어 필터링
- 원본 탭(나라장터, K-Startup)은 그대로 유지
- 금지어 제외한 결과를 별도 (필터) 탭에 업로드

## 파일 구조
```
main.py          — 메인 실행 (플로우 오케스트레이션)
config.py        — 환경변수, 헤더, 시트명 등 설정
src/api_client.py — NaraAPIClient, KStartupAPIClient
src/filter.py    — keyword, deadline, pdf_names, exclusion 필터
src/pdf_parser.py — PDF 목차/상세 파싱
src/spreadsheet.py — SpreadsheetManager (증분 업데이트, 하이라이팅)
src/logger.py    — 로깅 설정
```

## GitHub Actions
- 워크플로우: `.github/workflows/collect.yml`
- Secrets: NARA_API_KEY, KSTARTUP_API_KEY, GOOGLE_SHEET_ID, GOOGLE_CREDENTIALS_JSON, KEYWORDS, EXCLUSION_KEYWORDS
- GitHub Secrets는 저장 후 값 확인 불가 (write-only, 정상)
- .env 생성 시 sed로 앞공백 제거 필수

## 알려진 이슈
- PDF 날짜 추출: 509개 중 69개는 비정형 ("상시 모집", "프로그램별 상이" 등) → 빈칸 처리
- 나라장터 API: 주 단위 호출, 간헐적 타임아웃 시 재시도 3회
