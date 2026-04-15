import streamlit as st
import pandas as pd
import glob
from datetime import datetime, timedelta

st.set_page_config(page_title="서울 상권 및 유동인구 리포트", layout="wide")

st.title("📋 서울 상권 및 지하철 유동인구 리포트")

# 1. 데이터 로드 및 강제 클리닝 함수
@st.cache_data
def load_all_data():
    biz_files = glob.glob('data/서울시*.csv') + glob.glob('서울시*.csv')
    df_biz = pd.DataFrame()
    if biz_files:
        biz_list = []
        for f in biz_files:
            try: biz_list.append(pd.read_csv(f, encoding='cp949'))
            except: biz_list.append(pd.read_csv(f, encoding='utf-8-sig'))
        if biz_list: df_biz = pd.concat(biz_list, ignore_index=True)
    
    subway_files = glob.glob('data/CARD_SUBWAY_MONTH_*.csv') + glob.glob('CARD_SUBWAY_MONTH_*.csv')
    df_subway = pd.DataFrame()
    if subway_files:
        sub_list = []
        for f in subway_files:
            try: _df = pd.read_csv(f, encoding='utf-8-sig', index_col=False)
            except: _df = pd.read_csv(f, encoding='cp949', index_col=False)
            
            _df.columns = [_col.replace('"', '').strip() for _col in _df.columns]
            _df = _df.astype(str).apply(lambda x: x.str.replace('"', '').str.strip())
            _df = _df.loc[:, ~_df.columns.str.contains('^Unnamed')]
            sub_list.append(_df)
        if sub_list: df_subway = pd.concat(sub_list, ignore_index=True)
    
    return df_biz, df_subway

df_biz_raw, df_subway_raw = load_all_data()

# 2. 분석 지역 설정 (노선 정보 추가)
STATION_MAP = {
    "강남역": {"dong": "역삼1", "subway": "강남", "line": ["2호선"]},
    "홍대입구역": {"dong": "서교", "subway": "홍대입구", "line": ["2호선", "경의선", "공항철도"]},
    "종로3가역": {"dong": "종로1", "subway": "종로3가", "line": ["1호선", "3호선", "5호선"]},
    "을지로3가역": {"dong": "을지로", "subway": "을지로3가", "line": ["2호선", "3호선"]},
    "신촌역": {"dong": "신촌", "subway": "신촌", "line": ["2호선"]},
    "합정역": {"dong": "서교", "subway": "합정", "line": ["2호선", "6호선"]},
    "신림역": {"dong": "신림", "subway": "신림", "line": ["2호선", "신림선"]},
    "서울대입구역": {"dong": "청룡", "subway": "서울대입구", "line": ["2호선"]},
    "건대입구역": {"dong": "화양", "subway": "건대입구", "line": ["2호선", "7호선"]},
    "잠실역": {"dong": "잠실6", "subway": "잠실", "line": ["2호선", "8호선"]} # 잠실나루 등 제외
}

selected_label = st.sidebar.selectbox("📍 분석 지역 선택", list(STATION_MAP.keys()))
target_dong = STATION_MAP[selected_label]["dong"]
target_subway = STATION_MAP[selected_label]["subway"]
target_lines = STATION_MAP[selected_label]["line"]

tab1, tab2 = st.tabs(["🏬 업종별 개폐업 현황", "🚉 역별 유동인구 추이"])

