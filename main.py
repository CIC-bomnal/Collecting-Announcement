"""
공고 수집 시스템 메인 실행 파일
마감일 7일 이상 남은 공고 수집 및 증분 업데이트
"""
import time
from datetime import datetime, date, timedelta

# 프로젝트 모듈
import config
from src.logger import setup_logger
from src.api_client import NaraAPIClient, KStartupAPIClient
from src.filter import filter_by_keyword, filter_by_deadline, filter_by_pdf_names, filter_by_exclusion
from src.pdf_parser import parse_pdf
from src.spreadsheet import SpreadsheetManager


def main():
    """
    메인 실행 함수
    - API에서 공고 수집 → 키워드/마감일 필터링 → 스프레드시트 증분 업데이트
    """
    print("=" * 60)
    print("공고 수집 시스템 - 데이터 수집 및 업데이트")
    print("=" * 60)
    print()

    # 1. 환경변수 검증
    try:
        config.validate_config()
        print()
    except Exception as e:
        print(f"✗ 환경변수 오류: {str(e)}")
        return

    # 2. 로거 초기화
    logger = setup_logger(config.LOG_LEVEL)
    logger.info("=" * 60)
    logger.info("공고 데이터 수집 시작")
    logger.info(f"기준일: {config.BASE_DATE}")
    logger.info(f"최소 남은 일수: {config.MIN_DAYS_REMAINING}일")
    logger.info("=" * 60)

    start_time = time.time()

    try:
        # 3. API 클라이언트 초기화
        logger.info("API 클라이언트 초기화...")
        nara_client = NaraAPIClient(
            api_key=config.NARA_API_KEY,
            endpoint=config.NARA_API_ENDPOINT
        )
        kstartup_client = KStartupAPIClient(
            api_key=config.KSTARTUP_API_KEY,
            endpoint=config.KSTARTUP_API_ENDPOINT
        )

        # 4. 나라장터 데이터 수집 및 필터링
        logger.info(f"\n[나라장터] 데이터 수집 시작... (검색 범위: {config.SEARCH_DAYS_BACK}일 전~오늘)")
        nara_announcements = nara_client.fetch_announcements(search_days_back=config.SEARCH_DAYS_BACK)

        logger.info(f"[나라장터] 키워드 필터링 시작... (일반 {len(config.KEYWORDS)}개, 필수 {len(config.MUST_EXTRACT_KEYWORDS)}개, 끝부분 {len(config.END_KEYWORDS)}개, 조건부 {len(config.CONDITIONAL_KEYWORDS)}개)")
        nara_filtered_keyword = filter_by_keyword(
            nara_announcements,
            keywords=config.KEYWORDS,
            must_extract_keywords=config.MUST_EXTRACT_KEYWORDS,
            end_keywords=config.END_KEYWORDS,
            conditional_keywords=config.CONDITIONAL_KEYWORDS
        )

        logger.info(f"[나라장터] 마감일 필터링 시작...")
        nara_filtered_final = filter_by_deadline(
            nara_filtered_keyword,
            config.MIN_DAYS_REMAINING,
            config.BASE_DATE
        )

        # 5. PDF 사업명 파싱 (K-Startup 매칭용)
        logger.info("\n[PDF] 창업지원사업 안내서 파싱...")
        pdf_businesses = parse_pdf(config.PDF_PATH)
        pdf_names = [b['name'] for b in pdf_businesses]
        logger.info(f"[PDF] {len(pdf_names)}개 사업명 추출 완료")

        # 6. K-Startup 데이터 수집 및 필터링
        #    흐름: API 전체 fetch → 등록일 필터 → 마감일 필터 → (키워드 OR PDF 사업명) 매칭
        logger.info(f"\n[K-Startup] 데이터 수집 시작... (검색 범위: {config.SEARCH_DAYS_BACK}일 전~오늘)")
        kstartup_announcements = kstartup_client.fetch_announcements(year=2026)

        # 등록일 기준 필터 (검색 범위 내 공고만)
        cutoff_date = (date.today() - timedelta(days=config.SEARCH_DAYS_BACK)).isoformat()
        before_count = len(kstartup_announcements)
        kstartup_announcements = [
            a for a in kstartup_announcements
            if a.get('registration_date', '') >= cutoff_date
        ]
        logger.info(f"[K-Startup] 등록일 필터: {before_count}건 → {len(kstartup_announcements)}건 (기준: {cutoff_date}~)")

        logger.info(f"[K-Startup] 마감일 필터링 시작...")
        kstartup_deadline_filtered = filter_by_deadline(
            kstartup_announcements,
            config.MIN_DAYS_REMAINING,
            config.BASE_DATE
        )

        logger.info(f"[K-Startup] 키워드 필터링... (일반 {len(config.KEYWORDS)}개, 필수 {len(config.MUST_EXTRACT_KEYWORDS)}개, 끝부분 {len(config.END_KEYWORDS)}개, 조건부 {len(config.CONDITIONAL_KEYWORDS)}개)")
        kstartup_keyword_matched = filter_by_keyword(
            kstartup_deadline_filtered,
            keywords=config.KEYWORDS,
            must_extract_keywords=config.MUST_EXTRACT_KEYWORDS,
            end_keywords=config.END_KEYWORDS,
            conditional_keywords=config.CONDITIONAL_KEYWORDS
        )

        logger.info(f"[K-Startup] PDF 사업명 매칭... (사업명 {len(pdf_names)}개, 임계값 {config.MATCH_THRESHOLD})")
        kstartup_pdf_matched = filter_by_pdf_names(
            kstartup_deadline_filtered, pdf_names, config.MATCH_THRESHOLD
        )

        # OR 합산 (키워드 매칭 ∪ PDF 매칭)
        seen_ids = set()
        kstartup_filtered_final = []
        for a in kstartup_keyword_matched + kstartup_pdf_matched:
            if a['id'] not in seen_ids:
                seen_ids.add(a['id'])
                kstartup_filtered_final.append(a)

        pdf_only = len(kstartup_filtered_final) - len(kstartup_keyword_matched)
        logger.info(f"[K-Startup] 최종: {len(kstartup_filtered_final)}건 "
                     f"(키워드 {len(kstartup_keyword_matched)}건 + PDF추가 {max(0, pdf_only)}건)")

        # 7. 금지어 필터링 (육성기업 관점)
        nara_exclusion_filtered = []
        kstartup_exclusion_filtered = []
        if config.EXCLUSION_KEYWORDS:
            logger.info(f"\n[금지어] 필터링 시작... (금지어 {len(config.EXCLUSION_KEYWORDS)}개)")
            nara_exclusion_filtered = filter_by_exclusion(nara_filtered_final, config.EXCLUSION_KEYWORDS)
            kstartup_exclusion_filtered = filter_by_exclusion(kstartup_filtered_final, config.EXCLUSION_KEYWORDS)

        # 8. 스프레드시트 업데이트
        logger.info("\n스프레드시트 업데이트 시작...")
        sheet_manager = SpreadsheetManager(
            sheet_id=config.GOOGLE_SHEET_ID,
            credentials_file=config.GOOGLE_CREDENTIALS_FILE
        )

        # 8-0. 중복 제거 (기존 데이터 정리)
        logger.info("\n[중복 제거] 기존 데이터 정리...")
        nara_dedup = sheet_manager.deduplicate_sheet(
            sheet_name=config.SHEET_NAME_NARA,
            headers=config.NARA_HEADERS
        )
        kstartup_dedup = sheet_manager.deduplicate_sheet(
            sheet_name=config.SHEET_NAME_KSTARTUP,
            headers=config.KSTARTUP_HEADERS
        )
        if nara_dedup or kstartup_dedup:
            logger.info(f"중복 제거 완료: 나라장터 {nara_dedup}건, K-Startup {kstartup_dedup}건 삭제")

        # 8-1. 나라장터 탭 업데이트
        logger.info(f"\n[나라장터] 스프레드시트 업데이트... ({len(nara_filtered_final)}건)")
        nara_result = sheet_manager.update_announcements(
            nara_filtered_final,
            sheet_name=config.SHEET_NAME_NARA,
            headers=config.NARA_HEADERS
        )

        # 8-2. K-Startup 탭 업데이트
        logger.info(f"\n[K-Startup] 스프레드시트 업데이트... ({len(kstartup_filtered_final)}건)")
        kstartup_result = sheet_manager.update_announcements(
            kstartup_filtered_final,
            sheet_name=config.SHEET_NAME_KSTARTUP,
            headers=config.KSTARTUP_HEADERS
        )

        # 8-3. K-Startup 탭 PDF 매칭 행 하이라이팅
        pdf_matched_ids = [a['id'] for a in kstartup_filtered_final if a.get('pdf_matched')]
        if pdf_matched_ids:
            logger.info(f"\n[K-Startup] PDF 매칭 하이라이팅... ({len(pdf_matched_ids)}건)")
            sheet_manager.highlight_rows(
                sheet_name=config.SHEET_NAME_KSTARTUP,
                headers=config.KSTARTUP_HEADERS,
                matched_ids=pdf_matched_ids
            )

        # 8-4. "2026 창업지원사업" 탭 업로드
        logger.info(f"\n[PDF] '2026 창업지원사업' 탭 업로드... ({len(pdf_businesses)}건)")
        sheet_manager.upload_pdf_data(
            businesses=pdf_businesses,
            sheet_name=config.SHEET_NAME_PDF,
            headers=config.PDF_HEADERS
        )

        # 8-5. 금지어 필터 탭 업데이트
        if config.EXCLUSION_KEYWORDS:
            logger.info(f"\n[금지어] 나라장터(필터) 탭 업데이트... ({len(nara_exclusion_filtered)}건)")
            sheet_manager.update_announcements(
                nara_exclusion_filtered,
                sheet_name=config.SHEET_NAME_NARA_FILTERED,
                headers=config.NARA_HEADERS
            )

            logger.info(f"\n[금지어] K-Startup(필터) 탭 업데이트... ({len(kstartup_exclusion_filtered)}건)")
            sheet_manager.update_announcements(
                kstartup_exclusion_filtered,
                sheet_name=config.SHEET_NAME_KSTARTUP_FILTERED,
                headers=config.KSTARTUP_HEADERS
            )

            # 금지어 필터 탭에도 PDF 매칭 하이라이팅 적용
            filtered_pdf_ids = [a['id'] for a in kstartup_exclusion_filtered if a.get('pdf_matched')]
            if filtered_pdf_ids:
                logger.info(f"\n[금지어] K-Startup(필터) PDF 하이라이팅... ({len(filtered_pdf_ids)}건)")
                sheet_manager.highlight_rows(
                    sheet_name=config.SHEET_NAME_KSTARTUP_FILTERED,
                    headers=config.KSTARTUP_HEADERS,
                    matched_ids=filtered_pdf_ids
                )

        # 9. 완료
        elapsed_time = time.time() - start_time
        total_new = nara_result['new'] + kstartup_result['new']
        total_updated = nara_result['updated'] + kstartup_result['updated']

        logger.info("\n" + "=" * 60)
        logger.info("수집 완료!")
        logger.info(f"소요 시간: {elapsed_time:.1f}초")
        logger.info(f"나라장터: 신규 {nara_result['new']}건, 갱신 {nara_result['updated']}건")
        logger.info(f"K-Startup: 신규 {kstartup_result['new']}건, 갱신 {kstartup_result['updated']}건")
        logger.info(f"총 신규 {total_new}건, 갱신 {total_updated}건")
        logger.info("=" * 60)

        print("\n" + "=" * 60)
        print("✓ 공고 데이터 수집 완료!")
        print(f"  - 나라장터: 신규 {nara_result['new']}건, 갱신 {nara_result['updated']}건")
        print(f"  - K-Startup: 신규 {kstartup_result['new']}건, 갱신 {kstartup_result['updated']}건")
        print(f"  - 총 신규 {total_new}건, 갱신 {total_updated}건")
        if config.EXCLUSION_KEYWORDS:
            print(f"  - 금지어 필터: 나라장터 {len(nara_exclusion_filtered)}건, K-Startup {len(kstartup_exclusion_filtered)}건")
        print(f"  - 소요 시간: {elapsed_time:.1f}초")
        print("=" * 60)
        print(f"\n스프레드시트 확인: https://docs.google.com/spreadsheets/d/{config.GOOGLE_SHEET_ID}")

    except KeyboardInterrupt:
        logger.warning("\n사용자에 의해 중단되었습니다.")
        print("\n프로그램이 중단되었습니다.")

    except Exception as e:
        logger.error(f"\n치명적 오류 발생: {str(e)}", exc_info=True)
        print(f"\n✗ 오류 발생: {str(e)}")
        print("자세한 내용은 로그 파일을 확인하세요.")
        raise


if __name__ == '__main__':
    main()
