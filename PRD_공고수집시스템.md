# PRD: 공공 공고 자동 수집 및 관리 시스템

## 문서 정보
- **작성일**: 2026-01-31
- **최종 수정일**: 2026-01-31
- **버전**: 1.4
- **작성자**: Claude Code
- **기준일**: 2026-02-01

---

## 1. 프로젝트 개요

### 1.1 목적
나라장터와 창업진흥원 K-Startup의 공고 정보를 자동으로 수집하여, 특정 키워드가 포함된 마감일이 충분히 남은 공고를 구글 스프레드시트에 자동으로 업데이트하는 시스템 개발

### 1.2 배경
- 매일 올라오는 다양한 공고를 수동으로 확인하는 것은 비효율적
- 마감일이 촉박한 공고는 준비 시간 부족으로 지원이 어려움
- 관심 키워드에 맞는 공고만 필터링하여 효율적으로 관리 필요

### 1.3 실행 단계
이 시스템은 두 단계로 운영됩니다:

**Phase 1: 초기 데이터 수집 (최초 1회)**
- 2026년 2월 1일 기준으로 마감일이 2주 이상 남은 모든 공고 수집
- 필터링된 공고를 스프레드시트에 초기 리스트로 작성

**Phase 2: 일일 업데이트 (매일 자동 실행)**
- 매일 실행 시점(당일) 기준으로 마감일이 2주 이상 남은 공고 검색
- 신규 공고는 추가, 기존 공고는 정보 업데이트

### 1.4 핵심 가치
- 자동화를 통한 시간 절약
- 마감일 2주 전 공고만 필터링하여 충분한 준비 시간 확보
- 구글 스프레드시트를 통한 쉬운 접근성 및 협업 가능

---

## 2. 요구사항

### 2.1 기능 요구사항 (Functional Requirements)

#### FR-1: 공고 데이터 수집
- **FR-1.1**: 나라장터 API를 통해 2026년에 등록된 공고 수집
- **FR-1.2**: K-Startup API를 통해 2026년에 등록된 공고 수집
- **FR-1.3**: 각 API로부터 다음 정보를 추출:
  - 필수: 공고명, 발주기관(주최기관), 제출 일자(마감일), 공고 링크, 예산
  - 선택 (가능한 경우): 과업 내용, 사업 목적

#### FR-2: 키워드 필터링
- **FR-2.1**: 공고 제목에 다음 키워드 중 **하나 이상**이 포함된 경우 필터링:
  ```
  스타트업, 창업, 액셀러레이팅, 창업기획자, 벤처, 소상공인, 육성,
  액셀러레이터, 엑셀러레이터, 엑셀러레이팅, 투자, START-UP, 사업화,
  유니콘, 소셜, 임팩트, 사회문제, 활성화, 주관기관, 주관사, 운영사, 운영기업
  ```
- **FR-2.2**: 대소문자 구분 없이 검색 (예: "Start-up", "START-UP", "start-up" 모두 매칭)
- **FR-2.3**: 키워드는 `.env` 파일에서 쉼표로 구분된 문자열로 관리

#### FR-3: 마감일 필터링
- **FR-3.1**: 기준일 정의:
  - **초기 실행 (Phase 1)**: 2026년 2월 1일 고정
  - **일일 업데이트 (Phase 2)**: 프로그램 실행 당일 (동적)
- **FR-3.2**: 마감일이 기준일로부터 **14일(2주) 이상** 남은 공고만 선택
- **FR-3.3**: 마감일 계산 로직:
  ```
  남은 일수 = 마감일 - 기준일
  조건: 남은 일수 >= 14

  예시 (일일 업데이트):
  - 실행일: 2026-02-10
  - 공고 마감일: 2026-02-25
  - 남은 일수: 15일 → 조건 충족 (선택)
  ```
- **FR-3.4**: 마감일이 명시되지 않은 공고는 **제외**

#### FR-4: 구글 스프레드시트 업로드
- **FR-4.1**: 구글 스프레드시트 구조:

  **시트 구성:**
  - 나라장터와 K-Startup 공고를 **별도 탭으로 분리**
  - 탭 이름: `"나라장터"`, `"K-Startup"`

  **컬럼 구조 (양쪽 탭 동일):**
  | 컬럼명 | 데이터 타입 | 설명 | 필수여부 |
  |--------|------------|------|----------|
  | 공고명 | 문자열 (하이퍼링크) | 공고 제목 + 원본 링크 (셀에 하이퍼링크로 삽입) | 필수 |
  | 공고ID | 문자열 | 고유 식별자 (API 제공 또는 생성) | 필수 |
  | 발주기관 | 문자열 | 주최/발주 기관명 | 필수 |
  | 마감일 | 날짜 (YYYY-MM-DD) | 제출 마감일 | 필수 |
  | 남은일수 | 수식 (자동계산) | `=마감일 - TODAY()` 스프레드시트 함수로 자동 계산 | 필수 |
  | 예산 | 문자열 | 예산 규모 (원 단위 또는 텍스트) | 필수 |
  | 과업개요 | 문자열 | 개조식으로 정리된 과업 내용 | 선택 |
  | 요약 | 문자열 | 공고의 핵심 내용 요약 | 선택 |
  | 등록일시 | 날짜시간 | 스프레드시트에 추가된 시각 | 필수 |
  | 최종수정일시 | 날짜시간 | 마지막으로 업데이트된 시각 | 필수 |

  **컬럼 상세:**
  - **공고명**: 하이퍼링크 형식으로 저장. 텍스트는 공고 제목, URL은 원본 공고 링크
    - 예: `=HYPERLINK("https://example.com/notice/123", "2026년 스타트업 지원사업")`
  - **남은일수**: 스프레드시트 수식으로 자동 계산되므로 프로그램에서 값을 넣지 않음
    - 수식: `=D2-TODAY()` (D열이 마감일인 경우)
    - 매일 자동으로 재계산되어 최신 상태 유지

- **FR-4.2**: 첫 실행 시 각 탭에 위 컬럼으로 헤더 행 자동 생성
- **FR-4.3**: 데이터는 헤더 다음 행부터 순차적으로 추가
- **FR-4.4**: 나라장터 공고는 "나라장터" 탭에, K-Startup 공고는 "K-Startup" 탭에만 기록

#### FR-5: 중복 처리 및 업데이트
- **FR-5.1**: 중복 판단 기준: `공고ID` 컬럼으로 식별 (각 탭 내에서)
- **FR-5.2**: 중복 공고 발견 시:
  - 기존 행의 데이터를 최신 정보로 **업데이트**
  - `최종수정일시` 필드 갱신
  - `남은일수`는 스프레드시트 수식이 자동으로 계산하므로 프로그램에서 처리 불필요
- **FR-5.3**: 신규 공고인 경우:
  - 새로운 행으로 추가
  - `등록일시`와 `최종수정일시`를 현재 시각으로 설정
  - `남은일수` 컬럼에는 수식 `=D[행번호]-TODAY()` 자동 삽입

#### FR-6: 자동 업데이트