# --- TAB 1: 상권 개폐업 현황 (기존 동일) ---
with tab1:
    if not df_biz_raw.empty:
        df_biz_raw['행정동_코드_명'] = df_biz_raw['행정동_코드_명'].astype(str).str.replace(" ", "")
        filtered_biz = df_biz_raw[df_biz_raw['행정동_코드_명'].str.contains(target_dong, na=False)].copy()
        if not filtered_biz.empty:
            cols = ['개업_점포_수', '폐업_점포_수', '개업_율', '폐업_률', '점포_수']
            for col in cols: filtered_biz[col] = pd.to_numeric(filtered_biz[col], errors='coerce').fillna(0)
            
            FOOD_SERVICES = ["한식음식점", "중식음식점", "일식음식점", "양식음식점", "제과점", "패스트푸드점", "치킨전문점", "분식전문점", "호프-간이주점", "커피-음료"]
            summary_grouped = filtered_biz[filtered_biz['서비스_업종_코드_명'].isin(FOOD_SERVICES)].groupby(['기준_년분기_코드', '서비스_업종_코드_명']).agg({
                '점포_수': 'sum', '개업_점포_수': 'sum', '폐업_점포_수': 'sum', '개업_율': 'mean', '폐업_률': 'mean'
            }).reset_index()
            
            latest_q = summary_grouped['기준_년분기_코드'].max()
            st.subheader(f"📍 {selected_label} 상권 상세 ({latest_q} 기준)")
            latest_summary = summary_grouped[summary_grouped['기준_년분기_코드'] == latest_q]
            
            if not latest_summary.empty:
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
                            df_disp = service_df[['기준_년분기_코드', '점포_수', '개업_점포_수', '폐업_점포_수', '개업_율', '폐업_률']].copy()
                            df_disp.columns = ['년분기', '총 점포', '개업수', '폐업수', '개업률(%)', '폐업률(%)']
                            for col in ['총 점포', '개업수', '폐업수']: 
                                df_disp[col] = pd.to_numeric(df_disp[col], errors='coerce').fillna(0).astype(int)
                            for col in ['개업률(%)', '폐업률(%)']: 
                                df_disp[col] = pd.to_numeric(df_disp[col], errors='coerce').fillna(0).map('{:.1f}'.format)
                            st.table(df_disp)

# --- TAB 2: 지하철 유동인구 (노선 필터링 강화) ---
with tab2:
    if not df_subway_raw.empty:
        # 역명 클리닝
        df_subway_raw['역명'] = df_subway_raw['역명'].astype(str).str.replace('"', '').str.strip()
        df_subway_raw['노선명'] = df_subway_raw['노선명'].astype(str).str.replace('"', '').str.strip()
        
        # [수정] 역명과 노선명을 동시에 체크 (예: 잠실역이면서 2호선 혹은 8호선인 데이터만)
        sub_df = df_subway_raw[
            (df_subway_raw['역명'].str.contains(target_subway, na=False)) & 
            (df_subway_raw['노선명'].isin(target_lines))
        ].copy()
        
        if not sub_df.empty:
            sub_df['사용일자'] = pd.to_datetime(sub_df['사용일자'], format='%Y%m%d', errors='coerce')
            sub_df = sub_df.dropna(subset=['사용일자'])
            
            for col in ['승차총승객수', '하차총승객수']:
                sub_df[col] = pd.to_numeric(sub_df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            
            # 같은 날짜에 여러 노선이 있으면 합산
            daily_total = sub_df.groupby('사용일자')[['승차총승객수', '하차총승객수']].sum().reset_index()
            daily_total['총승하차'] = daily_total['승차총승객수'] + daily_total['하차총승객수']
            daily_total['요일'] = daily_total['사용일자'].dt.weekday
            
            def get_monday_label(dt):
                monday = dt - timedelta(days=dt.weekday())
                return monday.strftime('%y년%m월%d일(주)')
            
            daily_total['기간(월요일기준)'] = daily_total['사용일자'].apply(get_monday_label)
            
            def cat_day(d):
                if d <= 3: return "월~목(평균)"
                elif d <= 5: return "금~토(평균)"
                else: return "일요일"
            daily_total['기간분류'] = daily_total['요일'].apply(cat_day)
            
            # 집계
            final = daily_total.groupby(['기간(월요일기준)', '기간분류'])['총승하차'].mean().round(0).unstack().fillna(0).astype(int)
            
            target_cols = [c for c in ["월~목(평균)", "금~토(평균)", "일요일"] if c in final
