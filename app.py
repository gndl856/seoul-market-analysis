import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# 1. 기본 설정
st.set_page_config(page_title="서울 상권 Raw 데이터 분석", layout="wide")
API_KEY = "4d59784b56676e64363847736b5362"

# --- [보존된 유동인구 분석 함수: 나중에 필요할 때 바로 활성화 가능] ---
def get_subway_data(station_name):
    # 나중에 유동인구 기능을 다시 넣을 때 사용할 로직입니다.
    pass

# 2. UI 구성
st.title("🍕 서울시 상권 점포 개/폐업 Raw 데이터")
st.info("특정 지역 필터링 없이 현재 API가 제공하는 최신 데이터 1,000건을 그대로 불러옵니다.")

# 3. 데이터 호출 (가장 최신인 2024년 4분기 데이터 전체 요청)
# 1회 호출 최대치인 1000건을 요청합니다.
url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/VwsmTrdarStorQq/1/1000/20244"

with st.spinner('서울시 전체 상권 데이터를 불러오는 중...'):
    try:
        response = requests.get(url, timeout=15)
        res = response.json()
        
        if 'VwsmTrdarStorQq' in res:
            # 1,000건의 전체 로우 데이터 생성
            raw_df = pd.DataFrame(res['VwsmTrdarStorQq']['row'])
            
            # 보기 편하게 컬럼명만 한글로 변경
            cols_map = {
                'TRDAR_CD_NM': '상권명',
                'SVC_INDUTY_CD_NM': '업종명',
                'STOR_CO': '점포수',
                'OPN_STOR_CO': '개업수',
                'CLS_STOR_CO': '폐업수',
                'TRDAR_CD': '상권코드'
            }
            display_df = raw_df[list(cols_map.keys())].rename(columns=cols_map)
            
            # 데이터 요약 정보
            st.success(f"✅ 총 {len(display_df):,}건의 상권 데이터를 성공적으로 불러왔습니다.")
            
            # 메트릭 표시 (불러온 1,000건 전체 합계)
            m1, m2, m3 = st.columns(3)
            m1.metric("총 점포 합계", f"{display_df['점포수'].astype(int).sum():,}개")
            m2.metric("총 개업 합계", f"{display_df['개업수'].astype(int).sum():,}개")
            m3.metric("총 폐업 합계", f"{display_df['폐업수'].astype(int).sum():,}개")
            
            st.markdown("---")
            
            # 데이터 검색 기능 추가 (사용자가 직접 타이핑해서 찾기)
            search_query = st.text_input("🔍 찾고 싶은 상권명이나 업종명을 입력하세요 (예: 강남역, 커피전문점)")
            if search_query:
                filtered_df = display_df[
                    display_df['상권명'].str.contains(search_query) | 
                    display_df['업종명'].str.contains(search_query)
                ]
                st.dataframe(filtered_df, hide_index=True, use_container_width=True)
            else:
                st.dataframe(display_df, hide_index=True, use_container_width=True)
                
        else:
            st.error("❌ API 응답에 데이터가 없습니다. 인증키를 확인해 주세요.")
            
    except Exception as e:
        st.error(f"❌ 서버 연결 실패: {e}. 인증키가 유효한지 또는 호출 제한에 걸렸는지 확인이 필요합니다.")
