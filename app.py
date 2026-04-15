import streamlit as st
import pandas as pd
import glob
from datetime import datetime, timedelta

st.set_page_config(page_title="서울 상권 및 유동인구 리포트", layout="wide")

st.title("📋 서울 상권 및 지하철 유동인구 리포트")

# 1. 데이터 로드 및 전처리
@st.cache_data
def load_all_data():
    # 상권 데이터
    biz_files = glob.glob('data/서울시*.csv') + glob.glob('서울시*.csv')
    df_biz = pd.DataFrame()
    if biz_files:
        biz_list = []
        for f in biz_files:
            try: biz_list.append(pd.read_csv(f, encoding='cp949'))
            except: biz_list.append(pd.read_csv(f, encoding='utf-8-sig'))
        if biz_list: df_biz = pd.concat(biz_list, ignore_index=True)
    
    # 지하철 데이터
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

# 2. 분석 지역 설정 (잠실, 서울대입구 등 명칭 보정 완료)
STATION_MAP = {
    "강남역": {"dong": "역삼1", "subway_names": ["강남"]},
    "홍대입구역": {"dong": "서교", "subway_names": ["홍대입구"]},
    "종로3가역": {"dong": "종로1", "subway_names": ["종로3가"]},
    "을지로3가역": {"dong": "을지로", "subway_names": ["을지로3가"]},
    "신촌역": {"dong": "신촌", "subway_names": ["신촌"]},
    "합정역": {"dong": "서교", "subway_names": ["합정"]},
    "신림역": {"dong": "신림", "subway_names": ["신림"]},
    "서울대입구역": {"dong": "청룡", "subway_names": ["서울대입구(관악구청)", "서울대입구"]},
    "건대입구역": {"dong": "화양", "subway_names": ["건대입구"]},
    "잠실역": {"dong": "잠실6", "subway_names": ["잠실", "잠실(송파구청)"]}
}

selected_label = st.sidebar.selectbox("📍 분석 지역 선택", list(STATION_MAP.keys()))
target_info = STATION_MAP[selected_label]
target_dong = target_info["dong"]
target_subways = target_info["subway_names"]

tab1, tab2 = st.tabs(["🏬 업종별 개폐업 현황", "🚉 역별 유동인구 추이"])

# --- TAB 1: 상권 개폐업 현황 (전체 합계 탭 추가) ---
with tab1:
    if not df_biz_raw.empty:
        df_biz_raw['행정동_코드_명'] = df_biz_raw['행정동_코드_명'].astype(str).str.replace(" ", "")
        filtered_biz = df_biz_raw[df_biz_raw['행정동_코드_명'].str.contains(target_dong, na=False)].copy()
        
        if not filtered_biz.empty:
            cols = ['개업_점포_수', '폐업_점포_수', '개업_율', '폐업_률', '점포_수']
            for col in cols: filtered_biz[col] = pd.to_numeric(filtered_biz[col], errors='coerce').fillna(0)
            
            FOOD_SERVICES = ["한식음식점", "중식음식점", "일식음식점", "양식음식점", "제과점", "패스트푸드점", "치킨전문점", "분식전문점", "호프-간이주점", "커피-음료"]
            
            # 개별 업종 데이터
            summary_grouped = filtered_biz[filtered_biz['서비스_업종_코드_명'].isin(FOOD_SERVICES)].groupby(['기준_년분기_코드', '서비스_업종_코드_명']).agg({
                '점포_수': 'sum', '개업_점포_수': 'sum', '폐업_점포_수': 'sum', '개업_율': 'mean', '폐업_률': 'mean'
            }).reset_index()
            
            # 전체 합계 데이터
            total_summary = summary_grouped.groupby('기준_년분기_코드').agg({
                '점포_수': 'sum', '개업_점포_수': 'sum', '폐업_점포_수': 'sum', '개업_율': 'mean', '폐업_률': 'mean'
            }).reset_index()
            
            latest_q = summary_grouped['기준_년분기_코드'].max()
            st.subheader(f"📍 {selected_label} 상권 상세 ({latest_q} 기준)")
            
            latest_total = total_summary[total_summary['기준_년분기_코드'] == latest_q]
            if not latest_total.empty:
                m1, m2, m3 = st.columns(3)
                m1.metric("요식업 전체 점포", f"{int(latest_total['점포_수'].sum()):,}개")
                m2.metric("전체 평균 개업률", f"{latest_total['개업_율'].mean():.1f}%")
                m3.metric("전체 평균 폐업률", f"{latest_total['폐업_률'].mean():.1f}%")
            
            st.divider()

            # 하위 탭 구성 (전체 합계 + 10개 업종)
            tab_list = ["전체 합계"] + FOOD_SERVICES
            sub_tabs = st.tabs(tab_list)
            
            for i, name in enumerate(tab_list):
                with sub_tabs[i]:
                    if name == "전체 합계":
                        display_df = total_summary.sort_values('기준_년분기_코드', ascending=False).copy()
                    else:
                        display_df = summary_grouped[summary_grouped['서비스_업종_코드_명'] == name].sort_values('기준_년분기_코드', ascending=False).copy()
                    
                    if not display_df.empty:
                        df_disp = display_df[['기준_년분기_코드', '점포_수', '개업_점포_수', '폐업_점포_수', '개업_율', '폐업_률']].copy()
                        df_disp.columns = ['년분기', '총 점포', '개업수', '폐업수', '개업률(%)', '폐업률(%)']
                        
                        # 숫자 포맷팅 (콤마 추가 및 소수점 정렬)
                        df_disp['총 점포'] = df_disp['총 점포'].astype(int).apply(lambda x: f"{x:,}")
                        df_disp['개업수'] = df_disp['개업수'].astype(int).apply(lambda x: f"{x:,}")
                        df_disp['폐업수'] = df_disp['폐업수'].astype(int).apply(lambda x: f"{x:,}")
                        df_disp['개업률(%)'] = df_disp['개업률(%)'].apply(lambda x: f"{x:.1f}")
                        df_disp['폐업률(%)'] = df_disp['폐업률(%)'].apply(lambda x: f"{x:.1f}")
                        
                        # 깔끔한 정렬을 위해 st.dataframe 사용 (인덱스 숨김)
                        st.dataframe(df_disp, use_container_width=True, hide_index=True)
        else: st.warning("상권 데이터가 없습니다.")
    else: st.error("상권 데이터 로드 실패")

