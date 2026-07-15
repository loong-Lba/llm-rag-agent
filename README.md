# llm-rag-agent

个人 LLM 应用项目合集，聚焦 **RAG 检索增强问答、Agent 工作流、知识图谱问答、LangGraph 搜索助手** 等方向，适合作为课程设计、毕业设计、项目练习与能力展示仓库。

本仓库目前包含 3 个相对独立的项目：

- **Enterprise Private Knowledge Base AGENT**：企业私有知识库问答系统，基于 Vue + FastAPI + LangChain + Chroma 实现。
- **Smart Healthcare Knowledge Graph Q&A System**：医疗知识图谱智能问答系统，结合 Neo4j、混合检索与 Agent/MCP 工具调用实现。
- **Smart Travel Planning Agent System**：基于 LangGraph 的智能搜索助手，面向旅游/开放问答类信息检索场景。

---

## 仓库结构

```text
llm-rag-agent/
├── Enterprise Private Knowledge Base AGENT/
├── Smart Healthcare Knowledge Graph Q&A System/
├── Smart Travel Planning Agent System/
└── README.md
```

---

## 项目一：Enterprise Private Knowledge Base AGENT

### 项目简介

这是一个面向企业私有知识库场景的智能问答项目，采用 **前后端分离** 架构：

- 前端：`rag_app`，基于 Vue 构建聊天界面、登录注册等页面。
- 后端：`stu_fastapi`，基于 FastAPI 提供用户管理、聊天、历史记录等接口。
- 检索链路：结合 **向量检索 + BM25 + RRF 融合 + 重排序** 实现混合检索式 RAG。

从代码可以看出，这个项目的知识库场景目前偏向 **MotoGP / 675SR / 摩托车知识问答**，同时保留了完整的用户、聊天和历史记录模块，适合作为通用私有知识库 Agent 系统的原型项目。

### 主要技术栈

- Vue 2
- FastAPI
- LangChain
- Chroma
- HuggingFace Embeddings
- FlagEmbedding / BGE Reranker
- BM25
- MySQL

### 核心能力

- 用户注册 / 登录
- 聊天问答接口
- 历史对话记录
- 问题是否需要检索的路由判断
- 混合检索：向量检索 + BM25 检索 + RRF 融合
- 基于重排序模型优化召回结果
- 支持非流式 / 流式问答

### 目录说明

```text
Enterprise Private Knowledge Base AGENT/
├── rag_app/         # Vue 前端
└── stu_fastapi/     # FastAPI 后端
```

### 启动说明

#### 1）启动前端

进入：

```bash
cd "Enterprise Private Knowledge Base AGENT/rag_app"
npm install
npm run dev
```

默认前端开发端口为：

- `http://localhost:8080`

#### 2）启动后端

进入：

```bash
cd "Enterprise Private Knowledge Base AGENT/stu_fastapi"
```

安装依赖后运行：

```bash
python main.py
```

后端默认地址：

- `http://localhost:8001`
- 接口文档：`http://localhost:8001/docs`

### 项目特点

这个项目比较完整地展示了一个 **企业私有知识库问答系统** 的雏形：

- 有前端页面
- 有后端接口
- 有用户体系
- 有聊天历史
- 有知识库检索流程
- 有多路检索融合策略

如果后续继续完善，可以进一步抽象成通用的企业知识库问答平台。

---

## 项目二：Smart Healthcare Knowledge Graph Q&A System

### 项目简介

这是一个将 **医疗知识图谱 + Agent + 混合检索 + MCP 工具调用** 结合起来的智能问答系统。

项目整体也是前后端分离结构：

- `rag_server_app`：Vue 前端页面。
- `rag_server_project`：FastAPI 后端服务。
- 后端同时包含：
  - 医疗知识图谱问答逻辑
  - 业务型 Agent（验证码、邮箱发送等）
  - 混合检索工具
  - MCP Server 工具注册
  - Neo4j 图谱查询能力

相较于普通 RAG 项目，这个项目更强调：

1. **路由判断**：区分是否需要直接回答、是否依赖历史上下文、是否需要医疗图谱检索。
2. **工具调用**：支持查询邮箱、发送验证码、校验验证码等业务工具。
3. **图谱问答**：支持基于 Neo4j 的结构化查询。
4. **文本检索增强**：支持向量检索、BM25、RRF 融合与重排序。

### 主要技术栈

- Vue 2
- FastAPI
- LangChain Agent
- FastMCP
- Neo4j
- Chroma
- HuggingFace Embeddings
- FlagEmbedding / BGE Reranker
- BM25
- Redis
- MySQL
- 阿里云百炼 / Qwen 兼容接口

### 核心能力

