from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from social_media_auto_comment.tools.custom_vision_tool import CustomVisionTool

import os
import logging
    # 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@CrewBase
class MultiModalAnalysisCrew:
    """Book Outline Crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
    # llm = ChatOpenAI(model="chatgpt-4o-latest")

#google/gemini-2.5-pro-preview-03-25
    custom_llm = LLM(
            model="openrouter/google/gemini-2.0-flash-001",
			base_url="https://openrouter.ai/api/v1",
			api_key=os.environ['OPENROUTER_API_KEY'],
            temperature=0.1,
    )

    qwen_llm = LLM(
            model="openai/qwen-vl-max-latest", # liteLLM中使用openAI-compatible模式调用第三方model时，统一provider为openai,  https://docs.litellm.ai/docs/providers/openai_compatible
			base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
			api_key=os.environ['DASHSCOPE_API_KEY'],
            temperature=0.1,

	)


	# If you would like to add tools to your agents, you can learn more about it here:
	# https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def multi_modal_understand_analyst(self) -> Agent:
        return Agent(
			config=self.agents_config['multi_modal_understand_analyst'],
			# multimodal=True, # 不要加，一加就报错。
			llm=self.custom_llm,
			tools=[CustomVisionTool(model=self.custom_llm)],
			verbose=True
		)



	# To learn more about structured task outputs,
	# task dependencies, and task callbacks, check out the documentation:
	# https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def multi_modal_understand_task(self) -> Task:
        return Task(
			config=self.tasks_config['multi_modal_understand_task'],
			agent=self.multi_modal_understand_analyst(),
			output_file='image_analysis.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the ImageAnalysisCrew crew"""
        return Crew(
			agents=self.agents,
			tasks=self.tasks,
			process=Process.sequential,
			verbose=True
		)
