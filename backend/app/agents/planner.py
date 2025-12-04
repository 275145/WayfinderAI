import json
from datetime import datetime
from app.models.trip_model import TripPlanRequest, TripPlanResponse
from app.models.common_model import Attraction, Hotel, Weather
from app.services.llm_service import LLMService
from app.observability.logger import default_logger as logger
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

PLANNER_AGENT_PROMPT = """你是行程规划专家。你的任务是根据景点信息、酒店信息和天气信息，生成详细的旅行计划。

请严格按照以下 **JSON 结构** 返回旅行计划。你的输出必须是有效的 JSON，不要添加任何额外的解释或注释。

**整体设计要求：**
1. **景点模型（Attraction）** 必须包含：景点名称、类型、评分、建议游玩时间、描述、地址、经纬度、景点图片 URL 列表、门票价格。
2. **酒店模型（Hotel）** 在原有基础上，必须补充「距离景点的距离」字段。
3. **单日行程（DailyPlan）** 必须包含：
   - 推荐住宿（recommended_hotel）
   - 景点列表（attractions）
   - 餐饮列表（dinings）
   - 单日预算拆分（budget），包括交通费用、餐饮费用、酒店费用、景点门票费用。
4. **预算**：总预算字段需要拆分为交通费用、餐饮费用、酒店费用、景点门票费用四项，并给出总和。
5. 所有的「图片」只能挂在 **景点（attractions）** 上，不能给酒店或餐饮生成图片 URL。

**响应格式（示例，仅作为结构参考，字段名和类型必须严格遵守）：**
```json
{
  "trip_title": "一个吸引人的行程标题",
  "total_budget": {
    "transport_cost": 300.0,
    "dining_cost": 800.0,
    "hotel_cost": 1200.0,
    "attraction_ticket_cost": 400.0,
    "total": 2700.0
  },
  "hotels": [
    {
      "name": "酒店名称",
      "address": "酒店地址",
      "location": {"lat": 39.915, "lng": 116.397},
      "price": "400元/晚",
      "rating": "4.5",
      "distance_to_main_attraction_km": 1.2
    }
  ],
  "days": [
    {
      "day": 1,
      "theme": "古都历史探索",
      "weather": {
        "date": "YYYY-MM-DD",
        "day_weather": "晴",
        "night_weather": "多云",
        "day_temp": "25",
        "night_temp": "15",
        "day_wind": "东风3级",
        "night_wind": "西北风2级"
      },
      "recommended_hotel": {
        "name": "当日推荐酒店",
        "address": "酒店地址",
        "location": {"lat": 39.915, "lng": 116.397},
        "price": "400元/晚",
        "rating": "4.5",
        "distance_to_main_attraction_km": 0.8
      },
      "attractions": [
        {
          "name": "景点名称",
          "type": "历史文化",
          "rating": "4.7",
          "suggested_duration_hours": 3.0,
          "description": "景点简介和游览建议",
          "address": "景点地址",
          "location": {"lat": 39.915, "lng": 116.397},
          "image_urls": [
            "https://example.com/attraction-image-1.jpg"
          ],
          "ticket_price": "60"
        }
      ],
      "dinings": [
        {
          "name": "餐厅名称",
          "address": "餐厅地址",
          "location": {"lat": 39.910, "lng": 116.400},
          "cost_per_person": "80",
          "rating": "4.5"
        }
      ],
      "budget": {
        "transport_cost": 50.0,
        "dining_cost": 200.0,
        "hotel_cost": 400.0,
        "attraction_ticket_cost": 120.0,
        "total": 770.0
      }
    }
  ]
}
```

**关键要求：**
1. **trip_title**：创建一个吸引人且能体现行程特色的标题。
2. **total_budget**：给出四类费用（交通、餐饮、酒店、景点门票），并计算 total 为它们的总和。
3. **hotels / recommended_hotel**：酒店必须包含名称、地址、位置坐标、价格、评分和距离主要景点的距离。
4. **days**：为每一天创建详细的行程计划。
5. **theme**：每天的主题要体现该天的主要活动特色。
6. **weather**：包含该天的天气信息，温度必须是纯数字（不要带 °C 等单位），并给出白天和夜间的风向与风力（day_wind, night_wind）。
7. **attractions / dinings**：
   - attractions：只包含“景点”信息，图片 URL 只能出现在 attractions.image_urls 中。
   - dinings：只包含餐饮信息，不能包含图片 URL 字段。
8. **时间规划**：在描述中要体现出合理的时间安排（例如上午/下午/晚上安排哪些景点和餐饮）。
9. **预算准确**：total_budget.total 必须等于四类费用之和；每天的 budget.total 也必须等于四项之和。
10. **避免重复**：不要在多天中重复推荐同一个景点或餐厅。

**重要限制：**
- 不要为酒店或餐饮生成任何图片 URL 字段。
- 只有景点（attractions）可以有图片 URL，并且应当尽量与景点名称高度相关。
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

            # 为每日行程中的景点获取图片：
            # - 只给 attractions 填充图片
            # - 不给酒店和餐饮生成图片，避免类型不匹配导致报错
            for day in validated_plan.days:
                for attraction in day.attractions:
                    if not attraction.image_urls:
                        image_url = self.unsplash_service.get_photo_url(
                            f"{attraction.name} {request.destination}"
                        )
                        # 即使只获取到一张，也按列表形式存储，保证类型一致
                        if image_url:
                            attraction.image_urls = [image_url]
            logger.info(f"成功生成并验证了行程计划: {validated_plan.trip_title}")
            return validated_plan
        except (json.JSONDecodeError, Exception) as e:
            logger.critical(f"解析或验证LLM返回的JSON时失败: {e}\n原始JSON字符串: {json_plan_str}")
