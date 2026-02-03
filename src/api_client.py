"""
API 클라이언트 모듈
나라장터 및 K-Startup API 호출
"""
import requests
import time
import re
from datetime import datetime
from typing import List, Dict, Optional
import logging


logger = logging.getLogger('announcement_collector')


class NaraAPIClient:
    """나라장터 API 클라이언트"""

    def __init__(self, api_key: str, endpoint: str):
        self.api_key = api_key
        self.endpoint = endpoint
        self.timeout = 10
        self.max_retries = 3
        self.retry_delay = 5

    def fetch_announcements(self, year: int = 2026) -> List[Dict]:
        """
        나라장터에서 공고 데이터 수집

        Args:
            year: 수집할 연도

        Returns:
            공고 리스트
        """
        all_announcements = []

        # 주 단위(7일)로 데이터 수집 (API 제한: 999건/요청, 하루 평균 150건)
        # 1년 = 약 52주
        from datetime import datetime, timedelta

        start_of_year = datetime(year, 1, 1)
        end_of_year = datetime(year, 12, 31, 23, 59, 59)

        current_date = start_of_year
        week_num = 1

        while current_date <= end_of_year:
            # 주 단위 시작일과 종료일 계산
            week_start = current_date
            week_end = min(current_date + timedelta(days=6, hours=23, minutes=59, seconds=59), end_of_year)

            start_date = week_start.strftime('%Y%m%d%H%M')
            end_date = week_end.strftime('%Y%m%d%H%M')

            logger.info(f"나라장터 API 호출: {year}년 {week_num}주차 ({week_start.strftime('%m/%d')}~{week_end.strftime('%m/%d')})")

            page = 1
            while True:
                params = {
                    'ServiceKey': self.api_key,
                    'type': 'json',
                    'numOfRows': 100,
                    'pageNo': page,
                    'bidNtceBgnDt': start_date,
                    'bidNtceEndDt': end_date
                }

                try:
                    response = self._make_request(params)

                    # 원본 응답에서 실제 반환된 아이템 수 확인 (페이지네이션 판단용)
                    raw_items_count = self._get_raw_items_count(response)

                    items = self._parse_response(response)

                    if not items and raw_items_count == 0:
                        break

                    all_announcements.extend(items)
                    logger.debug(f"  페이지 {page}: {len(items)}건 수집 (원본 {raw_items_count}건)")

                    # 다음 페이지 확인: 원본 응답의 아이템 수로 판단
                    if raw_items_count < 100:
                        break
                    page += 1

                except Exception as e:
                    logger.error(f"나라장터 API 오류 ({year}년 {week_num}주차, 페이지 {page}): {str(e)}")
                    break

            # 다음 주로 이동
            current_date += timedelta(days=7)
            week_num += 1

        logger.info(f"나라장터 총 {len(all_announcements)}건 수집 완료")
        return all_announcements

    def _make_request(self, params: Dict) -> Dict:
        """
        API 요청 (재시도 로직 포함)
        """
        url = f"{self.endpoint}/getDataSetOpnStdBidPblancInfo"

        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                return response.json()

            except requests.exceptions.Timeout:
                logger.warning(f"나라장터 API 타임아웃 (시도 {attempt}/{self.max_retries})")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                else:
                    raise

            except requests.exceptions.RequestException as e:
                logger.error(f"나라장터 API 요청 실패: {str(e)}")
                raise

    def _get_raw_items_count(self, response_data: Dict) -> int:
        """
        API 응답에서 실제 반환된 아이템 수 확인 (파싱 전)
        """
        try:
            if 'response' not in response_data:
                return 0

            body = response_data['response'].get('body', {})
            items = body.get('items', [])

            # items가 딕셔너리인 경우 (단일 아이템)
            if isinstance(items, dict):
                item_list = items.get('item', [])
                if isinstance(item_list, list):
                    return len(item_list)
                elif isinstance(item_list, dict):
                    return 1
                else:
                    return 0
            elif isinstance(items, list):
                return len(items)
            else:
                return 0
        except Exception:
            return 0

    def _parse_response(self, response_data: Dict) -> List[Dict]:
        """
        API 응답 파싱
        """
        try:
            # 응답 구조 확인
            if 'response' not in response_data:
                return []

            body = response_data['response'].get('body', {})
            items = body.get('items', [])

            # items가 딕셔너리인 경우 (단일 아이템)
            if isinstance(items, dict):
                items = [items.get('item', {})]
            elif isinstance(items, list):
                # 리스트인 경우 그대로 사용
                pass
            else:
                return []

            parsed_items = []
            for item in items:
                if not isinstance(item, dict):
                    continue

                parsed_item = {
                    'id': item.get('bidNtceNo', ''),
                    'title': item.get('bidNtceNm', ''),
                    'organization': item.get('dmndInsttNm', '정보없음'),  # 수요기관명
                    'deadline': item.get('bidClseDate', ''),  # YYYY-MM-DD
                    'budget': item.get('asignBdgtAmt') or item.get('presmptPrce') or '정보없음',
                    'link': item.get('bidNtceUrl', ''),
                    'overview': '',  # 나라장터는 과업개요 제공 안 함
                    'summary': '',
                    'source': 'nara'
                }

                # 필수 필드 검증
                if parsed_item['id'] and parsed_item['title'] and parsed_item['deadline']:
                    parsed_items.append(parsed_item)

            return parsed_items

        except Exception as e:
            logger.error(f"나라장터 응답 파싱 오류: {str(e)}")
            return []


