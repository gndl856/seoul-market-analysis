import streamlit as st
import pandas as pd
import glob
from datetime import datetime

st.set_page_config(page_title="서울 상권 및 유동인구 리포트", layout="wide")

st.title("📋 서울 상권 및 지하철 유동인구 리포트")

# 1. 데이터 로드 함수 (data 폴더 및 메인 폴더 모두 탐색)
@st.cache_data
def load_all_data():
    # --- 상권 개폐업 데이터 로드 ---
    biz_files = glob.glob('data/서울시*.csv') + glob.glob('서울시*.csv')
    df_biz = None
    if biz_files:
        biz_list = []
        for f in biz_files:
            try:
                biz_list.append(pd.read_csv(f, encoding='cp949'))
            except:
                biz_list.append(pd.read_csv(f, encoding='utf-8-sig'))
        df_biz = pd.concat(biz_list, ignore_index=True)
    
    # --- 지하철 승하차 데이터 로드 ---
    subway_files = glob.glob('data/CARD_SUBWAY_MONTH_*.csv') + glob.glob('CARD_SUBWAY_MONTH_*.csv')
    df_subway = None
    if subway_files:
        sub_list = []
        for f in subway_files:
            try:
                # 깃허브/리눅스 환경에서 유니코드 에러 방지를 위해 utf-8-sig 우선 시도
                sub_list.append(pd.read_csv(f, encoding='utf-8-sig'))
            except:
                sub_list.append(pd.read_csv(f, encoding='cp949'))
        df_subway = pd.concat(sub_list, ignore_index=True)
    
    return df_biz, df_subway

df_biz_raw, df_subway_raw = load_all_data()

# 2. 분석 지역 설정
STATION_MAP = {
    "강남역": {"dong": "역삼1", "subway": "강남"},
    "홍대입구역": {"dong": "서교", "subway": "홍대입구"},
    "종로3가역": {"dong": "종로1", "subway": "종로3가"},
    "을지로3가역": {"dong": "을지로", "subway": "을지로3가"},
    "신촌역": {"dong": "신촌", "subway": "신촌"},
    "합정역": {"dong": "서교", "subway": "합정"},
    "신림역": {"dong": "신림", "subway": "신림"},
    "서울대입구역": {"dong": "청룡", "subway": "서울대입구"},
    "건대입구역": {"dong": "화양", "subway": "건대입구"},
    "잠실역": {"dong": "잠실6", "subway": "잠실"}
}

selected_label = st.sidebar.selectbox("📍 분석 지역 선택", list(STATION_MAP.keys()))
target_dong = STATION_MAP[selected_label]["dong"]
target_subway = STATION_MAP[selected_label]["subway"]

# 탭 구성
tab1, tab2 = st.tabs(["🏬 업종별 개폐업 현황", "🚉 역별 유동인구 추이"])

