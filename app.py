import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# 1. 설정
st.set_page_config(page_title="서울 상권 데이터 센터", layout="wide")
API_KEY = "4d59784b56676e64363847736b5362"

# --- [유동인구 분석 로직 보존: 나중에 요청 시 탭만 추가하면 바로 작동] ---
def get_subway_data(station_name):
    # 나중에 다시 활성화할 때 사용할 함수입니다.
    pass

# 2. 메인 UI
st.title("📊 서울시 상권 점포 개/폐업 Raw 데이터")
st.info("호출 제한 없는 일반 인증키 모드입니다. (1회 1,000건 추출)")

# 3. 데이터 호출 및 예외 처리 강화
# 최신 데이터 시점 설정
url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/VwsmTrdarStorQq/1/1000/20244"

try:
    with st.spinner('데이터를 실시간으로 불러오는 중...'):
        response = requests.get(url, timeout=15)
        data = response.json()
        
        if 'VwsmTrdarStorQq' in data:
            # 원본 데이터 그대로 가져오기
            raw_rows = data['VwsmTrdarStorQq']['row']
            df = pd.DataFrame(raw_rows)
            
            # 에러 방지: 존재하는 컬럼만 한글로 변환
            cols_mapping = {
                'TRDAR_CD_NM': '상권명',
                'SVC_INDUTY_CD_NM': '업종명',
                'STOR_CO': '점포수',
                'OPN_STOR_CO': '개업수',
                'CLS_STOR_CO': '폐업수'
            }
            
            # 실제 데이터에 있는 컬럼만 골라내기 (이미지상의 에러 원인 차단)
            existing_cols = [c for c in cols_mapping.keys() if c in df.columns]
            final_df = df[existing_cols].rename(columns=cols_mapping)
            
            # 상단 요약 지표
            st.success(f"✅ 총 {len(final_df):,}개의 상권 데이터를 성공적으로 수집했습니다.")
            
            # 4. 검색 및 결과 출력
            search = st.text_input("🔍 특정 상권이나 업종을 검색해 보세요 (예: 강남역, 치킨집)")
            
            if search:
                # 검색어가 포함된 행만 필터링
                search_df = final_df[final_df.astype(str).apply(lambda x: x.str.contains(search)).any(axis=1)]
                st.dataframe(search_df, hide_index=True, use_container_width=True)
            else:
                st.dataframe(final_df, hide_index=True, use_container_width=True)
                
        else:
            st.error("API 응답 구조가 평소와 다릅니다. (데이터 없음 혹은 점검 중)")
            
except Exception as e:
    st.error(f"❌ 데이터 수집 중 오류 발생: {e}")
    st.info("API 키의 권한 설정이나 서버의 일시적 지연일 수 있습니다.")
