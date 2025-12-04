<template>
  <div class="result-container" v-if="tripPlan">
    <!-- 背景装饰 -->
    <div class="background-decoration">
      <div class="decoration-wave wave-1"></div>
      <div class="decoration-wave wave-2"></div>
    </div>

    <div class="result-content" ref="contentRef">
      <!-- 头部信息 -->
      <div class="header-section">
        <el-card class="header-card">
          <div class="trip-header">
            <div class="header-left">
              <div class="back-button" @click="goBack">
                <el-icon><Back /></el-icon>
                <span>返回</span>
              </div>
              <div class="header-title">
                <h1>{{ tripPlan.trip_title }}</h1>
                <div class="header-meta">
                  <span class="meta-item">
                    <el-icon><Calendar /></el-icon>
                    {{ tripPlan.days.length }}天{{ tripPlan.days.length - 1 }}晚
                  </span>
                  <span class="meta-item">
                    <el-icon><Wallet /></el-icon>
                    预算：¥{{ tripPlan.total_budget }}
                  </span>
                </div>
              </div>
            </div>
            <div class="header-actions">
              <el-button @click="goEdit" size="large" class="action-btn">
                <el-icon><Edit /></el-icon>
                编辑行程
              </el-button>
              <ExportButtons :trip-plan="tripPlan" :content-ref="contentRef" />
            </div>
          </div>
        </el-card>
      </div>

      <!-- 主要内容区 -->
      <el-row :gutter="24" class="main-content">
        <!-- 左侧：地图和行程 -->
        <el-col :xl="16" :lg="16" :md="24" :sm="24" :xs="24">
          <!-- 地图展示 -->
          <el-card class="map-card" shadow="hover">
            <template #header>
              <div class="card-header-custom">
                <h3>📍 行程地图</h3>
                <el-tag type="success" size="small">{{ allActivities.length }} 个地点</el-tag>
              </div>
            </template>
            <MapView :activities="allActivities" :center="mapCenter" />
          </el-card>

          <!-- 每日行程 -->
          <el-card 
            class="daily-plan-card" 
            v-for="day in tripPlan.days" 
            :key="day.day"
            shadow="hover"
          >
            <template #header>
              <div class="day-header">
                <div class="day-info">
                  <div class="day-badge">第 {{ day.day }} 天</div>
                  <div class="day-content">
                    <h3>{{ day.theme }}</h3>
                    <div class="weather-info" v-if="day.weather">
                      <span class="weather-item">
                        <el-icon><Sunny /></el-icon>
                        {{ day.weather.day_weather }}
                      </span>
                      <span class="weather-item">
                        <el-icon><Thermometer /></el-icon>
                        {{ day.weather.day_temp }}°C / {{ day.weather.night_temp }}°C
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </template>

            <!-- 活动时间轴 -->
            <el-timeline class="activity-timeline">
              <el-timeline-item
                v-for="(activity, index) in day.activities"
                :key="index"
                :timestamp="activity.time"
                placement="top"
                :color="getActivityColor(activity.type)"
              >
                <el-card class="activity-card" :class="{ 'has-image': activity.image_url }">
                  <div class="activity-content">
                    <!-- 左侧：图片 -->
                    <div class="activity-image" v-if="activity.image_url">
                      <el-image
                        :src="activity.image_url"
                        :alt="activity.name"
                        fit="cover"
                        lazy
                      >
                        <template #placeholder>
                          <div class="image-placeholder">
                            <el-icon class="is-loading"><Loading /></el-icon>
                          </div>
                        </template>
                        <template #error>
                          <div class="image-error">
                            <el-icon><Picture /></el-icon>
                          </div>
                        </template>
                      </el-image>
                    </div>

                    <!-- 右侧：内容 -->
                    <div class="activity-main">
                      <div class="activity-icon">{{ getActivityIcon(activity.type) }}</div>
                      <div class="activity-info">
                        <h4>{{ activity.name }}</h4>
                        <p class="activity-details">{{ activity.details }}</p>
                        <div class="activity-meta">
                          <el-tag size="small">{{ getActivityTypeText(activity.type) }}</el-tag>
                          <span v-if="activity.cost > 0" class="cost">¥{{ activity.cost }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </el-card>
              </el-timeline-item>
            </el-timeline>
          </el-card>
        </el-col>

        <!-- 右侧：预算和酒店 -->
        <el-col :xl="8" :lg="8" :md="24" :sm="24" :xs="24">
          <!-- 预算明细 -->
          <BudgetSummary :trip-plan="tripPlan" class="budget-section" />

          <!-- 推荐酒店 -->
          <el-card class="hotels-card" v-if="tripPlan.hotels && tripPlan.hotels.length > 0" shadow="hover">
            <template #header>
              <div class="card-header-custom">
                <h3>🏨 推荐酒店</h3>
                <el-tag type="warning" size="small">{{ tripPlan.hotels.length }} 家</el-tag>
              </div>
            </template>
            <div class="hotel-list">
              <div class="hotel-item" v-for="(hotel, index) in tripPlan.hotels" :key="index">
                <div class="hotel-rank">{{ index + 1 }}</div>
                <div class="hotel-info">
                  <h4>{{ hotel.name }}</h4>
                  <p class="hotel-address">
                    <el-icon><Location /></el-icon>
                    {{ hotel.address }}
                  </p>
                  <div class="hotel-meta">
                    <el-rate
                      v-if="typeof hotel.rating === 'number'"
                      :model-value="hotel.rating"
                      disabled
                      size="small"
                    />
                    <span class="hotel-price" v-if="hotel.price">
                      ¥{{ hotel.price }} / 晚
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </el-card>

          <!-- 旅行贴士 -->
          <el-card class="tips-card" shadow="hover">
            <template #header>
              <div class="card-header-custom">
                <h3>💡 旅行贴士</h3>
              </div>
            </template>
            <ul class="tips-list">
              <li v-for="(tip, index) in tips" :key="index">
                <el-icon class="tip-icon"><Check /></el-icon>
                <span>{{ tip }}</span>
              </li>
            </ul>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
  
  <el-empty v-else description="暂无行程数据">
    <el-button type="primary" @click="goBack">返回首页</el-button>
  </el-empty>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Back, 
  Edit, 
  Loading, 
  Picture, 
  Calendar, 
  Wallet, 
  Location, 
  Sunny, 
  Thermometer,
  Check 
} from '@element-plus/icons-vue'
import MapView from '@/components/MapView.vue'
import BudgetSummary from '@/components/BudgetSummary.vue'
import ExportButtons from '@/components/ExportButtons.vue'
import type { TripPlanResponse, Activity, Location as LocationType } from '@/types'

