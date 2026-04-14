import streamlit as st
import pandas as pd
import glob

st.set_page_config(page_title="서울 요식업 상권 리포트", layout="wide")

st.title("📋 요식업 상권 상세 수치 리포트")
st.caption("요청하신 대로 뚝섬역과 둔촌역을 완전히 제거한 버전입니다.")

# 1. STATION_MAP (뚝섬, 둔촌역을 리스트에서 완전히 삭제했습니다)
STATION_MAP = {
    "강남역": "역삼1", 
    "홍대입구역": "서교", 
    "종로3가역": "종로1",      
    "을지로3가역": "을지로", 
    "신촌역": "신촌", 
    "합정역": "서교",
    "신림역": "신림", 
    "서울대입구역": "청룡", 
    "건대입구역": "화양",
    "잠실역": "잠실6"
}

FOOD_SERVICES = ["한식음식점", "중식음식점", "일식음식점", "양식음식점", "제과점", "패스트푸드점", "치킨전문점", "분식전문점", "호프-간이주점", "커피-음료"]

@st.cache_data
def load_all_data():
    all_files = glob.glob('서울시*.csv')
    if not all_files: return None
    df_list = []
    for f in all_files:
        try:
            df_list.append(pd.read_csv(f, encoding='cp949'))
        except:
            df_list.append(pd.read_csv(f, encoding='utf-8-sig'))
    return pd.concat(df_list, ignore_index=True)

df_raw = load_all_data()

if df_raw is not None:
    # 데이터 전처리: 행정동 명칭에서 공백 제거
    df_raw['행정동_코드_명'] = df_raw['행정동_코드_명'].str.replace(" ", "")
    
    # 사이드바 선택 메뉴 (여기서 뚝섬역이 이제 안 보일 거예요!)
    selected_station = st.sidebar.selectbox("📍 분석 지역 선택", list(STATION_MAP.keys()))
    keyword = STATION_MAP[selected_station]
    
    # 필터링
    filtered_df = df_raw[
        (df_raw['행정동_코드_명'].str.contains(keyword, na=False)) & 
        (df_raw['기준_년분기_코드'] >= 20221) &
        (df_raw['서비스_업종_코드_명'].isin(FOOD_SERVICES))
    ].copy()

    if not filtered_df.empty:
        for col in ['개업_점포_수', '폐업_점포_수', '개업_율', '폐업_률', '점포_수']:
            filtered_df[col] = pd.to_numeric(filtered_df[col], errors='coerce')
        filtered_df['기준_년분기_코드'] = filtered_df['기준_년분기_코드'].astype(str)

        summary_grouped = filtered_df.groupby(['기준_년분기_코드', '서비스_업종_코드_명']).agg({
            '점포_수': 'sum',
            '개업_점포_수': 'sum',
            '폐업_점포_수': 'sum',
            '개업_율': 'mean',
            '폐업_률': 'mean'
        }).reset_index()

        real_name = filtered_df['행정동_코드_명'].iloc[0]
        latest_q = summary_grouped['기준_년분기_코드'].max()
        
        st.subheader(f"📍 {selected_station} 분석 (매칭된 동네: {real_name})")
        
        latest_summary = summary_grouped[summary_grouped['기준_년분기_코드'] == latest_q]
        m1, m2, m3 = st.columns(3)
        m1.metric("현재 전체 점포", f"{int(latest_summary['점포_수'].sum()):,}개")
        m2.metric("평균 개업률", f"{latest_summary['개업_율'].mean():.1f}%")
        m3.metric("평균 폐업률", f"{latest_summary['폐업_률'].mean():.1f}%")

        st.divider()

        st.subheader("🔍 업종별 상세 성적표")
        tabs = st.tabs(FOOD_SERVICES)

        for i, service in enumerate(FOOD_SERVICES):
            with tabs[i]:
                service_df = summary_grouped[summary_grouped['서비스_업종_코드_명'] == service].sort_values('기준_년분기_코드', ascending=False)
                if not service_df.empty:
                    latest = service_df.iloc[0]
                    c1, c2, c3, c4 = st.columns(4)
                    c1.write(f"**총 점포:** {int(latest['점포_수'])}개")
                    c2.write(f"**신규 개업:** {int(latest['개업_점포_수'])}개")
                    c3.write(f"**이번 폐업:** {int(latest['폐업_점포_수'])}개")
                    c4.write(f"**폐업률:** {latest['폐업_률']:.1f}%")

                    st.markdown(f"**📅 {service} 분기별 상세 기록**")
                    display_df = service_df[['기준_년분기_코드', '점포_수', '개업_점포_수', '폐업_점포_수', '개업_율', '폐업_률']].copy()
                    display_df.columns = ['년분기', '총 점포', '개업수', '폐업수', '개업률(%)', '폐업률(%)']
                    st.table(display_df)
                else:
                    st.info(f"'{service}' 데이터가 없습니다.")
else:
    st.error("CSV 파일을 찾을 수 없습니다.")
