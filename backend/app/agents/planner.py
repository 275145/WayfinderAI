import json
from datetime import datetime
from app.models.trip_model import TripPlanRequest, TripPlanResponse
from app.models.common_model import Attraction, Hotel, Weather
from app.services.llm_service import LLMService
from app.config import logger
from typing import List
from app.tools.mcp_tool import MCPTool
from app.config import settings


from app.services.unsplash_service import UnsplashService


from hello_agents import SimpleAgent
# ============ Agent提示词 ============

ATTRACTION_AGENT_PROMPT = """你是景点搜索专家。你的任务是根据城市和用户偏好搜索合适的景点。

**重要提示:**
你必须使用工具来搜索景点!不要自己编造景点信息!

**工具调用格式:**
使用maps_text_search工具时,必须严格按照以下格式:
`[TOOL_CALL:amap_maps_text_search:keywords=景点关键词,city=城市名]`

**示例:**
用户: "搜索北京的历史文化景点"
你的回复: [TOOL_CALL:amap_maps_text_search:keywords=历史文化,city=北京]

用户: "搜索上海的公园"
你的回复: [TOOL_CALL:amap_maps_text_search:keywords=公园,city=上海]

**注意:**
1. 必须使用工具,不要直接回答
2. 格式必须完全正确,包括方括号和冒号
3. 参数用逗号分隔
"""

WEATHER_AGENT_PROMPT = """你是天气查询专家。你的任务是查询指定城市的天气信息。

**重要提示:**
你必须使用工具来查询天气!不要自己编造天气信息!

**工具调用格式:**
使用maps_weather工具时,必须严格按照以下格式:
`[TOOL_CALL:amap_maps_weather:city=城市名]`

**示例:**
用户: "查询北京天气"
你的回复: [TOOL_CALL:amap_maps_weather:city=北京]

用户: "上海的天气怎么样"
你的回复: [TOOL_CALL:amap_maps_weather:city=上海]

**注意:**
1. 必须使用工具,不要直接回答
2. 格式必须完全正确,包括方括号和冒号
"""

HOTEL_AGENT_PROMPT = """你是酒店推荐专家。你的任务是根据城市和景点位置推荐合适的酒店。

**重要提示:**
你必须使用工具来搜索酒店!不要自己编造酒店信息!

**工具调用格式:**
使用maps_text_search工具搜索酒店时,必须严格按照以下格式:
`[TOOL_CALL:amap_maps_text_search:keywords=酒店,city=城市名]`

**示例:**
用户: "搜索北京的酒店"
你的回复: [TOOL_CALL:amap_maps_text_search:keywords=酒店,city=北京]

**注意:**
1. 必须使用工具,不要直接回答
2. 格式必须完全正确,包括方括号和冒号
3. 关键词使用"酒店"或"宾馆"
"""

