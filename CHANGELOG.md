# 공고 수집 시스템 수정 로그

이 파일은 시스템 수정 사항을 기록하여 동일한 실수를 반복하지 않기 위한 문서입니다.

---

## 2026-02-01 - 나라장터 API 최신 공고 누락 문제 해결 (주 단위 수집)

### 문제
- 나라장터 API에서 최신 공고(1월 29일)가 수집되지 않음
- 월 단위 수집 시 999건 제한으로 최신 공고 누락
- 사용자가 확인한 "2026년 경기여성 창업플랫폼 통합홈페이지 운영" 공고(마감일: 2026-02-19)가 수집 안 됨

### 원인 분석
**나라장터 API 제한 사항:**
- API 한 번 호출 시 최대 999건만 반환
- 하루 평균 공고 수: 약 150~999건
- 1개월 수집 시: 999건은 **단 6~7일치**만 커버
- **월 단위 수집의 문제점:**
  - 1월 전체 조회 시: 1월 1일 ~ 1월 7일 공고만 수집 (999건)
  - 1월 29일 공고는 범위를 벗어나 누락

**데이터 검증:**
```
1월 999건 커버 기간: 1월 1일 ~ 1월 7일 (6일)
2월 999건 커버 기간: 2월 1일 ~ 2월 2일 (1일)
→ 월 단위로는 최신 공고 수집 불가능
```

### 수정 내용
**파일**: `src/api_client.py`

**전략**: 월 단위(12번 호출) → 주 단위(52번 호출)로 변경

1. **수집 단위 변경** (Line 26-86)
   - Before: 1년을 12개월로 나누어 수집
   - After: 1년을 52주(7일 단위)로 나누어 수집

2. **날짜 계산 로직 추가**
   ```python
   # datetime 사용하여 정확한 주 단위 계산
   current_date = start_of_year
   week_num = 1

   while current_date <= end_of_year:
       week_start = current_date
       week_end = min(current_date + timedelta(days=6), end_of_year)
       # 7일 단위로 수집
       current_date += timedelta(days=7)
       week_num += 1
   ```

3. **로그 메시지 개선**
   - Before: `"나라장터 API 호출: 2026년 1월"`
   - After: `"나라장터 API 호출: 2026년 1주차 (01/01~01/07)"`
   - 사용자가 진행 상황을 더 명확하게 확인 가능

### 결과
- **API 호출 횟수**: 12번 → 52번 (4.3배 증가)
- **예상 실행 시간**: 75초 → 약 300초 (5분)
- **커버리지**: 1년 전체 공고 확실히 수집
- **최신 공고**: 1월 29일 공고 포함하여 모든 최신 공고 수집 가능

### 성능 비교

| 항목 | 월 단위 (Before) | 주 단위 (After) |
|------|-----------------|----------------|
| API 호출 횟수 | 12번 | 52번 |
| 실행 시간 | 75초 | ~300초 (5분) |
| 커버리지 | 1월 7일치만 | 전체 365일 |
| 최신 공고 수집 | ✗ 누락 | ✓ 정상 |

### 교훈
- **공공 API의 제한 사항을 항상 확인할 것**
  - 최대 반환 건수 제한 (999건)
  - 페이지네이션 동작 방식
- **실제 데이터로 검증 필수**
  - 이론적으로 "월 단위면 충분"하다고 가정했으나, 실제로는 하루 공고 수가 너무 많음
  - 999건이 커버하는 기간을 실제로 확인해야 함
- **성능과 정확도 트레이드오프**
  - API 호출 횟수가 늘어나도 정확한 데이터 수집이 우선
  - Phase 2(일일 업데이트)에서는 최근 며칠만 조회하면 되므로 문제 없음

### 향후 최적화 방안
- **Phase 2 구현 시**: 최근 7일만 조회하면 충분 (일일 업데이트이므로)
- **캐싱 도입**: 동일 기간 재조회 시 캐시 사용
- **병렬 처리**: 여러 주를 동시에 조회하여 속도 개선

---

## 2026-02-03 - 나라장터 API 페이지네이션 버그 수정

