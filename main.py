import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import unicodedata
import io

# ===============================
# 기본 설정
# ===============================
st.set_page_config(
    page_title="극지식물 최적 EC 농도 연구",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

DATA_DIR = Path("data")

SCHOOL_EC = {
    "송도고": 1.0,
    "하늘고": 2.0,
    "아라고": 4.0,
    "동산고": 8.0
}

SCHOOL_COLOR = {
    "송도고": "#4C72B0",
    "하늘고": "#55A868",
    "아라고": "#C44E52",
    "동산고": "#8172B2"
}

# ===============================
# 파일 탐색 (NFC/NFD 안전)
# ===============================
def find_file_by_name(directory: Path, target_name: str):
    target_nfc = unicodedata.normalize("NFC", target_name)
    target_nfd = unicodedata.normalize("NFD", target_name)

    for file in directory.iterdir():
        fname_nfc = unicodedata.normalize("NFC", file.name)
        fname_nfd = unicodedata.normalize("NFD", file.name)

        if fname_nfc == target_nfc or fname_nfd == target_nfd:
            return file
    return None


# ===============================
# 데이터 로딩
# ===============================
@st.cache_data
def load_environment_data():
    env_data = {}
    for school in SCHOOL_EC.keys():
        file = find_file_by_name(DATA_DIR, f"{school}_환경데이터.csv")
        if file is None:
            st.error(f"{school} 환경 데이터 파일을 찾을 수 없습니다.")
            return None
        df = pd.read_csv(file)
        env_data[school] = df
    return env_data


@st.cache_data
def load_growth_data():
    xlsx_file = None
    for file in DATA_DIR.iterdir():
        if file.suffix == ".xlsx":
            xlsx_file = file
            break

    if xlsx_file is None:
        st.error("생육 결과 XLSX 파일을 찾을 수 없습니다.")
        return None

    sheets = pd.read_excel(xlsx_file, sheet_name=None)
    return sheets


with st.spinner("데이터 로딩 중..."):
    env_data = load_environment_data()
    growth_data = load_growth_data()

if env_data is None or growth_data is None:
    st.stop()

# ===============================
# 사이드바
# ===============================
st.sidebar.title("학교 선택")
selected_school = st.sidebar.selectbox(
    "학교",
    ["전체"] + list(SCHOOL_EC.keys())
)

# ===============================
# 제목
# ===============================
st.title("🌱 극지식물 최적 EC 농도 연구")

tab1, tab2, tab3 = st.tabs(["📖 실험 개요", "🌡️ 환경 데이터", "📊 생육 결과"])

# ===============================
# Tab 1: 실험 개요
# ===============================
with tab1:
    st.subheader("연구 배경 및 목적")
    st.markdown(
        "극지식물의 생육에 영향을 미치는 핵심 환경 요인 중 **EC(전기전도도)** 농도의 차이가 "

