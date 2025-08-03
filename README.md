# 💰 리셀러 가격 모니터링 시스템

네이버 쇼핑 검색 API를 활용하여 **오딧세이 블랙/로맨틱 2종** 상품군의 리셀러 판매가를 모니터링하고, 정상가 대비 할인율을 계산하여 **Streamlit 대시보드**로 시각화하는 시스템입니다.

## 🎯 주요 기능

- **네이버 쇼핑 API 연동**: 실시간 상품 검색 및 가격 정보 수집
- **리셀러 필터링**: 중고품, 리퍼 등 제외하고 신상품 리셀러만 추출
- **할인율 계산**: 정가 대비 할인율 자동 계산
- **Streamlit 대시보드**: 실시간 가격 비교 및 시각화
- **데이터 저장**: JSON/CSV 형태로 결과 저장

## 📦 설치 및 설정

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 네이버 API 키 설정

`.env` 파일에 네이버 개발자 센터에서 발급받은 API 키를 설정합니다:

```env
NAVER_CLIENT_ID=your_client_id_here
NAVER_CLIENT_SECRET=your_client_secret_here
```

### 3. 네이버 API 키 발급 방법

1. [네이버 개발자 센터](https://developers.naver.com/) 접속
2. 애플리케이션 등록
3. "Application > 애플리케이션 등록" 메뉴에서 새 애플리케이션 생성
4. "검색" API 서비스 추가
5. Client ID와 Client Secret 복사하여 `.env` 파일에 설정

## 🚀 사용 방법

### 1. 기본 모니터링 실행

```bash
python run_monitoring.py
```

### 2. Streamlit 대시보드 실행

```bash
python run_monitoring.py --dashboard
```

또는 직접 대시보드 실행:

```bash
streamlit run dashboard/app.py
```

### 3. 설정 파일 커스터마이징

`data/product_config.json` 파일에서 모니터링할 제품과 설정을 수정할 수 있습니다:

```json
{
  "target_products": [
    {
      "name": "오딧세이 블랙 2종",
      "keyword": "오딧세이 블랙 2종",
      "original_price": 79800
    },
    {
      "name": "오딧세이 로맨틱 2종",
      "keyword": "오딧세이 로맨틱 2종",
      "original_price": 59800
    }
  ],
  "monitoring_settings": {
    "max_results_per_product": 100,
    "exclude_keywords": ["중고", "사용감", "리퍼"],
    "min_price_threshold": 10000
  }
}
```

## 📊 대시보드 기능

### 1. 전체 현황
- 제품별 요약 통계
- 가격 분포 차트
- 할인율 분포 히스토그램

### 2. 가격 분석
- 제품별 상세 가격 통계
- 가격 분포 시각화
- 리셀러 목록 (가격순)

### 3. 최고 할인 리셀러
- 할인율 기준 상위 리셀러
- 색상 코딩된 할인율 표시

### 4. 상세 데이터
- 필터링 및 검색 기능
- CSV 다운로드
- 상세 리셀러 정보

## 📁 프로젝트 구조

```
resellerMonitor/
├── naver_api/                 # 네이버 API 모듈
│   ├── __init__.py
│   ├── naver_shopping_api.py  # 네이버 쇼핑 API 클라이언트
│   └── product_monitor.py     # 제품 모니터링 로직
├── dashboard/                 # Streamlit 대시보드
│   ├── app.py                # 메인 대시보드 애플리케이션
│   └── components/           # 대시보드 컴포넌트
├── data/                     # 설정 및 데이터
│   └── product_config.json   # 제품 설정 파일
├── results/                  # 모니터링 결과 저장
├── .env                      # 환경변수 (API 키)
├── run_monitoring.py         # 메인 실행 스크립트
└── requirements.txt          # 의존성 패키지
```

## 🔧 주요 모듈 설명

### NaverShoppingAPI
- 네이버 쇼핑 검색 API 클라이언트
- 상품 검색 및 가격 정보 추출
- 페이지네이션 지원

### ProductMonitor
- 제품별 모니터링 로직
- 리셀러 필터링
- 할인율 계산
- 결과 저장

### Streamlit Dashboard
- 실시간 가격 비교 시각화
- 인터랙티브 차트 및 그래프
- 데이터 필터링 및 다운로드

## 📈 모니터링 결과 예시

```
💰 리셀러 가격 모니터링 결과 요약
============================================================
📦 모니터링 제품 수: 2
🏪 발견된 리셀러 수: 45
📅 모니터링 시간: 2024-01-15T14:30:00

📦 오딧세이 블랙 2종
   💰 정가: 79,800원
   🏪 리셀러 수: 23개
   🔥 최저가: 65,000원 (18.5% 할인) - 쇼핑몰A

📦 오딧세이 로맨틱 2종
   💰 정가: 59,800원
   🏪 리셀러 수: 22개
   🔥 최저가: 48,500원 (18.9% 할인) - 쇼핑몰B
============================================================
```

## ⚠️ 주의사항

1. **API 호출 제한**: 네이버 API는 일일 호출 제한이 있으므로 과도한 사용을 피해주세요.
2. **데이터 정확성**: 검색 결과는 실시간으로 변동될 수 있습니다.
3. **리셀러 식별**: 자동 필터링이 완벽하지 않을 수 있으므로 결과를 검토해주세요.

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해주세요. 