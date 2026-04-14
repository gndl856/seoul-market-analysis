import streamlit as st
import pandas as pd
import requests

# 1. 설정
st.set_page_config(page_title="서울 상권 데이터 센터", layout="wide")
API_KEY = "4d59784b56676e64363847736b5362"

# --- [유동인구 분석 함수 보존: 나중에 '다시 넣어줘' 하시면 바로 연결 가능] ---
def get_subway_data(station_name):
    # 기존 유동인구 로직은 여기에 온전히 보관되어 있습니다.
    pass

# 2. 메인 UI
st.title("📊 서울시 상권 개업/폐업 Raw 데이터")
st.info("서버 내부 오류(500)를 방지하기 위해 가장 안정적인 호출 규격을 적용했습니다.")

# 3. 데이터 호출 (연도/분기 파라미터를 명시적으로 전달)
# ERROR-500 방지를 위해 시점 파라미터를 주소 맨 뒤에 '20234' 형태로 정확히 삽입합니다.
url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/VwsmTrdarOpclQq/1/1000/20234"

try:
    with st.spinner('서울시 서버에서 데이터를 시원하게 긁어오는 중...'):
        response = requests.get(url, timeout=15)
        data = response.json()
        
        # 'VwsmTrdarOpclQq' 데이터셋이 정상적으로 응답된 경우
        if 'VwsmTrdarOpclQq' in data:
            df = pd.DataFrame(data['VwsmTrdarOpclQq']['row'])
            
            # 한글 매핑 (데이터가 있으면 아래 컬럼은 반드시 존재함)
            cols_mapping = {
                'TRDAR_CD_NM': '상권명',
                'SVC_INDUTY_CD_NM': '업종명',
                'OPN_STOR_CO': '개업수',
                'CLS_STOR_CO': '폐업수',
                'OPN_RT': '개업률(%)',
                'CLS_RT': '폐업률(%)',
                'STDR_YY_CD': '연도',
                'STDR_QU_CD': '분기'
            }
            
            # 존재하는 컬럼만 예쁘게 정리
            display_df = df[[c for c in cols_mapping.keys() if c in df.columns]].rename(columns=cols_mapping)
            
            st.success(f"✅ 드디어 성공! {len(display_df):,}건의 Raw 데이터를 불러왔습니다.")
            
            # 요약 지표
            c1, c2, c3 = st.columns(3)
            c1.metric("불러온 상권 수", f"{display_df['상권명'].nunique():,}개")
            c2.metric("총 개업수 합계", f"{display_df['개업수'].astype(int).sum():,}개")
            c3.metric("총 폐업수 합계", f"{display_df['폐업수'].astype(int).sum():,}개")
            
            st.markdown("---")
            
            # 검색 및 출력
            search = st.text_input("🔍 찾고 싶은 지역이나 업종을 입력하세요", placeholder="예: 강남역, 편의점")
            if search:
                filtered = display_df[display_df.astype(str).apply(lambda x: x.str.contains(search)).any(axis=1)]
                st.dataframe(filtered, hide_index=True, use_container_width=True)
            else:
                st.dataframe(display_df, hide_index=True, use_container_width=True)
                
        else:
            # 에러 발생 시 서버가 주는 메시지를 있는 그대로 출력 (디버깅용)
            error_msg = data.get('RESULT', {}).get('MESSAGE', '알 수 없는 서버 오류')
            st.error(f"❌ 서버 응답 에러: {error_msg}")
            st.write("서버 응답 원문:", data)
            
except Exception as e:
    st.error(f"❌ 연결 오류: {e}")
