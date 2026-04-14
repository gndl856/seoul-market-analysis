import streamlit as st
import requests
import pandas as pd

# 새로 발급받은 키
API_KEY = "48476d747a676e6437365767456965"
SERVICE = "VwsmadstrStorW"

st.title("🔍 API 연결 긴급 점검")

# 테스트용: 강남역(11680640) 2024년 4분기 데이터 딱 하나만 호출
if st.button("강남역 2024년 4분기 데이터 호출 테스트"):
    # 명세서대로 URL 구성: 인증키/json/서비스명/시작/종료/기준년분기
    # 연도(2024) + 분기(4) = 20244
    url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/{SERVICE}/1/100/20244"
    
    res = requests.get(url)
    data = res.json()
    
    if SERVICE in data:
        df_all = pd.DataFrame(data[SERVICE]['row'])
        # 강남역(역삼1동) 코드만 필터링
        my_area = df_all[df_all['ADSTRD_CD'] == "11680640"]
        
        if not my_area.empty:
            st.success("✅ 데이터 호출 성공!")
            st.write("강남역 개업수:", my_area['OPBIZ_STOR_CO'].values[0])
            st.dataframe(my_area)
        else:
            st.warning("⚠️ 서비스는 응답하나, 강남역(11680640) 코드가 결과에 없습니다.")
            st.write("응답에 포함된 첫 5건 행정동 코드:", df_all['ADSTRD_CD'].head().tolist())
    else:
        st.error(f"❌ 데이터 로드 실패: {data.get('RESULT', {}).get('MESSAGE', '알 수 없는 오류')}")
        st.write("전체 서버 응답:", data)