const router = useRouter()
const contentRef = ref<HTMLElement>()
const tripPlan = ref<TripPlanResponse | null>(null)

// 旅行贴士列表
const tips = [
  '提前预订门票和酒店可享受优惠',
  '关注当地天气变化，准备合适衣物',
  '随身携带充电宝和常用药品',
  '建议购买旅游保险，保障出行安全',
  '保管好个人财物和重要证件',
  '尊重当地文化和习俗，做文明游客'
]

// 数据清理函数，确保经纬度是数字
const sanitizeTripPlan = (plan: TripPlanResponse): TripPlanResponse => {
  plan.days.forEach(day => {
    day.activities.forEach(activity => {
      if (activity.location) {
        activity.location.lat = parseFloat(activity.location.lat as any)
        activity.location.lng = parseFloat(activity.location.lng as any)
      }
    })
  })
  if (plan.hotels) {
    plan.hotels.forEach(hotel => {
      if (hotel.location) {
        hotel.location.lat = parseFloat(hotel.location.lat as any)
        hotel.location.lng = parseFloat(hotel.location.lng as any)
      }
    })
  }
  return plan
}

// 获取行程数据
onMounted(() => {
  // 从路由 state 获取数据
  const state = history.state as { tripPlan?: TripPlanResponse }
  let planData: TripPlanResponse | null = null

  if (state?.tripPlan) {
    planData = state.tripPlan
  } else {
    // 如果没有数据，尝试从 sessionStorage 获取
    const savedPlan = sessionStorage.getItem('currentTripPlan')
    if (savedPlan) {
      planData = JSON.parse(savedPlan)
    }
  }
  
  if (planData) {
    tripPlan.value = sanitizeTripPlan(planData)
    // 保存清理后的数据到 sessionStorage
    sessionStorage.setItem('currentTripPlan', JSON.stringify(tripPlan.value))
  } else {
    // 如果仍然没有数据，可以跳转回主页或显示错误
    // router.push('/')
  }
})

// 获取所有活动用于地图展示
const allActivities = computed(() => {
  if (!tripPlan.value) return []
  return tripPlan.value.days.flatMap(day => day.activities)
})

// 计算地图中心点
const mapCenter = computed((): LocationType | undefined => {
  const activities = allActivities.value.filter(a => a.location)
  if (activities.length === 0) return undefined
  
  const firstActivity = activities[0]
  return firstActivity.location
})

// 获取活动类型颜色
const getActivityColor = (type: string): string => {
  const colorMap: Record<string, string> = {
    attraction: '#409eff',
    dining: '#67c23a',
    hotel: '#e6a23c',
    transport: '#909399'
  }
  return colorMap[type] || '#909399'
}

