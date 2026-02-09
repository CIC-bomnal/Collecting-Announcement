"""나라장터 API 응답 샘플 확인용 (1회성 디버그)"""
import os
import json
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

api_key = os.getenv('NARA_API_KEY_DECODED')
endpoint = 'https://apis.data.go.kr/1230000/ao/PubDataOpnStdService/getDataSetOpnStdBidPblancInfo'

# 최근 1주일 등록 공고 1건만 조회
now = datetime.now()
week_ago = now - timedelta(days=7)

params = {
    'ServiceKey': api_key,
    'type': 'json',
    'numOfRows': 3,
    'pageNo': 1,
    'bidNtceBgnDt': week_ago.strftime('%Y%m%d%H%M'),
    'bidNtceEndDt': now.strftime('%Y%m%d%H%M'),
}

print(f"조회 범위: {week_ago.strftime('%Y-%m-%d')} ~ {now.strftime('%Y-%m-%d')}")
print(f"API URL: {endpoint}")
print()

resp = requests.get(endpoint, params=params, timeout=15)
data = resp.json()

body = data.get('response', {}).get('body', {})
items = body.get('items', [])

if isinstance(items, dict):
    item_list = items.get('item', [])
    if isinstance(item_list, dict):
        item_list = [item_list]
elif isinstance(items, list):
    item_list = items
else:
    item_list = []

print(f"총 {len(item_list)}건 응답")
print()

for i, item in enumerate(item_list[:3]):
    print(f"=== 공고 {i+1} ===")
    print(f"  bidNtceNo (공고번호): {item.get('bidNtceNo', 'N/A')}")
    print(f"  bidNtceOrd (차수): {item.get('bidNtceOrd', 'N/A')}")
    print(f"  bidNtceNm (공고명): {item.get('bidNtceNm', 'N/A')[:60]}")
    print(f"  bidNtceUrl (URL): {item.get('bidNtceUrl', 'N/A')}")
    print(f"  bidClseDate (마감일): {item.get('bidClseDate', 'N/A')}")
    print(f"  bidNtceDate (공고일): {item.get('bidNtceDate', 'N/A')}")
    print(f"  dmndInsttNm (기관): {item.get('dmndInsttNm', 'N/A')}")
    print()

# 전체 필드명 출력 (첫 번째 아이템)
if item_list:
    print("=== 전체 필드 목록 ===")
    for key in sorted(item_list[0].keys()):
        print(f"  {key}: {str(item_list[0][key])[:80]}")
