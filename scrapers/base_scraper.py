"""
스크래퍼 기본 클래스
모든 플랫폼 스크래퍼가 상속받는 추상 기본 클래스입니다.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """스크래퍼 기본 추상 클래스"""
    
    def __init__(self, platform_name: str):
        """
        기본 스크래퍼 초기화
        
        Args:
            platform_name (str): 플랫폼 이름 (예: '11st', 'gmarket', 'naver')
        """
        self.platform_name = platform_name
        self.logger = logging.getLogger(f"{__name__}.{platform_name}")
    
    @abstractmethod
    def extract_price(self, html_content: str) -> float:
        """
        HTML에서 가격 정보를 추출합니다.
        
        Args:
            html_content (str): HTML 내용
            
        Returns:
            float: 추출된 가격
            
        Raises:
            ValueError: 가격 정보를 찾을 수 없는 경우
        """
        pass
    
    @abstractmethod
    def extract_title(self, html_content: str) -> str:
        """
        HTML에서 상품 제목을 추출합니다.
        
        Args:
            html_content (str): HTML 내용
            
        Returns:
            str: 추출된 상품 제목
            
        Raises:
            ValueError: 제목 정보를 찾을 수 없는 경우
        """
        pass
    
    @abstractmethod
    def extract_stock(self, html_content: str) -> int:
        """
        HTML에서 재고 정보를 추출합니다.
        
        Args:
            html_content (str): HTML 내용
            
        Returns:
            int: 추출된 재고 수량
        """
        pass
    
    def extract_discount_rate(self, html_content: str) -> Optional[float]:
        """
        HTML에서 할인율을 추출합니다.
        
        Args:
            html_content (str): HTML 내용
            
        Returns:
            Optional[float]: 할인율 (없으면 None)
        """
        # 기본 구현: 하위 클래스에서 오버라이드
        return None
    
    def extract_original_price(self, html_content: str) -> Optional[float]:
        """
        HTML에서 원가를 추출합니다.
        
        Args:
            html_content (str): HTML 내용
            
        Returns:
            Optional[float]: 원가 (없으면 None)
        """
        # 기본 구현: 하위 클래스에서 오버라이드
        return None
    
    def calculate_discount_rate(self, current_price: float, original_price: float) -> float:
        """
        할인율을 계산합니다.
        
        Args:
            current_price (float): 현재 가격
            original_price (float): 원가
            
        Returns:
            float: 할인율 (%)
        """
        if original_price <= 0:
            return 0.0
        
        discount_rate = ((original_price - current_price) / original_price) * 100
        return round(discount_rate, 2)
    
    def format_result(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        스크래핑 결과를 표준 형식으로 포맷팅합니다.
        
        Args:
            data (Dict[str, Any]): 원본 데이터
            
        Returns:
            Dict[str, Any]: 포맷팅된 결과
        """
        return {
            'platform': self.platform_name,
            'timestamp': datetime.now().isoformat(),
            'price': data.get('price', 0.0),
            'title': data.get('title', ''),
            'stock': data.get('stock', 0),
            'discount_rate': data.get('discount_rate', 0.0),
            'original_price': data.get('original_price', None),
            'max_discount_price': data.get('max_discount_price', None),
            'max_discount_rate': data.get('max_discount_rate', None),
            'url': data.get('url', ''),
            'status': 'success'
        }
    
    def log_scraping_result(self, url: str, result: Dict[str, Any]):
        """
        스크래핑 결과를 로깅합니다.
        
        Args:
            url (str): 스크래핑한 URL
            result (Dict[str, Any]): 스크래핑 결과
        """
        self.logger.info(
            f"[{self.platform_name}] 스크래핑 완료: "
            f"{result.get('title', 'N/A')} - "
            f"{result.get('price', 0):,}원 "
            f"(할인율: {result.get('discount_rate', 0)}%)"
        ) 