// 获取活动图标
const getActivityIcon = (type: string): string => {
  const iconMap: Record<string, string> = {
    attraction: '🎯',
    dining: '🍽️',
    hotel: '🏨',
    transport: '🚗'
  }
  return iconMap[type] || '📍'
}

// 获取活动类型文本
const getActivityTypeText = (type: string): string => {
  const typeMap: Record<string, string> = {
    attraction: '景点',
    dining: '餐饮',
    hotel: '酒店',
    transport: '交通'
  }
  return typeMap[type] || type
}

// 返回首页
const goBack = () => {
  router.push({ name: 'Home' })
}

// 编辑行程
const goEdit = () => {
  router.push({ 
    name: 'EditPlan',
    state: { tripPlan: tripPlan.value }
  })
}
</script>

<style scoped lang="scss">
.result-container {
  position: relative;
  min-height: 100vh;
  padding: 0;
  background: linear-gradient(to bottom, #f8f9fa 0%, #e9ecef 100%);

  // 背景装饰
  .background-decoration {
    position: absolute;
    width: 100%;
    height: 400px;
    top: 0;
    left: 0;
    overflow: hidden;
    pointer-events: none;

    .decoration-wave {
      position: absolute;
      width: 200%;
      height: 100%;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

      &.wave-1 {
        opacity: 1;
        clip-path: polygon(0 0, 100% 0, 100% 85%, 0 100%);
      }

      &.wave-2 {
        opacity: 0.5;
        clip-path: polygon(0 0, 100% 0, 100% 75%, 0 90%);
      }
    }
  }

  .result-content {
    position: relative;
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
    z-index: 1;
  }

  // 头部区域
  .header-section {
    margin-bottom: 24px;

    .header-card {
      border-radius: 16px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
      border: none;
      overflow: hidden;

      :deep(.el-card__body) {
        padding: 24px 32px;
      }
      
      .trip-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 24px;

        .header-left {
          display: flex;
          align-items: center;
          gap: 24px;
          flex: 1;

          .back-button {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            border-radius: 8px;
            background: #f5f7fa;
            color: #606266;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 14px;

            &:hover {
              background: #e4e7ed;
              color: #409eff;
            }
          }

          .header-title {
            flex: 1;

            h1 {
              margin: 0 0 8px 0;
              font-size: 28px;
              font-weight: 600;
              color: #303133;
              background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
              -webkit-background-clip: text;
              -webkit-text-fill-color: transparent;
              background-clip: text;
            }

            .header-meta {
              display: flex;
              gap: 24px;
              
              .meta-item {
                display: flex;
                align-items: center;
                gap: 6px;
                font-size: 14px;
                color: #606266;

                .el-icon {
                  color: #909399;
                }
              }
            }
          }
        }
        
        .header-actions {
          display: flex;
          gap: 12px;
          flex-shrink: 0;

          .action-btn {
            border-radius: 8px;
            transition: all 0.3s;

            &:hover {
              transform: translateY(-2px);
              box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
            }
          }
        }
      }
    }
  }

  // 主要内容
  .main-content {
    // 通用卡片头部
    .card-header-custom {
      display: flex;
      justify-content: space-between;
      align-items: center;

      h3 {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
        color: #303133;
      }
    }

    .map-card {
      margin-bottom: 24px;
      border-radius: 16px;
      border: none;
      transition: all 0.3s;

      &:hover {
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
      }
    }

    .daily-plan-card {
      margin-bottom: 24px;
      border-radius: 16px;
      border: none;
      transition: all 0.3s;

      &:hover {
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
        transform: translateY(-2px);
      }
      
      .day-header {
        .day-info {
          display: flex;
          align-items: center;
          gap: 20px;

          .day-badge {
            padding: 8px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
            white-space: nowrap;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
          }

          .day-content {
            flex: 1;

            h3 {
              margin: 0 0 8px 0;
              font-size: 20px;
              font-weight: 600;
              color: #303133;
            }

            .weather-info {
              display: flex;
              gap: 20px;

              .weather-item {
                display: flex;
                align-items: center;
                gap: 6px;
                font-size: 14px;
                color: #606266;

                .el-icon {
                  color: #ffa500;
                }
              }
            }
          }
        }
      }

      .activity-timeline {
        padding: 20px 0;
        
        .activity-card {
          margin-top: 8px;
          transition: all 0.3s ease;
          border-radius: 12px;
          border: none;
          
          &:hover {
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
            transform: translateX(4px);
          }

          &.has-image {
            .activity-content {
              display: flex;
              gap: 20px;
            }
          }
          
          .activity-content {
            .activity-image {
              flex-shrink: 0;
              width: 200px;
              height: 150px;
              border-radius: 12px;
              overflow: hidden;
              box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

              :deep(.el-image) {
                width: 100%;
                height: 100%;
              }

              .image-placeholder,
              .image-error {
                width: 100%;
                height: 100%;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, #f5f7fa 0%, #e4e7ed 100%);
                color: #909399;
                font-size: 32px;
              }
            }

            .activity-main {
              display: flex;
              gap: 16px;
              flex: 1;
              
              .activity-icon {
                font-size: 36px;
                flex-shrink: 0;
                width: 48px;
                height: 48px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, #f5f7fa 0%, #e4e7ed 100%);
                border-radius: 12px;
              }
              
              .activity-info {
                flex: 1;
                
                h4 {
                  margin: 0 0 10px 0;
                  font-size: 17px;
                  color: #303133;
                  font-weight: 600;
                }
                
                .activity-details {
                  margin: 0 0 12px 0;
                  color: #606266;
                  font-size: 14px;
                  line-height: 1.8;
                }
                
                .activity-meta {
                  display: flex;
                  align-items: center;
                  gap: 12px;
                  
                  .cost {
                    font-weight: bold;
                    color: #f56c6c;
                    font-size: 16px;
                  }
                }
              }
            }
          }
        }
      }
    }

    .budget-section {
      margin-bottom: 24px;
    }

    .hotels-card {
      margin-bottom: 24px;
      border-radius: 16px;
      border: none;
      transition: all 0.3s;

      &:hover {
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
      }
      
      .hotel-list {
        .hotel-item {
          display: flex;
          gap: 16px;
          padding: 20px 0;
          border-bottom: 1px solid #f0f0f0;
          transition: all 0.3s;
          
          &:last-child {
            border-bottom: none;
          }

          &:hover {
            background: #fafafa;
            margin: 0 -16px;
            padding: 20px 16px;
            border-radius: 8px;
          }

          .hotel-rank {
            flex-shrink: 0;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
            color: #fff;
            border-radius: 50%;
            font-weight: bold;
            font-size: 14px;
            box-shadow: 0 2px 8px rgba(255, 215, 0, 0.3);
          }
          
          .hotel-info {
            flex: 1;

            h4 {
              margin: 0 0 8px 0;
              font-size: 16px;
              color: #303133;
              font-weight: 600;
            }
            
            .hotel-address {
              margin: 0 0 10px 0;
              font-size: 13px;
              color: #909399;
              display: flex;
              align-items: center;
              gap: 4px;

              .el-icon {
                color: #409eff;
              }
            }
            
            .hotel-meta {
              display: flex;
              justify-content: space-between;
              align-items: center;
              
              .hotel-price {
                font-weight: bold;
                color: #f56c6c;
                font-size: 16px;
              }
            }
          }
        }
      }
    }

    .tips-card {
      border-radius: 16px;
      border: none;
      transition: all 0.3s;

      &:hover {
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
      }
      
      .tips-list {
        margin: 0;
        padding: 0;
        list-style: none;
        
        li {
          display: flex;
          align-items: flex-start;
          gap: 12px;
          padding: 12px 0;
          color: #606266;
          font-size: 14px;
          line-height: 1.8;
          border-bottom: 1px solid #f0f0f0;
          transition: all 0.3s;

          &:last-child {
            border-bottom: none;
          }

          &:hover {
            color: #409eff;
            padding-left: 8px;

            .tip-icon {
              color: #67c23a;
              transform: scale(1.2);
            }
          }

          .tip-icon {
            color: #909399;
            font-size: 16px;
            flex-shrink: 0;
            margin-top: 2px;
            transition: all 0.3s;
          }

          span {
            flex: 1;
          }
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .result-container {
    .header-section {
      .header-card {
        .trip-header {
          flex-direction: column;
          align-items: flex-start;

          .header-left {
            width: 100%;
          }

          .header-actions {
            width: 100%;
            justify-content: flex-end;
          }
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .result-container {
    .result-content {
      padding: 12px;
    }

    .header-section {
      .header-card {
        :deep(.el-card__body) {
          padding: 16px;
        }

        .trip-header {
          .header-left {
            flex-direction: column;
            align-items: flex-start;
            gap: 12px;

            .header-title {
              h1 {
                font-size: 22px;
              }

              .header-meta {
                flex-direction: column;
                gap: 8px;
              }
            }
          }

          .header-actions {
            flex-direction: column;
            width: 100%;

            .action-btn {
              width: 100%;
            }
          }
        }
      }
    }

    .main-content {
      .daily-plan-card {
        .day-header {
          .day-info {
            flex-direction: column;
            align-items: flex-start;
            gap: 12px;
          }
        }

        .activity-card {
          &.has-image {
            .activity-content {
              flex-direction: column;
            }
          }

          .activity-content {
            .activity-image {
              width: 100%;
            }
          }
        }
      }
    }
  }
}
</style>
