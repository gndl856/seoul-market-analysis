import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timedelta

# 1. 설정 및 인증키
st.set_page_config(page_title="서울 상권 분석 시스템", layout="wide")
API_KEY = "4d59784b56676e64363847736b5362" #

# 2. 분석 지역 설정 (지하철역 이름과 상권 코드를 정확히 매칭)
# 상권 코드는 서울시 상권분석 서비스(image_410de3.png) 기준입니다.
STATION_CONFIG = {
    "홍대": {"subway": "홍대입구", "code": "3110040"},
    "합정": {"subway": "합정", "code": "3110041"},
    "신촌": {"subway": "신촌", "code": "3110042"},
    "신림": {"subway": "신림", "code": "3110153"},
    "서울대입구": {"subway": "서울대입구(관악구청)", "code": "3110155"},
    "을지로": {"subway": "을지로입구", "code": "3110013"},
    "종로": {"subway": "종로3가", "code": "3110011"},
    "강남": {"subway": "강남", "code": "3110141"},
    "건대": {"subway": "건대입구", "code": "3110115"},
    "방이역": {"subway": "방이", "code": "3110173"},
    "잠실": {"subway": "잠실(송파구청)", "code": "3110149"}
}
STATIONS = list(STATION_CONFIG.keys())

# --- [데이터 수집 로직] ---

def get_subway_data(station_name):
    target_name = STATION_CONFIG[station_name]["subway"]
    new_rows = []
    for i in range(1, 16):
        label = f"{i}주 전"
        target_date = (datetime.now() - timedelta(days=i*7 + 3)).strftime("%Y%m%d")
        url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/CardSubwayStatsNew/1/1000/{target_date}"
        try:
            res = requests.get(url, timeout=3).json()
            if 'CardSubwayStatsNew' in res:
                df = pd.DataFrame(res['CardSubwayStatsNew']['row'])
                stat_df = df[df['SBWY_STNS_NM'] == target_name]
                if not stat_df.empty:
                    total = stat_df['GTON_TNOPE'].astype(int).sum() + stat_df['GTOFF_TNOPE'].astype(int).sum()
                    new_rows.append({"주차": label, "날짜": target_date, "총 유동인구": total})
            else: break
        except: break

    if new_rows:
        final_df = pd.DataFrame(new_rows)
        final_df['sort'] = final_df['주차'].str.extract('(\d+)').astype(int)
        return final_df.sort_values('sort').drop('sort', axis=1).reset_index(drop=True)
    return pd.DataFrame()

def get_store_data(station_name):
    area_code = STATION_CONFIG[station_name]["code"]
    # 2024년 4분기 데이터를 우선 호출 (데이터 동기화 문제 방지)
    url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/VwsmTrdarStorQq/1/1000/20244"
    
    try:
        res = requests.get(url, timeout=5).json()
        if 'VwsmTrdarStorQq' in res:
            df = pd.DataFrame(res['VwsmTrdarStorQq']['row'])
            # 상권 코드(TRDAR_CD)가 문자열일 수 있어 문자열로 변환 후 비교
            area_df = df[df['TRDAR_CD'].astype(str) == str(area_code)].copy()
            
            if not area_df.empty:
                cols = {'SVC_INDUTY_CD_NM': '업종명', 'STOR_CO': '점포수', 'OPN_STOR_CO': '개업', 'CLS_STOR_CO': '폐업'}
                return area_df[list(cols.keys())].rename(columns=cols)
    except: pass
    return pd.DataFrame()

# --- [UI 구성] ---

st.markdown("""
    <style>
        div[data-testid="stDataFrame"] td { text-align: center !important; }
        div[data-testid="stDataFrame"] th { text-align: center !important; }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("📍 지역 선택")
    sel_station = st.selectbox("분석 지역", STATIONS)

st.title(f"🏙️ {sel_station} 상권 상세 분석")
tab1, tab2 = st.tabs(["📈 유동인구 (15주)", "🍕 업종별 개/폐업"])

with tab1:
    res1 = get_subway_data(sel_station)
    if not res1.empty:
        st.dataframe(res1, hide_index=True, use_container_width=True)
        st.markdown("---")
        st.subheader("📊 최근 5주 유동인구 추이")
        chart_data = res1.head(5).copy()
        chart_data['n'] = chart_data['주차'].str.extract('(\d+)').astype(int)
        chart_data = chart_data.sort_values('n', ascending=False)
        st.line_chart(data=chart_data, x='주차', y='총 유동인구', color="#FF4B4B")
    else:
        st.warning("지하철 데이터를 불러올 수 없습니다.")

with tab2:
    res2 = get_store_data(sel_station)
    if not res2.empty:
        st.dataframe(res2, hide_index=True, use_container_width=True)
        st.markdown("---")
        m1, m2, m3 = st.columns(3)
        m1.metric("전체 점포", f"{res2['점포수'].sum()}개")
        m2.metric("이번 분기 개업", f"{res2['개업'].sum()}개")
        m3.metric("이번 분기 폐업", f"{res2['폐업'].sum()}개")
    else:
        st.error(f"'{sel_station}' 지역의 상권 코드({STATION_CONFIG[sel_station]['code']})에 해당하는 데이터를 찾을 수 없습니다.")