**기본 요구사항:**
- **FR-6.1**: 실행 모드:
  - **Phase 1 (초기 실행)**: 최초 1회 수동 실행, 2026-02-01 기준
  - **Phase 2 (일일 업데이트)**: 매일 1회 자동 실행, 실행 당일 기준
- **FR-6.2**: 권장 실행 시간: 오전 9시 (변경 가능)

### FR-6 최종 결정 (Apps Script)

- **FR-6.3**: Google Apps Script 사용
  - 스프레드시트 메뉴: 확장 프로그램 → Apps Script
  - **Phase 1**: 최초 실행 시 `INITIAL_BASE_DATE = '2026-02-01'` 사용
  - **Phase 2**: Time-driven trigger 설정하여 매일 오전 9시 자동 실행
  - 스크립트는 스프레드시트에 저장되어 팀 전체 공유
  - 실행 프로세스:
    1. 두 API에서 공고 수집
    2. 키워드 필터링
    3. 마감일 필터링 (Phase 1: 2026-02-01 기준, Phase 2: 실행 당일 기준, 14일 이상)
    4. 스프레드시트 업데이트 (신규 추가/기존 업데이트)

- **FR-6.4**: Apps Script 구조
  - `main(isInitialRun)`: 전체 프로세스 실행 함수
    - `isInitialRun = true`: Phase 1, 기준일 2026-02-01
    - `isInitialRun = false`: Phase 2, 기준일 실행 당일
  - `fetchNaraAPI()`: 나라장터 API 호출
  - `fetchKStartupAPI()`: K-Startup API 호출
  - `filterByKeyword()`: 키워드 필터링
  - `filterByDeadline(baseDate)`: 마감일 필터링 (baseDate 기준 14일 이상)
  - `updateSheet()`: 스프레드시트 업데이트

#### FR-7: 과업 개조식 정리 및 한 줄 요약 (선택 기능)
- **FR-7.1**: API에서 과업 내용 또는 사업 설명 필드를 추출
- **FR-7.2**: 과업 개조식 정리:
  - HTML 태그 제거
  - 줄바꿈 기준으로 분리
  - 불렛 포인트(•) 또는 번호로 정리
  - 최대 5개 항목까지만 추출
- **FR-7.3**: 한 줄 요약:
  - 공고명과 과업 내용을 기반으로 1문장 요약
  - 최대 100자 이내
  - OpenAI API 또는 로컬 LLM 사용 고려 (선택사항)
  - API 사용이 어려운 경우, 공고명과 첫 문장을 조합하여 간단히 생성

### 2.2 비기능 요구사항 (Non-Functional Requirements)

#### NFR-1: 성능
- API 호출은 각 플랫폼당 5초 이내에 완료되어야 함
- 전체 프로세스는 1분 이내에 완료되어야 함
- 대용량 데이터(1000건 이상)도 처리 가능해야 함

#### NFR-2: 안정성
- API 호출 실패 시 최대 3회 재시도
- 재시도 간격: 5초
- 하나의 API 실패가 전체 프로세스를 중단시키지 않음

#### NFR-3: 보안
- API 키 및 인증 정보는 `.env` 파일에 저장
- `.env` 파일은 `.gitignore`에 포함
- `.env.example` 파일로 필요한 키 목록 제공

#### NFR-4: 유지보수성
- 모든 설정값(키워드, API URL 등)은 외부 파일로 관리
- 코드는 함수/클래스 단위로 모듈화
- 주요 함수에 docstring 작성

#### NFR-5: 로깅 및 모니터링
- 모든 실행은 로그 파일에 기록
- 로그 레벨: INFO, WARNING, ERROR
- 로그 파일: `logs/공고수집_YYYYMMDD.log`
- 로그 보관 기간: 30일

---

## 3. API 명세

### 3.1 나라장터 API

#### 3.1.1 API 정보
- **API 이름**: 나라장터 공공데이터개방표준서비스
- **API ID**: `PubDataOpnStdService`
- **Base URL**: `https://apis.data.go.kr/1230000/ao/PubDataOpnStdService`
- **인증 방식**: ServiceKey 기반
- **필요한 환경변수**: `NARA_API_KEY` (인코딩 또는 디코딩 버전)
- **데이터 형식**: XML / JSON
- **데이터 갱신주기**: 수시

#### 3.1.2 주요 엔드포인트
```
GET /getDataSetOpnStdBidPblancInfo
```
**설명**: 데이터셋 개방표준에 따른 입찰공고정보 조회

#### 3.1.3 요청 파라미터
| 파라미터 | 필수 | 타입 | 샘플 데이터 | 설명 |
|---------|------|------|------------|------|
| ServiceKey | Y | String(400) | (인증키) | 공공데이터포털에서 발급받은 인증키 |
| numOfRows | N | Integer(4) | 10 | 한 페이지 결과 수 |
| pageNo | N | Integer(4) | 1 | 페이지 번호 |
| type | N | String(4) | json | 오픈API 리턴 타입 ('json' 또는 생략 시 XML) |
| bidNtceBgnDt | N | String(12) | 202601010000 | 입찰공고 시작일시 (YYYYMMDDHHMM, 1개월 범위 제한) |
| bidNtceEndDt | N | String(12) | 202601312359 | 입찰공고 종료일시 (YYYYMMDDHHMM, 1개월 범위 제한) |

**조회 제한:** 입찰공고일시 범위는 최대 1개월로 제한됨

#### 3.1.4 응답 필드 매핑

| 스프레드시트 컬럼 | API 응답 필드 | 필드 설명 | 데이터 형식 |
|------------------|--------------|----------|------------|
| 공고ID | `bidNtceNo` | 입찰공고번호 | String(13) |
| 공고명 | `bidNtceNm` | 입찰공고명 | String(1000) |
| 발주기관 | `dmndInsttNm` | 수요기관명 | String(200) |
| 마감일 | `bidClseDate` | 입찰마감일자 | YYYY-MM-DD |
| 예산 | `asignBdgtAmt` 또는 `presmptPrce` | 배정예산금액 또는 추정가격 | Integer(원) |
| 공고링크 | `bidNtceUrl` | 입찰공고 상세 URL | URL(전체 경로 제공) |

**추가 유용 필드:**
- `bidNtceNo`: R25BK00933743 (차세대 번호체계: R+년도2자리+BK+순번8자리)
- `bidNtceOrd`: 입찰공고차수 (000~999, 정정공고 시 증가)
- `bidNtceDate`: 입찰공고일자 (YYYY-MM-DD)
- `bidNtceBgn`: 입찰공고시각 (HH:MM)
- `bsnsDivNm`: 업무구분명 (물품/용역/공사/외자)
- `bidBeginDate` / `bidBeginTm`: 입찰시작 일시
- `opengDate` / `opengTm`: 개찰 일시
- `cntrctCnclsMthdNm`: 계약체결방법명 (일반경쟁/제한경쟁/지명경쟁/수의계약)
- `rsrvtnPrce`: 예정가격 (원)

### 3.2 K-Startup API

