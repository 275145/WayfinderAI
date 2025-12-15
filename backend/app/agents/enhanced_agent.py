"""
增强的智能体基类
基于SimpleAgent，增加记忆、上下文、通信能力
"""
import re
from typing import Optional, Iterator, Dict, Any, List
from hello_agents import SimpleAgent, HelloAgentsLLM, Config, Message
from app.services.memory_service import memory_service
from app.services.context_manager import ContextManager
from app.agents.agent_communication import (
    AgentCommunicationHub,
    AgentMessage,
    MessageType
)
from app.observability.logger import default_logger as logger


class EnhancedAgent(SimpleAgent):
    """
    增强的智能体基类
    在SimpleAgent基础上增加：
    - 记忆能力（检索和存储记忆）
    - 上下文感知（使用上下文管理器）
    - 通信能力（与其他智能体通信）
    """
    
    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        tool_registry: Optional['ToolRegistry'] = None,
        enable_tool_calling: bool = True,
        context_manager: Optional[ContextManager] = None,
        communication_hub: Optional[AgentCommunicationHub] = None,
        user_id: Optional[str] = None
    ):
        """
        初始化增强智能体
        
        Args:
            name: 智能体名称
            llm: LLM服务
            system_prompt: 系统提示词
            config: 配置
            tool_registry: 工具注册表
            enable_tool_calling: 是否启用工具调用
            context_manager: 上下文管理器
            communication_hub: 通信中心
            user_id: 用户ID（用于记忆检索）
        """
        super().__init__(name, llm, system_prompt, config)
        self.tool_registry = tool_registry
        self.enable_tool_calling = enable_tool_calling and tool_registry is not None
        self.context_manager = context_manager
        self.communication_hub = communication_hub
        self.user_id = user_id
        
        # 注册到通信中心
        if self.communication_hub:
            self.communication_hub.register_agent(self.name, self)
            # 注册默认消息处理器
            self.communication_hub.register_message_handler(
                self.name,
                MessageType.QUERY,
                self._handle_query_message
            )
            self.communication_hub.register_message_handler(
                self.name,
                MessageType.REQUEST,
                self._handle_request_message
            )
        
        logger.info(f"✅ {name} 增强智能体初始化完成，工具调用: {'启用' if self.enable_tool_calling else '禁用'}")
    
    def _get_enhanced_system_prompt(self) -> str:
        """构建增强的系统提示词，包含工具信息和记忆上下文"""
        base_prompt = self.system_prompt or "你是一个有用的AI助手。"
        
        # 添加工具信息
        if self.enable_tool_calling and self.tool_registry:
            tools_description = self.tool_registry.get_tools_description()
            if tools_description and tools_description != "暂无可用工具":
                tools_section = "\n\n## 可用工具\n"
                tools_section += "你可以使用以下工具来帮助回答问题：\n"
                tools_section += tools_description + "\n"
                tools_section += "\n## 工具调用格式\n"
                tools_section += "当需要使用工具时，请使用以下格式：\n"
                tools_section += "`[TOOL_CALL:{tool_name}:{parameters}]`\n"
                tools_section += "例如：`[TOOL_CALL:search:Python编程]` 或 `[TOOL_CALL:memory:recall=用户信息]`\n\n"
                tools_section += "工具调用结果会自动插入到对话中，然后你可以基于结果继续回答。\n"
                base_prompt += tools_section
        
        # 添加记忆上下文
        if self.user_id:
            memory_context = self._get_memory_context()
            if memory_context:
                memory_section = "\n\n## 相关记忆信息\n"
                memory_section += "以下是与当前任务相关的历史信息，你可以参考这些信息来更好地完成任务：\n"
                memory_section += memory_context + "\n"
                base_prompt += memory_section
        
        # 添加上下文信息
        if self.context_manager:
            shared_data = self.context_manager.get_all_shared_data()
            if shared_data:
                context_section = "\n\n## 共享上下文信息\n"
                context_section += "以下是从其他智能体共享的信息：\n"
                for key, value in shared_data.items():
                    context_section += f"- {key}: {str(value)[:200]}\n"
                base_prompt += context_section
        
        return base_prompt
    
    def _get_memory_context(self) -> str:
        """获取记忆上下文"""
        if not self.user_id:
            return ""
        
        context_parts = []
        
        # 检索用户偏好
        preferences = memory_service.retrieve_user_preferences(self.user_id)
        if preferences:
            context_parts.append(f"用户历史偏好: {str(preferences)[:300]}")
        
        # 检索相似行程
        # 这里需要从上下文获取当前请求信息
        if self.context_manager:
            request_context = self.context_manager.get_shared_data("request")
            if request_context:
                destination = request_context.get("destination", "")
                prefs = request_context.get("preferences", [])
                if destination:
                    similar_trips = memory_service.retrieve_similar_trips(
                        destination, prefs, limit=3
                    )
                    if similar_trips:
                        context_parts.append(f"相似历史行程: {len(similar_trips)}个")
        
        return "\n".join(context_parts)
    
    def run(
        self,
        input_text: str,
        max_tool_iterations: int = 3,
        **kwargs
    ) -> str:
        """
        重写的运行方法 - 增强版，支持记忆和上下文
        """
        logger.info(f"🤖 {self.name} 正在处理: {input_text[:100]}...")
        
        # 更新上下文
        if self.context_manager:
            self.context_manager.update_context(
                self.name,
                {"input": input_text, "status": "processing"},
                "info"
            )
        
        # 构建消息列表
        messages = []
        
        # 添加增强的系统消息
        enhanced_system_prompt = self._get_enhanced_system_prompt()
        messages.append({"role": "system", "content": enhanced_system_prompt})
        
        # 添加历史消息
        for msg in self._history:
            messages.append({"role": msg.role, "content": msg.content})
        
        # 添加当前用户消息
        messages.append({"role": "user", "content": input_text})
        
        # 如果没有启用工具调用，使用简单对话逻辑
        if not self.enable_tool_calling:
            response = self.llm.invoke(messages, **kwargs)
            self.add_message(Message(input_text, "user"))
            self.add_message(Message(response, "assistant"))
            
            # 更新上下文
            if self.context_manager:
                self.context_manager.update_context(
                    self.name,
                    {"output": response, "status": "completed"},
                    "result"
                )
            
            logger.info(f"✅ {self.name} 响应完成")
            return response
        
        # 支持多轮工具调用的逻辑
        return self._run_with_tools(messages, input_text, max_tool_iterations, **kwargs)
    
    def _run_with_tools(
        self,
        messages: list,
        input_text: str,
        max_tool_iterations: int,
        **kwargs
    ) -> str:
        """支持工具调用的运行逻辑（增强版）"""
        current_iteration = 0
        final_response = ""
        
        while current_iteration < max_tool_iterations:
            # 调用LLM
            response = self.llm.invoke(messages, **kwargs)
            
            # 检查是否有工具调用
            tool_calls = self._parse_tool_calls(response)
            
            if tool_calls:
                logger.debug(f"🔧 {self.name} 检测到 {len(tool_calls)} 个工具调用")
                
                # 执行所有工具调用并收集结果
                tool_results = []
                clean_response = response
                
                for call in tool_calls:
                    result = self._execute_tool_call(call['tool_name'], call['parameters'])
                    tool_results.append(result)
                    # 从响应中移除工具调用标记
                    clean_response = clean_response.replace(call['original'], "")
                
                # 构建包含工具结果的消息
                messages.append({"role": "assistant", "content": clean_response})
                
                # 添加工具结果
                tool_results_text = "\n\n".join(tool_results)
                messages.append({
                    "role": "user",
                    "content": f"工具执行结果：\n{tool_results_text}\n\n请基于这些结果给出完整的回答。"
                })
                
                current_iteration += 1
                continue
            
            # 没有工具调用，这是最终回答
            final_response = response
            break
        
        # 如果超过最大迭代次数，获取最后一次回答
        if current_iteration >= max_tool_iterations and not final_response:
            final_response = self.llm.invoke(messages, **kwargs)
        
        # 保存到历史记录
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_response, "assistant"))
        
        # 更新上下文
        if self.context_manager:
            self.context_manager.update_context(
                self.name,
                {
                    "output": final_response,
                    "status": "completed",
                    "tool_iterations": current_iteration
                },
                "result"
            )
            
            # 共享结果数据
            self.context_manager.share_data(
                f"{self.name}_result",
                final_response,
                from_agent=self.name
            )
        
        logger.info(f"✅ {self.name} 响应完成")
        return final_response
    
    def _parse_tool_calls(self, text: str) -> list:
        """解析文本中的工具调用"""
        pattern = r'\[TOOL_CALL:([^:]+):([^\]]+)\]'
        matches = re.findall(pattern, text)
        tool_calls = []
        for tool_name, parameters in matches:
            tool_calls.append({
                'tool_name': tool_name.strip(),
                'parameters': parameters.strip(),
                'original': f'[TOOL_CALL:{tool_name}:{parameters}]'
            })
        return tool_calls
    
    def _execute_tool_call(self, tool_name: str, parameters: str) -> str:
        """执行工具调用"""
        if not self.tool_registry:
            return "❌ 错误：未配置工具注册表"
        
        try:
            # 智能参数解析
            if tool_name == 'calculator':
                result = self.tool_registry.execute_tool(tool_name, parameters)
            else:
                param_dict = self._parse_tool_parameters(tool_name, parameters)
                tool = self.tool_registry.get_tool(tool_name)
                if not tool:
                    return f"❌ 错误：未找到工具 '{tool_name}'"
                result = tool.run(param_dict)
            
            return f"🔧 工具 {tool_name} 执行结果：\n{result}"
        except Exception as e:
            logger.error(f"工具调用失败: {e}", exc_info=True)
            return f"❌ 工具调用失败：{str(e)}"
    
    def _parse_tool_parameters(self, tool_name: str, parameters: str) -> dict:
        """智能解析工具参数"""
        param_dict = {}
        if '=' in parameters:
            if ',' in parameters:
                pairs = parameters.split(',')
                for pair in pairs:
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        param_dict[key.strip()] = value.strip()
            else:
                key, value = parameters.split('=', 1)
                param_dict[key.strip()] = value.strip()
        else:
            if tool_name == 'search':
                param_dict = {'query': parameters}
            elif tool_name == 'memory':
                param_dict = {'action': 'search', 'query': parameters}
            else:
                param_dict = {'input': parameters}
        return param_dict
    
    def send_message_to_agent(
        self,
        receiver: str,
        message_type: MessageType,
        content: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        向其他智能体发送消息
        
        Args:
            receiver: 接收者名称
            message_type: 消息类型
            content: 消息内容
        
        Returns:
            响应内容
        """
        if not self.communication_hub:
            logger.warning(f"{self.name} 未配置通信中心，无法发送消息")
            return None
        
        message = AgentMessage(
            sender=self.name,
            receiver=receiver,
            message_type=message_type,
            content=content,
            context=self.context_manager.get_all_context() if self.context_manager else {}
        )
        
        return self.communication_hub.send_message(message)
    
    def handle_message(self, message: AgentMessage) -> Dict[str, Any]:
        """
        处理接收到的消息（子类可以重写）
        
        Args:
            message: 消息对象
        
        Returns:
            响应内容
        """
        logger.debug(f"{self.name} 收到消息 - From: {message.sender}, Type: {message.message_type.value}")
        
        # 默认处理：根据消息类型返回响应
        if message.message_type == MessageType.QUERY:
            return {
                "status": "received",
                "agent": self.name,
                "message": "查询已收到，正在处理"
            }
        elif message.message_type == MessageType.REQUEST:
            return {
                "status": "received",
                "agent": self.name,
                "message": "请求已收到，正在处理"
            }
        else:
            return {
                "status": "received",
                "agent": self.name
            }
    
    def _handle_query_message(self, message: AgentMessage) -> Dict[str, Any]:
        """处理查询消息"""
        return self.handle_message(message)
    
    def _handle_request_message(self, message: AgentMessage) -> Dict[str, Any]:
        """处理请求消息"""
        return self.handle_message(message)
    
    def store_memory(
        self,
        memory_type: str,
        memory_data: Dict[str, Any]
    ):
        """
        存储记忆
        
        Args:
            memory_type: 记忆类型
            memory_data: 记忆数据
        """
        if not self.user_id:
            return
        
        if memory_type == "preference":
            memory_service.store_user_preference(
                self.user_id,
                memory_data.get("preference_type", "general"),
                memory_data
            )
        elif memory_type == "feedback":
            memory_service.store_user_feedback(
                self.user_id,
                memory_data.get("trip_id", ""),
                memory_data
            )
        elif memory_type == "context":
            memory_service.store_short_term_context(
                self.user_id,
                memory_data.get("context_key", "general"),
                memory_data
            )
    
    def add_tool(self, tool) -> None:
        """添加工具到Agent（便利方法）"""
        if not self.tool_registry:
            from hello_agents import ToolRegistry
            self.tool_registry = ToolRegistry()
            self.enable_tool_calling = True
        self.tool_registry.register_tool(tool)
        logger.debug(f"🔧 工具 '{tool.name}' 已添加到 {self.name}")
    
    def has_tools(self) -> bool:
        """检查是否有可用工具"""
        return self.enable_tool_calling and self.tool_registry is not None
    
    def list_tools(self) -> list:
        """列出所有可用工具"""
        if self.tool_registry:
            return self.tool_registry.list_tools()
        return []

