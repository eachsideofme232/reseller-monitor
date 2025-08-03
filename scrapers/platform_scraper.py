"""
설정 기반 플랫폼 스크래퍼
JSON 설정 파일을 통해 다양한 플랫폼을 지원하는 범용 스크래퍼입니다.
"""

import json
import re
from typing import Dict, Any, Optional, List
from pathlib import Path
from bs4 import BeautifulSoup
import requests
from playwright.sync_api import sync_playwright, Page, Browser
import logging
from datetime import datetime

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class PlatformScraper(BaseScraper):
    """설정 기반 플랫폼 스크래퍼"""
    
    def __init__(self, platform_name: str, config_path: Optional[str] = None):
        """
        플랫폼 스크래퍼 초기화
        
        Args:
            platform_name (str): 플랫폼 이름 (예: '11st', 'gmarket')
            config_path (Optional[str]): 설정 파일 경로
        """
        super().__init__(platform_name)
        
        # 설정 파일 로드
        if config_path is None:
            config_path = f"config/platforms/{platform_name}.json"
        
        self.config = self._load_config(config_path)
        self.selectors = self.config.get('selectors', {})
        self.wait_selectors = self.config.get('wait_selectors', [])
        self.timeout = self.config.get('timeout', 10000)
        self.user_agent = self.config.get('user_agent', '')
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        설정 파일을 로드합니다.
        
        Args:
            config_path (str): 설정 파일 경로
            
        Returns:
            Dict[str, Any]: 설정 데이터
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"설정 파일을 찾을 수 없습니다: {config_path}")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"설정 파일 파싱 오류: {e}")
            return {}
    
    def _find_element_by_selectors(self, soup: BeautifulSoup, selector_list: List[str]) -> Optional[str]:
        """
        여러 선택자 중 하나로 요소를 찾습니다.
        
        Args:
            soup (BeautifulSoup): 파싱된 HTML
            selector_list (List[str]): CSS 선택자 리스트
            
        Returns:
            Optional[str]: 찾은 텍스트 또는 None
        """
        for selector in selector_list:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        return None
    
    def _extract_number_from_text(self, text: str) -> float:
        """
        텍스트에서 숫자를 추출합니다.
        
        Args:
            text (str): 숫자가 포함된 텍스트
            
        Returns:
            float: 추출된 숫자
        """
        if not text:
            return 0.0
        
        # 숫자와 쉼표만 추출
        numbers = re.findall(r'[\d,]+', text)
        if numbers:
            # 쉼표 제거하고 숫자로 변환
            number_str = numbers[0].replace(',', '')
            return float(number_str)
        
        return 0.0
    
    def extract_price(self, html_content: str) -> float:
        """
        HTML에서 가격 정보를 추출합니다.
        할인가가 있으면 할인가를, 없으면 원가를 반환합니다.
        
        Args:
            html_content (str): HTML 내용
            
        Returns:
            float: 추출된 가격 (할인가 우선)
            
        Raises:
            ValueError: 가격 정보를 찾을 수 없는 경우
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        price_selectors = self.selectors.get('price', [])
        
        # 할인가 우선 추출 시도
        for selector in price_selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text().strip()
                price = self._extract_number_from_text(price_text)
                if price > 0:
                    return price
        
        # 할인가를 찾지 못한 경우 원가에서 추출
        original_price_selectors = self.selectors.get('original_price', [])
        for selector in original_price_selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text().strip()
                price = self._extract_number_from_text(price_text)
                if price > 0:
                    return price
        
        raise ValueError(f"가격 정보를 찾을 수 없습니다. 선택자: {price_selectors}")
    
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
        soup = BeautifulSoup(html_content, 'html.parser')
        title_selectors = self.selectors.get('title', [])
        
        title = self._find_element_by_selectors(soup, title_selectors)
        if not title:
            raise ValueError(f"제목 정보를 찾을 수 없습니다. 선택자: {title_selectors}")
        
        return title
    
    def extract_stock(self, html_content: str) -> int:
        """
        HTML에서 재고 정보를 추출합니다.
        
        Args:
            html_content (str): HTML 내용
            
        Returns:
            int: 추출된 재고 수량
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        stock_selectors = self.selectors.get('stock', [])
        
        stock_text = self._find_element_by_selectors(soup, stock_selectors)
        if not stock_text:
            return 0  # 재고 정보가 없으면 0 반환
        
        stock = int(self._extract_number_from_text(stock_text))
        return max(0, stock)  # 음수 방지
    
    def extract_original_price(self, html_content: str) -> Optional[float]:
        """
        HTML에서 원가를 추출합니다.
        
        Args:
            html_content (str): HTML 내용
            
        Returns:
            Optional[float]: 원가 (없으면 None)
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        original_price_selectors = self.selectors.get('original_price', [])
        
        original_price_text = self._find_element_by_selectors(soup, original_price_selectors)
        if not original_price_text:
            return None
        
        original_price = self._extract_number_from_text(original_price_text)
        return original_price if original_price > 0 else None
    
    def extract_discount_rate(self, html_content: str) -> Optional[float]:
        """
        HTML에서 할인율을 추출합니다.
        
        Args:
            html_content (str): HTML 내용
            
        Returns:
            Optional[float]: 할인율 (없으면 None)
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        discount_selectors = self.selectors.get('discount_rate', [])
        
        discount_text = self._find_element_by_selectors(soup, discount_selectors)
        if not discount_text:
            return None
        
        # % 기호 제거하고 숫자만 추출
        discount_match = re.search(r'(\d+(?:\.\d+)?)', discount_text)
        if discount_match:
            return float(discount_match.group(1))
        
        return None
    
    def extract_max_discount_price(self, html_content: str) -> Optional[float]:
        """
        HTML에서 최대 할인가를 추출합니다.
        
        Args:
            html_content (str): HTML 내용
            
        Returns:
            Optional[float]: 최대 할인가 (없으면 None)
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        max_discount_selectors = self.selectors.get('max_discount_price', [])
        
        max_discount_text = self._find_element_by_selectors(soup, max_discount_selectors)
        if not max_discount_text:
            return None
        
        max_discount_price = self._extract_number_from_text(max_discount_text)
        return max_discount_price if max_discount_price > 0 else None
    
    def extract_max_discount_rate(self, html_content: str) -> Optional[float]:
        """
        HTML에서 최대 할인율을 추출합니다.
        
        Args:
            html_content (str): HTML 내용
            
        Returns:
            Optional[float]: 최대 할인율 (없으면 None)
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        max_discount_rate_selectors = self.selectors.get('max_discount_rate', [])
        
        max_discount_rate_text = self._find_element_by_selectors(soup, max_discount_rate_selectors)
        if not max_discount_rate_text:
            return None
        
        # % 기호 제거하고 숫자만 추출
        discount_match = re.search(r'(\d+(?:\.\d+)?)', max_discount_rate_text)
        if discount_match:
            return float(discount_match.group(1))
        
        return None
    
    def extract_discount_info(self, html_content: str) -> Dict[str, Any]:
        """
        플랫폼별 특화 할인 정보를 추출합니다.
        
        Args:
            html_content (str): HTML 내용
            
        Returns:
            Dict[str, Any]: 할인 정보
        """
        discount_info = {
            'price': 0.0,
            'original_price': None,
            'discount_rate': None,
            'max_discount_price': None,
            'max_discount_rate': None,
            'is_discounted': False,
            'discount_amount': 0
        }
        
        # 기본 정보 추출
        discount_info['price'] = self.extract_price(html_content)
        discount_info['original_price'] = self.extract_original_price(html_content)
        discount_info['discount_rate'] = self.extract_discount_rate(html_content)
        discount_info['max_discount_price'] = self.extract_max_discount_price(html_content)
        discount_info['max_discount_rate'] = self.extract_max_discount_rate(html_content)
        
        # 네이버 스마트스토어 특화 처리
        if self.platform_name == 'naver_smartstore':
            discount_info = self._extract_naver_discount_info(html_content, discount_info)
        
        # 할인 여부 및 할인금액 계산
        if (discount_info['original_price'] and 
            discount_info['price'] > 0 and 
            discount_info['original_price'] > discount_info['price']):
            discount_info['is_discounted'] = True
            discount_info['discount_amount'] = discount_info['original_price'] - discount_info['price']
            
            # 할인율이 없으면 계산
            if not discount_info['discount_rate']:
                calculated_rate = self.calculate_discount_rate(
                    discount_info['price'], 
                    discount_info['original_price']
                )
                if calculated_rate > 0:
                    discount_info['discount_rate'] = calculated_rate
        
        return discount_info
    
    def _extract_naver_discount_info(self, html_content: str, base_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        네이버 스마트스토어 특화 할인 정보 추출
        
        Args:
            html_content (str): HTML 내용
            base_info (Dict[str, Any]): 기본 할인 정보
            
        Returns:
            Dict[str, Any]: 네이버 특화 할인 정보
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 네이버 스마트스토어 특화 선택자들
        naver_price_selectors = [
            '#finalDscPrcArea .price strong .value',
            '.price_area .sale_price strong',
            '.price_area .final_price strong',
            '.price_area .price strong',
            '.price strong .value'
        ]
        
        naver_original_selectors = [
            '.price_area .original_price_area .price',
            '.price_area .list_price',
            '.price_area .before_price',
            '.price_area .strike_price',
            '.original_price strong'
        ]
        
        naver_discount_selectors = [
            '.price_area .discount_rate_area .rate',
            '.price_area .sale_rate_area .rate',
            '.price_area .discount_rate',
            '.price_area .sale_rate',
            '.discount_rate'
        ]
        
        # 할인가 우선 추출
        for selector in naver_price_selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text().strip()
                price = self._extract_number_from_text(price_text)
                if price > 0:
                    base_info['price'] = price
                    self.logger.info(f"네이버 할인가 추출 ({selector}): {price:,}원")
                    break
        
        # 원가 추출
        for selector in naver_original_selectors:
            element = soup.select_one(selector)
            if element:
                original_text = element.get_text().strip()
                original_price = self._extract_number_from_text(original_text)
                if original_price > 0:
                    base_info['original_price'] = original_price
                    self.logger.info(f"네이버 원가 추출 ({selector}): {original_price:,}원")
                    break
        
        # 할인율 추출
        for selector in naver_discount_selectors:
            element = soup.select_one(selector)
            if element:
                discount_text = element.get_text().strip()
                discount_match = re.search(r'(\d+(?:\.\d+)?)', discount_text)
                if discount_match:
                    discount_rate = float(discount_match.group(1))
                    base_info['discount_rate'] = discount_rate
                    self.logger.info(f"네이버 할인율 추출 ({selector}): {discount_rate}%")
                    break
        
        return base_info
    
    def _extract_naver_prices_with_playwright(self, page) -> tuple:
        """
        Playwright를 사용하여 네이버 스마트스토어 가격 정보를 추출합니다.
        
        Args:
            page: Playwright 페이지 객체
            
        Returns:
            tuple: (price_text, original_price_text, discount_rate_text)
        """
        price_text = None
        original_price_text = None
        discount_rate_text = None
        
        # 할인가 우선 시도 (네이버 스마트스토어 특화)
        price_selectors = [
            '#finalDscPrcArea .price strong .value',
            '.price_area .sale_price strong',
            '.price_area .final_price strong',
            '.price_area .price strong',
            '.price strong .value'
        ]
        
        for selector in price_selectors:
            try:
                price_element = page.locator(selector).first
                if price_element and price_element.inner_text().strip():
                    price_text = price_element.inner_text().strip()
                    self.logger.info(f"네이버 할인가 추출 ({selector}): {price_text}")
                    break
            except:
                continue
        
        # 원가 추출 시도
        original_price_selectors = [
            '.price_area .original_price_area .price',
            '.price_area .list_price',
            '.price_area .before_price',
            '.price_area .strike_price',
            '.original_price strong'
        ]
        
        for selector in original_price_selectors:
            try:
                original_element = page.locator(selector).first
                if original_element and original_element.inner_text().strip():
                    original_price_text = original_element.inner_text().strip()
                    self.logger.info(f"네이버 원가 추출 ({selector}): {original_price_text}")
                    break
            except:
                continue
        
        # 할인율 추출 시도
        discount_selectors = [
            '.price_area .discount_rate_area .rate',
            '.price_area .sale_rate_area .rate',
            '.price_area .discount_rate',
            '.price_area .sale_rate',
            '.discount_rate'
        ]
        
        for selector in discount_selectors:
            try:
                discount_element = page.locator(selector).first
                if discount_element and discount_element.inner_text().strip():
                    discount_rate_text = discount_element.inner_text().strip()
                    self.logger.info(f"네이버 할인율 추출 ({selector}): {discount_rate_text}")
                    break
            except:
                continue
        
        return price_text, original_price_text, discount_rate_text
    
    def _extract_general_prices_with_playwright(self, page) -> tuple:
        """
        Playwright를 사용하여 일반적인 가격 정보를 추출합니다.
        
        Args:
            page: Playwright 페이지 객체
            
        Returns:
            tuple: (price_text, original_price_text, discount_rate_text)
        """
        price_text = None
        original_price_text = None
        discount_rate_text = None
        
        # 일반적인 가격 추출
        try:
            price_element = page.locator('.price strong .value').first
            if price_element and price_element.inner_text().strip():
                price_text = price_element.inner_text().strip()
                self.logger.info(f"일반 가격 추출: {price_text}")
        except:
            pass
        
        return price_text, original_price_text, discount_rate_text
    
    def get_discount_summary(self, url: str) -> Dict[str, Any]:
        """
        할인 정보 요약을 반환합니다.
        
        Args:
            url (str): 상품 URL
            
        Returns:
            Dict[str, Any]: 할인 정보 요약
        """
        try:
            result = self.scrape(url)
            
            if result.get('status') == 'success':
                price = result.get('price', 0)
                original_price = result.get('original_price')
                discount_rate = result.get('discount_rate', 0)
                
                summary = {
                    'url': url,
                    'title': result.get('title', ''),
                    'current_price': price,
                    'original_price': original_price,
                    'discount_rate': discount_rate,
                    'discount_amount': 0,
                    'is_discounted': False,
                    'timestamp': datetime.now().isoformat()
                }
                
                if original_price and price > 0:
                    summary['discount_amount'] = original_price - price
                    summary['is_discounted'] = original_price > price
                
                return summary
            else:
                return {
                    'url': url,
                    'error': result.get('error', 'Unknown error'),
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"할인 정보 요약 추출 실패: {e}")
            return {
                'url': url,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def scrape_with_requests(self, url: str) -> Dict[str, Any]:
        """
        requests를 사용하여 스크래핑합니다.
        
        Args:
            url (str): 스크래핑할 URL
            
        Returns:
            Dict[str, Any]: 스크래핑 결과
        """
        # 11번가 전용 헤더 설정
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.11st.co.kr/',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        # 쿠키 설정 (필요시)
        cookies = {
            # 11번가 로그인 쿠키 예시 (실제 사용 시 로그인 후 쿠키 값으로 교체)
            # 'PCID': 'your_pcid_here',
            # 'xecurepopup': '1',
        }
        
        try:
            response = requests.get(url, headers=headers, cookies=cookies, timeout=15)
            response.raise_for_status()
            
            html_content = response.text
            
            # 데이터 추출
            price = self.extract_price(html_content)
            title = self.extract_title(html_content)
            stock = self.extract_stock(html_content)
            original_price = self.extract_original_price(html_content)
            discount_rate = self.extract_discount_rate(html_content)
            max_discount_price = self.extract_max_discount_price(html_content)
            max_discount_rate = self.extract_max_discount_rate(html_content)
            
            # 할인율 계산 (직접 추출한 할인율이 없으면 계산)
            if discount_rate is None and original_price:
                discount_rate = self.calculate_discount_rate(price, original_price)
            
            result = {
                'url': url,
                'price': price,
                'title': title,
                'stock': stock,
                'original_price': original_price,
                'discount_rate': discount_rate or 0.0,
                'max_discount_price': max_discount_price,
                'max_discount_rate': max_discount_rate
            }
            
            return self.format_result(result)
            
        except requests.RequestException as e:
            self.logger.error(f"Requests 스크래핑 실패: {e}")
            raise
    
    def scrape_with_playwright(self, url: str) -> Dict[str, Any]:
        """
        Playwright를 사용하여 동적 웹사이트를 스크래핑합니다.
        
        Args:
            url (str): 스크래핑할 URL
            
        Returns:
            Dict[str, Any]: 스크래핑 결과
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # 플랫폼별 헤더 설정
            if self.platform_name == 'naver_smartstore':
                page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
                    'Referer': 'https://smartstore.naver.com/'
                })
            else:
                # 11번가 전용 헤더 설정
                page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
                    'Referer': 'https://www.11st.co.kr/'
                })
            
            try:
                # 페이지 로드
                self.logger.info(f"페이지 로딩 중: {url}")
                page.goto(url, wait_until='networkidle', timeout=self.timeout)
                
                # .price 셀렉터가 로드될 때까지 대기
                self.logger.info("가격 정보 로딩 대기 중...")
                try:
                    page.wait_for_selector('.price', timeout=10000)
                    self.logger.info("✅ .price 셀렉터 로드 완료")
                except Exception as e:
                    self.logger.warning(f"⚠️ .price 셀렉터 대기 실패: {e}")
                
                # 추가 대기 (동적 콘텐츠 로드 대기)
                page.wait_for_timeout(3000)
                
                # 필요한 요소들이 로드될 때까지 대기
                for selector in self.wait_selectors:
                    try:
                        page.wait_for_selector(selector, timeout=5000)
                        self.logger.info(f"✅ {selector} 로드 완료")
                    except:
                        self.logger.warning(f"⚠️ {selector} 로드 실패")
                
                # 플랫폼별 특화 가격 추출 로직
                price_text = None
                original_price_text = None
                discount_rate_text = None
                
                try:
                    if self.platform_name == 'naver_smartstore':
                        # 네이버 스마트스토어 특화 가격 추출
                        price_text, original_price_text, discount_rate_text = self._extract_naver_prices_with_playwright(page)
                    else:
                        # 일반적인 가격 추출
                        price_text, original_price_text, discount_rate_text = self._extract_general_prices_with_playwright(page)
                            
                except Exception as e:
                    self.logger.warning(f"가격 정보 직접 추출 실패: {e}")
                
                # HTML 내용 가져오기
                html_content = page.content()
                
                # 데이터 추출 (HTML 파싱)
                price = self.extract_price(html_content)
                title = self.extract_title(html_content)
                stock = self.extract_stock(html_content)
                original_price = self.extract_original_price(html_content)
                discount_rate = self.extract_discount_rate(html_content)
                max_discount_price = self.extract_max_discount_price(html_content)
                max_discount_rate = self.extract_max_discount_rate(html_content)
                
                # Playwright로 직접 추출한 값들로 우선 교체
                if price_text:
                    try:
                        price_from_innertext = float(price_text.replace(',', ''))
                        if price_from_innertext > 0:
                            price = price_from_innertext
                            self.logger.info(f"Playwright 할인가 사용: {price}")
                    except:
                        pass
                
                if original_price_text:
                    try:
                        original_from_innertext = float(original_price_text.replace(',', ''))
                        if original_from_innertext > 0:
                            original_price = original_from_innertext
                            self.logger.info(f"Playwright 원가 사용: {original_price}")
                    except:
                        pass
                
                if discount_rate_text:
                    try:
                        # % 기호 제거하고 숫자만 추출
                        discount_match = re.search(r'(\d+(?:\.\d+)?)', discount_rate_text)
                        if discount_match:
                            discount_rate = float(discount_match.group(1))
                            self.logger.info(f"Playwright 할인율 사용: {discount_rate}%")
                    except:
                        pass
                
                # 할인율이 없고 원가가 있으면 계산
                if discount_rate is None and original_price and price > 0:
                    calculated_discount_rate = self.calculate_discount_rate(price, original_price)
                    if calculated_discount_rate > 0:
                        discount_rate = calculated_discount_rate
                        self.logger.info(f"할인율 계산: {discount_rate}%")
                
                result = {
                    'url': url,
                    'price': price,
                    'title': title,
                    'stock': stock,
                    'original_price': original_price,
                    'discount_rate': discount_rate or 0.0,
                    'max_discount_price': max_discount_price,
                    'max_discount_rate': max_discount_rate
                }
                
                return self.format_result(result)
                
            except Exception as e:
                self.logger.error(f"Playwright 스크래핑 실패: {e}")
                raise
            finally:
                browser.close()
    
    def scrape(self, url: str, use_playwright: bool = True) -> Dict[str, Any]:
        """
        URL을 스크래핑합니다.
        
        Args:
            url (str): 스크래핑할 URL
            use_playwright (bool): Playwright 사용 여부
            
        Returns:
            Dict[str, Any]: 스크래핑 결과
        """
        try:
            if use_playwright:
                result = self.scrape_with_playwright(url)
            else:
                result = self.scrape_with_requests(url)
            
            self.log_scraping_result(url, result)
            return result
            
        except Exception as e:
            self.logger.error(f"스크래핑 실패: {e}")
            return {
                'platform': self.platform_name,
                'timestamp': datetime.now().isoformat(),
                'url': url,
                'status': 'error',
                'error': str(e)
            } 