# xhs_comment_post_tool.py
import os
import sys
import json
import logging
import asyncio
import time
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, BrowserContext

current_path = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_path, '..', 'config')
sys.path.append(current_path)
sys.path.append(config_path)

from xhs_client import XiaoHongShuClient
from xhs_login import XiaoHongShuLogin
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
        self.user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

        # 私有属性
        self._browser_context = None
        self._page = None
        self._playwright = None
        self._xhs_client = None
        self._initialized = False
        self._cookies = None

    async def _load_cookies(self) -> bool:
        """从文件加载cookies"""
        try:
            if os.path.exists(COOKIE_FILE):
                with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
                    self._cookies = json.load(f)
                    logger.info("成功加载已保存的cookies")
                    return True
            return False
        except Exception as e:
            logger.error(f"加载cookies失败: {e}")
            return False

    async def _save_cookies(self):
        """保存cookies到文件"""
        try:
            if self._browser_context:
                cookies = await self._browser_context.cookies()
                with open(COOKIE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(cookies, f, ensure_ascii=False, indent=2)
                logger.info("成功保存cookies")
        except Exception as e:
            logger.error(f"保存cookies失败: {e}")

    async def _check_login_status(self) -> bool:
        """
        通过检查页面元素判断是否已登录
        Returns:
            bool: True 表示已登录，False 表示未登录
        """
        try:
            # 检查是否存在"我"的导航元素（已登录状态）
            try:
                # 使用准确的 XPath
                me_nav = await self._page.wait_for_selector(
                    "xpath=//*[@id='global']/div[2]/div[1]/ul/li[4]/div/a",
                    timeout=3000
                )
                if me_nav:
                    # 进一步验证元素的文本内容
                    element_text = await me_nav.text_content()
                    if element_text and "我" in element_text:
                        logger.info("检测到'我'的导航元素，已登录状态")
                        return True

            except Exception as e:
                logger.debug(f"使用主XPath查找'我'元素失败: {e}")
                # 如果主XPath失败，尝试备用选择器
                try:
                    me_nav = await self._page.wait_for_selector("text=我", timeout=2000)
                    if me_nav:
                        logger.info("通过文本内容检测到'我'元素，已登录状态")
                        return True
                except:
                    pass

            # 检查是否存在登录按钮（未登录状态）
            try:
                login_button = await self._page.wait_for_selector(
                "xpath=//*[@id='app']/div[1]/div[2]/div[1]/ul/div[1]/button",
                timeout=5000
                )
                if login_button:
                    logger.info("检测到登录按钮，未登录状态")
                    return False
            except Exception as e:
                logger.debug(f"查找登录按钮时出现异常: {e}")

            # 如果无法确定状态，检查页面URL或其他特征
            current_url = self._page.url
            if "login" in current_url:
                logger.info("当前在登录页面，未登录状态")
                return False

            logger.warning("无法确定登录状态，默认为未登录")
            return False

        except Exception as e:
            logger.warning(f"检查登录状态时发生错误: {e}")
            return False

    async def initialize(self):
        """初始化浏览器和登录"""
        if self._initialized:
            return

        try:
            logger.info("启动Playwright...")
            self._playwright = await async_playwright().start()

            logger.info("启动浏览器...")
            browser = await self._playwright.chromium.launch(
                headless=config.HEADLESS,
                timeout=60000
            )

            self._browser_context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=self.user_agent
            )

            # 尝试加载已保存的cookies
            if await self._load_cookies():
                await self._browser_context.add_cookies(self._cookies)
                logger.info("已加载保存的cookies")

            # 创建页面并导航
            self._page = await self._browser_context.new_page()
            await self._page.goto(self.index_url)

            # 创建API客户端
            self._xhs_client = await self._create_client()

            # 检查登录状态
            login_successful = await self._check_login_status()
            if login_successful:
                logger.info("使用已保存的cookies登录成功")
                self._initialized = True
                return

            # 如果登录失败，才进行二维码登录
            logger.info("需要登录，开始登录流程...")
            login_handler = XiaoHongShuLogin(
                login_type=config.LOGIN_TYPE,
                login_phone="",
                browser_context=self._browser_context,
                context_page=self._page,
                cookie_str=config.COOKIES
            )
            await login_handler.begin()
            await self._xhs_client.update_cookies(browser_context=self._browser_context)
            # 登录成功后保存cookies
            await self._save_cookies()

            self._initialized = True
            logger.info("初始化完成")

        except Exception as e:
            logger.error(f"初始化失败: {e}", exc_info=True)
            await self.cleanup()
            raise

    async def _create_client(self):
        """创建小红书API客户端"""
        logger.info("创建小红书客户端...")
        cookies = await self._browser_context.cookies()

        # 转换cookies为字符串和字典
        cookie_str = '; '.join([f"{c['name']}={c['value']}" for c in cookies])
        cookie_dict = {c['name']: c['value'] for c in cookies}

        # 设置请求头
        headers = {
            "User-Agent": self.user_agent,
            "Cookie": cookie_str,
            "Origin": "https://www.xiaohongshu.com",
            "Referer": "https://www.xiaohongshu.com"
        }

        return XiaoHongShuClient(
            headers=headers,
            playwright_page=self._page,
            cookie_dict=cookie_dict
        )

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
                await self.initialize()

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
        await self.initialize()
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
            note_id="67c97579000000000900f651",
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