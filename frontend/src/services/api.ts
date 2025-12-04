import axios from 'axios'
import type { TripPlanRequest, TripPlanResponse } from '@/types'

// 创建axios实例
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 100000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    const errorMessage = error.response?.data?.detail || error.message || '请求失败'
    return Promise.reject(new Error(errorMessage))
  }
)

// API服务
export const tripApi = {
  /**
   * 创建行程规划
   * @param request 行程规划请求数据
   * @param cancelToken 可选的取消令牌
   */
  async createTripPlan(
    request: TripPlanRequest,
    cancelToken?: any
  ): Promise<TripPlanResponse> {
    return apiClient.post('/api/v1/trips/plan', request, {
      cancelToken
    })
  },

  /**
   * 健康检查
   */
  async healthCheck(): Promise<{ status: string }> {
    return apiClient.get('/health')
  }
}

export default apiClient
