"""
네이버 쇼핑 검색 API 클라이언트
네이버 쇼핑 검색 API를 활용하여 상품 정보를 검색합니다.
"""

import os
import requests
import logging
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

logger = logging.getLogger(__name__)


class NaverShoppingAPI:
    """네이버 쇼핑 검색 API 클라이언트"""
    
    def __init__(self):
        """API 클라이언트 초기화"""
        self.client_id = os.getenv('NAVER_CLIENT_ID')
        self.client_secret = os.getenv('NAVER_CLIENT_SECRET')
        self.base_url = "https://openapi.naver.com/v1/search/shop.json"
        
        if not self.client_id or not self.client_secret:
            raise ValueError("네이버 API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.")
        
        self.headers = {
            'X-Naver-Client-Id': self.client_id,
            'X-Naver-Client-Secret': self.client_secret
        }
    
    def search_products(self, keyword: str, display: int = 100, start: int = 1, sort: str = 'sim') -> Dict[str, Any]:
        """
        네이버 쇼핑에서 상품을 검색합니다.
        
        Args:
            keyword (str): 검색 키워드
            display (int): 검색 결과 개수 (최대 100)
            start (int): 검색 시작 위치
            sort (str): 정렬 방식 ('sim': 정확도순, 'date': 날짜순, 'asc': 가격오름차순, 'dsc': 가격내림차순)
            
        Returns:
            Dict[str, Any]: 검색 결과
        """
        try:
            params = {
                'query': keyword,
                'display': min(display, 100),  # 최대 100개
                'start': start,
                'sort': sort
            }
            
            logger.info(f"네이버 쇼핑 검색: {keyword}")
            response = requests.get(self.base_url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"검색 결과: {data.get('total', 0)}개 상품 발견")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"네이버 API 요청 실패: {e}")
            return {
                'error': str(e),
                'items': [],
                'total': 0
            }
        except Exception as e:
            logger.error(f"검색 중 오류 발생: {e}")
            return {
                'error': str(e),
                'items': [],
                'total': 0
            }
    
    def extract_price_info(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        상품 아이템에서 가격 정보를 추출합니다.
        
        Args:
            item (Dict[str, Any]): 네이버 API 응답의 상품 아이템
            
        Returns:
            Dict[str, Any]: 추출된 가격 정보
        """
        try:
            # 가격 정보 추출
            price_str = item.get('lprice', '0')
            price = int(price_str) if price_str.isdigit() else 0
            
            # 상품명에서 HTML 태그 제거
            title = item.get('title', '').replace('<b>', '').replace('</b>', '')
            
            # 쇼핑몰 정보
            mall_name = item.get('mallName', '')
            
            # 상품 링크
            product_link = item.get('link', '')
            
            # 이미지 URL
            image_url = item.get('image', '')
            
            return {
                'title': title,
                'price': price,
                'mall_name': mall_name,
                'product_link': product_link,
                'image_url': image_url,
                'raw_item': item
            }
            
        except Exception as e:
            logger.error(f"가격 정보 추출 실패: {e}")
            return {
                'title': item.get('title', ''),
                'price': 0,
                'mall_name': item.get('mallName', ''),
                'product_link': item.get('link', ''),
                'image_url': item.get('image', ''),
                'error': str(e)
            }
    
    def search_with_pagination(self, keyword: str, max_results: int = 200) -> List[Dict[str, Any]]:
        """
        페이지네이션을 사용하여 더 많은 검색 결과를 가져옵니다.
        
        Args:
            keyword (str): 검색 키워드
            max_results (int): 최대 검색 결과 수
            
        Returns:
            List[Dict[str, Any]]: 검색 결과 리스트
        """
        all_items = []
        start = 1
        display = 100
        
        while len(all_items) < max_results:
            data = self.search_products(keyword, display=display, start=start)
            
            if 'error' in data:
                logger.error(f"검색 실패: {data['error']}")
                break
            
            items = data.get('items', [])
            if not items:
                break
            
            # 가격 정보 추출
            for item in items:
                price_info = self.extract_price_info(item)
                all_items.append(price_info)
            
            # 다음 페이지로 이동
            start += display
            
            # API 호출 제한을 위한 딜레이
            import time
            time.sleep(0.1)
            
            # 최대 결과 수에 도달하면 중단
            if len(all_items) >= max_results:
                break
        
        logger.info(f"총 {len(all_items)}개 상품 정보 수집 완료")
        return all_items[:max_results] 