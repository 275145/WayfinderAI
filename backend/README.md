# 智能旅行规划系统 - 后端文档

## 📋 目录

- [系统架构](#系统架构)
- [日志系统](#日志系统)
- [限流、熔断、降级](#限流熔断降级)
- [错误处理框架](#错误处理框架)
- [快速开始](#快速开始)
- [配置说明](#配置说明)

## 🏗️ 系统架构

```
backend/
├── app/
│   ├── agents/              # Agent 智能体
│   ├── api/v1/              # API 接口
│   ├── models/              # 数据模型
│   ├── services/            # 业务服务
│   ├── tools/               # MCP 工具
│   ├── middleware/          # 中间件
│   │   ├── request_id.py    # 请求ID追踪
│   │   ├── rate_limit.py    # 限流中间件
│   │   ├── circuit_breaker.py  # 熔断器
│   │   └── degradation.py   # 降级策略
│   ├── observability/       # 可观测性
│   │   └── logger.py       # 日志系统
│   └── exceptions/          # 异常处理
│       ├── error_codes.py   # 错误码定义
│       ├── custom_exceptions.py  # 自定义异常
│       └── exception_handler.py  # 异常处理器
└── requirements.txt
```

## 📝 日志系统

### 功能特性

- ✅ **结构化日志**: JSON格式，便于日志收集和分析
- ✅ **请求ID追踪**: 每个请求都有唯一ID，方便追踪
- ✅ **日志轮转**: 自动轮转，防止日志文件过大
- ✅ **多级别日志**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- ✅ **双格式输出**: 控制台人类可读，文件JSON格式
- ✅ **错误日志分离**: 错误日志单独文件存储

### 使用方法

#### 基础使用

```python
from app.observability.logger import default_logger

# 记录不同级别的日志
logger.info("这是一条信息日志")
logger.warning("这是一条警告日志")
logger.error("这是一条错误日志", exc_info=True)  # exc_info=True 会记录堆栈信息
```

#### 带上下文的日志

```python
from app.observability.logger import log_with_context

log_with_context(
    logger,
    logging.INFO,
    "处理用户请求",
    user_id="12345",
    action="plan_trip",
    destination="北京"
)
```

#### 获取请求ID

```python
from app.observability.logger import get_request_id

request_id = get_request_id()
logger.info(f"当前请求ID: {request_id}")
```

### 日志文件位置

- **所有日志**: `logs/app.log` (JSON格式)
- **错误日志**: `logs/error.log` (仅ERROR及以上级别，JSON格式)

### 日志格式示例

**控制台输出（人类可读）**:
```
[2024-01-15 10:30:45] INFO     [trip_planner] [RequestID: abc-123] 接收到新的行程规划请求 | trip.plan_trip:26
```

**文件输出（JSON格式）**:
```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "level": "INFO",
  "logger": "trip_planner",
  "message": "接收到新的行程规划请求",
  "request_id": "abc-123",
  "module": "trip",
  "function": "plan_trip",
  "line": 26,
  "context": {
    "destination": "北京",
    "budget": "中等"
  }
}
```

## 🚦 限流、熔断、降级

### 限流 (Rate Limiting)

#### 功能说明

- **令牌桶算法**: 平滑限流，允许突发流量
- **全局限流**: 限制整个服务的请求速率
- **IP限流**: 限制单个IP的请求速率
- **自动配置**: 默认已启用，可在代码中调整

#### 配置参数

```python
# 在 app/main.py 中配置
rate_limiter = RateLimiter(
    global_rate=(100, 1.0),    # 全局：100个请求/秒
    per_ip_rate=(20, 1.0),     # 每个IP：20个请求/秒
    enabled=True                # 是否启用
)
```

#### 限流响应

当请求被限流时，返回 `429 Too Many Requests`:

```json
{
  "success": false,
  "error_code": 4003,
  "error_message": "请求过于频繁，请稍后再试",
  "request_id": "abc-123"
}
```

### 熔断器 (Circuit Breaker)

#### 功能说明

- **三种状态**: CLOSED（正常）、OPEN（熔断）、HALF_OPEN（半开）
- **自动恢复**: 熔断后自动尝试恢复
- **失败计数**: 达到阈值自动熔断

#### 使用方法

```python
from app.middleware.circuit_breaker import circuit_breaker_manager

# 获取熔断器
breaker = circuit_breaker_manager.get_breaker(
    "llm_service",
    failure_threshold=5,      # 失败5次后熔断
    success_threshold=2,      # 半开状态下成功2次后恢复
    timeout=60.0              # 熔断后等待60秒
)

# 通过熔断器调用函数
try:
    result = breaker.call(llm_service.invoke, messages)
except Exception as e:
    # 熔断器已打开或调用失败
    logger.error(f"服务不可用: {e}")
```

#### 装饰器方式

```python
from app.middleware.degradation import circuit_breaker_with_fallback

@circuit_breaker_with_fallback(
    breaker_name="llm_service",
    fallback_value="",  # 降级返回值
    failure_threshold=5,
    timeout=60.0
)
def call_llm(messages):
    return llm_service.invoke(messages)
```

### 降级策略 (Degradation)

#### 功能说明

- **自动降级**: 服务失败时自动使用降级方案
- **灵活配置**: 支持函数降级和值降级

#### 使用方法

**装饰器方式**:
```python
from app.middleware.degradation import fallback_response

@fallback_response(default_value={"error": "服务暂时不可用"})
def get_attractions(destination):
    # 如果调用失败，返回默认值
    return external_api.get_attractions(destination)
```

**策略类方式**:
```python
from app.middleware.degradation import DegradationStrategy

def fallback_func(destination):
    # 降级函数：返回缓存数据或默认数据
    return get_cached_attractions(destination)

strategy = DegradationStrategy(fallback_func=fallback_func)
result = strategy.execute(
    main_func=get_attractions,
    destination="北京",
    fallback_value=[]
)
```

## ⚠️ 错误处理框架

### 错误码体系

错误码定义在 `app/exceptions/error_codes.py`:

```python
class ErrorCode(IntEnum):
    # 通用错误 (1000-1999)
    SUCCESS = 0
    UNKNOWN_ERROR = 1000
    INVALID_REQUEST = 1001
    
    # 业务错误 (2000-2999)
    TRIP_PLAN_FAILED = 2000
    DESTINATION_NOT_FOUND = 2001
    
    # 服务错误 (3000-3999)
    LLM_SERVICE_ERROR = 3000
    LLM_TIMEOUT = 3001
    
    # 系统错误 (4000-4999)
    CIRCUIT_BREAKER_OPEN = 4002
    RATE_LIMIT_EXCEEDED = 4003
```

### 自定义异常

#### 异常类型

- `BaseAppException`: 基础异常类
- `BusinessException`: 业务异常
- `ServiceException`: 服务异常
- `ValidationException`: 参数验证异常
- `ExternalServiceException`: 外部服务异常
- `LLMServiceException`: LLM服务异常
- `MapServiceException`: 地图服务异常
- `ImageServiceException`: 图片服务异常

#### 使用示例

```python
from app.exceptions.custom_exceptions import BusinessException
from app.exceptions.error_codes import ErrorCode

# 抛出业务异常
if not destination:
    raise BusinessException(
        ErrorCode.MISSING_PARAMETER,
        message="目的地不能为空",
        details={"field": "destination"}
    )

# 抛出服务异常
try:
    result = llm_service.invoke(messages)
except Exception as e:
    raise LLMServiceException(
        ErrorCode.LLM_SERVICE_ERROR,
        message=f"LLM服务调用失败: {str(e)}",
        details={"error_type": type(e).__name__}
    )
```

### 错误响应格式

所有错误都会返回统一的JSON格式:

```json
{
  "success": false,
  "error_code": 2000,
  "error_message": "行程规划失败",
  "details": {
    "field": "destination",
    "message": "目的地不能为空"
  },
  "request_id": "abc-123"
}
```

### 全局异常处理

全局异常处理器会自动处理所有异常:

- ✅ **自定义异常**: 返回业务错误响应
- ✅ **验证异常**: 返回参数验证错误
- ✅ **HTTP异常**: 返回HTTP错误响应
- ✅ **未知异常**: 返回500错误，记录详细日志

## 🚀 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件:

```env
# LLM配置
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.example.com/v1
LLM_MODEL_ID=gpt-4

# 高德地图
AMAP_API_KEY=your_amap_key

# 服务器配置
HOST=0.0.0.0
PORT=8000

# 日志配置
LOG_LEVEL=INFO

# CORS配置
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 3. 启动服务

```bash
python run.py
```

服务将运行在 `http://localhost:8000`

## ⚙️ 配置说明

### 日志配置

在代码中配置日志:

```python
from app.observability.logger import setup_logger

logger = setup_logger(
    name="my_service",
    log_level="INFO",           # 日志级别
    log_dir="logs",              # 日志目录
    enable_file_logging=True,    # 启用文件日志
    enable_console_logging=True, # 启用控制台日志
    max_bytes=10 * 1024 * 1024, # 单个日志文件最大10MB
    backup_count=5               # 保留5个备份文件
)
```

### 限流配置

在 `app/main.py` 中调整限流参数:

```python
rate_limiter = RateLimiter(
    global_rate=(100, 1.0),    # (容量, 每秒补充数)
    per_ip_rate=(20, 1.0),     # (容量, 每秒补充数)
    enabled=True
)
```

### 熔断器配置

在代码中配置熔断器:

```python
breaker = circuit_breaker_manager.get_breaker(
    "service_name",
    failure_threshold=5,    # 失败次数阈值
    success_threshold=2,     # 成功次数阈值
    timeout=60.0             # 熔断等待时间（秒）
)
```

## 📊 监控和调试

### 查看日志

```bash
# 查看所有日志
tail -f logs/app.log

# 查看错误日志
tail -f logs/error.log

# 使用jq格式化JSON日志
tail -f logs/app.log | jq
```

### 请求追踪

每个请求都有唯一的请求ID，在响应头中返回:

```
X-Request-ID: abc-123-def-456
```

在日志中搜索请求ID可以追踪整个请求的处理过程。

### 健康检查

```bash
curl http://localhost:8000/health
```

## 🔧 最佳实践

1. **日志记录**:
   - 使用适当的日志级别
   - 记录关键业务信息
   - 错误时使用 `exc_info=True` 记录堆栈

2. **异常处理**:
   - 使用自定义异常而非通用Exception
   - 提供有意义的错误消息
   - 包含必要的上下文信息

3. **限流配置**:
   - 根据实际负载调整限流参数
   - 监控限流触发情况
   - 为不同端点设置不同限流策略

4. **熔断器使用**:
   - 为关键外部服务配置熔断器
   - 设置合理的失败阈值
   - 实现降级方案

## 📝 更新日志

### v1.0.0 (2024-01-15)

- ✅ 实现结构化日志系统
- ✅ 实现请求ID追踪
- ✅ 实现限流中间件
- ✅ 实现熔断器
- ✅ 实现降级策略
- ✅ 实现统一错误处理框架
- ✅ 实现全局异常处理器

---

**维护者**: AI Assistant  
**版本**: v1.0.0

