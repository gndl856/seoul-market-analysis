import streamlit as st
import pandas as pd
import glob

st.set_page_config(page_title="서울 지하철 요식업 상권 분석", layout="wide")
st.title("🍴 지하철역 주변 요식업 상권 분석 (2022~2024)")

# 지하철역 - 행정동 매칭
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

# 요식업에 해당하는 서비스 업종 리스트 (CSV 내 '서비스_업종_코드_명' 기준)
FOOD_SERVICES = [
    "한식음식점", "중식음식점", "일식음식점", "양식음식점", 
    "제과점", "패스트푸드점", "치킨전문점", "분식전문점", 
    "호프-간이주점", "커피-음료"
]

@st.cache_data
def load_all_data():
    all_files = glob.glob('서울시*.csv')
    if not all_files:
        return None
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
    selected_station = st.selectbox("분석할 지하철역을 선택하세요", list(STATION_MAP.keys()))
    target_dong = STATION_MAP[selected_station]

    if st.button(f"{selected_station} 요식업 분석 시작"):
        # 필터링: 행정동 + 2022년 이후 + 요식업종 한정
        filtered_df = df_raw[
            (df_raw['행정동_코드_명'] == target_dong) & 
            (df_raw['기준_년분기_코드'] >= 20221) &
            (df_raw['서비스_업종_코드_명'].isin(FOOD_SERVICES))
        ].copy()
        
        if not filtered_df.empty:
            # 숫자형 변환
            cols = ['개업_점포_수', '폐업_점포_수', '개업_율', '폐업_률']
            for col in cols:
                filtered_df[col] = pd.to_numeric(filtered_df[col], errors='coerce')

            # 분기별 합계 및 평균 계산
            summary = filtered_df.groupby('기준_년분기_코드').agg({
                '개업_점포_수': 'sum',
                '폐업_점포_수': 'sum',
                '개업_율': 'mean',
                '폐업_률': 'mean'
            }).reset_index()
            
            summary = summary.sort_values('기준_년분기_코드')
            summary['기준_년분기_코드'] = summary['기준_년분기_코드'].astype(str)

            st.success(f"✅ {selected_station} ({target_dong}) 요식업 데이터 분석 완료")
            
            # 1. 상단 지표
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("요식업 총 개업", f"{int(summary['개업_점포_수'].sum()):,}개")
            m2.metric("요식업 총 폐업", f"{int(summary['폐업_점포_수'].sum()):,}개")
            m3.metric("평균 개업률", f"{summary['개업_율'].mean():.1f}%")
            m4.metric("평균 폐업률", f"{summary['폐업_률'].mean():.1f}%")
            
            # 2. 개폐업 수 차트
            st.subheader("📊 요식업 개업 vs 폐업 수 추이")
            chart_count = summary.set_index('기준_년분기_코드')[['개업_점포_수', '폐업_점포_수']]
            st.line_chart(chart_count, color=["#1f77b4", "#FF0000"])
            
            # 3. 개폐업률 차트
            st.subheader("📈 요식업 개업률 vs 폐업률 (%)")
            chart_rate = summary.set_index('기준_년분기_코드')[['개업_율', '폐업_률']]
            st.area_chart(chart_rate, color=["#1f77b4", "#FF0000"])
            
            # 4. 세부 업종별 비중 (보너스 차트)
            st.subheader("🍕 분기별 요식업 세부 업종 데이터")
            st.dataframe(filtered_df[['기준_년분기_코드', '서비스_업종_코드_명', '개업_점포_수', '폐업_점포_수', '개업_율', '폐업_률']], use_container_width=True)
        else:
            st.warning("선택하신 지역의 요식업 데이터를 찾을 수 없습니다.")
else:
    st.error("CSV 파일을 업로드해주세요.")
