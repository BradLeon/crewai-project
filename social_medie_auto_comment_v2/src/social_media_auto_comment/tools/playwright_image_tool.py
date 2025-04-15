from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import base64
from playwright.sync_api import sync_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
import os
import hashlib
from datetime import datetime


class PlaywrightImageInput(BaseModel):
    """Input schema for PlaywrightImageTool."""
    argument: str = Field(..., description="Description of the argument.")

class PlaywrightImageTool(BaseTool):
    name: str = "playwright_image_scraper"
    description: str = "使用 Playwright 加载网页并截图 image_url 页面"

    def _get_cache_filename(self, url: str) -> str:
        """生成基于URL的唯一缓存文件名"""
        cache_dir = os.path.join(os.getcwd(), "screenshot_cache")
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return os.path.join(cache_dir, f"screenshot_{url_hash}.png")

    def _read_cached_image(self, cache_file: str) -> str:
        """读取缓存的图片并返回base64编码"""
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'rb') as f:
                    image_data = f.read()
                    return base64.b64encode(image_data).decode("utf-8")
            return None
        except Exception as e:
            print(f"[❌ Error] Failed to read cached image: {str(e)}")
            return None

    def _run(self, url: str) -> str:
        """使用 Playwright 访问图像页面并返回截图 base64 字符串，同时保存到本地"""
        try:
            cache_file = self._get_cache_filename(url)
            
            # 检查是否存在缓存图片
            cached_base64 = self._read_cached_image(cache_file)
            if cached_base64:
                return f"✅ Using cached screenshot from {cache_file}. Base64 preview: {cached_base64[:100]}..."

            # 如果没有缓存，则下载新图片
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    proxy={
                        "server": "http://127.0.0.1:10080"
                    }
                )
                page = browser.new_page()
                page.goto(url)
                page.wait_for_timeout(3000)

                # 保存截图到本地文件
                page.screenshot(path=cache_file, full_page=True)
                
                # 同时获取base64编码
                screenshot = page.screenshot(full_page=True)
                browser.close()

                base64_image = base64.b64encode(screenshot).decode("utf-8")
                return f"✅ Screenshot captured and saved to {cache_file}. Base64 preview: {base64_image[:100]}..."
        except Exception as e:
            return f"[❌ Error] Failed to capture screenshot: {str(e)}"