# Scripts 目录说明

## 数据流程

**正确的数据流程**：

```
jobgraph-admin (数据中心)     →     jobgraph (客户端)
├── 爬取数据                        ├── 同步数据
├── 管理员录入数据                  ├── 智能匹配
├── 导出数据包                      ├── 简历解析
└── 启动 API 服务                   └── Web 界面查询
```

## 客户端脚本

- `sync_data.py` - 数据同步脚本
- `init_neo4j.py` - 初始化 Neo4j 数据库
- `benchmark.py` - 性能测试
- `query.py` - 查询测试

## 数据同步方式

### 方式一：离线数据包

```bash
# 1. 从 jobgraph-admin 导出数据包
cd jobgraph-admin
python scripts/data_tool.py export --output data_package.zip

# 2. 在 jobgraph Web 界面上传数据包
# 进入"数据同步"页面，上传 data_package.zip
```

### 方式二：API 同步

```bash
# 1. 启动 jobgraph-admin API 服务
cd jobgraph-admin
python scripts/data_tool.py serve --host 0.0.0.0 --port 8000

# 2. 在 jobgraph Web 界面输入数据中心地址
# 进入"数据同步"页面，输入 http://<数据中心IP>:8000
```

## 废弃脚本

以下脚本已废弃（示例数据，不再使用）：

- `deprecated/import_jobs.py` - 示例职位数据
- `deprecated/import_generated.py` - 生成的示例数据
- `deprecated/import_people.py` - 示例人物数据
- `deprecated/import_to_neo4j.py` - JSON 导入
- `deprecated/import_with_fusion.py` - 融合导入
