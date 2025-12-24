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
    page_title="극지 식물의 온도별 성장률",
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
    "동산고": 1.0
}

# ===============================
# 파일 탐색 (NFC/NFD 안전)
# ===============================
def find_file(directory: Path, target_name: str):
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
def load_env_data():
    data = {}
    for school in SCHOOL_EC.keys():
        file = find_file(DATA_DIR, f"{school}_환경데이터.csv")
        if file is None:
            st.error(f"{school} 환경 데이터 파일을 찾을 수 없습니다.")
