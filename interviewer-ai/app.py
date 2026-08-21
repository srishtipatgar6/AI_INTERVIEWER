import os
import tempfile
import textwrap

import streamlit as st

from src.resume_parser import extract_resume_text
from src.rag import (
    build_resume_vectorstore,
    retrieve_resume_context,
)

from src.llm import (
    extract_candidate_profile,
    generate_first_question,
    generate_final_evaluation,
)

from src.graph import process_answer


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Adaptive AI Interviewer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    textwrap.dedent(
        """
        <style>

        /* =====================================================
           GLOBAL / DESIGN TOKENS
           ===================================================== */

        @import url(
            'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
        );

        :root {
            --bg:            #f4f6fb;
            --surface:        #ffffff;
            --surface-alt:    #f8f9fd;
            --border:         #e3e7f0;
            --border-strong:  #cdd3e3;

            --text:           #12172b;
            --text-muted:     #5b6275;
            --text-faint:     #8a90a3;

            --primary:        #4338ca;
            --primary-hover:  #3730a3;
            --primary-soft:   #eeecfd;
            --primary-border: #c7c2f7;

            --success:        #16794f;
            --success-soft:   #e7f7ef;
            --warning:        #b45309;
            --warning-soft:   #fef3e2;
            --danger:         #b91c1c;

            --shadow-sm: 0 1px 2px rgba(17, 24, 39, 0.04);
            --shadow-md: 0 4px 16px rgba(17, 24, 39, 0.06);
            --shadow-lg: 0 12px 32px rgba(67, 56, 202, 0.10);

            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 16px;
        }

        html,
        body,
        [class*="css"] {
            font-family: "Inter", -apple-system, sans-serif;
        }

        .stApp {
            background: var(--bg);
            color: var(--text);
        }

        /* =====================================================
           IMPORTANT STREAMLIT HEADER FIX
           ===================================================== */

        header {
            visibility: hidden !important;
            height: 0 !important;
        }

        [data-testid="stHeader"] {
            display: none !important;
            height: 0 !important;
        }

        [data-testid="stToolbar"] {
            display: none !important;
        }

        #MainMenu {
            visibility: hidden !important;
        }

        footer {
            visibility: hidden !important;
        }

        /* =====================================================
           MAIN CONTAINER
           ===================================================== */

        .block-container {
            max-width: 1180px;
            padding-top: 2rem !important;
            padding-bottom: 4rem !important;
        }

        /* =====================================================
           SIDEBAR
           ===================================================== */

        section[data-testid="stSidebar"] {
            background: #171b2e !important;
            border-right: 1px solid #262b45 !important;
        }

        section[data-testid="stSidebar"] > div {
            background: #171b2e !important;
        }

        section[data-testid="stSidebar"] * {
            color: #f1f2f9;
        }

        section[data-testid="stSidebar"] hr {
            border-color: #2a2f4a !important;
            margin-top: 1.2rem !important;
            margin-bottom: 1.2rem !important;
        }

        .sidebar-title {
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #8b91c9;
            margin-bottom: 1.4rem;
        }

        .sidebar-label {
            color: #6f76ab;
            font-size: 0.7rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            margin-top: 1rem;
            margin-bottom: 0.3rem;
        }

        .sidebar-value {
            color: #f1f2f9;
            font-size: 0.92rem;
            font-weight: 600;
            line-height: 1.5;
        }

        .sidebar-skill {
            color: #d7d9ee;
            font-size: 0.86rem;
            margin: 0.3rem 0;
        }

        /* =====================================================
           SIDEBAR BUTTON
           ===================================================== */

        section[data-testid="stSidebar"] .stButton > button {
            width: 100%;
            min-height: 42px;

            background: rgba(255, 255, 255, 0.04) !important;

            border: 1px solid #363c5c !important;

            border-radius: var(--radius-sm) !important;

            color: #f1f2f9 !important;

            font-weight: 600;

            box-shadow: none !important;
        }

        section[data-testid="stSidebar"] .stButton > button:hover {
            background: rgba(239, 68, 68, 0.12) !important;
            border-color: #b91c1c !important;
            color: #fecaca !important;
        }

        /* =====================================================
           HERO
           ===================================================== */

        .hero {
            text-align: center;
            margin: 0.6rem auto 2.4rem auto;
            max-width: 720px;
        }

        .hero-eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;

            padding: 0.3rem 0.8rem;
            margin-bottom: 1rem;

            border-radius: 999px;
            background: var(--primary-soft);
            border: 1px solid var(--primary-border);

            color: var(--primary);
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .hero-title {
            color: var(--text);
            font-size: 2.15rem;
            line-height: 1.2;
            font-weight: 800;
            letter-spacing: -0.03em;
            margin-bottom: 0.6rem;
        }

        .hero-subtitle {
            color: var(--text-muted);
            font-size: 0.95rem;
            line-height: 1.6;
        }

        .hero-title span {
            color: var(--primary);
        }

        .hero-compact {
            margin: 0 auto 1.4rem auto;
        }

        .hero-compact .hero-title {
            margin-bottom: 0;
        }

        /* =====================================================
           INTERVIEW QUESTION
           ===================================================== */

        .question-area {
            max-width: 760px;
            margin: 0 auto;
        }

        .question-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-md);
            padding: 1.4rem 1.5rem;
            margin-bottom: 1.2rem;
        }

        .question-row {
            display: flex;
            align-items: flex-start;
            gap: 0.9rem;
        }

        .robot-icon {
            width: 38px;
            height: 38px;

            min-width: 38px;

            border-radius: var(--radius-sm);

            display: flex;
            align-items: center;
            justify-content: center;

            background: var(--primary);
            box-shadow: 0 6px 16px rgba(67, 56, 202, 0.28);

            font-size: 1.1rem;
        }

        .question-text {
            color: var(--text);

            font-size: 1.05rem;

            line-height: 1.75;

            font-weight: 600;

            padding-top: 0.1rem;
        }

        /* =====================================================
           TOPIC BADGE
           ===================================================== */

        .topic-badge {
            display: inline-block;

            padding: 0.3rem 0.7rem;

            margin: 0 0.4rem 0.6rem 0;

            border-radius: 999px;

            background: var(--primary-soft);

            border: 1px solid var(--primary-border);

            color: var(--primary);

            font-size: 0.7rem;

            font-weight: 700;

            letter-spacing: 0.02em;
        }

        /* =====================================================
           STATUS
           ===================================================== */

        .status-card {
            max-width: 760px;

            margin: 0 auto 1.2rem auto;

            padding: 0.85rem 1.1rem;

            border-radius: var(--radius-md);

            background: var(--surface);

            border: 1px solid var(--border);

            box-shadow: var(--shadow-sm);

            display: flex;

            align-items: center;

            justify-content: space-between;
        }

        .status-title {
            color: var(--text);

            font-size: 0.86rem;

            font-weight: 700;
        }

        .status-subtitle {
            color: var(--text-faint);

            font-size: 0.74rem;

            margin-top: 0.15rem;
        }

        .status-pill {
            color: var(--success);

            background: var(--success-soft);

            border: 1px solid #b7e4cd;

            border-radius: 999px;

            padding: 0.32rem 0.65rem;

            font-size: 0.68rem;

            font-weight: 700;

            white-space: nowrap;
        }

        /* =====================================================
           CHAT HISTORY
           ===================================================== */

        [data-testid="stChatMessage"] {
            max-width: 760px;

            margin-left: auto;
            margin-right: auto;

            border-radius: var(--radius-md) !important;

            border: 1px solid var(--border);

            background: var(--surface);

            box-shadow: var(--shadow-sm);

            margin-bottom: 0.65rem;
        }

        [data-testid="stChatMessage"] p {
            color: var(--text) !important;

            line-height: 1.7;
        }

        /* =====================================================
           CHAT INPUT
           ===================================================== */

        [data-testid="stChatInput"] {
            max-width: 760px;

            margin-left: auto !important;
            margin-right: auto !important;

            margin-top: 1.4rem;
        }

        [data-testid="stChatInput"] > div {
            background: var(--surface) !important;

            border: 1px solid var(--border-strong) !important;

            border-radius: var(--radius-sm) !important;

            box-shadow: var(--shadow-sm) !important;
        }

        [data-testid="stChatInput"] textarea {
            background: var(--surface) !important;

            color: var(--text) !important;

            border: none !important;

            font-size: 0.9rem !important;
        }

        [data-testid="stChatInput"] textarea::placeholder {
            color: var(--text-faint) !important;
        }

        [data-testid="stChatInput"] textarea:focus {
            border: none !important;

            box-shadow: none !important;
        }

        /* =====================================================
           SETUP PAGE
           ===================================================== */

        .setup-wrapper {
            max-width: 800px;
            margin: 0 auto;
        }

        /* =====================================================
           ALL INPUTS
           ===================================================== */

        .stTextInput input,
        .stTextArea textarea {
            background: var(--surface-alt) !important;

            color: var(--text) !important;

            border: 1px solid var(--border-strong) !important;

            border-radius: var(--radius-sm) !important;
        }

        .stTextInput input:focus,
        .stTextArea textarea:focus {
            border-color: var(--primary) !important;

            box-shadow: 0 0 0 3px var(--primary-soft) !important;
        }

        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder {
            color: var(--text-faint) !important;
        }

        [data-baseweb="select"] > div {
            background: var(--surface-alt) !important;

            color: var(--text) !important;

            border: 1px solid var(--border-strong) !important;

            border-radius: var(--radius-sm) !important;
        }

        [data-baseweb="select"] span {
            color: var(--text) !important;
        }

        label,
        [data-testid="stWidgetLabel"] p {
            color: var(--text) !important;

            font-weight: 600 !important;
            font-size: 0.88rem !important;
        }

        [data-testid="stCaptionContainer"] {
            color: var(--text-muted) !important;
        }

        /* =====================================================
           FILE UPLOADER
           ===================================================== */

        [data-testid="stFileUploader"] {
            background: var(--surface-alt) !important;

            border: 1.5px dashed var(--border-strong) !important;

            border-radius: var(--radius-md) !important;
        }

        [data-testid="stFileUploaderDropzone"] {
            background: var(--surface-alt) !important;
        }

        [data-testid="stFileUploader"] * {
            color: var(--text-muted) !important;
        }

        [data-testid="stFileUploader"] section button {
            background: var(--surface) !important;
            border: 1px solid var(--border-strong) !important;
            color: var(--text) !important;
        }

        /* =====================================================
           BUTTONS
           ===================================================== */

        .stButton > button {
            min-height: 44px;

            border-radius: var(--radius-sm) !important;

            font-weight: 650 !important;

            border: 1px solid var(--border-strong) !important;

            background: var(--surface) !important;

            color: var(--text) !important;

            transition: all 0.15s ease;
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            border-color: var(--primary) !important;
            color: var(--primary) !important;
        }

        .stButton > button[kind="primary"] {
            background: var(--primary) !important;

            border: 1px solid var(--primary) !important;

            color: #ffffff !important;

            box-shadow: var(--shadow-lg);
        }

        .stButton > button[kind="primary"]:hover {
            background: var(--primary-hover) !important;
            border-color: var(--primary-hover) !important;
            color: #ffffff !important;
        }

        /* =====================================================
           CONTAINERS (setup cards, evaluation panels)
           ===================================================== */

        [data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--surface) !important;

            border: 1px solid var(--border) !important;

            border-radius: var(--radius-lg) !important;

            box-shadow: var(--shadow-sm);
        }

        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] h3,
        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] h4 {
            color: var(--text) !important;
            font-weight: 700 !important;
            margin-bottom: 0.6rem;
        }

        h3, h4 {
            color: var(--text) !important;
            letter-spacing: -0.01em;
        }

        /* =====================================================
           ALERTS
           ===================================================== */

        [data-testid="stAlert"] {
            border-radius: var(--radius-sm) !important;
            border: 1px solid var(--border) !important;
            box-shadow: var(--shadow-sm);
        }

        /* =====================================================
           PROGRESS
           ===================================================== */

        [data-testid="stProgressBar"] {
            margin-top: 0.4rem;
        }

        [data-testid="stProgressBar"] > div {
            background: var(--border) !important;

            border-radius: 999px !important;
        }

        [data-testid="stProgressBar"] > div > div {
            background: var(--primary) !important;
            border-radius: 999px !important;
        }

        /* =====================================================
           EVALUATION
           ===================================================== */

        .score-box {
            background: var(--surface);

            border: 1px solid var(--border);

            border-radius: var(--radius-lg);

            box-shadow: var(--shadow-md);

            padding: 1.8rem;

            text-align: center;

            min-height: 140px;
        }

        .score-number {
            color: var(--primary);

            font-size: 2.4rem;

            font-weight: 800;

            letter-spacing: -0.02em;

            margin-bottom: 0.35rem;
        }

        .score-label {
            color: var(--text-faint);

            font-size: 0.78rem;

            font-weight: 600;

            text-transform: uppercase;

            letter-spacing: 0.04em;
        }

        /* =====================================================
           EXPANDERS (question-by-question review)
           ===================================================== */

        [data-testid="stExpander"] {
            border: 1px solid var(--border) !important;
            border-radius: var(--radius-md) !important;
            background: var(--surface) !important;
            box-shadow: var(--shadow-sm);
            margin-bottom: 0.6rem;
        }

        [data-testid="stExpander"] summary {
            color: var(--text) !important;
            font-weight: 600 !important;
        }

        /* =====================================================
           MOBILE
           ===================================================== */

        @media (max-width: 768px) {

            .block-container {
                padding-left: 1rem !important;
                padding-right: 1rem !important;
                padding-top: 1rem !important;
            }

            .hero-title {
                font-size: 1.6rem;
            }

            .hero-subtitle {
                font-size: 0.85rem;
            }

            .question-text {
                font-size: 0.95rem;
            }

            .status-card {
                flex-direction: column;
                align-items: flex-start;
                gap: 0.5rem;
            }

        }

        </style>
        """
    ),
    unsafe_allow_html=True,
)


