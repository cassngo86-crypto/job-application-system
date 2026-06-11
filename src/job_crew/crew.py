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
            tools=[self.scrape_tool, self.search_tool],
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
            tools=[self.scrape_tool, self.search_tool],
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
            tools=[self.scrape_tool, self.search_tool],
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
            tools=[self.scrape_tool, self.search_tool],
            llm=self.openrouter_llm,  
            verbose=True,
            max_iter=4
        )

    def crew(self) -> Crew:
        research_task = Task(
            description=(
                "Analyze the job posting URL provided ({job_posting_url}) to extract key skills, "
                "experiences, and qualifications required. Use the tools to gather content and identify "
                "and categorize the requirements."
            ),
            expected_output="A structured list of job requirements, including necessary skills, qualifications, and experiences.",
            agent=self.researcher,
            async_execution=True
        )

        profile_task = Task(
            description=(
                "Compile a detailed personal and professional profile using the background profile links or URLs ({profile_urls}), "
                "and the personal background write-up or file content provided ({personal_writeup}). "
                "Utilize your tools to extract, read, and synthesize information from these sources."
            ),
            expected_output="A comprehensive profile document that includes skills, project experiences, contributions, interests, and communication style.",
            agent=self.profiler,
            async_execution=True
        )

        resume_strategy_task = Task(
            description=(
                "Using the profile and job requirements obtained from previous tasks, tailor the resume to highlight "
                "the most relevant areas. Employ tools to adjust and enhance the resume content. Make sure this is "
                "the best resume ever, but don't make up any information. Update every section, including the initial summary, "
                "work experience, skills, and education. All to better reflect the candidate's abilities and how it matches the job posting."
            ),
            expected_output="An updated resume that effectively highlights the candidate's qualifications and experiences relevant to the job.",
            output_file="tailored_resume.md",
            context=[research_task, profile_task],
            agent=self.resume_strategist
        )

        interview_preparation_task = Task(
            description=(
                "Create a set of potential interview questions and talking points based on the tailored resume and job requirements. "
                "Utilize tools to generate relevant questions and discussion points. Make sure to use these questions and talking "
                "points to help the candidate highlight the main points of the resume and how it matches the job posting."
            ),
            expected_output="A document containing key questions and talking points that the candidate should prepare for the initial interview.",
            output_file="interview_materials.md",
            context=[research_task, profile_task, resume_strategy_task],
            agent=self.interview_preparer
        )

        return Crew(
            agents=[self.researcher, self.profiler, self.resume_strategist, self.interview_preparer],
            tasks=[research_task, profile_task, resume_strategy_task, interview_preparation_task],
            process=Process.sequential,
            memory=False,
            verbose=True
        )