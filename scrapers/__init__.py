"""
웹 스크래핑 모듈 패키지
다양한 플랫폼의 상품 정보를 수집하는 스크래퍼들을 포함합니다.
"""

from .base_scraper import BaseScraper
from .platform_scraper import PlatformScraper

__all__ = ['BaseScraper', 'PlatformScraper'] 