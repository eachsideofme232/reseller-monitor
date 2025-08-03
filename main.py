#!/usr/bin/env python3
"""
다중 플랫폼 가격 비교 시스템
여러 쇼핑몰의 상품 가격을 비교하고 최적의 할인율을 찾습니다.
"""

import sys
import argparse
import logging
from typing import List, Dict, Any
from pathlib import Path

# 프로젝트 모듈 import
from scrapers.platform_scraper import PlatformScraper
from utils.price_analyzer import PriceAnalyzer, DiscountCalculator

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MultiPlatformMonitor:
    """다중 플랫폼 가격 모니터링 클래스"""
    
    def __init__(self):
        """모니터링 시스템 초기화"""
        self.analyzers = {}
        self.scrapers = {}
        self._init_scrapers()
    
    def _init_scrapers(self):
        """스크래퍼들을 초기화합니다."""
        platforms = ['elevenst', 'gmarket', 'naver_smartstore']  # 지원하는 플랫폼 목록
        
        for platform in platforms:
            try:
                scraper = PlatformScraper(platform)
                self.scrapers[platform] = scraper
                logger.info(f"스크래퍼 초기화 완료: {platform}")
            except Exception as e:
                logger.error(f"스크래퍼 초기화 실패 ({platform}): {e}")
    
    def detect_platform(self, url: str) -> str:
        """
        URL에서 플랫폼을 자동 감지합니다.
        
        Args:
            url (str): 상품 URL
            
        Returns:
            str: 플랫폼 이름
        """
        url_lower = url.lower()
        
        if '11st.co.kr' in url_lower:
            return 'elevenst'
        elif 'gmarket.co.kr' in url_lower:
            return 'gmarket'
        elif 'smartstore.naver.com' in url_lower:
            return 'naver_smartstore'
        elif 'naver.com' in url_lower:
            return 'naver'
        elif 'coupang.com' in url_lower:
            return 'coupang'
        else:
            return 'unknown'
    
    def scrape_single_url(self, url: str, use_playwright: bool = True) -> Dict[str, Any]:
        """
        단일 URL을 스크래핑합니다.
        
        Args:
            url (str): 스크래핑할 URL
            use_playwright (bool): Playwright 사용 여부
            
        Returns:
            Dict[str, Any]: 스크래핑 결과
        """
        platform = self.detect_platform(url)
        
        if platform == 'unknown':
            return {
                'status': 'error',
                'error': f'지원하지 않는 플랫폼: {url}',
                'platform': 'unknown'
            }
        
        if platform not in self.scrapers:
            return {
                'status': 'error',
                'error': f'플랫폼 스크래퍼가 없음: {platform}',
                'platform': platform
            }
        
        try:
            scraper = self.scrapers[platform]
            result = scraper.scrape(url, use_playwright=use_playwright)
            
            # 네이버 스마트스토어인 경우 할인 정보 요약 추가
            if platform == 'naver_smartstore' and result.get('status') == 'success':
                discount_summary = scraper.get_discount_summary(url)
                result['discount_summary'] = discount_summary
                if 'error' not in discount_summary:
                    logger.info(f"네이버 할인 정보 요약: {discount_summary.get('discount_amount', 0):,}원 할인")
            
            return result
        except Exception as e:
            logger.error(f"스크래핑 실패 ({platform}): {e}")
            return {
                'status': 'error',
                'error': str(e),
                'platform': platform,
                'url': url
            }
    
    def compare_prices(self, urls: List[str], use_playwright: bool = True) -> Dict[str, Any]:
        """
        여러 URL의 가격을 비교합니다.
        
        Args:
            urls (List[str]): 비교할 URL 목록
            use_playwright (bool): Playwright 사용 여부
            
        Returns:
            Dict[str, Any]: 비교 결과
        """
        analyzer = PriceAnalyzer()
        
        logger.info(f"가격 비교 시작: {len(urls)}개 URL")
        
        for i, url in enumerate(urls, 1):
            logger.info(f"[{i}/{len(urls)}] 스크래핑 중: {url}")
            
            result = self.scrape_single_url(url, use_playwright)
            analyzer.add_result(result)
            
            # 요청 간 딜레이 (서버 부하 방지)
            if i < len(urls):
                import time
                time.sleep(2)
        
        # 비교 결과 생성
        comparison = analyzer.get_platform_comparison()
        
        # 결과 출력
        self._print_comparison_results(comparison)
        
        return comparison
    
    def _print_comparison_results(self, comparison: Dict[str, Any]):
        """
        비교 결과를 콘솔에 출력합니다.
        
        Args:
            comparison (Dict[str, Any]): 비교 결과
        """
        print("\n" + "="*60)
        print("🏪 다중 플랫폼 가격 비교 결과")
        print("="*60)
        
        if not comparison.get('platforms'):
            print("❌ 비교할 결과가 없습니다.")
            return
        
        # 플랫폼별 정보 출력
        for platform, data in comparison['platforms'].items():
            price = data.get('price', 0)
            discount_rate = data.get('discount_rate', 0)
            original_price = data.get('original_price')
            stock = data.get('stock', 0)
            max_discount_price = data.get('max_discount_price')
            max_discount_rate = data.get('max_discount_rate')
            discount_summary = data.get('discount_summary', {})
            
            print(f"\n📦 {platform.upper()}")
            print(f"   💰 가격: {price:,}원")
            if original_price:
                print(f"   📊 원가: {original_price:,}원")
            print(f"   🎯 할인율: {discount_rate}%")
            
            # 네이버 스마트스토어 특화 정보
            if platform == 'naver_smartstore' and discount_summary:
                discount_amount = discount_summary.get('discount_amount', 0)
                is_discounted = discount_summary.get('is_discounted', False)
                if is_discounted and discount_amount > 0:
                    print(f"   💸 할인금액: {discount_amount:,}원")
                    print(f"   ✅ 할인적용: 예")
                else:
                    print(f"   ❌ 할인적용: 아니오")
            
            if max_discount_price and max_discount_rate:
                print(f"   🔥 최대할인가: {max_discount_price:,}원 ({max_discount_rate}%)")
            print(f"   📦 재고: {stock}개")
        
        # 최적 정보 출력
        best_price = comparison.get('best_price')
        highest_discount = comparison.get('highest_discount')
        
        if best_price:
            print(f"\n🏆 최저가: {best_price.get('platform', '').upper()}")
            print(f"   💰 {best_price.get('price', 0):,}원")
        
        if highest_discount:
            print(f"\n🎉 최고 할인율: {highest_discount.get('platform', '').upper()}")
            print(f"   🎯 {highest_discount.get('discount_rate', 0)}%")
        
        print("\n" + "="*60)
    
    def save_results(self, comparison: Dict[str, Any], output_dir: str = "output"):
        """
        비교 결과를 파일로 저장합니다.
        
        Args:
            comparison (Dict[str, Any]): 비교 결과
            output_dir (str): 저장할 디렉토리
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # JSON 파일로 저장
        json_path = output_path / "price_comparison.json"
        import json
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(comparison, f, ensure_ascii=False, indent=2)
        
        # CSV 파일로 저장
        csv_path = output_path / "price_comparison.csv"
        analyzer = PriceAnalyzer()
        analyzer.export_comparison(str(csv_path), 'csv')
        
        logger.info(f"결과 저장 완료: {output_dir}")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='다중 플랫폼 가격 비교 시스템')
    parser.add_argument('urls', nargs='+', help='비교할 상품 URL들')
    parser.add_argument('--no-playwright', action='store_true', 
                       help='Playwright 사용하지 않음 (requests만 사용)')
    parser.add_argument('--output', default='output', 
                       help='결과 저장 디렉토리 (기본값: output)')
    
    args = parser.parse_args()
    
    # 모니터링 시스템 초기화
    monitor = MultiPlatformMonitor()
    
    # 가격 비교 실행
    comparison = monitor.compare_prices(args.urls, use_playwright=not args.no_playwright)
    
    # 결과 저장
    monitor.save_results(comparison, args.output)
    
    print(f"\n✅ 가격 비교 완료! 결과가 {args.output} 디렉토리에 저장되었습니다.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python main.py <URL1> <URL2> ...")
        print("예시: python main.py https://www.11st.co.kr/products/123 https://www.gmarket.co.kr/item/456")
        sys.exit(1)
    
    main() 