#### 3.2.1 API 정보
- **API 이름**: 창업진흥원_K-Startup(사업소개,사업공고, 콘텐츠 등)_조회서비스
- **API ID**: `kisedKstartupService01`
- **Base URL**: `https://apis.data.go.kr/B552735/kisedKstartupService01`
- **END POINT URL**: `https://nidapi.k-startup.go.kr/api/kisedKstartupService/v1/`
- **인증 방식**: ServiceKey 기반
- **필요한 환경변수**: `KSTARTUP_API_KEY` (인코딩 또는 디코딩 버전)
- **데이터 형식**: XML / JSON (기본값: JSON)
- **데이터 갱신주기**: 일 1회

#### 3.2.2 주요 엔드포인트
```
GET /getAnnouncementInformation01
```
**설명**: 지원사업 공고정보 조회 (공고명, 공고기간, 지원대상, 지원내용, 지원방법 등)

#### 3.2.3 요청 파라미터
| 파라미터 | 필수 | 타입 | 샘플 데이터 | 설명 |
|---------|------|------|------------|------|
| ServiceKey | Y | String(100) | (인증키) | 공공데이터포털에서 발급받은 인증키 (URL Encode) |
| page | N | Integer(100) | 1 | 페이지 |
| perPage | N | Integer(100) | 10 | 한 페이지 결과 수 |
| returnType | N | String(50) | json | 반환타입 (json/XML, 기본값: json) |
| intg_pbanc_yn | N | String(1) | N | 통합 공고 여부 (Y/N) |
| intg_pbanc_biz_nm | N | String(300) | | 통합 공고 사업명 |
| biz_pbanc_nm | N | String(300) | 창업보육센터 입주기업 수출상담회 | 지원 사업 공고명 |
| supt_biz_clsfc | N | String(50) | 행사·네트워크 | 지원 분야 |
| supt_regin | N | String(200) | 서울특별시 | 지역명 |
| pbanc_rcpt_bgng_dt | N | String(8) | 20121129 | 공고 접수 시작 일시 (YYYYMMDD) |
| pbanc_rcpt_end_dt | N | String(8) | 20121221 | 공고 접수 종료 일시 (YYYYMMDD) |
| Rcrt_prgs_yn | N | String(1) | Y | 모집진행여부 (Y/N) |

#### 3.2.4 응답 필드 매핑

| 스프레드시트 컬럼 | API 응답 필드 | 필드 설명 | 데이터 형식 |
|------------------|--------------|----------|------------|
| 공고ID | `detl_pg_url`에서 추출 | 상세 URL의 `pbancSn` 파라미터 값 | String(예: 14212) |
| 공고명 | `biz_pbanc_nm` | 지원 사업 공고명 | String(300) |
| 발주기관 | `sprv_inst` | 주관 기관명 | String(300) |
| 마감일 | `pbanc_rcpt_end_dt` | 공고 접수 종료 일시 | YYYY-MM-DD HH:MM:SS |
| 예산 | `pbanc_ctnt`에서 추출 | 공고 내용에서 예산 관련 텍스트 파싱 | String |
| 공고링크 | `detl_pg_url` | 상세페이지 URL | URL(상대경로, 도메인 추가 필요) |

**추가 유용 필드:**
- `intg_pbanc_yn`: 통합 공고 여부 (Y/N)
- `intg_pbanc_biz_nm`: 통합 공고 사업명
- `pbanc_ctnt`: 공고 내용 (과업개요로 활용)
- `supt_biz_clsfc`: 지원 분야 (행사·네트워크, 자금, 교육 등)
- `aply_trgt_ctnt`: 신청 대상 내용
- `supt_regin`: 지역명
- `pbanc_rcpt_bgng_dt`: 공고 접수 시작 일시 (YYYY-MM-DD HH:MM:SS)
- `sprv_inst`: 주관 기관 (공공기관/민간기관 등)
- `biz_prch_dprt_nm`: 사업 담당자 부서명
- `prch_cnpl_no`: 담당자 연락처
- `biz_gdnc_url`: 사업 안내 URL
- `aply_trgt`: 신청 대상 (청소년, 대학생, 일반인 등)
- `biz_enyy`: 창업 기간 (예비창업자, 1년미만, 3년미만 등)
- `biz_trgt_age`: 대상 연령 (만 20세 미만, 만 20세 이상 ~ 만 39세 이하 등)
- `rcrt_prgs_yn`: 모집진행여부 (Y/N)

**상세 URL 형식:**
```
www.k-startup.go.kr/web/contents/bizpbanc-ongoing.do?schM=view&pbancSn=14212
```
- 실제 사용 시 앞에 `https://` 추가 필요
- `pbancSn` 값이 공고 고유 번호

### 3.3 스프레드시트 컬럼 ↔ API 필드 매핑 요약

| 스프레드시트 컬럼 | 나라장터 API 필드 | K-Startup API 필드 | 비고 |
|------------------|------------------|-------------------|------|
| **공고명** (하이퍼링크) | `bidNtceNm` | `biz_pbanc_nm` | 하이퍼링크 수식으로 저장 |
| **공고ID** | `bidNtceNo` | `detl_pg_url`에서 `pbancSn` 추출 | 중복 판단 기준 |
| **발주기관** | `dmndInsttNm` | `sprv_inst` | 수요기관/주관기관 |
| **마감일** | `bidClseDate` | `pbanc_rcpt_end_dt` | YYYY-MM-DD 형식 통일 |
| **남은일수** | (수식) `=D행-TODAY()` | (수식) `=D행-TODAY()` | 스프레드시트 함수 |
| **예산** | `asignBdgtAmt` 또는 `presmptPrce` | `pbanc_ctnt`에서 파싱 | K-Startup은 텍스트 추출 필요 |
| **과업개요** | 제공 안 함 | `pbanc_ctnt` | 나라장터는 상세 크롤링 필요 |
| **한줄요약** | 공고명 기반 생성 | `supt_biz_clsfc` + 공고명 조합 | 선택 구현 |
| **등록일시** | 현재시각 | 현재시각 | YYYY-MM-DD HH:MM:SS |
| **최종수정일시** | 현재시각 | 현재시각 | YYYY-MM-DD HH:MM:SS |

**공고링크 처리:**
- 나라장터: `bidNtceUrl` (전체 URL 제공)
- K-Startup: `detl_pg_url` (상대경로, `https://` 추가 필요)

### 3.4 API 호출 공통 규칙

- **타임아웃**: 10초
- **재시도**: 최대 3회
- **Rate Limiting**: 각 API의 제한사항 준수
  - 나라장터: 초당 최대 30 tps
  - K-Startup: 초당 최대 30 tps
- **에러 처리**: HTTP 상태 코드별 적절한 처리
  - 200: 성공
  - 400: 잘못된 요청 → 로그 기록 후 스킵
  - 401/403: 인증 실패 → 에러 로그 기록
  - 429: Rate Limit 초과 → 1분 대기 후 재시도
  - 500: 서버 에러 → 재시도
- **날짜 형식 변환**:
  - 나라장터 입력: YYYYMMDDHHMM (예: 202601010000)
  - 나라장터 출력: YYYY-MM-DD
  - K-Startup 입력: YYYYMMDD (예: 20260101)
  - K-Startup 출력: YYYY-MM-DD HH:MM:SS
  - 스프레드시트 저장: YYYY-MM-DD (통일)