# --- TAB 1: 상권 개폐업 현황 ---
with tab1:
    if df_biz_raw is not None:
        df_biz_raw['행정동_코드_명'] = df_biz_raw['행정동_코드_명'].str.replace(" ", "")
        filtered_biz = df_biz_raw[
            (df_biz_raw['행정동_코드_명'].str.contains(target_dong, na=False)) & 
            (df_biz_raw['기준_년분기_코드'] >= 20221)
        ].copy()
        
        if not filtered_biz.empty:
            cols = ['개업_점포_수', '폐업_점포_수', '개업_율', '폐업_률', '점포_수']
            for col in cols:
                filtered_biz[col] = pd.to_numeric(filtered_biz[col], errors='coerce').fillna(0)
            
            filtered_biz['기준_년분기_코드'] = filtered_biz['기준_년분기_코드'].astype(str)
            
            # 업종 정의
            FOOD_SERVICES = ["한식음식점", "중식음식점", "일식음식점", "양식음식점", "제과점", "패스트푸드점", "치킨전문점", "분식전문점", "호프-간이주점", "커피-음료"]
            
            summary_grouped = filtered_biz[filtered_biz['서비스_업종_코드_명'].isin(FOOD_SERVICES)].groupby(['기준_년분기_코드', '서비스_업종_코드_명']).agg({
                '점포_수': 'sum', '개업_점포_수': 'sum', '폐업_점포_수': 'sum', '개업_율': 'mean', '폐업_률': 'mean'
            }).reset_index()

            latest_q = summary_grouped['기준_년분기_코드'].max()
            st.subheader(f"📍 {selected_label} {latest_q}분기 요약")
            
            latest_summary = summary_grouped[summary_grouped['기준_년분기_코드'] == latest_q]
            m1, m2, m3 = st.columns(3)
            m1.metric("현재 전체 점포", f"{int(latest_summary['점포_수'].sum()):,}개")
            m2.metric("평균 개업률", f"{latest_summary['개업_율'].mean():.1f}%")
            m3.metric("평균 폐업률", f"{latest_summary['폐업_률'].mean():.1f}%")

            st.divider()
            sub_tabs = st.tabs(FOOD_SERVICES)
            for i, service in enumerate(FOOD_SERVICES):
                with sub_tabs[i]:
                    service_df = summary_grouped[summary_grouped['서비스_업종_코드_명'] == service].sort_values('기준_년분기_코드', ascending=False)
                    if not service_df.empty:
                        # 상세 표 구성
                        display_df = service_df[['기준_년분기_코드', '점포_수', '개업_점포_수', '폐업_점포_수', '개업_율', '폐업_률']].copy()
                        display_df.columns = ['년분기', '총 점포', '개업수', '폐업수', '개업률(%)', '폐업률(%)']
                        # 정수 및 소수점 한자리 처리
                        for col in ['총 점포', '개업수', '폐업수']: display_df[col] = display_df[col].astype(int)
                        for col in ['개업률(%)', '폐업률(%)']: display_df[col] = display_df[col].map('{:.1f}'.format)
                        st.table(display_df)
                    else:
                        st.info("해당 업종 데이터가 없습니다.")
        else:
            st.warning("매칭된 상권 데이터가 없습니다.")
    else:
        st.error("상권 CSV 파일을 찾을 수 없습니다. (data 폴더 확인)")

# --- TAB 2: 지하철 유동인구 추이 ---
with tab2:
    if df_subway_raw is not None:
        sub_df = df_subway_raw[df_subway_raw['역명'].str.contains(target_subway, na=False)].copy()
        
        if not sub_df.empty:
            sub_df['사용일자'] = pd.to_datetime(sub_df['사용일자'], format='%Y%m%d', errors='coerce')
            sub_df = sub_df.dropna(subset=['사용일자'])
            sub_df['총승하차'] = sub_df['승차총승객수'] + sub_df['하차총승객수']
            sub_df['요일'] = sub_df['사용일자'].dt.weekday
            
            # 주차 계산 (2026-01-05 월요일 기준)
            sub_df['주차'] = sub_df['사용일자'].apply(lambda x: f"{(x - pd.Timestamp('2026-01-05')).days // 7 + 1}주차")
            
            def categorize_day(day):
                if day <= 3: return "월~목(평균)"
                elif day <= 5: return "금~토(평균)"
                else: return "일요일"
            
            sub_df['기간분류'] = sub_df['요일'].apply(categorize_day)
            
            # 주차별/기간별 평균 계산
            weekly_summary = sub_df.groupby(['주차', '사용일자', '기간분류'])['총승하차'].sum().reset_index()
            final_sub = weekly_summary.groupby(['주차', '기간분류'])['총승하차'].mean().round(0).astype(int).unstack()
            
            # 컬럼 순서 및 인덱스 정렬
            cols_order = [c for c in ["월~목(평균)", "금~토(평균)", "일요일"] if c in final_sub.columns]
            final_sub = final_sub[cols_order]
            final_sub.index = sorted(final_sub.index, key=lambda x: int(x.replace('주차', '')) if '주차' in x else 0)
            
            st.subheader(f"🚉 {target_subway}역 주차별 유동인구 (1일 평균 승하차)")
            st.table(final_sub.applymap(lambda x: "{:,}".format(x)))
            st.caption("※ 1주차 기준일: 2026년 1월 5일(월)")
        else:
            st.warning(f"'{target_subway}'역 데이터를 찾을 수 없습니다.")
    else:
        st.error("지하철 CSV 파일을 찾을 수 없습니다. (data 폴더 확인)")
