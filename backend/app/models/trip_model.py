from pydantic import BaseModel, Field
from typing import List, Optional
from .common_model import Location, Hotel, Weather, Attraction, Dining

# --- API 请求模型 ---

class TripPlanRequest(BaseModel):
    """行程规划的API请求体"""
    destination: str = Field(..., description="目的地城市", example="北京")
    start_date: str = Field(..., description="开始日期", example="2024-10-01")
    end_date: str = Field(..., description="结束日期", example="2024-10-03")
    preferences: List[str] = Field(default_factory=list, description="旅行偏好", example=["历史", "美食"])
    hotel_preferences: List[str] = Field(default_factory=list, description="酒店偏好", example=["经济型"])
    budget: str = Field("中等", description="预算", example="中等")

class Budget(BaseModel):
    """单日预算拆分"""
    transport_cost: float = Field(0.0, description="交通费用")
    dining_cost: float = Field(0.0, description="餐饮费用")
    hotel_cost: float = Field(0.0, description="酒店费用")
    ticket_cost: float = Field(0.0, description="景点门票费用")
    total_cost: float = Field(0.0, description="单日总费用")


class DailyPlan(BaseModel):
    """
    每日行程计划

    - recommended_hotel: 当日推荐住宿
    - attractions: 当日游玩的景点列表
      （景点模型包含名称、类型、评分、建议游玩时间、描述、地址、经纬度、图片URL列表、门票价格）
    - dinings: 当日推荐餐饮列表
    - budget: 单日预算拆分（交通 / 餐饮 / 酒店 / 景点门票）
    """
    day: int = Field(..., description="第几天")
    theme: str = Field("", description="当日主题")
    weather: Optional[Weather] = None
    recommended_hotel: Optional[Hotel] = Field(
        None, description="当日推荐住宿"
    )
    attractions: List[Attraction] = Field(
        default_factory=list,
        description="当日景点列表",
    )
    dinings: List[Dining] = Field(
        default_factory=list,
        description="当日餐饮列表",
    )
    budget: Budget = Field(
        default_factory=Budget,
        description="单日预算拆分",
    )

class TripPlanResponse(BaseModel):
    """行程规划的API响应体"""
    trip_title: str = Field(..., description="行程标题")
    total_budget: float = Field(..., description="整个行程的总预算（交通+餐饮+酒店+景点门票）")
    hotels: List[Hotel] = Field(default_factory=list, description="推荐酒店列表")
    days: List[DailyPlan] = Field(..., description="每日计划详情")