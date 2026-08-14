# LLM RAG Agent Projects

本仓库收录了 3 个基于大语言模型、RAG、知识图谱与 Agent 工作流构建的实践项目，覆盖企业私有知识库、医疗知识图谱问答和联网搜索助手等场景。

> 本仓库以学习和项目展示为目的。运行项目前，请先阅读各项目的“运行前准备”和“已知限制”。

## 项目概览

| 项目 | 主要能力 | 主要技术 |
| --- | --- | --- |
| [Enterprise Private Knowledge Base AGENT](#1-enterprise-private-knowledge-base-agent) | 企业知识库检索、混合召回、重排、流式问答、引用溯源、会话历史 | FastAPI、Vue 2、Chroma、BM25、BGE Reranker、通义千问、MySQL |
| [Smart Healthcare Knowledge Graph Q&A System](#2-smart-healthcare-knowledge-graph-qa-system) | 医疗知识图谱问答、混合检索、Agent 工具调用、邮箱验证码登录 | FastAPI、FastMCP、Neo4j、Chroma、Redis、Vue 2、通义千问 |
| [Smart Travel Planning Agent System](#3-smart-travel-planning-agent-system) | 问题理解、联网搜索、信息整合与中文回答 | LangGraph、Tavily、通义千问、Python CLI |

## 仓库结构

```text
llm-rag-agent/
├── Enterprise Private Knowledge Base AGENT/
│   ├── rag_app/                    # Vue 2 前端
│   └── stu_fastapi/                # FastAPI + RAG 后端
├── Smart Healthcare Knowledge Graph Q&A System/
│   ├── rag_server_app/             # Vue 2 前端
│   └── rag_server_project/         # FastAPI + MCP + 知识图谱后端
├── Smart Travel Planning Agent System/
│   ├── main.py                     # 命令行入口
│   ├── search_assistant.py         # LangGraph 工作流
│   └── requirements.txt
└── README.md
```

---

## 1. Enterprise Private Knowledge Base AGENT

企业私有知识库问答系统，支持用户登录、知识库选择、多轮会话、流式回答、历史记录和检索来源展示。

### 核心流程

```text
用户问题
  → Chroma 向量检索
  → BM25 关键词检索
  → RRF 融合
  → BGE Reranker 重排
  → 通义千问生成带引用的回答
  → SSE 流式返回前端
```

当前代码内置两个知识库：

- `motogp_675sr`：MotoGP / 675SR 相关知识
- `law`：法律知识数据

### 主要功能

- 用户注册与登录
- 新建、查看、修改和删除会话
- Chroma + BM25 混合检索
- RRF（Reciprocal Rank Fusion）结果融合
- BGE Reranker 语义重排
- 回答引用与证据来源展示
- SSE 流式输出
- 检索分数与知识库状态展示
- RAG 元数据持久化

### 技术栈

**前端**

- Vue 2
- Vue Router
- Element UI
- Axios
- Marked + DOMPurify
- Webpack 3

**后端**

- Python / FastAPI / Uvicorn
- LangChain
- 通义千问（DashScope OpenAI 兼容接口）
- Chroma
- Sentence Transformers
- FlagEmbedding / BGE Reranker
- Jieba / BM25
- MySQL / PyMySQL

### 运行前准备

1. 安装 Python 3.10 或更高版本、Node.js、npm 和 MySQL。
2. 创建 MySQL 数据库，并根据代码使用情况准备 `users`、`history` 表。
3. 执行增量迁移：

```sql
-- 文件位置：stu_fastapi/migrations/001_add_history_rag_metadata.sql
ALTER TABLE history ADD COLUMN rag_metadata LONGTEXT NULL;
```

4. 检查并修改数据库连接配置：

```text
stu_fastapi/common/MySQLUtil.py
```

5. 配置通义千问 API Key。PowerShell 示例：

```powershell
$env:DASHSCOPE_API_KEY="你的 DashScope API Key"
```

6. 准备本地嵌入模型和重排模型。代码默认从 `stu_fastapi/models/` 加载模型，但模型权重因体积较大未提交到 GitHub。

### 安装与启动

该项目目前没有 Python 依赖清单，需要根据后端 import 安装依赖。可参考：

```bash
python -m pip install fastapi uvicorn langchain-core langchain-openai langchain-chroma chromadb sentence-transformers FlagEmbedding jieba rank-bm25 pymysql jinja2 pandas
```

启动后端：

```bash
cd "Enterprise Private Knowledge Base AGENT/stu_fastapi"
python main.py
```

后端默认地址：`http://localhost:8001`

启动前端：

```bash
cd "Enterprise Private Knowledge Base AGENT/rag_app"
npm install
npm run dev
```

前端默认地址：`http://localhost:8080`

构建前端生产版本：

```bash
npm run build
```

### 重建知识库

在 `stu_fastapi` 目录执行：

```bash
# 重建全部知识库
python create_dataset/GouJianFaLuZhiShiKu.py all

# 仅重建法律知识库
python create_dataset/GouJianFaLuZhiShiKu.py law

# 仅重建 MotoGP / 675SR 知识库
python create_dataset/GouJianFaLuZhiShiKu.py motogp_675sr
```

### 重要说明

- 大模型权重、`node_modules`、IDE 文件和 Python 缓存未上传。
- 仓库中没有完整的 MySQL 初始化脚本，需要自行准备基础表结构。
- 前端后端地址及部分数据库参数目前写在源码中，部署前建议改为环境变量。
- 当前用户密码逻辑尚未使用安全哈希，仅适合学习环境；正式部署前应使用 Argon2 或 bcrypt。

---

## 2. Smart Healthcare Knowledge Graph Q&A System

基于医疗知识图谱、混合检索和 MCP 工具调用构建的智能医疗问答系统。系统能够判断问题类型，并选择直接回答、上下文回答或医疗知识图谱检索。

### 系统组成

```text
Vue 前端（8080）
        ↓
FastAPI 服务（8000）
        ↓
LLM Agent + MCP Client
        ↓
FastMCP 服务（9000）
   ├── Neo4j 医疗知识图谱
   ├── Chroma + BM25 + BGE Reranker
   ├── MySQL 用户与历史数据
   ├── Redis 验证码缓存
   └── SMTP 邮件服务
```

### 主要功能

- 邮箱验证码登录
- 医疗问题智能路由
- Neo4j 图谱关系查询
- Chroma + BM25 混合检索
- RRF 融合与 BGE 重排
- MCP 工具调用
- 多轮聊天与历史记录
- 检索失败时的降级回答

### 技术栈

**前端**

- Vue 2
- Vue Router
- Element UI
- Axios
- Marked + DOMPurify
- Webpack 3

**后端与 Agent**

- Python / FastAPI / Uvicorn
- LangChain Agent
- FastMCP
- 通义千问（DashScope）
- Neo4j
- Chroma
- Sentence Transformers / BGE Reranker
- MySQL / Redis
- SMTP

### 运行前准备

请先安装并启动：

- Python 3.10 或更高版本
- Node.js 与 npm
- MySQL
- Redis
- Neo4j

配置通义千问 API Key：

```powershell
$env:DASHSCOPE_API_KEY="你的 DashScope API Key"
```

此外，需要检查以下源码中的本地服务配置，并根据实际环境修改：

- `rag_server_project/mymcp/MCPServer.py`
- `rag_server_project/mymcp/MCPClient.py`
- `rag_server_project/history/dao/HistoryDao.py`

需要提前准备：

- MySQL 数据库 `rag_server_project`
- 用于邮箱登录的 `users` 表
- Neo4j 医疗知识图谱数据
- Redis 服务
- SMTP 发件邮箱配置

> 安全提醒：源码中的数据库、Neo4j 和 SMTP 配置仅应作为本地开发示例。公开部署前，请撤销或轮换已经使用过的凭据，并将所有密码、授权码迁移到环境变量中。

### 安装后端依赖

该项目目前没有 Python 依赖清单，可根据源码依赖参考安装：

```bash
python -m pip install fastapi uvicorn langchain-core langchain-openai langchain-chroma langchain-neo4j chromadb sentence-transformers FlagEmbedding jieba rank-bm25 pymysql redis neo4j fastmcp pandas
```

### 启动顺序

进入项目目录：

```bash
cd "Smart Healthcare Knowledge Graph Q&A System"
```

1. 启动 MCP 服务：

```bash
python -m rag_server_project.mymcp.MCPServer
```

MCP 默认地址：`http://127.0.0.1:9000/mcp`

2. 新开终端，启动 FastAPI：

```bash
python -m rag_server_project.main
```

后端默认地址：`http://127.0.0.1:8000`

3. 新开终端，启动前端：

```bash
cd rag_server_app
npm install
npm run dev
```

前端默认地址：`http://localhost:8080`

### 构建医疗向量检索库

Neo4j 中已有医疗图谱数据后，可执行：

```bash
python -m rag_server_project.create_dataset.BuildMedicalRetrievalStore
```

如果 Chroma 检索库为空，首次混合检索也会尝试根据 Neo4j 数据构建索引。

### 重要说明

- 仓库未包含完整的医疗图谱导入数据和初始化脚本。
- 嵌入模型、重排模型和 Chroma 数据未提交，首次运行可能需要联网下载模型。
- FastAPI 服务依赖 MCP、MySQL 和模型配置，建议严格按照启动顺序运行。
- `FlagReranker` 当前启用了 FP16；仅使用 CPU 时可能需要调整配置。
- 邮箱验证码有效期较短，需确保 Redis 和 SMTP 服务工作正常。

---

## 3. Smart Travel Planning Agent System

一个基于 LangGraph 和 Tavily 的联网搜索问答 CLI。项目能够理解用户问题、生成搜索关键词、查询互联网信息，并由大模型整理为中文回答。

当前实现更接近“通用联网搜索助手”，可用于查询旅行目的地、天气、景点和出行信息；尚未集成地图、酒店、机票或自动行程编排 API。

### 工作流

```text
START
  → understand：理解问题并生成搜索词
  → search：调用 Tavily 获取搜索结果
  → answer：整合搜索信息并生成中文回答
  → END
```

### 技术栈

- Python
- LangGraph
- LangChain Core
- 通义千问（默认模型 `qwen3.7-plus`）
- Tavily Search API
- python-dotenv

### 环境变量

项目会读取当前目录下的 `.env` 文件。请自行创建 `.env`：

```dotenv
DASHSCOPE_API_KEY=你的_DashScope_API_Key
TAVILY_API_KEY=你的_Tavily_API_Key

# 可选配置
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_ID=qwen3.7-plus
```

也可以使用 `LLM_API_KEY` 作为 `DASHSCOPE_API_KEY` 的备用配置。

> 不要将 `.env`、API Key 或其他凭据提交到 GitHub。

### 安装与运行

```bash
cd "Smart Travel Planning Agent System"
python -m pip install -r requirements.txt
python main.py
```

程序启动后，在终端输入问题即可。输入以下任一命令退出：

```text
quit
exit
q
```

### 重要说明

- 启动时必须同时提供 LLM API Key 和 `TAVILY_API_KEY`。
- 搜索发生运行时异常时，程序会尝试使用模型已有知识回答。
- 当前会话状态保存在内存中，程序退出后不会持久化。
- 当前 CLI 不会逐 Token 输出，尽管底层模型配置启用了 streaming。

---

## 通用安全建议

在本地学习之外使用这些项目之前，建议完成以下改造：

1. 将数据库密码、API Key、SMTP 授权码和服务地址迁移到环境变量。
2. 轮换所有曾经提交到公开仓库的凭据。
3. 为用户密码增加安全哈希和盐值。
4. 对 MCP 工具中的 SQL、Cypher 和外部输入增加严格校验与权限限制。
5. 为生产环境配置 HTTPS、访问控制、日志脱敏和限流。
6. 固定 Python 与 npm 依赖版本，并增加自动化测试。

## 模型与大文件说明

由于 GitHub 对单文件大小有限制，本仓库不提交本地模型权重、模型缓存、`node_modules` 和构建产物。请根据代码指定的模型名称自行下载：

- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- `BAAI/bge-reranker-large`

## License

本仓库当前未声明开源许可证。在添加许可证前，代码默认保留所有权利，不应视为已授权用于商业分发。
