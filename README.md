# Reseller Monitor - 웹 스크래핑 도구

상품 정보를 자동으로 스크래핑하는 Python 도구입니다.

## 기능

- 상품 상세 페이지에서 가격, 재고, 제목, 타임스탬프 정보 추출
- requests + BeautifulSoup 기반의 정적 웹사이트 스크래핑
- Playwright 기반의 동적 웹사이트 스크래핑
- 커스텀 예외 처리 및 로깅

## 설치

1. 의존성 패키지 설치:
```bash
pip install -r requirements.txt
```

2. Playwright 브라우저 설치 (Playwright 사용 시):
```bash
playwright install
```

## 사용법

### 기본 사용법

```python
from scraper import scrape_product, ScrapeError

try:
    # 상품 URL로 스크래핑
    result = scrape_product("https://example.com/product/123")
    
    print(f"제목: {result['title']}")
    print(f"가격: {result['price']}원")
    print(f"재고: {result['stock']}개")
    print(f"스크래핑 시간: {result['timestamp']}")
    
except ScrapeError as e:
    print(f"스크래핑 오류: {e}")
```

### Playwright 사용 (동적 웹사이트용)

```python
from scraper import scrape_product_with_playwright

result = scrape_product_with_playwright("https://example.com/product/123")
```

## 함수 스펙

### `scrape_product(url: str) -> Dict[str, Any]`

**입력:**
- `url` (str): 스크래핑할 상품 상세 페이지 URL

**반환값:**
- `Dict[str, Any]`: 다음 필드를 포함한 딕셔너리
  - `price` (float): 상품 가격
  - `stock` (int): 재고 수량
  - `title` (str): 상품 제목
  - `timestamp` (datetime): 스크래핑 시점

**예외:**
- `ScrapeError`: 스크래핑 중 오류 발생 시

## 커스터마이징

실제 웹사이트에 맞게 다음 함수들의 CSS 선택자를 수정하세요:

- `_extract_price()`: 가격 정보 선택자
- `_extract_stock()`: 재고 정보 선택자  
- `_extract_title()`: 제목 정보 선택자

## 예시

```python
# 현재는 일반적인 선택자 사용 (.price, .stock, .title 등)
# 실제 웹사이트에 맞게 수정 필요
```

## 주의사항

1. 웹사이트의 이용약관을 준수하세요
2. 과도한 요청을 피하고 적절한 딜레이를 두세요
3. 실제 사용 시에는 웹사이트별로 선택자를 맞춤 설정해야 합니다 