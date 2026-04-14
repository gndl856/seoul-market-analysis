import streamlit as st
import pandas as pd

st.set_page_config(page_title="서울 지하철 상권 분석", layout="wide")
st.title("🚇 지하철역 주변 상권 분석 (로컬 데이터 기반)")

# 1. 지하철역 - 행정동 매칭 사전 (주요 역 위주)
# CSV에 있는 '행정동_코드_명'과 정확히 일치해야 합니다.
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
def load_csv():
    try:
        # 파일 인코딩은 엑셀 저장 방식에 따라 'cp949' 또는 'utf-8-sig'를 사용합니다.
        df = pd.read_csv('data.csv', encoding='cp949') 
        return df
    except:
        return None

df_raw = load_csv()

if df_raw is not None:
    # 지하철역 선택 UI
    selected_station = st.selectbox("분석할 지하철역을 선택하세요", list(STATION_MAP.keys()))
    target_dong = STATION_MAP[selected_station]

    if st.button(f"{selected_station} 데이터 분석 시작"):
        # 매칭된 행정동으로 데이터 필터링
        filtered_df = df_raw[df_raw['행정동_코드_명'] == target_dong]
        
        if not filtered_df.empty:
            # 기준_년분기_코드 별로 개업/폐업 점포 수 합산
            summary = filtered_df.groupby('기준_년분기_코드').agg({
                '개업_점포_수': 'sum',
                '폐업_점포_수': 'sum'
            }).reset_index()
            
            summary = summary.sort_values('기준_년분기_코드')

            st.success(f"✅ {selected_station} ({target_dong}) 분석 완료!")
            
            # 상단 메트릭
            c1, c2 = st.columns(2)
            c1.metric("총 개업 수", f"{int(summary['개업_점포_수'].sum()):,}개")
            c2.metric("총 폐업 수", f"{int(summary['폐업_점포_수'].sum()):,}개")
            
            # 추이 그래프
            st.subheader(f"📊 {selected_station} 상권 개폐업 추이")
            st.line_chart(summary.set_index('기준_년분기_코드'))
            
            # 상세 데이터 표
            st.subheader("상세 데이터")
            st.dataframe(summary, use_container_width=True)
        else:
            st.warning(f"현재 CSV 파일 내에 '{target_dong}' 데이터가 존재하지 않습니다.")
else:
    st.error("GitHub에 'data.csv' 파일이 없습니다. 파일을 먼저 업로드해주세요.")
