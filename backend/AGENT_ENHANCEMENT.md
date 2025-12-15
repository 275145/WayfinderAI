# 方案一：基于记忆与上下文的个性化智能规划系统 - 实现文档

## 📋 概述

本实现基于方案一的设计，为智能体系统增加了记忆能力、上下文管理和智能体间通信功能，实现了真正的个性化智能规划。

## 🏗️ 架构设计

### 核心模块

1. **记忆服务 (MemoryService)**
   - 位置: `app/services/memory_service.py`
   - 功能: 管理用户记忆和知识记忆的存储、检索和更新

2. **上下文管理器 (ContextManager)**
   - 位置: `app/services/context_manager.py`
   - 功能: 管理请求的上下文信息，支持在智能体间共享和传递

3. **智能体通信中心 (AgentCommunicationHub)**
   - 位置: `app/agents/agent_communication.py`
   - 功能: 实现智能体之间的消息传递和协商机制

4. **增强智能体基类 (EnhancedAgent)**
   - 位置: `app/agents/enhanced_agent.py`
   - 功能: 基于SimpleAgent的增强版本，支持记忆、上下文和通信

5. **专业智能体 (SpecializedAgents)**
   - 位置: `app/agents/specialized_agents.py`
   - 功能: 各个专业领域的智能体实现

## 📦 模块详解

### 1. 记忆服务模块

#### 功能特性

- **用户记忆管理**
  - 长期记忆：用户历史行程、偏好标签、反馈评分
  - 短期记忆：当前会话上下文、临时偏好
  - 元记忆：用户行为模式、决策习惯

- **知识记忆管理**
  - 目的地知识库：城市特色、季节特点、文化背景
  - 经验库：成功案例、失败教训、优化策略

#### 主要方法

```python
# 存储用户偏好
memory_service.store_user_preference(user_id, preference_type, preference_data)

# 检索用户偏好
preferences = memory_service.retrieve_user_preferences(user_id, preference_type)

# 检索相似行程
similar_trips = memory_service.retrieve_similar_trips(destination, preferences, limit=5)

# 存储目的地知识
memory_service.store_destination_knowledge(destination, knowledge_data)
```

### 2. 上下文管理器模块

#### 功能特性

- **上下文构建**: 从记忆系统检索相关历史信息，构建多维度上下文
- **上下文传递**: 各智能体共享统一上下文，上下文在智能体间流转和增强
- **上下文版本管理**: 支持上下文快照和回溯

#### 主要方法

```python
# 获取上下文管理器
context_manager = get_context_manager(request_id)

# 更新上下文
context_manager.update_context(agent_name, context_data, context_type)

# 共享数据
context_manager.share_data(key, data, from_agent)

# 获取共享数据
shared_data = context_manager.get_shared_data(key)
```

### 3. 智能体通信模块

#### 功能特性

- **消息传递**: 支持查询、建议、协商、反馈等多种消息类型
- **协商机制**: 当智能体间产生冲突时，通过多轮对话达成共识
- **广播消息**: 支持向所有智能体广播消息

#### 消息类型

- `QUERY`: 查询信息
- `SUGGESTION`: 提供建议
- `NEGOTIATION`: 协商请求
- `FEEDBACK`: 反馈信息
- `RESULT`: 结果通知
- `REQUEST`: 请求操作

#### 使用示例

```python
# 发送消息
response = agent.send_message_to_agent(
    receiver="酒店推荐专家",
    message_type=MessageType.SUGGESTION,
    content={"message": "景点搜索完成", "attraction_info": result}
)

# 协商
result = communication_hub.negotiate(
    initiator="规划专家",
    participants=["景点专家", "酒店专家"],
    topic="预算分配",
    proposals={"budget": 1000}
)
```

### 4. 增强智能体基类

#### 增强功能

- **记忆能力**: 自动检索用户历史偏好和相似行程
- **上下文感知**: 使用上下文管理器获取共享信息
- **通信能力**: 与其他智能体进行消息传递和协商

#### 关键特性

1. **增强的系统提示词**
   - 自动包含工具信息
   - 自动包含记忆上下文
   - 自动包含共享上下文信息

2. **智能记忆检索**
   - 根据用户ID检索历史偏好
   - 检索相似行程作为参考
   - 在系统提示词中注入记忆信息

3. **上下文共享**
   - 执行结果自动共享到上下文
   - 可以从上下文获取其他智能体的结果

### 5. 专业智能体实现

#### 景点搜索智能体 (AttractionSearchAgent)

- 参考用户历史偏好优化搜索策略
- 搜索完成后将结果共享给酒店智能体
- 支持接收其他智能体的请求

#### 酒店推荐智能体 (HotelRecommendationAgent)

- 基于景点位置信息优化酒店推荐
- 参考用户历史酒店选择
- 推荐完成后将结果共享给规划智能体

#### 天气查询智能体 (WeatherQueryAgent)

- 查询整个行程期间的天气
- 查询完成后将结果共享给规划智能体

#### 规划智能体 (PlannerAgent)

- 整合所有智能体的结果
- 参考用户历史行程和反馈
- 可以请求其他智能体提供更多信息
- 规划完成后存储用户偏好记忆

