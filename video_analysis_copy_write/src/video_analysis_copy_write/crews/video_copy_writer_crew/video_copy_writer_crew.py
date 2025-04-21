from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task

import os


@CrewBase
class VideoCopyWriterCrew:
    """video copy writer crew"""
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    deepseek_r1_lm = LLM(
            model="openrouter/deepseek/deepseek-r1",
			base_url="https://openrouter.ai/api/v1",
			api_key=os.environ['OPENROUTER_API_KEY'],
            temperature=0.1,
    )

    gemini_llm = LLM(
            model="openrouter/google/gemini-2.5-pro-preview-03-25",
			base_url="https://openrouter.ai/api/v1",
			api_key=os.environ['OPENROUTER_API_KEY'],
            temperature=0.1,
    )


    @agent
    def video_copy_writer_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['video_copy_writer_agent'],
            llm=self.deepseek_r1_lm,
            verbose=True
        )
    

    @task
    def video_copy_writer_task(self) -> Task:
        return Task(
            config=self.tasks_config['video_copy_writer_task'],
            agent=self.video_copy_writer_agent(),
            output_file='video_copy_writer_output.md'
        )



    @crew
    def crew(self) -> Crew:
        """Creates the JobPostingCrew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
        )