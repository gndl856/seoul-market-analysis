import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="API 키 정밀 점검", layout="wide")

# 1. API 키 설정
API_KEY = "4d59784b56676e64363847736b5362"

st.title("🔑 API 연결 및 데이터셋 정밀 점검")

# 점검할 데이터셋 리스트 (가장 가벼운 것부터 순차 점검)
datasets = {
    "상권 점포수 (기본)": "VwsmTrdarStorQq",
    "상권 개폐업 (요청하신 것)": "VwsmTrdarOpclQq",
    "상권 유동인구": "VwsmTrdarFlpopQq"
}

target = st.selectbox("점검할 데이터셋을 선택하세요", list(datasets.keys()))
target_code = datasets[target]

if st.button("서버 연결 테스트 시작"):
    # 최하단 데이터 5건만 아주 가볍게 요청 (서버 과부하 방지)
    url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/{target_code}/1/5/20233"
    
    try:
        response = requests.get(url, timeout=10)
        res_data = response.json()
        
        if target_code in res_data:
            st.success(f"✅ {target} 데이터셋 연결 성공!")
            st.balloons()
            df = pd.DataFrame(res_data[target_code]['row'])
            st.dataframe(df)
        else:
            # 서버가 보낸 실제 에러 코드 분석
            error_info = res_data.get('RESULT', res_data.get('err', {}))
            st.error(f"❌ 서버 응답 오류: {error_info.get('MESSAGE', '알 수 없는 오류')}")
            st.info(f"에러 코드: {error_info.get('CODE', 'N/A')}")
            
            if "ERROR-500" in str(res_data):
                st.warning("💡 분석: 사용자님 키는 정상이지만, 서울시 서버가 현재 해당 데이터를 처리하지 못하고 있습니다. (서버 내부 점검 중)")

    except Exception as e:
        st.error(f"🔥 연결 불가: {e}")
