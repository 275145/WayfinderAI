"""
熔断器实现
实现Circuit Breaker模式，防止级联故障
"""
import time
from enum import Enum
from typing import Callable, Any, Optional
from threading import Lock
from app.observability.logger import default_logger as logger


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"  # 正常状态，允许请求通过
    OPEN = "open"  # 熔断状态，拒绝请求
    HALF_OPEN = "half_open"  # 半开状态，允许少量请求通过以测试服务是否恢复


class CircuitBreaker:
    """
    熔断器实现
    当失败率超过阈值时，熔断器会打开，拒绝请求
    一段时间后进入半开状态，允许少量请求测试服务是否恢复
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,  # 失败次数阈值
        success_threshold: int = 2,  # 半开状态下成功次数阈值
        timeout: float = 60.0,  # 熔断后等待时间（秒）
        expected_exception: type = Exception  # 期望的异常类型
    ):
        """
        初始化熔断器
        
        Args:
            failure_threshold: 失败次数阈值，超过此值将打开熔断器
            success_threshold: 半开状态下成功次数阈值，达到此值将关闭熔断器
            timeout: 熔断后等待时间（秒），之后进入半开状态
            expected_exception: 期望的异常类型
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED
        self.lock = Lock()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        通过熔断器调用函数
        
        Args:
            func: 要调用的函数
            *args: 位置参数
            **kwargs: 关键字参数
        
        Returns:
            函数返回值
        
        Raises:
            Exception: 当熔断器打开时抛出异常
        """
        with self.lock:
            # 检查状态
            if self.state == CircuitState.OPEN:
                # 检查是否可以进入半开状态
                if time.time() - (self.last_failure_time or 0) >= self.timeout:
                    logger.info(f"熔断器从OPEN状态进入HALF_OPEN状态")
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                else:
                    raise Exception("熔断器已打开，服务暂时不可用")
            
            # 尝试调用函数
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise e
            except Exception as e:
                # 非预期异常，不记录为失败
                raise e
    
    def _on_success(self):
        """处理成功调用"""
        with self.lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    logger.info("熔断器从HALF_OPEN状态进入CLOSED状态，服务已恢复")
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
            elif self.state == CircuitState.CLOSED:
                # 重置失败计数
                self.failure_count = 0
    
    def _on_failure(self):
        """处理失败调用"""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                # 半开状态下失败，重新打开熔断器
                logger.warning("半开状态下请求失败，熔断器重新打开")
                self.state = CircuitState.OPEN
                self.success_count = 0
            elif self.state == CircuitState.CLOSED:
                if self.failure_count >= self.failure_threshold:
                    logger.error(
                        f"失败次数达到阈值({self.failure_threshold})，熔断器打开",
                        extra={"failure_count": self.failure_count}
                    )
                    self.state = CircuitState.OPEN
    
    def get_state(self) -> CircuitState:
        """获取当前状态"""
        return self.state
    
    def reset(self):
        """重置熔断器"""
        with self.lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None


class CircuitBreakerManager:
    """
    熔断器管理器
    管理多个熔断器实例
    """
    
    def __init__(self):
        self.breakers: dict[str, CircuitBreaker] = {}
        self.lock = Lock()
    
    def get_breaker(self, name: str, **kwargs) -> CircuitBreaker:
        """
        获取或创建熔断器
        
        Args:
            name: 熔断器名称
            **kwargs: 熔断器配置参数
        
        Returns:
            熔断器实例
        """
        if name not in self.breakers:
            with self.lock:
                if name not in self.breakers:
                    self.breakers[name] = CircuitBreaker(**kwargs)
        return self.breakers[name]
    
    def reset_breaker(self, name: str):
        """重置指定熔断器"""
        if name in self.breakers:
            self.breakers[name].reset()


# 全局熔断器管理器
circuit_breaker_manager = CircuitBreakerManager()

