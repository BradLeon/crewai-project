import json
import logging
import asyncio
from typing import List, Dict, Any
from .xhs_comment_post_tool import XhsCommentPostTool

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("comment_publisher.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CommentPublisher:
    """直接处理评论发布的类，不依赖LLM"""
    
    def __init__(self):
        self.comment_tool = XhsCommentPostTool()
        
    async def publish_comments(self, note_id: str, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        发布评论到小红书
        
        Args:
            note_id: 笔记ID
            comments: 评论列表，每个评论包含：
                     - target_comment_id: 目标评论ID（可选）
                     - reply: 回复内容
                     
        Returns:
            Dict: 包含发布结果的字典
        """
        results = []
        try:
            for comment in comments:
                try:
                    # 提取评论内容
                    content = comment.get('reply')
                    target_comment_id = comment.get('target_comment_id')
                    
                    if not content:
                        logger.warning(f"跳过空评论: {comment}")
                        continue
                        
                    # 发布评论
                    logger.info(f"准备发布评论: content={content}, target_comment_id={target_comment_id}")
                    result = await self.comment_tool._async_run(
                        note_id=note_id,
                        content=content,
                        target_comment_id=target_comment_id
                    )
                    
                    # 处理结果
                    status = "success" if result.get('success') else "failed"
                    results.append({
                        "content": content,
                        "status": status,
                        "message": result.get('message', ''),
                        "data": result.get('data', {})
                    })
                    
                    # 添加延时，避免频繁发布
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"发布单条评论时出错: {e}", exc_info=True)
                    results.append({
                        "content": comment.get('reply', ''),
                        "status": "failed",
                        "message": f"发布失败: {str(e)}"
                    })
                    
            return {
                "success": any(r['status'] == 'success' for r in results),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"发布评论过程中出错: {e}", exc_info=True)
            return {
                "success": False,
                "results": results,
                "error": str(e)
            }
            
    def run(self, note_id: str, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        同步方式运行评论发布
        
        Args:
            note_id: 笔记ID
            comments: 评论列表
            
        Returns:
            Dict: 发布结果
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        return loop.run_until_complete(self.publish_comments(note_id, comments))


def main():
    """测试函数"""
    # 测试数据
    test_data = {
        "note_id": "67c97579000000000900f651",
        "comments": [
            {
                "target_comment_id": "67d2b21b000000001702bd15",
                "reply": "感谢分享，这个精油确实很适合睡眠！"
            },
            {
                "reply": "产品很不错，期待更多分享"
            }
        ]
    }
    
    # 运行测试
    publisher = CommentPublisher()
    result = publisher.run(test_data['note_id'], test_data['comments'])
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main() 