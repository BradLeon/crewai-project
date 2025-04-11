# src/social_media_auto_comment/tools/faiss_retrieval_tool.py
from crewai.tools import BaseTool
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import JSONLoader
from langchain_core.documents import Document
from typing import List, Dict, Any, Optional
import json
import os
import hashlib
import time
import logging
from functools import wraps

# 设置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FAISSRetrievalTool")

# 添加超时装饰器
def timeout_handler(timeout_seconds=10):
    """为函数添加超时控制的装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import threading
            import queue

            result_queue = queue.Queue()
            exception_queue = queue.Queue()
            
            def target():
                try:
                    result = func(*args, **kwargs)
                    result_queue.put(result)
                except Exception as e:
                    logger.error(f"函数执行出错: {func.__name__} - {str(e)}")
                    exception_queue.put(e)
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout_seconds)
            
            if thread.is_alive():
                logger.warning(f"函数执行超时: {func.__name__}, 超时时间 {timeout_seconds}秒")
                return f"操作超时: {timeout_seconds}秒内未完成"
            
            if not exception_queue.empty():
                e = exception_queue.get()
                return f"执行出错: {str(e)}"
                
            if not result_queue.empty():
                return result_queue.get()
                
            return "未知错误"
            
        return wrapper
    return decorator

class FAISSRetrievalTool(BaseTool):
    """基于FAISS向量数据库的检索工具"""
    
    name: str = "FAISS知识库"
    description: str = "通过FAISS向量数据库查询产品和对话相关信息"
    
    # 添加Pydantic模型字段
    file_paths: List[str] 
    embeddings: Any = None
    vector_store: Any = None
    cache_dir: str = "faiss_index"
    max_retries: int = 3
    retry_delay: int = 2
    search_timeout: int = 20
    
    def __init__(self, file_paths: List[str], embedding_model_name: str = "text-embedding-3-small", 
                 cache_dir: str = "faiss_index", max_retries: int = 3, retry_delay: int = 2,
                 search_timeout: int = 20):
        """
        初始化FAISS检索工具
        
        Args:
            file_paths: JSON知识库文件路径列表
            embedding_model_name: OpenAI嵌入模型名称
            cache_dir: 向量数据库缓存目录
            max_retries: 最大重试次数
            retry_delay: 重试间隔（秒）
            search_timeout: 搜索超时时间（秒）
        """
        super().__init__(file_paths=file_paths)
        self.embeddings = OpenAIEmbeddings(model=embedding_model_name)
        self.vector_store = None
        self.cache_dir = cache_dir
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.search_timeout = search_timeout
        self._initialize_vector_store()
    
    def _get_files_hash(self) -> str:
        """
        计算所有文件的组合哈希值，用于判断文件是否已更改
        """
        hash_obj = hashlib.md5()
        
        # 先把文件路径列表添加到哈希
        file_paths_str = ",".join(sorted(self.file_paths))
        hash_obj.update(file_paths_str.encode('utf-8'))
        
        for file_path in sorted(self.file_paths):
            if os.path.exists(file_path):
                try:
                    # 对文件大小和修改时间进行哈希，这些是确定性的
                    file_size = os.path.getsize(file_path)
                    mtime = int(os.path.getmtime(file_path))
                    file_info = f"{file_path}:{file_size}:{mtime}"
                    hash_obj.update(file_info.encode('utf-8'))
                    
                    # 用确定性的MD5哈希文件内容，而不是Python的hash函数
                    content_hash = hashlib.md5()
                    with open(file_path, 'rb') as f:
                        # 读取文件块并更新哈希，避免一次性加载大文件
                        for chunk in iter(lambda: f.read(8192), b""):
                            content_hash.update(chunk)
                    
                    hash_obj.update(content_hash.hexdigest().encode('utf-8'))
                except Exception as e:
                    logger.error(f"计算文件哈希时出错 {file_path}: {str(e)}")
                    # 如果出错，也要添加文件路径到哈希，防止跳过检测
                    hash_obj.update(f"ERROR:{file_path}".encode('utf-8'))
        
        return hash_obj.hexdigest()
    
    def _initialize_vector_store(self):
        """初始化向量存储，加载JSON文件内容"""
        start_time = time.time()
        logger.info("开始初始化向量存储")
        
        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 生成索引路径和哈希文件路径
        # 注意: FAISS索引文件是一个目录，不是单个文件
        hash_file = os.path.join(self.cache_dir, "files_hash.txt")
        
        # 计算当前文件哈希
        current_hash = self._get_files_hash()
        logger.info(f"当前文件哈希值: {current_hash}")
        
        # 检查缓存是否存在且有效
        cache_valid = False
        # 检查index.faiss和index.pkl文件是否存在，这是FAISS保存的两个文件
        index_files_exist = (
            os.path.exists(os.path.join(self.cache_dir, "index.faiss")) and
            os.path.exists(os.path.join(self.cache_dir, "index.pkl"))
        )
        
        if index_files_exist and os.path.exists(hash_file):
            try:
                with open(hash_file, 'r') as f:
                    saved_hash = f.read().strip()
                logger.info(f"已保存的哈希值: {saved_hash}")
                
                if saved_hash == current_hash:
                    logger.info(f"哈希匹配！从 {self.cache_dir} 加载向量存储")
                    try:
                        self.vector_store = FAISS.load_local(self.cache_dir, self.embeddings, "index", allow_dangerous_deserialization=True)
                        cache_valid = True
                        logger.info("向量存储加载成功")
                    except Exception as e:
                        logger.error(f"加载向量存储失败: {str(e)}")
                else:
                    logger.info(f"哈希不匹配，将重新创建向量存储")
            except Exception as e:
                logger.error(f"读取哈希文件失败: {str(e)}")
        else:
            logger.info(f"缓存文件不存在: index文件存在={index_files_exist}, hash文件存在={os.path.exists(hash_file)}")
        
        # 如果缓存无效或不存在，则重新创建索引
        if not cache_valid:
            logger.info("未发现有效缓存或文件已更改，将重新创建向量索引")
            documents = []
            
            for json_path in self.file_paths:
                if not os.path.exists(json_path):
                    logger.warning(f"警告: 文件 {json_path} 不存在")
                    continue
                    
                try:
                    # 加载JSON文件内容
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 处理数组类型的JSON
                    if isinstance(data, list):
                        for item in data:
                            # 如果是对话格式
                            if "messages" in item:
                                # 处理对话消息
                                combined_text = f"对话ID: {item.get('conversation_id', 'unknown')}\n"
                                for msg in item["messages"]:
                                    role = msg.get("role", "unknown")
                                    content = msg.get("content", "")
                                    combined_text += f"{role}: {content}\n"
                                
                                documents.append(Document(
                                    page_content=combined_text,
                                    metadata={"source": json_path, "type": "conversation"}
                                ))
                            else:
                                # 其他JSON对象
                                documents.append(Document(
                                    page_content=json.dumps(item, ensure_ascii=False),
                                    metadata={"source": json_path, "type": "json_object"}
                                ))
                    # 处理文本文件
                    elif json_path.endswith('.txt'):
                        with open(json_path, 'r', encoding='utf-8') as f:
                            text_content = f.read()
                        documents.append(Document(
                            page_content=text_content,
                            metadata={"source": json_path, "type": "text"}
                        ))
                except Exception as e:
                    logger.error(f"加载文件 {json_path} 时出错: {str(e)}")
            
            if documents:
                logger.info(f"成功加载 {len(documents)} 个文档到FAISS")
                try:
                    self.vector_store = FAISS.from_documents(documents, self.embeddings)
                    
                    # 保存向量存储以供日后使用
                    self.vector_store.save_local(self.cache_dir, "index")
                    
                    # 保存文件哈希
                    with open(hash_file, 'w') as f:
                        f.write(current_hash)
                        
                    logger.info(f"向量索引已保存到 {self.cache_dir}")
                except Exception as e:
                    logger.error(f"创建或保存向量存储失败: {str(e)}")
            else:
                logger.warning("警告: 没有文档被加载到向量存储")
        
        elapsed_time = time.time() - start_time
        logger.info(f"向量存储初始化完成，耗时: {elapsed_time:.2f}秒")
    
    @timeout_handler(20)  # 设置20秒超时
    def _search_with_timeout(self, query, k=3):
        """带超时的相似度搜索"""
        if not self.vector_store:
            return []
        return self.vector_store.similarity_search_with_score(query, k=k)
    
    def _run(self, query: str) -> str:
        """执行查询"""
        start_time = time.time()
        
        if not self.vector_store:
            return "错误: 向量存储未初始化，无法执行查询"
        
        # 添加重试逻辑
        for attempt in range(self.max_retries):
            try:
                logger.info(f"[FAISSretrivalTool] 开始查询 (尝试 {attempt+1}/{self.max_retries}): {query}")
                
                # 使用带超时的查询方法
                results = self._search_with_timeout(query, k=3)
                
                if isinstance(results, str) and "超时" in results:
                    logger.warning(f"查询超时: {results}")
                    if attempt < self.max_retries - 1:
                        logger.info(f"等待 {self.retry_delay} 秒后重试...")
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        return f"查询超时: 在 {self.search_timeout} 秒内未完成。请尝试简化查询或稍后再试。"
                
                if not results:
                    return "未找到相关信息"
                
                # 格式化结果
                response = "相关信息:\n\n"
                for i, (doc, score) in enumerate(results, 1):
                    response += f"[相似度: {score:.2f}] {doc.page_content}\n\n"
                
                elapsed_time = time.time() - start_time
                logger.info(f"[FAISSretrivalTool] 查询完成，耗时: {elapsed_time:.2f}秒")
                logger.info(f"[FAISSretrivalTool] 查询: {query}")
                logger.info(f"[FAISSretrivalTool] 响应: {response[:200]}...")  # 只记录部分响应，避免日志过大
                logger.info("--------------------------------")

                return response
                
            except Exception as e:
                logger.error(f"查询出错 (尝试 {attempt+1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    logger.info(f"等待 {self.retry_delay} 秒后重试...")
                    time.sleep(self.retry_delay)
                else:
                    return f"查询出错: {str(e)}。已重试 {self.max_retries} 次。"
        
        return "所有重试都失败，无法完成查询。"