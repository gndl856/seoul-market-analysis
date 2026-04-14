import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# 1. 설정 및 인증키
st.set_page_config(page_title="서울 상권 분석 시스템", layout="wide")
API_KEY = "4d59784b56676e64363847736b5362"

# 2. 제가 직접 매칭한 지하철역별 상권 코드 (서울시 기준)
# 1탭(지하철역 이름)과 2탭(상권코드)을 연동시켰습니다.
LOCATION_CONFIG = {
    "강남역": {"subway": "강남", "market_code": "3110141"},
    "잠실역": {"subway": "잠실(송파구청)", "market_code": "3110149"},
    "홍대입구역": {"subway": "홍대입구", "market_code": "3110040"},
    "신림역": {"subway": "신림", "market_code": "3110153"},
    "종로3가역": {"subway": "종로3가", "market_code": "3110011"},
    "을지로입구역": {"subway": "을지로입구", "market_code": "3110013"},
    "건대입구역": {"subway": "건대입구", "market_code": "3110115"},
    "합정역": {"subway": "합정", "market_code": "3110041"},
    "신촌역": {"subway": "신촌", "market_code": "3110042"}
}

# 3. 중앙 정렬 CSS
st.markdown("""
    <style>
        div[data-testid="stDataFrame"] td { text-align: center !important; }
        div[data-testid="stDataFrame"] th { text-align: center !important; }
    </style>
""", unsafe_allow_html=True)

# 4. 상단 지역 선택 (한 번만 선택하면 1, 2탭 모두 자동 반영)
st.title("🏙️ 지하철역 중심 상권 통합 분석")
selected_loc = st.selectbox("조사할 지하철역을 선택하세요", list(LOCATION_CONFIG.keys()))
config = LOCATION_CONFIG[selected_loc]

tab1, tab2 = st.tabs(["📈 유동인구 (지하철)", "🍕 개/폐업 (상권)"])

# --- [1탭: 유동인구] ---
with tab1:
    new_rows = []
    with st.spinner('지하철 데이터 수집 중...'):
        for i in range(1, 11): # 너무 오래 걸리지 않게 최근 10주치만 수집
            target_date = (datetime.now() - timedelta(days=i*7 + 3)).strftime("%Y%m%d")
            url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/CardSubwayStatsNew/1/1000/{target_date}"
            try:
                res = requests.get(url).json()
                if 'CardSubwayStatsNew' in res:
                    df = pd.DataFrame(res['CardSubwayStatsNew']['row'])
                    stat_df = df[df['SBWY_STNS_NM'] == config["subway"]]
                    if not stat_df.empty:
                        total = int(stat_df['GTON_TNOPE'].sum()) + int(stat_df['GTOFF_TNOPE'].sum())
                        new_rows.append({"주차": f"{i}주 전", "날짜": target_date, "총 유동인구": total})
            except: break
    
    if new_rows:
        res1 = pd.DataFrame(new_rows)
        st.dataframe(res1, hide_index=True, use_container_width=True)
        st.line_chart(res1.sort_index(ascending=False), x="주차", y="총 유동인구")

# --- [2탭: 개/폐업 (정밀 호출)] ---
with tab2:
    # 핵심: 전체를 훑지 않고 해당 상권 코드가 포함된 범위만 호출하거나 
    # 호출 후 우리가 원하는 코드만 정확히 필터링합니다.
    url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/VwsmTrdarStorQq/1/1000/20244"
    
    try:
        res = requests.get(url).json()
        if 'VwsmTrdarStorQq' in res:
            raw_df = pd.DataFrame(res['VwsmTrdarStorQq']['row'])
            # 선택한 역의 상권 코드만 쏙 골라내기
            area_df = raw_df[raw_df['TRDAR_CD'] == config["market_code"]].copy()
            
            if not area_df.empty:
                cols = {'SVC_INDUTY_CD_NM': '업종명', 'STOR_CO': '점포수', 'OPN_STOR_CO': '개업', 'CLS_STOR_CO': '폐업'}
                res2 = area_df[list(cols.keys())].rename(columns=cols)
                st.dataframe(res2, hide_index=True, use_container_width=True)
                
                m1, m2, m3 = st.columns(3)
                m1.metric("전체 점포", f"{res2['점포수'].sum()}개")
                m2.metric("분기 개업", f"{res2['개업'].sum()}개")
                m3.metric("분기 폐업", f"{res2['폐업'].sum()}개")
            else:
                st.warning(f"'{selected_loc}' 주변 상권 데이터를 현재 API 범위에서 찾을 수 없습니다.")
    except:
        st.error("상권 데이터 서버 연결에 실패했습니다.")