# ============================================================
# ROLES
# ============================================================

ROLES = [
    "Data Analyst",
    "Data Scientist",
    "Machine Learning Engineer",
    "AI Engineer",
    "AI/ML Engineer",
    "Software Engineer",
    "Backend Developer",
    "Frontend Developer",
    "Full Stack Developer",
    "Cloud Engineer",
    "DevOps Engineer",
    "Cybersecurity Analyst",
    "Business Analyst",
    "Product Manager",
    "Research Scientist",
    "QA Engineer",
    "UI/UX Designer",
    "Other",
]


# ============================================================
# SESSION STATE
# ============================================================

DEFAULTS = {
    "stage": "setup",
    "candidate_name": "",
    "selected_role": "Data Scientist",
    "custom_role": "",
    "skills": [],
    "certifications": [],
    "state": None,
    "messages": [],
    "question_number": 0,
    "final_evaluation": None,
    "resume_text": "",
    "profile": None,
    "vectorstore": None,
    "min_questions": 5,
    "max_questions": 10,
}


for key, value in DEFAULTS.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# HELPER: RESUME EXTRACTION
# ============================================================

def parse_uploaded_resume(uploaded_file):
    """
    Try the UploadedFile directly first.

    If the project's resume parser expects a filesystem path,
    temporarily save the uploaded file and try the path.
    """

    if uploaded_file is None:
        raise ValueError("No resume file was uploaded.")

    # --------------------------------------------------------
    # First attempt: Streamlit UploadedFile
    # --------------------------------------------------------

    try:

        result = extract_resume_text(uploaded_file)

        if result and str(result).strip():

            return str(result)

    except Exception as first_error:

        direct_error = first_error

    else:

        direct_error = None

    # --------------------------------------------------------
    # Second attempt: temporary filesystem path
    # --------------------------------------------------------

    suffix = os.path.splitext(
        uploaded_file.name
    )[1]

    temp_path = None

    try:

        file_bytes = uploaded_file.getvalue()

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp_file:

            temp_file.write(file_bytes)

            temp_path = temp_file.name

        result = extract_resume_text(temp_path)

        if result and str(result).strip():

            return str(result)

        raise ValueError(
            "The resume parser returned empty text."
        )

    except Exception as path_error:

        if direct_error is not None:

            raise RuntimeError(
                "Resume extraction failed using both "
                "the uploaded file and temporary file path.\n\n"
                f"Direct parser error: {direct_error}\n\n"
                f"Path parser error: {path_error}"
            )

        raise

    finally:

        if temp_path and os.path.exists(temp_path):

            try:
                os.remove(temp_path)
            except Exception:
                pass


