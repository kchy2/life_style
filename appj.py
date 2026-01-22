import streamlit as st
import json
import os
from datetime import datetime, timedelta
import sys
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Backend 모듈 import 경로 설정
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Backend 모듈 import (linter 경고 무시)
import importlib.util

# open.py 모듈 동적 로드
open_spec = importlib.util.spec_from_file_location("open_module", os.path.join(backend_path, "open.py"))
if open_spec and open_spec.loader:
    open_module = importlib.util.module_from_spec(open_spec)
    open_spec.loader.exec_module(open_module)
    get_routine_category_suggestion = open_module.get_routine_category_suggestion
    get_ai_advice = open_module.get_ai_advice
    get_realtime_feedback = open_module.get_realtime_feedback
else:
    raise ImportError("Cannot load backend/open.py module")

# database.py 모듈 동적 로드
database_spec = importlib.util.spec_from_file_location("database_module", os.path.join(backend_path, "database.py"))
if database_spec and database_spec.loader:
    database_module = importlib.util.module_from_spec(database_spec)
    database_spec.loader.exec_module(database_module)
    db_add_record = database_module.add_record
    get_all_records = database_module.get_all_records
    get_records_by_date = database_module.get_records_by_date
    get_records_by_date_range = database_module.get_records_by_date_range
    delete_record = database_module.delete_record
    update_record = database_module.update_record
    get_statistics = database_module.get_statistics
    migrate_from_json = database_module.migrate_from_json
    init_database = database_module.init_database
else:
    raise ImportError("Cannot load backend/database.py module")

