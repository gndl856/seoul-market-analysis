import streamlit as st
import pandas as pd
import glob
from datetime import datetime, timedelta

st.set_page_config(page_title="서울 상권 및 유동인구 리포트", layout="wide")

st.title("📋 서울 상권 및 지하철 유동인구 리포트")

# 1. 데이터 로드 및 강제 클리닝 함수
@st.cache_data
def load_all_data():
    # --- 상권 데이터 로드 ---
    biz_files = glob.glob('data/서울시*.csv') + glob.glob('서울시*.csv')
    df_biz = pd.DataFrame()
    if biz_files:
        biz_list = []
        for f in biz_files:
            try: biz_list.append(pd.read_csv(f, encoding='cp949'))
            except: biz_list.append(pd.read_csv(f, encoding='utf-8-sig'))
        if biz_list: df_biz = pd.concat(biz_list, ignore_index=True)
    
    # --- 지하철 데이터 로드 ---
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

# --- TAB 1: 상권 개폐업 현황 ---
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
                            # 에러 방지를 위해 에러 처리 강화
                            for col in ['총 점포', '개업수', '폐업수']: 
                                df_disp[col] = pd.to_numeric(df_disp[col], errors='coerce').fillna(0).astype(int)
                            for col in ['개업률(%)', '폐업률(%)']: 
                                df_disp[col] = pd.to_numeric(df_disp[col], errors='coerce').fillna(0).map('{:.1f}'.format)
                            st.table(df_disp)

# --- TAB 2: 지하철 유동인구 추이 ---
with tab2:
    if not df_subway_raw.empty:
        if '역명' in df_subway_raw.columns:
            sub_df = df_subway_raw[df_subway_raw['역명'].str.contains(target_subway, na=False)].copy()
            if not sub_df.empty:
                sub_df['사용일자'] = pd.to_datetime(sub_df['사용일자'], format='%Y%m%d', errors='coerce')
                sub_df = sub_df.dropna(subset=['사용일자'])
                
                for col in ['승차총승객수', '하차총승객수']:
                    sub_df[col] = pd.to_numeric(sub_df[col].str.replace(',', ''), errors='coerce').fillna(0)
                
                sub_df['총승하차'] = sub_df['승차총승객수'] + sub_df['하차총승객수']
                sub_df['요일'] = sub_df['사용일자'].dt.weekday
                
                def get_monday_label(dt):
                    monday = dt - timedelta(days=dt.weekday())
                    return monday.strftime('%y년%m월%d일(주)')
                
                sub_df['기간(월요일기준)'] = sub_df['사용일자'].apply(get_monday_label)
                
                def cat_day(d):
                    if d <= 3: return "월~목(평균)"
                    elif d <= 5: return "금~토(평균)"
                    else: return "일요일"
                sub_df['기간분류'] = sub_df['요일'].apply(cat_day)
                
                final = sub_df.groupby(['기간(월요일기준)', '사용일자', '기간분류'])['총승하차'].sum().reset_index()
                # 데이터가 없는 셀은 0으로 채우고 정수 변환
                final = final.groupby(['기간(월요일기준)', '기간분류'])['총승하차'].mean().round(0).unstack().fillna(0).astype(int)
                
                target_cols = [c for c in ["월~목(평균)", "금~토(평균)", "일요일"] if c in final.columns]
                final = final[target_cols]
                final = final.sort_index()
                
                st.subheader(f"🚉 {target_subway}역 주차별 유동인구 (1일 평균 승하차)")
                # 데이터가 None일 경우를 대비해 안전하게 포맷팅
                st.table(final.map(lambda x: "{:,}".format(int(x)) if pd.notnull(x) else "0"))
                st.caption("※ 기간은 해당 주차의 시작일(월요일) 기준입니다.")
        else: st.error("지하철 데이터 컬럼 인식 실패")
    else: st.error("지하철 데이터 로드 실패")
