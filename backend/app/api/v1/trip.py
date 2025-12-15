from fastapi import APIRouter
from app.models.trip_model import TripPlanRequest, TripPlanResponse
from app.observability.logger import default_logger as logger
from app.exceptions.custom_exceptions import (
    BusinessException,
    LLMServiceException,
    MapServiceException,
    ImageServiceException
)
from app.exceptions.error_codes import ErrorCode

# 导入新的Agent
from app.agents.planner import PlannerAgent

# 导入共享的服务实例
from app.services.llm_service import LLMService

router = APIRouter()

# 初始化所有Agent
# attraction_agent = AttractionSearchAgent()
# hotel_agent = HotelSearchAgent()
# weather_agent = WeatherQueryAgent()
planner_agent = PlannerAgent(llm_service=LLMService)


@router.post("/plan", response_model=TripPlanResponse)
def plan_trip(request: TripPlanRequest):
    """
    接收行程规划请求，通过多智能体协作完成规划。（增强版 - 支持记忆和上下文）
    """
    from app.observability.logger import get_request_id
    
    # 获取用户ID（可以从请求头或session中获取，这里简化处理）
    # 实际应用中可以从认证token中获取
    user_id = get_request_id()  # 暂时使用request_id作为user_id
    
    logger.info(
        f"接收到新的行程规划请求（增强版）",
        extra={
            "destination": request.destination,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "budget": request.budget,
            "preferences": request.preferences,
            "hotel_preferences": request.hotel_preferences,
            "user_id": user_id
        }
    )

    try:
        # 参数验证
        if not request.destination or not request.destination.strip():
            raise BusinessException(
                ErrorCode.MISSING_PARAMETER,
                details={"field": "destination", "message": "目的地不能为空"}
            )
        
        if not request.start_date or not request.end_date:
            raise BusinessException(
                ErrorCode.MISSING_PARAMETER,
                details={"field": "date_range", "message": "日期范围不能为空"}
            )

        # 调用增强的PlannerAgent进行规划
        final_plan = planner_agent.plan_trip(request=request, user_id=user_id)

        if not final_plan:
            raise BusinessException(
                ErrorCode.TRIP_PLAN_FAILED,
                details={"message": "无法生成行程计划，请检查日志获取更多信息"}
            )

        logger.info(
            f"行程规划成功（增强版）",
            extra={
                "destination": request.destination,
                "trip_title": final_plan.trip_title,
                "days": len(final_plan.days),
                "user_id": user_id
            }
        )

        return final_plan

    except BusinessException:
        # 业务异常直接抛出，由全局异常处理器处理
        raise
    except Exception as e:
        # 其他异常包装为业务异常
        logger.error(
            f"处理/plan请求时发生意外错误: {e}",
            exc_info=True,
            extra={
                "destination": request.destination,
                "error_type": type(e).__name__,
                "user_id": user_id
            }
        )
        raise BusinessException(
            ErrorCode.TRIP_PLAN_FAILED,
            message=f"行程规划失败: {str(e)}",
            details={"error_type": type(e).__name__}
        )