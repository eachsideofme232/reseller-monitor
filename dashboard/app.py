"""
리셀러 가격 모니터링 대시보드
Streamlit을 활용한 실시간 가격 비교 및 시각화
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import logging
from datetime import datetime
from pathlib import Path
import sys

# 프로젝트 루트 경로 추가
sys.path.append(str(Path(__file__).parent.parent))

from naver_api.product_monitor import ProductMonitor

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 페이지 설정
st.set_page_config(
    page_title="리셀러 가격 모니터링 대시보드",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .product-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def load_latest_results(results_dir: str = "results") -> dict:
    """최신 모니터링 결과를 로드합니다."""
    results_path = Path(results_dir)
    if not results_path.exists():
        return None
    
    # JSON 파일 중 가장 최신 파일 찾기
    json_files = list(results_path.glob("monitoring_results_*.json"))
    if not json_files:
        return None
    
    latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"결과 파일 로드 실패: {e}")
        return None


def create_price_comparison_chart(df: pd.DataFrame) -> go.Figure:
    """가격 비교 차트를 생성합니다."""
    fig = px.box(
        df, 
        x='product_name', 
        y='price',
        color='product_name',
        title='제품별 가격 분포',
        labels={'price': '가격 (원)', 'product_name': '제품명'}
    )
    
    fig.update_layout(
        height=400,
        showlegend=False
    )
    
    return fig


def create_discount_rate_chart(df: pd.DataFrame) -> go.Figure:
    """할인율 분포 차트를 생성합니다."""
    fig = px.histogram(
        df,
        x='discount_rate',
        color='product_name',
        title='할인율 분포',
        labels={'discount_rate': '할인율 (%)', 'product_name': '제품명'},
        nbins=20
    )
    
    fig.update_layout(
        height=400,
        showlegend=True
    )
    
    return fig


def create_top_resellers_table(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """최고 할인율 리셀러 테이블을 생성합니다."""
    if df.empty:
        return pd.DataFrame()
    
    # 할인율 기준으로 정렬하여 상위 N개 선택
    top_resellers = df.nlargest(top_n, 'discount_rate')
    
    # 표시할 컬럼만 선택
    display_columns = [
        'product_name', 'mall_name', 'price', 'original_price', 
        'discount_rate', 'discount_amount', 'title', 'product_link'
    ]
    
    return top_resellers[display_columns].copy()


def main():
    """메인 대시보드 함수"""
    
    # 헤더
    st.markdown('<h1 class="main-header">💰 리셀러 가격 모니터링 대시보드</h1>', unsafe_allow_html=True)
    
    # 사이드바
    st.sidebar.title("설정")
    
    # 실시간 모니터링 버튼
    if st.sidebar.button("🔄 실시간 모니터링 실행", type="primary"):
        with st.spinner("모니터링 중..."):
            try:
                monitor = ProductMonitor()
                results = monitor.monitor_all_products()
                
                # 결과 저장
                output_path = monitor.save_results(results)
                st.success(f"모니터링 완료! 결과 저장: {output_path}")
                
                # 세션 상태에 결과 저장
                st.session_state.latest_results = results
                st.session_state.monitoring_timestamp = datetime.now()
                
            except Exception as e:
                st.error(f"모니터링 실패: {e}")
    
    # 최신 결과 로드
    if 'latest_results' not in st.session_state:
        st.session_state.latest_results = load_latest_results()
    
    # 결과가 없으면 안내 메시지
    if not st.session_state.latest_results:
        st.warning("📊 모니터링 결과가 없습니다. 사이드바에서 '실시간 모니터링 실행' 버튼을 클릭하세요.")
        return
    
    # 모니터링 시간 표시
    monitoring_time = st.session_state.latest_results.get('monitoring_timestamp', '')
    if monitoring_time:
        st.info(f"📅 마지막 모니터링: {monitoring_time}")
    
    # 전체 통계
    total_products = st.session_state.latest_results.get('total_products', 0)
    total_resellers = st.session_state.latest_results.get('total_resellers', 0)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("📦 모니터링 제품 수", total_products)
    
    with col2:
        st.metric("🏪 발견된 리셀러 수", total_resellers)
    
    # DataFrame 생성
    monitor = ProductMonitor()
    df = monitor.get_dataframe(st.session_state.latest_results)
    
    if df.empty:
        st.warning("데이터가 없습니다.")
        return
    
    # 탭 생성
    tab1, tab2, tab3, tab4 = st.tabs(["📊 전체 현황", "💰 가격 분석", "🏆 최고 할인", "📋 상세 데이터"])
    
    with tab1:
        st.subheader("📊 전체 현황")
        
        # 제품별 요약 통계
        product_summary = df.groupby('product_name').agg({
            'price': ['count', 'mean', 'min', 'max'],
            'discount_rate': ['mean', 'min', 'max']
        }).round(2)
        
        st.write("**제품별 요약 통계**")
        st.dataframe(product_summary, use_container_width=True)
        
        # 가격 분포 차트
        col1, col2 = st.columns(2)
        
        with col1:
            fig_price = create_price_comparison_chart(df)
            st.plotly_chart(fig_price, use_container_width=True)
        
        with col2:
            fig_discount = create_discount_rate_chart(df)
            st.plotly_chart(fig_discount, use_container_width=True)
    
    with tab2:
        st.subheader("💰 가격 분석")
        
        # 제품별 선택
        selected_product = st.selectbox(
            "분석할 제품 선택",
            df['product_name'].unique()
        )
        
        if selected_product:
            product_df = df[df['product_name'] == selected_product].copy()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**{selected_product} 가격 통계**")
                
                # 기본 통계
                avg_price = product_df['price'].mean()
                min_price = product_df['price'].min()
                max_price = product_df['price'].max()
                avg_discount = product_df['discount_rate'].mean()
                
                st.metric("평균 가격", f"{avg_price:,.0f}원")
                st.metric("최저가", f"{min_price:,.0f}원")
                st.metric("최고가", f"{max_price:,.0f}원")
                st.metric("평균 할인율", f"{avg_discount:.1f}%")
            
            with col2:
                # 가격 분포 히스토그램
                fig = px.histogram(
                    product_df,
                    x='price',
                    title=f'{selected_product} 가격 분포',
                    labels={'price': '가격 (원)'},
                    nbins=15
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # 가격순 정렬된 리셀러 목록
            st.write(f"**{selected_product} 리셀러 목록 (가격순)**")
            
            # 링크가 포함된 데이터프레임 생성
            sorted_df = product_df.sort_values('price')[['mall_name', 'price', 'discount_rate', 'title', 'product_link']].copy()
            
            # 링크를 클릭 가능한 형태로 변환
            def make_clickable_link(url, text):
                if pd.isna(url) or url == '':
                    return text
                return f'<a href="{url}" target="_blank">{text}</a>'
            
            sorted_df['mall_name'] = sorted_df.apply(
                lambda row: make_clickable_link(row['product_link'], row['mall_name']), axis=1
            )
            
            # HTML로 렌더링
            st.write(sorted_df[['mall_name', 'price', 'discount_rate', 'title']].to_html(
                escape=False, 
                index=False,
                formatters={
                    'price': '{:,.0f}원'.format,
                    'discount_rate': '{:.1f}%'.format
                }
            ), unsafe_allow_html=True)
    
    with tab3:
        st.subheader("🏆 최고 할인 리셀러")
        
        # 상위 할인율 리셀러
        top_n = st.slider("표시할 리셀러 수", 5, 20, 10)
        top_resellers = create_top_resellers_table(df, top_n)
        
        if not top_resellers.empty:
            st.write(f"**상위 {top_n}개 최고 할인율 리셀러**")
            
            # 할인율에 따른 색상 적용
            def color_discount_rate(val):
                if val >= 20:
                    return 'background-color: #ffcdd2'  # 빨간색 (높은 할인)
                elif val >= 10:
                    return 'background-color: #fff3e0'  # 주황색 (중간 할인)
                else:
                    return 'background-color: #e8f5e8'  # 초록색 (낮은 할인)
            
            styled_df = top_resellers.style.applymap(
                color_discount_rate, subset=['discount_rate']
            ).format({
                'price': '{:,.0f}원',
                'original_price': '{:,.0f}원',
                'discount_rate': '{:.1f}%',
                'discount_amount': '{:,.0f}원'
            })
            
            # 링크가 포함된 최고 할인 리셀러 테이블
            display_df = top_resellers[['product_name', 'mall_name', 'price', 'original_price', 'discount_rate', 'discount_amount', 'title', 'product_link']].copy()
            
            # 링크를 클릭 가능한 형태로 변환
            def make_clickable_link(url, text):
                if pd.isna(url) or url == '':
                    return text
                return f'<a href="{url}" target="_blank">{text}</a>'
            
            display_df['mall_name'] = display_df.apply(
                lambda row: make_clickable_link(row['product_link'], row['mall_name']), axis=1
            )
            
            # HTML로 렌더링
            st.write(display_df[['product_name', 'mall_name', 'price', 'original_price', 'discount_rate', 'discount_amount', 'title']].to_html(
                escape=False, 
                index=False,
                formatters={
                    'price': '{:,.0f}원'.format,
                    'original_price': '{:,.0f}원'.format,
                    'discount_rate': '{:.1f}%'.format,
                    'discount_amount': '{:,.0f}원'.format
                }
            ), unsafe_allow_html=True)
    
    with tab4:
        st.subheader("📋 상세 데이터")
        
        # 필터링 옵션
        col1, col2 = st.columns(2)
        
        with col1:
            selected_products = st.multiselect(
                "제품 선택",
                df['product_name'].unique(),
                default=df['product_name'].unique()
            )
        
        with col2:
            min_discount = st.slider("최소 할인율 (%)", 0, 50, 0)
        
        # 필터링 적용
        filtered_df = df[
            (df['product_name'].isin(selected_products)) &
            (df['discount_rate'] >= min_discount)
        ].copy()
        
        if not filtered_df.empty:
            st.write(f"**필터링된 결과: {len(filtered_df)}개**")
            
            # 다운로드 버튼
            csv = filtered_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 CSV 다운로드",
                data=csv,
                file_name=f"reseller_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
            # 링크가 포함된 상세 데이터 테이블
            display_df = filtered_df[['product_name', 'mall_name', 'price', 'discount_rate', 'title', 'product_link']].copy()
            
            # 링크를 클릭 가능한 형태로 변환
            def make_clickable_link(url, text):
                if pd.isna(url) or url == '':
                    return text
                return f'<a href="{url}" target="_blank">{text}</a>'
            
            display_df['mall_name'] = display_df.apply(
                lambda row: make_clickable_link(row['product_link'], row['mall_name']), axis=1
            )
            
            # HTML로 렌더링
            st.write(display_df[['product_name', 'mall_name', 'price', 'discount_rate', 'title']].to_html(
                escape=False, 
                index=False,
                formatters={
                    'price': '{:,.0f}원'.format,
                    'discount_rate': '{:.1f}%'.format
                }
            ), unsafe_allow_html=True)
        else:
            st.warning("필터 조건에 맞는 데이터가 없습니다.")


if __name__ == "__main__":
    main() 