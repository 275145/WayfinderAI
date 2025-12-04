from fastapi import APIRouter, HTTPException
from app.models.trip_model import TripPlanRequest, TripPlanResponse
from app.config import logger

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
    接收行程规划请求，通过多智能体协作完成规划。（同步版本）
    """
    try:
        logger.info(f"接收到新的行程规划请求: destination={request.destination}")

        # # 1. 顺序执行各个子任务（景点搜索、酒店搜索、天气查询）
        # # 如果希望并行，可使用 ThreadPoolExecutor，但此处为简化使用顺序调用
        # attractions = attraction_agent.search(request.destination, request.preferences)
        # hotels = hotel_agent.search(request.destination, request.hotel_preferences)
        # weather = weather_agent.query(request.destination)

        # if not attractions:
        #     logger.warning("未能找到相关景点，但仍继续规划。")

        # 2. 调用PlannerAgent进行最终规划
        final_plan = planner_agent.plan_trip(
            request=request,
            # attractions=attractions,
            # hotels=hotels,
            # weather=weather
        )

        if not final_plan:
            raise HTTPException(status_code=500, detail="无法生成行程计划，请检查日志获取更多信息。")

        return final_plan

    except Exception as e:
        logger.error(f"处理/plan请求时发生意外错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {e}")