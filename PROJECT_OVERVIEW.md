# 智能旅行规划系统 - 项目总览

## 🎯 项目简介

这是一个基于 Vue 3 + TypeScript 的智能旅行规划前端系统，与后端 FastAPI + Agent 架构完美配合，提供完整的智能行程规划解决方案。

## 📁 项目结构

```
trip_planner/
├── backend/                      # 后端服务（已有）
│   ├── app/
│   │   ├── agents/              # Agent 智能体
│   │   ├── api/v1/              # API 接口
│   │   ├── models/              # 数据模型
│   │   ├── services/            # 业务服务
│   │   └── tools/               # MCP 工具
│   └── requirements.txt
│
└── frontend/                     # 前端应用（新建）
    ├── src/
    │   ├── components/          # 通用组件
    │   │   ├── MapView.vue     # 地图展示组件
    │   │   ├── BudgetSummary.vue  # 预算汇总组件
    │   │   └── ExportButtons.vue  # 导出功能组件
    │   ├── views/               # 页面组件
    │   │   ├── Home.vue        # 首页 - 行程规划表单
    │   │   ├── Result.vue      # 结果页 - 行程展示
    │   │   └── EditPlan.vue    # 编辑页 - 行程编辑
    │   ├── services/            # API 服务
    │   │   └── api.ts          # API 请求封装
    │   ├── types/               # 类型定义
    │   │   └── index.ts        # TypeScript 接口
    │   ├── router/              # 路由配置
    │   │   └── index.ts
    │   ├── App.vue              # 根组件
    │   ├── main.ts              # 应用入口
    │   └── env.d.ts             # 环境变量类型定义
    ├── index.html               # HTML 模板
    ├── package.json             # 依赖配置
    ├── tsconfig.json            # TypeScript 配置
    ├── vite.config.ts           # Vite 配置
    ├── .env                     # 环境变量
    └── README.md                # 前端文档
```

## ✨ 核心功能

### 1. 智能行程规划 (Home.vue)
- 📍 **目的地选择**：输入任意城市
- 📅 **日期范围**：灵活选择出行日期
- 🎯 **偏好设置**：历史、自然、美食、购物等多种偏好
- 🏨 **酒店选择**：经济、舒适、高档、豪华等级
- 💵 **预算控制**：经济、中等、宽裕、豪华四档
- 🔥 **热门推荐**：预设示例行程快速开始

### 2. 地图可视化 (MapView.vue)
- 🗺️ **高德地图集成**：专业地图服务
- 📍 **景点标记**：自动标注所有活动位置
- 🛣️ **路线绘制**：按时间顺序连接各个景点
- ℹ️ **信息窗口**：点击标记查看详细信息
- 🔍 **自适应视野**：自动调整最佳观看角度
- 👁️ **路线切换**：支持显示/隐藏路线

### 3. 预算计算 (BudgetSummary.vue)
- 💰 **总预算统计**：自动计算所有费用
- 📊 **分类展示**：景点、餐饮、住宿、交通分类
- 📈 **百分比显示**：各项费用占比一目了然
- 📝 **明细列表**：可展开查看每项费用详情
- 💡 **预算建议**：根据总额给出旅行建议

### 4. 行程编辑 (EditPlan.vue)
- ➕ **添加天数**：动态增加行程天数
- ✏️ **编辑活动**：修改活动名称、时间、描述、费用
- 🗑️ **删除操作**：删除不需要的天数或活动
- 🏨 **酒店管理**：添加、编辑、删除酒店信息
- 🗺️ **实时预览**：右侧地图实时更新
- 💾 **保存预览**：保存后跳转到结果页

### 5. 导出功能 (ExportButtons.vue)
- 📄 **PDF 导出**：高质量 PDF 文档
- 🖼️ **图片导出**：PNG 格式图片
- ⚙️ **自定义选项**：选择导出内容（预算、地图、酒店）
- 📏 **自动分页**：长内容自动分页处理

## 🔄 数据流转

```
用户输入 → 表单验证 → API 请求 → 后端处理
                                    ↓
后端 Agent 系统:
  - AttractionSearchAgent (景点搜索)
  - HotelSearchAgent (酒店推荐)
  - WeatherQueryAgent (天气查询)
  - PlannerAgent (行程规划)
                                    ↓
通过 MCP 协议调用外部 API (高德地图等)
                                    ↓
整合结果 → 返回前端 → 数据渲染 → 展示给用户
                                    ↓
用户可编辑 → 保存更新 → 导出分享
```

