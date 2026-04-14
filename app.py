import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# 1. 설정 및 인증키
st.set_page_config(page_title="서울 상권 분석 시스템", layout="wide")
API_KEY = "4d59784b56676e64363847736b5362" #

# 2. 데이터 매핑 (탭별 독립 관리)
# [1탭용] 지하철역 리스트
SUBWAY_LIST = {
    "강남역": "강남", "잠실역": "잠실(송파구청)", "홍대입구역": "홍대입구", 
    "신림역": "신림", "종로3가역": "종로3가", "을지로입구역": "을지로입구",
    "건대입구역": "건대입구", "합정역": "합정", "신촌역": "신촌"
}

# [2탭용] 상권 분석 코드 (서울시 상권분석 서비스 기준)
MARKET_LIST = {
    "강남역 상권": "3110141",
    "잠실역 상권": "3110149",
    "홍대입구역 상권": "3110040",
    "신림역 상권": "3110153",
    "종로3가역 상권": "3110011",
    "을지로입구역 상권": "3110013",
    "가로수길": "3110134",
    "방이동 먹자골목": "3110173"
}

# --- [UI 설정] ---
st.markdown("""
    <style>
        div[data-testid="stDataFrame"] td { text-align: center !important; }
        div[data-testid="stDataFrame"] th { text-align: center !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🏙️ 서울 상권·교통 복합 분석 시스템")
tab1, tab2 = st.tabs(["📈 지하철 유동인구", "🍕 업종별 개/폐업"])

# --- [TAB 1: 지하철 유동인구] ---
with tab1:
    st.subheader("📍 역별 유동인구 추이")
    sel_subway = st.selectbox("분석할 지하철역을 선택하세요", list(SUBWAY_LIST.keys()))
    target_name = SUBWAY_LIST[sel_subway]
    
    new_rows = []
    with st.spinner('데이터 수집 중...'):
        for i in range(1, 16):
            target_date = (datetime.now() - timedelta(days=i*7 + 3)).strftime("%Y%m%d")
            url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/CardSubwayStatsNew/1/1000/{target_date}"
            try:
                res = requests.get(url, timeout=3).json()
                if 'CardSubwayStatsNew' in res:
                    df = pd.DataFrame(res['CardSubwayStatsNew']['row'])
                    stat_df = df[df['SBWY_STNS_NM'] == target_name]
                    if not stat_df.empty:
                        total = stat_df['GTON_TNOPE'].astype(int).sum() + stat_df['GTOFF_TNOPE'].astype(int).sum()
                        new_rows.append({"주차": f"{i}주 전", "날짜": target_date, "총 유동인구": total})
            except: break

    if new_rows:
        res1 = pd.DataFrame(new_rows)
        st.dataframe(res1, hide_index=True, use_container_width=True)
        
        # 5주 그래프
        st.markdown("---")
        st.subheader(f"📊 {sel_subway} 최근 5주 추이")
        chart_data = res1.head(5).copy()
        chart_data['n'] = chart_data['주차'].str.extract('(\d+)').astype(int)
        st.line_chart(data=chart_data.sort_values('n', ascending=False), x='주차', y='총 유동인구', color="#FF4B4B")

# --- [TAB 2: 개/폐업 분석] ---
with tab2:
    st.subheader("🍔 상권별 점포 통계")
    sel_market = st.selectbox("분석할 상권 구역을 선택하세요", list(MARKET_LIST.keys()))
    area_code = MARKET_LIST[sel_market]
    
    # 상권분석 API 호출 (가장 안정적인 2024년 4분기 기준)
    url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/VwsmTrdarStorQq/1/1000/20244"
    
    try:
        res = requests.get(url, timeout=5).json()
        if 'VwsmTrdarStorQq' in res:
            df = pd.DataFrame(res['VwsmTrdarStorQq']['row'])
            area_df = df[df['TRDAR_CD'].astype(str) == str(area_code)].copy()
            
            if not area_df.empty:
                cols = {'SVC_INDUTY_CD_NM': '업종명', 'STOR_CO': '점포수', 'OPN_STOR_CO': '개업', 'CLS_STOR_CO': '폐업'}
                res2 = area_df[list(cols.keys())].rename(columns=cols)
                st.dataframe(res2, hide_index=True, use_container_width=True)
                
                # 메트릭 표시
                st.markdown("---")
                m1, m2, m3 = st.columns(3)
                m1.metric("전체 점포", f"{res2['점포수'].sum()}개")
                m2.metric("분기 개업", f"{res2['개업'].sum()}개")
                m3.metric("분기 폐업", f"{res2['폐업'].sum()}개")
            else:
                st.warning(f"'{sel_market}'에 해당하는 데이터가 현재 분기에 없습니다.")
    except:
        st.error("데이터 서버 연결에 실패했습니다.")
