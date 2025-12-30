"""
用户认证API接口
提供登录、注册等功能
"""
from fastapi import APIRouter, Request, HTTPException, status, Depends
from pydantic import BaseModel, validator
from typing import Optional
from app.middleware.auth import AuthMiddleware, get_current_user, get_user_id
from app.observability.logger import default_logger as logger
from app.config import settings

router = APIRouter()

# 用户模型
class UserLogin(BaseModel):
    """用户登录请求"""
    username: str
    password: str

class UserRegister(BaseModel):
    """用户注册请求"""
    username: str
    password: str

class UserUpdate(BaseModel):
    """用户信息更新请求"""
    username: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    birthday: Optional[str] = None
    bio: Optional[str] = None
    travel_preferences: Optional[list] = None
    avatar_url: Optional[str] = None

    @validator('gender')
    def validate_gender(cls, v):
        if v is not None and v not in ['male', 'female', 'other']:
            raise ValueError('性别必须是 male、female 或 other')
        return v

class ChangePassword(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str

class UserResponse(BaseModel):
    """用户响应"""
    user_id: str
    username: str
    user_type: str
    phone: Optional[str] = None
    gender: Optional[str] = None
    birthday: Optional[str] = None
    bio: Optional[str] = None
    travel_preferences: Optional[list] = None
    avatar_url: Optional[str] = None

class AuthToken(BaseModel):
    """认证令牌响应"""
    access_token: str
    token_type: str
    user: UserResponse

# 简单的用户存储（生产环境应使用数据库）
USERS_DB = {}

@router.post("/login", response_model=AuthToken)
def login(request: Request, login_data: UserLogin):
    """
    用户登录
    
    Args:
        request: FastAPI请求对象
        login_data: 登录数据
        
    Returns:
        JWT令牌和用户信息
    """
    logger.info(f"用户登录尝试 - 账号: {login_data.username}")
    
    # 在简单存储中查找用户（生产环境应使用数据库验证）
    user = None
    for key, value in USERS_DB.items():
        if value.get("username") == login_data.username:
            user = value
            break
    
    if not user or user.get("password") != login_data.password:
        logger.warning(f"登录失败 - 账号: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账号或密码错误"
        )
    
    # 生成JWT令牌
    access_token = AuthMiddleware.generate_jwt_token(
        user_id=user["user_id"],
        username=user["username"]
    )
    
    logger.info(f"用户登录成功 - UserID: {user['user_id']}")
    
    return AuthToken(
        access_token=access_token,
        token_type="Bearer",
        user=UserResponse(
            user_id=user["user_id"],
            username=user["username"],
            user_type="registered",
            phone=user.get("phone"),
            gender=user.get("gender"),
            birthday=user.get("birthday"),
            bio=user.get("bio"),
            travel_preferences=user.get("travel_preferences"),
            avatar_url=user.get("avatar_url")
        )
    )

@router.post("/register", response_model=AuthToken)
def register(request: Request, register_data: UserRegister):
    """
    用户注册
    
    Args:
        request: FastAPI请求对象
        register_data: 注册数据
        
    Returns:
        JWT令牌和用户信息
    """
    logger.info(f"用户注册尝试 - 账号: {register_data.username}")
    
    # 检查用户是否已存在
    for key, value in USERS_DB.items():
        if value.get("username") == register_data.username:
            logger.warning(f"注册失败，用户已存在 - 账号: {register_data.username}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="该账号已被注册"
            )
    
    # 创建新用户（生产环境应使用数据库）
    import uuid
    user_id = str(uuid.uuid4())
    # 使用用户名作为键
    USERS_DB[f"email_{user_id}"] = {
        "user_id": user_id,
        "username": register_data.username,
        "password": register_data.password,  # 生产环境应存储哈希值
        "created_at": "2024-01-01T00:00:00",  # 简化时间戳
        "phone": None,
        "gender": "other",
        "birthday": None,
        "bio": None,
        "travel_preferences": [],
        "avatar_url": None
    }
    
    # 生成JWT令牌
    access_token = AuthMiddleware.generate_jwt_token(
        user_id=user_id,
        username=register_data.username
    )
    
    logger.info(f"用户注册成功 - UserID: {user_id}")
    
    return AuthToken(
        access_token=access_token,
        token_type="Bearer",
        user=UserResponse(
            user_id=user_id,
            username=register_data.username,
            user_type="registered"
        )
    )

@router.get("/me", response_model=UserResponse)
def get_current_user_info(request: Request, current_user: dict = Depends(get_current_user)):
    """
    获取当前用户信息
    
    Args:
        request: FastAPI请求对象
        current_user: 当前认证用户信息
        
    Returns:
        用户信息
    """
    user_username = current_user.get("username", "")
    
    # 从数据库获取用户完整信息
    user = None
    for key, value in USERS_DB.items():
        if value.get("username") == user_username:
            user = value
            break
    
    if not user:
        # 如果找不到用户，返回基本信息
        return UserResponse(
            user_id=current_user["user_id"],
            username=current_user.get("username", ""),
            user_type="registered"
        )
    
    return UserResponse(
        user_id=current_user["user_id"],
        username=current_user.get("username", ""),
        user_type=current_user.get("user_type", "registered"),
        phone=user.get("phone"),
        gender=user.get("gender"),
        birthday=user.get("birthday"),
        bio=user.get("bio"),
        travel_preferences=user.get("travel_preferences", []),
        avatar_url=user.get("avatar_url")
    )

@router.put("/me", response_model=UserResponse)
def update_user_profile(
    request: Request,
    update_data: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    更新用户资料
    
    Args:
        request: FastAPI请求对象
        update_data: 更新数据
        current_user: 当前认证用户信息
        
    Returns:
        更新后的用户信息
    """
    user_username = current_user.get("username", "")
    
    # 从数据库获取用户信息
    user = None
    for key, value in USERS_DB.items():
        if value.get("username") == user_username:
            user = value
            break
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 更新用户信息（只更新提供的字段）
    update_dict = update_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        if value is not None:
            user[key] = value
    
    logger.info(f"用户资料更新成功 - UserID: {user['user_id']}")
    
    return UserResponse(
        user_id=user["user_id"],
        username=user["username"],
        user_type="registered",
        phone=user.get("phone"),
        gender=user.get("gender"),
        birthday=user.get("birthday"),
        bio=user.get("bio"),
        travel_preferences=user.get("travel_preferences", []),
        avatar_url=user.get("avatar_url")
    )

@router.post("/change-password")
def change_password(
    request: Request,
    password_data: ChangePassword,
    current_user: dict = Depends(get_current_user)
):
    """
    修改密码
    
    Args:
        request: FastAPI请求对象
        password_data: 密码数据
        current_user: 当前认证用户信息
        
    Returns:
        操作结果
    """
    user_username = current_user.get("username", "")
    
    # 从数据库获取用户信息
    user = None
    for key, value in USERS_DB.items():
        if value.get("username") == user_username:
            user = value
            break
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 验证原密码
    if user.get("password") != password_data.old_password:
        logger.warning(f"密码修改失败 - 原密码错误 - UserID: {user['user_id']}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="原密码错误"
        )
    
    # 更新密码
    user["password"] = password_data.new_password
    
    logger.info(f"用户密码修改成功 - UserID: {user['user_id']}")
    
    return {"message": "密码修改成功"}

@router.post("/logout")
def logout(request: Request, current_user: dict = Depends(get_current_user)):
    """
    退出登录
    
    Args:
        request: FastAPI请求对象
        current_user: 当前认证用户信息
        
    Returns:
        操作结果
    """
    user_id = current_user.get("user_id", "unknown")
    user_type = current_user.get("user_type", "unknown")
    
    logger.info(f"用户退出登录 - UserID: {user_id}, UserType: {user_type}")
    
    # 生产环境可能需要：
    # 1. 将JWT令牌加入黑名单
    # 2. 清除会话数据
    # 3. 记录退出时间等
    
    return {"message": "退出登录成功"}