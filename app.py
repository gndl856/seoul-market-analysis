import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="서울 요식업 분석", layout="wide")
API_KEY = "4d59784b56676e64363847736b5362"

def get_store_trend(search_keyword, quarters):
    all_data = []
    matched_names = []
    
    # 1. 먼저 상권명 찾기
    test_url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/VwsmTrdarStorQq/1/1000/20233"
    try:
        sample_res = requests.get(test_url).json()
        if 'VwsmTrdarStorQq' in sample_res:
            sample_df = pd.DataFrame(sample_res['VwsmTrdarStorQq']['row'])
            matched_names = sample_df[sample_df['TRDAR_CD_NM'].str.contains(search_keyword)]['TRDAR_CD_NM'].unique()
            
            if len(matched_names) == 0:
                return pd.DataFrame(), []
            
            # 2. 실제 데이터 수집
            for q in quarters:
                url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/VwsmTrdarStorQq/1/1000/{q}"
                res = requests.get(url).json()
                if 'VwsmTrdarStorQq' in res:
                    df = pd.DataFrame(res['VwsmTrdarStorQq']['row'])
                    target_df = df[
                        (df['TRDAR_CD_NM'].isin(matched_names)) & 
                        (df['SVC_INDUTY_CD_NM'].str.contains('한식|중식|일식|양식|제과|커피|분식'))
                    ].copy()
                    if not target_df.empty:
                        target_df['기준분기'] = q
                        all_data.append(target_df)
    except:
        pass
    return pd.concat(all_data) if all_data else pd.DataFrame(), matched_names

st.title("🍔 요식업 점포수 추이 및 증감 분석")

search_input = st.text_input("분석할 상권명 키워드 (예: 강남, 종로)", value="강남")
quarters = ["20231", "20232", "20233", "20234"]

if st.button("분석 시작"):
    with st.spinner("데이터 분석 중..."):
        trend_df, matched_list = get_store_trend(search_input, quarters)
        
    if not trend_df.empty:
        st.success(f"✅ 검색 결과: {', '.join(matched_list)}")
        
        # 데이터 정리
        display_df = trend_df[['기준분기', 'SVC_INDUTY_CD_NM', 'STOR_CO']].copy()
        display_df.columns = ['분기', '업종명', '점포수']
        display_df['점포수'] = pd.to_numeric(display_df['점포수'])
        
        # 피벗 테이블 생성
        pivot_df = display_df.pivot_table(index='업종명', columns='분기', values='점포수', aggfunc='sum').fillna(0)
        
        # [핵심 수정] 실제 존재하는 컬럼(분기)들만 추출하여 비교
        available_quarters = sorted(pivot_df.columns.tolist())
        
        if len(available_quarters) >= 2:
            first_q = available_quarters[0]
            last_q = available_quarters[-1]
            # 안전하게 컬럼 생성
            pivot_df['전체증감'] = pivot_df[last_q] - pivot_df[first_q]
            
            st.subheader(f"📊 {search_input} 인근 요식업 변동 ({first_q} ~ {last_q})")
            st.dataframe(pivot_df, use_container_width=True)
            
            total_diff = pivot_df['전체증감'].sum()
            st.metric(f"기간 내 점포 순증감", f"{int(total_diff)}개")
        else:
            st.warning("비교할 수 있는 분기 데이터가 충분하지 않습니다. (최소 2개 분기 필요)")
            st.dataframe(pivot_df)
    else:
        st.error("데이터를 찾을 수 없습니다.")