# ============================================================
# HELPER: FINAL EVALUATION
# ============================================================

def finish_interview():

    state = st.session_state.state

    if not state:
        st.error("Interview state is missing.")
        return

    with st.spinner(
        "Preparing final assessment..."
    ):

        evaluation = generate_final_evaluation(

            candidate_name=state.get(
                "candidate_name",
                "",
            ),

            role=state.get(
                "role",
                "",
            ),

            skills=state.get(
                "skills",
                [],
            ),

            profile=state.get(
                "profile",
                {},
            ),

            history=state.get(
                "history",
                [],
            ),
        )

    st.session_state.final_evaluation = evaluation

    st.session_state.stage = "evaluation"

    st.rerun()


# ============================================================
# SETUP HERO
# ============================================================

if st.session_state.stage == "setup":

    st.markdown(
        textwrap.dedent(
            """
            <div class="hero">
                <div class="hero-eyebrow">🎯 Adaptive Interviewer</div>
                <div class="hero-title">AI-Powered Technical Interviews</div>
                <div class="hero-subtitle">
                    Resume-grounded interview questions that adapt to every
                    candidate's experience, powered by Groq + LangGraph + RAG.
                </div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


# ============================================================
# SETUP PAGE
# ============================================================

if st.session_state.stage == "setup":

    with st.container():

        st.markdown(
            '<div class="setup-wrapper">',
            unsafe_allow_html=True,
        )

        st.markdown(
            "### Candidate Setup"
        )

        st.caption(
            "Configure the interview and upload the candidate resume."
        )

        # ====================================================
        # CANDIDATE
        # ====================================================

        with st.container(border=True):

            st.markdown(
                "#### Candidate"
            )

            candidate_name = st.text_input(
                "Candidate name",
                value=st.session_state.candidate_name,
                placeholder="e.g. Srishti",
                key="candidate_name_input",
            )

            current_role = st.session_state.selected_role

            role_index = (
                ROLES.index(current_role)
                if current_role in ROLES
                else ROLES.index("Data Scientist")
            )

            selected_role = st.selectbox(
                "Target role",
                ROLES,
                index=role_index,
                key="role_select",
            )

            if selected_role == "Other":

                custom_role = st.text_input(
                    "Enter target role",
                    value=st.session_state.custom_role,
                    placeholder="e.g. Robotics Engineer",
                    key="custom_role_input",
                )

            else:

                custom_role = ""

        # ====================================================
        # SKILLS
        # ====================================================

        with st.container(border=True):

            st.markdown(
                "#### Skills"
            )

            st.caption(
                "Add the skills that should receive extra interview focus."
            )

            current_skills = st.text_input(
                "Skills",
                value=", ".join(
                    st.session_state.skills
                ),
                placeholder=(
                    "Python, SQL, Pandas, Machine Learning"
                ),
                key="skills_input",
            )

            skills = [
                item.strip()
                for item in current_skills.split(",")
                if item.strip()
            ]

            if skills:

                st.markdown(
                    " ".join(
                        [
                            f'<span class="topic-badge">{skill}</span>'
                            for skill in skills
                        ]
                    ),
                    unsafe_allow_html=True,
                )

        # ====================================================
        # CERTIFICATIONS
        # ====================================================

        with st.container(border=True):

            st.markdown(
                "#### Certifications"
            )

            certifications_text = st.text_input(
                "Certifications",
                value=", ".join(
                    st.session_state.certifications
                ),
                placeholder="AWS, Azure, Cisco...",
                key="certifications_input",
            )

            certifications = [
                item.strip()
                for item in certifications_text.split(",")
                if item.strip()
            ]

        # ====================================================
        # RESUME
        # ====================================================

        with st.container(border=True):

            st.markdown(
                "#### Resume"
            )

            st.caption(
                "Upload the resume used as the primary source for interview personalization."
            )

            uploaded_resume = st.file_uploader(
                "Upload candidate resume",
                type=[
                    "pdf",
                    "docx",
                    "txt",
                ],
                help="Supported formats: PDF, DOCX and TXT",
                key="resume_uploader",
            )

        # ====================================================
        # SETTINGS
        # ====================================================

        with st.container(border=True):

            st.markdown(
                "#### Interview Settings"
            )

            col1, col2 = st.columns(2)

            with col1:

                min_questions = st.slider(
                    "Minimum questions",
                    min_value=5,
                    max_value=12,
                    value=st.session_state.min_questions,
                    key="min_questions_slider",
                )

            with col2:

                current_max = max(
                    st.session_state.max_questions,
                    min_questions,
                )

                max_questions = st.slider(
                    "Maximum questions",
                    min_value=min_questions,
                    max_value=15,
                    value=min(
                        current_max,
                        15,
                    ),
                    key="max_questions_slider",
                )

            st.info(
                "Question difficulty adapts automatically based on the candidate's answers."
            )

        st.write("")

        # ====================================================
        # START BUTTON
        # ====================================================

        if st.button(
            "🚀 Start Interview",
            type="primary",
            use_container_width=True,
            key="start_interview_button",
        ):

            # ------------------------------------------------
            # VALIDATION
            # ------------------------------------------------

            clean_name = candidate_name.strip()

            actual_role = (
                custom_role.strip()
                if selected_role == "Other"
                else selected_role
            )

            if not clean_name:

                st.error(
                    "Please enter the candidate name."
                )

                st.stop()

            if not actual_role:

                st.error(
                    "Please select or enter a target role."
                )

                st.stop()

            if not skills:

                st.error(
                    "Please add at least one skill."
                )

                st.stop()

            if uploaded_resume is None:

                st.error(
                    "Please upload a candidate resume."
                )

                st.stop()

            # ------------------------------------------------
            # START PROCESS
            # ------------------------------------------------

            try:

                # ============================================
                # RESUME
                # ============================================

                with st.spinner(
                    "📄 Parsing candidate resume..."
                ):

                    resume_text = parse_uploaded_resume(
                        uploaded_resume
                    )

                if not resume_text.strip():

                    raise ValueError(
                        "No readable text was found in the uploaded resume."
                    )

                # ============================================
                # RAG
                # ============================================

                with st.spinner(
                    "🔎 Building resume knowledge base..."
                ):

                    vectorstore = (
                        build_resume_vectorstore(
                            resume_text
                        )
                    )

                if vectorstore is None:

                    raise RuntimeError(
                        "Resume vectorstore could not be created."
                    )

                # ============================================
                # PROFILE
                # ============================================

                with st.spinner(
                    "🧠 Understanding candidate experience..."
                ):

                    profile = (
                        extract_candidate_profile(
                            resume_text=resume_text,
                            role=actual_role,
                            declared_skills=skills,
                        )
                    )

                if profile is None:

                    profile = {}

                # ============================================
                # RESUME CONTEXT
                # ============================================

                with st.spinner(
                    "📚 Retrieving relevant resume context..."
                ):

                    first_context = (
                        retrieve_resume_context(
                            vectorstore,
                            (
                                f"{actual_role} "
                                f"{', '.join(skills)} "
                                "projects experience "
                                "technologies education"
                            ),
                            k=4,
                        )
                    )

                # ============================================
                # FIRST QUESTION
                # ============================================

                with st.spinner(
                    "🎯 Preparing your first interview question..."
                ):

                    first_question = (
                        generate_first_question(
                            role=actual_role,
                            skills=skills,
                            profile=profile,
                            resume_context=first_context,
                        )
                    )

                if not first_question:

                    raise RuntimeError(
                        "The LLM did not return a first question."
                    )

                question = str(
                    first_question.get(
                        "question",
                        "",
                    )
                ).strip()

                if not question:

                    raise RuntimeError(
                        "The generated first question is empty."
                    )

                # ============================================
                # INITIAL INTERVIEW STATE
                # ============================================

                interview_state = {

                    "candidate_name":
                        clean_name,

                    "role":
                        actual_role,

                    "skills":
                        skills,

                    "certifications":
                        certifications,

                    "profile":
                        profile,

                    "vectorstore":
                        vectorstore,

                    "resume_context":
                        first_context,

                    "question":
                        question,

                    "answer":
                        "",

                    "topic":
                        first_question.get(
                            "topic",
                            "",
                        ),

                    "skill":
                        first_question.get(
                            "skill",
                            "",
                        ),

                    "difficulty":
                        first_question.get(
                            "difficulty",
                            "easy",
                        ),

                    "history":
                        [],

                    "scores":
                        [],

                    "asked_questions":
                        [question],

                    "next_strategy":
                        "continue",

                    "finished":
                        False,

                    "min_questions":
                        int(min_questions),

                    "max_questions":
                        int(max_questions),
                }

                # ============================================
                # SAVE SESSION
                # ============================================

                st.session_state.candidate_name = clean_name

                st.session_state.selected_role = selected_role

                st.session_state.custom_role = custom_role

                st.session_state.skills = skills

                st.session_state.certifications = certifications

                st.session_state.resume_text = resume_text

                st.session_state.profile = profile

                st.session_state.vectorstore = vectorstore

                st.session_state.state = interview_state

                st.session_state.question_number = 1

                st.session_state.min_questions = int(
                    min_questions
                )

                st.session_state.max_questions = int(
                    max_questions
                )

                st.session_state.messages = [
                    {
                        "role": "assistant",
                        "content": question,
                    }
                ]

                # ============================================
                # MOVE TO INTERVIEW
                # ============================================

                st.session_state.stage = "interview"

                st.rerun()

            except Exception as exc:

                st.error(
                    "❌ Could not start the interview."
                )

                st.error(
                    f"{type(exc).__name__}: {exc}"
                )

                with st.expander(
                    "Technical error details"
                ):

                    st.exception(exc)

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


# ============================================================
# INTERVIEW PAGE
# ============================================================

elif st.session_state.stage == "interview":

    state = st.session_state.state

    if not state:

        st.error(
            "Interview state is missing. Please start a new interview."
        )

        if st.button(
            "Start New Interview",
            type="primary",
        ):

            st.session_state.clear()

            st.rerun()

        st.stop()

    # ========================================================
    # SIDEBAR
    # ========================================================

    with st.sidebar:

        st.markdown(
            '<div class="sidebar-title">Interview Progress</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="sidebar-label">Candidate:</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="sidebar-value">'
            f'{state.get("candidate_name", "N/A")}'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="sidebar-label">Role:</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="sidebar-value">'
            f'{state.get("role", "N/A")}'
            f'</div>',
            unsafe_allow_html=True,
        )

        history_count = len(
            state.get(
                "history",
                [],
            )
        )

        # First question is question 1.
        current_question_number = (
            history_count + 1
        )

        max_questions = int(
            state.get(
                "max_questions",
                10,
            )
        )

        st.markdown(
            '<div class="sidebar-label">Question:</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="sidebar-value">'
            f'{current_question_number} / {max_questions}'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.progress(
            min(
                current_question_number / max_questions,
                1.0,
            )
        )

        st.divider()

        st.markdown(
            '<div class="sidebar-label">Skills</div>',
            unsafe_allow_html=True,
        )

        for skill in state.get(
            "skills",
            [],
        ):

            st.markdown(
                f'<div class="sidebar-skill">• {skill}</div>',
                unsafe_allow_html=True,
            )

        certifications = state.get(
            "certifications",
            [],
        )

        if certifications:

            st.divider()

            st.markdown(
                '<div class="sidebar-label">Certifications</div>',
                unsafe_allow_html=True,
            )

            for cert in certifications:

                st.markdown(
                    f'<div class="sidebar-skill">• {cert}</div>',
                    unsafe_allow_html=True,
                )

        st.divider()

        st.caption(
            "Questions adapt using resume context, "
            "previous answers and difficulty."
        )

        st.divider()

        # ----------------------------------------------------
        # END INTERVIEW
        # ----------------------------------------------------

        if st.button(
            "⛔ End Interview",
            use_container_width=True,
            key="sidebar_end_interview",
        ):

            finish_interview()

    # ========================================================
    # MAIN HERO
    # ========================================================

    st.markdown(
        textwrap.dedent(
            """
            <div class="hero hero-compact">
                <div class="hero-eyebrow">🎯 Adaptive Interviewer</div>
                <div class="hero-title" style="font-size:1.5rem;">Interview in Progress</div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    # ========================================================
    # STATUS
    # ========================================================

    st.markdown(
        textwrap.dedent(
            f"""
            <div class="status-card">
                <div>
                    <div class="status-title">Technical Interview</div>
                    <div class="status-subtitle">
                        Question {current_question_number} of {max_questions}
                    </div>
                </div>
                <div class="status-pill">● Adaptive Mode</div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    # ========================================================
    # CURRENT QUESTION
    # ========================================================

    current_question = state.get(
        "question",
        "",
    )

    current_topic = state.get(
        "topic",
        "",
    )

    current_skill = state.get(
        "skill",
        "",
    )

    badge_html = ""

    if current_skill or current_topic:

        badge_text = " · ".join(
            [
                value
                for value in [
                    current_skill,
                    current_topic,
                ]
                if value
            ]
        )

        badge_html = (
            f'<span class="topic-badge">{badge_text}</span>'
        )

    # ========================================================
    # QUESTION
    # ========================================================

    st.markdown(
        textwrap.dedent(
            f"""
            <div class="question-area">
                <div class="question-card">
                    {badge_html}
                    <div class="question-row">
                        <div class="robot-icon">🤖</div>
                        <div class="question-text">{current_question}</div>
                    </div>
                </div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    # ========================================================
    # CHAT HISTORY
    # ========================================================

    # Do not display the first assistant question twice.
    # The current question is rendered above.
    displayed_first_question = False

    for message in st.session_state.messages:

        if (
            message["role"] == "assistant"
            and not displayed_first_question
            and message["content"] == current_question
        ):

            displayed_first_question = True

            continue

        with st.chat_message(
            message["role"]
        ):

            st.write(
                message["content"]
            )

    # ========================================================
    # ANSWER INPUT
    # ========================================================

    answer = st.chat_input(
        "Type your answer...",
        key="interview_chat_input",
    )

    if answer:

        answer = answer.strip()

        if not answer:

            st.stop()

        # ====================================================
        # END COMMAND
        # ====================================================

        if answer.lower() in {
            "end",
            "stop",
            "quit",
            "exit",
            "finish",
            "end interview",
            "finish interview",
        }:

            finish_interview()

        # ====================================================
        # USER MESSAGE
        # ====================================================

        st.session_state.messages.append(
            {
                "role": "user",
                "content": answer,
            }
        )

        # ====================================================
        # RAG CONTEXT
        # ====================================================

        query = (
            f"{state.get('topic', '')} "
            f"{state.get('skill', '')} "
            f"{answer}"
        )

        try:

            resume_context = (
                retrieve_resume_context(
                    state["vectorstore"],
                    query,
                    k=4,
                )
            )

        except Exception as exc:

            st.error(
                "Could not retrieve resume context."
            )

            st.exception(exc)

            st.stop()

        state["resume_context"] = resume_context

        state["answer"] = answer

        # ====================================================
        # LANGGRAPH
        # ====================================================

        with st.spinner(
            "🤖 Evaluating your answer..."
        ):

            try:

                result = process_answer(
                    state
                )

            except Exception as exc:

                st.error(
                    "❌ The interviewer encountered an error."
                )

                st.error(
                    f"{type(exc).__name__}: {exc}"
                )

                with st.expander(
                    "Technical error details"
                ):

                    st.exception(exc)

                st.stop()

        # ====================================================
        # VALIDATE RESULT
        # ====================================================

        if not isinstance(result, dict):

            st.error(
                "The interview graph returned an invalid state."
            )

            st.stop()

        st.session_state.state = result

        # ====================================================
        # ANSWERED QUESTION COUNT
        # ====================================================

        answered_count = len(
            result.get(
                "history",
                [],
            )
        )

        result_max_questions = int(
            result.get(
                "max_questions",
                state.get(
                    "max_questions",
                    10,
                ),
            )
        )

        # ====================================================
        # MAX QUESTIONS REACHED
        # ====================================================

        if answered_count >= result_max_questions:

            finish_interview()

        # ====================================================
        # GRAPH SAYS FINISHED
        # ====================================================

        if result.get(
            "finished",
            False,
        ):

            finish_interview()

        # ====================================================
        # NEXT QUESTION
        # ====================================================

        next_question = str(
            result.get(
                "question",
                "",
            )
        ).strip()

        if not next_question:

            st.error(
                "The interviewer did not generate the next question."
            )

            st.stop()

        # ====================================================
        # ADD NEXT QUESTION
        # ====================================================

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": next_question,
            }
        )

        st.session_state.question_number = (
            answered_count + 1
        )

        st.session_state.state = result

        st.rerun()


# ============================================================
# FINAL EVALUATION
# ============================================================

elif st.session_state.stage == "evaluation":

    evaluation = (
        st.session_state.final_evaluation
        or {}
    )

    state = (
        st.session_state.state
        or {}
    )

    # ========================================================
    # HERO
    # ========================================================

    st.markdown(
        textwrap.dedent(
            """
            <div class="hero">
                <div class="hero-eyebrow">✓ Interview Complete</div>
                <div class="hero-title">Candidate <span>Evaluation Report</span></div>
                <div class="hero-subtitle">
                    The adaptive technical interview has been completed.
                    Review the candidate's performance below.
                </div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    # ========================================================
    # CANDIDATE DETAILS
    # ========================================================

    with st.container(border=True):

        st.markdown(
            "### Candidate Details"
        )

        col1, col2 = st.columns(2)

        with col1:

            st.markdown(
                f"**Name**  \n"
                f"{state.get('candidate_name', 'N/A')}"
            )

            st.markdown(
                f"**Role**  \n"
                f"{state.get('role', 'N/A')}"
            )

        with col2:

            st.markdown(
                f"**Questions answered**  \n"
                f"{len(state.get('history', []))}"
            )

            st.markdown(
                f"**Skills**  \n"
                f"{', '.join(state.get('skills', []))}"
            )

    st.write("")

    # ========================================================
    # SCORE
    # ========================================================

    try:

        overall_score = float(
            evaluation.get(
                "overall_score",
                0,
            )
        )

    except Exception:

        overall_score = 0.0

    if overall_score <= 10:

        display_score = overall_score * 10

    else:

        display_score = overall_score

    recommendation = evaluation.get(
        "recommendation",
        "Not Available",
    )

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            textwrap.dedent(
                f"""
                <div class="score-box">
                    <div class="score-number">{display_score:.0f}/100</div>
                    <div class="score-label">Overall Interview Score</div>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    with col2:

        st.markdown(
            textwrap.dedent(
                f"""
                <div class="score-box">
                    <div class="score-number" style="font-size:1.8rem;">{recommendation}</div>
                    <div class="score-label">Final Recommendation</div>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    st.write("")

    # ========================================================
    # SUMMARY
    # ========================================================

    with st.container(border=True):

        st.markdown(
            "### Candidate Summary"
        )

        st.write(
            evaluation.get(
                "technical_assessment",
                evaluation.get(
                    "candidate_summary",
                    "No summary available.",
                ),
            )
        )

    # ========================================================
    # STRENGTHS / GAPS
    # ========================================================

    col1, col2 = st.columns(2)

    with col1:

        with st.container(border=True):

            st.markdown(
                "### Strengths"
            )

            strengths = evaluation.get(
                "strengths",
                evaluation.get(
                    "technical_strengths",
                    [],
                ),
            )

            if isinstance(
                strengths,
                str,
            ):

                strengths = [
                    strengths
                ]

            for item in strengths:

                st.write(
                    f"✓ {item}"
                )

    with col2:

        with st.container(border=True):

            st.markdown(
                "### Knowledge Gaps"
            )

            gaps = evaluation.get(
                "knowledge_gaps",
                evaluation.get(
                    "technical_gaps",
                    [],
                ),
            )

            if isinstance(
                gaps,
                str,
            ):

                gaps = [
                    gaps
                ]

            for item in gaps:

                st.write(
                    f"• {item}"
                )

    # ========================================================
    # SKILL ASSESSMENT
    # ========================================================

    st.write("")

    with st.container(border=True):

        st.markdown(
            "### Skill Assessment"
        )

        skill_assessments = evaluation.get(
            "skills_assessment",
            [],
        )

        for item in skill_assessments:

            if not isinstance(
                item,
                dict,
            ):

                continue

            skill = item.get(
                "skill",
                "Unknown",
            )

            try:

                score = float(
                    item.get(
                        "score",
                        0,
                    )
                )

            except Exception:

                score = 0.0

            remark = item.get(
                "remark",
                "",
            )

            st.markdown(
                f"**{skill}** · {score:g}/10"
            )

            st.progress(
                min(
                    max(
                        score / 10,
                        0,
                    ),
                    1,
                )
            )

            if remark:

                st.caption(
                    remark
                )

    # ========================================================
    # FINAL REMARKS
    # ========================================================

    with st.container(border=True):

        st.markdown(
            "### Interviewer Remarks"
        )

        st.info(
            evaluation.get(
                "final_remarks",
                "No remarks available.",
            )
        )

    # ========================================================
    # QUESTION EVALUATION
    # ========================================================

    st.markdown(
        "### Question-by-Question Evaluation"
    )

    history = state.get(
        "history",
        [],
    )

    if not history:

        st.info(
            "No question evaluations are available."
        )

    for index, item in enumerate(
        history,
        start=1,
    ):

        if not isinstance(
            item,
            dict,
        ):

            continue

        score = item.get(
            "score",
            0,
        )

        topic = item.get(
            "topic",
            "General",
        )

        difficulty = item.get(
            "difficulty",
            "medium",
        )

        with st.expander(
            f"Question {index} · {score}/10 · {topic}"
        ):

            st.caption(
                f"Difficulty: {difficulty}"
            )

            st.markdown(
                "**Question**"
            )

            st.write(
                item.get(
                    "question",
                    "",
                )
            )

            st.markdown(
                "**Candidate Answer**"
            )

            st.write(
                item.get(
                    "answer",
                    "",
                )
            )

            evaluation_item = item.get(
                "evaluation",
                {},
            )

            if not isinstance(
                evaluation_item,
                dict,
            ):

                evaluation_item = {}

            st.markdown(
                "**Assessment**"
            )

            st.write(
                evaluation_item.get(
                    "feedback",
                    "",
                )
            )

            if evaluation_item.get(
                "strength"
            ):

                st.success(
                    "✓ "
                    + str(
                        evaluation_item[
                            "strength"
                        ]
                    )
                )

            if evaluation_item.get(
                "gap"
            ):

                st.warning(
                    "• "
                    + str(
                        evaluation_item[
                            "gap"
                        ]
                    )
                )

    # ========================================================
    # NEW INTERVIEW
    # ========================================================

    st.divider()

    if st.button(
        "🚀 Start New Interview",
        type="primary",
        use_container_width=True,
        key="new_interview_button",
    ):

        st.session_state.clear()

        st.rerun()