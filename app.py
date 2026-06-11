import os
import sys
import types

# --- BULLETPROOF RUNTIME MEMORY MOCK PATCH ---
# Force-create a dummy pkg_resources module in system memory to satisfy legacy CrewAI telemetry
IMAGINARY_PKG = types.ModuleType("pkg_resources")
IMAGINARY_PKG.declare_namespace = lambda name: None
IMAGINARY_PKG.get_distribution = lambda name: types.SimpleNamespace(version="0.28.8")
sys.modules["pkg_resources"] = IMAGINARY_PKG
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
        # Run the crew without touching st.session_state inside here
        result = JobApplicationCrew().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        print(f"Error running crew: {e}")

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

  
    # ─── RUN THE CREW NATIVELY HERE ───
    with st.spinner("Formulating strategy... The crew is analyzing your data live."):
        try:
            # Instantiate and run your crew class synchronously
            crew_instance = JobApplicationCrew().crew()
            result = crew_instance.kickoff(inputs=crew_inputs)
            
            # Save final raw result to session state
            st.session_state.crew_result = result
            st.success("Analysis Complete!")
            
            # ─── STREAMLIT INTERACTIVE TABS LAYOUT ───
            # Create professional separate tabs for your structural outputs
            tab1, tab2, tab3 = st.tabs([
                "🎯 Tailored Strategy & Prep", 
                "❓ Expected Interview Questions", 
                "📋 Custom Talking Points"
            ])
            
            with tab1:
                st.subheader("Application Strategy & Profile Alignment")
                # Pull specific task output if defined, otherwise display main result safely
                if len(crew_instance.tasks) > 0:
                    st.markdown(crew_instance.tasks[0].output.exported_output)
                else:
                    st.markdown(result)
                    
            with tab2:
                st.subheader("Targeted Interview Preparation Questions")
                if len(crew_instance.tasks) > 1:
                    st.markdown(crew_instance.tasks[1].output.exported_output)
                else:
                    st.info("Review your primary strategy or check task order definitions.")
                    
            with tab3:
                st.subheader("Key Interview Talking Points")
                if len(crew_instance.tasks) > 2:
                    st.markdown(crew_instance.tasks[2].output.exported_output)
                else:
                    st.info("Review your primary strategy or check task order definitions.")
            
        except Exception as e:
            st.error(f"An execution error occurred: {str(e)}")
            
        finally:
            # Re-enable the button so the user can run it again if needed
            st.session_state.crew_running = False