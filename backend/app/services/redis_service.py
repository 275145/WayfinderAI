"""
Redis服务模块
提供用户数据的持久化存储
"""
import json
import hashlib
from typing import Dict, Optional, Any
from contextlib import contextmanager
import redis
import bcrypt
from app.observability.logger import default_logger as logger
from app.config import settings


# 密码加密轮数
BCRYPT_ROUNDS = 12


class RedisService:
    """
    Redis服务类，负责用户数据的持久化存储
    """
    
    def __init__(self):
        """初始化Redis连接"""
        self._redis_client: Optional[redis.Redis] = None
        self._initialize_redis()
    
    def _initialize_redis(self):
        """初始化Redis连接"""
        try:
            self._redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=settings.REDIS_DECODE_RESPONSES,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # 测试连接
            self._redis_client.ping()
            logger.info(f"Redis连接成功 - {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except Exception as e:
            logger.error(f"Redis连接失败: {str(e)}")
            raise RuntimeError(f"无法连接到Redis服务器: {str(e)}")
    
    @property
    def redis(self) -> redis.Redis:
        """获取Redis客户端实例"""
        if self._redis_client is None:
            raise RuntimeError("Redis客户端未初始化")
        return self._redis_client
    
    def _generate_user_key(self, username: str) -> str:
        """生成用户数据的Redis键"""
        return f"user:{username}"
    
    def _generate_username_index_key(self, user_id: str) -> str:
        """生成用户名索引的Redis键"""
        return f"user_index:{user_id}"
    
    def _hash_password(self, password: str) -> str:
        """
        使用bcrypt加密密码
        
        注意：bcrypt算法有72字节的密码长度限制
        对于长密码，先使用SHA256哈希再进行bcrypt加密
        
        Args:
            password: 明文密码
            
        Returns:
            加密后的密码哈希
        """
        # 处理长密码：如果超过72字节，先使用SHA256哈希
        password_bytes = password.encode('utf-8')
        
        if len(password_bytes) > 72:
            logger.info(f"密码长度超过72字节，使用SHA256预处理")
            # 对于长密码，使用SHA256哈希后再加密
            sha256_hash = hashlib.sha256(password_bytes).digest()
            # 取前72字节
            password_bytes = sha256_hash[:72]
        
        # 使用bcrypt直接加密（避免passlib的兼容性问题）
        salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        return hashed.decode('utf-8')
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        验证密码
        
        Args:
            plain_password: 明文密码
            hashed_password: 加密后的密码哈希
            
        Returns:
            密码是否匹配
        """
        try:
            # 处理密码编码
            plain_password_bytes = plain_password.encode('utf-8')
            hashed_password_bytes = hashed_password.encode('utf-8')
            
            # 使用bcrypt直接验证
            result = bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)
            return result
        except Exception as e:
            logger.error(f"密码验证失败: {str(e)}")
            return False
    
    def create_user(
        self,
        user_id: str,
        username: str,
        password: str,
        phone: Optional[str] = None,
        gender: str = "other",
        birthday: Optional[str] = None,
        bio: Optional[str] = None,
        travel_preferences: list = None,
        avatar_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建新用户
        
        Args:
            user_id: 用户ID
            username: 用户名
            password: 明文密码
            phone: 手机号
            gender: 性别
            birthday: 生日
            bio: 个人简介
            travel_preferences: 旅行偏好
            avatar_url: 头像URL
            
        Returns:
            创建的用户数据
            
        Raises:
            ValueError: 用户名已存在
        """
        user_key = self._generate_user_key(username)
        
        # 检查用户名是否已存在
        if self.redis.exists(user_key):
            raise ValueError(f"用户名 '{username}' 已存在")
        
        # 加密密码
        hashed_password = self._hash_password(password)
        
        # 构建用户数据
        # 注意：Redis的hset只支持str, int, float, bytes类型
        # 所有字段必须是这些类型之一
        user_data = {
            "user_id": str(user_id),
            "username": str(username),
            "password": str(hashed_password),
            "phone": str(phone) if phone is not None else "",
            "gender": str(gender),
            "birthday": str(birthday) if birthday is not None else "",
            "bio": str(bio) if bio is not None else "",
            "travel_preferences": json.dumps(travel_preferences or []),  # 列表转为JSON字符串
            "avatar_url": str(avatar_url) if avatar_url is not None else "",
            "created_at": ""
        }
        
        # 保存用户数据
        try:
            self.redis.hset(user_key, mapping=user_data)
            # 创建用户名到ID的索引
            self.redis.set(self._generate_username_index_key(user_id), username)
            logger.info(f"用户创建成功 - Username: {username}, UserID: {user_id}")
            return user_data
        except Exception as e:
            logger.error(f"用户创建失败: {str(e)}")
            raise RuntimeError(f"用户创建失败: {str(e)}")
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        根据用户名获取用户数据
        
        Args:
            username: 用户名
            
        Returns:
            用户数据，如果不存在则返回None
        """
        try:
            user_key = self._generate_user_key(username)
            user_data = self.redis.hgetall(user_key)
            
            if not user_data:
                return None
            
            # 处理travel_preferences字段（JSON数组）
            if "travel_preferences" in user_data:
                try:
                    user_data["travel_preferences"] = json.loads(user_data["travel_preferences"])
                except (json.JSONDecodeError, TypeError):
                    user_data["travel_preferences"] = []
            
            return user_data
        except Exception as e:
            logger.error(f"获取用户数据失败: {str(e)}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        根据用户ID获取用户数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户数据，如果不存在则返回None
        """
        try:
            # 通过索引查找用户名
            username = self.redis.get(self._generate_username_index_key(user_id))
            if not username:
                return None
            
            return self.get_user_by_username(username)
        except Exception as e:
            logger.error(f"通过ID获取用户数据失败: {str(e)}")
            return None
    
    def verify_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        验证用户登录凭证
        
        Args:
            username: 用户名
            password: 明文密码
            
        Returns:
            验证成功返回用户数据，失败返回None
        """
        user_data = self.get_user_by_username(username)
        
        if not user_data:
            logger.warning(f"登录失败 - 用户不存在: {username}")
            return None
        
        hashed_password = user_data.get("password")
        if not hashed_password:
            logger.error(f"用户数据异常 - 没有密码哈希: {username}")
            return None
        
        if not self._verify_password(password, hashed_password):
            logger.warning(f"登录失败 - 密码错误: {username}")
            return None
        
        logger.info(f"用户验证成功 - Username: {username}")
        return user_data
    
    def update_user(
        self,
        username: str,
        **updates
    ) -> Optional[Dict[str, Any]]:
        """
        更新用户数据（密码除外）
        
        Args:
            username: 用户名
            **updates: 要更新的字段
            
        Returns:
            更新后的用户数据
            
        Raises:
            ValueError: 用户不存在
        """
        user_key = self._generate_user_key(username)
        
        # 检查用户是否存在
        if not self.redis.exists(user_key):
            raise ValueError(f"用户 '{username}' 不存在")
        
        # 过滤不允许更新的字段
        updates.pop("user_id", None)
        updates.pop("username", None)
        updates.pop("password", None)
        updates.pop("created_at", None)
        
        # 处理travel_preferences字段
        if "travel_preferences" in updates:
            updates["travel_preferences"] = json.dumps(updates["travel_preferences"])
        
        # 确保所有值都是字符串类型（Redis hset只支持str, int, float, bytes）
        clean_updates = {}
        for key, value in updates.items():
            if value is not None:
                clean_updates[key] = str(value)
            else:
                clean_updates[key] = ""
        
        try:
            # 更新用户数据
            if clean_updates:
                self.redis.hset(user_key, mapping=clean_updates)
            
            # 返回更新后的用户数据
            updated_user = self.get_user_by_username(username)
            logger.info(f"用户数据更新成功 - Username: {username}")
            return updated_user
        except Exception as e:
            logger.error(f"用户数据更新失败: {str(e)}")
            raise RuntimeError(f"用户数据更新失败: {str(e)}")
    
    def update_password(self, username: str, old_password: str, new_password: str) -> bool:
        """
        更新用户密码
        
        Args:
            username: 用户名
            old_password: 原密码
            new_password: 新密码
            
        Returns:
            是否更新成功
            
        Raises:
            ValueError: 用户不存在或原密码错误
        """
        # 验证原密码
        user_data = self.verify_user(username, old_password)
        if not user_data:
            raise ValueError("用户不存在或原密码错误")
        
        # 加密新密码
        hashed_password = self._hash_password(new_password)
        
        try:
            user_key = self._generate_user_key(username)
            self.redis.hset(user_key, "password", hashed_password)
            logger.info(f"用户密码更新成功 - Username: {username}")
            return True
        except Exception as e:
            logger.error(f"用户密码更新失败: {str(e)}")
            raise RuntimeError(f"用户密码更新失败: {str(e)}")
    
    def delete_user(self, username: str) -> bool:
        """
        删除用户
        
        Args:
            username: 用户名
            
        Returns:
            是否删除成功
        """
        try:
            user_data = self.get_user_by_username(username)
            if not user_data:
                return False
            
            user_id = user_data["user_id"]
            user_key = self._generate_user_key(username)
            
            # 删除用户数据和索引
            self.redis.delete(user_key)
            self.redis.delete(self._generate_username_index_key(user_id))
            
            logger.info(f"用户删除成功 - Username: {username}")
            return True
        except Exception as e:
            logger.error(f"用户删除失败: {str(e)}")
            return False
    
    def check_username_exists(self, username: str) -> bool:
        """
        检查用户名是否存在
        
        Args:
            username: 用户名
            
        Returns:
            用户名是否存在
        """
        try:
            user_key = self._generate_user_key(username)
            return self.redis.exists(user_key) > 0
        except Exception as e:
            logger.error(f"检查用户名存在性失败: {str(e)}")
            return False
    
    def get_all_usernames(self) -> list:
        """
        获取所有用户名列表
        
        Returns:
            用户名列表
        """
        try:
            # 使用SCAN遍历所有用户键
            keys = []
            for key in self.redis.scan_iter(match="user:*"):
                keys.append(key)
            
            usernames = [key.replace("user:", "") for key in keys]
            return usernames
        except Exception as e:
            logger.error(f"获取用户名列表失败: {str(e)}")
            return []
    
    def close(self):
        """关闭Redis连接"""
        if self._redis_client:
            try:
                self._redis_client.close()
                logger.info("Redis连接已关闭")
            except Exception as e:
                logger.error(f"关闭Redis连接失败: {str(e)}")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


# 创建全局Redis服务实例
redis_service = RedisService()