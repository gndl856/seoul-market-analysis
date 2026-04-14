import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# 1. 설정
st.set_page_config(page_title="서울 상권 개폐업 분석", layout="wide")
API_KEY = "4d59784b56676e64363847736b5362"

# --- [유동인구 분석 로직 보존: 나중에 다시 활성화 가능] ---
def get_subway_data(station_name):
    # 나중에 지하철 유동인구가 필요할 때 이 함수를 UI에 연결하면 됩니다.
    pass

# 2. 메인 UI
st.title("📊 서울시 상권 개업/폐업 Raw 데이터")
st.info("개업률과 폐업수가 포함된 '점포 개폐업' 전용 API 데이터를 호출합니다. (1,000건)")

# 3. 데이터 호출 (개폐업 전용 서비스명: VwsmTrdarOpclQq)
# 점포수 데이터가 아닌, '개업/폐업' 데이터셋으로 주소를 변경했습니다.
url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/VwsmTrdarOpclQq/1/1000/20244"

try:
    with st.spinner('실시간 개폐업 데이터를 불러오는 중...'):
        response = requests.get(url, timeout=15)
        data = response.json()
        
        # 서비스명에 맞춰 데이터 추출
        if 'VwsmTrdarOpclQq' in data:
            raw_rows = data['VwsmTrdarOpclQq']['row']
            df = pd.DataFrame(raw_rows)
            
            # 실제 개업/폐업 데이터 항목에 맞춰 한글 매핑
            cols_mapping = {
                'TRDAR_CD_NM': '상권명',
                'SVC_INDUTY_CD_NM': '업종명',
                'OPN_STOR_CO': '개업수',
                'OPN_RT': '개업률(%)',
                'CLS_STOR_CO': '폐업수',
                'CLS_RT': '폐업률(%)',
                'STDR_YYQU_CD': '기준분기'
            }
            
            # 존재하는 컬럼만 선별하여 정리
            existing_cols = [c for c in cols_mapping.keys() if c in df.columns]
            final_df = df[existing_cols].rename(columns=cols_mapping)
            
            # 요약 수치
            st.success(f"✅ 총 {len(final_df):,}개의 개폐업 데이터를 수집했습니다.")
            
            m1, m2, m3 = st.columns(3)
            m1.metric("총 개업수 합계", f"{final_df['개업수'].astype(int).sum():,}개")
            m2.metric("총 폐업수 합계", f"{final_df['폐업수'].astype(int).sum():,}개")
            m3.metric("평균 개업률", f"{final_df['개업률(%)'].astype(float).mean():.2f}%")

            st.markdown("---")
            
            # 4. 검색 및 출력
            search = st.text_input("🔍 분석하고 싶은 상권명이나 업종을 입력하세요", placeholder="예: 강남역, 치킨집, 편의점")
            
            if search:
                # 모든 열에서 검색어가 포함된 행 찾기
                search_df = final_df[final_df.astype(str).apply(lambda x: x.str.contains(search)).any(axis=1)]
                st.dataframe(search_df, hide_index=True, use_container_width=True)
            else:
                st.dataframe(final_df, hide_index=True, use_container_width=True)
                
        else:
            st.error("API 응답에 개폐업 데이터가 없습니다. (데이터셋 명칭 확인 필요)")
            
except Exception as e:
    st.error(f"❌ 데이터 수집 오류: {e}")
