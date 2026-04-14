import streamlit as st
import pandas as pd
import glob
import os

st.set_page_config(page_title="서울 지하철 상권 분석", layout="wide")
st.title("🚇 지하철역 주변 상권 분석 (2022~2024)")

# 1. 지하철역 - 행정동 매칭
STATION_MAP = {
    "강남역": "역삼1동",
    "홍대입구역": "서교동",
    "종로3가역": "종로1.2.3.4가동",
    "을지로3가역": "을지로동",
    "신촌역": "신촌동",
    "합정역": "서교동",
    "신림역": "신림동",
    "서울대입구역": "청룡동",
    "건대입구역": "화양동",
    "잠실역": "잠실6동",
    "둔촌역": "둔촌2동"
}

@st.cache_data
def load_all_data():
    # '서울시'로 시작하고 '.csv'로 끝나는 모든 파일을 찾아서 합칩니다.
    all_files = glob.glob('서울시*.csv')
    
    if not all_files:
        return None
        
    df_list = []
    for filename in all_files:
        # 파일별로 인코딩이 다를 수 있어 예외처리를 추가합니다.
        try:
            temp_df = pd.read_csv(filename, encoding='cp949')
        except:
            temp_df = pd.read_csv(filename, encoding='utf-8-sig')
        df_list.append(temp_df)
    
    return pd.concat(df_list, ignore_index=True)

df_raw = load_all_data()

if df_raw is not None:
    selected_station = st.selectbox("분석할 지하철역을 선택하세요", list(STATION_MAP.keys()))
    target_dong = STATION_MAP[selected_station]

    if st.button(f"{selected_station} 분석 시작"):
        # 20221(2022년 1분기) 이후 데이터 필터링
        filtered_df = df_raw[
            (df_raw['행정동_코드_명'] == target_dong) & 
            (df_raw['기준_년분기_코드'] >= 20221)
        ]
        
        if not filtered_df.empty:
            # 분기별 합산
            summary = filtered_df.groupby('기준_년분기_코드').agg({
                '개업_점포_수': 'sum',
                '폐업_점포_수': 'sum'
            }).reset_index()
            
            summary = summary.sort_values('기준_년분기_코드')
            summary['기준_년분기_코드'] = summary['기준_년분기_코드'].astype(str)

            st.success(f"✅ {selected_station} 데이터 로드 완료 (2022~2024)")
            
            # 메트릭
            c1, c2 = st.columns(2)
            c1.metric("총 개업 수", f"{int(summary['개업_점포_수'].sum()):,}개")
            c2.metric("총 폐업 수", f"{int(summary['폐업_점포_수'].sum()):,}개")
            
            # 그래프 (폐업은 빨간색)
            chart_data = summary.set_index('기준_년분기_코드')[['개업_점포_수', '폐업_점포_수']]
            st.line_chart(chart_data, color=["#1f77b4", "#FF0000"])
            
            st.dataframe(summary, use_container_width=True)
        else:
            st.warning("선택하신 조건에 맞는 데이터가 없습니다.")
else:
    st.error("GitHub에 CSV 파일이 하나도 보이지 않습니다. 파일들을 업로드해주세요!")