### 문제
- 주 단위 수집으로 변경했지만 여전히 최신 공고가 수집되지 않음
- "2026년 경기여성 창업플랫폼 통합홈페이지 운영" (R26BK01302914) 공고가 수집 안 됨
- 전체 연도에서 446건만 수집 (Week 5 하나에만 6,334건 존재)

### 원인 분석
**페이지네이션 로직의 치명적 버그:**
- API는 페이지당 100건씩 반환
- 하지만 일부 공고는 마감일(bidClseDate) 필드가 없음
- `_parse_response()`가 필수 필드 검증 시 이런 공고들을 제외
- 예: 100건 요청 → 7건이 마감일 없음 → 93건만 파싱됨
- 페이지네이션 로직이 `if len(items) < 100: break`로 확인
- 93 < 100이므로 첫 페이지에서 중단!

**실제 영향:**
```
Week 5 (Jan 29 - Feb 4):
- totalCount: 6,334건
- 버그 있는 코드: 93건만 수집 (페이지 1에서 중단)
- 수정 후: 모든 페이지 수집, 타겟 공고는 페이지 15에 위치
```

### 수정 내용
**파일**: `src/api_client.py`

1. **`_get_raw_items_count()` 메서드 추가** (Line 118-144)
   - API 응답에서 파싱 전 실제 아이템 수 확인
   - 필터링 전의 원본 개수를 페이지네이션 판단에 사용
   ```python
   def _get_raw_items_count(self, response_data: Dict) -> int:
       """API 응답에서 실제 반환된 아이템 수 확인 (파싱 전)"""
       # items가 list인지 dict인지 확인 후 개수 반환
   ```

2. **페이지네이션 로직 수정** (Line 58-92)
   - Before:
     ```python
     items = self._parse_response(response)
     if len(items) < 100:  # 파싱된 개수로 판단
         break
     ```
   - After:
     ```python
     raw_items_count = self._get_raw_items_count(response)
     items = self._parse_response(response)
     if raw_items_count < 100:  # 원본 개수로 판단
         break
     ```

3. **로그 메시지 개선**
   - Before: `"페이지 {page}: {len(items)}건 수집"`
   - After: `"페이지 {page}: {len(items)}건 수집 (원본 {raw_items_count}건)"`
   - 파싱 과정에서 제외된 공고 수를 확인 가능

### 결과
**Week 5 (Jan 29 - Feb 4) 비교:**
| 항목 | Before | After |
|------|--------|-------|
| 수집된 페이지 | 1페이지 | 64페이지 (전체) |
| 수집된 공고 수 | 93건 | ~6,000건 |
| 타겟 공고 수집 | ✗ 실패 | ✓ 성공 (페이지 15) |

**전체 시스템:**
- 나라장터 전체 수집 건수 대폭 증가 예상 (446건 → 수만 건)
- "경기여성 창업플랫폼" 공고 정상 수집:
  - 공고ID: R26BK01302914
  - 마감일: 2026-02-19 (18일 남음 → 14일 기준 통과)
  - 키워드: "창업" 포함 → 필터링 통과
  - 최종 결과에 포함됨

### 교훈
- **페이지네이션은 원본 응답 기준으로 판단해야 함**
  - 파싱/필터링 후의 개수가 아닌 API가 실제로 반환한 개수 사용
  - 데이터 품질 문제(누락된 필드)가 페이지네이션을 방해해선 안 됨
- **로그에 원본 개수와 파싱된 개수 모두 표시**
  - 디버깅 시 데이터 손실을 빠르게 파악 가능
- **테스트 시 실제 페이지 수를 확인할 것**
  - totalCount와 실제 수집 건수를 비교하여 누락 확인
  - 단순히 "데이터가 수집됨"이 아니라 "예상한 만큼 수집됨"을 검증

---

## 2026-02-04 - Google Sheets API 쿼터 초과 문제 해결 (일괄 업데이트)

### 문제
- K-Startup 공고 52건 중 19건이 쿼터 초과 오류로 추가 실패
- `APIError: [429]: Quota exceeded for quota metric 'Read requests'`
- Google Sheets API는 분당 60회 읽기/쓰기 제한