# --- TAB 2: 지하철 유동인구 추이 ---
with tab2:
    if not df_subway_raw.empty:
        df_subway_raw['역명'] = df_subway_raw['역명'].astype(str).str.replace('"', '').str.strip()
        sub_df = df_subway_raw[df_subway_raw['역명'].isin(target_subways)].copy()
        
        if not sub_df.empty:
            sub_df['사용일자'] = pd.to_datetime(sub_df['사용일자'], format='%Y%m%d', errors='coerce')
            sub_df = sub_df.dropna(subset=['사용일자'])
            for col in ['승차총승객수', '하차총승객수']:
                sub_df[col] = pd.to_numeric(sub_df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            
            daily = sub_df.groupby('사용일자')[['승차총승객수', '하차총승객수']].sum().reset_index()
            daily['총승하차'] = daily['승차총승객수'] + daily['하차총승객수']
            daily['요일'] = daily['사용일자'].dt.weekday
            
            def get_monday_label(dt):
                monday = dt - timedelta(days=dt.weekday())
                return monday.strftime('%y년%m월%d일(주)')
            daily['기간(월요일기준)'] = daily['사용일자'].apply(get_monday_label)
            
            def cat_day(d):
                if d <= 3: return "월~목(평균)"
                elif d <= 5: return "금~토(평균)"
                else: return "일요일"
            daily['기간분류'] = daily['요일'].apply(cat_day)
            
            final = daily.groupby(['기간(월요일기준)', '기간분류'])['총승하차'].mean().round(0).unstack().fillna(0).astype(int)
            target_cols = [c for c in ["월~목(평균)", "금~토(평균)", "일요일"] if c in final.columns]
            final = final[target_cols].sort_index(ascending=False)
            
            st.subheader(f"🚉 {selected_label} 유동인구 ({', '.join(target_subways)} 합산)")
            
            # 가독성을 위해 천단위 콤마 추가
            formatted_final = final.map(lambda x: "{:,}".format(int(x)))
            # 인덱스(날짜) 포함하여 출력
            st.dataframe(formatted_final, use_container_width=True)
            
            st.caption(f"※ {', '.join(target_subways)} 명칭의 데이터를 합산하여 집계했습니다.")
        else: st.warning(f"'{selected_label}'의 지하철 데이터를 찾을 수 없습니다.")
    else: st.error("지하철 데이터 로드 실패")
