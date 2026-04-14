import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# 1. 설정 및 인증키
st.set_page_config(page_title="서울 상권 분석 시스템", layout="wide")
API_KEY = "4d59784b56676e64363847736b5362"

# 2. 탭별 독립 지역 데이터 (데이터가 확실히 확인되는 곳 위주)
# [1탭용] 지하철 유동인구 기준
SUBWAY_MAP = {
    "강남역": "강남", "잠실역": "잠실(송파구청)", "홍대입구역": "홍대입구", 
    "신림역": "신림", "종로3가역": "종로3가", "건대입구역": "건대입구",
    "서울대입구역": "서울대입구(관악구청)", "합정역": "합정"
}

# [2탭용] 개/폐업 상권 코드 기준 (데이터 노출 확률이 높은 대표 상권들)
MARKET_MAP = {
    "강남역": "3110141",
    "잠실역": "3110149",
    "홍대입구역": "3110040",
    "신림역": "3110153",
    "종로3가역": "3110011",
    "신천역(잠실새내)": "3110042",
    "연남동(홍대인근)": "3110039",
    "가로수길": "3110134"
}

# 3. CSS 적용 (가운데 정렬)
st.markdown("""
    <style>
        div[data-testid="stDataFrame"] td { text-align: center !important; }
        div[data-testid="stDataFrame"] th { text-align: center !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🏙️ 서울 상권·교통 복합 분석 대시보드")
tab1, tab2 = st.tabs(["📈 지하철 유동인구 추이", "🍕 업종별 개/폐업 현황"])

# --- [1탭: 지하철 유동인구 분석] ---
with tab1:
    st.subheader("📍 역별 유동인구")
    sel_sub = st.selectbox("분석할 지하철역 선택", list(SUBWAY_MAP.keys()), key="sub_sel")
    target_name = SUBWAY_MAP[sel_sub]
    
    new_rows = []
    with st.spinner('유동인구 데이터 수집 중...'):
        for i in range(1, 16):
            # 최근 15주간 동일 요일 기준 (화요일 기준 보정)
            target_date = (datetime.now() - timedelta(days=i*7 + 3)).strftime("%Y%m%d")
            url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/CardSubwayStatsNew/1/1000/{target_date}"
            try:
                res = requests.get(url, timeout=3).json()
                if 'CardSubwayStatsNew' in res:
                    df = pd.DataFrame(res['CardSubwayStatsNew']['row'])
                    stat_df = df[df['SBWY_STNS_NM'] == target_name]
                    if not stat_df.empty:
                        total = int(stat_df['GTON_TNOPE'].sum()) + int(stat_df['GTOFF_TNOPE'].sum())
                        new_rows.append({"주차": f"{i}주 전", "날짜": target_date, "유동인구": total})
            except: break

    if new_rows:
        res_df = pd.DataFrame(new_rows)
        st.dataframe(res_df, hide_index=True, use_container_width=True)
        
        st.markdown("---")
        st.subheader("📊 최근 5주 추이 그래프")
        chart_data = res_df.head(5).copy()
        chart_data['n'] = chart_data['주차'].str.extract('(\d+)').astype(int)
        st.line_chart(data=chart_data.sort_values('n', ascending=False), x='주차', y='유동인구', color="#FF4B4B")

# --- [2탭: 개/폐업 분석] ---
with tab2:
    st.subheader("🍔 상권별 점포 통계")
    sel_mkt = st.selectbox("분석할 상권 구역 선택", list(MARKET_MAP.keys()), key="mkt_sel")
    area_code = MARKET_MAP[sel_mkt]
    
    # 2024년 4분기 데이터 (현재 가장 안정적으로 조회되는 시점)
    url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/VwsmTrdarStorQq/1/1000/20244"
    
    with st.spinner('상권 데이터 수집 중...'):
        try:
            res = requests.get(url, timeout=5).json()
            if 'VwsmTrdarStorQq' in res:
                raw_df = pd.DataFrame(res['VwsmTrdarStorQq']['row'])
                # 코드 타입을 문자열로 맞춰서 필터링
                target_df = raw_df[raw_df['TRDAR_CD'].astype(str) == str(area_code)].copy()
                
                if not target_df.empty:
                    cols = {'SVC_INDUTY_CD_NM': '업종명', 'STOR_CO': '점포수', 'OPN_STOR_CO': '개업', 'CLS_STOR_CO': '폐업'}
                    final_res = target_df[list(cols.keys())].rename(columns=cols)
                    st.dataframe(final_res, hide_index=True, use_container_width=True)
                    
                    st.markdown("---")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("전체 점포", f"{final_res['점포수'].sum()}개")
                    c2.metric("분기 개업", f"{final_res['개업'].sum()}개")
                    c3.metric("분기 폐업", f"{final_res['폐업'].sum()}개")
                else:
                    st.warning(f"⚠️ '{sel_mkt}'(코드:{area_code})의 현재 분기 데이터가 없습니다. 다른 지역을 선택해 보세요.")
        except:
            st.error("❌ 서버 연결 실패 또는 인증키 한도 초과입니다.")
