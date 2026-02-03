"""
Google Sheets 연동 모듈
스프레드시트 데이터 읽기/쓰기
"""
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from typing import List, Dict
import logging


logger = logging.getLogger('announcement_collector')


class SpreadsheetManager:
    """Google Sheets 관리 클래스"""

    def __init__(self, sheet_id: str, credentials_file: str):
        """
        Args:
            sheet_id: 스프레드시트 ID
            credentials_file: 서비스 계정 키 파일 경로
        """
        self.sheet_id = sheet_id
        self.credentials_file = credentials_file
        self.client = None
        self.spreadsheet = None
        self._init_client()

    def _init_client(self):
        """gspread 클라이언트 초기화"""
        try:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=scopes
            )
            self.client = gspread.authorize(creds)
            self.spreadsheet = self.client.open_by_key(self.sheet_id)
            logger.info(f"✓ 스프레드시트 연결 성공: {self.spreadsheet.title}")

        except Exception as e:
            logger.error(f"스프레드시트 인증 실패: {str(e)}")
            raise

    def get_or_create_worksheet(self, sheet_name: str) -> gspread.Worksheet:
        """
        워크시트 가져오기 또는 생성

        Args:
            sheet_name: 시트 이름

        Returns:
            워크시트 객체
        """
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            logger.info(f"✓ 기존 시트 사용: {sheet_name}")
            return worksheet

        except gspread.exceptions.WorksheetNotFound:
            # 시트가 없으면 생성
            worksheet = self.spreadsheet.add_worksheet(
                title=sheet_name,
                rows=1000,
                cols=10
            )
            logger.info(f"✓ 새 시트 생성: {sheet_name}")
            return worksheet

    def ensure_headers(self, worksheet: gspread.Worksheet, headers: List[str]):
        """
        헤더 행 확인 및 생성

        Args:
            worksheet: 워크시트 객체
            headers: 헤더 리스트
        """
        try:
            # 첫 행 읽기
            existing_headers = worksheet.row_values(1)

            if not existing_headers or existing_headers != headers:
                # 헤더 업데이트
                worksheet.update('A1:J1', [headers], value_input_option='RAW')
                logger.info(f"✓ 헤더 설정 완료: {len(headers)}개 컬럼")
            else:
                logger.info(f"✓ 헤더 이미 존재")

        except Exception as e:
            logger.error(f"헤더 설정 오류: {str(e)}")
            raise

    def update_announcements(self, announcements: List[Dict], sheet_name: str, headers: List[str]) -> Dict:
        """
        공고 데이터를 스프레드시트에 업데이트

        Args:
            announcements: 공고 리스트
            sheet_name: 시트 이름
            headers: 헤더 리스트

        Returns:
            {'new': 신규 추가 건수}
        """
        worksheet = self.get_or_create_worksheet(sheet_name)
        self.ensure_headers(worksheet, headers)

        new_count = 0

        # Phase 1이므로 중복 체크 없이 모두 추가
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
                logger.info(f"✓ {sheet_name} 탭 일괄 업데이트 완료: 신규 {new_count}건")
            else:
                logger.info(f"✓ {sheet_name} 탭: 추가할 데이터 없음")

        except Exception as e:
            logger.error(f"일괄 업데이트 오류: {str(e)}")
            raise

        return {'new': new_count}

    def _prepare_row_data(self, announcement: Dict, row_number: int) -> List:
        """
        공고 데이터를 스프레드시트 행 형식으로 변환

        Args:
            announcement: 공고 데이터
            row_number: 추가될 행 번호

        Returns:
            [공고명(하이퍼링크), 공고ID, 발주기관, 마감일, 남은일수(수식), 예산, 과업개요, 요약, 등록일시, 최종수정일시]
        """
        # 공고명에 하이퍼링크 삽입
        title = announcement.get('title', '').replace('"', '""')  # 쌍따옴표 이스케이프
        link = announcement.get('link', '')
        announcement_title_with_link = f'=HYPERLINK("{link}", "{title}")'

        # 현재 시각
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 남은일수 수식: 마감일(D열) - TODAY()
        # 예: =D2-TODAY(), =D3-TODAY(), ...
        remaining_days_formula = f'=D{row_number}-TODAY()'

        return [
            announcement_title_with_link,           # 공고명 (하이퍼링크)
            announcement.get('id', ''),             # 공고ID
            announcement.get('organization', ''),   # 발주기관
            announcement.get('deadline', ''),       # 마감일
            remaining_days_formula,                 # 남은일수 (수식)
            str(announcement.get('budget', '')),    # 예산
            announcement.get('overview', '')[:500], # 과업개요 (500자 제한)
            announcement.get('summary', '')[:100],  # 요약 (100자 제한)
            now,                                    # 등록일시
            now                                     # 최종수정일시
        ]
