# 智能旅行规划系统（Trip Planner）

基于 FastAPI + Vue3 + 多智能体 + 向量记忆 的智能行程规划应用，支持异步任务生成、行程版本管理、访客会话持久化和城市支持分级提示。

## 项目特性

- 智能行程生成：输入目的地、日期、偏好自动生成结构化行程
- 多智能体协作：景点、酒店、天气、规划智能体并行协作
- 异步任务化生成：`plan-async` + 任务进度查询接口
- 行程版本管理：版本历史、回滚、乐观锁冲突保护（409）
- 访客会话持久化：Redis 服务端 guest 会话 + 续期策略 + 可迁移会话标识
- 城市支持分级：`supported/beta/unsupported` 动态配置与提示文案
- 地图可视化与导出：高德地图展示行程点位，支持 PDF/图片导出

## 技术栈

### 后端

- FastAPI
- HelloAgents + MCP（`uvx amap-mcp-server`）
- OpenAI 兼容调用（当前可配 ModelScope/Qwen）
- Redis（用户、会话、行程、任务、版本）
- FAISS + Sentence-Transformers（向量记忆）

### 前端

- Vue 3 + TypeScript
- Vite + Element Plus
- Vue Router + Pinia
- 高德 JS API

## 目录结构

```text
trip_planner/
├─ backend/
│  ├─ app/
│  │  ├─ agents/
│  │  ├─ api/v1/
│  │  ├─ middleware/
│  │  ├─ services/
│  │  ├─ tools/
│  │  └─ data/city_support.json
│  ├─ tests/
│  ├─ requirements.txt
│  └─ run.py
├─ frontend/
│  ├─ src/components/
│  ├─ src/views/
│  ├─ src/services/
│  └─ src/types/
└─ README.md
```

## 环境要求

- Python 3.11（必须，3.9 会在类型语法上报错）
- Node.js 16+
- Redis 6+
- `uvx`（用于启动高德 MCP server）

## 快速启动

### 1. 后端

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
python run.py
```

后端默认地址：`http://localhost:8000`

### 2. 前端

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

前端默认地址：`http://localhost:5173`

## 关键配置（backend/.env）

至少需要：

- `LLM_API_KEY` / `OPENAI_API_KEY`
- `LLM_MODEL_ID`
- `LLM_BASE_URL`
- `AMAP_API_KEY`
- `UNSPLASH_ACCESS_KEY`
- `REDIS_HOST`
- `REDIS_PORT`
- `REDIS_PASSWORD`（若 Redis 开启认证）

城市支持配置文件：

- `CITY_CONFIG_PATH=app/data/city_support.json`

## 核心 API（v1）

### 行程生成与任务

- `POST /api/v1/trips/plan`：同步生成
- `POST /api/v1/trips/plan-async`：异步生成任务
- `GET /api/v1/trips/tasks/{task_id}`：查询任务状态与进度

### 行程管理

- `GET /api/v1/trips/list`：行程列表
- `GET /api/v1/trips/{trip_id}`：行程详情
- `PUT /api/v1/trips/{trip_id}`：更新行程（支持 `If-Match-Version`）
- `DELETE /api/v1/trips/{trip_id}`：删除行程

### 版本管理

- `GET /api/v1/trips/{trip_id}/versions`：版本历史
- `POST /api/v1/trips/{trip_id}/rollback?target_version={n}`：回滚到指定版本

### 城市支持

- `GET /api/v1/trips/city-support/{city}`：查询城市支持等级与提示
- `GET /api/v1/trips/cities`：查询全部城市配置

### 认证与访客

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/guest`

## 测试脚本

在项目根目录运行：

```bash
python backend/tests/test_enhanced_system.py
python backend/tests/test_task_and_version.py
python backend/tests/test_city_support.py
python backend/tests/test_trip_deletion.py
```

## 常见问题

### 1) Redis 连接失败：`Authentication required`

说明 Redis 实例开启了认证。请在 `backend/.env` 配置：

```env
REDIS_PASSWORD=你的密码
```

或关闭 Redis 服务端认证后重启 Redis。

### 2) 报错：`unsupported operand type(s) for |`

你在用 Python 3.9 运行。请切换到 Python 3.11 环境后启动。

### 3) 高德工具不可用：`amap_maps_text_search` not found

确认：

- 已安装并可执行 `uvx`
- `AMAP_API_KEY` 有效
- 后端日志里能看到 MCP 工具发现与注册成功

## 当前实现状态

- 异步任务化生成：已实现
- 版本历史/回滚/冲突保护：已实现
- Redis guest 服务端会话与续期：已实现
- 城市支持分级动态配置：已实现

