"""
Phase 1: 공고 수집 시스템 메인 실행 파일
2026-02-01 기준 마감일 2주 이상 남은 공고 초기 수집
"""
import time
from datetime import datetime

# 프로젝트 모듈
import config
from src.logger import setup_logger
from src.api_client import NaraAPIClient, KStartupAPIClient
from src.filter import filter_by_keyword, filter_by_deadline
from src.spreadsheet import SpreadsheetManager


def main():
    """
    Phase 1 메인 실행 함수
    """
    print("=" * 60)
    print("공고 수집 시스템 - Phase 1: 초기 데이터 수집")
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
    logger.info("Phase 1: 초기 데이터 수집 시작")
    logger.info(f"기준일: {config.PHASE1_BASE_DATE}")
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
        logger.info("\n[나라장터] 데이터 수집 시작...")
        nara_announcements = nara_client.fetch_announcements(year=2026)

        logger.info(f"[나라장터] 키워드 필터링 시작... (키워드 {len(config.KEYWORDS)}개)")
        nara_filtered_keyword = filter_by_keyword(nara_announcements, config.KEYWORDS)

        logger.info(f"[나라장터] 마감일 필터링 시작...")
        nara_filtered_final = filter_by_deadline(
            nara_filtered_keyword,
            config.MIN_DAYS_REMAINING,
            config.PHASE1_BASE_DATE
        )

        # 4-1. 나라장터 과업개요 웹 스크래핑 (필터링 통과 공고만)
        if nara_filtered_final:
            logger.info(f"[나라장터] 과업개요 크롤링 시작... ({len(nara_filtered_final)}건)")
            for i, ann in enumerate(nara_filtered_final):
                if ann.get('link') and not ann.get('overview'):
                    overview = nara_client.fetch_overview_from_page(ann['link'])
                    ann['overview'] = overview
                    if (i + 1) % 10 == 0:
                        logger.debug(f"  과업개요 크롤링 진행: {i + 1}/{len(nara_filtered_final)}건")
                    time.sleep(0.5)  # 서버 부하 방지
            logger.info(f"[나라장터] 과업개요 크롤링 완료")

        # 5. K-Startup 데이터 수집 및 필터링
        logger.info("\n[K-Startup] 데이터 수집 시작...")
        kstartup_announcements = kstartup_client.fetch_announcements(year=2026)

        logger.info(f"[K-Startup] 키워드 필터링 시작... (키워드 {len(config.KEYWORDS)}개)")
        kstartup_filtered_keyword = filter_by_keyword(kstartup_announcements, config.KEYWORDS)

        logger.info(f"[K-Startup] 마감일 필터링 시작...")
        kstartup_filtered_final = filter_by_deadline(
            kstartup_filtered_keyword,
            config.MIN_DAYS_REMAINING,
            config.PHASE1_BASE_DATE
        )

        # 5-1. K-Startup 예산 웹 스크래핑 (필터링 통과 공고만)
        if kstartup_filtered_final:
            logger.info(f"[K-Startup] 예산 크롤링 시작... ({len(kstartup_filtered_final)}건)")
            for i, ann in enumerate(kstartup_filtered_final):
                if ann.get('id') and (not ann.get('budget') or ann.get('budget') == '정보없음'):
                    budget = kstartup_client.fetch_budget_from_page(ann['id'])
                    ann['budget'] = budget
                    if (i + 1) % 10 == 0:
                        logger.debug(f"  예산 크롤링 진행: {i + 1}/{len(kstartup_filtered_final)}건")
                    time.sleep(0.5)  # 서버 부하 방지
            logger.info(f"[K-Startup] 예산 크롤링 완료")

        # 6. 스프레드시트 업데이트
        logger.info("\n스프레드시트 업데이트 시작...")
        sheet_manager = SpreadsheetManager(
            sheet_id=config.GOOGLE_SHEET_ID,
            credentials_file=config.GOOGLE_CREDENTIALS_FILE
        )

        # 나라장터 탭 업데이트
        logger.info(f"\n[나라장터] 스프레드시트 업데이트... ({len(nara_filtered_final)}건)")
        nara_result = sheet_manager.update_announcements(
            nara_filtered_final,
            sheet_name=config.SHEET_NAME_NARA,
            headers=config.SPREADSHEET_HEADERS
        )

        # K-Startup 탭 업데이트
        logger.info(f"\n[K-Startup] 스프레드시트 업데이트... ({len(kstartup_filtered_final)}건)")
        kstartup_result = sheet_manager.update_announcements(
            kstartup_filtered_final,
            sheet_name=config.SHEET_NAME_KSTARTUP,
            headers=config.SPREADSHEET_HEADERS
        )

        # 7. 완료
        elapsed_time = time.time() - start_time
        logger.info("\n" + "=" * 60)
        logger.info("Phase 1 완료!")
        logger.info(f"소요 시간: {elapsed_time:.1f}초")
        logger.info(f"나라장터: 신규 {nara_result['new']}건 추가")
        logger.info(f"K-Startup: 신규 {kstartup_result['new']}건 추가")
        logger.info(f"총 {nara_result['new'] + kstartup_result['new']}건 추가")
        logger.info("=" * 60)

        print("\n" + "=" * 60)
        print("✓ Phase 1 초기 데이터 수집 완료!")
        print(f"  - 나라장터: {nara_result['new']}건")
        print(f"  - K-Startup: {kstartup_result['new']}건")
        print(f"  - 총 {nara_result['new'] + kstartup_result['new']}건 추가")
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
