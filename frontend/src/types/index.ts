// 基础数据模型
export interface Location {
  lat: number
  lng: number
}

export interface Attraction {
  name: string
  address: string
  location?: Location
  rating: number | string
  type: string
}

export interface Hotel {
  name: string
  address: string
  location?: Location
  price: number | string
  rating: number | string
}

export interface Dining {
  name: string
  address: string
  location?: Location
  cost_per_person: number | string
  rating: number | string
}

export interface Weather {
  date: string
  day_weather: string
  night_weather: string
  day_temp: string
  night_temp: string
}

// 行程规划请求模型
export interface TripPlanRequest {
  destination: string
  start_date: string
  end_date: string
  preferences: string[]
  hotel_preferences: string[]
  budget: string
}

// 活动模型
export interface Activity {
  time: string
  type: string
  name: string
  details: string
  cost: number
  location?: Location
  image_url?: string  // 景点图片URL
}

// 每日行程计划
export interface DailyPlan {
  day: number
  theme: string
  weather?: Weather
  activities: Activity[]
}

// 行程规划响应模型
export interface TripPlanResponse {
  trip_title: string
  total_budget: number
  hotels: Hotel[]
  days: DailyPlan[]
}

// 表单数据类型
export interface TripFormData {
  destination: string
  dateRange: [string, string]
  preferences: string[]
  hotelPreferences: string[]
  budget: string
}

// 预算明细类型
export interface BudgetDetail {
  category: string
  amount: number
  items: {
    name: string
    cost: number
  }[]
}

// 导出选项类型
export interface ExportOptions {
  format: 'pdf' | 'image'
  includeBudget: boolean
  includeMap: boolean
}
