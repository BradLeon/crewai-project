from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from social_media_auto_comment.tools.faiss_retrival_tool import FAISSRetrievalTool
import os

import logging
    # 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 获取知识库文件的绝对路径
def get_knowledge_path(filename):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.abspath(os.path.join(current_dir, "../../../"))
    file_path = os.path.join(src_dir, "knowledge", filename)
    if not os.path.exists(file_path):
        logger.warning(f"Knowledge file not found: {file_path}")
    return file_path

@CrewBase
class CommentsWriter():
    """CommentsWriter crew"""


    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'


    deepseek_llm = LLM(
            model="openrouter/deepseek/deepseek-chat-v3-0324:free",
			base_url="https://openrouter.ai/api/v1",
			api_key=os.environ['OPENROUTER_API_KEY'],
            temperature=0.1,
            config={
                "trust_env": True,
                "verify": False,
                "timeout": 180,  # 增加超时时间到3分钟
                "max_retries": 3,  # 添加重试次数
                "retry_interval": 5,  # 重试间隔秒数
                "fail_on_rate_limit": False,  # 遇到限流时不立即失败
            }
    )

    deepseek_r1_lm = LLM(
            model="openrouter/deepseek/deepseek-r1-zero:free",
			base_url="https://openrouter.ai/api/v1",
			api_key=os.environ['OPENROUTER_API_KEY'],
            temperature=0.1,
    )



	# If you would like to add tools to your agents, you can learn more about it here:
	# https://docs.crewai.com/concepts/agents#agent-tools


    @agent
    def reply_assistant(self) -> Agent:
        return Agent(
			config=self.agents_config['reply_assistant'],
			verbose=True,
			llm=self.deepseek_llm,
			# 临时注释掉知识源，使用RagTool替代
			# knowledge_sources=[product_knowledge_source],
			tools=[FAISSRetrievalTool(file_paths=[
                get_knowledge_path("comment_conversations_corpus.json"),
                get_knowledge_path("product_info.json")
            ])],

		)


	# To learn more about structured task outputs,
	# task dependencies, and task callbacks, check out the documentation:
	# https://docs.crewai.com/concepts/tasks#overview-of-a-task

    @task
    def auto_reply_task(self) -> Task:
        return Task(
			config=self.tasks_config['auto_reply_task'],
			agent=self.reply_assistant(),
			output_file='auto_reply_report.json',
		)


    @crew
    def crew(self) -> Crew:
        """Creates the CommentsWriter crew"""
        return Crew(
			agents=self.agents,
			tasks=self.tasks,
			process=Process.sequential,
			verbose=True
        )
