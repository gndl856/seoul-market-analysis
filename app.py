import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# 1. 설정 및 인증키
st.set_page_config(page_title="서울 상권 분석 시스템", layout="wide")
API_KEY = "4d59784b56676e64363847736b5362"

# 2. 분석 대상 상권 설정 (지하철역 주변 주요 상권)
# 나중에 유동인구를 다시 넣을 때를 대비해 subway 이름도 남겨두었습니다.
MARKET_CONFIG = {
    "강남역": {"subway": "강남", "code": "3110141"},
    "잠실역": {"subway": "잠실(송파구청)", "code": "3110149"},
    "홍대입구역": {"subway": "홍대입구", "code": "3110040"},
    "신림역": {"subway": "신림", "code": "3110153"},
    "종로3가역": {"subway": "종로3가", "code": "3110011"},
    "을지로입구역": {"subway": "을지로입구", "code": "3110013"},
    "건대입구역": {"subway": "건대입구", "code": "3110115"},
    "합정역": {"subway": "합정", "code": "3110041"}
}

# --- [보존된 유동인구 분석 함수: 나중에 다시 활성화 가능] ---
def get_subway_data(station_name):
    # 이 함수는 현재 화면에 호출되지 않지만 코드는 그대로 유지합니다.
    target_name = MARKET_CONFIG[station_name]["subway"]
    rows = []
    for i in range(1, 6):
        date = (datetime.now() - timedelta(days=i*7 + 3)).strftime("%Y%m%d")
        url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/CardSubwayStatsNew/1/1000/{date}"
        try:
            res = requests.get(url).json()
            if 'CardSubwayStatsNew' in res:
                df = pd.DataFrame(res['CardSubwayStatsNew']['row'])
                stat = df[df['SBWY_STNS_NM'] == target_name]
                if not stat.empty:
                    total = int(stat['GTON_TNOPE'].sum()) + int(stat['GTOFF_TNOPE'].sum())
                    rows.append({"주차": f"{i}주 전", "유동인구": total})
        except: break
    return pd.DataFrame(rows)

# --- [개폐업 데이터 수집 함수] ---
def get_store_data(market_code):
    # 가장 안정적인 데이터 시점인 2024년 4분기 데이터 호출
    url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/VwsmTrdarStorQq/1/1000/20244"
    try:
        res = requests.get(url, timeout=10).json()
        if 'VwsmTrdarStorQq' in res:
            df = pd.DataFrame(res['VwsmTrdarStorQq']['row'])
            # 특정 상권 코드로 필터링
            target_df = df[df['TRDAR_CD'].astype(str) == str(market_code)].copy()
            if not target_df.empty:
                cols = {'SVC_INDUTY_CD_NM': '업종명', 'STOR_CO': '점포수', 'OPN_STOR_CO': '개업', 'CLS_STOR_CO': '폐업'}
                return target_df[list(cols.keys())].rename(columns=cols)
    except: pass
    return pd.DataFrame()

# --- [UI 구성] ---
st.markdown("<style>div[data-testid='stDataFrame'] td {text-align:center !important;} th {text-align:center !important;}</style>", unsafe_allow_html=True)

st.title("🍕 서울 주요 지역 개/폐업 현황 분석")
st.info("현재는 상권별 점포 데이터만 노출됩니다. (유동인구 분석 기능은 코드 내 보존됨)")

# 상단 지역 선택
selected_loc = st.selectbox("분석할 지역을 선택하세요", list(MARKET_CONFIG.keys()))
m_code = MARKET_CONFIG[selected_loc]["code"]

# 데이터 불러오기
with st.spinner(f'{selected_loc} 상권 데이터를 불러오는 중...'):
    res_store = get_store_data(m_code)

if not res_store.empty:
    # 1. 요약 지표 (Metric)
    c1, c2, c3 = st.columns(3)
    c1.metric("전체 점포수", f"{res_store['점포수'].sum():,}개")
    c2.metric("분기 개업", f"{res_store['개업'].sum():,}개", delta_color="normal")
    c3.metric("분기 폐업", f"{res_store['폐업'].sum():,}개", delta="-", delta_color="inverse")
    
    st.markdown("---")
    
    # 2. 세부 업종별 표
    st.subheader(f"📊 {selected_loc} 업종별 상세 현황")
    st.dataframe(res_store, hide_index=True, use_container_width=True)
else:
    st.error(f"❌ '{selected_loc}'의 데이터를 불러오지 못했습니다. 인증키 권한이나 서버 상태를 확인해 주세요.")
