from numpy import number
import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="라이프챙김 - AI 루틴 비서",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 커스텀 CSS 스타일
st.markdown("""
<style>
    /* 전체 배경색 */
    .stApp {
        background: #F8F9FA;
    }
    
    /* 전체 본문 텍스트 색상 - 진한 녹색 계열 (#2d5a27) */
    p, span, div, label, .stMarkdown, .stText {
        color: #2d5a27 !important;
    }
    
    /* 메인 컨테이너 스타일 */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
    }
    
    /* 중앙 정렬 컨테이너 */
    .center-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        min-height: 80vh;
        width: 100%;
    }
    
    /* 타이틀 스타일 */
    .main-title {
        font-size: 3.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #2d5a27 0%, #1e4d2b 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .subtitle {
        font-size: 1.3rem;
        color: #2d5a27;
        text-align: center;
        margin-bottom: 3rem;
        font-weight: 500;
    }
    
    /* 버튼 컨테이너 */
    .button-container {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
        align-items: center;
        width: 100%;
        max-width: 400px;
    }
    
    /* 버튼 스타일 - 연두색 배경, 흰색 텍스트 */
    .stButton > button {
        width: 100%;
        max-width: 350px;
        background: #90EE90 !important;
        color: white !important;
        border: none;
        border-radius: 15px;
        padding: 1rem 2rem;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(144, 238, 144, 0.4);
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 25px rgba(144, 238, 144, 0.6);
        background: #7dd87d !important;
    }
    
    /* 로그인/회원가입 폼 스타일 */
    .auth-form {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 25px;
        padding: 3rem;
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
        max-width: 450px;
        width: 100%;
        margin: 0 auto;
    }
    
    /* 입력 필드 스타일 */
    .stTextInput > div > div > input {
        border-radius: 12px;
        border: 2px solid #e2e8f0;
        padding: 0.8rem;
        transition: all 0.3s ease;
        font-size: 1rem;
        color: #2d5a27;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #90EE90;
        box-shadow: 0 0 0 3px rgba(144, 238, 144, 0.1);
    }
    
    /* 입력 필드 라벨 색상 */
    .stTextInput label {
        color: #2d5a27 !important;
    }
    
    /* 푸터 숨기기 */
    footer {
        display: none;
    }
    
    /* 스크롤바 스타일 */
    ::-webkit-scrollbar {
        width: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #90EE90;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #7dd87d;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'show_login' not in st.session_state:
    st.session_state.show_login = False
if 'show_signup' not in st.session_state:
    st.session_state.show_signup = False

# 간단한 사용자 데이터 저장 (실제로는 데이터베이스 사용 권장)
if 'users' not in st.session_state:
    st.session_state.users = {}

def login_user(username, password):
    """사용자 로그인 처리"""
    if username in st.session_state.users:
        if st.session_state.users[username]['password'] == password:
            st.session_state.authenticated = True
            st.session_state.current_user = username
            st.session_state.show_login = False
            return True, "로그인 성공!"
        else:
            return False, "비밀번호가 일치하지 않습니다."
    else:
        return False, "존재하지 않는 사용자입니다."

def signup_user(username, password, email=""):
    """사용자 회원가입 처리"""
    if username in st.session_state.users:
        return False, "이미 존재하는 사용자명입니다."
    if len(username) < 3:
        return False, "사용자명은 3자 이상이어야 합니다."
    if len(password) < 4:
        return False, "비밀번호는 4자 이상이어야 합니다."
    
    st.session_state.users[username] = {
        'password': password,
        'email': email,
        'created_at': st.session_state.get('current_time', '')
    }
    return True, "회원가입이 완료되었습니다!"

# 메인 화면
if not st.session_state.authenticated:
    # 중앙 정렬을 위한 컨테이너
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # 타이틀
        st.markdown("""
        <div style='text-align: center; margin-bottom: 2rem;'>
            <h1 class="main-title">🌱 라이프챙김</h1>
            <p class="subtitle">AI 루틴 비서로 시작하는 초개인화 일상</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 로그인/회원가입 버튼 (초기 화면)
        if not st.session_state.show_login and not st.session_state.show_signup:
            st.markdown("""
            <div class="button-container">
            </div>
            """, unsafe_allow_html=True)
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("로그인", use_container_width=True, key="login_btn"):
                    st.session_state.show_login = True
                    st.session_state.show_signup = False
                    st.rerun()
            
            with col_btn2:
                if st.button("회원가입", use_container_width=True, key="signup_btn"):
                    st.session_state.show_signup = True
                    st.session_state.show_login = False
                    st.rerun()
        
        # 로그인 폼
        elif st.session_state.show_login:
            st.markdown("""
            <div class="auth-form">
                <h2 style='text-align: center; color: #2d5a27; margin-bottom: 2rem; font-size: 2rem;'>
                로그인</h2>
            </div>
            """, unsafe_allow_html=True)
            
            with st.form("login_form"):
                username = st.text_input("사용자명", placeholder="사용자명을 입력하세요")
                password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
                
                col_submit, col_back = st.columns([1, 1])
                with col_submit:
                    submitted = st.form_submit_button("로그인", use_container_width=True)
                with col_back:
                    if st.form_submit_button("뒤로가기", use_container_width=True):
                        st.session_state.show_login = False
                        st.rerun()
                
                if submitted:
                    if username and password:
                        success, message = login_user(username, password)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.warning("사용자명과 비밀번호를 모두 입력해주세요.")
        
        # 회원가입 폼
        elif st.session_state.show_signup:
            st.markdown("""
            <div class="auth-form">
                <h2 style='text-align: center; color: #2d5a27; margin-bottom: 2rem; font-size: 2rem;'>
                회원가입</h2>
            </div>
            """, unsafe_allow_html=True)
            
            with st.form("signup_form"):
                username = st.text_input("아이디", placeholder="3자 이상 입력하세요")
                password = st.text_input("비밀번호", type="password", placeholder="4자 이상 입력하세요")
                email = st.text_input("이메일 (선택)", placeholder="이메일을 입력하세요 (선택사항)")
                col_submit, col_back = st.columns([1, 1])
                with col_submit:
                    submitted = st.form_submit_button("회원가입", use_container_width=True)
                with col_back:
                    if st.form_submit_button("뒤로가기", use_container_width=True):
                        st.session_state.show_signup = False
                        st.rerun()
                
                if submitted:
                    if username and password:
                        success, message = signup_user(username, password, email)
                        if success:
                            st.success(message)
                            # 회원가입 후 자동 로그인
                            st.session_state.authenticated = True
                            st.session_state.current_user = username
                            st.session_state.show_signup = False
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.warning("사용자명과 비밀번호를 모두 입력해주세요.")

else:
    # 로그인 성공 후 메인 화면
    st.markdown(f"""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='font-size: 3rem; margin: 0; background: linear-gradient(135deg, #2d5a27 0%, #1e4d2b 100%); 
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;'>
        🌱 라이프챙김</h1>
        <p style='font-size: 1.2rem; color: #2d5a27; margin: 1rem 0; font-weight: 500;'>
        환영합니다, <strong>{st.session_state.current_user}</strong>님!</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("로그아웃", use_container_width=False):
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.rerun()
    
    st.info("메인 기능은 여기에 구현됩니다. (app.py의 기능을 통합할 예정)")
