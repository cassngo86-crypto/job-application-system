import os
import sys
import subprocess
import importlib

# --- BULLETPROOF RUNTIME BOOTSTRAP PATCH ---
# Force-install setuptools and explicitly refresh the workspace import tracking environment
try:
    import pkg_resources
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "setuptools"])
    importlib.invalidate_caches()  # <--- Forces Python to re-scan the drive for the new module
    import pkg_resources
# ──────────────────────────────────────

import streamlit as st
import io
from docx import Document
import threading
from streamlit.runtime.scriptrunner import add_script_run_ctx

# Add source directory path and import your crew module
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from src.job_crew.crew import JobApplicationCrew


st.set_page_config(page_title="AI Application Tailoring Crew", page_icon="💼", layout="wide")

st.title("💼 Multi-Agent Job Tailoring System")
st.caption("Coordinate autonomous agents to evaluate listings, profiles, and deliver targeted interview briefs.")

# Initialize background worker states
if "crew_running" not in st.session_state:
    st.session_state.crew_running = False
if "crew_result" not in st.session_state:
    st.session_state.crew_result = None

def run_crew_async(inputs):
    try:
        # Create an instance and call the crew method directly
        crew_instance = JobApplicationCrew().crew()
        result = crew_instance.kickoff(inputs=inputs)
        st.session_state.crew_result = result
    except Exception as e:
        st.session_state.crew_result = f"Error during execution: {str(e)}"
    finally:
        st.session_state.crew_running = False

# Layout Forms
with st.sidebar:
    st.header("Pipeline Inputs")
    job_url = st.text_input("Job Posting URL", value="https://jobs.lever.co/AIFund/6c82e23e-d954-4dd8-a734-c0c2c5ee00f1")
    
    st.markdown("---")
    st.subheader("Candidate Information")
    
    # 1. Flexible Input Strategy Selector
    profile_source = st.radio(
        "Choose profile background source:",
        ["Provide Profile URL (LinkedIn / GitHub / Portfolio)", "Upload Profile Document (TXT / MD)"]
    )
    
    profile_url_input = ""
    uploaded_text_content = ""
    
    if profile_source == "Provide Profile URL (LinkedIn / GitHub / Portfolio)":
        profile_url_input = st.text_input("Profile URL", value="https://github.com/joaomdmoura")
    else:
        uploaded_file = st.file_uploader("Upload background profile or existing resume", type=["txt", "md"])
        if uploaded_file is not None:
            # Safely decode binary stream payload to string data
            uploaded_text_content = uploaded_file.read().decode("utf-8")
            st.success("File uploaded successfully!")

    st.markdown("---")
    
    # 2. Text Summary Box
    text_summary = st.text_area(
        "Professional Summary / Additional Context",
        value="Jansen is an accomplished Software Engineering Leader with 18 years of experience, specializing in managing remote and in-office teams.",
        height=150
    )
    
    submit_btn = st.button("Kickoff Crew Agents", disabled=st.session_state.crew_running)

# Controller Action
if submit_btn and not st.session_state.crew_running:
    st.session_state.crew_running = True
    st.session_state.crew_result = None
    
    # Consolidate text content based on what the user provided
    final_writeup = text_summary
    if uploaded_text_content:
        final_writeup += f"\n\n--- EMBEDDED ATTACHMENT PROFILE CONTENT ---\n{uploaded_text_content}"
    
    # Format inputs dynamically to match our updated tasks configuration map
    crew_inputs = {
        'job_posting_url': job_url,
        'profile_urls': profile_url_input if profile_url_input else "No URL provided; check text/attachment profile data.",
        'personal_writeup': final_writeup
    }
    
    worker_thread = threading.Thread(target=run_crew_async, args=(crew_inputs,))
    add_script_run_ctx(worker_thread)
    worker_thread.start()

# Live Interface Rendering Contexts
if st.session_state.crew_running:
    st.info("🤖 Multi-agent runtime pipeline active. Running web scraping, profile synthesis, and building materials...")
    st.spinner("Agents are collaborating...")
    st.rerun()

elif st.session_state.crew_result:
    st.success("🎉 Crew completed assignment pipeline successfully!")
    
    tab1, tab2, tab3 = st.tabs(["📝 Tailored Resume", "🎯 Interview Preparation Materials", "⚙️ Raw Run Trace"])
    
    with tab1:
        if os.path.exists("tailored_resume.md"):
            with open("tailored_resume.md", "r", encoding="utf-8") as f:
                resume_content = f.read()
            
            # Compile into Word Document structure
            doc1 = Document()
            doc1.add_paragraph(resume_content)
            bio1 = io.BytesIO()
            doc1.save(bio1)
            
            # Download as Word (.docx)
            st.download_button(
                label="📥 Download Tailored Resume (.docx)",
                data=bio1.getvalue(),
                file_name="tailored_resume.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            st.markdown("---")
            st.markdown(resume_content)
        else:
            st.warning("Resume file artifact was not committed successfully to workspace.")
            
    with tab2:
        if os.path.exists("interview_materials.md"):
            with open("interview_materials.md", "r", encoding="utf-8") as f:
                interview_content = f.read()
            
            # Compile into Word Document structure
            doc2 = Document()
            doc2.add_paragraph(interview_content)
            bio2 = io.BytesIO()
            doc2.save(bio2)
            
            # Download as Word (.docx)
            st.download_button(
                label="📥 Download Interview Prep Materials (.docx)",
                data=bio2.getvalue(),
                file_name="interview_materials.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            st.markdown("---")
            st.markdown(interview_content)
        else:
            st.warning("Interview prep file artifact was not committed successfully to workspace.")
            
    with tab3:
        st.subheader("Raw Output Payload")
        st.write(str(st.session_state.crew_result))