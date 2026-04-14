import streamlit as st
import pandas as pd
import glob

st.set_page_config(page_title="서울 요식업 상권 리포트", layout="wide")

st.title("📋 요식업 상권 상세 수치 리포트")
st.caption("그래프 없이 깔끔하게 수치와 표로만 구성된 버전입니다.")

# 1. 데이터 로드 및 전처리 (뚝섬역 추가)
STATION_MAP = {
    "강남역": "역삼1동", 
    "홍대입구역": "서교동", 
    "뚝섬역(성수)": "성수동1가1동", # 새로 추가된 성수/뚝섬 지역
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
FOOD_SERVICES = ["한식음식점", "중식음식점", "일식음식점", "양식음식점", "제과점", "패스트푸드점", "치킨전문점", "분식전문점", "호프-간이주점", "커피-음료"]

@st.cache_data
def load_all_data():
    all_files = glob.glob('서울시*.csv')
    if not all_files: return None
    df_list = [pd.read_csv(f, encoding='cp949') for f in all_files]
    return pd.concat(df_list, ignore_index=True)

df_raw = load_all_data()

if df_raw is not None:
    # 사이드바에서 지역 선택
    selected_station = st.sidebar.selectbox("📍 분석 지역 선택", list(STATION_MAP.keys()))
    target_dong = STATION_MAP[selected_station]
    
    filtered_df = df_raw[
        (df_raw['행정동_코드_명'] == target_dong) & 
        (df_raw['기준_년분기_코드'] >= 20221) &
        (df_raw['서비스_업종_코드_명'].isin(FOOD_SERVICES))
    ].copy()

    if not filtered_df.empty:
        # 데이터 타입 정리
        for col in ['개업_점포_수', '폐업_점포_수', '개업_율', '폐업_률', '점포_수']:
            filtered_df[col] = pd.to_numeric(filtered_df[col], errors='coerce')
        filtered_df['기준_년분기_코드'] = filtered_df['기준_년분기_코드'].astype(str)

        # [상단] 지역 전체 요약 (Metric 카드)
        latest_q = filtered_df['기준_년분기_코드'].max()
        summary_df = filtered_df[filtered_df['기준_년분기_코드'] == latest_q]
        
        st.subheader(f"📍 {selected_station}({target_dong}) {latest_q}분기 요약")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("현재 전체 점포", f"{int(summary_df['점포_수'].sum()):,}개")
        m2.metric("평균 개업률", f"{summary_df['개업_율'].mean():.1f}%")
        m3.metric("평균 폐업률", f"{summary_df['폐업_률'].mean():.1f}%")
        
        # 최다 업종 추출 시 예외 처리
        if not summary_df.empty:
            max_service = summary_df.loc[summary_df['점포_수'].idxmax(), '서비스_업종_코드_명']
            m4.metric("최다 업종", max_service)

        st.divider()

        # [하단] 업종별 상세 수치 (Tabs)
        st.subheader("🔍 업종별 상세 성적표")
        tabs = st.tabs(FOOD_SERVICES)

        for i, service in enumerate(FOOD_SERVICES):
            with tabs[i]:
                # 최신순 정렬
                service_df = filtered_df[filtered_df['서비스_업종_코드_명'] == service].sort_values('기준_년분기_코드', ascending=False)
                
                if not service_df.empty:
                    # 현재 분기 주요 수치 강조
                    latest = service_df.iloc[0]
                    
                    c1, c2, c3, c4 = st.columns(4)
                    c1.write(f"**현재 점포 수:** {int(latest['점포_수'])}개")
                    c2.write(f"**신규 개업:** {int(latest['개업_점포_수'])}개")
                    c3.write(f"**이번 폐업:** {int(latest['폐업_점포_수'])}개")
                    c4.write(f"**폐업률:** {latest['폐업_률']}%")

                    # 상세 이력 표 (2022년부터 전체 기록)
                    st.markdown("**📅 분기별 상세 기록 (2022~)**")
                    display_df = service_df[['기준_년분기_코드', '점포_수', '개업_점포_수', '폐업_점포_수', '개업_율', '폐업_률']].copy()
                    display_df.columns = ['년분기', '총 점포', '개업수', '폐업수', '개업률(%)', '폐업률(%)']
                    
                    # 수치 중심으로 깔끔하게 표 출력
                    st.table(display_df)
                else:
                    st.info(f"'{service}' 데이터가 이 지역에는 없습니다.")
    else:
        st.warning(f"{selected_station} 지역의 2022년 이후 요식업 데이터가 없습니다.")
else:
    st.error("CSV 파일이 없습니다. GitHub에 '서울시_상권분석...' 파일들을 업로드해주세요.")
