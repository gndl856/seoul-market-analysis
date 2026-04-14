import streamlit as st
import pandas as pd

st.set_page_config(page_title="서울 지하철 상권 분석", layout="wide")
st.title("🚇 지하철역 주변 상권 분석 (2022~2025)")

# 1. 지하철역 - 행정동 매칭 (데이터 내 '행정동_코드_명' 기준)
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
        # 엑셀 저장 시 인코딩에 맞춰 cp949 적용
        df = pd.read_csv('data.csv', encoding='cp949') 
        return df
    except:
        return None

df_raw = load_csv()

if df_raw is not None:
    selected_station = st.selectbox("분석할 지하철역을 선택하세요", list(STATION_MAP.keys()))
    target_dong = STATION_MAP[selected_station]

    if st.button(f"{selected_station} 분석 업데이트"):
        # 필터링 1: 행정동 매칭
        # 필터링 2: 2022년 1분기(20221) 이후 데이터만 포함
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
            summary['기준_년분기_코드'] = summary['기준_년분기_코드'].astype(str) # 축 표시 개선

            st.success(f"✅ {selected_station} ({target_dong}) 2022년 이후 데이터 로드 완료")
            
            # 메트릭
            c1, c2 = st.columns(2)
            c1.metric("총 개업 수", f"{int(summary['개업_점포_수'].sum()):,}개")
            c2.metric("총 폐업 수", f"{int(summary['폐업_점포_수'].sum()):,}개")
            
            # 그래프 섹션 (선 색상 커스텀)
            st.subheader(f"📊 {selected_station} 연도별 개폐업 추이 (2022~)")
            
            # 색상 지정: 개업은 파란색, 폐업은 빨간색
            chart_data = summary.set_index('기준_년분기_코드')[['개업_점포_수', '폐업_점포_수']]
            st.line_chart(chart_data, color=["#1f77b4", "#FF0000"]) # 파랑, 빨강 순서
            
            # 상세 데이터
            st.subheader("상세 통계 데이터")
            st.dataframe(summary, use_container_width=True)
        else:
            st.warning(f"2022년 이후의 '{target_dong}' 데이터가 CSV에 없습니다.")
else:
    st.error("GitHub 리포지토리에 'data.csv' 파일이 있는지 확인해 주세요.")