# 페이지 설정
st.set_page_config(
    page_title="라이프챙김 - AI 루틴 비서",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 몽글몽글한 폰트와 디자인 스타일
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
    /* 전체 폰트 적용 - 몽글몽글한 느낌 */
    * {
        font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        letter-spacing: -0.02em;
    }
    
    /* 전체 배경색 - 디자인에 맞춤 */
    .stApp {
        background: #F7F9FA !important;
    }
    
    /* 메인 컨테이너 - 중앙 정렬 */
    .main .block-container {
        padding: 0 !important;
        max-width: 100% !important;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
    }
    
    /* 헤더 숨기기 */
    header {
        display: none !important;
    }
    
    /* 푸터 숨기기 */
    footer {
        display: none !important;
    }
    
    /* 메인 타이틀 스타일 - 디자인에 맞춤 */
    .main-title {
        font-size: 3.5rem;
        font-weight: 700;
        color: #2C3E50;
        text-align: center;
        margin: 0 0 0.3rem 0;
        padding: 0;
        line-height: 1.2;
        letter-spacing: -0.03em;
    }
    
    /* 부제목 스타일 */
    .subtitle {
        font-size: 1.1rem;
        color: #6C7A89;
        text-align: center;
        margin: 0.5rem 0 2rem 0;
        font-weight: 400;
        line-height: 1.5;
        letter-spacing: -0.01em;
    }
    
    /* 메인 버튼 컨테이너 */
    .main-button-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 2rem 0;
    }
    
    /* 메인 버튼 스타일 - Streamlit 버튼 커스터마이징 */
    .main-button-wrapper {
        position: relative;
        display: inline-block;
        width: 100%;
        max-width: 300px;
        margin: 0 auto;
    }
    
    /* 메인 화면 버튼 컨테이너 */
    .center-content .main-button-wrapper {
        margin: 0 auto;
    }
    
    .main-button-wrapper .stButton > button {
        background: #B8F2A3 !important;
        color: #2D8F0B !important;
        border: none !important;
        border-radius: 16px !important;
        padding: 1.2rem 2.5rem 1.2rem 3.5rem !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(184, 242, 163, 0.3) !important;
        transition: all 0.3s ease !important;
        font-family: 'Noto Sans KR', sans-serif !important;
        letter-spacing: -0.01em !important;
        position: relative !important;
        width: 100% !important;
    }

    .calendar-day-wrapper .stButton > button {
        background: white !important;
        color: #2C3E50 !important;
        border: 2px solid #E2E8F0 !important;
    }

    /* ★ 오늘 날짜만 초록색으로 강조 (우선순위 최상위) */
    .calendar-day-wrapper .stButton > button[data-testid*="baseButton-primary"] {
        background-color: #B8F2A3 !important;
        background: #B8F2A3 !important;
        color: #2D8F0B !important;
        border: 2px solid #2D8F0B !important;
    }

    .main-button-wrapper .stButton > button:hover {
        background: #A8E893 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(184, 242, 163, 0.4) !important;
    }
    
    /* + 아이콘을 버튼 앞에 배치 */
    .main-button-wrapper::before {
        content: '+';
        position: absolute;
        left: 1.5rem;
        top: 50%;
        transform: translateY(-50%);
        width: 24px;
        height: 24px;
        background: #2D8F0B;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 18px;
        font-weight: 600;
        z-index: 10;
        pointer-events: none;
    }
    
    /* 페이지네이션 점들 */
    .pagination-dots {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 0.5rem;
        margin: 2rem 0 0 0;
    }
    
    .pagination-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #B8F2A3;
        transition: all 0.3s ease;
    }
    
    .pagination-dot.active {
        background: #2D8F0B;
        width: 10px;
        height: 10px;
    }
    
    /* 도움말 아이콘 */
    .help-icon {
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        width: 48px;
        height: 48px;
        background: #2C3E50;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 24px;
        font-weight: 600;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(44, 62, 80, 0.3);
        transition: all 0.3s ease;
        z-index: 1000;
        user-select: none;
    }
    
    .help-icon:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 20px rgba(44, 62, 80, 0.4);
        background: #34495E;
    }
    
    /* 중앙 컨텐츠 컨테이너 */
    .center-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        width: 100%;
        padding: 2rem;
    }
    
    /* 기록 폼 스타일 */
    .record-form-container {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        margin: 2rem 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        max-width: 600px;
        width: 100%;
    }
    
    .record-form-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2C3E50;
        margin-bottom: 1.5rem;
    }
    
    /* 입력 필드 스타일 */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        border-radius: 12px;
        border: 2px solid #E2E8F0;
        padding: 0.8rem;
        font-size: 1rem;
        color: #2C3E50;
        font-family: 'Noto Sans KR', sans-serif;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #B8F2A3;
        box-shadow: 0 0 0 3px rgba(184, 242, 163, 0.1);
        outline: none;
    }
    
    .stTextInput label,
    .stTextArea label,
    .stSelectbox label {
        color: #2C3E50 !important;
        font-weight: 500;
        font-family: 'Noto Sans KR', sans-serif;
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        background: #B8F2A3 !important;
        color: #2D8F0B !important;
        border: none;
        border-radius: 12px;
        padding: 0.8rem 1.5rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(184, 242, 163, 0.3);
        font-family: 'Noto Sans KR', sans-serif;
    }
    
    .stButton > button:hover {
        background: #A8E893 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(184, 242, 163, 0.4);
    }
    
    /* 오늘 날짜 버튼 연두색 스타일 */
    .calendar-container .stButton > button[data-testid*="baseButton-primary"] {
        background: #B8F2A3 !important;
        color: #2D8F0B !important;
        border-color: #B8F2A3 !important;
    }
    
    .calendar-container .stButton > button[data-testid*="baseButton-primary"]:hover {
        background: #A8E893 !important;
        border-color: #A8E893 !important;
    }
    
    /* 기록 카드 스타일 */
    .record-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
        border-left: 4px solid #B8F2A3;
        width: 100%;
    }
    
    /* 수정/삭제 버튼 스타일 */
    button[key^="edit_"], button[key^="delete_"] {
        background: transparent !important;
        border: 1px solid #E2E8F0 !important;
        color: #6C7A89 !important;
        border-radius: 8px !important;
        padding: 0.4rem 0.6rem !important;
        font-size: 1.2rem !important;
        min-width: auto !important;
        width: 100% !important;
    }
    
    button[key^="edit_"]:hover {
        background: #B8F2A3 !important;
        border-color: #B8F2A3 !important;
        color: #2D8F0B !important;
    }
    
    button[key^="delete_"]:hover {
        background: #f56565 !important;
        border-color: #f56565 !important;
        color: white !important;
    }
    
    .record-card-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #2C3E50;
        margin: 0 0 0.5rem 0;
    }
    
    .record-card-meta {
        font-size: 0.9rem;
        color: #6C7A89;
        margin: 0.5rem 0;
    }
    
    /* 빈 상태 메시지 */
    .empty-state {
        text-align: center;
        padding: 3rem 2rem;
        color: #6C7A89;
    }
    
    /* 스크롤바 숨기기 */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #F7F9FA;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #B8F2A3;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #A8E893;
    }
    
    /* 모달 오버레이 */
    .modal-overlay {
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        z-index: 2000;
        justify-content: center;
        align-items: center;
    }
    
    .modal-overlay.show {
        display: flex;
    }
    
    /* 모달 창 */
    .modal-content {
        background: white;
        border-radius: 24px;
        padding: 2.5rem;
        max-width: 600px;
        width: 90%;
        max-height: 90vh;
        overflow-y: auto;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
        position: relative;
        animation: modalSlideIn 0.3s ease;
    }
    
    @keyframes modalSlideIn {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
    }
    
    .modal-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #2C3E50;
        margin: 0;
    }
    
    .modal-close {
        background: #F7F9FA;
        border: none;
        border-radius: 50%;
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-size: 20px;
        color: #6C7A89;
        transition: all 0.3s ease;
    }
    
    .modal-close:hover {
        background: #E2E8F0;
        color: #2C3E50;
    }
    
    /* AI 제안 카드 */
    .ai-suggestion-card {
        background: linear-gradient(135deg, rgba(184, 242, 163, 0.1) 0%, rgba(184, 242, 163, 0.05) 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #B8F2A3;
    }
    
    .ai-suggestion-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2C3E50;
        margin-bottom: 0.5rem;
    }
    
    .category-badge {
        display: inline-block;
        background: #B8F2A3;
        color: #2D8F0B;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        margin: 0.5rem 0.5rem 0.5rem 0;
    }
    
    .routine-suggestion {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid #E2E8F0;
    }
    
    .routine-suggestion-name {
        font-weight: 600;
        color: #2C3E50;
        margin-bottom: 0.3rem;
    }
    
    .routine-suggestion-desc {
        font-size: 0.9rem;
        color: #6C7A89;
        margin-bottom: 0.3rem;
    }
    
    .routine-suggestion-time {
        font-size: 0.85rem;
        color: #A0AEC0;
    }
    
    /* AI 조언 카드 스타일 */
    .ai-advice-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
    }
    
    .ai-advice-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #2C3E50;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .ai-advice-summary {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        font-size: 1rem;
        color: #2C3E50;
        font-weight: 500;
    }
    
    .ai-advice-item {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.8rem;
        border-left: 3px solid #667eea;
    }
    
    .ai-advice-item-title {
        font-weight: 600;
        color: #2C3E50;
        margin-bottom: 0.5rem;
        font-size: 1rem;
    }
    
    .ai-advice-item-desc {
        font-size: 0.9rem;
        color: #6C7A89;
        line-height: 1.6;
    }
    
    .ai-advice-priority {
        display: inline-block;
        background: #667eea;
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    
    /* 캘린더 스타일 */
    .calendar-container {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        margin: 2rem 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        width: 200px;
        max-width: 200px;
        height: 60px;
        margin-left: auto;
        margin-right: auto;
        display: flex;
        justify-content: center; 
        align-items: center; 
    }
    
    /* 캘린더 날짜 셀에 기록 표시용 동그라미 */
    /* 1. 버튼 주위의 여백(보라색 영역)을 제거 */
    .calendar-day-wrapper .stButton {
        padding: 0 !important;
        margin: 0 !important;
        width: 100% !important;
    }

    .calendar-day-wrapper .stButton > button {
        padding: 4px 0 !important; /* 위아래 여백을 4px로 최소화 */
        margin: 0 !important;
        min-height: 40px !important; /* 모든 버튼 높이 통일 */
        width: 100% !important;
    }

    /* 2. 초록색 점을 버튼 하단에 겹쳐서 배치 */
    .calendar-record-indicator {
        position: absolute;
        bottom: 6px;           /* 버튼 하단에서 6px 위치 */
        left: 50%;
        transform: translateX(-50%); /* 가로 중앙 정렬 */
        width: 6px;
        height: 6px;
        background: #2D8F0B !important; /* 더 진한 초록색으로 가독성 확보 */
        border-radius: 50%;
        pointer-events: none;  /* 클릭 방해 안 되게 함 */
        z-index: 100;          /* 버튼보다 위에 표시 */
    }
    
    /* 기록 표시용 초록 점 (버튼 아래에 표시, 버튼에 가깝게) */
    .calendar-record-indicator {
        display: inline-block;
        width: 6px;
        height: 6px;
        background: #AEEDB9 !important;
        border-radius: 50%;
        margin-top: 2px;
        margin-bottom: 2px;
    }
    
    .calendar-header {
        justify-content: center;
        align-items: center;
    }
    
    .calendar-header h2 {
        font-size: 1.2rem !important;
        text-align: center;
        margin: 0;
    }
    
    .calendar-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .calendar-day-header {
        text-align: center;
        font-weight: 600;
        color: #6C7A89;
        padding: 0.5rem;
        font-size: 0.9rem;
    }
    
    .calendar-day {
        aspect-ratio: 1;
        border: 2px solid #E2E8F0;
        border-radius: 12px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.3s ease;
        background: white;
        position: relative;
        padding: 0.3rem;
    }
    
    .calendar-day:hover {
        border-color: #B8F2A3;
        background: rgba(184, 242, 163, 0.1);
        transform: scale(1.05);
    }
    
    .calendar-day.other-month {
        opacity: 0.3;
        background: #F7F9FA;
    }
    
    .calendar-day.today {
        border-color: #2D8F0B;
        background: rgba(45, 143, 11, 0.1);
        font-weight: 700;
    }
    
    .calendar-day.selected {
        border-color: #667eea;
        background: rgba(102, 126, 234, 0.2);
        font-weight: 700;
    }
    
    .calendar-day-number {
        font-size: 1rem;
        color: #2C3E50;
        margin-bottom: 0.2rem;
    }
    
    .calendar-day-count {
        font-size: 0.7rem;
        color: #B8F2A3;
        background: #2D8F0B;
        border-radius: 50%;
        width: 18px;
        height: 18px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
    }
    
    .calendar-day.has-records .calendar-day-count {
        background: #B8F2A3;
        color: #2D8F0B;
    }
    
    /* 캘린더 날짜 클릭 가능 */
    .calendar-day {
        cursor: pointer;
    }
    
    /* 캘린더 버튼의 padding과 margin 줄이기 */
    .calendar-day-wrapper .stButton {
        padding: 0 !important;
        margin: 0 !important;
    }
    
    .calendar-day-wrapper .stButton > button {
        padding: 0.3rem !important;
        margin: 0 !important;
        min-height: auto !important;
    }
    
    /* Streamlit 제목의 앵커 링크 아이콘 숨기기 */
    .stMarkdown h2 a,
    .stMarkdown h1 a,
    .stMarkdown h3 a,
    .calendar-header h2 a {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'show_record_form' not in st.session_state:
    st.session_state.show_record_form = False
if 'show_records' not in st.session_state:
    st.session_state.show_records = False
if 'show_category_modal' not in st.session_state:
    st.session_state.show_category_modal = False
if 'category_suggestion' not in st.session_state:
    st.session_state.category_suggestion = None
if 'ai_loading' not in st.session_state:
    st.session_state.ai_loading = False
if 'ai_advice' not in st.session_state:
    st.session_state.ai_advice = None
if 'show_ai_advice' not in st.session_state:
    st.session_state.show_ai_advice = False
if 'migrated' not in st.session_state:
    st.session_state.migrated = False
if 'editing_record_id' not in st.session_state:
    st.session_state.editing_record_id = None
if 'editing_record_data' not in st.session_state:
    st.session_state.editing_record_data = None
if 'deleting_record_id' not in st.session_state:
    st.session_state.deleting_record_id = None
if 'show_calendar' not in st.session_state:
    st.session_state.show_calendar = False
if 'selected_calendar_date' not in st.session_state:
    st.session_state.selected_calendar_date = datetime.now().date()
if 'calendar_year' not in st.session_state:
    st.session_state.calendar_year = datetime.now().year
if 'calendar_month' not in st.session_state:
    st.session_state.calendar_month = datetime.now().month
if 'selected_record_date' not in st.session_state:
    st.session_state.selected_record_date = None
if 'show_visualizations' not in st.session_state:
    st.session_state.show_visualizations = False
if 'show_csv_upload' not in st.session_state:
    st.session_state.show_csv_upload = False

# 데이터베이스 초기화
init_database()


def add_record(activity, category, start_time, end_time, memo, record_date=None):
    """새 기록 추가 (데이터베이스)"""
    return db_add_record(activity, category, start_time, end_time, memo, record_date)

def calculate_time_duration(start_time: str, end_time: str) -> float:
    """시간 차이 계산 (분 단위)"""
    try:
        start = datetime.strptime(start_time, "%H:%M")
        end = datetime.strptime(end_time, "%H:%M")
        if end < start:
            # 자정을 넘어가는 경우
            end += timedelta(days=1)
        duration = (end - start).total_seconds() / 60  # 분 단위
        return duration
    except:
        return 0

def parse_csv_file(uploaded_file) -> list:
    """CSV 파일 파싱"""
    try:
        # CSV 파일 읽기
        df = pd.read_csv(uploaded_file, encoding='utf-8')
        
        records = []
        for _, row in df.iterrows():
            # 시간 범위 파싱 (예: "00:00-07:34")
            time_range = str(row['시간(시작-종료)']).strip()
            if '-' in time_range:
                start_time, end_time = time_range.split('-')
                start_time = start_time.strip()
                end_time = end_time.strip()
            else:
                continue
            
            # 날짜 파싱
            date_str = str(row['날짜']).strip()
            
            record = {
                'date': date_str,
                'activity': str(row['활동명']).strip(),
                'category': str(row['카테고리']).strip(),
                'start_time': start_time,
                'end_time': end_time,
                'memo': str(row['메모']).strip() if pd.notna(row['메모']) else ''
            }
            records.append(record)
        
        return records
    except Exception as e:
        st.error(f"CSV 파일 파싱 오류: {str(e)}")
        return []

def import_csv_to_database(records: list) -> dict:
    """CSV 데이터를 데이터베이스에 임포트"""
    success_count = 0
    error_count = 0
    duplicate_count = 0
    
    for record in records:
        try:
            # 중복 체크 (날짜, 활동명, 시작시간이 동일한 경우)
            existing_records = get_records_by_date(record['date'])
            is_duplicate = False
            
            for existing in existing_records:
                if (existing.get('activity') == record['activity'] and
                    existing.get('start_time') == record['start_time']):
                    is_duplicate = True
                    duplicate_count += 1
                    break
            
            if not is_duplicate:
                result = db_add_record(
                    activity=record['activity'],
                    category=record['category'],
                    start_time=record['start_time'],
                    end_time=record['end_time'],
                    memo=record['memo'],
                    record_date=record['date']
                )
                if result:
                    success_count += 1
                else:
                    error_count += 1
        except Exception as e:
            error_count += 1
            print(f"기록 추가 오류: {e}")
    
    return {
        'success': success_count,
        'error': error_count,
        'duplicate': duplicate_count,
        'total': len(records)
    }

def create_calendar_view():
    """캘린더 뷰 생성"""
    year = st.session_state.calendar_year
    month = st.session_state.calendar_month
    
    # 해당 월의 첫 날과 마지막 날
    first_day = datetime(year, month, 1)
    last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # 첫 날의 요일 (월요일=0, 일요일=6)
    start_weekday = first_day.weekday()
    
    # 날짜별 기록 수 가져오기
    start_date = first_day.date()
    end_date = last_day.date()
    month_records = get_records_by_date_range(start_date.isoformat(), end_date.isoformat())
    
    # 날짜별 기록 수 딕셔너리
    date_counts = {}
    for record in month_records:
        date = record.get('date')
        if date in date_counts:
            date_counts[date] += 1
        else:
            date_counts[date] = 1
    
    # 요일 헤더
    weekdays = ['월', '화', '수', '목', '금', '토', '일']
    
    # 캘린더 컨테이너
    st.markdown(f"""
    <div class="calendar-container">
        <div class="calendar-header">
            <h2 style="margin: 0; color: #2C3E50; text-align: center; font-size: 1.2rem;">{year}년 {month}월</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 요일 헤더 표시
    header_cols = st.columns(7)
    for idx, day_name in enumerate(weekdays):
        with header_cols[idx]:
            st.markdown(f'<div class="calendar-day-header" style="text-align: center; font-weight: 600; color: #6C7A89; padding: 0.5rem;">{day_name}</div>', unsafe_allow_html=True)
    
    # 이전 달의 빈 칸 채우기
    today = datetime.now().date()
    selected_date = st.session_state.selected_calendar_date
    
    # 첫 주 시작
    week_cols = st.columns(7)
    col_idx = 0
    
    # 이전 달의 마지막 날들 (월요일부터 시작하므로 start_weekday가 0이면 빈칸 없음)
    prev_month_last = first_day - timedelta(days=1)
    prev_month_days = prev_month_last.day
    
    # 이전 달 날짜 표시
    for i in range(start_weekday):
        with week_cols[col_idx]:
            day_num = prev_month_days - (start_weekday - 1 - i)
            st.markdown(f'<div style="text-align: center; padding: 0.5rem; color: #A0AEC0; opacity: 0.3;">{day_num}</div>', unsafe_allow_html=True)
        col_idx += 1
    
    # 현재 달의 날들
    for day in range(1, last_day.day + 1):
        if col_idx >= 7:
            week_cols = st.columns(7)
            col_idx = 0
        
        current_date = datetime(year, month, day).date()
        date_str = current_date.isoformat()
        count = date_counts.get(date_str, 0)
        
        is_today = current_date == today
        is_selected = current_date == selected_date
        has_records = count > 0
        
        with week_cols[col_idx]:
            # 날짜 셀을 감싸는 컨테이너
            st.markdown('<div class="calendar-day-wrapper">', unsafe_allow_html=True)

            # 날짜 버튼 레이블 (개수 제거, 날짜만 표시)
            button_label = str(day)
            
            # 툴팁 메시지 (마우스 오버 시 표시)
            tooltip_message = f"{year}년 {month}월 {day}일"
            if count > 0:
                tooltip_message += f" - {count}개 기록"
            else:
                tooltip_message += " - 기록 없음"
            
            # 버튼 타입 결정 (오늘 날짜는 primary, 선택된 날짜는 secondary, 나머지는 secondary)
            button_type = "secondary"
            if is_today:
                button_type = "primary"
            
            # 버튼 클릭 처리
            # 버튼 생성
            clicked = st.button(
                button_label, 
                key=f"cal_btn_{date_str}", 
                use_container_width=True, 
                type=button_type, # 오늘만 primary가 들어감
                help=tooltip_message
            )
            
            # 기록이 있는 경우: CSS에 정의된 클래스를 사용하여 버튼 위에 겹침
            if count > 0:
                # div의 margin-top을 2px로 변경하여 버튼과의 간격을 벌림
                st.markdown(f'''
                    <div style="text-align: center; margin-top: 2px; margin-bottom: 4px;">
                        <div class="calendar-record-indicator"></div>
                    </div>
                ''', unsafe_allow_html=True)

            # wrapper 끝
            st.markdown('</div>', unsafe_allow_html=True)

            if clicked:
                st.session_state.selected_calendar_date = current_date
                st.rerun()
            
            # 선택된 날짜 표시 (버튼 아래에 표시)
            if is_selected and not is_today:
                st.markdown(f'<div style="text-align: center; color: #667eea; font-weight: 600; font-size: 0.8rem; margin-top: 0.2rem;">✓ 선택됨</div>', unsafe_allow_html=True)
        
        col_idx += 1
    
    # 다음 달의 첫 날들 (캘린더를 채우기 위해)
    remaining_days = 7 - (col_idx % 7)
    if remaining_days < 7 and remaining_days > 0:
        for i in range(remaining_days):
            if col_idx >= 7:
                week_cols = st.columns(7)
                col_idx = 0
            with week_cols[col_idx]:
                st.markdown('<div class="calendar-day-wrapper">', unsafe_allow_html=True)
            col_idx += 1
    
    # 월 이동 버튼
    col_prev, col_current, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("◀ 이전 달", key="prev_month"):
            if month == 1:
                st.session_state.calendar_year = year - 1
                st.session_state.calendar_month = 12
            else:
                st.session_state.calendar_month = month - 1
            st.rerun()
    
    with col_current:
        st.markdown(f"<div style='text-align: center; padding: 0.5rem; color: #2C3E50; font-weight: 600;'>{year}년 {month}월</div>", unsafe_allow_html=True)
    
    with col_next:
        if st.button("다음 달 ▶", key="next_month"):
            if month == 12:
                st.session_state.calendar_year = year + 1
                st.session_state.calendar_month = 1
            else:
                st.session_state.calendar_month = month + 1
            st.rerun()
    
    # 선택한 날짜의 기록 표시
    st.markdown("---")
    if st.session_state.selected_calendar_date:
        selected_date_str = st.session_state.selected_calendar_date.isoformat()
        selected_records = get_records_by_date(selected_date_str)
        
        # 삭제 중인 기록은 목록에서 제외
        if st.session_state.deleting_record_id:
            selected_records = [r for r in selected_records if r.get('id') != st.session_state.deleting_record_id]
        
        st.markdown(f"""
        <h3 style="color: #2C3E50; margin: 1rem 0;">📅 {st.session_state.selected_calendar_date.strftime('%Y년 %m월 %d일')} 기록</h3>
        """, unsafe_allow_html=True)
        
        if selected_records:
            for record in selected_records:
                record_id = record.get('id', '')
                
                # 삭제 중인 기록은 표시하지 않음
                if record_id == st.session_state.deleting_record_id:
                    continue
                    
                activity = record.get('activity', '')
                category = record.get('category', '')
                start_time = record.get('start_time', '')
                end_time = record.get('end_time', '')
                memo = record.get('memo', '') or ''
                
                col_card, col_actions = st.columns([4, 1])
                
                with col_card:
                    st.markdown(f"""
                    <div class="record-card">
                        <div class="record-card-title">{activity}</div>
                        <div class="record-card-meta">
                            <span>카테고리: {category}</span> | 
                            <span>시간: {start_time} - {end_time}</span>
                        </div>
                        {f"<p style='color: #6C7A89; margin: 0.5rem 0 0 0; font-size: 0.95rem;'>{memo}</p>" if memo else ""}
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_actions:
                    st.markdown("<br>", unsafe_allow_html=True)
                    col_edit, col_delete = st.columns(2)
                    
                    with col_edit:
                        if st.button("✏️", key=f"edit_cal_{record_id}", help="수정"):
                            st.session_state.editing_record_id = record_id
                            st.session_state.editing_record_data = {
                                'activity': activity,
                                'category': category,
                                'start_time': start_time,
                                'end_time': end_time,
                                'memo': memo
                            }
                            st.rerun()
                    
                    with col_delete:
                        if st.button("🗑️", key=f"delete_cal_{record_id}", help="삭제"):
                            st.session_state.deleting_record_id = record_id
                            st.rerun()
        else:
            st.info(f"{st.session_state.selected_calendar_date.strftime('%Y년 %m월 %d일')}에는 기록이 없습니다.")
            
            # 해당 날짜에 기록 추가 버튼
            if st.button("+ 이 날짜에 기록 추가", key="add_record_to_date"):
                st.session_state.show_category_modal = True
                st.session_state.selected_record_date = st.session_state.selected_calendar_date
                st.rerun()

def create_visualizations():
    """데이터베이스 기록 시각화 생성"""
    all_records = get_all_records()
    
    if not all_records:
        st.info("📊 시각화할 데이터가 없습니다. 기록을 추가해보세요!")
        return
    
    # 데이터프레임 생성
    df = pd.DataFrame(all_records)
    
    # 시간 계산 (분 단위)
    df['duration_minutes'] = df.apply(
        lambda row: calculate_time_duration(row['start_time'], row['end_time']), 
        axis=1
    )
    df['date'] = pd.to_datetime(df['date'])
    
    # 탭 생성
    tab1, tab2, tab3, tab4 = st.tabs(["📅 날짜별 통계", "📊 카테고리별 통계", "⏰ 시간 분석", "📈 전체 통계"])
    
    with tab1:
        st.subheader("날짜별 카테고리 기록")
        
        # 최근 30일 데이터
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        recent_records = get_records_by_date_range(start_date.isoformat(), end_date.isoformat())
        
        if recent_records:
            df_recent = pd.DataFrame(recent_records)
            df_recent['date'] = pd.to_datetime(df_recent['date'])
            
            # 날짜별 카테고리별 기록 수 계산
            daily_category_count = df_recent.groupby(['date', 'category']).size().reset_index(name='count')
            daily_category_count = daily_category_count.sort_values('date')
            
            # 카테고리 순서 정의
            category_order = ["수면", "식사", "일과", "운동", "취미", "기타"]
            
            # 스택 바 차트로 날짜별 카테고리별 기록 표시
            fig = px.bar(
                daily_category_count,
                x='date',
                y='count',
                color='category',
                title="최근 30일 날짜별 카테고리 기록",
                labels={'date': '날짜', 'count': '기록 수', 'category': '카테고리'},
                color_discrete_map={
                    '수면': '#87CEEB',
                    '식사': '#B0E0E6',
                    '일과': '#ADD8E6',
                    '운동': '#E0F6FF',
                    '취미': '#C6E2FF',
                    '기타': '#A8D8EA'
                },
                category_orders={'category': category_order}
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Noto Sans KR", size=12),
                height=400,
                barmode='stack',  # 스택 모드로 카테고리를 쌓아서 표시
                legend=dict(
                    title="카테고리",
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.02
                )
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("최근 30일간의 기록이 없습니다.")
    
    with tab2:
        st.subheader("카테고리별 분포")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 카테고리별 기록 수
            category_count = df['category'].value_counts().reset_index()
            category_count.columns = ['category', 'count']
            
            # 카테고리 순서 정의
            category_order = ["수면", "식사", "일과", "운동", "취미", "기타"]
            
            # 카테고리 순서에 따라 정렬
            category_count['순서'] = category_count['category'].apply(
                lambda x: category_order.index(x) if x in category_order else len(category_order)
            )
            category_count = category_count.sort_values('순서')
            category_count = category_count.drop('순서', axis=1)
            
            # 하늘색 계열 색상 팔레트
            sky_blue_colors = [
                '#87CEEB',  # Sky Blue
                '#B0E0E6',  # Powder Blue
                '#ADD8E6',  # Light Blue
                '#E0F6FF',  # Very Light Blue
                '#C6E2FF',  # Light Sky Blue
                '#A8D8EA',  # Soft Sky Blue
                '#B8E6FF',  # Bright Sky Blue
                '#9ED5E8'   # Medium Sky Blue
            ]
            
            fig_pie = px.pie(
                category_count,
                values='count',
                names='category',
                title="카테고리별 기록 분포",
                color_discrete_sequence=sky_blue_colors,
                category_orders={'category': category_order}
            )
            fig_pie.update_layout(
                font=dict(family="Noto Sans KR", size=12),
                height=400
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # 카테고리별 총 시간
            category_time = df.groupby('category')['duration_minutes'].sum().reset_index()
            category_time['hours'] = category_time['duration_minutes'] / 60
            
            # 카테고리 순서 정의
            category_order = ["수면", "식사", "일과", "운동", "취미", "기타"]
            
            # 카테고리 순서에 따라 정렬
            category_time['순서'] = category_time['category'].apply(
                lambda x: category_order.index(x) if x in category_order else len(category_order)
            )
            category_time = category_time.sort_values('순서')
            category_time = category_time.drop('순서', axis=1)
            
            fig_bar = px.bar(
                category_time,
                x='category',
                y='hours',
                title="카테고리별 총 시간 (시간)",
                labels={'category': '카테고리', 'hours': '시간'},
                color='hours',
                color_continuous_scale='Blues',
                category_orders={'category': category_order}
            )
            fig_bar.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Noto Sans KR", size=12),
                height=400,
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig_bar, use_container_width=True)
    
    with tab3:
        st.subheader("시간대별 활동 분석")
        
        # 시간대별 기록 수
        df['start_hour'] = df['start_time'].apply(lambda x: int(x.split(':')[0]))
        hourly_count = df.groupby('start_hour').size().reset_index(name='count')
        hourly_count = hourly_count.sort_values('start_hour')
        
        fig_hour = px.line(
            hourly_count,
            x='start_hour',
            y='count',
            title="시간대별 활동 시작 횟수",
            labels={'start_hour': '시간 (시)', 'count': '기록 수'},
            markers=True
        )
        fig_hour.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Noto Sans KR", size=12),
            height=400,
            xaxis=dict(tickmode='linear', tick0=0, dtick=1)
        )
        st.plotly_chart(fig_hour, use_container_width=True)
        
        # 평균 활동 시간
        st.subheader("카테고리별 평균 활동 시간")
        category_avg = df.groupby('category')['duration_minutes'].mean().reset_index()
        category_avg['avg_hours'] = category_avg['duration_minutes'] / 60
        
        # 카테고리 순서 정의
        category_order = ["수면", "식사", "일과", "운동", "취미", "기타"]
        
        # 카테고리 순서에 따라 정렬
        category_avg['순서'] = category_avg['category'].apply(
            lambda x: category_order.index(x) if x in category_order else len(category_order)
        )
        category_avg = category_avg.sort_values('순서')
        category_avg = category_avg.drop('순서', axis=1)
        
        fig_avg = px.bar(
            category_avg,
            x='category',
            y='avg_hours',
            title="카테고리별 평균 활동 시간",
            labels={'category': '카테고리', 'avg_hours': '평균 시간 (시간)'},
            color='avg_hours',
            color_continuous_scale='Blues',
            category_orders={'category': category_order}
        )
        fig_avg.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Noto Sans KR", size=12),
            height=400,
            xaxis_tickangle=-45
        )
        st.plotly_chart(fig_avg, use_container_width=True)
    
    with tab4:
        st.subheader("전체 통계 요약")
        
        # 통계 정보
        stats = get_statistics()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("총 기록 수", f"{stats['total_records']}개")
        
        with col2:
            total_time = df['duration_minutes'].sum() / 60
            st.metric("총 활동 시간", f"{total_time:.1f}시간")
        
        with col3:
            avg_time = df['duration_minutes'].mean() / 60 if len(df) > 0 else 0
            st.metric("평균 활동 시간", f"{avg_time:.1f}시간")
        
        with col4:
            unique_days = df['date'].nunique()
            st.metric("기록한 날짜", f"{unique_days}일")
        
        # 카테고리별 상세 통계
        st.subheader("카테고리별 상세 통계")
        if stats['category_stats']:
            # 카테고리 순서 정의
            category_order = ["수면", "식사", "일과", "운동", "취미", "기타"]
            
            # 카테고리별 기록 수
            category_count_data = [
                {'카테고리': k, '기록 수': v} 
                for k, v in stats['category_stats'].items()
            ]
            
            # 카테고리별 시간 계산
            category_time_data = df.groupby('category')['duration_minutes'].sum().reset_index()
            category_time_data['시간(시간)'] = (category_time_data['duration_minutes'] / 60).round(2)
            
            # 데이터 병합
            category_df = pd.DataFrame(category_count_data)
            category_df = category_df.merge(
                category_time_data[['category', '시간(시간)']], 
                left_on='카테고리', 
                right_on='category', 
                how='left'
            )
            category_df = category_df.drop('category', axis=1)
            category_df['시간(시간)'] = category_df['시간(시간)'].fillna(0)
            
            # 카테고리 순서에 따라 정렬 (지정된 순서 우선, 그 다음 기록 수 순)
            category_df['순서'] = category_df['카테고리'].apply(
                lambda x: category_order.index(x) if x in category_order else len(category_order)
            )
            category_df = category_df.sort_values(['순서', '기록 수'], ascending=[True, False])
            category_df = category_df.drop('순서', axis=1)
            
            # 컬럼 순서: 카테고리, 기록 수, 시간
            category_df = category_df[['카테고리', '기록 수', '시간(시간)']]
            
            st.dataframe(category_df, use_container_width=True, hide_index=True)
        
        # 최근 활동 추이
        st.subheader("주간 활동 추이")
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        weekly_records = get_records_by_date_range(start_date.isoformat(), end_date.isoformat())
        
        if weekly_records:
            df_weekly = pd.DataFrame(weekly_records)
            df_weekly['date'] = pd.to_datetime(df_weekly['date'])
            df_weekly['duration_minutes'] = df_weekly.apply(
                lambda row: calculate_time_duration(row['start_time'], row['end_time']), 
                axis=1
            )
            daily_stats = df_weekly.groupby('date').agg({
                'duration_minutes': ['sum', 'count']
            }).reset_index()
            daily_stats.columns = ['date', '총 시간(분)', '기록 수']
            daily_stats['총 시간(시간)'] = daily_stats['총 시간(분)'] / 60
            
            fig_weekly = go.Figure()
            fig_weekly.add_trace(go.Scatter(
                x=daily_stats['date'],
                y=daily_stats['기록 수'],
                mode='lines+markers',
                name='기록 수',
                line=dict(color='#B8F2A3', width=3),
                marker=dict(size=8)
            ))
            fig_weekly.add_trace(go.Scatter(
                x=daily_stats['date'],
                y=daily_stats['총 시간(시간)'],
                mode='lines+markers',
                name='총 시간(시간)',
                yaxis='y2',
                line=dict(color='#667eea', width=3),
                marker=dict(size=8)
            ))
            fig_weekly.update_layout(
                title="최근 7일 활동 추이",
                xaxis_title="날짜",
                yaxis_title="기록 수",
                yaxis2=dict(title="총 시간(시간)", overlaying='y', side='right'),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Noto Sans KR", size=12),
                height=400,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_weekly, use_container_width=True)
        else:
            st.info("최근 7일간의 기록이 없습니다.")
    
    # 실시간 피드백 섹션 추가
    st.markdown("---")
    st.markdown("""
    <div style="max-width: 1000px; margin: 2rem auto;">
        <h2 style="text-align: center; color: #2C3E50; margin-bottom: 1rem;">💬 실시간 피드백</h2>
        <p style="text-align: center; color: #6C7A89; margin-bottom: 2rem;">AI가 분석한 당신의 루틴 패턴에 대한 피드백입니다</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 피드백 로딩 및 표시
    with st.spinner("피드백을 생성하는 중..."):
        try:
            feedback_data = get_realtime_feedback()
            
            if feedback_data and 'feedbacks' in feedback_data:
                # 요약 표시
                if 'summary' in feedback_data:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                padding: 1.5rem; 
                                border-radius: 12px; 
                                margin-bottom: 1.5rem;
                                color: white;
                                text-align: center;
                                font-size: 1.1rem;
                                font-weight: 500;">
                        {feedback_data['summary']}
                    </div>
                    """, unsafe_allow_html=True)
                
                # 피드백 카드 표시
                feedbacks = feedback_data['feedbacks']
                
                # 타입별 색상 정의
                type_colors = {
                    'positive': {'bg': '#E8F5E9', 'border': '#4CAF50', 'icon': '✅'},
                    'suggestion': {'bg': '#FFF3E0', 'border': '#FF9800', 'icon': '💡'},
                    'neutral': {'bg': '#E3F2FD', 'border': '#2196F3', 'icon': '📊'}
                }
                
                # 피드백을 타입별로 정렬 (positive -> suggestion -> neutral)
                type_order = ['positive', 'suggestion', 'neutral']
                sorted_feedbacks = sorted(feedbacks, key=lambda x: type_order.index(x.get('type', 'neutral')) if x.get('type', 'neutral') in type_order else 999)
                
                for idx, feedback in enumerate(sorted_feedbacks):
                    feedback_type = feedback.get('type', 'neutral')
                    colors = type_colors.get(feedback_type, type_colors['neutral'])
                    
                    st.markdown(f"""
                    <div style="background: {colors['bg']}; 
                                border-left: 4px solid {colors['border']}; 
                                padding: 1.5rem; 
                                border-radius: 8px; 
                                margin-bottom: 1rem;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                            <span style="font-size: 1.5rem; margin-right: 0.5rem;">{colors['icon']}</span>
                            <h3 style="margin: 0; color: #2C3E50; font-size: 1.2rem;">{feedback.get('title', '피드백')}</h3>
                        </div>
                        <p style="margin: 0; color: #4A5568; line-height: 1.6; font-size: 1rem;">{feedback.get('description', '')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # 타임스탬프 표시
                if 'timestamp' in feedback_data:
                    st.markdown(f"""
                    <div style="text-align: center; color: #A0AEC0; font-size: 0.85rem; margin-top: 1rem;">
                        마지막 업데이트: {feedback_data['timestamp']}
                    </div>
                    """, unsafe_allow_html=True)
                
                # 새로고침 버튼
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("🔄 피드백 새로고침", use_container_width=True, key="refresh_feedback"):
                        st.rerun()
            else:
                st.info("피드백을 생성할 수 없습니다. 기록을 추가해보세요!")
        except Exception as e:
            st.error(f"피드백을 불러오는 중 오류가 발생했습니다: {str(e)}")
            st.info("잠시 후 다시 시도해주세요.")

# 메인 화면 - 디자인에 맞춘 초기 화면
if not st.session_state.show_record_form and not st.session_state.show_records and not st.session_state.show_category_modal and not st.session_state.show_calendar and not st.session_state.editing_record_id and not st.session_state.deleting_record_id and not st.session_state.show_visualizations:
    # 중앙 컨텐츠 - 모든 요소를 하나의 컨테이너에
    st.markdown("""
    <div class="center-content">
        <h1 class="main-title">라이프챙김</h1>
        <p class="subtitle">AI 루틴 비서로 시작하는 초개인화 일상</p>
    """, unsafe_allow_html=True)
    
    # 메인 버튼
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="main-button-wrapper">', unsafe_allow_html=True)
        if st.button("오늘의 기록", use_container_width=True, key="main_record_button"):
            st.session_state.show_category_modal = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 페이지네이션 점들
    st.markdown("""
        <div class="pagination-dots">
            <div class="pagination-dot active"></div>
            <div class="pagination-dot"></div>
            <div class="pagination-dot"></div>
        </div>
    """, unsafe_allow_html=True)
    
    # 캘린더 및 시각화 버튼
    st.markdown("""
    <div style="margin: 2rem 0;">
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        col_cal, col_viz = st.columns(2)
        with col_cal:
            if st.button("📅 캘린더 보기", use_container_width=True, key="show_calendar_btn"):
                st.session_state.show_calendar = True
                st.rerun()
        with col_viz:
            if st.button("📊 통계 보기", use_container_width=True, key="show_visualizations_btn"):
                st.session_state.show_visualizations = True
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    
    # AI 조언 섹션
    st.markdown("---")
    st.markdown("""
    <div style="max-width: 600px; margin: 2rem auto;">
        <h3 style="text-align: center; color: #2C3E50; margin-bottom: 1rem;">🤖 AI 조언 받기</h3>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("ai_advice_form", clear_on_submit=False):
        advice_input = st.text_area(
            "현재 상황이나 고민을 입력해주세요",
            placeholder="예: 요즘 운동을 시작하고 싶은데 시간이 부족해요, 루틴을 지키기가 어려워요 등",
            height=100,
            key="ai_advice_input"
        )
        
        col_submit, col_clear = st.columns([1, 1])
        with col_submit:
            get_advice = st.form_submit_button("조언 받기", use_container_width=True)
        with col_clear:
            clear_advice = st.form_submit_button("초기화", use_container_width=True)
        
        if clear_advice:
            st.session_state.ai_advice = None
            st.session_state.show_ai_advice = False
            st.rerun()
        
        if get_advice and advice_input:
            with st.spinner("AI가 조언을 생성하는 중입니다..."):
                try:
                    advice_result = get_ai_advice(advice_input)
                    st.session_state.ai_advice = advice_result
                    st.session_state.show_ai_advice = True
                except Exception as e:
                    st.error(f"AI 조언을 가져오는 중 오류가 발생했습니다: {str(e)}")
                    st.session_state.ai_advice = None
    
    # AI 조언 결과 표시
    if st.session_state.show_ai_advice and st.session_state.ai_advice:
        advice = st.session_state.ai_advice
        st.markdown(f"""
        <div class="ai-advice-card">
            <div class="ai-advice-title">
                ✨ AI 조언
            </div>
            <div class="ai-advice-summary">
                {advice.get('summary', '')}
            </div>
        """, unsafe_allow_html=True)
        
        # 조언 목록 표시 (priority 순으로 정렬)
        if advice.get('advices'):
            sorted_advices = sorted(advice['advices'], key=lambda x: x.get('priority', 999))
            for idx, item in enumerate(sorted_advices, 1):
                st.markdown(f"""
                <div class="ai-advice-item">
                    <div class="ai-advice-item-title">
                        <span class="ai-advice-priority">우선순위 {item.get('priority', idx)}</span>
                        {item.get('title', '')}
                    </div>
                    <div class="ai-advice-item-desc">
                        {item.get('description', '')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# 기록 입력 폼
if st.session_state.show_record_form:
    st.markdown("""
    <div class="center-content">
        <h1 class="main-title" style="margin-bottom: 1rem;">라이프챙김</h1>
        <div class="record-form-container">
            <div class="record-form-title">새 기록 추가</div>
    """, unsafe_allow_html=True)
    
    with st.form("record_form", clear_on_submit=True):
        activity = st.text_input("활동/루틴 *", placeholder="예: 아침 명상, 운동, 독서 등")
        category = st.selectbox(
            "카테고리",
            ["수면", "식사", "일과", "운동", "취미", "기타"]
        )
        
        col1, col2 = st.columns(2)
        with col1:
            start_time_str = st.text_input("시작 시간 (HH:MM)", value=datetime.now().strftime("%H:%M"), key="form_start_time", placeholder="예: 09:00")
        with col2:
            end_time_str = st.text_input("종료 시간 (HH:MM)", value=datetime.now().strftime("%H:%M"), key="form_end_time", placeholder="예: 10:30")
        
        memo = st.text_area("메모 (선택)", placeholder="자유롭게 기록해주세요...", height=100)
        
        col_submit, col_cancel = st.columns([1, 1])
        with col_submit:
            submitted = st.form_submit_button("기록 저장", use_container_width=True)
        with col_cancel:
            if st.form_submit_button("취소", use_container_width=True):
                st.session_state.show_record_form = False
                st.rerun()
        
        if submitted:
            if activity:
                # 시간 형식 검증
                time_format_valid = True
                start_time = None
                end_time = None
                
                try:
                    start_time = datetime.strptime(start_time_str, "%H:%M").time()
                except ValueError:
                    st.warning("시작 시간 형식이 올바르지 않습니다. HH:MM 형식으로 입력해주세요 (예: 09:00)")
                    time_format_valid = False
                
                try:
                    end_time = datetime.strptime(end_time_str, "%H:%M").time()
                except ValueError:
                    st.warning("종료 시간 형식이 올바르지 않습니다. HH:MM 형식으로 입력해주세요 (예: 10:30)")
                    time_format_valid = False
                
                if time_format_valid:
                    if start_time >= end_time:
                        st.warning("종료 시간은 시작 시간보다 늦어야 합니다.")
                    else:
                        add_record(activity, category, start_time_str, end_time_str, memo)
                        st.success("기록이 저장되었습니다! 🌱")
                        st.session_state.show_record_form = False
                        st.session_state.show_records = True
                        st.session_state.selected_record_date = None
                        st.rerun()
            else:
                st.warning("활동/루틴을 입력해주세요.")
    
    st.markdown("</div></div>", unsafe_allow_html=True)

# 기록 목록 보기
if st.session_state.show_records and not st.session_state.show_record_form and not st.session_state.show_category_modal and not st.session_state.editing_record_id and not st.session_state.deleting_record_id:
    st.markdown("""
    <div class="center-content">
        <h1 class="main-title" style="margin-bottom: 1rem;">라이프챙김</h1>
        <p class="subtitle" style="margin-bottom: 2rem;">오늘의 기록</p>
    """, unsafe_allow_html=True)
    
    # 오늘의 기록 목록 (데이터베이스에서 조회 - 삭제 후 최신 데이터 가져오기)
    today = datetime.now().date().isoformat()
    today_records = get_records_by_date(today)
    
    # 삭제 중인 기록은 목록에서 제외
    if st.session_state.deleting_record_id:
        today_records = [r for r in today_records if r.get('id') != st.session_state.deleting_record_id]
    
    if today_records:
        # 최신순으로 표시 (데이터베이스는 시간순으로 정렬되어 있으므로 역순으로)
        for idx, record in enumerate(reversed(today_records)):
            record_id = record.get('id', '')
            
            # 삭제 중인 기록은 표시하지 않음
            if record_id == st.session_state.deleting_record_id:
                continue
                
            activity = record.get('activity', '')
            category = record.get('category', '')
            start_time = record.get('start_time', '')
            end_time = record.get('end_time', '')
            memo = record.get('memo', '') or ''
            
            # 기록 카드
            col_card, col_actions = st.columns([4, 1])
            
            with col_card:
                st.markdown(f"""
                <div class="record-card">
                    <div class="record-card-title">{activity}</div>
                    <div class="record-card-meta">
                        <span>카테고리: {category}</span> | 
                        <span>시간: {start_time} - {end_time}</span>
                    </div>
                    {f"<p style='color: #6C7A89; margin: 0.5rem 0 0 0; font-size: 0.95rem;'>{memo}</p>" if memo else ""}
                </div>
                """, unsafe_allow_html=True)
            
            with col_actions:
                st.markdown("<br>", unsafe_allow_html=True)
                col_edit, col_delete = st.columns(2)
                
                with col_edit:
                    if st.button("✏️", key=f"edit_{record_id}", help="수정"):
                        st.session_state.editing_record_id = record_id
                        st.session_state.editing_record_data = {
                            'activity': activity,
                            'category': category,
                            'start_time': start_time,
                            'end_time': end_time,
                            'memo': memo
                        }
                        st.rerun()
                
                with col_delete:
                    if st.button("🗑️", key=f"delete_{record_id}", help="삭제"):
                        st.session_state.deleting_record_id = record_id
                        st.rerun()
    else:
        st.markdown("""
        <div class="empty-state">
            <p style="font-size: 1.1rem; margin: 0;">아직 오늘의 기록이 없습니다.</p>
            <p style="font-size: 0.9rem; margin: 0.5rem 0 0 0; color: #A0AEC0;">위의 버튼을 눌러 오늘의 활동을 기록해보세요!</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 시각화 섹션
    st.markdown("---")
    st.markdown("""
    <div style="max-width: 1000px; margin: 2rem auto;">
        <h2 style="text-align: center; color: #2C3E50; margin-bottom: 2rem;">📊 기록 통계 및 시각화</h2>
    </div>
    """, unsafe_allow_html=True)
    
    create_visualizations()
    
    # 오늘의 기록 버튼 (메인 버튼 스타일)
    st.markdown("""
    <div style="margin: 2rem 0;">
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="main-button-wrapper">', unsafe_allow_html=True)
        if st.button("오늘의 기록", use_container_width=True, key="record_button_from_list"):
            st.session_state.show_category_modal = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # AI 조언 섹션 (기록 목록 화면)
    st.markdown("---")
    st.markdown("""
    <div style="max-width: 600px; margin: 2rem auto;">
        <h3 style="text-align: center; color: #2C3E50; margin-bottom: 1rem;">🤖 AI 조언 받기</h3>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("ai_advice_form_list", clear_on_submit=False):
        advice_input_list = st.text_area(
            "현재 상황이나 고민을 입력해주세요",
            placeholder="예: 요즘 운동을 시작하고 싶은데 시간이 부족해요, 루틴을 지키기가 어려워요 등",
            height=100,
            key="ai_advice_input_list"
        )
        
        col_submit, col_clear = st.columns([1, 1])
        with col_submit:
            get_advice_list = st.form_submit_button("조언 받기", use_container_width=True)
        with col_clear:
            clear_advice_list = st.form_submit_button("초기화", use_container_width=True)
        
        if clear_advice_list:
            st.session_state.ai_advice = None
            st.session_state.show_ai_advice = False
            st.rerun()
        
        if get_advice_list and advice_input_list:
            with st.spinner("AI가 조언을 생성하는 중입니다..."):
                try:
                    advice_result = get_ai_advice(advice_input_list)
                    st.session_state.ai_advice = advice_result
                    st.session_state.show_ai_advice = True
                except Exception as e:
                    st.error(f"AI 조언을 가져오는 중 오류가 발생했습니다: {str(e)}")
                    st.session_state.ai_advice = None
    
    # AI 조언 결과 표시
    if st.session_state.show_ai_advice and st.session_state.ai_advice:
        advice = st.session_state.ai_advice
        st.markdown(f"""
        <div class="ai-advice-card">
            <div class="ai-advice-title">
                ✨ AI 조언
            </div>
            <div class="ai-advice-summary">
                {advice.get('summary', '')}
            </div>
        """, unsafe_allow_html=True)
        
        # 조언 목록 표시 (priority 순으로 정렬)
        if advice.get('advices'):
            sorted_advices = sorted(advice['advices'], key=lambda x: x.get('priority', 999))
            for idx, item in enumerate(sorted_advices, 1):
                st.markdown(f"""
                <div class="ai-advice-item">
                    <div class="ai-advice-item-title">
                        <span class="ai-advice-priority">우선순위 {item.get('priority', idx)}</span>
                        {item.get('title', '')}
                    </div>
                    <div class="ai-advice-item-desc">
                        {item.get('description', '')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# CSV 업로드 화면
if st.session_state.show_csv_upload and not st.session_state.show_category_modal and not st.session_state.editing_record_id and not st.session_state.deleting_record_id:
    st.markdown("""
    <div class="center-content">
        <h1 class="main-title" style="margin-bottom: 1rem;">📁 CSV 파일 업로드</h1>
        <p class="subtitle" style="margin-bottom: 2rem;">CSV 파일을 업로드하여 기록 데이터를 가져옵니다</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="max-width: 800px; margin: 0 auto; background: white; border-radius: 20px; padding: 2rem; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);">
    """, unsafe_allow_html=True)
    
    # CSV 파일 형식 안내
    st.markdown("### 📋 CSV 파일 형식")
    st.markdown("""
    CSV 파일은 다음 형식이어야 합니다:
    - **컬럼**: 날짜, 시간(시작-종료), 활동명, 카테고리, 메모
    - **날짜 형식**: YYYY-MM-DD (예: 2026-01-01)
    - **시간 형식**: HH:MM-HH:MM (예: 09:00-10:30)
    - **카테고리**: 수면, 식사, 일과, 운동, 취미, 기타
    """)
    
    st.markdown("---")
    
    # 파일 업로드
    uploaded_file = st.file_uploader(
        "CSV 파일 선택",
        type=['csv'],
        help="routine_data_v2.csv 형식의 CSV 파일을 업로드하세요"
    )
    
    if uploaded_file is not None:
        # 파일 미리보기
        st.markdown("### 📄 파일 미리보기")
        try:
            df_preview = pd.read_csv(uploaded_file, encoding='utf-8', nrows=5)
            st.dataframe(df_preview, use_container_width=True)
        except Exception as e:
            st.error(f"파일 읽기 오류: {str(e)}")
        
        # 업로드 버튼
        col_upload, col_cancel = st.columns([1, 1])
        
        with col_upload:
            if st.button("✅ 데이터베이스에 임포트", use_container_width=True, key="import_csv", type="primary"):
                with st.spinner("CSV 파일을 파싱하고 데이터베이스에 저장하는 중..."):
                    # 파일을 처음부터 다시 읽기
                    uploaded_file.seek(0)
                    records = parse_csv_file(uploaded_file)
                    
                    if records:
                        result = import_csv_to_database(records)
                        
                        st.success(f"""
                        ✅ 임포트 완료!
                        - 성공: {result['success']}개
                        - 중복: {result['duplicate']}개 (건너뜀)
                        - 오류: {result['error']}개
                        - 전체: {result['total']}개
                        """)
                        
                        # 잠시 후 메인 화면으로 돌아가기
                        import time
                        time.sleep(2)
                        st.session_state.show_csv_upload = False
                        st.rerun()
                    else:
                        st.error("CSV 파일에서 데이터를 읽을 수 없습니다. 파일 형식을 확인해주세요.")
        
        with col_cancel:
            if st.button("취소", use_container_width=True, key="cancel_csv_upload"):
                st.session_state.show_csv_upload = False
                st.rerun()
    
    # 돌아가기 버튼
    st.markdown("---")
    col_back1, col_back2, col_back3 = st.columns([1, 2, 1])
    with col_back2:
        if st.button("← 메인으로", use_container_width=True, key="back_from_csv"):
            st.session_state.show_csv_upload = False
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

# 시각화 화면
if st.session_state.show_visualizations and not st.session_state.show_category_modal and not st.session_state.editing_record_id and not st.session_state.deleting_record_id:
    st.markdown("""
    <div class="center-content">
        <h1 class="main-title" style="margin-bottom: 1rem;">📊 통계 및 시각화</h1>
        <p class="subtitle" style="margin-bottom: 2rem;">데이터베이스에 저장된 기록을 분석하고 시각화합니다</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 시각화 생성
    create_visualizations()
    
    # 돌아가기 버튼
    st.markdown("<br>", unsafe_allow_html=True)
    col_back1, col_back2, col_back3 = st.columns([1, 2, 1])
    with col_back2:
        if st.button("← 메인으로", use_container_width=True, key="back_from_visualizations"):
            st.session_state.show_visualizations = False
            st.rerun()

# 캘린더 화면
if st.session_state.show_calendar and not st.session_state.show_category_modal and not st.session_state.editing_record_id and not st.session_state.deleting_record_id and not st.session_state.show_visualizations:
    st.markdown("""
    <div class="center-content">
        <h1 class="main-title" style="margin-bottom: 1rem;">📅 캘린더</h1>
        <p class="subtitle" style="margin-bottom: 2rem;">캘린더에서 날짜를 클릭하면 해당 날짜의 기록을 확인할 수 있습니다</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 캘린더 뷰
    create_calendar_view()
    
    # 돌아가기 버튼
    st.markdown("<br>", unsafe_allow_html=True)
    col_back1, col_back2, col_back3 = st.columns([1, 2, 1])
    with col_back2:
        if st.button("← 메인으로", use_container_width=True, key="back_from_calendar"):
            st.session_state.show_calendar = False
            st.rerun()

# 기록 수정 모달
if st.session_state.editing_record_id and st.session_state.editing_record_data:
    edit_data = st.session_state.editing_record_data
    
    st.markdown("""
    <div class="center-content" style="background: #F7F9FA; min-height: 100vh;">
        <div class="record-form-container" style="max-width: 700px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
                <h2 class="modal-title" style="margin: 0;">기록 수정</h2>
            </div>
    """, unsafe_allow_html=True)
    
    with st.form("edit_record_form", clear_on_submit=False):
        activity_edit = st.text_input(
            "활동/루틴 *",
            value=edit_data.get('activity', ''),
            key="edit_activity"
        )
        
        category_options = ["수면", "식사", "일과", "운동", "취미", "기타"]
        default_category_idx = category_options.index(edit_data.get('category', '기타')) if edit_data.get('category') in category_options else 5
        
        category_edit = st.selectbox(
            "카테고리 *",
            category_options,
            index=default_category_idx,
            key="edit_category"
        )
        
        # 시간 입력
        col1, col2 = st.columns(2)
        with col1:
            start_time_edit_str = st.text_input("시작 시간 (HH:MM)", value=edit_data.get('start_time', datetime.now().strftime("%H:%M")), key="edit_start_time", placeholder="예: 09:00")
        with col2:
            end_time_edit_str = st.text_input("종료 시간 (HH:MM)", value=edit_data.get('end_time', datetime.now().strftime("%H:%M")), key="edit_end_time", placeholder="예: 10:30")
        
        memo_edit = st.text_area(
            "메모 (선택)",
            value=edit_data.get('memo', ''),
            placeholder="자유롭게 기록해주세요...",
            height=100,
            key="edit_memo"
        )
        
        col_submit, col_cancel = st.columns([1, 1])
        with col_submit:
            submitted_edit = st.form_submit_button("수정 저장", use_container_width=True)
        with col_cancel:
            cancel_edit = st.form_submit_button("취소", use_container_width=True)
        
        if cancel_edit:
            st.session_state.editing_record_id = None
            st.session_state.editing_record_data = None
            st.rerun()
        
        if submitted_edit:
            if activity_edit:
                # 시간 형식 검증
                time_format_valid = True
                start_time_edit = None
                end_time_edit = None
                
                try:
                    start_time_edit = datetime.strptime(start_time_edit_str, "%H:%M").time()
                except ValueError:
                    st.warning("시작 시간 형식이 올바르지 않습니다. HH:MM 형식으로 입력해주세요 (예: 09:00)")
                    time_format_valid = False
                
                try:
                    end_time_edit = datetime.strptime(end_time_edit_str, "%H:%M").time()
                except ValueError:
                    st.warning("종료 시간 형식이 올바르지 않습니다. HH:MM 형식으로 입력해주세요 (예: 10:30)")
                    time_format_valid = False
                
                if time_format_valid:
                    if start_time_edit >= end_time_edit:
                        st.warning("종료 시간은 시작 시간보다 늦어야 합니다.")
                    else:
                        success = update_record(
                            st.session_state.editing_record_id,
                            activity=activity_edit,
                            category=category_edit,
                            start_time=start_time_edit_str,
                            end_time=end_time_edit_str,
                            memo=memo_edit
                        )
                        if success:
                            st.success("기록이 수정되었습니다! ✨")
                        else:
                            st.error("기록 수정에 실패했습니다.")
                        st.session_state.editing_record_id = None
                        st.session_state.editing_record_data = None
                        st.rerun()
            else:
                st.warning("활동/루틴을 입력해주세요.")
    
    st.markdown("</div></div>", unsafe_allow_html=True)

# 기록 삭제 확인
if st.session_state.deleting_record_id:
    st.markdown("""
    <div class="center-content" style="background: #F7F9FA; min-height: 100vh;">
        <div class="record-form-container" style="max-width: 500px;">
    """, unsafe_allow_html=True)
    
    st.warning("⚠️ 기록을 삭제하시겠습니까?")
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_confirm, col_cancel_del = st.columns(2)
    
    with col_confirm:
        if st.button("삭제", use_container_width=True, key="confirm_delete", type="primary"):
            record_id_to_delete = st.session_state.deleting_record_id
            # 삭제 전에 상태 초기화
            st.session_state.deleting_record_id = None
            
            if delete_record(record_id_to_delete):
                st.success("✅ 기록이 삭제되었습니다!")
                # 삭제 후 즉시 화면 갱신
                st.rerun()
            else:
                st.error("❌ 삭제 중 오류가 발생했습니다.")
    
    with col_cancel_del:
        if st.button("취소", use_container_width=True, key="cancel_delete"):
            st.session_state.deleting_record_id = None
            st.rerun()
    
    st.markdown("</div></div>", unsafe_allow_html=True)

# 루틴 카테고리 기록 모달 창 (전체 페이지로 표시)
if st.session_state.show_category_modal and not st.session_state.editing_record_id and not st.session_state.deleting_record_id:
    # 선택한 날짜 표시
    record_date_display = ""
    if st.session_state.selected_record_date:
        record_date_display = f" ({st.session_state.selected_record_date.strftime('%Y년 %m월 %d일')})"
    
    # [수정 포인트] 시각화 화면과 동일한 '중앙 타이틀' 구조 적용
    st.markdown(f"""
    <div class="center-content">
        <h1 class="main-title" style="margin-bottom: 1rem;">📝 루틴 카테고리 기록</h1>
        <p class="subtitle" style="margin-bottom: 2rem;"></p>
        
    """, unsafe_allow_html=True)
    
    # 모달 내용
    with st.form("category_form", clear_on_submit=False):
        activity_input = st.text_input(
            "어떤 활동을 하고 싶으신가요? *",
            placeholder="예: 아침 명상, 운동, 독서, 요리 등",
            key="modal_activity"
        )
        
       
        
        # 카테고리 선택
        suggested_category = None
        if st.session_state.category_suggestion:
            suggested_category = st.session_state.category_suggestion.get('suggested_category', '기타')
        
        category_options = ["수면", "식사", "일과", "운동", "취미", "기타"]
        default_index = category_options.index(suggested_category) if suggested_category and suggested_category in category_options else 5
        
        category = st.selectbox(
            "카테고리 선택 *",
            category_options,
            index=default_index,
            key="modal_category"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            start_time_str = st.text_input("시작 시간 (HH:MM)", value=datetime.now().strftime("%H:%M"), key="modal_start_time", placeholder="예: 09:00")
        with col2:
            end_time_str = st.text_input("종료 시간 (HH:MM)", value=datetime.now().strftime("%H:%M"), key="modal_end_time", placeholder="예: 10:30")
        
        memo = st.text_area("메모 (선택)", placeholder="자유롭게 기록해주세요...", height=100, key="modal_memo")
        
        # 제출 버튼
        col_submit, col_cancel = st.columns([1, 1])
        with col_submit:
            submitted = st.form_submit_button("기록 저장", use_container_width=True)
        with col_cancel:
            cancel_clicked = st.form_submit_button("취소", use_container_width=True)
        
        if cancel_clicked:
            st.session_state.show_category_modal = False
            st.session_state.category_suggestion = None
            st.rerun()
        
        if submitted:
            if activity_input:
                # 시간 형식 검증
                time_format_valid = True
                start_time = None
                end_time = None
                
                try:
                    start_time = datetime.strptime(start_time_str, "%H:%M").time()
                except ValueError:
                    st.warning("시작 시간 형식이 올바르지 않습니다. HH:MM 형식으로 입력해주세요 (예: 09:00)")
                    time_format_valid = False
                
                try:
                    end_time = datetime.strptime(end_time_str, "%H:%M").time()
                except ValueError:
                    st.warning("종료 시간 형식이 올바르지 않습니다. HH:MM 형식으로 입력해주세요 (예: 10:30)")
                    time_format_valid = False
                
                if time_format_valid:
                    if start_time >= end_time:
                        st.warning("종료 시간은 시작 시간보다 늦어야 합니다.")
                    else:
                        # 선택한 날짜가 있으면 해당 날짜로 저장, 없으면 오늘 날짜로 저장
                        record_date = None
                        if st.session_state.selected_record_date:
                            record_date = st.session_state.selected_record_date.isoformat()
                        
                        add_record(activity_input, category, start_time_str, end_time_str, memo, record_date)
                        st.success("기록이 저장되었습니다! 🌱")
                        st.session_state.show_category_modal = False
                        st.session_state.show_records = True
                        st.session_state.category_suggestion = None
                        st.session_state.selected_record_date = None
                        st.rerun()
            else:
                st.warning("활동/루틴을 입력해주세요.")
    
    st.markdown("</div></div>", unsafe_allow_html=True)

# 도움말 아이콘 (항상 표시)
st.markdown("""
<div class="help-icon" style="cursor: pointer;" onclick="alert('도움말: 오늘의 기록을 추가하고 관리할 수 있습니다.')">?</div>
""", unsafe_allow_html=True)
