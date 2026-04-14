import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# 1. 설정
st.set_page_config(page_title="서울 상권 데이터 센터", layout="wide")
API_KEY = "4d59784b56676e64363847736b5362"

# --- [유동인구 분석 함수 보존: 나중에 탭 추가 시 바로 사용 가능] ---
def get_subway_data(station_name):
    # 이 로직은 나중에 다시 연결해 드릴 수 있도록 그대로 둡니다.
    pass

# 2. 메인 UI
st.title("📊 서울시 상권 개업/폐업 Raw 데이터")
st.info("데이터 유무가 확인된 시점의 개폐업 Raw 데이터 1,000건을 불러옵니다.")

# 3. 데이터 호출 (가장 안정적인 2023년 4분기 데이터로 시점 조정)
# 20244에서 데이터가 없다고 나오므로, 데이터가 확실히 있는 20234를 호출합니다.
url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/VwsmTrdarOpclQq/1/1000/20234"

try:
    with st.spinner('안정적인 데이터 구간을 찾는 중...'):
        response = requests.get(url, timeout=15)
        data = response.json()
        
        # 'VwsmTrdarOpclQq' 데이터셋 확인
        if 'VwsmTrdarOpclQq' in data:
            raw_df = pd.DataFrame(data['VwsmTrdarOpclQq']['row'])
            
            # API에서 내려주는 실제 영문 컬럼명 확인 후 매핑
            # 서울시 API 특성상 데이터가 있으면 아래 컬럼들이 반드시 포함됩니다.
            cols_mapping = {
                'TRDAR_CD_NM': '상권명',
                'SVC_INDUTY_CD_NM': '업종명',
                'OPN_STOR_CO': '개업수',
                'CLS_STOR_CO': '폐업수',
                'OPN_RT': '개업률(%)',
                'CLS_RT': '폐업률(%)'
            }
            
            # 존재하는 컬럼만 필터링해서 보여주기
            existing_cols = [c for c in cols_mapping.keys() if c in raw_df.columns]
            final_df = raw_df[existing_cols].rename(columns=cols_mapping)
            
            st.success(f"✅ 2023년 4분기 기준, {len(final_df):,}건의 데이터를 불러왔습니다.")
            
            # 상단 요약 지표 (Metric)
            m1, m2, m3 = st.columns(3)
            m1.metric("총 개업수", f"{final_df['개업수'].astype(int).sum():,}개")
            m2.metric("총 폐업수", f"{final_df['폐업수'].astype(int).sum():,}개")
            m3.metric("평균 개업률", f"{final_df['개업률(%)'].astype(float).mean():.2f}%")
            
            st.markdown("---")
            
            # 4. 검색 및 Raw 테이블 출력
            search = st.text_input("🔍 찾고 싶은 상권이나 업종을 입력하세요", placeholder="예: 강남역, 치킨집")
            if search:
                search_df = final_df[final_df.astype(str).apply(lambda x: x.str.contains(search)).any(axis=1)]
                st.dataframe(search_df, hide_index=True, use_container_width=True)
            else:
                st.dataframe(final_df, hide_index=True, use_container_width=True)
                
        else:
            # 2023년 데이터도 없을 경우에 대한 예외 처리
            st.error("지정한 시점에 데이터가 없습니다. API 서버 점검 중일 수 있습니다.")
            
except Exception as e:
    st.error(f"❌ 데이터 수집 중 오류: {e}")
