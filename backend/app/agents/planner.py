import json
import math
from datetime import datetime
from app.models.trip_model import TripPlanRequest, TripPlanResponse
from app.models.common_model import Attraction, Hotel, Weather
from app.services.llm_service import LLMService
from app.observability.logger import default_logger as logger
from typing import List, Optional, Tuple
from app.tools.mcp_tool import MCPTool
from app.config import settings
from app.services.unsplash_service import UnsplashService
# from app.services.memory_service import memory_service  # 替换为向量记忆服务
from app.services.vector_memory_service import VectorMemoryService
from app.services.context_manager import ContextManager, get_context_manager
from app.agents.agent_communication import communication_hub
from app.agents.specialized_agents import (
    AttractionSearchAgent,
    HotelRecommendationAgent,
    WeatherQueryAgent,
    PlannerAgent as EnhancedPlannerAgent
)
from hello_agents import ToolRegistry
from app.observability.logger import get_request_id

# 主要城市的经纬度范围（用于验证）
CITY_BOUNDS = {
    "北京": {"lat_min": 39.4, "lat_max": 41.1, "lng_min": 115.7, "lng_max": 117.4},
    "上海": {"lat_min": 30.7, "lat_max": 31.9, "lng_min": 120.8, "lng_max": 122.2},
    "杭州": {"lat_min": 30.0, "lat_max": 30.5, "lng_min": 119.5, "lng_max": 120.5},
    "广州": {"lat_min": 22.7, "lat_max": 23.8, "lng_min": 112.9, "lng_max": 114.0},
    "深圳": {"lat_min": 22.4, "lat_max": 22.9, "lng_min": 113.7, "lng_max": 114.6},
    "成都": {"lat_min": 30.4, "lat_max": 30.9, "lng_min": 103.9, "lng_max": 104.5},
    "西安": {"lat_min": 34.0, "lat_max": 34.5, "lng_min": 108.7, "lng_max": 109.2},
    "南京": {"lat_min": 31.9, "lat_max": 32.2, "lng_min": 118.4, "lng_max": 119.2},
    "苏州": {"lat_min": 31.1, "lat_max": 31.5, "lng_min": 120.3, "lng_max": 121.0},
    "厦门": {"lat_min": 24.4, "lat_max": 24.6, "lng_min": 118.0, "lng_max": 118.2},
}
# 注意：Agent提示词已移至 specialized_agents.py
class PlannerAgent:
    """
    行程规划专家 (Orchestrator) - 增强版
    负责协调多个增强智能体，整合信息，并生成最终的行程计划。
    支持记忆、上下文、智能体间通信等功能。
    """
    def __init__(self, llm_service: LLMService, memory_service: VectorMemoryService = None):
        self.llm = LLMService()
        self.settings = settings
        self.unsplash_service = UnsplashService(settings.UNSPLASH_ACCESS_KEY)
        self.memory_service = memory_service or VectorMemoryService()
        
        # 创建工具注册表
        self.tool_registry = ToolRegistry()
        
        # 创建高德地图工具
        self.amap_tool = MCPTool(
                name="amap",
                description="高德地图服务",
                server_command=["uvx", "amap-mcp-server"],
                env={"AMAP_MAPS_API_KEY": settings.AMAP_API_KEY},
                auto_expand=True
            )
        self.tool_registry.register_tool(self.amap_tool)
        
        logger.info("✅ 多智能体系统初始化完成（增强版）")
    def _validate_location_in_city(self, lat: float, lng: float, city: str) -> bool:
        """
        验证位置是否在指定城市范围内
        
        Args:
            lat: 纬度
            lng: 经度
            city: 城市名称
        
        Returns:
            是否在范围内
        """
        if city not in CITY_BOUNDS:
            # 如果城市不在预定义列表中，使用更宽松的验证
            # 可以根据需要扩展城市列表
            logger.warning(f"城市 {city} 不在预定义列表中，跳过严格验证")
            return True
        
        bounds = CITY_BOUNDS[city]
        return (
            bounds["lat_min"] <= lat <= bounds["lat_max"] and
            bounds["lng_min"] <= lng <= bounds["lng_max"]
        )
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        计算两点之间的距离（公里）
        
        Args:
            lat1, lng1: 第一个点的经纬度
            lat2, lng2: 第二个点的经纬度
        
        Returns:
            距离（公里）
        """
        # 使用Haversine公式计算两点间距离
        R = 6371  # 地球半径（公里）
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = (
            math.sin(dlat / 2) ** 2 +
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))
        return R * c
    
    def _validate_and_filter_plan(self, plan: TripPlanResponse, destination: str) -> TripPlanResponse:
        """
        验证并过滤行程计划，移除不在目标城市范围内的景点
        
        Args:
            plan: 行程计划
            destination: 目标城市
        
        Returns:
            验证后的行程计划
        """
        filtered_days = []
        removed_count = 0
        
        for day in plan.days:
            # 过滤景点
            valid_attractions = []
            for attraction in day.attractions:
                if attraction.location:
                    lat = float(attraction.location.lat)
                    lng = float(attraction.location.lng)
                    
                    if self._validate_location_in_city(lat, lng, destination):
                        valid_attractions.append(attraction)
                    else:
                        removed_count += 1
                        logger.warning(
                            f"移除不在目标城市范围内的景点: {attraction.name} "
                            f"(位置: {lat}, {lng}, 目标城市: {destination})"
                        )
                else:
                    # 没有位置信息的景点也移除
                    removed_count += 1
                    logger.warning(f"移除没有位置信息的景点: {attraction.name}")
            
            # 验证同一天景点距离
            if len(valid_attractions) > 1:
                for i in range(len(valid_attractions) - 1):
                    att1 = valid_attractions[i]
                    att2 = valid_attractions[i + 1]
                    if att1.location and att2.location:
                        distance = self._calculate_distance(
                            float(att1.location.lat), float(att1.location.lng),
                            float(att2.location.lat), float(att2.location.lng)
                        )
                        if distance > 50:
                            logger.warning(
                                f"第{day.day}天的景点 {att1.name} 和 {att2.name} 距离较远: {distance:.2f}公里"
                            )
            
            # 过滤餐饮
            valid_dinings = []
            for dining in day.dinings:
                if dining.location:
                    lat = float(dining.location.lat)
                    lng = float(dining.location.lng)
                    if self._validate_location_in_city(lat, lng, destination):
                        valid_dinings.append(dining)
                    else:
                        logger.warning(f"移除不在目标城市范围内的餐饮: {dining.name}")
            
            # 验证酒店
            if day.recommended_hotel and day.recommended_hotel.location:
                lat = float(day.recommended_hotel.location.lat)
                lng = float(day.recommended_hotel.location.lng)
                if not self._validate_location_in_city(lat, lng, destination):
                    logger.warning(f"第{day.day}天的推荐酒店不在目标城市范围内: {day.recommended_hotel.name}")
                    day.recommended_hotel = None
            
            # 更新过滤后的数据
            day.attractions = valid_attractions
            day.dinings = valid_dinings
            filtered_days.append(day)
        
        # 验证相邻天景点距离
        for i in range(len(filtered_days) - 1):
            day1 = filtered_days[i]
            day2 = filtered_days[i + 1]
            
            if day1.attractions and day2.attractions:
                last_att_day1 = day1.attractions[-1]
                first_att_day2 = day2.attractions[0]
                
                if last_att_day1.location and first_att_day2.location:
                    distance = self._calculate_distance(
                        float(last_att_day1.location.lat), float(last_att_day1.location.lng),
                        float(first_att_day2.location.lat), float(first_att_day2.location.lng)
                    )
                    if distance > 100:
                        logger.warning(
                            f"第{day1.day}天和第{day2.day}天的景点距离较远: {distance:.2f}公里"
                        )
        
        plan.days = filtered_days
        
        if removed_count > 0:
            logger.info(f"已移除 {removed_count} 个不在目标城市范围内的景点")
        
        return plan
    
    def _construct_prompt(self, request: TripPlanRequest, attractions: str, hotels: str, weather: str) -> str:
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(request.end_date, "%Y-%m-%d")
        duration = (end_date - start_date).days + 1

        # attraction_details = [f"- {a.name} (评分: {a.rating}, 类型: {a.type})" for a in attractions]
        # hotel_details = [f"- {h.name} (价格: {h.price}, 评分: {h.rating})" for h in hotels]
        # weather_details = [f"- {w.date}: {w.day_weather}, {w.day_temp}°C" for w in weather]

        prompt = f"""
        请为我创建一个前往 {request.destination} 的旅行计划。

        **基本信息:**
        - 旅行天数: {duration} 天 (从 {request.start_date} 到 {request.end_date})
        - 预算水平: {request.budget}
        - 个人偏好: {', '.join(request.preferences) if request.preferences else '无'}
        - 酒店偏好: {', '.join(request.hotel_preferences) if request.hotel_preferences else '无'}

        **可用资源:**
        - **推荐景点列表:**\n{(attractions)}
        - **推荐酒店列表:**\n{(hotels)}
        - **天气预报:**\n{(weather)}

        **输出要求:**
        1. 严格按照系统提示中给定的 JSON 结构和字段名生成行程计划。
        2. 你的输出必须是一个完整的 JSON 对象，包含：
           - trip_title
           - total_budget（含 transport_cost / dining_cost / hotel_cost / attraction_ticket_cost / total）
           - hotels
           - days（其中包含 recommended_hotel / attractions / dinings / budget 等字段）
        3. 不要输出任何额外的解释或 Markdown，只输出 JSON。
        """
        return prompt

    def _build_attraction_query(self, request: TripPlanRequest) -> str:
        """构建景点搜索查询 - 直接包含工具调用"""
        keywords = []
        if request.preferences:
            # 只取第一个偏好作为关键词
            keywords = request.preferences[0]
        else:
            keywords = "景点"

        # 直接返回工具调用格式
        query = f"请使用amap_maps_text_search工具搜索{request.destination}的{keywords}相关景点。\n[TOOL_CALL:amap_maps_text_search:keywords={keywords},city={request.destination}]"
        return query
    def _build_hotel_query(self, request: TripPlanRequest) -> str:
        """构建酒店搜索查询 - 直接包含工具调用"""

        query = f"请使用amap_maps_text_search工具搜索{request.destination}的酒店。请确保返回的酒店信息详细且准确。\n[TOOL_CALL:amap_maps_text_search:keywords=酒店,city={request.destination}]"
        return query
    
    def plan_trip(
        self,
        request: TripPlanRequest,
        user_id: Optional[str] = None
    ) -> TripPlanResponse | None:
        """
        规划行程（增强版）
        
        Args:
            request: 行程规划请求
            user_id: 用户ID（用于记忆检索）
        
        Returns:
            行程规划响应
        """
        # 获取请求ID
        request_id = get_request_id() or f"req_{datetime.now().timestamp()}"
        
        # 创建或获取上下文管理器
        context_manager = get_context_manager(request_id)
        
        # 在上下文中存储请求信息
        context_manager.share_data("request", {
            "destination": request.destination,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "preferences": request.preferences,
            "hotel_preferences": request.hotel_preferences,
            "budget": request.budget
        })
        
        # 如果没有提供user_id，使用request_id作为临时user_id
        if not user_id:
            user_id = request_id
        
        # 检索用户记忆并添加到上下文（使用向量记忆服务）
        # 构建查询文本
        query_text = f"{request.destination} {' '.join(request.preferences or [])} {request.budget}"
        
        # 检索用户记忆
        user_memories = self.memory_service.retrieve_user_memories(
            user_id=user_id,
            query=query_text,
            limit=5,
            memory_types=["preference", "trip"]
        )
        if user_memories:
            context_manager.add_memory_context("user_memories", user_memories)
            logger.info(f"已加载 {len(user_memories)} 条用户记忆 - UserID: {user_id}")
        
        # 检索相关知识记忆
        knowledge_memories = self.memory_service.retrieve_knowledge_memories(
            query=f"{request.destination} 旅行 景点 特色",
            limit=3,
            knowledge_types=["destination", "experience"]
        )
        if knowledge_memories:
            context_manager.add_memory_context("knowledge_memories", knowledge_memories)
            logger.info(f"已加载 {len(knowledge_memories)} 条知识记忆")
        
        # 创建增强的智能体
        logger.info("创建增强智能体...")
        
        attraction_agent = AttractionSearchAgent(
            llm=self.llm,
            tool_registry=self.tool_registry,
            context_manager=context_manager,
            communication_hub=communication_hub,
            user_id=user_id
        )
        
        hotel_agent = HotelRecommendationAgent(
            llm=self.llm,
            tool_registry=self.tool_registry,
            context_manager=context_manager,
            communication_hub=communication_hub,
            user_id=user_id
        )
        
        weather_agent = WeatherQueryAgent(
            llm=self.llm,
            tool_registry=self.tool_registry,
            context_manager=context_manager,
            communication_hub=communication_hub,
            user_id=user_id
        )
        
        planner_agent = EnhancedPlannerAgent(
            llm=self.llm,
            context_manager=context_manager,
            communication_hub=communication_hub,
            user_id=user_id
        )
        
        # 执行规划流程
        try:
            # 1. 景点搜索
            logger.info("开始景点搜索...")
            attraction_query = self._build_attraction_query(request)
            attractions = attraction_agent.run(attraction_query)
            logger.info(f"景点搜索完成: {attractions[:200]}...")
            
            # 2. 酒店推荐
            logger.info("开始酒店推荐...")
            hotel_query = self._build_hotel_query(request)
            hotels = hotel_agent.run(hotel_query)
            logger.info(f"酒店推荐完成: {hotels[:200]}...")
            
            # 3. 天气查询
            logger.info("开始天气查询...")
            weather_query = f"请查询{request.destination}的天气信息，日期范围：{request.start_date} 到 {request.end_date}"
            weather = weather_agent.run(weather_query)
            logger.info(f"天气查询完成: {weather[:200]}...")
            
            # 4. 行程规划
            logger.info("开始行程规划...")
            prompt = self._construct_prompt(request, attractions, hotels, weather)
            json_plan_str = planner_agent.run(prompt)
        
            if not json_plan_str:
                logger.error("LLM未能生成有效的行程计划JSON。")
                return None

            # 5. 解析和验证
            if '```json' in json_plan_str:
                json_plan_str = json_plan_str.split('```json')[1].split('```')[0].strip()
            
            plan_data = json.loads(json_plan_str)
            validated_plan = TripPlanResponse.model_validate(plan_data)

            # 6. 验证和过滤地理位置
            validated_plan = self._validate_and_filter_plan(validated_plan, request.destination)
            
            # 7. 为景点添加图片（优化搜索关键词）
            for day in validated_plan.days:
                for attraction in day.attractions:
                    # 如果已有图片且不为空列表，跳过
                    # if attraction.image_urls and len(attraction.image_urls) > 0:
                    #     continue
                    
                    # 构造搜索关键词：优先用"景点名 + 城市"，失败则只用城市
                    search_queries = [
                        f"{attraction.name} {request.destination}",  # 完整名称 + 城市
                        f"{attraction.name}",  # 只用景点名
                        f"{request.destination} landmark"  # 兜底：城市地标
                    ]
                    
                    logger.info(f"为景点 '{attraction.name}' 搜索图片，尝试关键词: {search_queries[0]}")
                    
                    image_url = None
                    for query in search_queries:
                        image_url = self.unsplash_service.get_photo_url(query)
                        if image_url:
                            logger.info(f"✅ 景点 '{attraction.name}' 成功获取图片: {image_url[:80]}...")
                            break
                        else:
                            logger.warning(f"⚠️ 关键词 '{query}' 未找到图片，尝试下一个")
                    
                    if image_url:
                        attraction.image_urls = [image_url]
                    else:
                        logger.warning(f"❌ 景点 '{attraction.name}' 所有关键词均未找到图片，保持为空列表")
                        attraction.image_urls = []
            
            # 8. 存储用户偏好记忆
            self.memory_service.store_user_preference(
                user_id,
                "trip_request",
                {
                    "destination": request.destination,
                    "preferences": request.preferences,
                    "hotel_preferences": request.hotel_preferences,
                    "budget": request.budget,
                    "trip_title": validated_plan.trip_title
                }
            )
            
            logger.info(f"成功生成并验证了行程计划: {validated_plan.trip_title}")
            
            # 清理上下文管理器（可选，也可以保留用于后续查询）
            # remove_context_manager(request_id)
            
            return validated_plan
            
        except (json.JSONDecodeError, Exception) as e:
            logger.error(
                f"解析或验证LLM返回的JSON时失败: {e}",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "destination": request.destination
                }
            )
            return None
