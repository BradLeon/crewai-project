import os
import re
import requests
import oss2
from typing import Optional
import uuid
from urllib.parse import urlparse, parse_qs
import aiohttp
import asyncio
from playwright.async_api import async_playwright

class VideoProcessor:
    def __init__(self):
        # 获取环境变量，设置默认值防止 None
        access_key_id = os.getenv('BAILIAN_ACCESSKEY_ID')
        access_key_secret = os.getenv('BAILIAN_ACCESSKEY_SECRET')
        oss_endpoint = os.getenv('VIDEO_OSS_ENDPOINT')
        oss_bucket_name = os.getenv('VIDEO_OSS_BUCKET_NAME')
        
        # 验证必要的环境变量
        if not all([access_key_id, access_key_secret, oss_endpoint, oss_bucket_name]):
            raise ValueError(
                "缺少必要的环境变量。请确保设置了以下环境变量：\n"
                "- BAILIAN_ACCESSKEY_ID\n"
                "- BAILIAN_ACCESSKEY_SECRET\n"
                "- VIDEO_OSS_ENDPOINT\n"
                "- VIDEO_OSS_BUCKET_NAME"
            )
            
        # 初始化OSS客户端
        self.auth = oss2.Auth(access_key_id, access_key_secret)
        self.bucket = oss2.Bucket(
            self.auth,
            oss_endpoint,
            oss_bucket_name
        )
        self.bucket_name = oss_bucket_name

    async def get_real_download_url(self, video_url: str) -> Optional[str]:
        """获取视频的真实下载地址"""
        try:
            print(f"正在获取视频下载链接: {video_url}")
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
                    # 访问视频页面
                    await page.goto(video_url)
                    await page.wait_for_load_state('domcontentloaded')
                    
                    # 处理登录弹窗
                    try:
                        close_button = await page.wait_for_selector('div[aria-label="关闭"]', timeout=2000)
                        if close_button:
                            await close_button.click()
                            print("已关闭登录弹窗")
                    except Exception as e:
                        print(f"处理登录弹窗时出错（可以忽略）: {str(e)}")

                    # 等待下载按钮出现并点击
                    print("等待下载按钮加载...")
                    download_button = await page.wait_for_selector('button:has-text("下载")', timeout=10000)
                    if not download_button:
                        raise ValueError("未找到下载按钮")
                    
                    print("点击下载按钮...")
                    await download_button.click()
                    await page.wait_for_timeout(1000)  # 等待下载链接生成
                    
                    # 获取视频下载链接
                    print("获取视频下载链接...")
                    download_url = await page.evaluate('''() => {
                        const videos = Array.from(document.querySelectorAll('video'));
                        for (const video of videos) {
                            if (video.src) {
                                return video.src;
                            }
                            if (video.currentSrc) {
                                return video.currentSrc;
                            }
                        }
                        return null;
                    }''')
                    
                    if not download_url:
                        # 保存调试信息
                        await page.screenshot(path='debug_screenshot.png')
                        content = await page.content()
                        with open('debug_page.html', 'w', encoding='utf-8') as f:
                            f.write(content)
                        raise ValueError("未找到视频下载链接")
                    
                    print(f"成功获取下载链接: {download_url}")
                    return download_url
                    
                except Exception as e:
                    print(f"获取下载链接时出错: {str(e)}")
                    # 保存错误信息
                    await page.screenshot(path='error_screenshot.png')
                    content = await page.content()
                    with open('error_page.html', 'w', encoding='utf-8') as f:
                        f.write(content)
                    return None
                    
                finally:
                    await browser.close()
                    
        except Exception as e:
            print(f"获取下载链接过程中出错: {str(e)}")
            return None

    async def download_video(self, video_url: str, save_path: str) -> bool:
        """下载视频到本地
        
        Args:
            video_url: 视频直链URL
            save_path: 保存路径
            
        Returns:
            bool: 下载是否成功
        """
        try:
            print(f"开始下载视频: {video_url}")
            
            # 设置请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Referer': 'https://www.douyin.com/'
            }
            
            # 确保目标目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # 使用aiohttp下载视频
            async with aiohttp.ClientSession() as session:
                async with session.get(video_url, headers=headers) as response:
                    if response.status != 200:
                        print(f"下载请求失败，状态码: {response.status}")
                        return False
                    
                    # 检查内容类型
                    content_type = response.headers.get('content-type', '')
                    if not content_type.startswith('video/'):
                        print(f"警告：响应的内容类型不是视频: {content_type}")
                    
                    # 下载文件
                    total_size = 0
                    with open(save_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            if chunk:
                                f.write(chunk)
                                total_size += len(chunk)
                                
            print(f"视频下载完成，大小: {total_size / 1024 / 1024:.2f}MB")
            
            # 验证文件
            if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                return True
            else:
                print("下载的文件大小为0或文件不存在")
                return False
                
        except aiohttp.ClientError as e:
            print(f"下载视频时网络错误: {str(e)}")
            return False
        except Exception as e:
            print(f"下载视频时出错: {str(e)}")
            return False

    def upload_to_oss(self, local_path: str, oss_path: str) -> Optional[str]:
        """上传视频到OSS"""
        try:
            print(f"开始上传文件到OSS: {oss_path}")
            
            # 检查本地文件
            if not os.path.exists(local_path):
                print(f"本地文件不存在: {local_path}")
                return None
                
            file_size = os.path.getsize(local_path)
            if file_size == 0:
                print("本地文件大小为0")
                return None
                
            print(f"本地文件大小: {file_size / 1024 / 1024:.2f}MB")
            
            # 上传到OSS
            self.bucket.put_object_from_file(oss_path, local_path)
            
            # 返回OSS链接
            oss_url = f"oss://{self.bucket_name}/{oss_path}"
            print(f"文件上传成功: {oss_url}")
            return oss_url
            
        except oss2.exceptions.OssError as e:
            print(f"OSS操作错误: {str(e)}")
            return None
        except Exception as e:
            print(f"上传到OSS时出错: {str(e)}")
            return None

    def extract_video_id(self, url: str) -> str:
        """从URL中提取或生成视频ID"""
        try:
            # 尝试从URL参数中提取video_id
            if 'video_id=' in url:
                video_id = re.search(r'video_id=([^&]+)', url).group(1)
                return video_id.replace('v', '')  # 移除可能的'v'前缀
            
            # 生成一个基于URL的唯一ID
            import hashlib
            return hashlib.md5(url.encode()).hexdigest()[:16]
            
        except Exception as e:
            print(f"提取视频ID时出错: {str(e)}")
            # 生成一个基于时间戳的ID
            import time
            return f"video_{int(time.time())}"

    async def process_douyin_video(self, video_url: str) -> Optional[str]:
        """处理抖音视频的完整流程"""
        try:
            print(f"开始处理视频: {video_url}")
            
            # 1. 获取视频ID
            video_id = self.extract_video_id(video_url)
            print(f"视频ID: {video_id}")
            
            # 2. 创建临时文件路径
            temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, f"douyin_{video_id}.mp4")
            
            try:
                # 3. 下载视频
                if not await self.download_video(video_url, temp_path):
                    print("视频下载失败")
                    return None
                
                # 4. 上传到OSS
                oss_path = f"aimiaobi/videoAnalysis/{video_id}/{video_id}.mp4"
                oss_url = self.upload_to_oss(temp_path, oss_path)
                if not oss_url:
                    print("视频上传失败")
                    return None
                
                return oss_url
                
            finally:
                # 5. 清理临时文件
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                        print(f"已删除临时文件: {temp_path}")
                except Exception as e:
                    print(f"清理临时文件时出错: {str(e)}")
            
        except Exception as e:
            print(f"处理抖音视频时出错: {str(e)}")
            return None 