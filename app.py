import streamlit as st
import requests
import pandas as pd

# 1. 설정 및 상권 코드 매핑 (행정동 코드가 아닌 '상권 코드'로 변경하여 정확도 향상)
# 행정동 단위 조회가 막혀있을 경우를 대비해 가장 확실한 '발달상권' 코드를 사용합니다.
API_KEY = "4d59784b56676e64363847736b5362"

STATIONS = {
    "홍대입구역": "3120037", "합정역": "3110214", "신촌역": "3120038",
    "신림역": "3110850", "서울대입구역": "3110854", "을지로3가역": "3120017",
    "종로3가역": "3120011", "강남역": "3110656", "건대입구역": "3110395",
    "방이역": "3110943", "잠실역": "3110955"
}

st.set_page_config(page_title="서울 상권 분석 툴", layout="wide")
st.title("🚇 지하철역 주변 상권 개폐업 분석 (2020~2025)")

# 2. 데이터 호출 함수
def fetch_data(trdar_code):
    all_rows = []
    # 데이터셋 명칭 확인: V_TRDAR_STRE_METRA_STATS_QU_S (상권별 점포 통계)
    # 이 API는 일일 호출 제한이 없으므로 안전합니다.
    for year in range(2020, 2026):
        for quarter in range(1, 5):
            # 상권 코드 필터링을 URL에 포함
            url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/V_TRDAR_STRE_METRA_STATS_QU_S/1/5/{year}/{quarter}/{trdar_code}"
            res = requests.get(url)
            
            if res.status_code == 200:
                data = res.json()
                if 'V_TRDAR_STRE_METRA_STATS_QU_S' in data:
                    all_rows.extend(data['V_TRDAR_STRE_METRA_STATS_QU_S']['row'])
            else:
                continue
    return pd.DataFrame(all_rows)

# 3. 사용자 인터페이스
selected_station = st.selectbox("분석할 지하철역을 선택하세요", list(STATIONS.keys()))

if st.button("데이터 분석 시작"):
    with st.spinner(f'{selected_station} 데이터를 수집 중... (2020년~2025년)'):
        df = fetch_data(STATIONS[selected_station])
        
        if not df.empty:
            # 컬럼명 매핑 (API 응답 기준)
            # STDR_YY_CD: 기준년도, STDR_QU_CD: 기준분기, OPN_STOR_CO: 개업점포수, CLS_STOR_CO: 폐업점포수
            df = df[['STDR_YY_CD', 'STDR_QU_CD', 'OPN_STOR_CO', 'CLS_STOR_CO']]
            df.columns = ['연도', '분기', '개업점포수', '폐업점포수']
            
            # 데이터 타입 변환 (숫자로 정렬하기 위함)
            df = df.sort_values(['연도', '분기'], ascending=True)
            
            st.success(f"✅ {selected_station} 상권 데이터 조회를 완료했습니다!")
            
            # 상단 지표 요약
            col1, col2 = st.columns(2)
            col1.metric("총 개업 수 (기간 내)", f"{df['개업점포수'].astype(int).sum():,}개")
            col2.metric("총 폐업 수 (기간 내)", f"{df['폐업점포수'].astype(int).sum():,}개")

            # 데이터 표 및 차트
            st.subheader("연도/분기별 추이")
            st.line_chart(df.set_index(['연도', '분기'])[['개업점포수', '폐업점포수']])
            st.dataframe(df, use_container_width=True)
        else:
            st.error("데이터를 불러오지 못했습니다. 원인: 해당 상권 코드가 시스템에서 일시적으로 조회되지 않거나 API 서버 응답이 없습니다.")
            st.info("Tip: 다른 역을 먼저 선택해서 데이터가 나오는지 확인해 보세요.")