## 🔄 工作流程

### 1. 请求处理流程

```
用户请求
  ↓
创建上下文管理器
  ↓
检索用户记忆（偏好、相似行程）
  ↓
创建增强智能体（注入记忆和上下文）
  ↓
景点搜索Agent → 搜索景点 → 共享结果
  ↓
酒店推荐Agent → 推荐酒店（参考景点位置）→ 共享结果
  ↓
天气查询Agent → 查询天气 → 共享结果
  ↓
规划Agent → 整合信息 → 生成方案
  ↓
存储用户偏好记忆
  ↓
返回结果
```

### 2. 智能体间通信流程

```
景点Agent完成搜索
  ↓
发送SUGGESTION消息给酒店Agent
  ↓
酒店Agent接收消息，优化推荐策略
  ↓
酒店Agent完成推荐
  ↓
共享结果到上下文
  ↓
规划Agent从上下文获取所有信息
  ↓
生成最终方案
```

### 3. 记忆使用流程

```
用户请求到达
  ↓
检索用户历史偏好
  ↓
检索相似行程
  ↓
注入到智能体系统提示词
  ↓
智能体基于记忆优化策略
  ↓
执行任务
  ↓
存储新的偏好和反馈
```

## 🚀 使用示例

### 基本使用

```python
from app.agents.planner import PlannerAgent
from app.services.llm_service import LLMService

# 创建规划器
planner = PlannerAgent(LLMService())

# 规划行程（自动使用记忆和上下文）
plan = planner.plan_trip(request, user_id="user123")
```

### 手动使用记忆服务

```python
from app.services.memory_service import memory_service

# 存储用户偏好
memory_service.store_user_preference(
    user_id="user123",
    preference_type="destination_preference",
    preference_data={
        "destination": "北京",
        "preferences": ["历史", "文化"],
        "budget": "中等"
    }
)

# 检索用户偏好
preferences = memory_service.retrieve_user_preferences("user123")

# 检索相似行程
similar = memory_service.retrieve_similar_trips(
    destination="北京",
    preferences=["历史", "文化"],
    limit=5
)
```

### 使用上下文管理器

```python
from app.services.context_manager import get_context_manager

# 获取上下文管理器
context = get_context_manager("request123")

# 共享数据
context.share_data("attraction_locations", locations_data)

# 获取共享数据
locations = context.get_shared_data("attraction_locations")
```

## 📊 数据存储

### 记忆数据存储

- **位置**: `memory/user_memory.json`
- **格式**: JSON
- **结构**:
  ```json
  {
    "user_id": {
      "long_term_memory": {
        "preference_type": [...],
        "feedback_history": [...]
      },
      "short_term_memory": {
        "context_key": {...}
      },
      "meta_memory": {...}
    }
  }
  ```

### 知识记忆存储

- **位置**: `memory/knowledge_memory.json`
- **格式**: JSON
- **结构**:
  ```json
  {
    "destinations": {
      "北京": {
        "knowledge": [...]
      }
    },
    "experiences": {
      "success_case": [...],
      "failure_lesson": [...]
    }
  }
  ```

## 🔧 配置说明

### 记忆服务配置

```python
# 在 memory_service.py 中
memory_service = MemoryService(memory_dir="memory")
```

### 上下文管理器配置

```python
# 自动管理，无需手动配置
# 每个请求自动创建，请求完成后可清理
```

### 通信中心配置

```python
# 全局单例，自动管理
# 智能体注册时自动加入通信中心
```

## 📈 性能优化建议

1. **记忆检索优化**
   - 使用缓存减少重复检索
   - 限制检索数量避免性能问题
   - 异步加载记忆数据

2. **上下文管理优化**
   - 定期清理过期上下文
   - 限制上下文大小
   - 使用快照机制减少内存占用

3. **通信优化**
   - 批量处理消息
   - 异步消息处理
   - 消息队列机制

## 🐛 故障排查

### 常见问题

1. **记忆检索失败**
   - 检查 `memory/` 目录是否存在
   - 检查 JSON 文件格式是否正确
   - 检查用户ID是否正确

2. **上下文丢失**
   - 确保请求ID正确传递
   - 检查上下文管理器是否正确初始化

3. **智能体通信失败**
   - 检查智能体是否正确注册
   - 检查消息处理器是否正确注册
   - 查看日志了解详细错误

## 📝 后续优化方向

1. **记忆系统增强**
   - 向量数据库支持（语义搜索）
   - 记忆重要性评分
   - 自动记忆清理

2. **上下文系统增强**
   - 上下文压缩
   - 上下文版本控制
   - 分布式上下文管理

3. **通信系统增强**
   - 消息队列
   - 异步通信
   - 通信协议优化

## ✅ 实现检查清单

- [x] 记忆服务模块实现
- [x] 上下文管理器实现
- [x] 智能体通信中心实现
- [x] 增强智能体基类实现
- [x] 专业智能体实现
- [x] PlannerAgent集成
- [x] API路由更新
- [x] 日志和错误处理

---

**版本**: v1.0.0  
**实现日期**: 2024-01-15  
**维护者**: AI Assistant

