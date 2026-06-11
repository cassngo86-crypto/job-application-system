import os
import streamlit as st  
from crewai import Agent, Crew, Process, Task
# Remove ScrapeWebsiteTool completely to prevent browser page-load locks
from crewai_tools import SerperDevTool 
from langchain_openai import ChatOpenAI

class JobApplicationCrew:
    def __init__(self) -> None:
        openrouter_key = str(st.secrets["OPENROUTER_API_KEY"]).strip()
        serper_key = str(st.secrets["SERPER_API_KEY"]).strip()
        
        os.environ["OPENROUTER_API_KEY"] = openrouter_key
        os.environ["SERPER_API_KEY"] = serper_key

        # Configure the LLM with a strict local request timeout limit
        self.openrouter_llm = ChatOpenAI(
            model="openai/gpt-4o-mini",
            openai_api_base="https://openrouter.ai/api/v1",
            openai_api_key=openrouter_key,
            max_tokens=2000,
            timeout=30.0, # Enforces a hard network drop if OpenRouter stalls
            max_retries=1
        )

        # Use only the search tool for now to keep execution lean and fast
        self.search_tool = SerperDevTool()

    # Make sure verbose=True and max_iter are set on your Agents below!

        # Define Agents directly and bind the secure LLM configuration object
        self.researcher = Agent(
            role="Tech Job Researcher",
            goal="Make sure to do amazing analysis on job postings to help job applicants.",
            backstory=(
                "As a Job Researcher, your prowess in navigating and extracting critical "
                "information from job postings is unmatched. Your skills help pinpoint the necessary "
                "qualifications and skills sought by employers, forming the foundation for effective application tailoring."
            ),
            tools=[self.search_tool],
            llm=self.openrouter_llm,  
            verbose=True,
            max_iter=4
        )

        self.profiler = Agent(
            role="Personal Profiler for Engineers",
            goal="Do incredible research on job applicants to help them stand out in the job market.",
            backstory=(
                "Equipped with analytical prowess, you dissect and synthesize information "
                "from diverse sources to craft comprehensive personal and professional profiles, "
                "laying the groundwork for personalized resume enhancements."
            ),
            tools=[self.search_tool],
            llm=self.openrouter_llm,  
            verbose=True,
            max_iter=4
        )

        self.resume_strategist = Agent(
            role="Resume Strategist for Engineers",
            goal="Find all the best ways to make a resume stand out in the job market.",
            backstory=(
                "With a strategic mind and an eye for detail, you excel at refining resumes to "
                "highlight the most relevant skills and experiences, ensuring they resonate perfectly "
                "with the job's requirements."
            ),
            tools=[self.search_tool],
            llm=self.openrouter_llm,  
            verbose=True,
            max_iter=4
        )

        self.interview_preparer = Agent(
            role="Engineering Interview Preparer",
            goal="Create interview questions and talking points based on the resume and job requirements.",
            backstory=(
                "Your role is crucial in anticipating the dynamics of interviews. With your ability "
                "to formulate key questions and talking points, you prepare candidates for success, "
                "ensuring they can confidently address all aspects of the job they are applying for."
            ),
            tools=[self.search_tool],
            llm=self.openrouter_llm,  
            verbose=True,
            max_iter=4
        )

    def crew(self) -> Crew:
        # Task 1: Research the job and align it with the candidate profile
        strategy_task = Task(
            description=(
                "1. Analyze the job posting URL provided ({job_posting_url}) using your search tools to extract key skills, "
                "experiences, and qualifications required for the role.\n"
                "2. Synthesize this data with the candidate's background details provided in {personal_writeup} and {profile_urls}.\n"
                "3. Generate a comprehensive strategy document highlighting the most crucial alignment points, mandatory skills, "
                "and recommended baseline presentation strategy. Do not invent facts."
            ),
            expected_output="A structured document detailing the job requirements matched explicitly against the candidate's core strengths.",
            output_file="strategy_output.md", # Matches Tab 1
            agent=self.resume_strategist,
            verbose=True
        )

        # Task 2: Formulate Expected Interview Questions
        questions_task = Task(
            description=(
                "Review the matching strategy generated in the previous task. Create a set of targeted, highly probable "
                "technical and situational interview questions specifically tailored for this role and the candidate's profile. "
                "Include brief guidelines on what a successful answer should highlight based on their background."
            ),
            expected_output="A clean markdown document containing expected interview questions with contextual response guidelines.",
            output_file="questions_output.md", # Matches Tab 2
            context=[strategy_task],
            agent=self.interview_preparer,
            verbose=True
        )

        # Task 3: Develop Custom Strategic Talking Points
        talking_points_task = Task(
            description=(
                "Develop high-impact, custom interview talking points and behavioral discussion cues. Ensure these "
                "talking points help the candidate naturally elevate key elements of their project experiences, "
                "contributions, and technical capabilities to demonstrate immediate value to the hiring manager."
            ),
            expected_output="A document containing clear bullet points, elevator pitches, and talking points for the interview.",
            output_file="talking_points_output.md", # Matches Tab 3
            context=[strategy_task, questions_task],
            agent=self.interview_preparer,
            verbose=True
        )

        return Crew(
            agents=[self.resume_strategist, self.interview_preparer],
            tasks=[strategy_task, questions_task, talking_points_task],
            process=Process.sequential, # Guarantees each task finishes cleanly before the next begins
            memory=False,
            verbose=True
        )