---

## 4. 구글 스프레드시트 연동

### 4.1 인증 방식
- **Google Sheets API v4** 사용
- **Service Account** 방식 권장
- 필요한 파일:
  - `credentials.json`: Google Cloud Console에서 다운로드한 서비스 계정 키
  - `.env` 파일에 `GOOGLE_SHEET_ID` 저장

### 4.2 권한 설정
1. Google Cloud Console에서 프로젝트 생성
2. Google Sheets API 활성화
3. 서비스 계정 생성 및 키 다운로드
4. 스프레드시트에 서비스 계정 이메일 주소를 **편집자**로 공유

### 4.3 스프레드시트 ID 확인
- URL 형식: `https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit`
- `{SHEET_ID}` 부분을 `.env` 파일에 저장

### 4.4 시트 구조
- **시트 이름**:
  - `"나라장터"`: 나라장터 공고 전용 탭
  - `"K-Startup"`: K-Startup 공고 전용 탭
- **각 탭 구조**:
  - **첫 행**: 헤더 (고정)
  - **데이터 시작**: 2행부터
  - **남은일수 컬럼**: 수식으로 자동 계산 (`=마감일셀-TODAY()`)

---

## 5. 에러 처리 및 로깅

### 5.1 에러 처리 전략

#### 5.1.1 에러 분류
| 에러 타입 | 처리 방식 | 로그 레벨 |
|-----------|----------|----------|
| API 연결 실패 | 3회 재시도 → 실패 시 로그 기록 | ERROR |
| 인증 실패 | 재시도 없이 즉시 중단 → 로그 기록 | CRITICAL |
| 데이터 파싱 에러 | 해당 항목 스킵, 처리 계속 | WARNING |
| 스프레드시트 쓰기 실패 | 3회 재시도 → 실패 시 로그 기록 | ERROR |
| 키워드 필터링 에러 | 로그 기록, 처리 계속 | WARNING |

> **참고**: 이메일 알림은 현재 비활성화 상태입니다. 추후 구현 시 에러 로그와 함께 이메일 발송이 추가될 예정입니다.

#### 5.1.2 이메일 알림 설정 (추후 구현 예정)
> **참고**: 이메일 알림 기능은 현재 비활성화 상태이며, 추후 필요 시 구현할 예정입니다.

- **SMTP 서버**: Gmail 사용 권장
- **환경변수**:
  - `SMTP_SERVER`: smtp.gmail.com
  - `SMTP_PORT`: 587
  - `EMAIL_SENDER`: 발신 이메일 주소
  - `EMAIL_PASSWORD`: 앱 비밀번호
  - `EMAIL_RECEIVER`: 수신 이메일 주소
- **알림 조건** (구현 시):
  - API 인증 실패
  - 3회 재시도 후에도 실패
  - 스프레드시트 업데이트 실패

### 5.2 로깅 구조

#### 5.2.1 로그 파일
```
logs/
  ├── 공고수집_20260201.log
  ├── 공고수집_20260202.log
  └── error_summary.log  # 에러만 모아서 기록
```

#### 5.2.2 로그 포맷
```
[2026-02-01 09:00:00] [INFO] 프로그램 시작
[2026-02-01 09:00:05] [INFO] 나라장터 API 호출 중...
[2026-02-01 09:00:10] [INFO] 나라장터: 총 45건 수집
[2026-02-01 09:00:10] [INFO] 키워드 필터링: 45건 중 12건 매칭
[2026-02-01 09:00:10] [INFO] 마감일 필터링: 12건 중 8건 선택
[2026-02-01 09:00:15] [WARNING] K-Startup API 타임아웃, 재시도 1/3
[2026-02-01 09:00:22] [INFO] K-Startup: 총 23건 수집
[2026-02-01 09:00:30] [INFO] 스프레드시트 업데이트 완료: 신규 5건, 업데이트 3건
[2026-02-01 09:00:30] [INFO] 프로그램 종료 (소요시간: 30초)
```

#### 5.2.3 로그 레벨
- **DEBUG**: 개발 시 상세 정보 (배포 시 비활성화)
- **INFO**: 정상 실행 흐름
- **WARNING**: 주의가 필요하지만 처리 가능한 상황
- **ERROR**: 오류 발생, 일부 기능 실패
- **CRITICAL**: 치명적 오류, 프로그램 중단

---

## 6. QA 테스트 계획

### 6.1 단위 테스트 (Unit Test)

#### UT-1: API 호출 테스트
- **테스트 케이스 1.1**: 나라장터 API 정상 호출
  - 입력: 유효한 API 키, 날짜 범위
  - 예상 결과: 200 응답, JSON 데이터 반환

- **테스트 케이스 1.2**: K-Startup API 정상 호출
  - 입력: 유효한 API 키
  - 예상 결과: 200 응답, JSON 데이터 반환

- **테스트 케이스 1.3**: 잘못된 API 키
  - 입력: 잘못된 API 키
  - 예상 결과: 401/403 응답, 에러 로그 기록, 이메일 발송

#### UT-2: 키워드 필터링 테스트
- **테스트 케이스 2.1**: 단일 키워드 매칭
  - 입력: "스타트업 지원 사업"
  - 예상 결과: True (필터링 통과)

- **테스트 케이스 2.2**: 대소문자 무시
  - 입력: "Start-Up 액셀러레이팅"
  - 예상 결과: True (필터링 통과)

- **테스트 케이스 2.3**: 키워드 없음
  - 입력: "디지털 전환 지원"
  - 예상 결과: False (필터링 탈락)

- **테스트 케이스 2.4**: 부분 문자열 매칭
  - 입력: "스타트업사업"
  - 예상 결과: True ("스타트업" 포함)

#### UT-3: 마감일 필터링 테스트
- **테스트 케이스 3.1**: 마감일 14일 정확히
  - 입력: 마감일 = 2026-02-15, 기준일 = 2026-02-01
  - 예상 결과: True (14일 남음)

- **테스트 케이스 3.2**: 마감일 13일
  - 입력: 마감일 = 2026-02-14, 기준일 = 2026-02-01
  - 예상 결과: False (13일 남음, 기준 미달)

- **테스트 케이스 3.3**: 마감일 30일
  - 입력: 마감일 = 2026-03-03, 기준일 = 2026-02-01
  - 예상 결과: True (30일 남음)

- **테스트 케이스 3.4**: 마감일이 과거
  - 입력: 마감일 = 2026-01-25, 기준일 = 2026-02-01
  - 예상 결과: False (이미 마감)

#### UT-4: 중복 처리 테스트
- **테스트 케이스 4.1**: 신규 공고
  - 입력: 공고ID = "NEW123" (스프레드시트에 없음)
  - 예상 결과: 새 행 추가

- **테스트 케이스 4.2**: 기존 공고
  - 입력: 공고ID = "EXIST456" (이미 존재)
  - 예상 결과: 기존 행 업데이트, 최종수정일시 갱신

