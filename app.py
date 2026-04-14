import streamlit as st
import pandas as pd
import requests

# 1. 설정
st.set_page_config(page_title="서울 상권 데이터 센터", layout="wide")
API_KEY = "4d59784b56676e64363847736b5362"

# --- [유동인구 분석 함수 보존: 필요할 때 언제든 다시 연결 가능] ---
def get_subway_data(station_name):
    # 나중에 지하철 데이터가 필요할 때 사용할 보존용 함수입니다.
    pass

# 2. 메인 UI
st.title("📊 서울시 상권 개업/폐업 Raw 데이터")
st.info("서버 내부 오류(500)를 방지하기 위해 정밀 파라미터로 호출합니다.")

# 3. 데이터 호출 (서버가 요구하는 필수 시점 파라미터 포함)
# 'ERROR-500'은 시점이 누락되었을 때 자주 발생하므로, 확실한 시점(20233)을 다시 명시합니다.
url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/VwsmTrdarOpclQq/1/1000/20233"

try:
    with st.spinner('서울시 데이터 서버에 정밀 접속 중...'):
        response = requests.get(url, timeout=15)
        data = response.json()
        
        # 데이터셋 존재 여부 확인
        if 'VwsmTrdarOpclQq' in data:
            raw_rows = data['VwsmTrdarOpclQq']['row']
            df = pd.DataFrame(raw_rows)
            
            # 실제 데이터 컬럼 매핑
            cols_mapping = {
                'TRDAR_CD_NM': '상권명',
                'SVC_INDUTY_CD_NM': '업종명',
                'OPN_STOR_CO': '개업수',
                'CLS_STOR_CO': '폐업수',
                'OPN_RT': '개업률(%)',
                'CLS_RT': '폐업률(%)'
            }
            
            # 존재하는 컬럼만 선별하여 출력
            existing_cols = [c for c in cols_mapping.keys() if c in df.columns]
            final_df = df[existing_cols].rename(columns=cols_mapping)
            
            st.success(f"✅ 서버 연결 성공! {len(final_df):,}건의 데이터를 불러왔습니다.")
            
            # 검색 및 결과 테이블
            search = st.text_input("🔍 상권이나 업종을 검색하세요 (예: 강남역, 편의점)")
            if search:
                search_df = final_df[final_df.astype(str).apply(lambda x: x.str.contains(search)).any(axis=1)]
                st.dataframe(search_df, hide_index=True, use_container_width=True)
            else:
                st.dataframe(final_df, hide_index=True, use_container_width=True)
        
        elif 'RESULT' in data:
            st.error(f"❌ 서버 메시지: {data['RESULT']['MESSAGE']} ({data['RESULT']['CODE']})")
            st.info("이 에러는 주로 시점(20233) 데이터가 해당 구간에 없을 때 발생합니다. 숫자를 조금씩 바꿔보세요.")
            
except Exception as e:
    st.error(f"❌ 통신 오류: {e}")
