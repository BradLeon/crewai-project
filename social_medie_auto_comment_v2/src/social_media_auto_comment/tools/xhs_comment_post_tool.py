# xhs_comment_post_tool.py
import os
import sys
import json
import logging
import asyncio
import time
from typing import Optional, Dict, Any, List
from playwright.async_api import BrowserContext, BrowserType, Page, async_playwright

current_path = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_path, '..', 'config')
utils_path = os.path.join(current_path, '..', 'utils')
sys.path.append(current_path)
sys.path.append(config_path)
sys.path.append(utils_path)

from xhs_client import XiaoHongShuClient
from xhs_login import XiaoHongShuLogin
from xhs_help import convert_cookies
from path_utils import get_lib_path
import base_config as config

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("xhs_tool.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("xhs_tool")

# Cookie 文件路径
COOKIE_FILE = os.path.join(current_path, 'xhs_cookies.json')

class XhsCommentPostTool:
    """
    小红书评论发布工具，简单实现初始化浏览器和发布评论功能
    """

    def __init__(self):
        """初始化属性"""
        self.index_url = "https://www.xiaohongshu.com"
        # self.user_agent = utils.get_user_agent()
        self.user_agent = config.UA if config.UA else "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        # 私有属性
        self._browser_context = None
        self._page = None
        self._playwright = None
        self._xhs_client = None
        self._initialized = False
        self._cookies = None


    async def start(self):
        """启动浏览器"""
        try:
            playwright_proxy, httpx_proxy = None, None
            self._playwright = await async_playwright().start()
            chromium = self._playwright.chromium

            self._browser_context = await self.launch_browser(
                chromium, None, self.user_agent, headless=config.HEADLESS
            )

            # 注入stealth.min.js
            await self._browser_context.add_init_script(path=get_lib_path("stealth.min.js"))
            # add webId cookie to avoid sliding captcha
            await self._browser_context.add_cookies(
                [
                    {
                        "name": "webId",
                        "value": "xxx123",
                        "domain": ".xiaohongshu.com",
                        "path": "/",
                    }
                ]
            )
            self._context_page = await self._browser_context.new_page()
            await self._context_page.goto(self.index_url)

            # 创建客户端和尝试登录
            self._xhs_client = await self.create_xhs_client(httpx_proxy)
            login_successful = await self._xhs_client.pong()
                            # 如果启用了保存登录状态但当前没有登录成功，尝试从保存的cookies登录
            if not login_successful and config.SAVE_LOGIN_STATE:
                login_obj = XiaoHongShuLogin(
                    login_type="cookie",
                    login_phone="",
                    browser_context=self._browser_context,
                    context_page=self._context_page,
                    cookie_str=config.COOKIES,
                )
                # 尝试加载保存的cookies
                cookies = await login_obj.load_saved_cookies()
                if cookies:
                    await self._browser_context.add_cookies(cookies)
                    await self._context_page.reload()
                    # 更新客户端cookies
                    await self._xhs_client.update_cookies(browser_context=self._browser_context)
                    login_successful = await self._xhs_client.pong()

            # 如果仍未登录成功，使用配置的登录方式
            if not login_successful:
                login_obj = XiaoHongShuLogin(
                    login_type=config.LOGIN_TYPE,
                    login_phone="",
                    browser_context=self._browser_context,
                    context_page=self._context_page,
                    cookie_str=config.COOKIES,
                )
                await login_obj.begin()
                await self._xhs_client.update_cookies(browser_context=self._browser_context)

                # 如果启用了保存登录状态，保存cookies
                if config.SAVE_LOGIN_STATE:
                    await login_obj.save_cookies()

            self._initialized = True
            logger.info("初始化完成")

        except Exception as e:
            logger.error(f"启动浏览器失败: {e}", exc_info=True)
            raise

    async def create_xhs_client(self, httpx_proxy: Optional[str]) -> XiaoHongShuClient:
        """Create xhs client"""
        logger.info(
            "[XiaoHongShuCrawler.create_xhs_client] Begin create xiaohongshu API client ..."
        )
        cookie_str, cookie_dict = convert_cookies(
            await self._browser_context.cookies()
        )

        # 添加更多的请求头，使请求更接近真实浏览器
        headers = {
            "User-Agent": self.user_agent,
            "Cookie": cookie_str,
            "Origin": "https://www.xiaohongshu.com",
            "Referer": "https://www.xiaohongshu.com",
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "sec-ch-ua": '"Google Chrome";v="133", "Not(A:Brand";v="8", "Chromium";v="133"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

        xhs_client_obj = XiaoHongShuClient(
            proxies=httpx_proxy,
            headers=headers,
            playwright_page=self._context_page,
            cookie_dict=cookie_dict,
        )
        return xhs_client_obj

    async def launch_browser(
        self,
        chromium: BrowserType,
        playwright_proxy: Optional[Dict],
        user_agent: Optional[str],
        headless: bool = True
    ) -> BrowserContext:
        """Launch browser and create browser context"""
        logger.info("[XiaoHongShuCrawler.launch_browser] Begin launch chromium browser ...")

        if config.SAVE_LOGIN_STATE:
            # feat issue #14
            # we will save login state to avoid login every time
            user_data_dir = os.path.join(
                os.getcwd(), "browser_data", config.USER_DATA_DIR % config.PLATFORM
            )  # type: ignore
            browser_context = await chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                accept_downloads=True,
                headless=headless,
                proxy=playwright_proxy,  # type: ignore
                viewport={"width": 1920, "height": 1080},
                user_agent=user_agent,
            )
            return browser_context

        else:
            browser = await chromium.launch(headless=headless, proxy=playwright_proxy)  # type: ignore
            browser_context = await browser.new_context(
                viewport={"width": 1920, "height": 1080}, user_agent=user_agent
            )
            return browser_context


    async def post_comment(self, note_id: str, content: str, target_comment_id: Optional[str] = None) -> Dict[str, Any]:
        """
        发布评论

        Args:
            note_id: 笔记ID
            content: 评论内容
            target_comment_id: 要回复的评论ID，不提供则发表主评论

        Returns:
            Dict: 评论结果
        """
        try:
            # 确保已初始化
            if not self._initialized:
                await self.start()

            logger.info(f"发布评论: note_id={note_id}, content={content}, target_comment_id={target_comment_id}")

            # 根据是发布主评论还是回复评论选择不同API
            if target_comment_id:
                logger.info(f"回复评论 {target_comment_id}")
                coroutine = self._xhs_client.comment_user(note_id, target_comment_id, content)
            else:
                logger.info(f"发布主评论")
                coroutine = self._xhs_client.comment_note(note_id, content)

            # 等待coroutine完成并获取结果
            result = await coroutine

            # 格式化打印结果
            logger.info("评论发布成功, API调用结果:")
            logger.info(json.dumps(result, ensure_ascii=False, indent=2))

            return {
                "success": True,
                "data": result,
                "message": "评论发布成功"
            }

        except Exception as e:
            logger.error(f"评论发布失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"评论发布失败: {str(e)}"
            }

    async def cleanup(self):
        """清理资源"""
        logger.info("清理资源...")

        if self._browser_context:
            await self._browser_context.close()
            self._browser_context = None

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

        self._page = None
        self._xhs_client = None
        self._initialized = False

        logger.info("资源清理完成")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.cleanup()


# 主函数示例
async def main():
    """测试示例"""
    tool = XhsCommentPostTool()

    try:
        logger.info("开始测试评论发布功能...")

        # 发布主评论测试
        logger.info("\n1. 测试发布主评论...")
        result1 = await tool.post_comment(
            note_id="6475ddce0000000012032250",
            content="这个笔记很有价值，学习了！[鼓掌R]"
        )
        logger.info(f"主评论发布结果:\n{json.dumps(result1, ensure_ascii=False, indent=2)}")

        # 等待一段时间再发下一条评论
        await asyncio.sleep(3)

        # 回复评论测试
        logger.info("\n2. 测试回复评论...")
        result2 = await tool.post_comment(
            note_id="67c97579000000000900f651",
            content="银河六律的香味确实很助眠[心动R]",
            target_comment_id="67cd158a000000001802951b"  # 回复 momo 的评论
        )
        logger.info(f"回复评论发布结果:\n{json.dumps(result2, ensure_ascii=False, indent=2)}")

    except Exception as e:
        logger.error(f"测试过程中出现错误: {e}", exc_info=True)
    finally:
        # 确保清理资源
        logger.info("\n清理资源...")
        await tool.cleanup()
        logger.info("测试完成")


if __name__ == "__main__":
    # 设置日志级别为 DEBUG 以查看更多信息
    logging.getLogger("xhs_tool").setLevel(logging.DEBUG)

    # 运行测试
    print("开始运行测试...")
    asyncio.run(main())