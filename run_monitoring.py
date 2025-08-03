#!/usr/bin/env python3
"""
네이버 API 리셀러 가격 모니터링 실행 스크립트
"""

import sys
import argparse
import logging
from pathlib import Path

# 프로젝트 모듈 import
from naver_api.product_monitor import ProductMonitor

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='네이버 API 리셀러 가격 모니터링')
    parser.add_argument('--config', default='data/product_config.json', 
                       help='제품 설정 파일 경로 (기본값: data/product_config.json)')
    parser.add_argument('--output', default='results', 
                       help='결과 저장 디렉토리 (기본값: results)')
    parser.add_argument('--dashboard', action='store_true',
                       help='Streamlit 대시보드 실행')
    
    args = parser.parse_args()
    
    try:
        # 모니터링 시스템 초기화
        logger.info("리셀러 가격 모니터링 시스템 초기화...")
        monitor = ProductMonitor(args.config)
        
        # 전체 제품 모니터링 실행
        logger.info("모니터링 시작...")
        results = monitor.monitor_all_products()
        
        # 결과 저장
        output_path = monitor.save_results(results, args.output)
        logger.info(f"결과 저장 완료: {output_path}")
        
        # 결과 요약 출력
        print("\n" + "="*60)
        print("💰 리셀러 가격 모니터링 결과 요약")
        print("="*60)
        
        total_products = results.get('total_products', 0)
        total_resellers = results.get('total_resellers', 0)
        
        print(f"📦 모니터링 제품 수: {total_products}")
        print(f"🏪 발견된 리셀러 수: {total_resellers}")
        print(f"📅 모니터링 시간: {results.get('monitoring_timestamp', 'N/A')}")
        
        # 제품별 요약
        for product_result in results.get('products', []):
            product_name = product_result.get('product_name', 'Unknown')
            reseller_count = product_result.get('reseller_count', 0)
            original_price = product_result.get('original_price', 0)
            
            print(f"\n📦 {product_name}")
            print(f"   💰 정가: {original_price:,}원")
            print(f"   🏪 리셀러 수: {reseller_count}개")
            
            # 최저가 정보
            if product_result.get('results'):
                min_price_item = min(product_result['results'], key=lambda x: x['price'])
                min_price = min_price_item['price']
                min_discount = min_price_item['discount_rate']
                min_mall = min_price_item['mall_name']
                
                print(f"   🔥 최저가: {min_price:,}원 ({min_discount:.1f}% 할인) - {min_mall}")
        
        print("\n" + "="*60)
        
        # 대시보드 실행 옵션
        if args.dashboard:
            print("\n🚀 Streamlit 대시보드를 실행합니다...")
            print("브라우저에서 http://localhost:8501 을 열어주세요.")
            
            import subprocess
            import os
            
            dashboard_path = Path(__file__).parent / "dashboard" / "app.py"
            if dashboard_path.exists():
                subprocess.run([sys.executable, "-m", "streamlit", "run", str(dashboard_path)])
            else:
                logger.error("대시보드 파일을 찾을 수 없습니다.")
        
        else:
            print(f"\n✅ 모니터링 완료! 결과가 {args.output} 디렉토리에 저장되었습니다.")
            print("대시보드를 실행하려면: python run_monitoring.py --dashboard")
        
    except Exception as e:
        logger.error(f"모니터링 실행 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 