# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

import os
import sys
import json
from typing import List, Dict
import random
import requests

from alibabacloud_quanmiaolightapp20240801.client import Client as QuanMiaoLightApp20240801Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_quanmiaolightapp20240801 import models as quan_miao_light_app_20240801_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient
from alibabacloud_credentials.client import Client as CredClient
from alibabacloud_credentials.models import Config as CreConfig



class VideoAnalysisResult:
    def __init__(self, video_analysis_report, video_story_summary, video_story_board, video_understand_report,
                 video_analysis_report_token, video_story_summary_token, video_story_board_token, video_understand_report_token,
                 snapshot_url_list):
        self.video_analysis_report = video_analysis_report
        self.video_story_summary = video_story_summary
        self.video_story_board = video_story_board
        self.video_understand_report = video_understand_report
        self.video_analysis_report_token = video_analysis_report_token
        self.video_story_summary_token = video_story_summary_token
        self.video_story_board_token = video_story_board_token
        self.video_understand_report_token = video_understand_report_token
        self.snapshot_url_list = snapshot_url_list

    def get_video_analysis_report(self):
        return self.video_analysis_report

    def get_video_story_summary(self):
        return self.video_story_summary 

    def get_video_story_board(self):
        return self.video_story_board

    def get_video_understand_report(self):
        return self.video_understand_report 

    def get_snapshot_url_list(self):
        return self.snapshot_url_list

    def get_video_analysis_report_token(self):
        return self.video_analysis_report_token     

    def get_video_story_summary_token(self):
        return self.video_story_summary_token

    def get_video_story_board_token(self):
        return self.video_story_board_token

    def get_video_understand_report_token(self):
        return self.video_understand_report_token


