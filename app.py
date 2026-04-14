import streamlit as st
import pandas as pd
import requests

# 1. 설정
st.set_page_config(page_title="서울 상권 데이터 센터", layout="wide")
API_KEY = "4d59784b56676e64363847736b5362"

# --- [유동인구 분석 함수 보존: 나중에 다시 연결 가능] ---
def get_subway_data(station_name):
    pass

# 2. 메인 UI
st.title("📊 서울시 상권 개업/폐업 Raw 데이터")
st.warning("서버 과부하를 방지하기 위해 데이터를 100건씩 끊어서 호출합니다.")

# 3. 데이터 호출 (서버 부담을 줄이기 위해 1~100번까지만 요청)
# ERROR-500은 보통 대량 데이터 요청 시 발생하므로 범위를 좁힙니다.
url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/VwsmTrdarOpclQq/1/100/20233"

try:
    with st.spinner('서울시 서버에서 안전하게 데이터를 가져오는 중...'):
        response = requests.get(url, timeout=20)
        data = response.json()
        
        # 정상 응답 확인
        if 'VwsmTrdarOpclQq' in data:
            df = pd.DataFrame(data['VwsmTrdarOpclQq']['row'])
            
            # 컬럼 매핑
            cols_mapping = {
                'TRDAR_CD_NM': '상권명',
                'SVC_INDUTY_CD_NM': '업종명',
                'OPN_STOR_CO': '개업수',
                'CLS_STOR_CO': '폐업수',
                'OPN_RT': '개업률(%)',
                'CLS_RT': '폐업률(%)'
            }
            
            final_df = df[[c for c in cols_mapping.keys() if c in df.columns]].rename(columns=cols_mapping)
            
            st.success(f"✅ 서버 연결 성공! 최신 데이터 {len(final_df)}건을 불러왔습니다.")
            
            # 4. 출력 및 검색
            search = st.text_input("🔍 상권명 또는 업종 검색 (예: 강남역, 치킨)")
            if search:
                search_df = final_df[final_df.astype(str).apply(lambda x: x.str.contains(search)).any(axis=1)]
                st.dataframe(search_df, hide_index=True, use_container_width=True)
            else:
                st.dataframe(final_df, hide_index=True, use_container_width=True)
                
        elif 'RESULT' in data:
            # 500 에러 등이 날 경우 서버의 응답 코드를 상세히 출력
            st.error(f"❌ 서버 오류 발생: {data['RESULT']['MESSAGE']} ({data['RESULT']['CODE']})")
            st.info("이 오류는 서울시 API 서버 자체의 지연 문제입니다. 잠시 후 다시 시도해 주세요.")
            
except Exception as e:
    st.error(f"❌ 통신 오류: {e}")
