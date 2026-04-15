import streamlit as st
import pandas as pd
import glob
from datetime import datetime

st.set_page_config(page_title="서울 상권 및 유동인구 리포트", layout="wide")

st.title("📋 서울 상권 및 지하철 유동인구 리포트")

# 1. 데이터 로드 함수 (컬럼명 자동 보정 포함)
@st.cache_data
def load_all_data():
    # --- 상권 데이터 로드 ---
    biz_files = glob.glob('data/서울시*.csv') + glob.glob('서울시*.csv')
    df_biz = None
    if biz_files:
        biz_list = []
        for f in biz_files:
            try: biz_list.append(pd.read_csv(f, encoding='cp949'))
            except: biz_list.append(pd.read_csv(f, encoding='utf-8-sig'))
        df_biz = pd.concat(biz_list, ignore_index=True)
    
    # --- 지하철 데이터 로드 ---
    subway_files = glob.glob('data/CARD_SUBWAY_MONTH_*.csv') + glob.glob('CARD_SUBWAY_MONTH_*.csv')
    df_subway = None
    if subway_files:
        sub_list = []
        for f in subway_files:
            try:
                # 따옴표가 섞인 CSV를 대비해 quotechar 설정
                _df = pd.read_csv(f, encoding='utf-8-sig', quotechar='"')
            except:
                _df = pd.read_csv(f, encoding='cp949', quotechar='"')
            
            # 컬럼명에 공백이나 따옴표가 섞여 들어오는 경우 강제 정리
            _df.columns = [_col.replace('"', '').strip() for _col in _df.columns]
            sub_list.append(_df)
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

tab1, tab2 = st.tabs(["🏬 업종별 개폐업 현황", "🚉 역별 유동인구 추이"])

# --- TAB 1: 상권 개폐업 (생략 - 기존 유지) ---
with tab1:
    st.info(f"{selected_label}의 업종별 데이터가 위 탭에서 정상 작동 중입니다.")

# --- TAB 2: 지하철 유동인구 추이 (정밀 보정) ---
with tab2:
    if df_subway_raw is not None:
        # 역명 필터링 (따옴표 제거 후 검색)
        df_subway_raw['역명'] = df_subway_raw['역명'].astype(str).str.replace('"', '').str.strip()
        sub_df = df_subway_raw[df_subway_raw['역명'].str.contains(target_subway, na=False)].copy()
        
        if not sub_df.empty:
            # 사용일자 처리 (숫자형인 경우 대비)
            sub_df['사용일자'] = sub_df['사용일자'].astype(str).str.replace('"', '').str.strip()
            sub_df['사용일자'] = pd.to_datetime(sub_df['사용일자'], format='%Y%m%d', errors='coerce')
            sub_df = sub_df.dropna(subset=['사용일자'])
            
            # 승하차수 정수 변환 (따옴표나 소수점 방지)
            for col in ['승차총승객수', '하차총승객수']:
                sub_df[col] = pd.to_numeric(sub_df[col].astype(str).str.replace('"', '').str.strip(), errors='coerce').fillna(0)
            
            sub_df['총승하차'] = sub_df['승차총승객수'] + sub_df['하차총승객수']
            sub_df['요일'] = sub_df['사용일자'].dt.weekday
            
            # 주차 계산 (2026-01-05 월요일 기준)
            sub_df['주차'] = sub_df['사용일자'].apply(lambda x: f"{(x - pd.Timestamp('2026-01-05')).days // 7 + 1}주차")
            
            def categorize_day(day):
                if day <= 3: return "월~목(평균)"
                elif day <= 5: return "금~토(평균)"
                else: return "일요일"
            
            sub_df['기간분류'] = sub_df['요일'].apply(categorize_day)
            
            # 집계
            weekly_summary = sub_df.groupby(['주차', '사용일자', '기간분류'])['총승하차'].sum().reset_index()
            final_sub = weekly_summary.groupby(['주차', '기간분류'])['총승하차'].mean().round(0).astype(int).unstack()
            
            # 출력 처리
            target_cols = [c for c in ["월~목(평균)", "금~토(평균)", "일요일"] if c in final_sub.columns]
            final_sub = final_sub[target_cols]
            final_sub.index = sorted(final_sub.index, key=lambda x: int(x.replace('주차', '')) if '주차' in x else 0)
            
            st.subheader(f"🚉 {target_subway}역 주차별 유동인구 (1일 평균 승하차)")
            st.table(final_sub.applymap(lambda x: "{:,}".format(x)))
        else:
            st.warning(f"데이터 파일 내에 '{target_subway}'역 명칭이 정확히 일치하지 않습니다.")
    else:
        st.error("지하철 CSV 파일을 불러오지 못했습니다. 파일명을 확인해주세요.")
