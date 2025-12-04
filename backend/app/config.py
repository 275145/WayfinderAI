import logging
import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# 配置日志记录
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class Settings(BaseSettings):
    """
    应用配置类，用于加载和管理环境变量。
    """
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')

    # LLM 配置
    LLM_MODEL_ID: Optional[str] = None
    LLM_API_KEY: Optional[str] = None
    LLM_BASE_URL: Optional[str] = None
    LLM_TIMEOUT: int = 100

    # 特定服务商的API Keys (用于自动检测)
    OPENAI_API_KEY: Optional[str] = None
    ZHIPU_API_KEY: Optional[str] = None
    MODELSCOPE_API_KEY: Optional[str] = None

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS 配置
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # 日志级别
    LOG_LEVEL: str = "INFO"

    # Unsplash API
    UNSPLASH_ACCESS_KEY: Optional[str] = None
    UNSPLASH_SECRET_KEY: Optional[str] = None

    # 高德地图 API
    AMAP_API_KEY: str

    # AMAP MCP Server
    AMAP_MCP_SERVER_URL: str = "http://127.0.0.1:8000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')

    def get_cors_origins_list(self) -> List[str]:
        """获取CORS origins列表"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(',')]

# 创建一个全局可用的配置实例
settings = Settings()

# 获取一个logger实例
logger = logging.getLogger(__name__)
logger.setLevel(settings.LOG_LEVEL)

logger.info("配置加载完成。")
