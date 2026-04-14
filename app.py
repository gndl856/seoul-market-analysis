import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timedelta

# 1. 설정 및 인증키
st.set_page_config(page_title="서울 상권 분석 시스템", layout="wide")
API_KEY = "4d59784b56676e64363847736b5362" #

# 2. 분석 지역 설정 (이미지 image_416bfa.png 기준)
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

# --- [1. 유동인구 데이터 수집] ---
def get_subway_data(station_name):
    file_path = f"subway_{station_name}.csv"
    if os.path.exists(file_path):
        return pd.read_csv(file_path).reset_index(drop=True)
    
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
        final_df = final_df.sort_values('sort').drop('sort', axis=1).reset_index(drop=True)
        final_df.to_csv(file_path, index=False)
        return final_df
    return pd.DataFrame()

# --- [2. 개/폐업 데이터 수집 - 에러 수정 버전] ---
def get_store_data(station_name):
    file_path = f"store_{station_name}.csv"
    if os.path.exists(file_path): 
        return pd.read_csv(file_path).reset_index(drop=True)

    area_code = STATION_CONFIG[station_name]["code"]
    # 점포 데이터 API 서비스명 정확히 지정
    url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/VwsmTrdarStorQq/1/1000/20244"
    
    try:
        res = requests.get(url, timeout=5).json()
        if 'VwsmTrdarStorQq' in res:
            df = pd.DataFrame(res['VwsmTrdarStorQq']['row'])
            # 해당 상권 코드 데이터만 필터링
            area_df = df[df['TRDAR_CD'] == area_code].copy()
            
            # 에러 방지를 위해 실제 컬럼명이 있는지 확인 후 매핑
            cols = {
                'SVC_INDUTY_CD_NM': '업종명', 
                'STOR_CO': '점포수', 
                'OPN_STOR_CO': '개업', 
                'CLS_STOR_CO': '폐업'
            }
            
            if not area_df.empty:
                result = area_df[list(cols.keys())].rename(columns=cols)
                result.to_csv(file_path, index=False)
                return result
    except Exception as e:
        st.error(f"데이터 연결 오류: {e}")
    return pd.DataFrame()

# --- [UI 구성 및 가운데 정렬] ---
st.markdown("""
    <style>
        div[data-testid="stDataFrame"] td { text-align: center !important; }
        div[data-testid="stDataFrame"] th { text-align: center !important; }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("📍 지역 선택")
    sel_station = st.selectbox("분석 지역", STATIONS)
    st.markdown("---")
    st.success("배포가 완료되었습니다.")

st.title(f"🏙️ {sel_station} 상권 분석")
tab1, tab2 = st.tabs(["📈 유동인구", "🍕 업종별 개/폐업"])

with tab1:
    res1 = get_subway_data(sel_station)
    if not res1.empty:
        st.dataframe(res1, hide_index=True, use_container_width=True)
    else:
        st.info("데이터를 불러오는 중...")

with tab2:
    res2 = get_store_data(sel_station)
    if not res2.empty:
        # 개업/폐업 표도 가운데 정렬 적용
        st.dataframe(res2, hide_index=True, use_container_width=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("총 점포", f"{res2['점포수'].sum()}개")
        c2.metric("총 개업", f"{res2['개업'].sum()}개", delta_color="normal")
        c3.metric("총 폐업", f"{res2['폐업'].sum()}개", delta_color="inverse")
    else:
        st.warning("이 지역의 점포 데이터를 찾을 수 없습니다.")