## 🛠️ 技术栈

### 前端技术
- **Vue 3**: Composition API + `<script setup>` 语法
- **TypeScript**: 完整类型安全
- **Vite**: 极速开发服务器
- **Element Plus**: 企业级 UI 组件库
- **Vue Router**: 单页应用路由
- **Axios**: HTTP 请求库
- **高德地图 JS API**: 地图服务
- **html2canvas**: HTML 转图片
- **jsPDF**: PDF 生成
- **dayjs**: 日期处理

### 后端技术（已有）
- **FastAPI**: 现代化 Python Web 框架
- **LangChain/Agent**: AI 智能体框架
- **MCP Protocol**: 模型上下文协议
- **Pydantic**: 数据验证

## 🚀 快速启动

### 1. 安装前端依赖

```bash
cd frontend
npm install
```

### 2. 配置环境变量

编辑 `frontend/.env` 文件：

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_AMAP_KEY=您的高德地图Key
VITE_AMAP_SECURITY_CODE=您的安全密钥（可选）
```

### 3. 启动后端服务

```bash
cd backend
python run.py
```

后端将运行在 http://localhost:8000

### 4. 启动前端服务

```bash
cd frontend
npm run dev
```

前端将运行在 http://localhost:5173

## 📝 开发说明

### API 接口

**行程规划接口**
- 端点: `POST /api/v1/trips/plan`
- 请求体: `TripPlanRequest`
- 响应: `TripPlanResponse`

**健康检查**
- 端点: `GET /health`
- 响应: `{"status": "ok"}`

### 数据模型

主要接口定义在 `frontend/src/types/index.ts`：
- `TripPlanRequest`: 行程规划请求
- `TripPlanResponse`: 行程规划响应
- `DailyPlan`: 每日计划
- `Activity`: 活动信息
- `Hotel`: 酒店信息
- `Location`: 地理位置

### 组件使用

```vue
<!-- 地图组件 -->
<MapView :activities="activities" :center="center" />

<!-- 预算组件 -->
<BudgetSummary :trip-plan="tripPlan" />

<!-- 导出按钮 -->
<ExportButtons :trip-plan="tripPlan" :content-ref="contentRef" />
```

## 🎨 UI/UX 特性

- 🎯 **现代化设计**: 清爽简洁的界面
- 📱 **响应式布局**: 适配各种屏幕尺寸
- 🎭 **过渡动画**: 流畅的页面切换
- 🌈 **主题色彩**: 统一的视觉风格
- ⚡ **加载状态**: 友好的加载提示
- 💬 **消息反馈**: 清晰的操作反馈

## 🔧 配置说明

### Vite 配置
- 路径别名: `@` 指向 `src` 目录
- 代理配置: `/api` 代理到后端服务
- 开发端口: 5173

### TypeScript 配置
- 严格模式: 启用
- 装饰器: 支持
- JSX: preserve 模式

## 📦 依赖说明

### 核心依赖
- `vue`: ^3.4.0
- `vue-router`: ^4.2.5
- `element-plus`: ^2.5.0
- `axios`: ^1.6.2
- `@amap/amap-jsapi-loader`: ^1.0.1

### 工具依赖
- `html2canvas`: ^1.4.1
- `jspdf`: ^2.5.1
- `dayjs`: ^1.11.10

### 开发依赖
- `typescript`: ^5.3.3
- `vite`: ^5.0.10
- `@vitejs/plugin-vue`: ^5.0.0

## 🐛 注意事项

1. **高德地图 Key**: 需要在高德开放平台申请 Web 端 Key
2. **CORS 配置**: 后端已配置 CORS，默认允许 5173 端口
3. **浏览器支持**: 推荐使用 Chrome、Edge、Firefox 等现代浏览器
4. **依赖安装**: 首次运行需要安装所有依赖
5. **TypeScript 错误**: 安装依赖后 TypeScript 错误会自动消失

## 📈 未来优化

- [ ] 添加 Pinia 状态管理
- [ ] 实现行程收藏功能
- [ ] 添加用户登录系统
- [ ] 支持多种地图服务
- [ ] 优化移动端体验
- [ ] 添加单元测试
- [ ] 实现 PWA 支持
- [ ] 国际化支持

## 📄 许可证

MIT License

---

**开发完成时间**: 2024年
**维护者**: AI Assistant
**版本**: v1.0.0
