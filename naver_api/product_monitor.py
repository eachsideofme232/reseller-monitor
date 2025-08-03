"""
제품별 모니터링 시스템
네이버 쇼핑 API를 활용하여 특정 제품들의 리셀러 가격을 모니터링합니다.
"""

import json
import logging
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from .naver_shopping_api import NaverShoppingAPI

logger = logging.getLogger(__name__)


class ProductMonitor:
    """제품별 모니터링 클래스"""
    
    def __init__(self, config_path: str = "data/product_config.json"):
        """
        모니터링 시스템 초기화
        
        Args:
            config_path (str): 제품 설정 파일 경로
        """
        self.config_path = Path(config_path)
        self.api_client = NaverShoppingAPI()
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """설정 파일을 로드합니다."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"설정 파일 로드 완료: {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"설정 파일 로드 실패: {e}")
            raise
    
    def filter_reseller_items(self, items: List[Dict[str, Any]], exclude_keywords: List[str] = None) -> List[Dict[str, Any]]:
        """
        리셀러 아이템을 필터링합니다.
        
        Args:
            items (List[Dict[str, Any]]): 검색된 아이템 리스트
            exclude_keywords (List[str]): 제외할 키워드 리스트
            
        Returns:
            List[Dict[str, Any]]: 필터링된 리셀러 아이템 리스트
        """
        if exclude_keywords is None:
            exclude_keywords = self.config.get('monitoring_settings', {}).get('exclude_keywords', [])
        
        filtered_items = []
        
        for item in items:
            title = item.get('title', '').lower()
            mall_name = item.get('mall_name', '').lower()
            
            # 제외 키워드가 포함된 상품 제외
            should_exclude = any(keyword.lower() in title for keyword in exclude_keywords)
            
            if not should_exclude:
                # 가격 임계값 확인
                min_price = self.config.get('monitoring_settings', {}).get('min_price_threshold', 10000)
                max_price = self.config.get('monitoring_settings', {}).get('max_price_threshold', 1000000)
                item_price = item.get('price', 0)
                
                if min_price <= item_price <= max_price:
                    filtered_items.append(item)
        
        logger.info(f"리셀러 아이템 필터링 완료: {len(items)}개 → {len(filtered_items)}개")
        return filtered_items
    
    def calculate_discount_rate(self, current_price: int, original_price: int) -> float:
        """
        할인율을 계산합니다.
        
        Args:
            current_price (int): 현재 판매가
            original_price (int): 정가
            
        Returns:
            float: 할인율 (%)
        """
        if original_price <= 0:
            return 0.0
        
        discount_rate = ((original_price - current_price) / original_price) * 100
        return round(discount_rate, 2)
    
    def monitor_product(self, product_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        단일 제품을 모니터링합니다.
        
        Args:
            product_config (Dict[str, Any]): 제품 설정 정보
            
        Returns:
            Dict[str, Any]: 모니터링 결과
        """
        product_name = product_config['name']
        keyword = product_config['keyword']
        original_price = product_config['original_price']
        
        logger.info(f"제품 모니터링 시작: {product_name}")
        
        try:
            # 네이버 쇼핑 검색
            max_results = self.config.get('monitoring_settings', {}).get('max_results_per_product', 100)
            items = self.api_client.search_with_pagination(keyword, max_results)
            
            # 리셀러 아이템 필터링
            filtered_items = self.filter_reseller_items(items)
            
            # 할인율 계산 및 결과 정리
            results = []
            for item in filtered_items:
                discount_rate = self.calculate_discount_rate(item['price'], original_price)
                
                result = {
                    'product_name': product_name,
                    'title': item['title'],
                    'price': item['price'],
                    'original_price': original_price,
                    'discount_rate': discount_rate,
                    'discount_amount': original_price - item['price'],
                    'mall_name': item['mall_name'],
                    'product_link': item['product_link'],
                    'image_url': item['image_url'],
                    'search_timestamp': datetime.now().isoformat()
                }
                results.append(result)
            
            # 가격순으로 정렬
            results.sort(key=lambda x: x['price'])
            
            logger.info(f"제품 모니터링 완료: {product_name} - {len(results)}개 리셀러 발견")
            
            return {
                'product_name': product_name,
                'keyword': keyword,
                'original_price': original_price,
                'total_items': len(items),
                'filtered_items': len(filtered_items),
                'reseller_count': len(results),
                'results': results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"제품 모니터링 실패 ({product_name}): {e}")
            return {
                'product_name': product_name,
                'error': str(e),
                'results': [],
                'timestamp': datetime.now().isoformat()
            }
    
    def monitor_all_products(self) -> Dict[str, Any]:
        """
        모든 타겟 제품을 모니터링합니다.
        
        Returns:
            Dict[str, Any]: 전체 모니터링 결과
        """
        target_products = self.config.get('target_products', [])
        all_results = []
        
        logger.info(f"전체 제품 모니터링 시작: {len(target_products)}개 제품")
        
        for product_config in target_products:
            result = self.monitor_product(product_config)
            all_results.append(result)
            
            # API 호출 간격 조절
            import time
            time.sleep(1)
        
        # 전체 요약 정보 생성
        total_resellers = sum(len(r.get('results', [])) for r in all_results)
        total_products = len(target_products)
        
        summary = {
            'total_products': total_products,
            'total_resellers': total_resellers,
            'monitoring_timestamp': datetime.now().isoformat(),
            'products': all_results
        }
        
        logger.info(f"전체 모니터링 완료: {total_products}개 제품, {total_resellers}개 리셀러")
        
        return summary
    
    def save_results(self, results: Dict[str, Any], output_dir: str = "results") -> str:
        """
        모니터링 결과를 파일로 저장합니다.
        
        Args:
            results (Dict[str, Any]): 모니터링 결과
            output_dir (str): 저장할 디렉토리
            
        Returns:
            str: 저장된 파일 경로
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # JSON 파일로 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"monitoring_results_{timestamp}.json"
        json_path = output_path / json_filename
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # CSV 파일로 저장 (리셀러 정보만)
        csv_filename = f"reseller_data_{timestamp}.csv"
        csv_path = output_path / csv_filename
        
        all_reseller_data = []
        for product_result in results.get('products', []):
            for reseller in product_result.get('results', []):
                all_reseller_data.append(reseller)
        
        if all_reseller_data:
            df = pd.DataFrame(all_reseller_data)
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            logger.info(f"CSV 파일 저장 완료: {csv_path}")
        
        logger.info(f"결과 저장 완료: {json_path}")
        return str(json_path)
    
    def get_dataframe(self, results: Dict[str, Any]) -> pd.DataFrame:
        """
        모니터링 결과를 DataFrame으로 변환합니다.
        
        Args:
            results (Dict[str, Any]): 모니터링 결과
            
        Returns:
            pd.DataFrame: 변환된 DataFrame
        """
        all_reseller_data = []
        
        for product_result in results.get('products', []):
            for reseller in product_result.get('results', []):
                all_reseller_data.append(reseller)
        
        if all_reseller_data:
            df = pd.DataFrame(all_reseller_data)
            return df
        else:
            return pd.DataFrame() 