- 医疗问答路由判断
- 医疗知识图谱问答
- 混合检索增强问答
- 基于 Neo4j 的结构化查询
- 验证码发送与校验业务 Agent
- MCP 工具注册与调用
- 用户 / 聊天 / 历史记录接口

### 目录说明

```text
Smart Healthcare Knowledge Graph Q&A System/
├── rag_server_app/       # Vue 前端
├── rag_server_project/   # FastAPI 后端
└── start                 # 启动辅助脚本/入口文件
```

### 启动说明

#### 1）启动前端

```bash
cd "Smart Healthcare Knowledge Graph Q&A System/rag_server_app"
npm install
npm run dev
```

默认前端端口通常为：

- `http://localhost:8080`

#### 2）启动后端

```bash
cd "Smart Healthcare Knowledge Graph Q&A System"
python -m rag_server_project.main
```

或在项目环境中直接运行对应入口。

后端默认地址：

- `http://127.0.0.1:8000`

### 依赖环境说明

该项目依赖相对较多，通常需要准备：

- Neo4j 数据库
- MySQL 数据库
- Redis
- 向量库与本地模型缓存
- `DASHSCOPE_API_KEY`

### 项目特点

这个项目比普通问答系统更接近一个 **复合型医疗智能体系统**：

- 既能回答自然语言医疗问题
- 又能基于图谱进行结构化查询
- 还能处理验证码、邮箱发送等工具型业务流程
- 并且引入了 MCP Server 的设计思路

如果作为简历或毕设项目，这个项目的亮点会比较突出。

---

## 项目三：Smart Travel Planning Agent System

### 项目简介

这是一个基于 **LangGraph** 构建的命令行智能搜索助手项目，整体设计思路清晰，适合展示 Agent 工作流编排能力。

项目将一次问答拆成 3 个阶段：

1. **理解用户问题**：提炼用户真实需求，生成更适合检索的搜索词。
2. **执行联网搜索**：调用 Tavily 搜索 API 获取结果。
3. **生成最终答案**：基于搜索结果或模型已有知识输出回答。

从实现上看，这个项目更偏向 **LangGraph 工作流学习 / Agent 搜索问答示例**，适合作为 Agent 入门项目、流程编排示例或课程展示项目。

### 主要技术栈

- Python
- LangGraph
- LangChain
- ChatOpenAI 兼容接口
- Tavily Search API
- python-dotenv

### 核心能力

- 用户问题理解与改写
- 搜索关键词生成
- 联网搜索结果整理
- 基于搜索结果生成答案
- 搜索失败时自动降级为模型知识回答
- 命令行交互式使用

### 目录说明

```text
Smart Travel Planning Agent System/
├── main.py
├── search_assistant.py
└── requirements.txt
```

### 启动说明

进入项目目录后：

```bash
cd "Smart Travel Planning Agent System"
pip install -r requirements.txt
python main.py
```

### 环境变量

运行前通常需要准备：

- `DASHSCOPE_API_KEY` 或 `LLM_API_KEY`
- `LLM_BASE_URL`（可选）
- `LLM_MODEL_ID`（可选）
- `TAVILY_API_KEY`

### 项目特点

这个项目最大的优点是结构清晰，特别适合学习：

- LangGraph 状态图
- 多阶段 Agent 工作流
- 问题理解与查询改写
- 搜索增强回答
- 失败兜底机制

---

## 技术关键词汇总

本仓库涉及的核心技术方向包括：

- LLM 应用开发
- RAG（检索增强生成）
- Agent / 智能体
- LangChain
- LangGraph
- MCP
- FastAPI
- Vue
- Neo4j 知识图谱
- Chroma 向量数据库
- BM25 / RRF 混合检索
- HuggingFace Embedding
- BGE Reranker
- Redis / MySQL

---

## 适用场景

这个仓库适合用于：

- 毕业设计 / 课程设计项目整理
- LLM 应用开发作品集
- RAG / Agent / 知识图谱方向学习
- 求职时展示 AI 应用项目实践能力
- 后续继续扩展为更完整的智能体系统

---

## 后续可优化方向

如果后续继续维护这个仓库，建议优先做这些优化：

1. 为每个子项目补充独立 README。
2. 补充统一的环境配置说明（Python 版本、Node 版本、数据库版本）。
3. 增加 `.gitignore`，排除缓存、数据库文件、向量索引、模型文件、IDE 文件。
4. 将敏感配置改为 `.env.example`。
5. 为每个项目补充架构图、流程图和运行截图。
6. 对项目命名、目录结构和脚本入口做统一整理。

---

## 说明

本仓库当前更适合作为 **项目集合仓库**，而不是单一应用仓库。三个项目分别对应不同方向：

- 企业知识库问答
- 医疗知识图谱智能问答
- LangGraph 搜索 Agent

如果后续需要，也可以把它们拆分成 3 个独立仓库分别维护。
