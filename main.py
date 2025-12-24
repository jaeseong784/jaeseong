# ===============================
# 0. 기본 설정 및 필수 import
# ===============================
import streamlit as st
import pandas as pd
from pathlib import Path
import unicodedata
import io

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ===============================
# 1. Streamlit 기본 설정
# ===============================
st.set_page_config(
    page_title="극지식물 최적 EC 농도 연구",
    layout="wide"
)

# 한글 폰트 (UI + Plotly)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)


# ===============================
# 2. 파일명 정규화 함수 (NFC/NFD 완벽 대응)
# ===============================
def normalize_name(name: str) -> str:
    return unicodedata.normalize("NFC", name)


# ===============================
# 3. 데이터 로딩 함수
# ===============================
@st.cache_data
def load_environment_data(data_dir: Path):
    env_data = {}

    with st.spinner("환경 데이터 로딩 중..."):
        for file in data_dir.iterdir():
            if file.suffix.lower() == ".csv":
                fname = normalize_name(file.name)
                school = fname.replace("_환경데이터.csv", "")

                try:
                    df = pd.read_csv(file)
                    env_data[school] = df
                except Exception as e:
                    st.error(f"{file.name} 로딩 실패: {e}")

    if not env_data:
        st.error("환경 데이터 CSV 파일을 찾을 수 없습니다.")

    return env_data


@st.cache_data
def load_growth_data(data_dir: Path):
    with st.spinner("생육 결과 데이터 로딩 중..."):
        for file in data_dir.iterdir():
            if file.suffix.lower() == ".xlsx":
                try:
                    xls = pd.ExcelFile(file, engine="openpyxl")
                    growth_data = {
                        sheet: xls.parse(sheet)
                        for sheet in xls.sheet_names
                    }
                    return growth_data
                except Exception as e:
                    st.error(f"엑셀 파일 로딩 실패: {e}")

    st.error("생육 결과 XLSX 파일을 찾을 수 없습니다.")
    return {}


# ===============================
# 4. 데이터 로딩 실행
# ===============================
DATA_DIR = Path("data")

env_data = load_environment_data(DATA_DIR)
growth_data = load_growth_data(DATA_DIR)

if not env_data or not growth_data:
    st.stop()


# ===============================
# 5. 메타 정보
# ===============================
EC_TARGET = {
    "송도고": 1.0,
    "하늘고": 2.0,  # 최적
    "아라고": 4.0,
    "동산고": 8.0
}

SCHOOLS = ["전체"] + list(EC_TARGET.keys())


# ===============================
# 6. 제목 & 사이드바
# ===============================
st.title("🌱 극지식물 최적 EC 농도 연구")

selected_school = st.sidebar.selectbox(
    "학교 선택",
    SCHOOLS
)


# ===============================
# 7. TAB 구성
# ===============================
tab1, tab2, tab3 = st.tabs([
    "📖 실험 개요",
    "🌡️ 환경 데이터",
    "📊 생육 결과"
])


# ======================================================
# TAB 1 : 실험 개요
# ======================================================
with tab1:
    st.subheader("연구 배경 및 목적")
    st.markdown("""
    극지식물은 저온 환경에 적응한 식물이지만,  
    본 연구에서는 **상온 환경에서의 EC 농도 차이**가  
    생육에 미치는 영향을 비교 분석하였다.
    """)

    # 학교별 EC 조건 표
    overview_df = pd.DataFrame({
        "학교": EC_TARGET.keys(),
        "목표 EC": EC_TARGET.values(),
        "개체 수": [len(growth_data[k]) for k in EC_TARGET.keys()]
    })

    st.dataframe(overview_df, use_container_width=True)

    # 주요 지표 카드
    col1, col2, col3, col4 = st.columns(4)

    total_plants = sum(len(df) for df in growth_data.values())
    avg_temp = pd.concat(env_data.values())["temperature"].mean()
    avg_hum = pd.concat(env_data.values())["humidity"].mean()

    col1.metric("총 개체 수", f"{total_plants} 개")
    col2.metric("평균 온도", f"{avg_temp:.1f} ℃")
    col3.metric("평균 습도", f"{avg_hum:.1f} %")
    col4.metric("최적 EC", "2.0 (하늘고)")


