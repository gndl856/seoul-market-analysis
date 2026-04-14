import streamlit as st
import pandas as pd
import requests

# 1. 설정
st.set_page_config(page_title="서울 요식업 분석", layout="wide")
API_KEY = "4d59784b56676e64363847736b5362"

# --- [점포수 데이터 수집 함수 (강화형)] ---
def get_store_trend(search_keyword, quarters):
    all_data = []
    # 2023년 3분기 데이터를 기준으로 '상권명' 리스트를 먼저 확보 (매칭용)
    test_url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/VwsmTrdarStorQq/1/1000/20233"
    try:
        sample_res = requests.get(test_url).json()
        if 'VwsmTrdarStorQq' in sample_res:
            sample_df = pd.DataFrame(sample_res['VwsmTrdarStorQq']['row'])
            # 입력한 키워드가 포함된 공식 상권명 리스트 추출
            matched_names = sample_df[sample_df['TRDAR_CD_NM'].str.contains(search_keyword)]['TRDAR_CD_NM'].unique()
            
            if len(matched_names) == 0:
                return pd.DataFrame(), [] # 매칭되는 상권 없음
            
            # 찾은 공식 상권명들로 데이터 수집
            for q in quarters:
                url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/VwsmTrdarStorQq/1/1000/{q}"
                res = requests.get(url).json()
                if 'VwsmTrdarStorQq' in res:
                    df = pd.DataFrame(res['VwsmTrdarStorQq']['row'])
                    # 공식 명칭과 일치하고 요식업종인 데이터 필터링
                    target_df = df[
                        (df['TRDAR_CD_NM'].isin(matched_names)) & 
                        (df['SVC_INDUTY_CD_NM'].str.contains('한식|중식|일식|양식|제과|커피|패스트푸드|분식'))
                    ].copy()
                    if not target_df.empty:
                        target_df['기준분기'] = q
                        all_data.append(target_df)
            return pd.concat(all_data), matched_names
    except:
        pass
    return pd.DataFrame(), []

# 2. 메인 UI
st.title("🍔 요식업 점포수 추이 및 증감 분석")
st.info("검색하신 키워드가 포함된 모든 공식 상권 데이터를 합산하여 분석합니다.")

# 분석 대상 상권 입력
search_input = st.text_input("분석할 상권명을 입력하세요 (예: 강남, 종로, 신림)", value="강남")
quarters = ["20231", "20232", "20233", "20234"]

if st.button("분석 시작"):
    with st.spinner(f"'{search_input}' 관련 상권을 찾는 중..."):
        trend_df, matched_list = get_store_trend(search_input, quarters)
        
    if not trend_df.empty:
        st.success(f"✅ 검색 결과: {', '.join(matched_list)} 상권 데이터를 찾았습니다.")
        
        # 데이터 정리 및 피벗
        display_df = trend_df[['기준분기', 'SVC_INDUTY_CD_NM', 'STOR_CO']].copy()
        display_df.columns = ['분기', '업종명', '점포수']
        display_df['점포수'] = display_df['점포수'].astype(int)
        
        pivot_df = display_df.pivot_table(index='업종명', columns='분기', values='점포수', aggfunc='sum').fillna(0)
        
        # 증감 계산
        pivot_df['전체증감'] = pivot_df[quarters[-1]] - pivot_df[quarters[0]]
        st.subheader(f"📊 {search_input} 인근 요식업 점포수 변동")
        st.dataframe(pivot_df, use_container_width=True)
        
        # 증감 결과 요약
        total_growth = pivot_df['전체증감'].sum()
        status = "순증" if total_growth > 0 else "감소"
        st.metric(f"최근 1년 {search_input} 상권 요식업 변화", f"{int(total_growth)}개 {status}")
            
    else:
        st.error(f"❌ '{search_input}'이(가) 포함된 상권명을 찾을 수 없습니다.")
        st.write("팁: '강남역' 대신 '강남'으로, '종로3가' 대신 '종로'로 검색해 보세요.")
