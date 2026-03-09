"""
用户认证中间件
支持JWT令牌认证和游客模式
"""
import jwt
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.observability.logger import default_logger as logger
from app.config import settings
from app.services.redis_service import redis_service

class AuthMiddleware(BaseHTTPMiddleware):
    """用户认证中间件"""
    
    def __init__(self, app, jwt_secret: str = None, jwt_expiry_hours: int = 24):
        super().__init__(app)
        self.jwt_secret = jwt_secret or settings.JWT_SECRET
        self.jwt_expiry_hours = jwt_expiry_hours
        
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        认证处理流程
        1. 检查Authorization头中的JWT令牌
        2. 如果没有令牌，检查Cookie中的访客ID
        3. 如果都没有，创建新的访客ID
        4. 将用户信息添加到请求状态中
        """
        # 跳过健康检查和认证端点
        if request.url.path in [
            "/health",
            "/api/v1/auth/login",
            "/api/v1/auth/register"
        ]:
            return await call_next(request)
            
        user_info = None
        need_set_guest_cookie = False
        guest_id = None
        
        # 1. 尝试JWT认证
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            user_info = self._verify_jwt_token(token)
            if user_info:
                logger.info(f"JWT认证成功 - UserID: {user_info['user_id']}")
        
        # 2. 尝试访客认证
        if not user_info:
            # 优先使用可迁移的Header会话标识（支持清Cookie后恢复/跨设备迁移）
            guest_id = request.headers.get("X-Guest-Session") or request.cookies.get("guest_id")
            if guest_id:
                # 服务端会话表（Redis） + 续期
                user_info = redis_service.create_or_get_guest_session(guest_id)
                logger.info(f"访客认证成功 - GuestID: {guest_id}")
            else:
                # 创建新的访客会话
                guest_id = str(uuid.uuid4())
                user_info = redis_service.create_or_get_guest_session(guest_id)
                need_set_guest_cookie = True
                logger.info(f"创建新访客会话 - GuestID: {guest_id}")
        
        # 将用户信息添加到请求状态
        request.state.user = user_info
        response = await call_next(request)

        # 为新访客设置cookie（必须在响应阶段设置）
        if need_set_guest_cookie and guest_id:
            response.set_cookie(
                key="guest_id",
                value=guest_id,
                max_age=int(timedelta(days=30).total_seconds()),
                httponly=True,
                secure=False,  # 开发环境设为False，生产环境应为True
                samesite="lax"
            )

        return response
    
    def _verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(
                token, 
                self.jwt_secret, 
                algorithms=["HS256"]
            )
            
            # 检查令牌是否过期
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.now():
                return None
                
            return {
                "user_id": payload.get("user_id"),
                "user_type": "registered",
                "username": payload.get("username")
            }
        except jwt.ExpiredSignatureError:
            logger.warning("JWT令牌已过期")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"无效的JWT令牌: {e}")
            return None
        except Exception as e:
            logger.error(f"JWT验证过程中发生错误: {e}")
            return None
    
    @staticmethod
    def generate_jwt_token(user_id: str, username: str,
                          jwt_secret: str = None, expiry_hours: int = 24) -> str:
        """生成JWT令牌"""
        if not jwt_secret:
            jwt_secret = settings.JWT_SECRET
            
        payload = {
            "user_id": user_id,
            "username": username,
            "iat": int(datetime.now().timestamp()),
            "exp": int((datetime.now() + timedelta(hours=expiry_hours)).timestamp())
        }
        
        return jwt.encode(payload, jwt_secret, algorithm="HS256")


def get_current_user(request: Request) -> Dict[str, Any]:
    """从请求中获取当前用户信息"""
    if hasattr(request.state, "user"):
        return request.state.user
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="未认证的用户"
    )


def get_user_id(request: Request) -> str:
    """从请求中获取用户ID"""
    user = get_current_user(request)
    return user["user_id"]