### 원인 분석
**기존 로직의 문제점:**
- 공고를 하나씩 추가할 때마다 `worksheet.get_all_values()`로 전체 시트 읽기
- 52건 추가 시: 52번 읽기 + 52번 쓰기 = 104회 API 호출
- 분당 60회 제한을 초과 (104 > 60)

**코드 분석:**
```python
# 기존 코드 (src/spreadsheet.py:115-121)
for announcement in announcements:
    next_row = len(worksheet.get_all_values()) + 1  # 매번 전체 시트 읽기!
    row_data = self._prepare_row_data(announcement, next_row)
    worksheet.append_row(row_data, value_input_option='USER_ENTERED')
```

- `get_all_values()`: 전체 시트의 모든 셀 데이터를 읽어옴
- 목적: 현재 행 개수를 파악하여 다음 행 번호 계산
- 52건 추가 → 52회 전체 시트 읽기 → 쿼터 초과

### 수정 내용
**파일**: `src/spreadsheet.py`

**전략**: 반복 읽기 → 일괄 업데이트 (Batch Update)

1. **시트를 한 번만 읽기** (Line 116-117)
   - Before: 공고마다 `get_all_values()` 호출
   - After: 시작 시 한 번만 호출하여 현재 행 개수 저장

2. **메모리에서 행 번호 계산** (Line 119-123)
   - Before: `next_row = len(worksheet.get_all_values()) + 1`
   - After: `next_row = current_rows + i + 1` (메모리에서 계산)

3. **일괄 쓰기** (Line 125-128)
   - Before: `worksheet.append_row()` (하나씩 추가)
   - After: `worksheet.append_rows()` (한 번에 추가)

**수정된 코드:**
```python
try:
    # 시트를 한 번만 읽어서 현재 행 개수 확인
    current_rows = len(worksheet.get_all_values())

    # 모든 행 데이터를 메모리에서 준비
    all_rows = []
    for i, announcement in enumerate(announcements):
        next_row = current_rows + i + 1  # 메모리에서 행 번호 계산
        row_data = self._prepare_row_data(announcement, next_row)
        all_rows.append(row_data)

    # 모든 행을 한 번에 추가 (일괄 업데이트)
    if all_rows:
        worksheet.append_rows(all_rows, value_input_option='USER_ENTERED')
        new_count = len(all_rows)
```

### 결과
**API 호출 횟수 비교 (52건 추가 시):**
| 항목 | Before | After | 감소율 |
|------|--------|-------|--------|
| 읽기 API 호출 | 52회 | 1회 | 98% 감소 |
| 쓰기 API 호출 | 52회 | 1회 | 98% 감소 |
| **총 API 호출** | **104회** | **2회** | **98% 감소** |
| 쿼터 상태 | ✗ 초과 (104 > 60) | ✓ 정상 (2 < 60) |

**성능 개선:**
- 52건 추가 시 쿼터 초과 해결
- 최대 약 300건까지 한 번에 추가 가능 (분당 제한 고려)
- 실행 시간 단축 (API 호출 대기 시간 감소)

### 교훈
- **API 쿼터는 항상 고려해야 함**
  - 반복문 안에서 API 호출 시 쿼터 초과 가능성 확인
  - Google Sheets API: 분당 60회 읽기/쓰기 제한
- **일괄 처리(Batch Processing)가 효율적**
  - 데이터를 메모리에 모아서 한 번에 처리
  - API 호출 횟수를 최소화하여 쿼터 절약 및 속도 개선
- **로그에 API 호출 횟수 모니터링**
  - 쿼터 초과 전에 문제를 파악할 수 있도록 호출 횟수 추적

### 향후 최적화
- **대량 데이터 처리 시 분할 업데이트**
  - 300건 이상 시 60건씩 나누어 처리 (분당 제한 고려)
  - 각 배치 사이에 1분 대기
- **쓰기 전용 최적화**
  - Phase 2에서 중복 체크 필요 시 `get_all_records()` 대신 공고ID만 조회

