import os
import re
import tempfile
import uuid
import streamlit as st

from parser import ResumeParser
from scorer import ATSScorer
from optimizer import ATSOptimizer

# Page Configuration
st.set_page_config(
    page_title="ATS Score Checker & Optimizer",
    page_icon="⚙️",
    layout="centered"
)

# Custom High-Contrast Black & White CSS Style injection
st.markdown(
    """
    <style>
    /* Premium B&W minimalist styling overrides */
    .stApp {
        background-color: #000000;
        color: #ffffff;
    }
    
    /* Header design elements */
    .app-header {
        text-align: center;
        border-bottom: 1px solid #222222;
        padding-bottom: 24px;
        margin-bottom: 32px;
    }
    .logo-title {
        font-size: 26px;
        font-weight: 800;
        letter-spacing: 0.15em;
        margin-bottom: 8px;
        text-transform: uppercase;
        color: #ffffff;
    }
    .logo-subtitle {
        color: #888888;
        font-size: 12px;
        font-weight: 400;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    
    /* Custom Card */
    .bw-card {
        background-color: #0a0a0a;
        border: 1px solid #222222;
        border-radius: 4px;
        padding: 24px;
        margin-bottom: 24px;
    }
    
    /* High-contrast Score banner */
    .score-summary-bar {
        display: flex;
        align-items: center;
        gap: 24px;
        background-color: #0a0a0a;
        border: 1px solid #222222;
        border-radius: 4px;
        padding: 20px;
        margin-bottom: 30px;
    }
    .score-circle {
        width: 84px;
        height: 84px;
        border: 3px solid #ffffff;
        border-radius: 50%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background-color: #000000;
        flex-shrink: 0;
        transition: border-color 0.3s ease;
    }
    .score-number {
        font-size: 30px;
        font-weight: 800;
        line-height: 1;
        color: #ffffff;
        transition: color 0.3s ease;
    }
    .score-total {
        font-size: 10px;
        color: #888888;
        font-weight: 600;
    }
    .score-text-details {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 4px;
    }
    .status-badge {
        font-size: 9px;
        font-weight: 700;
        letter-spacing: 0.08em;
        background-color: #ffffff;
        color: #000000;
        padding: 2px 8px;
        border-radius: 2px;
        text-transform: uppercase;
    }
    .scan-filename {
        font-size: 16px;
        font-weight: 700;
        margin: 0;
        color: #ffffff;
    }
    .scan-meta {
        font-size: 11px;
        color: #888888;
        margin: 0;
    }
    
    /* Diagnostic Remarks List styling */
    .remark-item {
        border-left: 3px solid #333333;
        padding: 4px 0 4px 16px;
        margin-bottom: 16px;
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .remark-item.warning {
        border-left-color: #888888;
    }
    .remark-item.critical {
        border-left-color: #ffffff;
        background-color: rgba(255, 255, 255, 0.02);
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .remark-header {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .remark-section-tag {
        font-size: 8px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        border: 1px solid #333333;
        padding: 1px 5px;
        color: #888888;
    }
    .remark-title {
        font-size: 13px;
        font-weight: 600;
        color: #ffffff;
    }
    .remark-suggestion {
        font-size: 12px;
        color: #888888;
    }
    
    /* Auto Rewrite changes list styling */
    .change-item {
        background-color: #080808;
        border: 1px solid #181818;
        padding: 16px;
        margin-bottom: 16px;
        border-radius: 2px;
    }
    .change-original {
        color: #555555;
        text-decoration: line-through;
        font-size: 12px;
        margin-bottom: 6px;
        line-height: 1.5;
    }
    .change-optimized {
        color: #ffffff;
        font-weight: 500;
        border-left: 2px solid #ffffff;
        padding-left: 10px;
        font-size: 12.5px;
        line-height: 1.5;
    }
    
    /* Clean, premium bullet points */
    .bullet-list {
        list-style: none;
        padding-left: 0;
    }
    .bullet-list li {
        font-size: 12.5px;
        color: #888888;
        position: relative;
        padding-left: 16px;
        margin-bottom: 8px;
    }
    .bullet-list li::before {
        content: "—";
        position: absolute;
        left: 0;
        color: #555555;
    }
    
    /* Fix blank text color on Streamlit buttons */
    div.stButton > button {
        color: #ffffff !important;
        background-color: transparent !important;
        border: 1px solid #222222 !important;
        border-radius: 4px !important;
        transition: all 0.2s ease !important;
    }
    div.stButton > button:hover {
        border-color: #ffffff !important;
        background-color: #121212 !important;
    }
    div.stButton > button[kind="primary"] {
        color: #000000 !important;
        background-color: #ffffff !important;
        border: 1px solid #ffffff !important;
        font-weight: 700 !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #e5e5e5 !important;
        border-color: #e5e5e5 !important;
    }
    
    /* Streamlit download link buttons should match standard button design */
    div.stDownloadButton > button {
        color: #000000 !important;
        background-color: #ffffff !important;
        border: 1px solid #ffffff !important;
        border-radius: 4px !important;
        font-weight: 700 !important;
        transition: all 0.2s ease !important;
    }
    div.stDownloadButton > button:hover {
        background-color: #e5e5e5 !important;
        border-color: #e5e5e5 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize Session State
if "step" not in st.session_state:
    st.session_state.step = "upload"
if "parsed_data" not in st.session_state:
    st.session_state.parsed_data = None
if "file_name" not in st.session_state:
    st.session_state.file_name = ""

# Centered Logo and Application Header HTML
if os.path.exists("ats_logo.png"):
    col1, col2, col3 = st.columns([5, 2, 5])
    with col2:
        st.image("ats_logo.png", use_container_width=True)

st.markdown(
    """
    <div class="app-header" style="margin-top: -15px;">
        <h1 class="logo-title">ATS SCORE CHECKER & OPTIMIZER</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# Helper function to switch steps
def navigate_to(step_name):
    st.session_state.step = step_name
    st.rerun()

# -------------------------------------------------------------
# STEP 1: RESUME UPLOAD STATE
# -------------------------------------------------------------
if st.session_state.step == "upload":
    role = st.selectbox(
        "Target Role Profile",
        options=[
            ("Auto-Detect Industry Profile", ""),
            ("Software Engineering / DevOps", "software_engineering"),
            ("Data Science / ML Engineering", "data_science"),
            ("UI/UX Design & Research", "design"),
            ("Product Management", "product_management"),
            ("Project & Program Management", "project_management"),
            ("Digital Marketing & Growth", "marketing"),
            ("Sales & Business Development", "sales"),
            ("Finance & Business Analysis", "finance"),
            ("Human Resources & Recruitment", "hr"),
            ("Operations & Supply Chain", "operations"),
            ("Healthcare Administration", "healthcare")
        ],
        format_func=lambda x: x[0]
    )
    
    uploaded_file = st.file_uploader(
        "Upload your resume",
        type=["pdf", "docx"],
        help="Support PDF or DOCX files. Older format CVs with graphics or multiple columns are audited."
    )
    
    if uploaded_file is not None:
        st.session_state.file_name = uploaded_file.name
        # Save uploader stream to temporary file safely
        with tempfile.NamedTemporaryFile(suffix=os.path.splitext(uploaded_file.name)[1], delete=False) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
            
        with st.spinner("Extracting layout blocks and running diagnostics..."):
            try:
                parse_result = ResumeParser.parse_file(tmp_path)
                if parse_result.get("success"):
                    text = parse_result["text"]
                    issues = parse_result["structural_issues"]
                    
                    # Compute initial metrics
                    selected_profile_code = role[1] if role else None
                    score_data = ATSScorer.calculate_score(text, issues, selected_profile_code)
                    manual_opt = ATSOptimizer.get_manual_suggestions(score_data)
                    
                    # Automatically trigger sentence optimization
                    env_api_key = os.environ.get("GEMINI_API_KEY", "")
                    rewrite_res = ATSOptimizer.optimize_resume_text(
                        text,
                        score_data["profile"],
                        env_api_key if env_api_key else None
                    )
                    
                    # Analyze specific deficiencies for each rewritten sentence
                    corrections = []
                    for chg in rewrite_res.get("changes", []):
                        orig = chg["original"]
                        opt = chg["optimized"]
                        
                        clean_orig = re.sub(r'^[\s•\-\*▪●]+', '', orig).strip()
                        clean_opt = re.sub(r'^[\s•\-\*▪●]+', '', opt).strip()
                        
                        analysis = ATSOptimizer.analyze_bullet_deficiencies(clean_orig, clean_opt)
                        corrections.append({
                            "original_raw": clean_orig,
                            "original_html": analysis["original_html"],
                            "optimized": clean_opt,
                            "badges": analysis["badges"]
                        })
                    
                    st.session_state.parsed_data = {
                        "text": text,
                        "structural_issues": issues,
                        "score_data": score_data,
                        "manual_optimization": manual_opt,
                        "format": parse_result["format"],
                        "corrections": corrections
                    }
                    st.session_state.target_profile = score_data["profile"]
                    navigate_to("dashboard")
                else:
                    st.error(f"Ingestion failed: {parse_result.get('error')}")
            except Exception as e:
                st.error(f"Error executing scan: {str(e)}")
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

# -------------------------------------------------------------
# STEP 2: EVALUATION DASHBOARD STATE
# -------------------------------------------------------------
elif st.session_state.step == "dashboard":
    s = st.session_state.parsed_data["score_data"]
    
    # Determine dynamic color — Green only at 90+, Yellow 60-89, Red below 60
    score = s['score']
    if score >= 90:
        score_color = "#10b981"  # Excellent: Green
    elif score >= 60:
        score_color = "#f59e0b"  # Moderate: Yellow/Amber
    else:
        score_color = "#ef4444"  # Poor: Red
    
    # Inject dynamic CSS to override the static class colors — this has higher
    # specificity than the base class since it's added after the base stylesheet
    st.markdown(
        f"""
        <style>
        .score-circle {{ border-color: {score_color} !important; }}
        .score-number {{ color: {score_color} !important; }}
        .status-badge {{
            background-color: {score_color} !important;
            color: #000000 !important;
            font-weight: 800 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
        
    # HTML High-contrast metrics row
    st.markdown(
        f"""
        <div class="score-summary-bar">
            <div class="score-circle">
                <span class="score-number">{score}</span>
                <span class="score-total">/100</span>
            </div>
            <div class="score-text-details">
                <span class="status-badge">{s['status']}</span>
                <h3 class="scan-filename">{st.session_state.file_name}</h3>
                <p class="scan-meta">Profile: {s['profile'].replace('_', ' ').upper()}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("### Detailed Remarks & Gap Isolation")
    
    # Streamlit Tab Panels
    tab_sentences, tab_keywords, tab_formatting = st.tabs([
        "❌ Sentence Corrections", "🔑 Missing Keywords", "📐 Layout & General Gaps"
    ])
    
    with tab_sentences:
        corrections = st.session_state.parsed_data.get("corrections", [])
        if not corrections:
            st.success("🎉 No sentence-level deficiencies detected! All bullet points are well-quantified and use strong action verbs.")
        else:
            st.markdown(
                "<p style='color: #888888; font-size: 13px; margin-bottom: 20px;'>"
                "The following CV lines lower your ATS score due to weak phrasing, missing metrics, or passive verbs. "
                "Consider replacing them with the suggested high-impact corrections:</p>",
                unsafe_allow_html=True
            )
            for c in corrections:
                badges_html = " ".join([
                    f'<span style="border: 1px solid {"#ef4444" if b in ["Weak Phrasing", "Weak Action Verb"] else "#f59e0b"}; '
                    f'color: {"#ef4444" if b in ["Weak Phrasing", "Weak Action Verb"] else "#f59e0b"}; '
                    f'font-size: 9px; font-weight: 700; padding: 2px 6px; border-radius: 2px; '
                    f'margin-right: 6px; text-transform: uppercase; letter-spacing: 0.05em;">{b}</span>'
                    for b in c["badges"]
                ])
                
                st.markdown(
                    f"""
                    <div class="bw-card" style="border-left: 3px solid #ef4444; padding: 16px; margin-bottom: 16px;">
                        <div style="margin-bottom: 8px;">{badges_html}</div>
                        <div style="font-size: 13px; color: #666666; text-decoration: line-through; margin-bottom: 8px; line-height: 1.5;">
                            {c['original_html']}
                        </div>
                        <div style="font-size: 14px; color: #ffffff; border-left: 2px solid #ffffff; padding-left: 10px; font-weight: 500; line-height: 1.5;">
                            {c['optimized']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    with tab_keywords:
        missing_kws = s["breakdown"]["keywords"]["missing"]
        matched_kws = s["breakdown"]["keywords"]["matched"]
        
        if not missing_kws:
            st.success("🏆 Perfect keyword match! You have integrated all required core skills and tools.")
        else:
            st.markdown(
                f"<p style='color: #888888; font-size: 13px; margin-bottom: 20px;'>"
                f"Your CV is missing the following key industry terms for the **{s['profile'].replace('_', ' ').upper()}** profile. "
                f"Adding these will raise your score:</p>",
                unsafe_allow_html=True
            )
            
            # Show missing keywords in red/amber styled pills
            kw_html = "".join([
                f'<span style="background-color: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; '
                f'color: #ef4444; font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 4px; '
                f'margin: 4px; display: inline-block;">{kw}</span>'
                for kw in missing_kws
            ])
            st.markdown(f'<div style="margin-bottom: 24px;">{kw_html}</div>', unsafe_allow_html=True)
            
            # Also show matched keywords in sub-section to distinguish them
            if matched_kws:
                st.markdown("**Already Matched Keywords:**")
                matched_html = "".join([
                    f'<span style="background-color: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; '
                    f'color: #10b981; font-size: 11px; font-weight: 500; padding: 3px 8px; border-radius: 4px; '
                    f'margin: 4px; display: inline-block;">{kw}</span>'
                    for kw in matched_kws
                ])
                st.markdown(f'<div style="margin-top: 8px;">{matched_html}</div>', unsafe_allow_html=True)

    with tab_formatting:
        remarks_list = s["remarks"]
        if not remarks_list:
            st.success("🎉 No formatting or layout issues detected! The document structure is fully ATS-compliant.")
        else:
            st.markdown(
                "<p style='color: #888888; font-size: 13px; margin-bottom: 20px;'>"
                "The following layout, formatting, or general issues are lowering your score:</p>",
                unsafe_allow_html=True
            )
            for rem in remarks_list:
                sev = rem.get("severity", "warning").lower()
                # Determine color based on severity
                color = "#ffffff" if sev == "critical" else "#888888"
                border_color = "#ffffff" if sev == "critical" else "#222222"
                bg_color = "rgba(255, 255, 255, 0.04)" if sev == "critical" else "#0a0a0a"
                
                st.markdown(
                    f"""
                    <div class="remark-item {sev}" style="border-left: 3px solid {color}; background-color: {bg_color}; border-right: 1px solid {border_color}; border-top: 1px solid {border_color}; border-bottom: 1px solid {border_color}; border-radius: 4px; padding: 16px; margin-bottom: 12px;">
                        <div class="remark-header" style="margin-bottom: 6px;">
                            <span class="remark-section-tag" style="border-color: {color}; color: {color};">{rem.get('section', 'general')}</span>
                            <span class="remark-title" style="font-weight: 700; color: #ffffff; margin-left: 8px;">{rem['issue']}</span>
                        </div>
                        <div class="remark-suggestion" style="font-size: 12px; color: #aaaaaa; line-height: 1.4;">{rem['suggestion']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # Go back / Upload another
    st.markdown("---")
    if st.button("Upload Another Resume", use_container_width=True):
        st.session_state.step = "upload"
        st.session_state.parsed_data = None
        st.rerun()
