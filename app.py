import streamlit as st
import pandas as pd
import glob
from datetime import datetime

st.set_page_config(page_title="서울 상권 및 유동인구 리포트", layout="wide")

st.title("📋 서울 상권 및 지하철 유동인구 리포트")

# 1. 데이터 로드 함수 (기존 개폐업 + 신규 지하철 데이터)
@st.cache_data
def load_all_data():
    # 상권 개폐업 데이터
    biz_files = glob.glob('서울시*.csv')
    df_biz = pd.concat([pd.read_csv(f, encoding='cp949') for f in biz_files], ignore_index=True) if biz_files else None
    
    # 지하철 승하차 데이터 (CARD_SUBWAY_MONTH_*.csv)
    subway_files = glob.glob('CARD_SUBWAY_MONTH_*.csv')
    df_subway = pd.concat([pd.read_csv(f, encoding='utf-8-sig' if 'utf-8' in f else 'cp949') for f in subway_files], ignore_index=True) if subway_files else None
    
    return df_biz, df_subway

df_biz_raw, df_subway_raw = load_all_data()

# 2. 지역 설정 (기존 리스트 유지)
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

# --- TAB 1: 기존 개폐업 현황 ---
with tab1:
    if df_biz_raw is not None:
        df_biz_raw['행정동_코드_명'] = df_biz_raw['행정동_코드_명'].str.replace(" ", "")
        filtered_biz = df_biz_raw[df_biz_raw['행정동_코드_명'].str.contains(target_dong, na=False)].copy()
        
        if not filtered_biz.empty:
            # (기존 소수점 한자리 로직 동일 적용...)
            st.subheader(f"📍 {selected_label} 상권 상세 (매칭: {target_dong})")
            # ... 기존 탭1 코드 내용 ... (지면상 생략, 구조 유지)
            st.info("기존에 완성된 개폐업 수치 표가 여기에 나타납니다.")
    else:
        st.error("상권 CSV 파일이 없습니다.")

# --- TAB 2: 지하철 유동인구 추이 (신규) ---
with tab2:
    if df_subway_raw is not None:
        # 지하철역 필터링 (역명에 타겟 키워드 포함)
        sub_df = df_subway_raw[df_subway_raw['역명'].str.contains(target_subway, na=False)].copy()
        
        if not sub_df.empty:
            # 날짜 처리
            sub_df['사용일자'] = pd.to_datetime(sub_df['사용일자'], format='%Y%m%d')
            sub_df['총승하차'] = sub_df['승차총승객수'] + sub_df['하차총승객수']
            sub_df['요일'] = sub_df['사용일자'].dt.weekday  # 0:월, 1:화 ... 6:일
            
            # 주차 계산 (2026-01-05 월요일이 포함된 주를 1주차로 설정하는 로직)
            # 요청하신 1월 6일(화)이 포함된 주는 1월 5일(월)부터 시작하는 주입니다.
            sub_df['주차'] = sub_df['사용일자'].apply(lambda x: f"{(x - pd.Timestamp('2026-01-05')).days // 7 + 1}주차")
            
            # 기간 분류 (월-목: 0,1,2,3 / 금-토: 4,5 / 일: 6)
            def categorize_day(day):
                if day <= 3: return "월~목(평균)"
                elif day <= 5: return "금~토(평균)"
                else: return "일요일"
            
            sub_df['기간분류'] = sub_df['요일'].apply(categorize_day)
            
            # 주차별/기간별 그룹화 및 평균 계산
            # 동일 역이 여러 노선(예: 1호선, 3호선 종로3가)일 경우 합산 후 평균
            weekly_sub = sub_df.groupby(['주차', '사용일자', '기간분류'])['총승하차'].sum().reset_index()
            final_sub = weekly_sub.groupby(['주차', '기간분류'])['총승하차'].mean().round(0).astype(int).unstack()
            
            # 열 순서 고정 및 인덱스 정렬
            final_sub = final_sub[['월~목(평균)', '금~토(평균)', '일요일']]
            final_sub.index = sorted(final_sub.index, key=lambda x: int(x.replace('주차', '')))
            
            st.subheader(f"🚉 {target_subway}역 주차별 유동인구 (승하차 합계)")
            st.table(final_sub.style.format("{:,}"))
            
            st.caption("※ 1주차 시작일: 2026년 1월 5일(월) / 데이터 출처: 서울시 지하철 승하차 정보")
        else:
            st.warning(f"'{target_subway}'역에 대한 지하철 데이터를 찾을 수 없습니다.")
    else:
        st.error("지하철 CSV 파일(CARD_SUBWAY_MONTH_...)이 없습니다.")
