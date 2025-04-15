import os
import sys
from pathlib import Path

def setup_project_path():
    """
    设置项目路径，确保可以正确导入项目内的模块
    """
    # 获取当前文件的绝对路径
    current_file = Path(__file__).resolve()

    # 获取项目根目录（src目录）
    project_root = current_file.parent.parent.parent

    # 将项目根目录添加到 Python 路径
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    return project_root

def get_lib_path(lib_name):
    """
    获取libs目录下的库路径
    """
    project_root = setup_project_path()
    lib_path = project_root / "libs" / lib_name
    if lib_path.exists():
        return str(lib_path)
    return None