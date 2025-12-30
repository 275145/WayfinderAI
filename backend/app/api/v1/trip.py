from fastapi import APIRouter, Request, Depends
from app.models.trip_model import TripPlanRequest, TripPlanResponse
from app.observability.logger import default_logger as logger
from app.exceptions.custom_exceptions import (
    BusinessException,
    LLMServiceException,
    MapServiceException,
    ImageServiceException
)
from app.exceptions.error_codes import ErrorCode
from app.middleware.auth import get_user_id

# 导入新的Agent
from app.agents.planner import PlannerAgent

# 导入共享的服务实例
from app.services.llm_service import LLMService
from app.services.vector_memory_service import vector_memory_service

router = APIRouter()

# 初始化所有Agent
# attraction_agent = AttractionSearchAgent()
# hotel_agent = HotelSearchAgent()
# weather_agent = WeatherQueryAgent()
planner_agent = PlannerAgent(llm_service=LLMService, memory_service=vector_memory_service)


@router.post("/plan", response_model=TripPlanResponse)
def plan_trip(request: TripPlanRequest, http_request: Request):
    """
    接收行程规划请求，通过多智能体协作完成规划。（增强版 - 支持记忆和上下文）
    """
    # 获取用户ID（从认证中间件获取）
    user_id = get_user_id(http_request)
    
    logger.info(
        f"接收到新的行程规划请求",
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
        
        # 保存向量记忆
        if final_plan:
            # 存储用户行程到向量数据库
            trip_data = {
                "destination": request.destination,
                "start_date": request.start_date,
                "end_date": request.end_date,
                "preferences": request.preferences,
                "hotel_preferences": request.hotel_preferences,
                "budget": request.budget,
                "trip_title": final_plan.trip_title,
                "days": [day.dict() for day in final_plan.days]
            }
            vector_memory_service.store_user_trip(user_id, trip_data)
            
            # 存储用户偏好
            vector_memory_service.store_user_preference(user_id, "trip_preferences", {
                "destination": request.destination,
                "preferences": request.preferences,
                "hotel_preferences": request.hotel_preferences,
                "budget": request.budget
            })
            
            # 保存向量索引
            vector_memory_service.save()

        if not final_plan:
            raise BusinessException(
                ErrorCode.TRIP_PLAN_FAILED,
                details={"message": "无法生成行程计划，请检查日志获取更多信息"}
            )

        logger.info(
            f"行程规划成功",
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