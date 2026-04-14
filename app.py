import streamlit as st
import pandas as pd

st.set_page_config(page_title="서울 상권 분석 (로컬 데이터)", layout="wide")
st.title("🚇 지하철역 주변 상권 분석 (CSV 기반)")

# 1. 데이터 로드 (업로드하신 csv 파일을 읽어옵니다)
@st.cache_data
def load_csv():
    try:
        # 파일명이 다를 수 있으니 확인해주세요. 여기서는 'data.csv'로 가정합니다.
        df = pd.read_csv('data.csv', encoding='cp949') 
        return df
    except:
        return None

df_raw = load_csv()

if df_raw is not None:
    # 2. 지역 선택 (CSV 내에 있는 행정동 리스트를 자동으로 가져옵니다)
    all_dongs = df_raw['행정동_코드_명'].unique()
    selected_dong = st.selectbox("분석할 지역(행정동)을 선택하세요", all_dongs)

    if st.button("데이터 분석 시작"):
        # 필터링
        filtered_df = df_raw[df_raw['행정동_코드_명'] == selected_dong]
        
        # 분기별 합산
        summary = filtered_df.groupby('기준_년분기_코드').agg({
            '개업_점포_수': 'sum',
            '폐업_점포_수': 'sum'
        }).reset_index()
        
        summary = summary.sort_values('기준_년분기_코드')

        st.success(f"✅ {selected_dong} 분석 완료!")
        
        # 지표 표시
        c1, c2 = st.columns(2)
        c1.metric("총 개업 수", f"{int(summary['개업_점포_수'].sum()):,}개")
        c2.metric("총 폐업 수", f"{int(summary['폐업_점포_수'].sum()):,}개")
        
        # 그래프
        st.line_chart(summary.set_index('기준_년분기_코드'))
        st.dataframe(summary, use_container_width=True)
else:
    st.error("GitHub에 'data.csv' 파일이 업로드되지 않았습니다.")
    st.info("방금 직접 받으신 엑셀 파일을 data.csv로 이름을 바꿔서 깃허브에 올려주세요!")