class KStartupAPIClient:
    """K-Startup API 클라이언트"""

    def __init__(self, api_key: str, endpoint: str):
        self.api_key = api_key
        self.endpoint = endpoint
        self.timeout = 10
        self.max_retries = 3
        self.retry_delay = 5

    def fetch_announcements(self, year: int = 2026) -> List[Dict]:
        """
        K-Startup에서 공고 데이터 수집

        Args:
            year: 수집할 연도

        Returns:
            공고 리스트
        """
        all_announcements = []

        logger.info(f"K-Startup API 호출: {year}년")

        page = 1
        while True:
            params = {
                'ServiceKey': self.api_key,
                'returnType': 'json',
                'page': page,
                'perPage': 100
                # 날짜 필터 제거: K-Startup API는 모든 공고를 반환하고 클라이언트가 필터링
            }

            try:
                response = self._make_request(params)
                items = self._parse_response(response)

                if not items:
                    break

                all_announcements.extend(items)
                logger.debug(f"  페이지 {page}: {len(items)}건 수집")

                # 다음 페이지 확인
                if len(items) < 100:
                    break
                page += 1

            except Exception as e:
                logger.error(f"K-Startup API 오류 (페이지 {page}): {str(e)}")
                break

        logger.info(f"K-Startup 총 {len(all_announcements)}건 수집 완료")
        return all_announcements

    def _make_request(self, params: Dict) -> Dict:
        """
        API 요청 (재시도 로직 포함)
        """
        url = f"{self.endpoint}/getAnnouncementInformation01"

        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                return response.json()

            except requests.exceptions.Timeout:
                logger.warning(f"K-Startup API 타임아웃 (시도 {attempt}/{self.max_retries})")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                else:
                    raise

            except requests.exceptions.RequestException as e:
                logger.error(f"K-Startup API 요청 실패: {str(e)}")
                raise

    def _parse_response(self, response_data: Dict) -> List[Dict]:
        """
        API 응답 파싱
        """
        try:
            # K-Startup API는 직접 'data' 키에 배열 반환
            items = response_data.get('data', [])

            if not isinstance(items, list):
                return []

            parsed_items = []
            for item in items:
                if not isinstance(item, dict):
                    continue

                # 공고ID: pbanc_sn 사용
                announcement_id = str(item.get('pbanc_sn', ''))

                # 마감일 형식 변환 (YYYYMMDD → YYYY-MM-DD)
                deadline_str = item.get('pbanc_rcpt_end_dt', '')
                if deadline_str and len(deadline_str) == 8 and deadline_str.isdigit():
                    deadline = f"{deadline_str[:4]}-{deadline_str[4:6]}-{deadline_str[6:8]}"
                else:
                    deadline = ''

                # 링크: detl_pg_url이 이미 절대경로
                full_url = item.get('detl_pg_url', '')

                # 과업개요 (pbanc_ctnt)
                pbanc_ctnt = item.get('pbanc_ctnt', '')
                overview = self._clean_html(pbanc_ctnt)

                # 발주기관을 과업개요에서 추출
                organization = self._extract_organization(pbanc_ctnt)

                parsed_item = {
                    'id': announcement_id,
                    'title': item.get('biz_pbanc_nm', ''),
                    'organization': organization,  # 과업개요에서 추출
                    'deadline': deadline,
                    'budget': '',  # K-Startup은 예산 수집 안 함
                    'link': full_url,
                    'overview': overview[:500] if overview else '',  # 500자로 제한
                    'summary': item.get('supt_biz_clsfc', ''),  # 지원 분야를 요약으로 사용
                    'source': 'kstartup'
                }

                # 필수 필드 검증
                if parsed_item['id'] and parsed_item['title'] and parsed_item['deadline']:
                    parsed_items.append(parsed_item)

            return parsed_items

        except Exception as e:
            logger.error(f"K-Startup 응답 파싱 오류: {str(e)}")
            return []

    def _extract_pbanc_sn(self, url: str) -> str:
        """
        URL에서 pbancSn 파라미터 추출
        """
        match = re.search(r'pbancSn=(\d+)', url)
        return match.group(1) if match else ''

    def _clean_html(self, text: str) -> str:
        """
        HTML 태그 제거
        """
        if not text:
            return ''
        # HTML 태그 제거
        clean_text = re.sub(r'<[^>]+>', '', text)
        # 연속된 공백/줄바꿈 정리
        clean_text = re.sub(r'\s+', ' ', clean_text)
        return clean_text.strip()

    def _extract_budget(self, content: str) -> str:
        """
        내용에서 예산 정보 추출
        """
        if not content:
            return '정보없음'

        # 예산 관련 패턴 검색
        patterns = [
            r'(\d{1,3}(?:,\d{3})*)\s*(?:만|억|천만)?\s*원',
            r'예산[:\s]*(\d{1,3}(?:,\d{3})*)\s*(?:만|억|천만)?\s*원',
            r'지원금[:\s]*(\d{1,3}(?:,\d{3})*)\s*(?:만|억|천만)?\s*원'
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(0)

        return '정보없음'

    def _extract_organization(self, content: str) -> str:
        """
        과업개요에서 발주기관(주관기관) 정보 추출
        """
        if not content:
            return '정보없음'

        # HTML 태그 제거
        clean_content = self._clean_html(content)

        # 발주기관 관련 패턴 검색
        patterns = [
            r'주관기관[:\s]*([^\n,\.]+)',
            r'주관사[:\s]*([^\n,\.]+)',
            r'운영기관[:\s]*([^\n,\.]+)',
            r'운영사[:\s]*([^\n,\.]+)',
            r'수행기관[:\s]*([^\n,\.]+)',
            r'사업주관[:\s]*([^\n,\.]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, clean_content)
            if match:
                org = match.group(1).strip()
                # 너무 긴 경우 첫 50자만
                return org[:50] if org else '정보없음'

        return '정보없음'
