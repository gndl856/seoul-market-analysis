import streamlit as st
import requests
import pandas as pd

# 1. 새로 발급받으신 인증키
API_KEY = "48476d747a676e6437365767456965"

# 2. 명세서 기반 서비스명 및 지역 매핑
SERVICE_NAME = "VwsmadstrStorW" 
STATIONS = {
    "강남역": "11680640", "홍대입구역": "11440660", "종로3가역": "11110615",
    "을지로3가역": "11140605", "신촌역": "11410585", "합정역": "11440610",
    "신림역": "11620695", "서울대입구역": "11620595", "건대입구역": "11215710",
    "방이역": "11710562", "잠실역": "11710710"
}

st.set_page_config(page_title="서울 상권 분석 (공식 명세 반영)", layout="wide")
st.title("🚇 지하철역 주변 상권 분석 (2020~2025)")

def fetch_data(dong_code):
    all_rows = []
    
    # 명세서의 STDR_YYQU_CD 형식(YYYYQ)에 맞춰 루프 생성
    years = [str(y) for y in range(2020, 2026)]
    quarters = ["1", "2", "3", "4"]
    
    progress_bar = st.progress(0)
    total = len(years) * len(quarters)
    count = 0

    for y in years:
        for q in quarters:
            target_period = y + q # 예: "20241"
            
            # 명세서 구조: 인증키/타입/서비스명/시작/종료/기준_년분기_코드
            # 행정동 코드는 필터링 인자가 없으므로 전체를 가져와서 코드 내에서 필터링해야 합니다.
            url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/{SERVICE_NAME}/1/1000/{target_period}"
            
            try:
                res = requests.get(url)
                if res.status_code == 200:
                    data = res.json()
                    if SERVICE_NAME in data:
                        rows = data[SERVICE_NAME]['row']
                        # 선택한 행정동 코드(ADSTRD_CD)와 일치하는 데이터만 필터링
                        filtered = [r for r in rows if r.get('ADSTRD_CD') == dong_code]
                        all_rows.extend(filtered)
            except:
                pass
            
            count += 1
            progress_bar.progress(count / total)
                
    return pd.DataFrame(all_rows)

selected_station = st.selectbox("분석할 지하철역을 선택하세요", list(STATIONS.keys()))

if st.button("데이터 분석 시작"):
    with st.spinner('명세서 데이터 로드 중...'):
        df = fetch_data(STATIONS[selected_station])
        
        if not df.empty:
            # 명세서 출력값 매핑: OPBIZ_STOR_CO(개업), CLSBIZ_STOR_CO(폐업)
            df['OPBIZ_STOR_CO'] = pd.to_numeric(df['OPBIZ_STOR_CO'])
            df['CLSBIZ_STOR_CO'] = pd.to_numeric(df['CLSBIZ_STOR_CO'])
            
            # 분기별 합산 (여러 업종 데이터를 하나로 합침)
            summary = df.groupby('STDR_YYQU_CD').agg({
                'OPBIZ_STOR_CO': 'sum',
                'CLSBIZ_STOR_CO': 'sum'
            }).reset_index()
            
            # 시각화용 이름 변경
            summary.columns = ['년분기', '개업수', '폐업수']
            summary = summary.sort_values('년분기')

            st.success(f"✅ {selected_station} 분석 완료!")
            
            # 메트릭
            c1, c2 = st.columns(2)
            c1.metric("총 개업 수", f"{int(summary['개업수'].sum()):,}개")
            c2.metric("총 폐업 수", f"{int(summary['폐업수'].sum()):,}개")
            
            # 그래프 및 표
            st.line_chart(summary.set_index('년분기'))
            st.dataframe(summary, use_container_width=True)
        else:
            st.error("데이터가 없습니다. (TIP: 새로 받은 키가 시스템에 등록되는 데 시간이 걸릴 수 있습니다.)")
