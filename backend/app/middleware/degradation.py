"""
降级策略实现
当服务不可用或性能下降时，提供降级方案
"""
from typing import Callable, Any, Optional
from functools import wraps
from app.observability.logger import default_logger
from app.middleware.circuit_breaker import CircuitBreaker, circuit_breaker_manager

logger = default_logger


def fallback_response(default_value: Any = None):
    """
    降级装饰器
    当函数调用失败时，返回默认值
    
    Args:
        default_value: 降级时的默认返回值
    
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(
                    f"函数 {func.__name__} 调用失败，使用降级方案: {e}",
                    extra={"function": func.__name__, "error": str(e)}
                )
                return default_value
        return wrapper
    return decorator


def circuit_breaker_with_fallback(
    breaker_name: str,
    fallback_value: Any = None,
    **breaker_kwargs
):
    """
    带降级的熔断器装饰器
    当熔断器打开时，直接返回降级值，不抛出异常
    
    Args:
        breaker_name: 熔断器名称
        fallback_value: 降级时的返回值
        **breaker_kwargs: 熔断器配置参数
    
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        breaker = circuit_breaker_manager.get_breaker(breaker_name, **breaker_kwargs)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return breaker.call(func, *args, **kwargs)
            except Exception as e:
                logger.warning(
                    f"熔断器已打开或调用失败，使用降级方案 - 函数: {func.__name__}, 错误: {e}",
                    extra={
                        "function": func.__name__,
                        "breaker_name": breaker_name,
                        "breaker_state": breaker.get_state().value,
                        "error": str(e)
                    }
                )
                return fallback_value
        return wrapper
    return decorator


class DegradationStrategy:
    """
    降级策略类
    提供更灵活的降级控制
    """
    
    def __init__(self, fallback_func: Optional[Callable] = None):
        """
        初始化降级策略
        
        Args:
            fallback_func: 降级时调用的函数
        """
        self.fallback_func = fallback_func
    
    def execute(
        self,
        main_func: Callable,
        *args,
        fallback_value: Any = None,
        **kwargs
    ) -> Any:
        """
        执行主函数，失败时执行降级策略
        
        Args:
            main_func: 主函数
            *args: 位置参数
            fallback_value: 降级时的默认返回值
            **kwargs: 关键字参数
        
        Returns:
            函数返回值或降级值
        """
        try:
            return main_func(*args, **kwargs)
        except Exception as e:
            logger.warning(
                f"主函数执行失败，执行降级策略 - 函数: {main_func.__name__}, 错误: {e}",
                extra={"function": main_func.__name__, "error": str(e)}
            )
            
            # 如果有降级函数，调用它
            if self.fallback_func:
                try:
                    return self.fallback_func(*args, **kwargs)
                except Exception as fallback_error:
                    logger.error(
                        f"降级函数执行失败: {fallback_error}",
                        extra={"error": str(fallback_error)}
                    )
                    return fallback_value
            
            return fallback_value

