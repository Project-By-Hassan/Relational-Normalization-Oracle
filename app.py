import streamlit as st
import normalization_engine as engine
import ai_assistant
import pandas as pd
import os
import requests

# Load local environment variables from .env if it exists
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    # Split by the first '=' to handle values that may contain '='
                    parts = line.strip().split('=', 1)
                    if len(parts) == 2:
                        key, val = parts
                        os.environ[key.strip()] = val.strip()

load_env()

# Page configurations
st.set_page_config(
    page_title="Academic Relational Normalization Validator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Light Theme (Premium grey/blue background, clean white cards, dark visible headings, purple accent)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

    /* Global Overrides */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #F8FAFC !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: #1E293B !important;
    }
    
    [data-testid="stHeader"] {
        background: transparent !important;
    }
    
    .main .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1300px !important;
    }
    
    /* Sidebar Overrides */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0 !important;
    }
    
    /* White Card Style with Shadow */
    .glass-card {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        margin-bottom: 1.5rem !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03) !important;
    }
    
    /* Primary buttons */
    div.stButton > button {
        background: linear-gradient(135deg, #6B21A8, #8B5CF6) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.8rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(107, 33, 168, 0.15) !important;
        width: 100% !important;
    }
    
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(139, 92, 246, 0.3) !important;
        border: none !important;
        color: #FFFFFF !important;
    }
    
    div.stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* Input Elements in Light Mode */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }
    
    /* High contrast text inputs on focus */
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #6B21A8 !important;
        box-shadow: 0 0 8px rgba(107, 33, 168, 0.2) !important;
    }
    
    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        color: #0F172A !important;
        font-weight: 700 !important;
    }
    
    /* Badges */
    .badge-pass {
        background-color: rgba(22, 163, 74, 0.1) !important;
        color: #16A34A !important;
        border: 1px solid rgba(22, 163, 74, 0.2) !important;
        padding: 4px 10px !important;
        border-radius: 6px !important;
        font-size: 0.85rem !important;
        font-weight: 700 !important;
        display: inline-block !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .badge-fail {
        background-color: rgba(220, 38, 38, 0.1) !important;
        color: #DC2626 !important;
        border: 1px solid rgba(220, 38, 38, 0.2) !important;
        padding: 4px 10px !important;
        border-radius: 6px !important;
        font-size: 0.85rem !important;
        font-weight: 700 !important;
        display: inline-block !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .badge-info {
        background-color: rgba(107, 33, 168, 0.08) !important;
        color: #6B21A8 !important;
        border: 1px solid rgba(107, 33, 168, 0.2) !important;
        padding: 4px 10px !important;
        border-radius: 6px !important;
        font-size: 0.85rem !important;
        font-weight: 700 !important;
        display: inline-block;
    }

    .badge-neutral {
        background-color: #F1F5F9 !important;
        color: #64748B !important;
        border: 1px solid #E2E8F0 !important;
        padding: 4px 10px !important;
        border-radius: 6px !important;
        font-size: 0.85rem !important;
        font-weight: 700 !important;
        display: inline-block !important;
    }

    .muted-text {
        color: #475569 !important;
        font-size: 0.95rem;
    }
    
    code {
        color: #6B21A8 !important;
        background-color: #F1F5F9 !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        font-weight: 500 !important;
    }

    /* ---- Dark-mode safety net ----
       Streamlit renders some components (dropdown popovers, alerts, expanders,
       chat, file uploader) using its own theme engine. On devices set to a
       system/browser dark mode, these can end up with light text on light
       backgrounds (or vice versa) unless explicitly pinned below. */

    /* Labels above inputs */
    label p, .stTextInput label p, .stTextArea label p, .stSelectbox label p,
    .stFileUploader label p, .stCheckbox label p {
        color: #334155 !important;
    }

    /* Placeholder text */
    ::placeholder {
        color: #94A3B8 !important;
        opacity: 1 !important;
    }

    /* Selectbox closed value */
    .stSelectbox div[data-baseweb="select"] * {
        color: #0F172A !important;
    }

    /* Selectbox/dropdown popover menu (rendered in a portal outside the card) */
    div[data-baseweb="popover"] ul[data-baseweb="menu"],
    div[data-baseweb="popover"] div[role="listbox"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
    }
    div[data-baseweb="popover"] li[role="option"],
    div[data-baseweb="popover"] li {
        color: #0F172A !important;
        background-color: #FFFFFF !important;
    }
    div[data-baseweb="popover"] li[role="option"]:hover,
    div[data-baseweb="popover"] li:hover {
        background-color: #F1F5F9 !important;
    }

    /* Alerts: st.error / st.warning / st.info / st.success */
    [data-testid="stAlert"] {
        background-color: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
    }
    [data-testid="stAlert"] p, [data-testid="stAlert"] span, [data-testid="stAlert"] div {
        color: #0F172A !important;
    }

    /* Expanders (1NF-5NF checks, chase matrix, etc.) */
    [data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
    }
    [data-testid="stExpander"] summary, [data-testid="stExpander"] summary p {
        color: #0F172A !important;
        background-color: #FFFFFF !important;
    }

    /* Tabs (3NF / BCNF decomposition) */
    [data-baseweb="tab-list"] {
        background-color: transparent !important;
        border-bottom: 1px solid #E2E8F0 !important;
    }
    [data-baseweb="tab"] {
        color: #64748B !important;
    }
    [data-baseweb="tab"] p {
        color: inherit !important;
    }
    [data-baseweb="tab"][aria-selected="true"] {
        color: #6B21A8 !important;
    }

    /* Chat messages and chat input */
    [data-testid="stChatMessage"] {
        background-color: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
    }
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li, [data-testid="stChatMessage"] span {
        color: #0F172A !important;
    }
    [data-testid="stChatInput"] textarea {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
    }

    /* File uploader dropzone */
    [data-testid="stFileUploaderDropzone"] {
        background-color: #FFFFFF !important;
        border: 1px dashed #CBD5E1 !important;
    }
    [data-testid="stFileUploaderDropzone"] * {
        color: #475569 !important;
    }
    [data-testid="stFileUploaderDropzone"] button {
        color: #6B21A8 !important;
        background-color: #F1F5F9 !important;
    }

    /* Generic markdown text (falls back safely instead of inheriting a dark-mode white) */
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] span {
        color: inherit;
    }

    /* Dataframe / table rendering (mined FD preview, etc.) */
    [data-testid="stDataFrame"], [data-testid="stTable"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
    }

    /* ---- Sidebar reopen / collapse arrow: make it always clearly visible ---- */
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stSidebarCollapseButton"],
    button[kind="header"] {
        background-color: #6B21A8 !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 10px rgba(107, 33, 168, 0.35) !important;
        opacity: 1 !important;
        visibility: visible !important;
        z-index: 999999 !important;
    }
    [data-testid="collapsedControl"] svg,
    [data-testid="stSidebarCollapsedControl"] svg,
    [data-testid="stSidebarCollapseButton"] svg,
    button[kind="header"] svg {
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
    }
    [data-testid="collapsedControl"]:hover,
    [data-testid="stSidebarCollapsedControl"]:hover {
        background-color: #8B5CF6 !important;
    }

    /* App title: keeps a strong desktop size but shrinks on small screens so it
       doesn't overflow or look oversized on mobile. */
    .app-title {
        font-size: 2.1rem !important;
        line-height: 1.25 !important;
    }
    @media (max-width: 768px) {
        .app-title {
            font-size: 1.35rem !important;
            line-height: 1.3 !important;
        }
        h2 {
            font-size: 1.25rem !important;
        }
        h3 {
            font-size: 1.05rem !important;
        }
        .main .block-container {
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Header Section
st.markdown(
    """
    <div style="margin-bottom: 2rem;">
        <h1 class="app-title" style="font-weight: 800; color: #0F172A; margin-bottom: 0.2rem;">
            ⚡ Relational Normalization Oracle
        </h1>
        <p class="muted-text">
            An advanced step-by-step academic validator checks for relational databases from 1NF to 5NF, featuring CSV/Excel dataset FD mining and an integrated Groq AI assistant.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Preset configs
presets = {
    "1. Student Enrollment (2NF Violation)": {
        "attributes": "StudentID, StudentName, CourseID, CourseName, Grade",
        "fds": "StudentID -> StudentName\nCourseID -> CourseName\nStudentID, CourseID -> Grade",
        "mvds": "",
        "jds": "",
        "1nf_check": True,
        "description": "StudentName depends partially on StudentID, and CourseName depends partially on CourseID. This violates 2NF because non-prime attributes are determined by a subset of a candidate key."
    },
    "2. Employee Department (3NF Violation)": {
        "attributes": "EmployeeID, EmployeeName, DepartmentID, DepartmentName",
        "fds": "EmployeeID -> EmployeeName\nEmployeeID -> DepartmentID\nDepartmentID -> DepartmentName",
        "mvds": "",
        "jds": "",
        "1nf_check": True,
        "description": "DepartmentName transitively depends on EmployeeID through DepartmentID. This violates 3NF because DepartmentID -> DepartmentName has a non-superkey LHS and a non-prime RHS."
    },
    "3. Book Store (BCNF Violation)": {
        "attributes": "BookTitle, Author, Publisher",
        "fds": "BookTitle, Author -> Publisher\nPublisher -> Author",
        "mvds": "",
        "jds": "",
        "1nf_check": True,
        "description": "The candidate keys are {BookTitle, Author} and {BookTitle, Publisher}. The FD Publisher -> Author violates BCNF because Publisher is not a superkey, although Author is prime (satisfies 3NF)."
    },
    "4. Course Teacher Textbook (4NF Violation)": {
        "attributes": "Course, Teacher, Textbook",
        "fds": "",
        "mvds": "Course ->-> Teacher\nCourse ->-> Textbook",
        "jds": "",
        "1nf_check": True,
        "description": "Teachers and Textbooks are independent of each other. Candidate key is {Course, Teacher, Textbook}. The MVDs violate 4NF because Course is not a superkey."
    },
    "5. Supplier Part Project (5NF Violation)": {
        "attributes": "Supplier, Part, Project",
        "fds": "",
        "mvds": "",
        "jds": "Join(Supplier Part, Part Project, Supplier Project)",
        "1nf_check": True,
        "description": "If a supplier supplies a part, that part is used in a project, and the supplier supplies to that project, then the supplier must supply that part to that project. Violates 5NF unless components SP, PJ, SJ are superkeys."
    },
    "6. Custom Canvas": {
        "attributes": "A, B, C, D, E",
        "fds": "A -> B, C\nC -> D\nB -> E",
        "mvds": "",
        "jds": "",
        "1nf_check": True,
        "description": "Build your own custom relation."
    }
}

# Session state initialization for inputs
if "input_attrs" not in st.session_state:
    st.session_state.input_attrs = presets["6. Custom Canvas"]["attributes"]
    st.session_state.input_fds = presets["6. Custom Canvas"]["fds"]
    st.session_state.input_mvds = presets["6. Custom Canvas"]["mvds"]
    st.session_state.input_jds = presets["6. Custom Canvas"]["jds"]
    st.session_state.input_1nf = presets["6. Custom Canvas"]["1nf_check"]
    st.session_state.prev_preset = "6. Custom Canvas"

# Sidebar configuration
with st.sidebar:
    st.markdown("<h3 style='margin-top:0; font-weight:600;'>Configure Canvas</h3>", unsafe_allow_html=True)
    
    preset_choice = st.selectbox(
        "Load Preset Templates",
        options=list(presets.keys()),
        index=list(presets.keys()).index(st.session_state.prev_preset)
    )
    
    if preset_choice != st.session_state.prev_preset:
        st.session_state.prev_preset = preset_choice
        st.session_state.input_attrs = presets[preset_choice]["attributes"]
        st.session_state.input_fds = presets[preset_choice]["fds"]
        st.session_state.input_mvds = presets[preset_choice]["mvds"]
        st.session_state.input_jds = presets[preset_choice]["jds"]
        st.session_state.input_1nf = presets[preset_choice]["1nf_check"]
        st.rerun()
        
    st.markdown("<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 1.5rem 0;' />", unsafe_allow_html=True)
    
    # Dataset File Uploader (CSV & Excel)
    st.markdown("<h4 style='font-weight:600;'>Upload Dataset</h4>", unsafe_allow_html=True)
    st.markdown("<p class='muted-text' style='font-size:0.8rem; margin-bottom: 8px;'>Upload a CSV or Excel table to automatically mine columns and functional dependencies.</p>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Choose CSV/Excel", type=["csv", "xlsx", "xls"])
    
    if uploaded_file is not None:
        file_id = f"{uploaded_file.name}_{uploaded_file.size}"
        if "last_file_id" not in st.session_state or st.session_state.last_file_id != file_id:
            st.session_state.last_file_id = file_id
            try:
                # Read dataset
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                    
                if len(df) > 0:
                    # Extract columns
                    cols = ", ".join(df.columns)
                    st.session_state.input_attrs = cols
                    
                    # Mine FDs
                    mined = engine.discover_fds_from_dataframe(df, max_lhs_size=2)
                    fd_strings = []
                    for fd in mined:
                        lhs_str = ", ".join(sorted(list(fd["lhs"])))
                        rhs_str = ", ".join(sorted(list(fd["rhs"])))
                        fd_strings.append(f"{lhs_str} -> {rhs_str}")
                    st.session_state.input_fds = "\n".join(fd_strings)
                    st.session_state.input_mvds = ""
                    st.session_state.input_jds = ""
                    st.session_state.input_1nf = True
                    st.session_state.prev_preset = "6. Custom Canvas"
                    
                    # Clear chat history on dataset update
                    if "chat_messages" in st.session_state:
                        st.session_state.chat_messages = []
                        
                    st.success(f"Discovered {len(mined)} FDs from {uploaded_file.name}!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error parsing dataset: {str(e)}")

    st.markdown("<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 1.5rem 0;' />", unsafe_allow_html=True)

    # AI-Powered Problem Uploader (Image & PDF)
    st.markdown("<h4 style='font-weight:600;'>📸 Upload Problem (Image / PDF)</h4>", unsafe_allow_html=True)
    st.markdown(
        "<p class='muted-text' style='font-size:0.8rem; margin-bottom: 8px;'>"
        "Upload a photo, screenshot, or PDF of a normalization question (textbook, "
        "handwritten notes, whiteboard). The AI will read it and auto-fill the canvas."
        "</p>",
        unsafe_allow_html=True
    )

    problem_file = st.file_uploader(
        "Choose Image (PNG/JPG) or PDF",
        type=["png", "jpg", "jpeg", "pdf"],
        key="problem_file_uploader"
    )

    if problem_file is not None:
        problem_file_id = f"{problem_file.name}_{problem_file.size}"
        if "last_problem_file_id" not in st.session_state or st.session_state.last_problem_file_id != problem_file_id:
            # Mark as processed immediately (even before we know the outcome) so a
            # failure doesn't cause a silent, repeated retry loop on every rerun.
            st.session_state.last_problem_file_id = problem_file_id
            st.session_state.problem_extraction_status = None

            api_key_for_extraction = os.getenv("GROQ_API_KEY")
            if not api_key_for_extraction:
                st.session_state.problem_extraction_status = {
                    "type": "error",
                    "msg": "⚠️ Groq API Key is missing. Add `GROQ_API_KEY=...` to your `.env` file in the project root and restart the app."
                }
            else:
                with st.spinner("Reading problem and extracting schema..."):
                    try:
                        file_bytes = problem_file.getvalue()
                        if not file_bytes:
                            raise ai_assistant.ExtractionError("The uploaded file appears to be empty.")

                        if problem_file.name.lower().endswith(".pdf"):
                            extracted = ai_assistant.extract_schema_from_pdf_bytes(file_bytes, api_key_for_extraction)
                        else:
                            ext = problem_file.name.lower().rsplit(".", 1)[-1]
                            mime_type = "image/png" if ext == "png" else "image/jpeg"
                            extracted = ai_assistant.extract_schema_from_image_bytes(file_bytes, mime_type, api_key_for_extraction)

                        if not extracted.get("attributes"):
                            st.session_state.problem_extraction_status = {
                                "type": "warning",
                                "msg": f"Couldn't confidently identify a schema in this file. AI note: {extracted.get('summary', 'No details.')}"
                            }
                        else:
                            st.session_state.input_attrs = extracted.get("attributes", "")
                            st.session_state.input_fds = extracted.get("fds", "")
                            st.session_state.input_mvds = extracted.get("mvds", "")
                            st.session_state.input_jds = extracted.get("jds", "")
                            st.session_state.input_1nf = True
                            st.session_state.prev_preset = "6. Custom Canvas"

                            if "chat_messages" in st.session_state:
                                st.session_state.chat_messages = []

                            st.session_state.problem_extraction_status = {
                                "type": "success",
                                "msg": f"✅ Extracted schema: {extracted.get('summary', 'Canvas updated.')}"
                            }
                    except ai_assistant.ExtractionError as e:
                        st.session_state.problem_extraction_status = {"type": "error", "msg": f"❌ {str(e)}"}
                    except Exception as e:
                        st.session_state.problem_extraction_status = {
                            "type": "error",
                            "msg": f"❌ Unexpected error while processing file: `{type(e).__name__}: {str(e)}`"
                        }
            st.rerun()

    # Persist the outcome of the last extraction attempt across reruns so it
    # doesn't flash and disappear before the user can read it.
    status = st.session_state.get("problem_extraction_status")
    if status:
        if status["type"] == "success":
            st.success(status["msg"])
        elif status["type"] == "warning":
            st.warning(status["msg"])
        else:
            st.error(status["msg"])


    st.markdown("<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 1.5rem 0;' />", unsafe_allow_html=True)
    st.markdown(f"<p class='muted-text'><b>Preset Description:</b><br/>{presets[preset_choice]['description']}</p>", unsafe_allow_html=True)
    
    st.markdown("<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 1.5rem 0;' />", unsafe_allow_html=True)
    st.markdown(
        """
        <div style='background-color: #F8FAFC; padding: 1rem; border-radius: 8px; border: 1px solid #E2E8F0;'>
            <h5 style='color: #6B21A8; margin: 0 0 0.5rem 0;'>Syntax Guide</h5>
            <span class='muted-text' style='font-size: 0.8rem;'>
                <b>FDs:</b> <code>A -> B</code> or <code>A, B -> C</code><br/>
                <b>MVDs:</b> <code>A ->-> B</code> or <code>A --> B</code><br/>
                <b>JDs:</b> <code>Join(AB, BC, AC)</code>
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

# Layout division: Left Panel (Inputs) & Right Panel (Results)
col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin-top:0; font-weight:600;'>Relation Inputs</h3>", unsafe_allow_html=True)
    
    attrs_input = st.text_input(
        "Attributes (R)",
        value=st.session_state.input_attrs,
        placeholder="e.g., StudentID, StudentName, CourseID"
    )
    
    fds_input = st.text_area(
        "Functional Dependencies (FDs)",
        value=st.session_state.input_fds,
        placeholder="e.g., StudentID -> StudentName\nCourseID -> CourseName",
        height=120
    )
    
    mvd_input = st.text_area(
        "Multi-valued Dependencies (MVDs) [Optional]",
        value=st.session_state.input_mvds,
        placeholder="e.g., Course ->-> Teacher\nCourse ->-> Textbook",
        height=70
    )
    
    jd_input = st.text_area(
        "Join Dependencies (JDs) [Optional]",
        value=st.session_state.input_jds,
        placeholder="e.g., Join(AB, BC, AC)",
        height=70
    )
    
    is_atomic = st.checkbox(
        "Are all attribute domains atomic? (Breaks 1NF if unchecked)",
        value=st.session_state.input_1nf
    )
    
    st.markdown("</div>", unsafe_allow_html=True)

    # Parsing inputs
    R = engine.parse_attributes(attrs_input)
    fds = engine.parse_fds(fds_input, R)
    mvds = engine.parse_mvds(mvd_input, R)
    jds = engine.parse_jds(jd_input, R)
    
    if not R:
        st.warning("Please enter at least one attribute to begin validation.")
        st.stop()

    unknown_attrs = engine.find_unknown_attributes(R, fds, mvds, jds)
    if unknown_attrs:
        st.error(
            f"⚠️ These attributes appear in your FDs/MVDs/JDs but are NOT listed in "
            f"**Attributes (R)**: `{sorted(list(unknown_attrs))}`. "
            f"Add them to R above, or fix the typo, then try again."
        )
        st.stop()

    # Closure Simulator
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin-top:0; font-weight:600;'>Closure Simulator</h3>", unsafe_allow_html=True)
    st.markdown("<p class='muted-text' style='font-size:0.85rem;'>Select attributes to calculate their closure under current FDs.</p>", unsafe_allow_html=True)
    
    sim_attrs_input = st.text_input(
        "Attributes for Closure Check",
        value="",
        placeholder=f"e.g., {sorted(list(R))[0] if R else 'A'}"
    )
    
    if sim_attrs_input:
        sim_attrs = engine.parse_attributes(sim_attrs_input, R)
        invalid_attrs = sim_attrs - R
        if invalid_attrs:
            st.error(f"Attributes {sorted(list(invalid_attrs))} are not in relation R.")
        else:
            closure = engine.compute_closure(sim_attrs, fds)
            st.markdown(
                f"""
                <div style='background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 0.8rem; border-radius: 8px;'>
                    <b>{sorted(list(sim_attrs)) if sim_attrs else '{}'}<sup>+</sup></b> = <code>{sorted(list(closure))}</code>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Closure steps
            steps = []
            curr_closure = set(sim_attrs)
            steps.append(set(curr_closure))
            while True:
                added = False
                for fd in fds:
                    if fd["lhs"].issubset(curr_closure):
                        new_elements = fd["rhs"] - curr_closure
                        if new_elements:
                            curr_closure.update(new_elements)
                            steps.append(set(curr_closure))
                            added = True
                if not added:
                    break
            if len(steps) > 1:
                st.markdown("<span style='font-size:0.85rem; color:#64748B;'>Derivation steps:</span>", unsafe_allow_html=True)
                for idx, step in enumerate(steps):
                    st.markdown(f"<span style='font-size:0.8rem; color:#64748B;'>Step {idx+1}: <code>{sorted(list(step))}</code></span>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# Math Normalization Logic Calculations
candidate_keys = engine.find_candidate_keys(R, fds)
prime_attrs = set()
for key in candidate_keys:
    prime_attrs.update(key)
non_prime_attrs = R - prime_attrs

is_1nf = is_atomic
viol_1nf = "Domain contains composite/multi-valued attributes." if not is_atomic else ""

is_2nf, viol_2nf = (True, []) if not is_1nf else engine.check_2nf(R, fds, candidate_keys, non_prime_attrs)
is_3nf, viol_3nf = (True, []) if not is_2nf else engine.check_3nf(R, fds, candidate_keys, prime_attrs)
is_bcnf, viol_bcnf = (True, []) if not is_3nf else engine.check_bcnf(R, fds, candidate_keys)
is_4nf, viol_4nf = (True, []) if not is_bcnf else engine.check_4nf(R, mvds, fds, candidate_keys)
is_5nf, viol_5nf = (True, []) if not is_4nf else engine.check_5nf(R, jds, fds, candidate_keys)

# Highest Normal Form String
highest_nf = "UNNORMALIZED"
if is_1nf:
    highest_nf = "1NF"
    if is_2nf:
        highest_nf = "2NF"
        if is_3nf:
            highest_nf = "3NF"
            if is_bcnf:
                highest_nf = "BCNF"
                if is_4nf:
                    highest_nf = "4NF"
                    if is_5nf:
                        highest_nf = "5NF"

with col_right:
    # Summary Card
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin-top:0; font-weight:600;'>Relation Analysis Summary</h3>", unsafe_allow_html=True)
    
    summary_cols = st.columns([1, 1])
    with summary_cols[0]:
        st.markdown(
            f"""
            <div style='background: rgba(107, 33, 168, 0.05); border: 1px solid rgba(107, 33, 168, 0.15); padding: 1rem; border-radius: 8px; text-align: center; height: 100%;'>
                <span class='muted-text' style='font-size: 0.85rem; font-weight: 600; text-transform:uppercase;'>HIGHEST NORMAL FORM</span><br/>
                <span style='font-size: 2.2rem; font-weight: 800; color: #6B21A8;'>{highest_nf}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    with summary_cols[1]:
        keys_html = "".join([f"<span class='badge-info' style='margin-right: 5px; margin-bottom: 5px;'>{sorted(list(k))}</span>" for k in candidate_keys])
        st.markdown(
            f"""
            <div style='background: #F8FAFC; border: 1px solid #E2E8F0; padding: 0.8rem; border-radius: 8px; height: 100%;'>
                <span style='font-size: 0.85rem; color:#475569;'><b>Relation:</b> R({", ".join(sorted(list(R)))})</span><br/>
                <span style='font-size: 0.85rem; color:#475569;'><b>Candidate Keys:</b></span><br/>
                <div style='margin-top: 4px;'>{keys_html}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    st.markdown(
        f"""
        <div style='margin-top: 1rem; font-size: 0.85rem;'>
            <span class='muted-text'><b>Prime Attributes:</b> <code>{sorted(list(prime_attrs))}</code></span><br/>
            <span class='muted-text'><b>Non-Prime Attributes:</b> <code>{sorted(list(non_prime_attrs))}</code></span>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # Step-by-Step Normalization Trace
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin-top:0; font-weight:600;'>Normalization Checks (1NF - 5NF)</h3>", unsafe_allow_html=True)
    
    # 1NF
    with st.expander(f"1NF: First Normal Form — {'PASSED' if is_1nf else 'VIOLATED'}", expanded=not is_1nf):
        if is_1nf:
            st.markdown("<span class='badge-pass'>PASSED</span> &nbsp;&nbsp;All attributes contain atomic values.", unsafe_allow_html=True)
        else:
            st.markdown("<span class='badge-fail'>VIOLATED</span> &nbsp;&nbsp;Domains are not atomic.", unsafe_allow_html=True)
            st.error(viol_1nf)
            
    # 2NF
    with st.expander(f"2NF: Second Normal Form — {'PASSED' if is_2nf else 'VIOLATED'}", expanded=(is_1nf and not is_2nf)):
        if not is_1nf:
            st.markdown("<span class='badge-neutral'>BLOCKED</span> &nbsp;&nbsp;Blocked by 1NF violation.", unsafe_allow_html=True)
        elif is_2nf:
            st.markdown("<span class='badge-pass'>PASSED</span> &nbsp;&nbsp;No partial dependencies exist. All non-prime attributes depend on full candidate keys.", unsafe_allow_html=True)
        else:
            st.markdown("<span class='badge-fail'>VIOLATED</span> &nbsp;&nbsp;Found partial dependencies:", unsafe_allow_html=True)
            for viol in viol_2nf:
                st.markdown(
                    f"- Proper subset `{sorted(list(viol['subset']))}` of Candidate Key `{sorted(list(viol['key']))}` determines non-prime attribute `{viol['target']}`."
                )
                
    # 3NF
    with st.expander(f"3NF: Third Normal Form — {'PASSED' if is_3nf else 'VIOLATED'}", expanded=(is_2nf and not is_3nf)):
        if not is_2nf:
            st.markdown("<span class='badge-neutral'>BLOCKED</span> &nbsp;&nbsp;Blocked by 2NF violation.", unsafe_allow_html=True)
        elif is_3nf:
            st.markdown("<span class='badge-pass'>PASSED</span> &nbsp;&nbsp;No transitive dependencies. For all non-trivial FDs $X \\rightarrow Y$, either $X$ is a superkey or $Y \\setminus X$ is prime.", unsafe_allow_html=True)
        else:
            st.markdown("<span class='badge-fail'>VIOLATED</span> &nbsp;&nbsp;Found transitive dependencies:", unsafe_allow_html=True)
            for viol in viol_3nf:
                fd = viol["fd"]
                st.markdown(
                    f"- FD `{sorted(list(fd['lhs']))} -> {sorted(list(fd['rhs']))}` violates 3NF because LHS is not a superkey and RHS has non-prime attributes `{sorted(list(viol['violators']))}`."
                )
                
    # BCNF
    with st.expander(f"BCNF: Boyce-Codd Normal Form — {'PASSED' if is_bcnf else 'VIOLATED'}", expanded=(is_3nf and not is_bcnf)):
        if not is_3nf:
            st.markdown("<span class='badge-neutral'>BLOCKED</span> &nbsp;&nbsp;Blocked by 3NF violation.", unsafe_allow_html=True)
        elif is_bcnf:
            st.markdown("<span class='badge-pass'>PASSED</span> &nbsp;&nbsp;For all non-trivial FDs $X \\rightarrow Y$, LHS $X$ is a superkey.", unsafe_allow_html=True)
        else:
            st.markdown("<span class='badge-fail'>VIOLATED</span> &nbsp;&nbsp;Found BCNF violations:", unsafe_allow_html=True)
            for viol in viol_bcnf:
                fd = viol["fd"]
                st.markdown(
                    f"- FD `{sorted(list(fd['lhs']))} -> {sorted(list(fd['rhs']))}` violates BCNF because LHS is not a superkey."
                )
                
    # 4NF
    with st.expander(f"4NF: Fourth Normal Form — {'PASSED' if is_4nf else 'VIOLATED'}", expanded=(is_bcnf and not is_4nf)):
        if not is_bcnf:
            st.markdown("<span class='badge-neutral'>BLOCKED</span> &nbsp;&nbsp;Blocked by BCNF violation.", unsafe_allow_html=True)
        elif not mvds:
            st.markdown("<span class='badge-pass'>PASSED (ASSUMED)</span> &nbsp;&nbsp;No Multi-valued Dependencies (MVDs) specified. Satisfies 4NF by default.", unsafe_allow_html=True)
        elif is_4nf:
            st.markdown("<span class='badge-pass'>PASSED</span> &nbsp;&nbsp;For all non-trivial MVDs $X \\twoheadrightarrow Y$, LHS $X$ is a superkey.", unsafe_allow_html=True)
        else:
            st.markdown("<span class='badge-fail'>VIOLATED</span> &nbsp;&nbsp;Found MVD violations:", unsafe_allow_html=True)
            for viol in viol_4nf:
                mvd = viol["mvd"]
                st.markdown(
                    f"- MVD `{sorted(list(mvd['lhs']))} ->-> {sorted(list(mvd['rhs']))}` violates 4NF because LHS is not a superkey."
                )
                
    # 5NF
    with st.expander(f"5NF: Fifth Normal Form — {'PASSED' if is_5nf else 'VIOLATED'}", expanded=(is_4nf and not is_5nf)):
        if not is_4nf:
            st.markdown("<span class='badge-neutral'>BLOCKED</span> &nbsp;&nbsp;Blocked by 4NF violation.", unsafe_allow_html=True)
        elif not jds:
            st.markdown("<span class='badge-pass'>PASSED (ASSUMED)</span> &nbsp;&nbsp;No Join Dependencies (JDs) specified. Satisfies 5NF by default.", unsafe_allow_html=True)
        elif is_5nf:
            st.markdown("<span class='badge-pass'>PASSED</span> &nbsp;&nbsp;Every join dependency is implied by candidate keys.", unsafe_allow_html=True)
        else:
            st.markdown("<span class='badge-fail'>VIOLATED</span> &nbsp;&nbsp;Found Join Dependency violations:", unsafe_allow_html=True)
            for viol in viol_5nf:
                jd = viol["jd"]
                st.markdown(
                    f"- JD `{jd['name']}` violates 5NF because the following components are not superkeys: "
                )
                for ns in viol["non_superkeys"]:
                    st.markdown(f"  - `{sorted(list(ns))}`")
                
    st.markdown("</div>", unsafe_allow_html=True)

# Decomposition & Lossless Chase checks
st.markdown("<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 2rem 0;' />", unsafe_allow_html=True)

st.markdown("<h2 style='font-weight: 800; color: #0F172A;'>🗂️ Relation Decomposition Engine</h2>", unsafe_allow_html=True)

tab3nf, tabbcnf = st.tabs(["3NF Decomposition (Bernstein's Synthesis)", "BCNF Decomposition (Binary Split)"])

with tab3nf:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3>3NF Synthesis Process</h3>", unsafe_allow_html=True)
    st.markdown("<p class='muted-text'>Bernstein's Synthesis algorithm constructs relations directly from the minimal (canonical) cover of functional dependencies. This guarantees that the decomposition is always <b>lossless-join</b> and <b>dependency-preserving</b>.</p>", unsafe_allow_html=True)
    
    decomp_3nf, min_cover, added_key = engine.decompose_3nf(R, fds, candidate_keys)
    
    # 1. Minimal Cover Display
    st.markdown("##### 1. Find Canonical Cover (Minimal Cover)")
    if not min_cover:
        st.markdown("`No functional dependencies to compute cover.`")
    else:
        cover_html = "".join([f"<li><code>{sorted(list(fd['lhs']))} -> {sorted(list(fd['rhs']))}</code></li>" for fd in min_cover])
        st.markdown(f"<ul>{cover_html}</ul>", unsafe_allow_html=True)
        
    # 2. Schema mapping
    st.markdown("##### 2. Synthesize Sub-Relations")
    for idx, rel in enumerate(decomp_3nf):
        rel_fds = engine.project_fds(rel, fds)
        rel_keys = engine.find_candidate_keys(rel, rel_fds)
        keys_str = ", ".join([str(sorted(list(k))) for k in rel_keys])
        
        is_added_key_info = ""
        if added_key and rel == added_key:
            is_added_key_info = " <span class='badge-info' style='font-size:0.75rem;'>Candidate Key Added</span>"
            
        st.markdown(
            f"""
            <div style='background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 0.8rem; border-radius: 8px; margin-bottom: 0.8rem;'>
                <b>Relation {idx+1}:</b> <code>R{idx+1}({", ".join(sorted(list(rel)))})</code> {is_added_key_info}<br/>
                <span class='muted-text' style='font-size:0.85rem;'>Candidate Keys: <code>{keys_str}</code></span><br/>
                <span class='muted-text' style='font-size:0.85rem;'>Projected FDs: <code>{[str(sorted(list(f['lhs']))) + ' -> ' + str(sorted(list(f['rhs']))) for f in rel_fds]}</code></span>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    # 3. Verification checks
    st.markdown("##### 3. Decomposition Properties")
    is_preserving, preserved_fds, failed_fds = engine.check_dependency_preservation(decomp_3nf, fds, R)
    is_lossless, chase_table = engine.check_lossless_join(decomp_3nf, fds, R)
    
    prop_col1, prop_col2 = st.columns(2)
    with prop_col1:
        if is_lossless:
            st.markdown("<span class='badge-pass'>LOSSLESS-JOIN ✔️</span>", unsafe_allow_html=True)
            st.markdown("<span class='muted-text' style='font-size:0.85rem;'>The decomposition can be joined back to reconstruct the original table without introducing spurious rows.</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span class='badge-fail'>LOSSY-JOIN ❌</span>", unsafe_allow_html=True)
            
    with prop_col2:
        if is_preserving:
            st.markdown("<span class='badge-pass'>DEPENDENCY PRESERVING ✔️</span>", unsafe_allow_html=True)
            st.markdown("<span class='muted-text' style='font-size:0.85rem;'>All original functional dependencies can be enforced directly within individual sub-relations.</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span class='badge-fail'>DEPENDENCY LOSS ❌</span>", unsafe_allow_html=True)
            
    # Render Chase matrix visualizer
    with st.expander("Show Chase Lossless Verification Matrix"):
        st.markdown("<p class='muted-text'>Initial state and equivalence resolutions of Chase algorithm. Rows are sub-relations, columns are attributes of R. A row with all <code>a_j</code> variables indicates lossless join.</p>", unsafe_allow_html=True)
        R_list = sorted(list(R))
        header_cols = st.columns([1] + [1]*len(R_list))
        header_cols[0].markdown("**Sub-Rel**")
        for j, attr in enumerate(R_list):
            header_cols[j+1].markdown(f"**{attr} (a_{j})**")
            
        for i, row in enumerate(chase_table):
            row_cols = st.columns([1] + [1]*len(R_list))
            row_cols[0].markdown(f"`R{i+1}`")
            for j, attr in enumerate(R_list):
                val = row[attr]
                if val.startswith("a_"):
                    row_cols[j+1].markdown(f"<span style='color: #16A34A; font-weight:bold;'>{val}</span>", unsafe_allow_html=True)
                else:
                    row_cols[j+1].markdown(f"<span style='color: #DC2626;'>{val}</span>", unsafe_allow_html=True)
                    
    st.markdown("</div>", unsafe_allow_html=True)

with tabbcnf:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3>BCNF Decomposition Process</h3>", unsafe_allow_html=True)
    st.markdown("<p class='muted-text'>BCNF decomposition recursively splits a relation using violating functional dependencies. Note that BCNF decomposition is always <b>lossless-join</b> but is <b>NOT guaranteed to be dependency-preserving</b>.</p>", unsafe_allow_html=True)
    
    decomp_bcnf, trace = engine.decompose_bcnf_trace(R, fds)
    
    # 1. Step by step split trace
    st.markdown("##### 1. Decomposition Splits Trace")
    if not trace:
        st.info("The original relation is already in BCNF. No splits needed!")
    else:
        for idx, step in enumerate(trace):
            rel = step["relation"]
            fd = step["violating_fd"]
            r1, r2 = step["split_into"]
            st.markdown(
                f"""
                <div style='border-left: 3px solid #6B21A8; padding-left: 1rem; margin-bottom: 1rem;'>
                    <b>Step {idx+1}:</b> Decompose <code>R({", ".join(sorted(list(rel)))})</code><br/>
                    <span style='font-size:0.9rem;' class='muted-text'>Violating Dependency: <code>{sorted(list(fd['lhs']))} -> {sorted(list(fd['rhs']))}</code></span><br/>
                    <span style='font-size:0.9rem;' class='muted-text'>Splits into: <code>R1({", ".join(sorted(list(r1)))})</code> and <code>R2({", ".join(sorted(list(r2)))})</code></span>
                </div>
                """,
                unsafe_allow_html=True
            )
            
    # 2. Final BCNF Sub-relations
    st.markdown("##### 2. Final BCNF Relations")
    for idx, rel in enumerate(decomp_bcnf):
        rel_fds = engine.project_fds(rel, fds)
        rel_keys = engine.find_candidate_keys(rel, rel_fds)
        keys_str = ", ".join([str(sorted(list(k))) for k in rel_keys])
        
        st.markdown(
            f"""
            <div style='background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 0.8rem; border-radius: 8px; margin-bottom: 0.8rem;'>
                <b>Relation {idx+1}:</b> <code>R{idx+1}({", ".join(sorted(list(rel)))})</code><br/>
                <span class='muted-text' style='font-size:0.85rem;'>Candidate Keys: <code>{keys_str}</code></span><br/>
                <span class='muted-text' style='font-size:0.85rem;'>Projected FDs: <code>{[str(sorted(list(f['lhs']))) + ' -> ' + str(sorted(list(f['rhs']))) for f in rel_fds]}</code></span>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    # 3. Verification checks
    st.markdown("##### 3. Decomposition Properties")
    is_preserving_bcnf, preserved_fds_bcnf, failed_fds_bcnf = engine.check_dependency_preservation(decomp_bcnf, fds, R)
    is_lossless_bcnf, chase_table_bcnf = engine.check_lossless_join(decomp_bcnf, fds, R)
    
    prop_col1, prop_col2 = st.columns(2)
    with prop_col1:
        if is_lossless_bcnf:
            st.markdown("<span class='badge-pass'>LOSSLESS-JOIN ✔️</span>", unsafe_allow_html=True)
            st.markdown("<span class='muted-text' style='font-size:0.85rem;'>The decomposition can be joined back to reconstruct the original table without introducing spurious rows.</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span class='badge-fail'>LOSSY-JOIN ❌</span>", unsafe_allow_html=True)
            
    with prop_col2:
        if is_preserving_bcnf:
            st.markdown("<span class='badge-pass'>DEPENDENCY PRESERVING ✔️</span>", unsafe_allow_html=True)
            st.markdown("<span class='muted-text' style='font-size:0.85rem;'>All original functional dependencies can be enforced directly within individual sub-relations.</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span class='badge-fail'>DEPENDENCY LOSS ❌</span>", unsafe_allow_html=True)
            if failed_fds_bcnf:
                st.markdown("<span class='muted-text' style='font-size:0.8rem; color:#DC2626;'>Lost Dependencies:</span>", unsafe_allow_html=True)
                for fd in failed_fds_bcnf:
                    st.markdown(f"- `{sorted(list(fd['lhs']))} -> {sorted(list(fd['rhs']))}`")
                    
    # Render Chase matrix visualizer
    with st.expander("Show Chase Lossless Verification Matrix"):
        st.markdown("<p class='muted-text'>Initial state and equivalence resolutions of Chase algorithm. Rows are sub-relations, columns are attributes of R. A row with all <code>a_j</code> variables indicates lossless join.</p>", unsafe_allow_html=True)
        R_list = sorted(list(R))
        header_cols = st.columns([1] + [1]*len(R_list))
        header_cols[0].markdown("**Sub-Rel**")
        for j, attr in enumerate(R_list):
            header_cols[j+1].markdown(f"**{attr} (a_{j})**")
            
        for i, row in enumerate(chase_table_bcnf):
            row_cols = st.columns([1] + [1]*len(R_list))
            row_cols[0].markdown(f"`R{i+1}`")
            for j, attr in enumerate(R_list):
                val = row[attr]
                if val.startswith("a_"):
                    row_cols[j+1].markdown(f"<span style='color: #16A34A; font-weight:bold;'>{val}</span>", unsafe_allow_html=True)
                else:
                    row_cols[j+1].markdown(f"<span style='color: #DC2626;'>{val}</span>", unsafe_allow_html=True)
                    
    st.markdown("</div>", unsafe_allow_html=True)

# Groq AI Assistant Section
st.markdown("<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 2rem 0;' />", unsafe_allow_html=True)
st.markdown("<h2 style='font-weight: 800; color: #0F172A;'>🤖 AI Normalization Guide & Assistant</h2>", unsafe_allow_html=True)
st.markdown("<p class='muted-text'>Ask any question regarding database normalization rules, how keys were computed, or how to resolve dependencies. The AI has full context of your current canvas!</p>", unsafe_allow_html=True)

# Initialize chat history
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# Display chat messages from history
for message in st.session_state.chat_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Ask a question (e.g., 'Explain why my schema violates BCNF and how to fix it')"):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    
    # Prepare system prompt with active relation context
    fds_str = "\n".join([f"{sorted(list(f['lhs']))} -> {sorted(list(f['rhs']))}" for f in fds])
    mvds_str = "\n".join([f"{sorted(list(m['lhs']))} ->-> {sorted(list(m['rhs']))}" for m in mvds])
    jds_str = "\n".join([j["name"] for j in jds])
    
    system_prompt = f"""You are an elite academic Database Normalization Assistant.
You help students understand relational database design, candidate keys, attribute closures, and normal forms (1NF, 2NF, 3NF, BCNF, 4NF, 5NF).
Currently, the user is working on the following schema:
- Relation R: R({", ".join(sorted(list(R)))})
- Functional Dependencies (FDs):
{fds_str if fds_str else "None"}
- Multi-valued Dependencies (MVDs):
{mvds_str if mvds_str else "None"}
- Join Dependencies (JDs):
{jds_str if jds_str else "None"}
- Candidate Keys: {[sorted(list(k)) for k in candidate_keys]}
- Highest Normal Form satisfied: {highest_nf}

Explain clearly, step-by-step, using simple relational algebra definitions. Highlight which dependencies break which normal form rules. Keep answers academic, concise, and professional."""

    # Fetch Groq API Key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        with st.chat_message("assistant"):
            st.markdown("⚠️ **Groq API Key is missing.** Please verify that your API key is correctly configured in the `.env` file at the project root directory.")
    else:
        # Limit history payload for tokens
        payload_messages = [{"role": "system", "content": system_prompt}]
        for msg in st.session_state.chat_messages[-5:]:
            payload_messages.append({"role": msg["role"], "content": msg["content"]})

        try:
            with st.spinner("Thinking..."):
                reply = ai_assistant.chat_completion(payload_messages, api_key)

            with st.chat_message("assistant"):
                st.markdown(reply)
            st.session_state.chat_messages.append({"role": "assistant", "content": reply})
        except ai_assistant.ExtractionError as e:
            with st.chat_message("assistant"):
                st.markdown(f"❌ **Groq API Error:** {str(e)}")
        except Exception as e:
            with st.chat_message("assistant"):
                st.markdown(f"❌ **Failed to reach Groq API:** {str(e)}")