- **테스트 케이스 4.3**: 마감일 변경
  - 입력: 기존 공고의 마감일이 연장됨
  - 예상 결과: 마감일 및 남은일수 업데이트

#### UT-5: 스프레드시트 쓰기 테스트
- **테스트 케이스 5.1**: 빈 시트에 헤더 생성
  - 입력: 빈 스프레드시트
  - 예상 결과: 첫 행에 헤더 생성

- **테스트 케이스 5.2**: 데이터 추가
  - 입력: 유효한 공고 데이터 5건
  - 예상 결과: 5개 행 추가

- **테스트 케이스 5.3**: 잘못된 인증 정보
  - 입력: 잘못된 credentials.json
  - 예상 결과: 에러 로그, 이메일 발송

### 6.2 통합 테스트 (Integration Test)

#### IT-1: End-to-End 테스트
- **시나리오**: 전체 프로세스 실행
- **단계**:
  1. 프로그램 실행
  2. 나라장터 API 호출
  3. K-Startup API 호출
  4. 키워드 필터링
  5. 마감일 필터링
  6. 스프레드시트 업데이트
  7. 로그 파일 생성
- **검증 항목**:
  - 각 단계 성공 여부
  - 스프레드시트에 데이터 정확히 반영
  - 로그 파일 생성 및 내용 정확성
  - 소요 시간 1분 이내

#### IT-2: 에러 복구 테스트
- **시나리오**: API 일시적 장애
- **단계**:
  1. 나라장터 API를 일시적으로 차단 (Mock)
  2. 재시도 로직 작동 확인
  3. 3회 재시도 후 실패 시 이메일 발송 확인
  4. K-Startup API는 정상 처리 확인
- **검증 항목**:
  - 한 API 실패가 전체 프로세스를 중단시키지 않음
  - 재시도 간격 5초 준수
  - 에러 로그 정확히 기록
  - 이메일 알림 정상 발송

#### IT-3: 대용량 데이터 테스트
- **시나리오**: 1000건 이상 공고 처리
- **검증 항목**:
  - 메모리 사용량 적정 수준 유지
  - 처리 시간 1분 이내
  - 모든 데이터 정확히 처리
  - 스프레드시트 API Rate Limit 준수

### 6.3 사용자 수용 테스트 (UAT)

#### UAT-1: 일일 자동 실행
- **테스트 기간**: 7일
- **검증 항목**:
  - 매일 정해진 시간에 정확히 실행
  - 스프레드시트가 매일 업데이트됨
  - 로그 파일이 매일 생성됨

#### UAT-2: 데이터 정확성
- **방법**: 수동 확인과 비교
- **샘플 크기**: 최소 20건
- **검증 항목**:
  - 공고 정보가 원본과 일치
  - 마감일 계산이 정확함
  - 키워드 필터링이 정확함

#### UAT-3: 알림 기능
- **시나리오**: 의도적으로 에러 발생
- **검증 항목**:
  - 이메일이 정확한 수신자에게 발송됨
  - 이메일 내용에 에러 정보가 포함됨

### 6.4 테스트 환경

#### 개발 환경
- **OS**: macOS / Windows (개발자 환경)
- **Python**: 3.8 이상
- **테스트 스프레드시트**: 별도의 테스트용 시트 사용
- **API**: 실제 API 사용 (Staging 환경이 있다면 사용)

#### 테스트 데이터
- **Mock Data**: API 응답 샘플 JSON 파일 준비
- **실제 Data**: 실제 API 호출로 테스트 (일일 호출 제한 고려)

### 6.5 테스트 체크리스트

```markdown
## 배포 전 체크리스트

### 기능 테스트
- [ ] 나라장터 API 정상 호출
- [ ] K-Startup API 정상 호출
- [ ] 키워드 필터링 정확성 (20개 샘플)
- [ ] 마감일 필터링 정확성 (14일 경계값 테스트)
- [ ] 중복 공고 업데이트 확인
- [ ] 신규 공고 추가 확인
- [ ] 스프레드시트 헤더 생성
- [ ] 모든 컬럼 데이터 정확히 입력

### 에러 처리
- [ ] API 타임아웃 시 재시도
- [ ] 잘못된 API 키 에러 처리
- [ ] 스프레드시트 인증 실패 처리
- [ ] 이메일 발송 성공 확인

### 로깅
- [ ] 로그 파일 생성 확인
- [ ] 로그 내용 정확성
- [ ] 로그 레벨 적절성

### 보안
- [ ] .env 파일이 .gitignore에 포함
- [ ] credentials.json이 .gitignore에 포함
- [ ] .env.example 파일 존재

### 성능
- [ ] 전체 실행 시간 1분 이내
- [ ] 대용량 데이터(100건) 처리 확인

### 스케줄러
- [ ] 자동 실행 설정 완료
- [ ] 실행 시간 정확성
- [ ] 7일 연속 실행 확인
```

---

## 7. 기술 스택

### 7.1 프로그래밍 언어
- **Python 3.8+**

### 7.2 주요 라이브러리

| 라이브러리 | 버전 | 용도 |
|-----------|------|------|
| `requests` | 2.31+ | API 호출 |
| `python-dotenv` | 1.0+ | 환경변수 관리 (.env 파일) |
| `gspread` | 5.12+ | 구글 스프레드시트 연동 |
| `google-auth` | 2.23+ | 구글 인증 |
| `pandas` | 2.1+ | 데이터 처리 및 변환 (선택) |
| `pytest` | 7.4+ | 단위 테스트 |

### 7.3 스케줄링

#### Windows
```batch
# 작업 스케줄러 등록 명령어
schtasks /create /tn "공고수집" /tr "python C:\path\to\main.py" /sc daily /st 09:00
```

#### macOS/Linux
```bash
# crontab 설정
0 9 * * * /usr/bin/python3 /path/to/main.py >> /path/to/logs/cron.log 2>&1
```

---

## 8. 프로젝트 구조

```
project/
├── .env                      # 환경변수 (비공개)
├── .env.example              # 환경변수 템플릿
├── .gitignore
├── README.md
├── requirements.txt
├── credentials.json          # Google Service Account 키 (비공개)
├── main.py                   # 메인 실행 파일
├── config.py                 # 설정 관리
├── src/
│   ├── __init__.py
│   ├── api_client.py         # API 호출 클래스
│   ├── filter.py             # 키워드/마감일 필터링
│   ├── spreadsheet.py        # 구글 시트 연동
│   ├── logger.py             # 로깅 설정
│   └── email_sender.py       # 이메일 알림
├── tests/
│   ├── __init__.py
│   ├── test_api_client.py
│   ├── test_filter.py
│   ├── test_spreadsheet.py
│   └── mock_data/
│       ├── nara_response.json
│       └── kstartup_response.json
└── logs/                     # 로그 파일 저장 (자동 생성)
    └── .gitkeep
```

---

## 9. 환경변수 (.env)

### 9.1 필수 환경변수

