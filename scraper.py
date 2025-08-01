"""
웹 스크래핑을 위한 모듈
상품 정보를 추출하는 함수들을 포함합니다.
"""

from typing import Dict, Any
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScrapeError(Exception):
    """웹 스크래핑 중 발생하는 예외를 처리하기 위한 커스텀 예외 클래스"""
    
    def __init__(self, message: str, original_exception: Exception = None):
        self.message = message
        self.original_exception = original_exception
        super().__init__(self.message)
    
    def __str__(self):
        if self.original_exception:
            return f"{self.message} (원본 예외: {self.original_exception})"
        return self.message


def scrape_product(url: str) -> Dict[str, Any]:
    """
    상품 상세 페이지에서 가격, 재고, 제목, 타임스탬프 정보를 스크래핑합니다.
    
    Args:
        url (str): 스크래핑할 상품 상세 페이지의 URL
        
    Returns:
        Dict[str, Any]: 스크래핑된 상품 정보를 담은 딕셔너리
            - price (float): 상품 가격
            - stock (int): 재고 수량
            - title (str): 상품 제목
            - timestamp (datetime): 스크래핑 시점의 타임스탬프
            
    Raises:
        ScrapeError: 스크래핑 중 오류가 발생한 경우
        
    Example:
        >>> result = scrape_product("https://example.com/product/123")
        >>> print(result)
        {
            'price': 29900.0,
            'stock': 5,
            'title': '상품명',
            'timestamp': datetime(2024, 1, 1, 12, 0, 0)
        }
    """
    try:
        # 1. HTTP 요청 (requests 사용)
        logger.info(f"URL 요청 시작: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # 2. HTML 파싱 (BeautifulSoup 사용)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 3. 데이터 추출
        # TODO: 실제 웹사이트 구조에 맞게 선택자를 수정해야 합니다
        price = _extract_price(soup)
        stock = _extract_stock(soup)
        title = _extract_title(soup)
        timestamp = datetime.now()
        
        # 4. 결과 반환
        result = {
            'price': price,
            'stock': stock,
            'title': title,
            'timestamp': timestamp
        }
        
        logger.info(f"스크래핑 완료: {title} - {price}원, 재고: {stock}개")
        return result
        
    except requests.RequestException as e:
        raise ScrapeError(f"HTTP 요청 실패: {url}", e)
    except Exception as e:
        raise ScrapeError(f"스크래핑 중 예상치 못한 오류 발생: {url}", e)


def _extract_price(soup: BeautifulSoup) -> float:
    """
    HTML에서 가격 정보를 추출합니다.
    
    Args:
        soup (BeautifulSoup): 파싱된 HTML 객체
        
    Returns:
        float: 추출된 가격
        
    Raises:
        ScrapeError: 가격 정보를 찾을 수 없는 경우
    """
    try:
        # TODO: 실제 웹사이트의 가격 선택자로 수정
        price_element = soup.select_one('.price, .product-price, [data-price]')
        if not price_element:
            raise ScrapeError("가격 정보를 찾을 수 없습니다")
        
        # 가격 텍스트에서 숫자만 추출
        price_text = price_element.get_text().strip()
        price = float(''.join(filter(str.isdigit, price_text)))
        return price
        
    except (ValueError, AttributeError) as e:
        raise ScrapeError("가격 정보 파싱 실패", e)


def _extract_stock(soup: BeautifulSoup) -> int:
    """
    HTML에서 재고 정보를 추출합니다.
    
    Args:
        soup (BeautifulSoup): 파싱된 HTML 객체
        
    Returns:
        int: 추출된 재고 수량
        
    Raises:
        ScrapeError: 재고 정보를 찾을 수 없는 경우
    """
    try:
        # TODO: 실제 웹사이트의 재고 선택자로 수정
        stock_element = soup.select_one('.stock, .inventory, [data-stock]')
        if not stock_element:
            # 재고 정보가 없는 경우 기본값 반환
            return 0
        
        # 재고 텍스트에서 숫자만 추출
        stock_text = stock_element.get_text().strip()
        stock = int(''.join(filter(str.isdigit, stock_text)))
        return stock
        
    except (ValueError, AttributeError) as e:
        raise ScrapeError("재고 정보 파싱 실패", e)


def _extract_title(soup: BeautifulSoup) -> str:
    """
    HTML에서 상품 제목을 추출합니다.
    
    Args:
        soup (BeautifulSoup): 파싱된 HTML 객체
        
    Returns:
        str: 추출된 상품 제목
        
    Raises:
        ScrapeError: 제목 정보를 찾을 수 없는 경우
    """
    try:
        # TODO: 실제 웹사이트의 제목 선택자로 수정
        title_element = soup.select_one('.title, .product-title, h1')
        if not title_element:
            raise ScrapeError("상품 제목을 찾을 수 없습니다")
        
        title = title_element.get_text().strip()
        return title
        
    except AttributeError as e:
        raise ScrapeError("제목 정보 파싱 실패", e)


# Playwright를 사용한 대안 함수 (더 복잡한 동적 웹사이트용)
def scrape_product_with_playwright(url: str) -> Dict[str, Any]:
    """
    Playwright를 사용하여 동적 웹사이트에서 상품 정보를 스크래핑합니다.
    
    Args:
        url (str): 스크래핑할 상품 상세 페이지의 URL
        
    Returns:
        Dict[str, Any]: 스크래핑된 상품 정보를 담은 딕셔너리
        
    Raises:
        ScrapeError: 스크래핑 중 오류가 발생한 경우
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # 페이지 로드
            page.goto(url, wait_until='networkidle')
            
            # 데이터 추출
            price = page.locator('.price').text_content()
            stock = page.locator('.stock').text_content()
            title = page.locator('.title').text_content()
            timestamp = datetime.now()
            
            browser.close()
            
            return {
                'price': float(''.join(filter(str.isdigit, price))),
                'stock': int(''.join(filter(str.isdigit, stock))),
                'title': title.strip(),
                'timestamp': timestamp
            }
            
    except Exception as e:
        raise ScrapeError(f"Playwright 스크래핑 실패: {url}", e)


if __name__ == "__main__":
    # 테스트 코드
    try:
        # 예시 URL (실제 테스트 시 유효한 URL로 변경)
        test_url = "https://example.com/product/123"
        result = scrape_product(test_url)
        print("스크래핑 결과:", result)
    except ScrapeError as e:
        print(f"스크래핑 오류: {e}")
    except Exception as e:
        print(f"예상치 못한 오류: {e}") 