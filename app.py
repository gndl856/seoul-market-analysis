import streamlit as st
import pandas as pd
import requests

# 1. 설정
st.set_page_config(page_title="서울 상권 점포수 분석", layout="wide")
API_KEY = "4d59784b56676e64363847736b5362"

# --- [보존된 유동인구 분석 함수] ---
def get_subway_data(station_name):
    pass

# --- [점포수 데이터 수집 함수] ---
def get_store_trend(market_name, quarters):
    all_data = []
    # 점포수 데이터셋은 서비스명이 VwsmTrdarStorQq 입니다.
    for q in quarters:
        url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/VwsmTrdarStorQq/1/1000/{q}"
        try:
            res = requests.get(url, timeout=10).json()
            if 'VwsmTrdarStorQq' in res:
                df = pd.DataFrame(res['VwsmTrdarStorQq']['row'])
                # 1. 해당 상권 필터링
                # 2. 요식업(외식업) 관련 업종만 필터링 (서비스 업종 코드 기준)
                # 서울시 기준 외식업은 보통 '외식업' 대분류로 묶입니다.
                target_df = df[
                    (df['TRDAR_CD_NM'] == market_name) & 
                    (df['SVC_INDUTY_CD_NM'].str.contains('한식|중식|일식|양식|제과|커피|패스트푸드|분식'))
                ].copy()
                
                if not target_df.empty:
                    target_df['기준분기'] = q
                    all_data.append(target_df)
        except:
            continue
    return pd.concat(all_data) if all_data else pd.DataFrame()

# 2. 메인 UI
st.title("🍔 요식업 점포수 추이 및 증감 분석")
st.info("정상 작동하는 '점포수 API'를 활용해 상권의 활성도를 유추합니다.")

# 분석 대상 상권 입력
target_market = st.text_input("분석할 상권명을 입력하세요", value="강남역")

# 비교할 분기 설정 (최근 1년치 예시)
quarters = ["20231", "20232", "20233", "20234"]

if st.button("분석 시작"):
    with st.spinner(f'{target_market} 요식업 데이터를 분석 중...'):
        trend_df = get_store_trend(target_market, quarters)
        
    if not trend_df.empty:
        # 보기 좋게 정리
        display_df = trend_df[['기준분기', 'SVC_INDUTY_CD_NM', 'STOR_CO']].copy()
        display_df.columns = ['분기', '업종명', '점포수']
        display_df['점포수'] = display_df['점포수'].astype(int)
        
        # 업종별/분기별 피벗 테이블 생성
        pivot_df = display_df.pivot_table(index='업종명', columns='분기', values='점포수', aggfunc='sum').fillna(0)
        
        # 증감 계산 (최근 분기 - 이전 분기)
        if len(quarters) >= 2:
            pivot_df['전체증감'] = pivot_df[quarters[-1]] - pivot_df[quarters[0]]
        
        st.subheader(f"📊 {target_market} 요식업 점포수 변동 (23년 1Q ~ 4Q)")
        st.dataframe(pivot_df, use_container_width=True)
        
        # 하단 분석 코멘트
        total_growth = pivot_df['전체증감'].sum() if '전체증감' in pivot_df.columns else 0
        if total_growth > 0:
            st.success(f"📈 해당 기간 동안 요식업 점포가 총 {int(total_growth)}개 순증했습니다. (개업 > 폐업)")
        elif total_growth < 0:
            st.warning(f"📉 해당 기간 동안 요식업 점포가 총 {int(abs(total_growth))}개 감소했습니다. (폐업 > 개업)")
        else:
            st.info("점포 수에 변동이 없거나 데이터가 동일합니다.")
            
    else:
        st.error("데이터를 찾을 수 없습니다. 상권명을 정확히 입력했는지 확인해 주세요.")
