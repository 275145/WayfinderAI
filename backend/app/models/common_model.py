from pydantic import BaseModel, Field
from typing import List, Optional, Union

class Location(BaseModel):
    """地理位置模型"""
    lat: float = Field(..., description="纬度")
    lng: float = Field(..., description="经度")

class Attraction(BaseModel):
    """景点信息模型"""
    name: str = Field(..., description="景点名称")
    type: str = Field("", description="景点类型，例如：历史、人文、公园等")
    rating: Union[float, str] = Field("N/A", description="评分")
    suggested_duration_hours: Optional[float] = Field(
        None, description="建议游玩时长（小时）"
    )
    description: Optional[str] = Field(
        None, description="景点介绍/描述"
    )
    address: str = Field("", description="地址")
    location: Optional[Location] = None
    image_urls: List[str] = Field(
        default_factory=list,
        description="景点图片URL列表，仅包含景点相关图片",
    )
    ticket_price: Optional[float] = Field(
        None, description="门票价格（单位：元）"
    )

class Hotel(BaseModel):
    """酒店信息模型"""
    name: str = Field(..., description="酒店名称")
    address: str = Field("", description="地址")
    location: Optional[Location] = None
    price: Union[float, str] = Field("N/A", description="价格")
    rating: Union[float, str] = Field("N/A", description="评分")
    distance_to_attraction_km: Optional[float] = Field(
        None, description="酒店与主要景点的距离（千米）"
    )

class Dining(BaseModel):
    """餐饮信息模型"""
    name: str = Field(..., description="餐厅名称")
    address: str = Field("", description="地址")
    location: Optional[Location] = None
    cost_per_person: Union[float, str] = Field("N/A", description="人均消费")
    rating: Union[float, str] = Field("N/A", description="评分")

class Weather(BaseModel):
    """天气信息模型"""
    date: str = Field(..., description="日期")
    day_weather: str = Field(..., description="白天天气现象")
    night_weather: str = Field(..., description="夜间天气现象")
    day_temp: str = Field(..., description="白天温度")
    night_temp: str = Field(..., description="夜间温度")
