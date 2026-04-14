import streamlit as st
import pandas as pd
import glob

st.set_page_config(page_title="서울 요식업 상권 리포트", layout="wide")

st.title("📋 요식업 상권 상세 수치 리포트")
st.caption("뚝섬(성수), 종로3가 매칭 수정 및 둔촌역 삭제 버전입니다.")

# 1. STATION_MAP 정밀 수정 (데이터상의 정확한 명칭으로 변경)
# 둔촌역은 리스트에서 완전히 제거했습니다.
STATION_MAP = {
    "강남역": "역삼1동", 
    "홍대입구역": "서교동", 
    "뚝섬역(성수)": "성수동1가제1동", # '제'가 포함된 명칭으로 수정
    "종로3가역": "종로1·2·3·4가동", # 특수기호(·) 확인 필요하여 표준 명칭 적용
    "을지로3가역": "을지로동", 
    "신촌역": "신촌동", 
    "합정역": "서교동",
    "신림역": "신림동", 
    "서울대입구역": "청룡동", 
    "건대입구역": "화양동",
    "잠실역": "잠실6동"
}

FOOD_SERVICES = ["한식음식점", "중식음식점", "일식음식점", "양식음식점", "제과점", "패스트푸드점", "치킨전문점", "분식전문점", "호프-간이주점", "커피-음료"]

@st.cache_data
def load_all_data():
    all_files = glob.glob('서울시*.csv')
    if not all_files: return None
    df_list = []
    for f in all_files:
        try:
            # 윈도우 엑셀 형식(cp949) 우선 시도
            df_list.append(pd.read_csv(f, encoding='cp949'))
        except:
            df_list.append(pd.read_csv(f, encoding='utf-8-sig'))
    return pd.concat(df_list, ignore_index=True)

df_raw = load_all_data()

if df_raw is not None:
    # 2. 동네 이름 보정 (데이터 내의 공백이나 특수문자 차이 해결)
    df_raw['행정동_코드_명'] = df_raw['행정동_코드_명'].str.strip()
    
    selected_station = st.sidebar.selectbox("📍 분석 지역 선택", list(STATION_MAP.keys()))
    target_dong = STATION_MAP[selected_station]
    
    # 필터링
    filtered_df = df_raw[
        (df_raw['행정동_코드_명'] == target_dong) & 
        (df_raw['기준_년분기_코드'] >= 20221) &
        (df_raw['서비스_업종_코드_명'].isin(FOOD_SERVICES))
    ].copy()

    if not filtered_df.empty:
        for col in ['개업_점포_수', '폐업_점포_수', '개업_율', '폐업_률', '점포_수']:
            filtered_df[col] = pd.to_numeric(filtered_df[col], errors='coerce')
        filtered_df['기준_년분기_코드'] = filtered_df['기준_년분기_코드'].astype(str)

        latest_q = filtered_df['기준_년분기_코드'].max()
        summary_df = filtered_df[filtered_df['기준_년분기_코드'] == latest_q]
        
        st.subheader(f"📍 {selected_station}({target_dong}) {latest_q}분기 요약")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("현재 전체 점포", f"{int(summary_df['점포_수'].sum()):,}개")
        m2.metric("평균 개업률", f"{summary_df['개업_율'].mean():.1f}%")
        m3.metric("평균 폐업률", f"{summary_df['폐업_률'].mean():.1f}%")
        
        if not summary_df.empty:
            m4.metric("최다 업종", summary_df.loc[summary_df['점포_수'].idxmax(), '서비스_업종_코드_명'])

        st.divider()

        st.subheader("🔍 업종별 상세 성적표")
        tabs = st.tabs(FOOD_SERVICES)

        for i, service in enumerate(FOOD_SERVICES):
            with tabs[i]:
                service_df = filtered_df[filtered_df['서비스_업종_코드_명'] == service].sort_values('기준_년분기_코드', ascending=False)
                if not service_df.empty:
                    latest = service_df.iloc[0]
                    c1, c2, c3, c4 = st.columns(4)
                    c1.write(f"**점포 수:** {int(latest['점포_수'])}개")
                    c2.write(f"**신규 개업:** {int(latest['개업_점포_수'])}개")
                    c3.write(f"**이번 폐업:** {int(latest['폐업_점포_수'])}개")
                    c4.write(f"**폐업률:** {latest['폐업_률']}%")

                    st.markdown("**📅 분기별 상세 기록 (2022~)**")
                    display_df = service_df[['기준_년분기_코드', '점포_수', '개업_점포_수', '폐업_점포_수', '개업_율', '폐업_률']].copy()
                    display_df.columns = ['년분기', '총 점포', '개업수', '폐업수', '개업률(%)', '폐업률(%)']
                    st.table(display_df)
                else:
                    st.info(f"'{service}' 데이터가 이 지역에는 없습니다.")
    else:
        # 데이터가 없을 경우 리스트 확인용 메시지 출력
        st.warning(f"'{target_dong}' 명칭으로 검색된 데이터가 없습니다.")
        if st.checkbox("데이터 내부 행정동 명칭 확인해보기"):
            st.write(df_raw['행정동_코드_명'].unique()[:50]) # 상위 50개만 출력
else:
    st.error("CSV 파일을 찾을 수 없습니다.")
