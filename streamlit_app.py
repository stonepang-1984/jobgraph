"""Streamlit Cloud Demo 入口

使用 SQLite 存储，无需 PyTorch 和 Neo4j
"""

import os
import sys
from pathlib import Path

# 设置 Demo 模式环境变量
os.environ["STORAGE_BACKEND"] = "sqlite"
os.environ["USE_TORCH"] = "false"
os.environ["DEMO_MODE"] = "true"
os.environ["TORCH_DISABLE_CUSTOM_CLASS_CHECK"] = "1"

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 确保数据目录存在
data_dir = project_root / "data"
data_dir.mkdir(exist_ok=True)

# 导入并运行主应用
# Streamlit 会自动执行文件中的代码
exec(open("web/jobgraph.py").read())
