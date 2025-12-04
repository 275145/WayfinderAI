from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1 import trip as trip_v1
from .config import settings
from .observability.logger import setup_logger, default_logger
from .middleware.request_id import RequestIDMiddleware
from .middleware.rate_limit import RateLimitMiddleware, RateLimiter
from .exceptions.exception_handler import global_exception_handler

# 设置日志系统
logger = setup_logger(
    name="trip_planner",
    log_level=settings.LOG_LEVEL,
    enable_file_logging=True,
    enable_console_logging=True
)

# 创建FastAPI应用实例
app = FastAPI(
    title="智能旅行助手 API",
    description="一个使用Agent和LLM进行智能行程规划的API服务。",
    version="1.0.0"
)

# 注册全局异常处理器
app.add_exception_handler(Exception, global_exception_handler)

# 配置中间件（注意顺序很重要）
# 1. 请求ID中间件（最外层，最先执行）
app.add_middleware(RequestIDMiddleware)

# 2. 限流中间件
rate_limiter = RateLimiter(
    global_rate=(100, 1.0),  # 全局：100个请求/秒
    per_ip_rate=(20, 1.0),  # 每个IP：20个请求/秒
    enabled=True
)
app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)

# 3. CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含v1版本的API路由
app.include_router(trip_v1.router, prefix="/api/v1/trips", tags=["Trip Planning"])

@app.on_event("startup")
def on_startup():
    """应用启动时执行"""
    logger.info("智能旅行助手API已启动")
    logger.info("已启用功能: 日志系统、请求ID追踪、限流、熔断、降级、异常处理")

@app.get("/health", tags=["Health Check"])
def health_check():
    """健康检查端点，用于确认服务是否正常运行。"""
    return {"status": "ok"}