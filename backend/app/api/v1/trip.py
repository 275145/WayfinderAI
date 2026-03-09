from fastapi import APIRouter, Request, HTTPException, Header
from app.models.trip_model import TripPlanRequest, TripPlanResponse
from app.observability.logger import default_logger as logger
from app.exceptions.custom_exceptions import BusinessException
from app.exceptions.error_codes import ErrorCode
from app.middleware.auth import get_user_id
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid
import threading

from app.agents.planner import PlannerAgent
from app.services.llm_service import LLMService
from app.services.vector_memory_service import vector_memory_service
from app.services.redis_service import redis_service
from app.services.city_service import city_support_service

router = APIRouter()

planner_agent = PlannerAgent(llm_service=LLMService, memory_service=vector_memory_service)


def _build_and_store_plan(request: TripPlanRequest, user_id: str) -> TripPlanResponse:
    city_info = city_support_service.get_city_support_info(request.destination)

    final_plan = planner_agent.plan_trip(request=request, user_id=user_id)
    if not final_plan:
        raise BusinessException(
            ErrorCode.TRIP_PLAN_FAILED,
            details={"message": "无法生成行程计划，请检查日志获取更多信息"}
        )

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
    vector_memory_service.store_user_preference(user_id, "trip_preferences", {
        "destination": request.destination,
        "preferences": request.preferences,
        "hotel_preferences": request.hotel_preferences,
        "budget": request.budget
    })
    vector_memory_service.save()

    trip_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    full_trip_data = final_plan.model_dump()
    full_trip_data["id"] = trip_id
    full_trip_data["created_at"] = now
    full_trip_data["updated_at"] = now
    full_trip_data["version"] = 1
    full_trip_data["city_support_level"] = city_info.get("level")
    full_trip_data["city_support_message"] = city_info.get("message")
    redis_service.store_trip(user_id, trip_id, full_trip_data)

    return TripPlanResponse(**full_trip_data)


@router.post("/plan", response_model=TripPlanResponse)
def plan_trip(request: TripPlanRequest, http_request: Request):
    user_id = get_user_id(http_request)
    logger.info("接收到新的行程规划请求", extra={"user_id": user_id, "destination": request.destination})

    try:
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
        city_info = city_support_service.get_city_support_info(request.destination)
        logger.info(
            "城市支持等级评估",
            extra={
                "destination": request.destination,
                "city_support_level": city_info.get("level"),
                "city_support_message": city_info.get("message")
            }
        )
        return _build_and_store_plan(request, user_id)
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"处理/plan请求时发生意外错误: {e}", exc_info=True)
        raise BusinessException(
            ErrorCode.TRIP_PLAN_FAILED,
            message=f"行程规划失败: {str(e)}",
            details={"error_type": type(e).__name__}
        )


def _plan_task_worker(task_id: str, user_id: str, request_data: Dict[str, Any]):
    try:
        redis_service.update_trip_task(task_id, status="running", progress=10, message="任务启动中")
        request = TripPlanRequest(**request_data)
        city_info = city_support_service.get_city_support_info(request.destination)
        redis_service.update_trip_task(
            task_id,
            progress=20,
            message="已完成城市支持评估",
            city_support_level=city_info.get("level"),
            city_support_message=city_info.get("message")
        )
        result = _build_and_store_plan(request, user_id)
        redis_service.update_trip_task(
            task_id,
            status="succeeded",
            progress=100,
            message="行程生成完成",
            result_trip_id=result.id or ""
        )
    except Exception as e:
        logger.error(f"异步行程任务失败: task_id={task_id}, error={e}", exc_info=True)
        redis_service.update_trip_task(
            task_id,
            status="failed",
            progress=100,
            message="行程生成失败",
            error=str(e)
        )


@router.post("/plan-async")
def plan_trip_async(request: TripPlanRequest, http_request: Request):
    user_id = get_user_id(http_request)
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

    task_id = str(uuid.uuid4())
    request_data = request.model_dump()
    if not redis_service.create_trip_task(task_id, user_id, request_data):
        raise BusinessException(ErrorCode.TRIP_PLAN_FAILED, message="创建任务失败")

    worker = threading.Thread(
        target=_plan_task_worker,
        args=(task_id, user_id, request_data),
        daemon=True
    )
    worker.start()

    return {"task_id": task_id, "status": "pending", "message": "任务已创建"}


@router.get("/tasks/{task_id}")
def get_trip_task(task_id: str, http_request: Request):
    user_id = get_user_id(http_request)
    task = redis_service.get_trip_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="无权访问该任务")

    response: Dict[str, Any] = {
        "task_id": task.get("task_id"),
        "status": task.get("status"),
        "progress": int(task.get("progress", "0")),
        "message": task.get("message", ""),
        "result_trip_id": task.get("result_trip_id") or None,
        "error": task.get("error") or None,
        "city_support_level": task.get("city_support_level") or None,
        "city_support_message": task.get("city_support_message") or None,
        "updated_at": task.get("updated_at")
    }
    return response


