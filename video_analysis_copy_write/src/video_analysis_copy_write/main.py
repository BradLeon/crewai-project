#!/usr/bin/env python
from random import randint
import asyncio
from pydantic import BaseModel
from crewai.flow.flow import Flow, listen, start

from .crews.video_analysis_crew import VideoAnalysisCrew, VideoAnalysisResult
from .crews.video_copy_writer_crew import VideoCopyWriterCrew
from .utils.video_processor import VideoProcessor



class VideoCopyWriteState(BaseModel):
    sentence_count: int = 1
    poem: str = ""
    raw_video_share_text: str = ""  # 原始分享文本
    douyin_url: str = ""  # 抖音短链接
    target_video_url: str = ""  # 最终的OSS链接
    account_position: str = ""
    video_topic: str = ""
    target_audience: str = ""
    video_story_summary: str = ""
    video_story_board: str = ""
    video_analysis_report: str = ""


class VideoCopyWriteFlow(Flow[VideoCopyWriteState]):

    @start()
    async def get_user_input(self):
        '''获取用户输入信息
        
        
        self.state.target_video_url = "oss://default/aimiaobi-service-prod/aimiaobi/videoAnalysis/1290225910686270_10695028/1290225910686270_1290225910686270_ae7cff20924c43c6818d727ceb694b2c.mp4"
        self.state.account_position = "家具家装领域专业买手IP"
        self.state.video_topic = "苏州地区的高品位全屋家具定制工厂探店"
        self.state.target_audience = "追求性价比和一站式解决便捷的装修业主"
        
        '''
        try:
            while True:
                # 获取视频分享文本
                share_text = input("请输入视频分享文本: ").strip()
                if not share_text:
                    print("错误: 分享文本不能为空")
                    continue
                
                # 保存原始分享文本
                self.state.raw_video_share_text = share_text
                
                # 获取账号定位
                account_positioning = input("请输入账号定位: ").strip()
                if not account_positioning:
                    print("错误: 账号定位不能为空")
                    continue
                    
                # 获取主题
                topic = input("请输入主题: ").strip()
                if not topic:
                    print("错误: 主题不能为空")
                    continue
                    
                # 获取目标受众
                target_audience = input("请输入目标受众: ").strip()
                if not target_audience:
                    print("错误: 目标受众不能为空")
                    continue
                
                # 所有输入都有效，保存并退出循环
                self.state.account_position = account_positioning
                self.state.video_topic = topic
                self.state.target_audience = target_audience
                break
                
        except Exception as e:
            print(f"获取用户输入时出错: {str(e)}")
            raise

    @listen(get_user_input)
    async def process_video_url(self):
        '''处理视频链接'''
        try:
            print("开始处理视频链接...")
            
            # 1. 从分享文本中提取抖音链接
            import re
            douyin_urls = re.findall(r'https://v\.douyin\.com/[a-zA-Z0-9\-]+/?', self.state.raw_video_share_text)
            if not douyin_urls:
                raise ValueError("未找到有效的抖音链接")
            
            self.state.douyin_url = douyin_urls[0]
            print(f"提取到抖音链接: {self.state.douyin_url}")
            
            # 2. 使用 Playwright 打开链接获取视频
            from playwright.async_api import async_playwright
            import time
            
            video_processor = VideoProcessor()
            
            async with async_playwright() as p:
                # 配置浏览器选项
                browser = await p.chromium.launch(
                    headless=False,  # 设置为 False 以便调试
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--no-sandbox',
                    ]
                )
                
                # 创建上下文并设置更多选项
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                )
                
                page = await context.new_page()
                
                try:
                    # 访问抖音链接
                    print("正在访问抖音链接...")
                    await page.goto(self.state.douyin_url)
                    
                    # 等待页面加载完成
                    print("等待页面加载...")
                    await page.wait_for_load_state('domcontentloaded')
                    
                    # 获取重定向后的URL
                    current_url = page.url
                    print(f"当前页面URL: {current_url}")
                    
                    # 处理登录弹窗
                    try:
                        # 等待关闭按钮出现并点击
                        close_button = await page.wait_for_selector('div[aria-label="关闭"]', timeout=2000)
                        if close_button:
                            await close_button.click()
                            print("已关闭登录弹窗")
                    except Exception as e:
                        print(f"处理登录弹窗时出错（可以忽略）: {str(e)}")
                    
                    # 调试：打印页面上所有video元素
                    print("检查页面上的视频元素...")
                    video_elements = await page.query_selector_all('video')
                    print(f"找到 {len(video_elements)} 个视频元素")
                    
                    # 等待视频元素加载
                    print("等待视频元素加载...")
                    await page.wait_for_selector('video', state='attached', timeout=10000)
                    
                    # 获取所有可能的视频元素
                    video_info = await page.evaluate('''() => {
                        const videos = Array.from(document.querySelectorAll('video'));
                        return videos.map(video => ({
                            src: video.src,
                            currentSrc: video.currentSrc,
                            className: video.className,
                            id: video.id,
                            parentClass: video.parentElement ? video.parentElement.className : null
                        }));
                    }''')
                    print("视频元素信息:", video_info)
                    
                    # 尝试获取视频URL
                    video_url = None
                    if video_info:
                        for info in video_info:
                            if info.get('src'):
                                video_url = info['src']
                                break
                            elif info.get('currentSrc'):
                                video_url = info['currentSrc']
                                break
                    
                    if not video_url:
                        # 保存页面内容以便调试
                        content = await page.content()
                        with open('debug_page.html', 'w', encoding='utf-8') as f:
                            f.write(content)
                        raise ValueError("未找到视频源地址")
                    
                    print(f"找到视频源地址: {video_url}")
                    
                    # 处理视频并上传到OSS
                    print("开始处理视频并上传到OSS...")
                    oss_url = await video_processor.process_douyin_video(video_url)
                    if not oss_url:
                        raise ValueError("视频处理失败")
                    
                    print(f"视频处理完成，上传到OSS: {oss_url}")
                    self.state.target_video_url = oss_url
                    
                except Exception as e:
                    print(f"处理视频时出错: {str(e)}")
                    # 保存更多调试信息
                    await page.screenshot(path='error_screenshot.png', full_page=True)
                    content = await page.content()
                    with open('error_page.html', 'w', encoding='utf-8') as f:
                        f.write(content)
                    raise
                
                finally:
                    await browser.close()
            
            print("视频链接处理完成")
            
        except Exception as e:
            print(f"处理视频链接时出错: {str(e)}")
            raise

    @listen(process_video_url)
    async def video_analysis(self):
        '''执行视频分析'''
        try:
            print("开始视频分析...")
            video_analysis_result = await VideoAnalysisCrew().run(self.state.target_video_url)
            if video_analysis_result:
                self.state.video_story_summary = video_analysis_result.get_video_story_summary()
                self.state.video_story_board = video_analysis_result.get_video_story_board()
                self.state.video_analysis_report = video_analysis_result.get_video_analysis_report()
            else:
                print("video_analysis_result is None")
                raise Exception("video_analysis_result is None")
            
            print("视频分析完成")
            
        except Exception as e:
            print(f"视频分析过程中出错: {str(e)}")
            raise

    @listen(video_analysis)
    def video_copy_write(self):
        '''
        2. 根据爆款视频生成视频文案
        '''
        print("video copy write")

        result = (
            VideoCopyWriterCrew()
            .crew()
            .kickoff(inputs={"account_position": self.state.account_position,
                            "video_topic": self.state.video_topic,
                            "target_audience": self.state.target_audience,
                            "video_story_summary": self.state.video_story_summary,
                            "video_story_board": self.state.video_story_board,
                            "video_analysis_report": self.state.video_analysis_report})
        )

    async def run(self):
        '''
        执行视频分析和文案生成的主流程
        
        步骤：
        1. 获取用户输入信息
        2. 执行视频分析
        3. 生成视频文案
        
        返回：
        - 生成的视频文案内容
        '''
        try:
            print("开始执行视频分析和文案生成流程...")
            
            # 获取用户输入
            print("正在获取用户输入...")
            await self.get_user_input()
            print("用户输入获取完成")

            print("开始处理视频链接...")
            await self.process_video_url()
            print("视频链接处理完成")

            '''
            # 执行视频分析
            print("开始视频分析...")
            await self.video_analysis()
            print("视频分析完成")
            
            # 生成视频文案
            print("开始生成视频文案...")
            result = self.video_copy_write()
            print("视频文案生成完成")
            
            return result
            '''
        except Exception as e:
            print(f"执行过程中出现错误: {str(e)}")
            raise


def kickoff():
    '''
    启动视频分析和文案生成流程
    
    流程说明：
    1. 获取用户输入（视频链接、账号定位、选题、目标受众）
    2. 调用视频分析服务，分析视频内容
    3. 根据分析结果生成视频文案
    
    异常处理：
    - 如果视频分析失败，会抛出异常
    - 如果用户输入无效，会提示重新输入
    '''
    try:
        poem_flow = VideoCopyWriteFlow()
        asyncio.run(poem_flow.run())
    except asyncio.CancelledError:
        print("流程被取消")
    except Exception as e:
        print(f"执行过程中出现错误: {str(e)}")
        raise


def plot():
    poem_flow = VideoCopyWriteFlow()
    poem_flow.plot()


if __name__ == "__main__":
    kickoff()