```bash
# API 인증
NARA_API_KEY=your_nara_api_key_here
KSTARTUP_API_KEY=your_kstartup_api_key_here

# 구글 스프레드시트
GOOGLE_SHEET_ID=1AbCdEfGhIjKlMnOpQrStUvWxYz
GOOGLE_CREDENTIALS_FILE=./credentials.json

# 키워드 (쉼표로 구분)
KEYWORDS=스타트업,창업,액셀러레이팅,창업기획자,벤처,소상공인,육성,액셀러레이터,엑셀러레이터,엑셀러레이팅,투자,START-UP,사업화,유니콘,소셜,임팩트,사회문제,활성화,주관기관,운영사

# 마감일 필터링 (최소 남은 일수)
MIN_DAYS_REMAINING=14

# 이메일 알림 (선택)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECEIVER=receiver@example.com

# 로그 설정
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=30
```

### 9.2 .env.example 파일

```bash
# API 인증 (필수)
NARA_API_KEY=
KSTARTUP_API_KEY=

# 구글 스프레드시트 (필수)
GOOGLE_SHEET_ID=
GOOGLE_CREDENTIALS_FILE=./credentials.json

# 키워드 (필수) - 쉼표로 구분
KEYWORDS=스타트업,창업,액셀러레이팅,창업기획자,벤처,소상공인,육성,액셀러레이터,엑셀러레이터,엑셀러레이팅,투자,START-UP,사업화,유니콘,소셜,임팩트,사회문제,활성화,주관기관,운영사

# 마감일 필터링 (필수)
MIN_DAYS_REMAINING=14

# 이메일 알림 (선택 - 에러 알림을 원하지 않으면 비워두세요)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_SENDER=
EMAIL_PASSWORD=
EMAIL_RECEIVER=

# 로그 설정 (선택 - 기본값 사용 가능)
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=30
```

---

## 10. 주요 함수 명세 (Pseudo Code)

### 10.1 메인 함수

```python
def main(is_initial_run=False):
    """
    메인 실행 함수

    Args:
        is_initial_run: True면 Phase 1 (2026-02-01 기준), False면 Phase 2 (실행 당일 기준)
    """
    # 1. 환경변수 로드
    load_env_variables()

    # 2. 로거 초기화
    logger = setup_logger()

    # 3. 기준일 설정
    if is_initial_run:
        base_date = datetime(2026, 2, 1).date()  # Phase 1: 고정 기준일
        logger.info("Phase 1: 초기 데이터 수집 시작 (기준일: 2026-02-01)")
    else:
        base_date = datetime.now().date()  # Phase 2: 실행 당일
        logger.info(f"Phase 2: 일일 업데이트 시작 (기준일: {base_date})")

    start_time = time.time()

    try:
        # 4. API 클라이언트 초기화
        nara_client = NaraAPIClient(api_key=os.getenv('NARA_API_KEY'))
        kstartup_client = KStartupAPIClient(api_key=os.getenv('KSTARTUP_API_KEY'))

        # 5. 공고 데이터 수집
        nara_announcements = nara_client.fetch_announcements(year=2026)
        kstartup_announcements = kstartup_client.fetch_announcements(year=2026)

        logger.info(f"나라장터: {len(nara_announcements)}건 수집")
        logger.info(f"K-Startup: {len(kstartup_announcements)}건 수집")

        # 6. 필터링
        keywords = os.getenv('KEYWORDS').split(',')
        min_days = int(os.getenv('MIN_DAYS_REMAINING', 14))

        # 나라장터 필터링
        nara_filtered_keyword = filter_by_keyword(nara_announcements, keywords)
        nara_filtered_final = filter_by_deadline(nara_filtered_keyword, min_days, base_date)
        logger.info(f"나라장터 필터링 결과: {len(nara_filtered_final)}건 선택")

        # K-Startup 필터링
        kstartup_filtered_keyword = filter_by_keyword(kstartup_announcements, keywords)
        kstartup_filtered_final = filter_by_deadline(kstartup_filtered_keyword, min_days, base_date)
        logger.info(f"K-Startup 필터링 결과: {len(kstartup_filtered_final)}건 선택")

        # 7. 스프레드시트 업데이트 (각 탭별로)
        sheet_id = os.getenv('GOOGLE_SHEET_ID')
        sheet_manager = SpreadsheetManager(sheet_id)

        # 나라장터 탭 업데이트
        nara_result = sheet_manager.update_announcements(nara_filtered_final, sheet_name="나라장터")
        logger.info(f"나라장터 탭 업데이트: 신규 {nara_result['new']}건, 업데이트 {nara_result['updated']}건")

        # K-Startup 탭 업데이트
        kstartup_result = sheet_manager.update_announcements(kstartup_filtered_final, sheet_name="K-Startup")
        logger.info(f"K-Startup 탭 업데이트: 신규 {kstartup_result['new']}건, 업데이트 {kstartup_result['updated']}건")

        # 8. 완료
        elapsed_time = time.time() - start_time
        phase_name = "Phase 1 완료" if is_initial_run else "Phase 2 완료"
        logger.info(f"{phase_name} (소요시간: {elapsed_time:.1f}초)")

    except Exception as e:
        logger.error(f"치명적 에러 발생: {str(e)}", exc_info=True)
        # send_error_email(str(e))  # 추후 구현 예정
        raise
```

### 10.2 키워드 필터링

```python
def filter_by_keyword(announcements: List[dict], keywords: List[str]) -> List[dict]:
    """
    공고 제목에 키워드가 포함된 항목만 필터링

    Args:
        announcements: 공고 리스트
        keywords: 키워드 리스트

    Returns:
        필터링된 공고 리스트
    """
    filtered = []

    for announcement in announcements:
        title = announcement.get('title', '').lower()

        # 키워드 중 하나라도 포함되면 선택
        for keyword in keywords:
            if keyword.strip().lower() in title:
                filtered.append(announcement)
                break  # 하나만 매칭되어도 추가

    return filtered
```

### 10.3 마감일 필터링

```python
def filter_by_deadline(announcements: List[dict], min_days: int, base_date: date) -> List[dict]:
    """
    마감일이 기준일로부터 최소 일수 이상 남은 공고만 필터링

    Args:
        announcements: 공고 리스트
        min_days: 최소 남은 일수 (기본값: 14일)
        base_date: 기준일 (Phase 1: 2026-02-01, Phase 2: 실행 당일)

    Returns:
        필터링된 공고 리스트
    """
    filtered = []

    for announcement in announcements:
        deadline_str = announcement.get('deadline')

        if not deadline_str:
            continue  # 마감일이 없으면 제외

        # 날짜 형식 변환
        deadline = parse_date(deadline_str)  # YYYY-MM-DD or YYYYMMDD

        # 남은 일수 계산 (기준일 기준)
        days_remaining = (deadline - base_date).days
        announcement['days_remaining'] = days_remaining

        # 기준 이상 남았으면 선택
        if days_remaining >= min_days:
            filtered.append(announcement)

    return filtered
```

### 10.4 스프레드시트 업데이트

