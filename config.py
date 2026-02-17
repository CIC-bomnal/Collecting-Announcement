"""
설정 관리 모듈
환경변수 로드 및 전역 설정 관리
"""
import os
from datetime import datetime, date
from dotenv import load_dotenv
from pathlib import Path

# .env 파일 로드
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# 기준일 (실행 당일)
BASE_DATE = date.today()

# API 설정
NARA_API_KEY = os.getenv('NARA_API_KEY_DECODED')
NARA_API_ENDPOINT = os.getenv('NARA_API_ENDPOINT', 'https://apis.data.go.kr/1230000/ao/PubDataOpnStdService')

KSTARTUP_API_KEY = os.getenv('KSTARTUP_API_KEY_DECODED')
KSTARTUP_API_ENDPOINT = os.getenv('KSTARTUP_API_ENDPOINT', 'https://apis.data.go.kr/B552735/kisedKstartupService01')

# Google Sheets 설정
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', './credentials.json')

# 키워드 설정
KEYWORDS_STR = os.getenv('KEYWORDS', '')
KEYWORDS = [k.strip() for k in KEYWORDS_STR.split(',') if k.strip()]

# 필터링 설정
MIN_DAYS_REMAINING = int(os.getenv('MIN_DAYS_REMAINING', '7'))

# 검색 범위 설정 (실행일로부터 N일 전까지 탐색, 기본 60일=2개월)
SEARCH_DAYS_BACK = int(os.getenv('SEARCH_DAYS_BACK', '60'))

# 필수 추출 키워드 (하나라도 매칭 → 무조건 추출)
MUST_EXTRACT_KEYWORDS_STR = os.getenv('MUST_EXTRACT_KEYWORDS', '협력기관,수행기관,주관기관,액셀러레이팅')
MUST_EXTRACT_KEYWORDS = [k.strip() for k in MUST_EXTRACT_KEYWORDS_STR.split(',') if k.strip()]

# 끝부분 키워드 (제목 맨 끝에 매칭 → 무조건 추출)
END_KEYWORDS_STR = os.getenv('END_KEYWORDS', '운영용역')
END_KEYWORDS = [k.strip() for k in END_KEYWORDS_STR.split(',') if k.strip()]

# 조건부 키워드 (일반/필수/끝부분 키워드 1개 이상 함께 매칭 시에만 추출)
CONDITIONAL_KEYWORDS_STR = os.getenv('CONDITIONAL_KEYWORDS', '소상공인,소셜,활성화')
CONDITIONAL_KEYWORDS = [k.strip() for k in CONDITIONAL_KEYWORDS_STR.split(',') if k.strip()]

# 로그 설정
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_RETENTION_DAYS = int(os.getenv('LOG_RETENTION_DAYS', '30'))

# 금지어 설정 (육성기업 관점 필터링)
EXCLUSION_KEYWORDS_STR = os.getenv('EXCLUSION_KEYWORDS', '')
EXCLUSION_KEYWORDS = [k.strip() for k in EXCLUSION_KEYWORDS_STR.split(',') if k.strip()]

# API 공통 설정
API_TIMEOUT = 10
API_MAX_RETRIES = 3
API_RETRY_DELAY = 5

# 시트 이름
SHEET_NAME_NARA = '나라장터'
SHEET_NAME_KSTARTUP = 'K-Startup'
SHEET_NAME_PDF = '2026 창업지원사업'
SHEET_NAME_NARA_FILTERED = '나라장터(필터)'
SHEET_NAME_KSTARTUP_FILTERED = 'K-Startup(필터)'

# 스프레드시트 헤더 (탭별 상이)
NARA_HEADERS = ['공고명', '공고ID', '발주기관', '마감일', '남은일수', '예산', '등록일자', '업로드일자']
KSTARTUP_HEADERS = ['공고명', '공고ID', '발주기관', '마감일', '남은일수', '과업개요', '등록일자', '업로드일자']
PDF_HEADERS = ['사업명', '구분(주관)', '구분(성격)', '예정공고시기', '페이지']

# PDF 설정
PDF_PATH = os.path.join(os.path.dirname(__file__), 'Public_Announcement_guidebook.pdf')
MATCH_THRESHOLD = 60  # rapidfuzz token_set_ratio 임계값


def validate_config():
    """
    필수 환경변수 검증
    """
    required_vars = {
        'NARA_API_KEY': NARA_API_KEY,
        'KSTARTUP_API_KEY': KSTARTUP_API_KEY,
        'GOOGLE_SHEET_ID': GOOGLE_SHEET_ID,
    }

    missing_vars = [name for name, value in required_vars.items() if not value]

    if missing_vars:
        raise ValueError(f"필수 환경변수가 설정되지 않았습니다: {', '.join(missing_vars)}")

    # credentials.json 존재 확인
    creds_path = Path(GOOGLE_CREDENTIALS_FILE)
    if not creds_path.exists():
        raise FileNotFoundError(
            f"Google 서비스 계정 키 파일이 존재하지 않습니다: {GOOGLE_CREDENTIALS_FILE}"
            f"\nGoogle Cloud Console에서 서비스 계정 키를 다운로드하여 credentials.json으로 저장하세요."
        )

    # 검증 완료 출력
    print("✓ 환경변수 검증 완료")
    print(f"  - 나라장터 API 키: {NARA_API_KEY[:20]}...")
    print(f"  - K-Startup API 키: {KSTARTUP_API_KEY[:20]}...")
    print(f"  - 스프레드시트 ID: {GOOGLE_SHEET_ID}")
    print(f"  - 키워드: 일반 {len(KEYWORDS)}개, 필수 {len(MUST_EXTRACT_KEYWORDS)}개, 끝부분 {len(END_KEYWORDS)}개, 조건부 {len(CONDITIONAL_KEYWORDS)}개")
    print(f"  - 금지어 개수: {len(EXCLUSION_KEYWORDS)}개")
    print(f"  - 검색 범위: {SEARCH_DAYS_BACK}일 전~오늘")
    print(f"  - 최소 남은 일수: {MIN_DAYS_REMAINING}일")
    print(f"  - 기준일: {BASE_DATE}")