PLANNER_AGENT_PROMPT = """你是行程规划专家。你的任务是根据**景点信息、酒店信息和天气信息**，生成结构化的旅行计划。

请**严格按照以下 JSON 结构**返回结果，你的输出必须是**有效的 JSON**，不要添加任何额外的解释或注释。

**整体结构:**
```json
{
  "trip_title": "一个吸引人的行程标题",
  "total_budget": 2000.0,
  "hotels": [
    {
      "name": "酒店名称",
      "address": "酒店地址",
      "location": { "lat": 39.915, "lng": 116.397 },
      "price": 400.0,
      "rating": 4.5,
      "distance_to_attraction_km": 1.2
    }
  ],
  "days": [
    {
      "day": 1,
      "theme": "当天主题，例如：古都历史探索",
      "weather": {
        "date": "YYYY-MM-DD",
        "day_weather": "晴",
        "night_weather": "多云",
        "day_temp": "25",
        "night_temp": "15"
      },
      "recommended_hotel": {
        "name": "当日推荐酒店名称",
        "address": "酒店地址",
        "location": { "lat": 39.915, "lng": 116.397 },
        "price": 400.0,
        "rating": 4.5,
        "distance_to_attraction_km": 0.8
      },
      "attractions": [
        {
          "name": "景点名称",
          "type": "景点类型，如：历史、人文、公园",
          "rating": 4.7,
          "suggested_duration_hours": 3.0,
          "description": "景点简要介绍和游玩建议",
          "address": "景点地址",
          "location": { "lat": 39.915, "lng": 116.397 },
          "image_urls": [
            "https://example.com/attraction-image-1.jpg",
            "https://example.com/attraction-image-2.jpg"
          ],
          "ticket_price": 60.0
        }
      ],
      "dinings": [
        {
          "name": "餐厅名称",
          "address": "餐厅地址",
          "location": { "lat": 39.910, "lng": 116.400 },
          "cost_per_person": 50.0,
          "rating": 4.5
        }
      ],
      "budget": {
        "transport_cost": 80.0,
        "dining_cost": 150.0,
        "hotel_cost": 400.0,
        "ticket_cost": 120.0,
        "total_cost": 750.0
      }
    }
  ]
}
```

**关键要求:**
1. **trip_title**: 创建一个吸引人且能体现行程特色的标题。
2. **total_budget**: 为整个行程计算总预算，包含：交通费用 + 餐饮费用 + 酒店费用 + 景点门票费用。
3. **hotels**: 列出若干推荐酒店（整体推荐），包含名称、地址、坐标、价格、评分、与主要景点的大致距离（km）。
4. **days**: 为每一天创建详细的行程：
   - **recommended_hotel**: 当日推荐住宿（可以从 hotels 中选择或新增）。
   - **attractions**: 仅包含景点信息，必须使用上面定义的景点字段结构。
   - **dinings**: 餐饮信息，不要包含景点图片字段。
   - **budget**: 单日预算拆分，所有字段必须为数字（float），`total_cost` = 当日交通 + 餐饮 + 酒店 + 门票。
5. **图片要求（重要）**:
   - 只为 **景点 (attractions)** 提供图片 URL，放在 `image_urls` 数组中。
   - **不要**为酒店或餐饮生成图片 URL 字段，以免后端在拉取图片时出错。
6. **天气**: `day_temp` 和 `night_temp` 必须是纯数字字符串（不带单位）。
7. **避免重复**: 不要在多天中重复推荐完全相同的景点或餐厅。

请务必保证返回 JSON 的字段名和结构与上述示例**一致**。
"""
class PlannerAgent:
    """
    行程规划专家 (Orchestrator)。
    负责接收其他Agent的输出，整合信息，并调用LLM生成最终的行程计划。
    """
    def __init__(self, llm_service: LLMService):
        self.llm = LLMService()
        self.settings = settings
        self.amap_tool = MCPTool(
                name="amap",
                description="高德地图服务",
                server_command=["uvx", "amap-mcp-server"],
                env={"AMAP_MAPS_API_KEY": settings.AMAP_API_KEY},
                auto_expand=True
            )
        self.unsplash_service = UnsplashService(settings.UNSPLASH_ACCESS_KEY)
        # self.attraction_agent = AttractionSearchAgent(self.amap_tool)
        # self.hotel_agent = HotelSearchAgent(self.amap_tool)
        # self.weather_agent = WeatherQueryAgent(self.amap_tool)
        # 创建景点搜索Agent
        print("  - 创建景点搜索Agent...")
        self.attraction_agent = SimpleAgent(
            name="景点搜索专家",
            llm=self.llm,
            system_prompt=ATTRACTION_AGENT_PROMPT
        )
        self.attraction_agent.add_tool(self.amap_tool)

        # 创建天气查询Agent
        print("  - 创建天气查询Agent...")
        self.weather_agent = SimpleAgent(
            name="天气查询专家",
            llm=self.llm,
            system_prompt=WEATHER_AGENT_PROMPT
        )
        self.weather_agent.add_tool(self.amap_tool)

        # 创建酒店推荐Agent
        print("  - 创建酒店推荐Agent...")
        self.hotel_agent = SimpleAgent(
            name="酒店推荐专家",
            llm=self.llm,
            system_prompt=HOTEL_AGENT_PROMPT
        )
        self.hotel_agent.add_tool(self.amap_tool)

        # 创建行程规划Agent(不需要工具)
        print("  - 创建行程规划Agent...")
        self.planner_agent = SimpleAgent(
            name="行程规划专家",
            llm=self.llm,
            system_prompt=PLANNER_AGENT_PROMPT
        )
        
        print(f"✅ 多智能体系统初始化成功")
        # print(f"   景点搜索Agent: {len(self.attraction_agent.list_tools())} 个工具")
        # print(f"   天气查询Agent: {len(self.weather_agent.list_tools())} 个工具")
        # print(f"   酒店推荐Agent: {len(self.hotel_agent.list_tools())} 个工具")
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

        **可用资源（原始数据，供你参考生成结构化 JSON）:**
        - 推荐景点原始信息:\n{(attractions)}
        - 推荐酒店原始信息:\n{(hotels)}
        - 天气预报原始信息:\n{(weather)}

        请使用系统提示词中给出的 JSON 结构（包含 trip_title、total_budget、hotels、days、recommended_hotel、attractions、dinings、budget 等字段），
        按照要求返回一个**完整且合法的 JSON 对象**。不要输出 Markdown 代码块标记（如 ```json），也不要添加任何解释文字。
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
        # attractions: List[Attraction],
        # hotels: List[Hotel],
        # weather: List[Weather]
    ) -> TripPlanResponse | None:
        attraction_query = self._build_attraction_query(request)
        attractions = self.attraction_agent.run(attraction_query)
        print(f"景点搜索结果: {attractions[:200]}...\n")
        hotel_query = self._build_hotel_query(request)
        hotels = self.hotel_agent.run(hotel_query)
        print(f"酒店搜索结果: {hotels[:200]}...\n")
        weather_query = f"请查询{request.destination}的天气信息"
        weather = self.weather_agent.run(weather_query)
        print(f"天气查询结果: {weather[:200]}...\n")
 
        prompt = self._construct_prompt(request, attractions, hotels, weather)
        json_plan_str = self.planner_agent.run(prompt)

        
        
        if not json_plan_str:
            logger.error("LLM未能生成有效的行程计划JSON。")
            return None

        try:
            if '```json' in json_plan_str:
                json_plan_str = json_plan_str.split('```json')[1].split('```')[0].strip()
            
            plan_data = json.loads(json_plan_str)
            validated_plan = TripPlanResponse.model_validate(plan_data)

            # 只为景点获取图片：遍历每日行程的 attractions
            for day in validated_plan.days:
                for attraction in day.attractions:
                    # 仅在 image_urls 为空时补充一张图片，且严格限定为景点图片
                    if not attraction.image_urls:
                        image_url = self.unsplash_service.get_photo_url(
                            f"{attraction.name} {request.destination} 景点 landmark tourist attraction",
                            ensure_attraction=True
                        )
                        if image_url:
                            attraction.image_urls.append(image_url)
            logger.info(f"成功生成并验证了行程计划: {validated_plan.trip_title}")
            return validated_plan
        except (json.JSONDecodeError, Exception) as e:
            logger.critical(f"解析或验证LLM返回的JSON时失败: {e}\n原始JSON字符串: {json_plan_str}")
