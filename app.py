import streamlit as st
import requests
import pandas as pd

API_KEY = "4d59784b56676e64363847736b5362"

# 1. 행정동 코드 기반 매핑 (가장 데이터가 안정적으로 적재되는 기준입니다)
STATIONS = {
    "강남역": "11680640", "홍대입구역": "11440660", "신촌역": "11410585",
    "합정역": "11440610", "신림역": "11620695", "서울대입구역": "11620595",
    "을지로3가역": "11140605", "종로3가역": "11110615", "건대입구역": "11215710",
    "방이역": "11710562", "잠실역": "11710710"
}

st.set_page_config(page_title="서울 상권 분석 (최종 점검)", layout="wide")
st.title("🚇 지하철역 주변 상권 분석 (행정동 기준)")

def fetch_data(dong_code):
    all_rows = []
    # 데이터셋명: T_TRDAR_INDUTY_STORE_QU (서울시 상권분석서비스(점포-행정동))
    # 조회 범위를 2024년 데이터 하나만 먼저 테스트해보도록 범위를 좁혔습니다 (성공 시 다시 확대 예정)
    for year in ["2024", "2025"]: 
        for quarter in ["1", "2", "3", "4"]:
            # API 가이드에 맞춘 엄격한 URL 구조
            url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/V_TRDAR_STRE_METRA_ADSTR_STATS_QU_S/1/100/{year}/{quarter}/{dong_code}"
            
            try:
                res = requests.get(url)
                data = res.json()
                
                if 'V_TRDAR_STRE_METRA_ADSTR_STATS_QU_S' in data:
                    all_rows.extend(data['V_TRDAR_STRE_METRA_ADSTR_STATS_QU_S']['row'])
                else:
                    # 데이터가 없을 때 서버의 실제 응답을 기록 (디버깅용)
                    st.write(f"로그: {year}년 {quarter}분기 - {data.get('RESULT', {}).get('MESSAGE', '데이터 없음')}")
            except Exception as e:
                st.error(f"통신 중 오류: {e}")
    
    return pd.DataFrame(all_rows)

selected_station = st.selectbox("분석할 지역을 선택하세요", list(STATIONS.keys()))

if st.button("데이터 분석 시작"):
    with st.spinner('서울시 서버에서 데이터를 가져오는 중...'):
        df = fetch_data(STATIONS[selected_station])
        
        if not df.empty:
            # 컬럼명이 데이터셋마다 다를 수 있어 유연하게 대처
            cols = {'STDR_YY_CD': '연도', 'STDR_QU_CD': '분기', 'OPN_STOR_CO': '개업수', 'CLS_STOR_CO': '폐업수'}
            df = df.rename(columns=cols)
            df = df[['연도', '분기', '개업수', '폐업수']]
            
            st.success("데이터 로드 성공!")
            st.dataframe(df)
            st.line_chart(df.set_index(['연도', '분기']))
        else:
            st.error("모든 시도에서 데이터를 찾지 못했습니다.")
            st.info("화면에 출력된 '로그' 메시지를 확인해 주세요. 거기에 에러 원인이 적혀 있습니다.")
