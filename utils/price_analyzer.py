"""
가격 분석 및 할인율 계산 유틸리티
여러 플랫폼의 가격을 비교하고 최적의 할인율을 찾는 기능을 제공합니다.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PriceAnalyzer:
    """가격 분석 및 할인율 계산 클래스"""
    
    def __init__(self):
        """가격 분석기 초기화"""
        self.results = []
    
    def add_result(self, result: Dict[str, Any]):
        """
        스크래핑 결과를 추가합니다.
        
        Args:
            result (Dict[str, Any]): 스크래핑 결과
        """
        if result.get('status') == 'success':
            self.results.append(result)
            logger.info(f"결과 추가: {result.get('platform')} - {result.get('price'):,}원")
    
    def get_best_price(self) -> Optional[Dict[str, Any]]:
        """
        가장 저렴한 가격의 상품을 반환합니다.
        
        Returns:
            Optional[Dict[str, Any]]: 최저가 상품 정보
        """
        if not self.results:
            return None
        
        return min(self.results, key=lambda x: x.get('price', float('inf')))
    
    def get_highest_discount(self) -> Optional[Dict[str, Any]]:
        """
        가장 높은 할인율의 상품을 반환합니다.
        
        Returns:
            Optional[Dict[str, Any]]: 최고 할인율 상품 정보
        """
        if not self.results:
            return None
        
        return max(self.results, key=lambda x: x.get('discount_rate', 0))
    
    def get_platform_comparison(self) -> Dict[str, Any]:
        """
        플랫폼별 가격 비교 결과를 반환합니다.
        
        Returns:
            Dict[str, Any]: 플랫폼별 비교 결과
        """
        if not self.results:
            return {}
        
        comparison = {
            'total_platforms': len(self.results),
            'best_price': self.get_best_price(),
            'highest_discount': self.get_highest_discount(),
            'platforms': {}
        }
        
        for result in self.results:
            platform = result.get('platform', 'unknown')
            comparison['platforms'][platform] = {
                'price': result.get('price', 0),
                'discount_rate': result.get('discount_rate', 0),
                'original_price': result.get('original_price'),
                'stock': result.get('stock', 0),
                'url': result.get('url', ''),
                'timestamp': result.get('timestamp', '')
            }
        
        return comparison
    
    def calculate_savings(self, target_price: float) -> Dict[str, Any]:
        """
        목표 가격 대비 절약 금액을 계산합니다.
        
        Args:
            target_price (float): 목표 가격
            
        Returns:
            Dict[str, Any]: 절약 정보
        """
        if not self.results:
            return {}
        
        savings_info = {
            'target_price': target_price,
            'platforms': {}
        }
        
        for result in self.results:
            platform = result.get('platform', 'unknown')
            current_price = result.get('price', 0)
            
            savings = target_price - current_price
            savings_percentage = (savings / target_price * 100) if target_price > 0 else 0
            
            savings_info['platforms'][platform] = {
                'current_price': current_price,
                'savings_amount': savings,
                'savings_percentage': round(savings_percentage, 2),
                'is_better': savings > 0
            }
        
        return savings_info
    
    def get_price_history(self, platform: str, days: int = 7) -> List[Dict[str, Any]]:
        """
        특정 플랫폼의 가격 이력을 반환합니다.
        
        Args:
            platform (str): 플랫폼 이름
            days (int): 조회할 일수
            
        Returns:
            List[Dict[str, Any]]: 가격 이력
        """
        # TODO: 데이터베이스 연동하여 실제 가격 이력 조회
        # 현재는 메모리상의 결과만 반환
        return [r for r in self.results if r.get('platform') == platform]
    
    def export_comparison(self, filepath: str, format: str = 'json'):
        """
        비교 결과를 파일로 내보냅니다.
        
        Args:
            filepath (str): 저장할 파일 경로
            format (str): 파일 형식 ('json' 또는 'csv')
        """
        comparison = self.get_platform_comparison()
        
        if format.lower() == 'json':
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(comparison, f, ensure_ascii=False, indent=2)
        elif format.lower() == 'csv':
            # CSV 형식으로 내보내기
            import csv
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Platform', 'Price', 'Discount Rate', 'Original Price', 'Stock', 'URL'])
                
                for platform, data in comparison.get('platforms', {}).items():
                    writer.writerow([
                        platform,
                        data.get('price', 0),
                        data.get('discount_rate', 0),
                        data.get('original_price', ''),
                        data.get('stock', 0),
                        data.get('url', '')
                    ])
        
        logger.info(f"비교 결과 저장됨: {filepath}")
    
    def clear_results(self):
        """결과 목록을 초기화합니다."""
        self.results.clear()
        logger.info("결과 목록 초기화됨")


class DiscountCalculator:
    """할인율 계산 전용 클래스"""
    
    @staticmethod
    def calculate_discount_rate(current_price: float, original_price: float) -> float:
        """
        할인율을 계산합니다.
        
        Args:
            current_price (float): 현재 가격
            original_price (float): 원가
            
        Returns:
            float: 할인율 (%)
        """
        if original_price <= 0 or current_price >= original_price:
            return 0.0
        
        discount_rate = ((original_price - current_price) / original_price) * 100
        return round(discount_rate, 2)
    
    @staticmethod
    def calculate_savings_amount(current_price: float, original_price: float) -> float:
        """
        절약 금액을 계산합니다.
        
        Args:
            current_price (float): 현재 가격
            original_price (float): 원가
            
        Returns:
            float: 절약 금액
        """
        return max(0, original_price - current_price)
    
    @staticmethod
    def is_good_deal(current_price: float, original_price: float, threshold: float = 20.0) -> bool:
        """
        좋은 할인인지 판단합니다.
        
        Args:
            current_price (float): 현재 가격
            original_price (float): 원가
            threshold (float): 할인율 임계값 (%)
            
        Returns:
            bool: 좋은 할인 여부
        """
        discount_rate = DiscountCalculator.calculate_discount_rate(current_price, original_price)
        return discount_rate >= threshold 