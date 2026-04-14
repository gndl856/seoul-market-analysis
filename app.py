import streamlit as st
import requests
import pandas as pd

# 1. 설정 및 데이터 매핑
API_KEY = "4d59784b56676e64363847736b5362"

STATIONS = {
    "홍대입구역": "11440660", "합정역": "11440610", "신촌역": "11410585",
    "신림역": "11620695", "서울대입구역": "11620595", "을지로3가역": "11140605",
    "종로3가역": "11110615", "강남역": "11680640", "건대입구역": "11215710",
    "방이역": "11710562", "잠실역": "11710710"
}

st.set_page_config(page_title="서울 상권 분석 툴", layout="wide")
st.title("🚇 지하철역 주변 상권 개폐업 분석 (2020~2025)")

# 2. 데이터 호출 함수
def fetch_data(dong_code):
    all_rows = []
    # 2020년부터 2025년까지 반복 (상권 데이터는 호출 제한 없음)
    for year in range(2020, 2026):
        for quarter in range(1, 5):
            url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/V_TRDAR_STRE_METRA_ADSTR_STATS_QU_S/1/1000/{year}/{quarter}/{dong_code}"
            res = requests.get(url)
            if res.status_code == 200:
                data = res.json()
                if 'V_TRDAR_STRE_METRA_ADSTR_STATS_QU_S' in data:
                    all_rows.extend(data['V_TRDAR_STRE_METRA_ADSTR_STATS_QU_S']['row'])
    return pd.DataFrame(all_rows)

# 3. 사용자 인터페이스
selected_station = st.selectbox("분석할 지하철역을 선택하세요", list(STATIONS.keys()))

if st.button("데이터 분석 시작"):
    with st.spinner('데이터를 불러오는 중입니다...'):
        df = fetch_data(STATIONS[selected_station])
        
        if not df.empty:
            # 출력 데이터 정리 (연도, 분기, 개업수, 폐업수)
            df = df[['STDR_YY_CD', 'STDR_QU_CD', 'OPN_STOR_CO', 'CLS_STOR_CO']]
            df.columns = ['연도', '분기', '개업점포수', '폐업점포수']
            
            st.success(f"{selected_station} 분석 완료!")
            st.dataframe(df, use_container_width=True)
            
            # 간단한 차트 시각화
            st.line_chart(df.set_index(['연도', '분기'])[['개업점포수', '폐업점포수']])
        else:
            st.warning("해당 기간의 데이터를 찾을 수 없습니다.")
