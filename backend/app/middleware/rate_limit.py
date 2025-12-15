"""
限流中间件
实现令牌桶算法进行请求限流
"""
import time
from typing import Dict, Tuple
from collections import defaultdict
from threading import Lock
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.observability.logger import default_logger as logger, get_request_id


class TokenBucket:
    """
    令牌桶算法实现
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        初始化令牌桶
        
        Args:
            capacity: 桶的容量（最大令牌数）
            refill_rate: 每秒补充的令牌数
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.time()
        self.lock = Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        尝试消费令牌
        
        Args:
            tokens: 需要消费的令牌数量
        
        Returns:
            如果成功消费返回True，否则返回False
        """
        with self.lock:
            # 补充令牌
            now = time.time()
            elapsed = now - self.last_refill
            tokens_to_add = elapsed * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now
            
            # 检查是否有足够的令牌
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def get_available_tokens(self) -> float:
        """
        获取当前可用的令牌数
        
        Returns:
            可用令牌数
        """
        with self.lock:
            now = time.time()
            elapsed = now - self.last_refill
            tokens_to_add = elapsed * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now
            return self.tokens


class RateLimiter:
    """
    限流器
    支持基于IP和全局的限流
    """
    
    def __init__(
        self,
        global_rate: Tuple[int, float] = (100, 1.0),  # (容量, 每秒补充数)
        per_ip_rate: Tuple[int, float] = (20, 1.0),  # (容量, 每秒补充数)
        enabled: bool = True
    ):
        """
        初始化限流器
        
        Args:
            global_rate: 全局限流配置 (容量, 每秒补充数)
            per_ip_rate: 每个IP的限流配置 (容量, 每秒补充数)
            enabled: 是否启用限流
        """
        self.enabled = enabled
        self.global_bucket = TokenBucket(global_rate[0], global_rate[1])
        self.per_ip_buckets: Dict[str, TokenBucket] = {}
        self.per_ip_config = per_ip_rate
        self.lock = Lock()
    
    def get_client_ip(self, request: Request) -> str:
        """
        获取客户端IP地址
        
        Args:
            request: FastAPI请求对象
        
        Returns:
            客户端IP地址
        """
        # 优先从X-Forwarded-For获取（适用于反向代理场景）
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # 从X-Real-IP获取
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 从客户端获取
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def get_ip_bucket(self, ip: str) -> TokenBucket:
        """
        获取或创建IP对应的令牌桶
        
        Args:
            ip: IP地址
        
        Returns:
            令牌桶实例
        """
        if ip not in self.per_ip_buckets:
            with self.lock:
                if ip not in self.per_ip_buckets:
                    self.per_ip_buckets[ip] = TokenBucket(
                        self.per_ip_config[0],
                        self.per_ip_config[1]
                    )
        return self.per_ip_buckets[ip]
    
    def is_allowed(self, request: Request) -> Tuple[bool, str]:
        """
        检查请求是否被允许
        
        Args:
            request: FastAPI请求对象
        
        Returns:
            (是否允许, 错误消息)
        """
        if not self.enabled:
            return True, ""
        
        # 检查全局限流
        if not self.global_bucket.consume():
            request_id = get_request_id()
            logger.warning(
                f"全局限流触发 - RequestID: {request_id}",
                extra={"request_id": request_id, "path": request.url.path}
            )
            return False, "请求过于频繁，请稍后再试"
        
        # 检查IP限流
        client_ip = self.get_client_ip(request)
        ip_bucket = self.get_ip_bucket(client_ip)
        
        if not ip_bucket.consume():
            request_id = get_request_id()
            logger.warning(
                f"IP限流触发 - IP: {client_ip}, RequestID: {request_id}",
                extra={"request_id": request_id, "ip": client_ip, "path": request.url.path}
            )
            return False, "您的请求过于频繁，请稍后再试"
        
        return True, ""


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    限流中间件
    """
    
    def __init__(self, app, rate_limiter: RateLimiter):
        """
        初始化限流中间件
        
        Args:
            app: FastAPI应用实例
            rate_limiter: 限流器实例
        """
        super().__init__(app)
        self.rate_limiter = rate_limiter
    
    async def dispatch(self, request: Request, call_next):
        """
        处理请求
        
        Args:
            request: FastAPI请求对象
            call_next: 下一个中间件或路由处理函数
        
        Returns:
            响应对象
        """
        # 跳过健康检查端点的限流
        if request.url.path == "/health":
            return await call_next(request)
        
        # 检查限流
        allowed, error_message = self.rate_limiter.is_allowed(request)
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=error_message
            )
        
        return await call_next(request)

