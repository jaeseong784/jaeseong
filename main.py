import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path
import unicodedata
import io

# ===============================
# Streamlit 기본 설정
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

st.title("🌱 극지 식물의 온도별 성장률 대시보드")

# ===============================
# 경로 설정
# ===============================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

st.write("📁 data 폴더 경로:", DATA_DIR)

if not DATA_DIR.exists():
    st.error("❌ data 폴더가 존재하지 않습니다.")
    st.stop()

# ===============================
# 학교별 EC 조건
# ===============================
SCHOOL_EC = {
    "송도고": 1.0,
    "하늘고": 2.0,
    "아라고": 4.0,
    "동산고": 1.0
}

# ===============================
# NFC / NFD 안전 파일 찾기
# ===============================
def find_file(directory: Path, target_name: str):
    target_nfc = unicodedata.normalize("NFC", target_name)
    target_nfd = unicodedata.normalize("NFD", target_name)

    for file in directory.iterdir():
        name_nfc = unicodedata.normalize("NFC", file.name)
        name_nfd = unicodedata.normalize("NFD", file.name)

        if name_nfc == target_nfc or name_nfd == target_nfd:
            return file

    return None

# ===============================
# 환경 데이터 로딩
# ===============================
@st.cache_data
def load_environment_data():
    env_data = {}

    for school in SCHOOL_EC:
        filename = f"{school}_환경데이터.csv"
        file = find_file(DATA_DIR, filename)

        if file is None:
            st.error(f"❌ 환경 데이터 파일 없음: {filename}")
            return None

        df = pd.read_csv(file)
        env_data[school] = df

    return env_data

# ===============
