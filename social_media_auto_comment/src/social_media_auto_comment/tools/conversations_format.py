#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import argparse
from collections import defaultdict
from typing import Dict, List, Any, Optional

def convert_conversations(input_file: str, output_file: str) -> None:
    """
    将原始对话数据转换为结构化的完整对话格式，并输出为单个JSON文件
    
    Args:
        input_file: 输入文件路径（原始JSONL）
        output_file: 输出文件路径（JSON文件，包含对话数组）
    """
    print(f"正在读取文件: {input_file}")
    
    # 存储所有评论，按conversation_id分组
    conversations = defaultdict(list)
    
    # 读取原始数据
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                comment = json.loads(line.strip())
                conversations[comment.get('conversation_id', 'unknown')].append(comment)
            except json.JSONDecodeError:
                print(f"警告: 跳过无效的JSON行: {line[:50]}...")
                continue
    
    print(f"找到 {len(conversations)} 个对话")
    
    # 转换为结构化格式
    structured_conversations = []
    
    for conv_id, comments in conversations.items():
        # 按comment_id创建查找表，方便构建对话树
        comment_map = {comment['comment_id']: comment for comment in comments if 'comment_id' in comment}
        
        # 尝试重建对话顺序
        ordered_comments = reconstruct_conversation(comments, comment_map)
        
        # 转换为目标格式
        messages = []
        for comment in ordered_comments:
            role = "agent" if comment.get('is_author', False) else "customer"
            content = comment.get('content', '')
            if content:  # 只添加有内容的消息
                messages.append({
                    "role": role,
                    "content": content
                })
        
        # 创建最终结构
        if messages:  # 只添加有消息的对话
            structured_conv = {
                "conversation_id": conv_id,
                "messages": messages,
                "metadata": {
                    "original_comment_count": len(comments)
                    # 可以添加更多元数据
                }
            }
            structured_conversations.append(structured_conv)
    
    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(structured_conversations, f, ensure_ascii=False, indent=2)
    
    print(f"已成功转换 {len(structured_conversations)} 个对话并写入 {output_file}")

def reconstruct_conversation(comments: List[Dict[str, Any]], comment_map: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    尝试根据parent_id重建对话的正确顺序
    
    这个函数处理两种情况:
    1. 线性对话: 每条消息都只回复前一条消息
    2. 非线性对话: 消息可能回复任何之前的消息
    
    Args:
        comments: 原始评论列表
        comment_map: 评论ID到评论对象的映射
        
    Returns:
        按时间顺序排列的评论列表
    """
    # 首先找到对话的根消息（没有parent_id的消息）
    root_comments = [c for c in comments if not c.get('parent_id')]
    
    # 如果没有根消息，尝试使用其他方法构建顺序
    if not root_comments and comments:
        # 按照某种规则排序，例如时间戳或ID
        if 'created_at' in comments[0]:
            return sorted(comments, key=lambda x: x.get('created_at', ''))
        else:
            # 如果没有时间戳，尝试使用comment_id排序或保持原始顺序
            return comments
            
    # 构建回复树
    reply_tree = defaultdict(list)
    for comment in comments:
        parent_id = comment.get('parent_id')
        if parent_id:
            reply_tree[parent_id].append(comment)
    
    # 使用深度优先搜索重建对话
    ordered_comments = []
    
    def dfs(comment_id: Optional[str] = None, comment: Optional[Dict[str, Any]] = None) -> None:
        if comment:
            ordered_comments.append(comment)
        
        # 获取当前评论的ID
        current_id = comment_id
        if not current_id and comment:
            current_id = comment.get('comment_id')
        
        # 处理回复
        if current_id and current_id in reply_tree:
            # 按时间或ID排序回复
            replies = reply_tree[current_id]
            if replies and 'created_at' in replies[0]:
                replies = sorted(replies, key=lambda x: x.get('created_at', ''))
            
            for reply in replies:
                dfs(None, reply)
    
    # 从所有根评论开始遍历
    for root in root_comments:
        dfs(None, root)
    
    # 如果DFS没有覆盖所有评论，添加剩余的评论
    processed_ids = {comment.get('comment_id') for comment in ordered_comments if 'comment_id' in comment}
    for comment in comments:
        if 'comment_id' in comment and comment['comment_id'] not in processed_ids:
            ordered_comments.append(comment)
    
    return ordered_comments

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="转换对话数据格式")
    parser.add_argument("--input", "-i", required=True, help="输入JSONL文件路径")
    parser.add_argument("--output", "-o", required=True, help="输出JSONL文件路径")
    
    args = parser.parse_args()
    convert_conversations(args.input, args.output)