class VideoAnalysisCrew:
    def __init__(self):
        # 获取当前文件所在目录的路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.prompts_config = os.path.join(current_dir, "config", "prompts.json")
        # 加载prompts配置
        with open(self.prompts_config, 'r', encoding='utf-8') as f:
            self.prompts = json.load(f)
        self.workspace_id = 'llm-gkxhlygbzd1di15t'
    @staticmethod
    def create_client() -> QuanMiaoLightApp20240801Client:
        """
        使用凭据初始化账号Client
        @return: Client
        @throws Exception
        """
        # 使用AK 初始化Credentials Client。
        credentialsConfig = CreConfig(
            # 凭证类型。
            type='access_key',
            # 设置为AccessKey ID值。
            access_key_id=os.environ.get('BAILIAN_ACCESSKEY_ID'),
            # 设置为AccessKey Secret值。
            access_key_secret=os.environ.get('BAILIAN_ACCESSKEY_SECRET'),
        )
        credentialClient = CredClient(credentialsConfig)

        # 工程代码建议使用更安全的无AK方式，凭据配置方式请参见：https://help.aliyun.com/document_detail/378659.html。
        config = open_api_models.Config(
            # 通过credentialClient获取credential
            credential=credentialClient
        )
        # Endpoint 请参考 https://api.aliyun.com/product/QuanMiaoLightApp
        config.endpoint = f'quanmiaolightapp.cn-beijing.aliyuncs.com'
        return QuanMiaoLightApp20240801Client(config)

    @staticmethod
    def submit_video_analysis_task(self,
                                   video_url: str
    ) -> None:
        video_url = 'oss://default/aimiaobi-service-prod/aimiaobi/videoAnalysis/1290225910686270_10695028/1290225910686270_1290225910686270_ae7cff20924c43c6818d727ceb694b2c.mp4'
        client = self.create_client()

        text_process_tasks_0 = quan_miao_light_app_20240801_models.SubmitVideoAnalysisTaskRequestTextProcessTasks(
            model_id='qwen-max-latest',
            model_custom_prompt_template=json.loads(self.prompts_config).get("video_analysis_report_prompt")
        )

        text_process_tasks_1 = quan_miao_light_app_20240801_models.SubmitVideoAnalysisTaskRequestTextProcessTasks(
            model_id='qwen-max-latest',
            model_custom_prompt_template=json.loads(self.prompts_config).get("video_story_summary_prompt")
        )
        text_process_tasks_2 = quan_miao_light_app_20240801_models.SubmitVideoAnalysisTaskRequestTextProcessTasks(
            model_id='qwen-max-latest',
            model_custom_prompt_template=json.loads(self.prompts_config).get("video_story_board_prompt")
        )

        frame_sample_method = quan_miao_light_app_20240801_models.SubmitVideoAnalysisTaskRequestFrameSampleMethod(
            method_name='standard'
        )
        submit_video_analysis_task_request = quan_miao_light_app_20240801_models.SubmitVideoAnalysisTaskRequest(
            video_url=video_url,
            video_model_custom_prompt_template=json.loads(self.prompts_config).get("video_understand_prompt"),
            video_model_id='qwen-vl-max-latest',
            model_id='qwen-max-latest',
            generate_options=[
                'videoMindMappingGenerate',
                'videoAnalysis',
                'videoGenerate'
            ],
            language='chinese', # 目前只支持中文视频拆解
            frame_sample_method=frame_sample_method,
            text_process_tasks=[
                text_process_tasks_0,
                text_process_tasks_1,
                text_process_tasks_2
            ]
        )
        runtime = util_models.RuntimeOptions()
        headers = {}
        try:
            # 复制代码运行请自行打印 API 的返回值
            res =client.submit_video_analysis_task_with_options(self.workspace_id, submit_video_analysis_task_request, headers, runtime)
            print(f"response of submit_video_analysis_task: {res.body}")
            print("================================================")
            print(f"type of res.body.data   : {type(res.body.data)}")
            if res.body.http_status_code == 200:
                return res.body.data.task_id
            else:
                print(f"some thing wrong, error message: {res.body.message}")
        except Exception as error:
            # 此处仅做打印展示，请谨慎对待异常处理，在工程项目中切勿直接忽略异常。
            # 错误 message
            print(error)
            print(res.message)
            # 诊断地址
            print(res.data.get("Recommend"))
            UtilClient.assert_as_string(error.message)

    async def submit_video_analysis_task_async(self, video_url: str) -> None:
        client = self.create_client()
        text_process_tasks_0 = quan_miao_light_app_20240801_models.SubmitVideoAnalysisTaskRequestTextProcessTasks(
            model_id='qwen-max-latest',
            model_custom_prompt_template=self.prompts.get("video_analysis_report_prompt")
        )

        text_process_tasks_1 = quan_miao_light_app_20240801_models.SubmitVideoAnalysisTaskRequestTextProcessTasks(
            model_id='qwen-max-latest',
            model_custom_prompt_template=self.prompts.get("video_story_summary_prompt")
        )
        text_process_tasks_2 = quan_miao_light_app_20240801_models.SubmitVideoAnalysisTaskRequestTextProcessTasks(
            model_id='qwen-max-latest',
            model_custom_prompt_template=self.prompts.get("video_story_board_prompt")
        )

        frame_sample_method = quan_miao_light_app_20240801_models.SubmitVideoAnalysisTaskRequestFrameSampleMethod(
            method_name='standard'
        )

        submit_video_analysis_task_request = quan_miao_light_app_20240801_models.SubmitVideoAnalysisTaskRequest(
            video_url=video_url,
            video_model_custom_prompt_template=self.prompts.get("video_understand_prompt"),
            video_model_id='qwen-vl-max-latest',
            model_id='qwen-max-latest',
            generate_options=[
                'videoMindMappingGenerate',
                'videoAnalysis',
                'videoGenerate'
            ],
            language='chinese', # 目前只支持中文视频
            frame_sample_method=frame_sample_method,
            text_process_tasks=[
                text_process_tasks_0,
                text_process_tasks_1,
                text_process_tasks_2
            ]
        )
        runtime = util_models.RuntimeOptions()
        headers = {}
        try:
            # 复制代码运行请自行打印 API 的返回值
            res = await client.submit_video_analysis_task_with_options_async(self.workspace_id, submit_video_analysis_task_request, headers, runtime)
            print(f"response of submit_video_analysis_task: {res.body}")
            print("================================================")
            print(f"type of res.body.data   : {type(res.body.data)}")
            if res.body.http_status_code == 200:
                return res.body.data.task_id
            else:
                print(f"some thing wrong, error message: {res.body.message}")
        except Exception as error:
            # 此处仅做打印展示，请谨慎对待异常处理，在工程项目中切勿直接忽略异常。
            # 错误 message
            print(error)
            print(res.message)
            # 诊断地址
            print(res.data.get("Recommend"))
     

    @staticmethod
    def get_video_analysis_task(self, task_id: str
    ) -> None:
        client = self.create_client()
        get_video_analysis_task_request = quan_miao_light_app_20240801_models.GetVideoAnalysisTaskRequest(
            task_id=task_id
        )
        runtime = util_models.RuntimeOptions()
        headers = {}
        try:
            # 复制代码运行请自行打印 API 的返回值
            res = client.get_video_analysis_task_with_options(self.workspace_id, get_video_analysis_task_request, headers, runtime)
            #print(f"response of get_video_analysis_task_with_options: {res.body}")
            #print("================================================")
            #print(f"type of res.body.data   : {type(res.body.data)}")
            if res.body.http_status_code == 200:
                return res.body.data.task_id
            else:
                print(f"some thing wrong, error message: {res.message}")
        except Exception as error:
            print(error)
            print(res.message)
            # 诊断地址
            print(res.data.get("Recommend"))
            # 此处仅做打印展示，请谨慎对待异常处理，在工程项目中切勿直接忽略异常。
            # 错误 message
      
    

    async def get_video_analysis_task_async(self, task_id: str) -> None:
        client = self.create_client()
        get_video_analysis_task_request = quan_miao_light_app_20240801_models.GetVideoAnalysisTaskRequest(
            task_id=task_id
        )
        runtime = util_models.RuntimeOptions()
        headers = {}
        
        # 轮询等待任务完成
        while True:
            try:
                res = await client.get_video_analysis_task_with_options_async(self.workspace_id, get_video_analysis_task_request, headers, runtime)
                #print(f"response of get_video_analysis_task: {res.body}")
                #print("================================================")
                #print(f"type of res.body.data   : {type(res.body.data)}")
                
                if res.body.http_status_code == 200:
                    # 检查任务状态
                    task_status = res.body.data.task_status
                    if task_status == "SUCCEEDED" or task_status == "SUCCESSED":
                        return res.body.data
                    elif task_status == "FAILED":
                        print(f"Task failed: {res.body.message}")
                        return None
                    elif task_status == "RUNNING" or task_status == "PENDING":
                        print("Task is still running, waiting...")
                        await asyncio.sleep(5)  # 等待5秒后再次查询
                        continue
                    else:
                        print(f"Unknown task status: {task_status}")
                        return None
                else:
                    print(f"Request failed: {res.body.message}")
                    return None
            except Exception as error:
                print(f"Error occurred: {str(error)}")
                return None
            
    def format_result_json_file_url(self, result_json_file_url: str) -> List[str]:
        try:
            # 下载JSON文件
            response = requests.get(result_json_file_url)
            if response.status_code != 200:
                print(f"Failed to download JSON file from {result_json_file_url}")
                return []

            # 解析JSON内容
            json_data = response.json()
            snapshot_url_list = []

            # 获取payload数据
            payload = json_data.get("payload", {})
            if not payload:
                print("No payload data in JSON")
                return []

            # 获取output数据
            output = payload.get("output", {})
            if not output:
                print("No output data in payload")
                return []

            # 获取videoShotSnapshotResult数据
            video_shot_snapshot_result = output.get("videoShotSnapshotResult", {})
            if not video_shot_snapshot_result:
                print("No videoShotSnapshotResult data in output")
                return []

            # 获取videoShots数据
            video_shots = video_shot_snapshot_result.get("videoShots", [])
            for video_shot in video_shots:
                # 获取每个shot的snapshots
                snapshots = video_shot.get("videoSnapshots", [])
                if snapshots:
                    # 从每个shot随机选择一张截图
                    random_snapshot = random.choice(snapshots)
                    snapshot_url = random_snapshot.get("url")
                    if snapshot_url:
                        snapshot_url_list.append(snapshot_url)

            print(f"Successfully extracted {len(snapshot_url_list)} snapshot URLs")
            return snapshot_url_list
        except requests.RequestException as e:
            print(f"Network error when downloading JSON file: {str(e)}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON content: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error in format_result_json_file_url: {str(e)}")
            return []

    def format_video_analysis_result(self, task_result: quan_miao_light_app_20240801_models.GetVideoAnalysisTaskResponseBodyData) -> VideoAnalysisResult:
        try:
            if task_result is None:
                print("task_result is None")
                return None
                
            # 获取payload数据
            payload = task_result.payload
            if not payload or not payload.output:
                print("No output data in task result")
                return None

            # 文生文任务处理结果(model: qwen-max-latest)
            video_generate_results = payload.output.video_generate_results
            if not video_generate_results:
                print("No video generate results")
                return None

            result_size = len(video_generate_results)
            print(f"result_size of video_generate_results: {result_size}")
            
       
            # 分析报告
            video_analysis_report = video_generate_results[0].text if result_size > 0 else ""
            video_analysis_report_token = video_generate_results[0].usage.total_tokens if result_size > 0 else 0

            # 剧情概述
            video_story_summary = video_generate_results[1].text if result_size > 1 else ""
            video_story_summary_token = video_generate_results[1].usage.total_tokens if result_size > 1 else 0

            # 分镜脚本
            video_story_board = video_generate_results[2].text if result_size > 2 else ""
            video_story_board_token = video_generate_results[2].usage.total_tokens if result_size > 2 else 0
            
            # 视频->抽帧->图片理解->文字 任务处理结果(model: qwen-vl-max-latest)
            video_analysis_result = payload.output.video_analysis_result
            video_understand_report = video_analysis_result.text if video_analysis_result else ""
            video_understand_report_token = video_analysis_result.usage.total_tokens if video_analysis_result else 0

            # 获取result_json_file_url
            result_json_file_url = payload.output.result_json_file_url
            
            # 解析result_json_file_url获取snapshot_url_list
            snapshot_url_list = self.format_result_json_file_url(result_json_file_url)

            video_analysis_result = VideoAnalysisResult(
                video_analysis_report, 
                video_story_summary,
                video_story_board, 
                video_understand_report,            
                video_analysis_report_token, 
                video_story_summary_token, 
                video_story_board_token, 
                video_understand_report_token,
                snapshot_url_list
            )
            
            return video_analysis_result
        except Exception as e:
            print(f"format_video_analysis_result error: {str(e)}")
            return None
    
    async def run(self, video_url: str):
        try:
            # 提交任务
            '''
            task_id = await self.submit_video_analysis_task_async(video_url=video_url)
            if not task_id:
                print("Failed to submit task")
                return None
                
            print(f"Task submitted successfully, task_id: {task_id}")
            '''
            task_id = '5ca3606b8f814ee2b6aa30d8bac91934'
            # 等待任务完成并获取结果
            task_result = await self.get_video_analysis_task_async(task_id=task_id)
            if not task_result:
                print("Failed to get task result")
                return None
                
            # 格式化结果
            format_video_analysis_result = self.format_video_analysis_result(task_result)
            if format_video_analysis_result:
                # print("video_analysis_result:" ,json.dumps(format_video_analysis_result, default=lambda o: o.__dict__, indent=4))
                
                # 将结果缓存到文件
                try:
                    with open('video_analysis_result.json', 'w', encoding='utf-8') as f:
                        json.dump(format_video_analysis_result.__dict__, f, ensure_ascii=False, indent=4)
                    print("Analysis result has been cached to video_analysis_result.json")
                except Exception as e:
                    print(f"Failed to cache analysis result: {str(e)}")
            
            return format_video_analysis_result
        except Exception as e:
            print(f"Error in run: {str(e)}")
            return None
        

if __name__ == '__main__':
    import asyncio
    asyncio.run(VideoAnalysisCrew().run('oss://default/aimiaobi-service-prod/aimiaobi/videoAnalysis/1290225910686270_10695028/1290225910686270_1290225910686270_ae7cff20924c43c6818d727ceb694b2c.mp4'))


