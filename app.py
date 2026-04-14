import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# 1. 설정 및 인증키
st.set_page_config(page_title="서울 상권 분석 시스템", layout="wide")
API_KEY = "4d59784b56676e64363847736b5362"

# 2. 지하철역별 상권 코드 매핑 (직접 확인된 최신 코드들입니다)
LOCATION_CONFIG = {
    "강남역": {"subway": "강남", "market_code": "3110141"},
    "잠실역": {"subway": "잠실(송파구청)", "market_code": "3110149"},
    "홍대입구역": {"subway": "홍대입구", "market_code": "3110040"},
    "신림역": {"subway": "신림", "market_code": "3110153"},
    "종로3가역": {"subway": "종로3가", "market_code": "3110011"},
    "을지로입구역": {"subway": "을지로입구", "market_code": "3110013"},
    "건대입구역": {"subway": "건대입구", "market_code": "3110115"},
    "합정역": {"subway": "합정", "market_code": "3110041"}
}

# 3. 중앙 정렬 CSS
st.markdown("<style>div[data-testid='stDataFrame'] td {text-align:center !important;} th {text-align:center !important;}</style>", unsafe_allow_html=True)

st.title("🏙️ 지하철역 중심 상권 통합 분석")
selected_loc = st.selectbox("분석할 지역을 선택하세요", list(LOCATION_CONFIG.keys()))
config = LOCATION_CONFIG[selected_loc]

tab1, tab2 = st.tabs(["📈 유동인구 (지하철)", "🍕 개/폐업 (상권)"])

# --- [1탭: 유동인구] ---
with tab1:
    new_rows = []
    with st.spinner('지하철 데이터 수집 중...'):
        for i in range(1, 11): 
            target_date = (datetime.now() - timedelta(days=i*7 + 3)).strftime("%Y%m%d")
            url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/CardSubwayStatsNew/1/1000/{target_date}"
            try:
                res = requests.get(url, timeout=10).json() # 대기 시간 10초로 연장
                if 'CardSubwayStatsNew' in res:
                    df = pd.DataFrame(res['CardSubwayStatsNew']['row'])
                    stat_df = df[df['SBWY_STNS_NM'] == config["subway"]]
                    if not stat_df.empty:
                        total = int(stat_df['GTON_TNOPE'].sum()) + int(stat_df['GTOFF_TNOPE'].sum())
                        new_rows.append({"주차": f"{i}주 전", "날짜": target_date, "총 유동인구": total})
            except: break
    
    if new_rows:
        st.dataframe(pd.DataFrame(new_rows), hide_index=True, use_container_width=True)
    else:
        st.warning("지하철 데이터를 불러올 수 없습니다. 인증키를 확인해 주세요.")

# --- [2탭: 개/폐업] ---
with tab2:
    # 안내에 따라 1/1000 범위로 호출하되, 가장 안정적인 2024년 4분기 데이터 요청
    url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/VwsmTrdarStorQq/1/1000/20244"
    
    with st.spinner('상권 데이터 수집 중...'):
        try:
            # ⚠️ 핵심: 연결 대기 시간을 15초로 늘려 서버 응답 지연 해결
            response = requests.get(url, timeout=15)
            res = response.json()
            
            if 'VwsmTrdarStorQq' in res:
                raw_df = pd.DataFrame(res['VwsmTrdarStorQq']['row'])
                # 선택한 상권 코드만 필터링
                area_df = raw_df[raw_df['TRDAR_CD'].astype(str) == str(config["market_code"])].copy()
                
                if not area_df.empty:
                    cols = {'SVC_INDUTY_CD_NM': '업종명', 'STOR_CO': '점포수', 'OPN_STOR_CO': '개업', 'CLS_STOR_CO': '폐업'}
                    res2 = area_df[list(cols.keys())].rename(columns=cols)
                    st.dataframe(res2, hide_index=True, use_container_width=True)
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric("전체 점포", f"{res2['점포수'].sum()}개")
                    m2.metric("분기 개업", f"{res2['개업'].sum()}개")
                    m3.metric("분기 폐업", f"{res2['폐업'].sum()}개")
                else:
                    st.error(f"'{selected_loc}'의 상권 코드({config['market_code']})가 현재 호출 범위(1-1000번) 내에 없습니다.")
            else:
                st.error("상권 분석 API 응답에 문제가 있습니다. 인증키 권한을 다시 확인해 보세요.")
        except Exception as e:
            st.error(f"서버 연결 실패: {e}. 잠시 후 다시 시도해 주세요.")
