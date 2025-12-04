from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1 import trip as trip_v1
from .config import settings, logger

# 创建FastAPI应用实例
app = FastAPI(
    title="智能旅行助手 API",
    description="一个使用Agent和LLM进行智能行程规划的API服务。",
    version="1.0.0"
)

# 配置CORS中间件
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

@app.get("/health", tags=["Health Check"])
def health_check():
    """健康检查端点，用于确认服务是否正常运行。"""
    return {"status": "ok"}