```python
def update_announcements(self, announcements: List[dict], sheet_name: str) -> dict:
    """
    스프레드시트에 공고 데이터 업데이트

    Args:
        announcements: 공고 리스트
        sheet_name: 시트 이름 ("나라장터" 또는 "K-Startup")

    Returns:
        {'new': 신규 추가 건수, 'updated': 업데이트 건수}
    """
    # 해당 탭 열기 (없으면 생성)
    try:
        worksheet = self.client.open_by_key(self.sheet_id).worksheet(sheet_name)
    except:
        spreadsheet = self.client.open_by_key(self.sheet_id)
        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=10)
        # 헤더 생성
        headers = ['공고명', '공고ID', '발주기관', '마감일', '남은일수', '예산',
                   '과업개요', '요약', '등록일시', '최종수정일시']
        worksheet.update('A1:J1', [headers])

    # 기존 데이터 로드
    existing_data = worksheet.get_all_records()
    existing_ids = {row['공고ID']: idx + 2 for idx, row in enumerate(existing_data)}  # 헤더는 1행

    new_count = 0
    updated_count = 0

    for announcement in announcements:
        announcement_id = announcement['id']
        row_data = self._prepare_row_data(announcement)

        if announcement_id in existing_ids:
            # 업데이트
            row_index = existing_ids[announcement_id]
            # 남은일수 컬럼(E열)을 제외하고 업데이트 (수식 유지)
            worksheet.update(f'A{row_index}:D{row_index}', [row_data[:4]])  # 공고명~마감일
            worksheet.update(f'F{row_index}:J{row_index}', [row_data[5:]])  # 예산~최종수정일시
            updated_count += 1
        else:
            # 신규 추가
            # 남은일수 컬럼에 수식 삽입
            row_data_with_formula = row_data[:4]  # 공고명~마감일
            next_row = len(existing_data) + 2
            row_data_with_formula.append(f'=D{next_row}-TODAY()')  # 남은일수 수식
            row_data_with_formula.extend(row_data[5:])  # 예산~최종수정일시

            worksheet.append_row(row_data_with_formula, value_input_option='USER_ENTERED')
            new_count += 1

    return {'new': new_count, 'updated': updated_count}

def _prepare_row_data(self, announcement: dict) -> List:
    """
    공고 데이터를 스프레드시트 행 형식으로 변환

    Returns:
        [공고명(하이퍼링크), 공고ID, 발주기관, 마감일, (남은일수-스킵), 예산, 과업개요, 요약, 등록일시, 최종수정일시]
    """
    # 공고명에 하이퍼링크 삽입
    announcement_title_with_link = f'=HYPERLINK("{announcement["link"]}", "{announcement["title"]}")'

    return [
        announcement_title_with_link,  # 공고명 (하이퍼링크)
        announcement['id'],            # 공고ID
        announcement['organization'],  # 발주기관
        announcement['deadline'],      # 마감일
        # 남은일수는 여기서 스킵 (스프레드시트 수식으로 계산)
        announcement.get('budget', '정보없음'),     # 예산
        announcement.get('overview', ''),           # 과업개요
        announcement.get('summary', ''),            # 요약
        announcement.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),  # 등록일시
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 최종수정일시
    ]
```

---

## 11. 배포 및 운영

### 11.1 초기 설정 가이드

1. **Python 설치 확인**
   ```bash
   python --version  # 3.8 이상 확인
   ```

2. **프로젝트 클론 및 의존성 설치**
   ```bash
   git clone <repository_url>
   cd project
   pip install -r requirements.txt
   ```

3. **환경변수 설정**
   ```bash
   cp .env.example .env
   # .env 파일을 열어서 API 키 등 입력
   ```

4. **Google Service Account 설정**
   - Google Cloud Console에서 프로젝트 생성
   - Google Sheets API 활성화
   - 서비스 계정 생성 및 JSON 키 다운로드
   - `credentials.json`으로 저장
   - 스프레드시트에 서비스 계정 이메일 공유

5. **테스트 실행**
   ```bash
   python main.py
   ```

6. **스케줄러 설정**
   - Windows: 작업 스케줄러 등록
   - macOS/Linux: crontab 설정

### 11.2 운영 가이드

#### 일일 점검 항목
- [ ] 스프레드시트가 업데이트되었는지 확인
- [ ] 로그 파일에 에러가 없는지 확인

#### 주간 점검 항목
- [ ] 7일 연속 정상 실행 확인
- [ ] 로그 파일 용량 확인 (30일 이상 된 파일 삭제)

#### 이슈 발생 시 대응
1. **API 호출 실패**: `.env` 파일의 API 키 확인
2. **스프레드시트 쓰기 실패**: 서비스 계정 권한 확인
3. **이메일 발송 실패**: SMTP 설정 및 앱 비밀번호 확인

### 11.3 유지보수

#### 키워드 추가/변경
1. `.env` 파일 열기
2. `KEYWORDS` 변수에 쉼표로 구분하여 추가
3. 저장 후 다음 실행 시 자동 반영

#### 마감일 기준 변경
1. `.env` 파일 열기
2. `MIN_DAYS_REMAINING` 값 변경 (예: 14 → 21)
3. 저장 후 다음 실행 시 자동 반영

---

## 12. 리스크 및 제약사항

### 12.1 API 의존성
- **리스크**: API 제공자의 서비스 중단, 변경, Rate Limiting
- **대응**:
  - 재시도 로직 구현
  - 에러 발생 시 이메일 알림
  - API 문서 정기적으로 확인

### 12.2 데이터 품질
- **리스크**: API 응답 데이터의 일관성 부족 (필드 누락, 형식 불일치)
- **대응**:
  - 데이터 검증 로직 추가
  - 누락된 필드는 "정보없음"으로 표시
  - WARNING 로그 기록

### 12.3 구글 스프레드시트 제한
- **제약**:
  - 셀 수 제한: 최대 1000만 셀
  - API 할당량: 분당 100 요청
- **대응**:
  - 배치 업데이트 사용
  - 요청 간 지연 추가 (필요 시)

### 12.4 로컬 실행 환경
- **리스크**: 컴퓨터가 꺼져있으면 실행 안됨
- **대응**:
  - 컴퓨터를 항상 켜두거나 절전 모드 설정
  - 장기적으로는 클라우드 서버 고려

---

## 13. 용어 정의

| 용어 | 정의 |
|------|------|
| 공고 | 정부, 공공기관, 창업지원기관에서 발표하는 사업 공고 |
| 나라장터 | 대한민국 정부 조달 시스템 (g2b) |
| K-Startup | 창업진흥원에서 운영하는 창업 지원 플랫폼 |
| 마감일 | 공고의 제출 마감 일자 |
| 남은일수 | 오늘(실행일)부터 마감일까지 남은 일수 |
| 기준일 | 남은일수 계산의 기준이 되는 날짜 (프로그램 실행일) |
| 공고ID | 각 공고를 고유하게 식별하는 ID (API 제공 또는 생성) |
| 중복 공고 | 이미 스프레드시트에 존재하는 공고 (공고ID 기준) |
| 서비스 계정 | Google API를 사용하기 위한 인증 계정 (사람이 아닌 프로그램용) |

---

## 14. FAQ (자주 묻는 질문)

