import streamlit as st
import requests
import pandas as pd

# 1. 설정 및 상권 코드 매핑 (발달상권 기준 고정 코드)
API_KEY = "4d59784b56676e64363847736b5362"

# 서울시에서 공식적으로 사용하는 상권분석 서비스 상권코드 (발달상권 위주)
STATIONS = {
    "강남역": "3120153", "홍대입구역": "3120101", "신촌역": "3120102",
    "합정역": "3120103", "신림역": "3120215", "서울대입구역": "3120216",
    "을지로3가역": "3120018", "종로3가역": "3120012", "건대입구역": "3120067",
    "방이역": "3120240", "잠실역": "3120241"
}

st.set_page_config(page_title="서울 상권 분석 서비스", layout="wide")
st.title("🚇 지하철역 주변 상권 개폐업 분석 (2020~2025)")

def fetch_data(trdar_code):
    all_rows = []
    # 데이터셋 서비스명을 가장 대중적인 것으로 교체
    # 'V_TRDAR_STRE_METRA_STATS_QU_S' 대신 'V_TRDAR_STRE_METRA_STATS_QU_S' 혹은 
    # 유사한 점포 통계 API를 사용하되, 호출 구조를 표준화함
    
    for year in range(2020, 2026):
        for quarter in range(1, 5):
            # API URL 구성 (인자 순서: 인증키/타입/서비스명/시작/종료/년도/분기/상권코드)
            url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/V_TRDAR_STRE_METRA_STATS_QU_S/1/10/{year}/{quarter}/{trdar_code}"
            
            try:
                res = requests.get(url)
                if res.status_code == 200:
                    data = res.json()
                    # 서비스명 키가 있는지 확인
                    if 'V_TRDAR_STRE_METRA_STATS_QU_S' in data:
                        rows = data['V_TRDAR_STRE_METRA_STATS_QU_S']['row']
                        all_rows.extend(rows)
                    elif 'RESULT' in data and data['RESULT']['CODE'] != 'INFO-000':
                        # 데이터가 없는 분기는 그냥 넘어감
                        continue
            except Exception as e:
                st.error(f"통신 에러 발생: {e}")
                break
    return pd.DataFrame(all_rows)

selected_station = st.selectbox("분석할 지하철역을 선택하세요", list(STATIONS.keys()))

if st.button("데이터 분석 시작"):
    with st.spinner(f'{selected_station} 데이터를 수집 중입니다...'):
        df = fetch_data(STATIONS[selected_station])
        
        if not df.empty:
            # 출력 데이터 정제
            df = df[['STDR_YY_CD', 'STDR_QU_CD', 'OPN_STOR_CO', 'CLS_STOR_CO']]
            df.columns = ['연도', '분기', '개업점포수', '폐업점포수']
            
            # 숫자형 변환 및 정렬
            df['개업점포수'] = pd.to_numeric(df['개업점포수'])
            df['폐업점포수'] = pd.to_numeric(df['폐업점포수'])
            df = df.sort_values(['연도', '분기'])

            st.success(f"✅ {selected_station} 데이터 조회 성공!")
            
            col1, col2 = st.columns(2)
            col1.metric("총 개업 수", f"{int(df['개업점포수'].sum()):,}개")
            col2.metric("총 폐업 수", f"{int(df['폐업점포수'].sum()):,}개")

            st.line_chart(df.set_index(['연도', '분기'])[['개업점포수', '폐업점포수']])
            st.dataframe(df, use_container_width=True)
        else:
            # 실패 원인 시각화
            st.error("데이터를 찾을 수 없습니다.")
            st.info("""
            **확인 사항:**
            1. 제공해주신 API 인증키가 '상권분석서비스' 권한을 승인받았는지 확인이 필요합니다. 
            2. 서울 열린데이터광장 마이페이지에서 해당 데이터셋의 '활용신청'이 되어있는지 체크해 주세요.
            3. 만약 키가 정상인데도 안 된다면, 서비스명을 'V_TRDAR_STRE_METRA_STATS_QU_S'에서 다른 유관 데이터셋으로 교체해야 할 수도 있습니다.
            """)
