import streamlit as st
import pandas as pd
import glob
import plotly.express as px  # 업종별 비교를 위해 추가

st.set_page_config(page_title="서울 지하철 요식업 상권 분석", layout="wide")
st.title("🍴 지하철역 주변 요식업 업종별 상세 분석")

# 1. 지하철역 - 행정동 매칭
STATION_MAP = {
    "강남역": "역삼1동", "홍대입구역": "서교동", "종로3가역": "종로1.2.3.4가동",
    "을지로3가역": "을지로동", "신촌역": "신촌동", "합정역": "서교동",
    "신림역": "신림동", "서울대입구역": "청룡동", "건대입구역": "화양동",
    "잠실역": "잠실6동", "둔촌역": "둔촌2동"
}

# 요식업종 리스트
FOOD_SERVICES = [
    "한식음식점", "중식음식점", "일식음식점", "양식음식점", 
    "제과점", "패스트푸드점", "치킨전문점", "분식전문점", 
    "호프-간이주점", "커피-음료"
]

@st.cache_data
def load_all_data():
    all_files = glob.glob('서울시*.csv')
    if not all_files: return None
    df_list = []
    for filename in all_files:
        try:
            temp_df = pd.read_csv(filename, encoding='cp949')
        except:
            temp_df = pd.read_csv(filename, encoding='utf-8-sig')
        df_list.append(temp_df)
    return pd.concat(df_list, ignore_index=True)

df_raw = load_all_data()

if df_raw is not None:
    # 사이드바에서 지역 선택
    selected_station = st.sidebar.selectbox("📍 분석 지역 선택", list(STATION_MAP.keys()))
    target_dong = STATION_MAP[selected_station]
    
    # 분석 기간 필터링
    filtered_df = df_raw[
        (df_raw['행정동_코드_명'] == target_dong) & 
        (df_raw['기준_년분기_코드'] >= 20221) &
        (df_raw['서비스_업종_코드_명'].isin(FOOD_SERVICES))
    ].copy()

    if not filtered_df.empty:
        # 데이터 타입 변환
        for col in ['개업_점포_수', '폐업_점포_수', '개업_율', '폐업_률', '점포_수']:
            filtered_df[col] = pd.to_numeric(filtered_df[col], errors='coerce')

        # --- 메인 대시보드 ---
        st.subheader(f"✅ {selected_station}({target_dong}) 요식업 현황")
        
        # 1. 업종별 점포 비중 (파이 차트)
        latest_quarter = filtered_df['기준_년분기_코드'].max()
        latest_df = filtered_df[filtered_df['기준_년분기_코드'] == latest_quarter]
        
        fig_pie = px.pie(latest_df, values='점포_수', names='서비스_업종_코드_명', 
                         title=f"현재({latest_quarter}) 가장 많은 요식업종 비중",
                         hole=.3, color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig_pie, use_container_width=True)

        # 2. 업종별 개업/폐업 수 비교 (막대 그래프)
        st.subheader("📊 어떤 업종이 가장 많이 생기고 문을 닫았을까?")
        category_sum = filtered_df.groupby('서비스_업종_코드_명').agg({
            '개업_점포_수': 'sum',
            '폐업_점포_수': 'sum'
        }).reset_index()

        fig_bar = px.bar(category_sum, x='서비스_업종_코드_명', y=['개업_점포_수', '폐업_점포_수'],
                         barmode='group', title="업종별 누적 개폐업 수 비교",
                         color_discrete_map={'개업_점포_수': '#1f77b4', '폐업_점포_수': '#FF0000'})
        st.plotly_chart(fig_bar, use_container_width=True)

        # 3. 업종별 개폐업률 추이 (멀티 선택 필터)
        st.subheader("📈 업종별 상세 추이 확인")
        selected_sub_services = st.multiselect("확인하고 싶은 업종을 선택하세요", 
                                              FOOD_SERVICES, default=["한식음식점", "커피-음료"])
        
        if selected_sub_services:
            trend_df = filtered_df[filtered_df['서비스_업종_코드_명'].isin(selected_sub_services)]
            trend_df['기준_년분기_코드'] = trend_df['기준_년분기_코드'].astype(str)
            
            fig_line = px.line(trend_df, x='기준_년분기_코드', y='폐업_률', color='서비스_업종_코드_명',
                               title="선택 업종별 폐업률 추이 (%)", markers=True)
            st.plotly_chart(fig_line, use_container_width=True)
            
        # 4. 상세 데이터 테이블
        with st.expander("🔍 전체 요식업 상세 데이터 보기"):
            st.dataframe(filtered_df.sort_values(['기준_년분기_코드', '개업_점포_수'], ascending=[False, False]), 
                         use_container_width=True)
    else:
        st.warning("데이터가 없습니다.")
else:
    st.error("CSV 파일을 업로드해주세요.")