### Q1: API 키는 어디서 발급받나요?
**A**:
- **나라장터**: [나라장터 오픈API](https://www.g2b.go.kr) → 회원가입 → API 신청
- **K-Startup**: [K-Startup 공식 사이트](https://www.k-startup.go.kr) 또는 관리자 문의

### Q2: credentials.json 파일은 어떻게 생성하나요?
**A**:
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 프로젝트 생성
3. "API 및 서비스" → "라이브러리" → "Google Sheets API" 활성화
4. "사용자 인증 정보" → "서비스 계정 만들기"
5. JSON 키 다운로드

### Q3: 매일 오전 9시가 아닌 다른 시간에 실행하고 싶어요.
**A**:
- **Windows**: 작업 스케줄러에서 시간 변경
- **macOS/Linux**: crontab의 시간 부분 수정 (예: `0 9` → `0 14`는 오후 2시)

### Q4: 키워드를 추가하거나 삭제하고 싶어요.
**A**: `.env` 파일의 `KEYWORDS` 항목을 수정하고 저장하세요. 다음 실행부터 자동 반영됩니다.

### Q5: 마감일 2주가 아닌 3주로 변경하고 싶어요.
**A**: `.env` 파일의 `MIN_DAYS_REMAINING=14`를 `MIN_DAYS_REMAINING=21`로 변경하세요.

### Q6: 이메일 알림이 오지 않아요.
**A**:
- Gmail을 사용하는 경우, "앱 비밀번호"를 사용해야 합니다 (일반 비밀번호 X)
- Gmail 설정 → 보안 → 2단계 인증 활성화 → 앱 비밀번호 생성
- 생성된 16자리 비밀번호를 `.env`의 `EMAIL_PASSWORD`에 입력

### Q7: 스프레드시트에 데이터가 추가되지 않아요.
**A**:
1. 서비스 계정 이메일을 스프레드시트에 "편집자" 권한으로 공유했는지 확인
2. `.env`의 `GOOGLE_SHEET_ID`가 정확한지 확인
3. `credentials.json` 파일 경로가 올바른지 확인

---

## 15. 다음 단계 (개발 프로세스)

### Phase 1: 개발 환경 구축 (1일차)
- [ ] Python 및 필요 라이브러리 설치
- [ ] 프로젝트 구조 생성
- [ ] `.env`, `.gitignore` 설정
- [ ] Google Service Account 설정
- [ ] API 키 발급 (나라장터, K-Startup)

### Phase 2: API 클라이언트 개발 (2-3일차)
- [ ] 나라장터 API 클라이언트 구현
- [ ] K-Startup API 클라이언트 구현
- [ ] API 응답 파싱 로직
- [ ] 단위 테스트 작성

### Phase 3: 필터링 로직 개발 (3-4일차)
- [ ] 키워드 필터링 함수 구현
- [ ] 마감일 필터링 함수 구현
- [ ] 단위 테스트 작성

### Phase 4: 스프레드시트 연동 (4-5일차)
- [ ] 구글 시트 인증 및 연결
- [ ] 데이터 쓰기 로직
- [ ] 중복 처리 로직
- [ ] 단위 테스트 작성

### Phase 5: 에러 처리 및 로깅 (5-6일차)
- [ ] 로거 설정
- [ ] 재시도 로직 구현
- [ ] 이메일 알림 구현
- [ ] 에러 시나리오 테스트

### Phase 6: QA 및 통합 테스트 (6-7일차)
- [ ] End-to-End 테스트
- [ ] 대용량 데이터 테스트
- [ ] 에러 복구 테스트
- [ ] 사용자 수용 테스트 (7일간)

### Phase 7: 배포 및 스케줄러 설정 (7일차)
- [ ] 스케줄러 등록 (Windows/macOS)
- [ ] 첫 실행 확인
- [ ] 7일간 모니터링

---

## 16. 변경 이력

| 버전 | 날짜 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| 1.0 | 2026-01-31 | 최초 작성 | Claude Code |
| 1.1 | 2026-01-31 | FR-4.1: 시트 구조 변경 (탭 분리, 하이퍼링크, 남은일수 수식화)<br>FR-5: 중복 처리 로직 수정<br>FR-6: 자동화 방식 의사결정 가이드 추가 (Apps Script 선택)<br>이메일 알림 기능 비활성화 | Claude Code |
| 1.2 | 2026-01-31 | 섹션 3: API 명세 완전 업데이트<br>- 나라장터 API 정확한 엔드포인트 및 필드 매핑 완료<br>- K-Startup API 정확한 엔드포인트 및 필드 매핑 완료<br>- 실제 API 문서 기반 상세 파라미터 및 응답 필드 정리 | Claude Code |
| 1.3 | 2026-01-31 | API 필드 매핑 수정<br>- 나라장터 발주기관 필드: `ntceInsttNm` → `dmndInsttNm` (수요기관명)<br>- K-Startup 발주기관 필드: `pbanc_ntrp_nm` → `sprv_inst` (주관기관명)<br>- K-Startup 과업개요 필드: `aply_trgt_ctnt` → `pbanc_ctnt` (공고내용) | Claude Code |
| 1.4 | 2026-01-31 | 실행 단계 명확화<br>- Phase 1 (초기 실행): 2026-02-01 기준 2주 이상 공고 수집<br>- Phase 2 (일일 업데이트): 실행 당일 기준 2주 이상 공고 검색/업데이트<br>- FR-3, FR-6, Section 10 함수 명세 업데이트 | Claude Code |

---

## 17. 승인 및 검토

| 역할 | 이름 | 승인일 | 서명 |
|------|------|--------|------|
| 프로젝트 오너 | [이름] | [날짜] | |
| 개발자 | [이름] | [날짜] | |

---

## 부록 A: API 엔드포인트 상세 (개발 중 업데이트 필요)

**주의**: 실제 API 문서를 확인하여 다음 정보를 업데이트해야 합니다.

### 나라장터 API
- **문서 URL**: https://www.g2b.go.kr/index.jsp → "오픈API" 메뉴
- **Base URL**: (문서 확인 필요)
- **주요 엔드포인트**: (문서 확인 필요)

### K-Startup API
- **문서 URL**: (확인 필요, 창업진흥원 문의)
- **Base URL**: (문서 확인 필요)
- **주요 엔드포인트**: (문서 확인 필요)

---

## 부록 B: 샘플 코드

### 환경변수 로드
```python
from dotenv import load_dotenv
import os

load_dotenv()

NARA_API_KEY = os.getenv('NARA_API_KEY')
KSTARTUP_API_KEY = os.getenv('KSTARTUP_API_KEY')
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
KEYWORDS = os.getenv('KEYWORDS', '').split(',')
MIN_DAYS_REMAINING = int(os.getenv('MIN_DAYS_REMAINING', 14))
```

### 로거 설정
```python
import logging
from datetime import datetime

def setup_logger():
    log_filename = f"logs/공고수집_{datetime.now().strftime('%Y%m%d')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    return logging.getLogger(__name__)
```

---

**문서 끝**

이 PRD를 기반으로 개발을 시작하면, 누구든지 동일한 결과물을 만들 수 있습니다.
추가 질문이나 명확하지 않은 부분이 있으면 언제든지 문의하세요.