@router.get("/list", response_model=List[TripPlanResponse])
def get_trip_list(http_request: Request):
    user_id = get_user_id(http_request)
    logger.info(f"获取用户行程列表 - UserID: {user_id}")
    try:
        return redis_service.list_user_trips(user_id)
    except Exception as e:
        logger.error(f"获取行程列表失败: {str(e)}")
        raise BusinessException(ErrorCode.TRIP_PLAN_FAILED, message="获取行程列表失败")


@router.get("/city-support/{city}")
def get_city_support(city: str):
    return city_support_service.get_city_support_info(city)


@router.get("/cities")
def list_city_support():
    cities = city_support_service.list_cities()
    return {
        "count": len(cities),
        "cities": cities
    }


@router.get("/{trip_id}", response_model=TripPlanResponse)
def get_trip(trip_id: str, http_request: Request):
    user_id = get_user_id(http_request)
    logger.info(f"获取行程详情 - UserID: {user_id}, TripID: {trip_id}")
    try:
        trip_data = redis_service.get_trip(trip_id)
        if not trip_data:
            raise HTTPException(status_code=404, detail="行程不存在")
        # 所有权校验
        user_trips = [t.get("id") for t in redis_service.list_user_trips(user_id)]
        if trip_id not in user_trips:
            raise HTTPException(status_code=403, detail="无权访问该行程")
        return TripPlanResponse(**trip_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取行程详情失败: {str(e)}")
        raise BusinessException(ErrorCode.TRIP_PLAN_FAILED, message="获取行程详情失败")


@router.delete("/{trip_id}")
def delete_trip(trip_id: str, http_request: Request):
    user_id = get_user_id(http_request)
    logger.info(f"删除行程 - UserID: {user_id}, TripID: {trip_id}")
    try:
        success = redis_service.delete_trip(user_id, trip_id)
        if not success:
            raise HTTPException(status_code=404, detail="行程不存在或删除失败")
        return {"message": "行程已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除行程失败: {str(e)}")
        raise BusinessException(ErrorCode.TRIP_PLAN_FAILED, message="删除行程失败")


@router.put("/{trip_id}", response_model=TripPlanResponse)
def update_trip(
    trip_id: str,
    request: TripPlanResponse,
    http_request: Request,
    if_match_version: Optional[int] = Header(default=None, alias="If-Match-Version")
):
    user_id = get_user_id(http_request)
    logger.info(f"更新行程 - UserID: {user_id}, TripID: {trip_id}")

    try:
        trip_data = request.model_dump()
        # 优先使用Header中的版本；否则使用body中的version
        expected_version = if_match_version if if_match_version is not None else request.version
        success, reason = redis_service.update_trip(
            user_id=user_id,
            trip_id=trip_id,
            trip_data=trip_data,
            expected_version=expected_version
        )

        if not success:
            if reason == "version_conflict":
                raise HTTPException(status_code=409, detail="行程版本冲突，请先刷新后再保存")
            if reason in ("forbidden",):
                raise HTTPException(status_code=403, detail="无权修改该行程")
            raise HTTPException(status_code=404, detail="行程不存在或更新失败")

        updated_trip = redis_service.get_trip(trip_id)
        if not updated_trip:
            raise HTTPException(status_code=404, detail="更新后行程不存在")
        return TripPlanResponse(**updated_trip)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新行程失败: {str(e)}")
        raise BusinessException(ErrorCode.TRIP_PLAN_FAILED, message="更新行程失败")


@router.get("/{trip_id}/versions")
def get_trip_versions(trip_id: str, http_request: Request):
    user_id = get_user_id(http_request)
    versions = redis_service.list_trip_versions(user_id=user_id, trip_id=trip_id)
    if not versions:
        return {"trip_id": trip_id, "versions": []}
    return {"trip_id": trip_id, "versions": versions}


@router.post("/{trip_id}/rollback")
def rollback_trip(trip_id: str, target_version: int, http_request: Request):
    user_id = get_user_id(http_request)
    success, reason = redis_service.rollback_trip(user_id=user_id, trip_id=trip_id, target_version=target_version)
    if not success:
        if reason == "forbidden":
            raise HTTPException(status_code=403, detail="无权回滚该行程")
        if reason == "version_not_found":
            raise HTTPException(status_code=404, detail="目标版本不存在")
        if reason == "not_found":
            raise HTTPException(status_code=404, detail="行程不存在")
        raise HTTPException(status_code=500, detail="回滚失败")
    trip = redis_service.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="回滚后行程不存在")
    return TripPlanResponse(**trip)