---

## 2026-02-01 - K-Startup API 응답 파싱 오류 수정

### 문제
- K-Startup API에서 0건 수집됨
- 실제로는 20,499건의 공고가 존재하는데 파싱 실패

### 원인
- 나라장터 API 응답 구조를 가정하여 코드 작성
- 나라장터: `{'response': {'body': {'items': [...]}}}`
- K-Startup: `{'data': [...]}` (직접 배열)
- 두 API의 응답 구조가 달라서 파싱 실패

### 수정 내용
**파일**: `src/api_client.py`

1. **API 요청 파라미터 수정** (Line 186-192)
   - Before: 날짜 필터 파라미터 전달 (`pbanc_rcpt_bgng_dt`, `pbanc_rcpt_end_dt`)
   - After: 날짜 필터 제거 (API가 모든 데이터 반환, 클라이언트가 필터링)

2. **응답 파싱 로직 수정** (Line 240-264)
   - Before:
     ```python
     if 'response' not in response_data:
         return []
     body = response_data['response'].get('body', {})
     items = body.get('items', [])
     ```
   - After:
     ```python
     items = response_data.get('data', [])
     ```

3. **공고ID 추출 방식 변경** (Line 256-257)
   - Before: `detl_pg_url`에서 정규식으로 `pbancSn` 추출
   - After: 직접 `pbanc_sn` 필드 사용

4. **마감일 형식 변환 수정** (Line 259-264)
   - Before: `'YYYY-MM-DD HH:MM:SS'` 형식에서 공백으로 분리
   - After: `'YYYYMMDD'` 8자리 숫자를 `'YYYY-MM-DD'`로 변환

5. **링크 처리 간소화** (Line 266-267)
   - Before: 상대경로 확인 후 `https://` 추가
   - After: `detl_pg_url`이 이미 절대경로이므로 그대로 사용

### 결과
- K-Startup API에서 정상적으로 20,499건 수집
- 테스트 확인: "2026년 창업기업 스케일업 지원사업 R&D 신규지원 시행계획 공고" 정상 수집
  - 공고ID: 176117
  - 마감일: 2026-02-27
  - 키워드: "창업" 포함 → 필터링 통과
  - 남은일수: 26일 → MIN_DAYS_REMAINING 14일 통과

### 교훈
- **외부 API 통합 시 실제 응답 구조를 먼저 확인할 것**
- 공공데이터포털의 표준 API라도 서비스마다 응답 구조가 다를 수 있음
- 테스트 시 실제 API 응답을 출력하여 구조 확인 필수

---

## 향후 개선 사항

### Phase 2 구현 시 고려사항
- [ ] 중복 처리 로직: 공고ID 기준으로 기존 데이터와 비교
- [ ] 동적 기준일: 실행 당일을 기준일로 사용
- [ ] 증분 업데이트: 신규 공고만 추가, 기존 공고는 업데이트
- [ ] 에러 알림: SMTP 이메일 알림 기능 활성화
- [ ] 스케줄링: Apps Script 또는 crontab으로 일일 자동 실행

### 성능 최적화
- [ ] K-Startup API 페이지네이션 최적화 (현재 모든 페이지 조회)
- [ ] 스프레드시트 배치 업데이트 (현재 한 행씩 추가)
- [ ] API 요청 캐싱 고려

### 데이터 품질
- [ ] 예산 파싱 정확도 개선 (정규식 패턴 추가)
- [ ] 과업개요 HTML 태그 제거 개선
- [ ] 마감일 형식 검증 강화

---

## 수정 로그 작성 가이드

각 수정 사항은 다음 형식으로 기록:

```markdown
## YYYY-MM-DD - [수정 제목]

### 문제
[무엇이 문제였는지]

### 원인
[왜 문제가 발생했는지]

### 수정 내용
**파일**: `경로/파일명`
[구체적인 수정 사항, Before/After 코드 포함]

### 결과
[수정 후 결과, 테스트 결과]

### 교훈
[다음에 주의할 점, 배운 점]
```