# ======================================================
# TAB 2 : 환경 데이터
# ======================================================
with tab2:
    st.subheader("학교별 환경 평균 비교")

    summary_rows = []

    for school, df in env_data.items():
        summary_rows.append({
            "학교": school,
            "온도": df["temperature"].mean(),
            "습도": df["humidity"].mean(),
            "pH": df["ph"].mean(),
            "EC": df["ec"].mean(),
            "목표 EC": EC_TARGET.get(school, None)
        })

    summary_df = pd.DataFrame(summary_rows)

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=["평균 온도", "평균 습도", "평균 pH", "목표 EC vs 실측 EC"]
    )

    fig.add_trace(go.Bar(x=summary_df["학교"], y=summary_df["온도"]), row=1, col=1)
    fig.add_trace(go.Bar(x=summary_df["학교"], y=summary_df["습도"]), row=1, col=2)
    fig.add_trace(go.Bar(x=summary_df["학교"], y=summary_df["pH"]), row=2, col=1)

    fig.add_trace(
        go.Bar(x=summary_df["학교"], y=summary_df["EC"], name="실측 EC"),
        row=2, col=2
    )
    fig.add_trace(
        go.Bar(x=summary_df["학교"], y=summary_df["목표 EC"], name="목표 EC"),
        row=2, col=2
    )

    fig.update_layout(
        height=700,
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )

    st.plotly_chart(fig, use_container_width=True)

    # 시계열
    if selected_school != "전체":
        st.subheader(f"{selected_school} 환경 시계열")
        df = env_data[selected_school]

        fig_ts = px.line(
            df,
            x="time",
            y=["temperature", "humidity", "ec"],
            labels={"value": "측정값", "time": "시간"}
        )
        fig_ts.add_hline(
            y=EC_TARGET[selected_school],
            line_dash="dash",
            annotation_text="목표 EC"
        )
        st.plotly_chart(fig_ts, use_container_width=True)

    with st.expander("환경 데이터 원본"):
        st.dataframe(summary_df)

        buffer = io.BytesIO()
        summary_df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)

        st.download_button(
            "환경 데이터 다운로드",
            data=buffer,
            file_name="환경_요약.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


# ======================================================
# TAB 3 : 생육 결과
# ======================================================
with tab3:
    st.subheader("EC별 생육 결과 비교")

    growth_summary = []

    for school, df in growth_data.items():
        growth_summary.append({
            "학교": school,
            "EC": EC_TARGET[school],
            "평균 생중량": df["생중량(g)"].mean(),
            "평균 잎 수": df["잎 수(장)"].mean(),
            "평균 지상부 길이": df["지상부 길이(mm)"].mean(),
            "개체수": len(df)
        })

    gdf = pd.DataFrame(growth_summary)

    best_idx = gdf["평균 생중량"].idxmax()
    best_ec = gdf.loc[best_idx, "EC"]

    st.metric("🥇 최적 EC (평균 생중량 기준)", f"{best_ec}")

    fig2 = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            "평균 생중량",
            "평균 잎 수",
            "평균 지상부 길이",
            "개체 수"
        ]
    )

    fig2.add_trace(go.Bar(x=gdf["EC"], y=gdf["평균 생중량"]), row=1, col=1)
    fig2.add_trace(go.Bar(x=gdf["EC"], y=gdf["평균 잎 수"]), row=1, col=2)
    fig2.add_trace(go.Bar(x=gdf["EC"], y=gdf["평균 지상부 길이"]), row=2, col=1)
    fig2.add_trace(go.Bar(x=gdf["EC"], y=gdf["개체수"]), row=2, col=2)

    fig2.update_layout(
        height=700,
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )

    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("생육 데이터 원본"):
        full_growth = pd.concat(
            [df.assign(학교=school) for school, df in growth_data.items()]
        )

        st.dataframe(full_growth)

        buffer = io.BytesIO()
        full_growth.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)

        st.download_button(
            "생육 데이터 다운로드",
            data=buffer,
            file_name="생육_전체.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
