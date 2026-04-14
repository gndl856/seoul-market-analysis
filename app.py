import streamlit as st
import pandas as pd
import glob
import plotly.express as px

st.set_page_config(page_title="서울 요식업 상권 분석", layout="wide")
st.title("🍴 업종별 상세 상권 분석 대시보드")

# 1. 지역 매칭 및 데이터 로드
STATION_MAP = {
    "강남역": "역삼1동", "홍대입구역": "서교동", "종로3가역": "종로1.2.3.4가동",
    "을지로3가역": "을지로동", "신촌역": "신촌동", "합정역": "서교동",
    "신림역": "신림동", "서울대입구역": "청룡동", "건대입구역": "화양동",
    "잠실역": "잠실6동", "둔촌역": "둔촌2동"
}

FOOD_SERVICES = ["한식음식점", "중식음식점", "일식음식점", "양식음식점", "제과점", "패스트푸드점", "치킨전문점", "분식전문점", "호프-간이주점", "커피-음료"]

@st.cache_data
def load_all_data():
    all_files = glob.glob('서울시*.csv')
    if not all_files: return None
    df_list = [pd.read_csv(f, encoding='cp949' if 'cp949' else 'utf-8-sig') for f in all_files]
    return pd.concat(df_list, ignore_index=True)

df_raw = load_all_data()

if df_raw is not None:
    selected_station = st.sidebar.selectbox("📍 분석 지역 선택", list(STATION_MAP.keys()))
    target_dong = STATION_MAP[selected_station]
    
    filtered_df = df_raw[
        (df_raw['행정동_코드_명'] == target_dong) & 
        (df_raw['기준_년분기_코드'] >= 20221) &
        (df_raw['서비스_업종_코드_명'].isin(FOOD_SERVICES))
    ].copy()

    if not filtered_df.empty:
        # 데이터 정리
        for col in ['개업_점포_수', '폐업_점포_수', '개업_율', '폐업_률', '점포_수']:
            filtered_df[col] = pd.to_numeric(filtered_df[col], errors='coerce')
        filtered_df['기준_년분기_코드'] = filtered_df['기준_년분기_코드'].astype(str)

        # --- 대시보드 레이아웃 ---
        
        # 상단: 지역 전체 요약
        st.subheader(f"📊 {selected_station} 요식업 전체 요약")
        c1, c2, c3 = st.columns(3)
        total_stores = filtered_df[filtered_df['기준_년분기_코드'] == filtered_df['기준_년분기_코드'].max()]['점포_수'].sum()
        c1.metric("현재 총 요식업 점포", f"{int(total_stores)}개")
        c2.metric("누적 개업(22년~)", f"{int(filtered_df['개업_점포_수'].sum())}개")
        c3.metric("누적 폐업(22년~)", f"{int(filtered_df['폐업_점포_수'].sum())}개", delta_color="inverse")

        st.divider()

        # 중단: 업종별 탭 (이 부분이 핵심입니다!)
        st.subheader("🔍 업종별 상세 보기")
        tabs = st.tabs(FOOD_SERVICES) # 요식업종별로 클릭 가능한 탭 생성

        for i, service in enumerate(FOOD_SERVICES):
            with tabs[i]:
                service_df = filtered_df[filtered_df['서비스_업종_코드_명'] == service].sort_values('기준_년분기_코드')
                
                if not service_df.empty:
                    col_chart, col_data = st.columns([2, 1])
                    
                    with col_chart:
                        # 해당 업종의 개폐업 수 추이
                        fig = px.line(service_df, x='기준_년분기_코드', y=['개업_점포_수', '폐업_점포_수'],
                                      title=f"{service} 분기별 개폐업 추이",
                                      color_discrete_map={'개업_점포_수': '#1f77b4', '폐업_점포_수': '#FF0000'},
                                      markers=True)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # 해당 업종의 폐업률 추이
                        fig_rate = px.area(service_df, x='기준_년분기_코드', y='폐업_률', 
                                           title=f"{service} 폐업률 추이 (%)",
                                           color_discrete_sequence=['#FF4B4B'])
                        st.plotly_chart(fig_rate, use_container_width=True)
                    
                    with col_data:
                        st.write(f"**{service}** 상세 지표")
                        st.dataframe(service_df[['기준_년분기_코드', '점포_수', '개업_점포_수', '폐업_점포_수', '폐업_률']], 
                                     hide_index=True, use_container_width=True)
                else:
                    st.info(f"해당 지역에 {service} 데이터가 없습니다.")

    else:
        st.warning("데이터가 없습니다.")
