import streamlit as st
import requests
import pandas as pd

API_KEY = "4d59784b56676e64363847736b5362"

# 1. 엑셀 데이터와 일치하는 행정동 코드 매핑
STATIONS = {
    "강남역": "11680640", "홍대입구역": "11440660", "종로3가역": "11110615",
    "을지로3가역": "11140605", "신촌역": "11410585", "합정역": "11440610",
    "신림역": "11620695", "서울대입구역": "11620595", "건대입구역": "11215710",
    "방이역": "11710562", "잠실역": "11710710"
}

st.set_page_config(page_title="서울 상권 분석 툴", layout="wide")
st.title("🚇 지하철역 주변 상권 개폐업 분석 (2020~2025)")

def fetch_data(dong_code):
    all_rows = []
    # 데이터셋 명칭: V_TRDAR_STRE_METRA_ADSTR_STATS_QU_S
    # 엑셀에서 보신 데이터와 동일한 소스입니다.
    
    # 서버 부하를 방지하고 성공률을 높이기 위해 최근 데이터부터 호출
    for year in range(2020, 2026):
        for quarter in range(1, 5):
            # API URL (행정동 코드를 마지막에 넣는 방식)
            url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/V_TRDAR_STRE_METRA_ADSTR_STATS_QU_S/1/1000/{year}/{quarter}/{dong_code}"
            
            try:
                res = requests.get(url)
                data = res.json()
                
                if 'V_TRDAR_STRE_METRA_ADSTR_STATS_QU_S' in data:
                    rows = data['V_TRDAR_STRE_METRA_ADSTR_STATS_QU_S']['row']
                    # '전체 업종' 합산 데이터를 만들기 위해 데이터 저장
                    all_rows.extend(rows)
            except:
                continue
                
    return pd.DataFrame(all_rows)

selected_station = st.selectbox("분석할 지하철역을 선택하세요", list(STATIONS.keys()))

if st.button("데이터 분석 시작"):
    with st.spinner(f'{selected_station} 데이터를 불러오는 중...'):
        df = fetch_data(STATIONS[selected_station])
        
        if not df.empty:
            # 엑셀 컬럼명과 매칭하여 정리
            # OPN_STOR_CO = 개업 점포 수 / CLS_STOR_CO = 폐업 점포 수
            df['OPN_STOR_CO'] = pd.to_numeric(df['OPN_STOR_CO'])
            df['CLS_STOR_CO'] = pd.to_numeric(df['CLS_STOR_CO'])
            
            # 연도/분기별로 모든 업종의 개폐업 수를 합산합니다.
            summary = df.groupby(['STDR_YY_CD', 'STDR_QU_CD']).agg({
                'OPN_STOR_CO': 'sum',
                'CLS_STOR_CO': 'sum'
            }).reset_index()
            
            summary.columns = ['연도', '분기', '총_개업수', '총_폐업수']
            summary = summary.sort_values(['연도', '분기'])

            st.success(f"✅ {selected_station} 데이터 로드 완료!")
            
            # 시각화
            st.subheader(f"📊 {selected_station} 상권 개폐업 추이")
            st.line_chart(summary.set_index(['연도', '분기']))
            
            st.subheader("상세 데이터 (분기별 합계)")
            st.dataframe(summary, use_container_width=True)
        else:
            st.error("데이터를 불러오지 못했습니다. API 키가 해당 데이터셋(상권분석-행정동)에 접근 권한이 있는지 확인이 필요할 수 있습니다.")
