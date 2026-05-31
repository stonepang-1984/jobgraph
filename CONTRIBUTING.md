# Contributing to JobGraph

感谢你对 JobGraph 的关注！欢迎提交 Issue 和 Pull Request。

## 如何贡献

### 报告 Bug

1. 在 GitHub Issues 中搜索是否已有相同问题
2. 如果没有，创建新 Issue
3. 请包含以下信息：
   - 操作系统和版本
   - Python 版本
   - 错误信息和堆栈跟踪
   - 复现步骤

### 提交功能建议

1. 在 GitHub Issues 中创建 Feature Request
2. 详细描述你的需求和使用场景
3. 如果可能，提供设计方案

### 提交代码

1. Fork 本仓库
2. 创建你的功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交你的修改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 开发环境

### 环境要求

- Python 3.10+
- Neo4j 5.x
- Redis (可选)

### 安装依赖

```bash
# 克隆仓库
git clone https://github.com/yourusername/jobgraph.git
cd jobgraph

# 安装依赖
pip install -e ".[dev]"
```

### 启动服务

```bash
# 一键启动
./dev.sh

# 或手动启动
docker-compose up -d
make init-db
make jobgraph
```

### 运行测试

```bash
make test
```

### 代码风格

```bash
# 检查代码风格
make lint

# 格式化代码
make format
```

## 提交规范

### Commit Message 格式

```
<type>: <subject>

<body>

<footer>
```

### Type 类型

- `feat`: 新功能
- `fix`: 修复 Bug
- `docs`: 文档更新
- `style`: 代码格式修改
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具相关

### 示例

```
feat: add data export feature

- Add CSV export for company data
- Add JSON export for job data
- Add export button to UI

Closes #123
```

## 代码规范

### Python 代码风格

- 遵循 PEP 8
- 使用 type hints
- 编写 docstring
- 保持函数简洁

### 文件命名

- 使用小写字母和下划线
- 例如: `data_export.py`, `job_search.py`

### 测试

- 为新功能编写测试
- 确保所有测试通过
- 保持测试覆盖率

## Pull Request 规范

### PR 标题

使用与 Commit Message 相同的格式

### PR 描述

请包含：

1. 修改内容描述
2. 相关 Issue 编号
3. 测试情况
4. 截图 (如果是 UI 修改)

### 代码审查

- 至少需要一个维护者审查
- 所有 CI 检查必须通过
- 没有合并冲突

## 行为准则

- 尊重他人
- 保持专业
- 建设性讨论
- 欢迎新手

## 问题？

如有疑问，请在 GitHub Issues 中提问。

---

再次感谢你的贡献！🎉
