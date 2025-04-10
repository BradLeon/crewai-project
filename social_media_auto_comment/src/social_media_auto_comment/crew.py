from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import VisionTool
import os
import logging


# If you want to run a snippet of code before or after the crew starts, 
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

# 设置代理配置
PROXY_CONFIG = {
    "http_proxy": "http://127.0.0.1:10080",
    "https_proxy": "http://127.0.0.1:10080",
    "no_proxy": "localhost,127.0.0.1"
}

# 配置日志级别
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@CrewBase
class SocialMediaAutoComment():
	"""SocialMediaAutoComment crew"""

	# Learn more about YAML configuration files here:
	# Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
	# Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'


#google/gemini-2.5-pro-preview-03-25
	custom_llm = LLM(
            model="openrouter/google/gemini-2.0-flash-001",
			base_url="https://openrouter.ai/api/v1",
			api_key=os.environ['OPENROUTER_API_KEY'],
            temperature=0.1,
    )

	deepseek_llm = LLM(
            model="openrouter/deepseek/deepseek-chat-v3-0324:free",
			base_url="https://openrouter.ai/api/v1",
			api_key=os.environ['OPENROUTER_API_KEY'],
            temperature=0.1,
            config={
                "proxies": PROXY_CONFIG,
                "trust_env": True,
                "verify": False,
                "timeout": 60
            }
    )

	gemini_llm = LLM(
            model="gemini/gemini-2.0-flash",
			base_url="https://generativelanguage.googleapis.com/",
			api_key=os.environ['GEMINI_API_KEY'],
            temperature=0.1,
            config={
                "proxies": PROXY_CONFIG,
                "trust_env": True,
                "verify": False,
                "timeout": 60
            }
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
			llm=self.qwen_llm,
			tools=[VisionTool(model=self.qwen_llm)],
			verbose=True
		)
	
	@agent
	def reply_assistant(self) -> Agent:
		return Agent(
			config=self.agents_config['reply_assistant'],
			verbose=True,
			llm=self.deepseek_llm,
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
	
	@task
	def auto_reply_task(self) -> Task:
		return Task(
			config=self.tasks_config['auto_reply_task'],
			agent=self.reply_assistant(),
			output_file='report.md'
		)
	

	@crew
	def crew(self) -> Crew:
		"""Creates the SocialMediaAutoComment crew"""
		# To learn how to add knowledge sources to your crew, check out the documentation:
		# https://docs.crewai.com/concepts/knowledge#what-is-knowledge

		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=True,
			# process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
		)
