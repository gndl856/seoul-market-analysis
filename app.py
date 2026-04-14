import streamlit as st
import pandas as pd
import requests

# 1. 설정
st.set_page_config(page_title="서울 상권 데이터 센터", layout="wide")
API_KEY = "4d59784b56676e64363847736b5362"

# --- [유동인구 분석 함수 보존] ---
def get_subway_data(station_name):
    # 나중에 다시 연결할 유동인구 로직입니다.
    pass

# 2. 메인 UI
st.title("📊 서울시 상권 개업/폐업 Raw 데이터")
st.info("시점 제한을 풀고 서버의 최신 Raw 데이터를 직접 호출합니다.")

# 3. 데이터 호출 (가장 단순한 주소로 변경)
# 뒤의 시점(20234 등)을 아예 빼고 1~1000번 데이터를 요청하여 서버 응답을 확인합니다.
url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/VwsmTrdarOpclQq/1/1000/"

try:
    with st.spinner('서울시 서버와 직접 통신 중...'):
        response = requests.get(url, timeout=15)
        data = response.json()
        
        # 4. 서버 응답 메시지 직접 확인 (디버깅용)
        if 'RESULT' in data:
            st.warning(f"⚠️ 서버 응답 메시지: {data['RESULT']['MESSAGE']}")
        
        if 'VwsmTrdarOpclQq' in data:
            raw_rows = data['VwsmTrdarOpclQq']['row']
            df = pd.DataFrame(raw_rows)
            
            # 한글 컬럼 매핑
            cols_mapping = {
                'STDR_YY_CD': '연도',
                'STDR_QU_CD': '분기',
                'TRDAR_CD_NM': '상권명',
                'SVC_INDUTY_CD_NM': '업종명',
                'OPN_STOR_CO': '개업수',
                'CLS_STOR_CO': '폐업수'
            }
            
            # 존재하는 컬럼만 필터링
            final_df = df[[c for c in cols_mapping.keys() if c in df.columns]].rename(columns=cols_mapping)
            
            st.success(f"✅ 성공적으로 {len(final_df):,}건의 데이터를 가져왔습니다.")
            
            # 데이터 출력
            search = st.text_input("🔍 검색 (상권명 또는 업종)", placeholder="예: 강남역")
            if search:
                search_df = final_df[final_df.astype(str).apply(lambda x: x.str.contains(search)).any(axis=1)]
                st.dataframe(search_df, hide_index=True, use_container_width=True)
            else:
                st.dataframe(final_df, hide_index=True, use_container_width=True)
                
        else:
            # 데이터셋 이름이 다를 경우를 대비해 전체 구조 출력
            st.error("데이터 구조를 찾을 수 없습니다. 서버 응답 결과:")
            st.json(data)
            
except Exception as e:
    st.error(f"❌ 통신 오류 발생: {e}")
