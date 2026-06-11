import os
import streamlit as st
from crewai import Agent, Crew, Process, Task
from langchain_openai import ChatOpenAI

class JobApplicationCrew:
    def __init__(self) -> None:
        openrouter_key = str(st.secrets["OPENROUTER_API_KEY"]).strip()
        os.environ["OPENROUTER_API_KEY"] = openrouter_key

        # Configure the LLM exactly for CrewAI 0.30.x standard compliance
        self.openrouter_llm = ChatOpenAI(
            model="openai/gpt-4o-mini",
            openai_api_base="https://openrouter.ai/api/v1",
            openai_api_key=openrouter_key,
            max_tokens=2000,
            timeout=45.0,
            max_retries=1
        )

        # 1. Define Agents natively to avoid version 0.30.x property mismatches
        self.resume_strategist = Agent(
            role="Resume Strategist",
            goal="Align candidate profiles with target job descriptions flawlessly",
            backstory="An expert technical recruiter who knows exactly how to map engineering skills to core job requirements.",
            tools=[], # Keep empty to ensure 0-loop pure text analysis
            llm=self.openrouter_llm,
            verbose=True,
            max_iter=3,
            allow_delegation=False # Crucial for 0.30.x to prevent agents trying to talk to each other indefinitely
        )

        self.interview_preparer = Agent(
            role="Interview Prep Specialist",
            goal="Formulate high-probability interview questions and custom behavioral talking points",
            backstory="A veteran career coach specialized in preparing candidates for rigorous technical rounds.",
            tools=[], 
            llm=self.openrouter_llm,
            verbose=True,
            max_iter=3,
            allow_delegation=False
        )

    def crew(self) -> Crew:
        # 2. Define Tasks explicitly with proper inputs matching app.py
        strategy_task = Task(
            description=(
                "Analyze the provided job destination requirements and candidate details. "
                "Using the context directly from {personal_writeup} and the reference URL {job_posting_url}, "
                "generate a comprehensive strategy document highlighting the most crucial alignment points, "
                "mandatory skills, and recommended presentation strategy. Work strictly with the text provided."
            ),
            expected_output="A structured markdown document detailing the job requirements matched explicitly against the candidate's core strengths.",
            output_file="strategy_output.md",
            agent=self.resume_strategist
        )

        questions_task = Task(
            description=(
                "Review the matching strategy generated in the previous task. Create a set of targeted, highly probable "
                "technical and situational interview questions specifically tailored for this role and the candidate's profile."
            ),
            expected_output="A clean markdown document containing expected interview questions with contextual response guidelines.",
            output_file="questions_output.md",
            context=[strategy_task], # Native task sequencing context matching
            agent=self.interview_preparer
        )

        talking_points_task = Task(
            description=(
                "Develop high-impact, custom interview talking points and behavioral discussion cues based on the strategy "
                "to help the candidate naturally elevate key elements of their project experiences during the conversation."
            ),
            expected_output="A clean markdown document containing clear bullet points, elevator pitches, and talking points for the interview.",
            output_file="talking_points_output.md",
            context=[strategy_task, questions_task],
            agent=self.interview_preparer
        )

        # 3. Assemble and return the Crew object
        return Crew(
            agents=[self.resume_strategist, self.interview_preparer],
            tasks=[strategy_task, questions_task, talking_points_task],
            process=Process.sequential,
            memory=False,
            verbose=True
        )