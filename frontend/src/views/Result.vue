<template>
  <div class="result-container" v-if="tripPlan">
    <!-- 鑳屾櫙瑁呴グ -->
    <div class="background-decoration">
      <div class="decoration-wave wave-1"></div>
      <div class="decoration-wave wave-2"></div>
    </div>

    <div class="result-content" ref="contentRef">
      <!-- 澶撮儴淇℃伅 -->
      <div class="header-section">
        <el-card class="header-card">
          <div class="trip-header">
            <div class="header-left">
              <div class="back-button" @click="goBack">
                <el-icon><Back /></el-icon>
                <span>杩斿洖</span>
              </div>
              <div class="header-title">
                <h1>{{ tripPlan.trip_title }}</h1>
                <div class="header-meta">
                  <span class="meta-item">
                    <el-icon><Calendar /></el-icon>
                    {{ tripPlan.days.length }}澶﹞{{ tripPlan.days.length - 1 }}鏅?
                  </span>
                  <span class="meta-item">
                    <el-icon><Wallet /></el-icon>
                    棰勭畻浼扮畻锛毬{{ tripPlan.total_budget.total }}
                  </span>
                  <span class="meta-item" v-if="tripPlan.version != null">
                    鐗堟湰锛歷{{ tripPlan.version }}
                  </span>
                </div>
              </div>
            </div>
            <div class="header-actions">
              <el-button @click="goEdit" size="large" class="action-btn">
                <el-icon><Edit /></el-icon>
                缂栬緫琛岀▼
              </el-button>
              <ExportButtons :trip-plan="tripPlan" :content-ref="contentRef" :map-ref="mapViewRef" />
            </div>
          </div>
        </el-card>
      </div>

      <!-- 涓昏鍐呭鍖?-->
      <el-alert
        v-if="tripPlan.city_support_message"
        :title="tripPlan.city_support_message"
        :type="tripPlan.city_support_level === 'supported' ? 'success' : (tripPlan.city_support_level === 'beta' ? 'warning' : 'error')"
        :closable="false"
        class="city-support-alert"
      />

      <el-row :gutter="24" class="main-content">
        <!-- 宸︿晶锛氬湴鍥惧拰琛岀▼ -->
        <el-col :xl="16" :lg="16" :md="24" :sm="24" :xs="24">
          <!-- 鍦板浘灞曠ず -->
          <el-card class="map-card" shadow="hover">
            <template #header>
              <div class="card-header-custom">
                <h3>馃搷 琛岀▼鍦板浘</h3>
                <el-tag type="success" size="small">{{ allPoints.length }} 涓湴鐐?</el-tag>
              </div>
            </template>
            <MapView ref="mapViewRef" :points="allPoints" :center="mapCenter" />
          </el-card>

          <!-- 姣忔棩琛岀▼ -->
          <el-card
            class="daily-plan-card"
            v-for="day in tripPlan.days"
            :key="day.day"
            shadow="hover"
          >
            <template #header>
              <div class="day-header">
                <div class="day-info">
                  <div class="day-badge">绗?{{ day.day }} 澶?</div>
                  <div class="day-content">
                    <h3>{{ day.theme }}</h3>
                    <div class="weather-info" v-if="day.weather">
                      <span class="weather-item">
                        <el-icon><Sunny /></el-icon>
                        {{ day.weather.day_weather }} / {{ day.weather.night_weather }}
                      </span>
                      <span class="weather-item">
                        娓╁害锛歿{{ day.weather.day_temp }}掳C / {{ day.weather.night_temp }}掳C
                      </span>
                      <span
                        class="weather-item"
                        v-if="day.weather.day_wind || day.weather.night_wind"
                      >
                        椋庡悜椋庡姏锛?
                        <template v-if="day.weather.day_wind">
                          鐧藉ぉ {{ day.weather.day_wind }}
                        </template>
                        <template v-if="day.weather.night_wind">
                          锛屽闂?{{ day.weather.night_wind }}
                        </template>
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </template>

            <!-- 鎺ㄨ崘浣忓 -->
            <div v-if="day.recommended_hotel" class="recommended-hotel">
              <el-card shadow="never">
                <div class="recommended-hotel-content">
                  <div class="hotel-icon">馃彣</div>
                  <div class="hotel-info">
                    <h4>鎺ㄨ崘浣忓锛歿{{ day.recommended_hotel.name }}</h4>
                    <p class="hotel-address">
                      <el-icon><Location /></el-icon>
                      {{ day.recommended_hotel.address }}
                    </p>
                    <div class="hotel-meta">
                      <span v-if="day.recommended_hotel.distance_to_main_attraction_km != null">
                        璺濅富瑕佹櫙鐐圭害 {{ day.recommended_hotel.distance_to_main_attraction_km }} km
                      </span>
                      <span v-if="day.budget.hotel_cost > 0" class="cost">
                        閰掑簵棰勭畻锛毬{{ day.budget.hotel_cost.toFixed(2) }}
                      </span>
                    </div>
                  </div>
                </div>
              </el-card>
            </div>

            <!-- 鏅偣鍒楄〃 -->
            <div class="section-title">
              <h4>馃幆 鏅偣瀹夋帓</h4>
              <span class="section-subtitle">鍏?{{ day.attractions.length }} 涓櫙鐐?</span>
            </div>

            <el-timeline class="activity-timeline">
              <el-timeline-item
                v-for="(attraction, index) in day.attractions"
                :key="`attraction-${index}`"
                :timestamp="`绗?${index + 1} 绔檂`"
                placement="top"
                :color="getActivityColor('attraction')"
              >
                <el-card class="activity-card" :class="{ 'has-image': attraction.image_urls && attraction.image_urls.length > 0 }">
                  <div class="activity-content">
                    <!-- 宸︿晶锛氬浘鐗囷紝浼樺厛浣跨敤鏅偣鍥剧墖锛岀己澶辨椂鏄剧ず榛樿鍥?-->
                    <div class="activity-image">
                      <div class="attraction-number-badge">{{ index + 1 }}</div>
                      <el-image
                        :src="attraction.image_urls && attraction.image_urls.length > 0 ? attraction.image_urls[0] : DEFAULT_ATTRACTION_IMAGE"
                        :alt="attraction.name"
                        fit="cover"
                        lazy
                      >
                        <template #placeholder>
                          <div class="image-placeholder">
                            <el-icon class="is-loading"><Loading /></el-icon>
                          </div>
                        </template>
                        <template #error>
                          <div class="image-error image-fallback">
                            <!-- 榛樿鏅偣鍥剧墖 -->
                          </div>
                        </template>
                      </el-image>
                    </div>

                    <!-- 鍙充晶锛氬唴瀹?-->
                    <div class="activity-main">
                      <div class="activity-icon">{{ getActivityIcon('attraction') }}</div>
                      <div class="activity-info">
                        <h4>{{ attraction.name }}</h4>
                        <p class="activity-details">{{ attraction.description }}</p>
                        <div class="activity-meta">
                          <el-tag size="small">鏅偣 路 {{ attraction.type }}</el-tag>
                          <span v-if="attraction.ticket_price && attraction.ticket_price !== 'N/A'" class="cost">
                            <template v-if="typeof attraction.ticket_price === 'number'">
                              闂ㄧエ锛毬{{ attraction.ticket_price }}
                            </template>
                            <template v-else-if="attraction.ticket_price === '鍏嶈垂'">
                              闂ㄧエ锛氬厤璐?
                            </template>
                            <template v-else>
                              闂ㄧエ锛歿{{ attraction.ticket_price }}
                            </template>
                          </span>
                          <span v-if="attraction.suggested_duration_hours" class="duration">
                            寤鸿娓哥帺锛歿{{ attraction.suggested_duration_hours }} 灏忔椂
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </el-card>
              </el-timeline-item>
            </el-timeline>

            <!-- 椁愰ギ鍒楄〃 -->
            <div class="section-title" v-if="day.dinings && day.dinings.length > 0">
              <h4>馃嵔锔?椁愰ギ鎺ㄨ崘</h4>
              <span class="section-subtitle">鍏?{{ day.dinings.length }} 瀹堕鍘?</span>
            </div>
            <div v-if="day.dinings && day.dinings.length > 0" class="dining-list">
              <el-card
                v-for="(dining, index) in day.dinings"
                :key="`dining-${index}`"
                class="dining-card"
                shadow="never"
              >
                <div class="dining-content">
                  <div class="dining-icon">{{ getActivityIcon('dining') }}</div>
                  <div class="dining-info">
                    <h4>{{ dining.name }}</h4>
                    <p class="dining-address">
                      <el-icon><Location /></el-icon>
                      {{ dining.address }}
                    </p>
                    <div class="dining-meta">
                      <span v-if="dining.cost_per_person && dining.cost_per_person !== 'N/A'">
                        浜哄潎锛毬{{ dining.cost_per_person }}
                      </span>
                      <span v-if="dining.rating && dining.rating !== 'N/A'">
                        璇勫垎锛歿{{ dining.rating }}
                      </span>
                    </div>
                  </div>
                </div>
              </el-card>
            </div>
          </el-card>
        </el-col>

        <!-- 鍙充晶锛氶绠楀拰閰掑簵 -->
        <el-col :xl="8" :lg="8" :md="24" :sm="24" :xs="24">
          <!-- 棰勭畻鏄庣粏 -->
          <BudgetSummary :trip-plan="tripPlan" class="budget-section" />

          <!-- 鎺ㄨ崘閰掑簵 -->
          <el-card class="hotels-card" v-if="tripPlan.hotels && tripPlan.hotels.length > 0" shadow="hover">
            <template #header>
              <div class="card-header-custom">
                <h3>馃彣 鎺ㄨ崘閰掑簵</h3>
                <el-tag type="warning" size="small">{{ tripPlan.hotels.length }} 瀹?</el-tag>
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
                      <template v-if="typeof hotel.price === 'number' && hotel.price > 0">
                        楼{{ hotel.price.toFixed(2) }} / 鏅?
                      </template>
                      <template v-else>
                        {{ hotel.price }}
                      </template>
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </el-card>

          <!-- 鏃呰璐村＋ -->
          <el-card class="tips-card" shadow="hover">
            <template #header>
              <div class="card-header-custom">
                <h3>馃挕 鏃呰璐村＋</h3>
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

  <el-empty v-else description="鏆傛棤琛岀▼鏁版嵁">
    <el-button type="primary" @click="goBack">杩斿洖棣栭〉</el-button>
  </el-empty>
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  Back,
  Edit,
  Loading,
  Calendar,
  Wallet,
  Location,
  Sunny,
  Check,
} from '@element-plus/icons-vue'
import BudgetSummary from '@/components/BudgetSummary.vue'
import type { Location as LocationType, MapPoint, TripPlanResponse } from '@/types'
import { useTripStore } from '@/stores/trip'

const MapView = defineAsyncComponent(() => import('@/components/MapView.vue'))
const ExportButtons = defineAsyncComponent(() => import('@/components/ExportButtons.vue'))

const router = useRouter()
const tripStore = useTripStore()
const contentRef = ref<HTMLElement>()
const mapViewRef = ref<any>(null)

const tripPlan = computed<TripPlanResponse | null>(() => {
  return tripStore.currentTrip ?? tripStore.hydrateCurrentTrip()
})

const DEFAULT_ATTRACTION_IMAGE =
  'https://images.unsplash.com/photo-1508261306211-45a1c5c2a5c5?auto=format&fit=crop&w=900&q=80'

const tips = [
  '鎻愬墠棰勮闂ㄧエ鍜岄厭搴楀彲浜彈浼樻儬',
  '鍏虫敞褰撳湴澶╂皵鍙樺寲锛屽噯澶囧悎閫傝。鐗?',
  '闅忚韩鎼哄甫鍏呯數瀹濆拰甯哥敤鑽搧',
  '寤鸿璐拱鏃呮父淇濋櫓锛屼繚闅滃嚭琛屽畨鍏?',
  '淇濈濂戒釜浜鸿储鐗╁拰閲嶈璇佷欢',
  '灏婇噸褰撳湴鏂囧寲鍜屼範淇楋紝鍋氭枃鏄庢父瀹?',
]

const allPoints = computed<MapPoint[]>(() => {
  if (!tripPlan.value) return []

  const points: MapPoint[] = []

  tripPlan.value.days.forEach((day) => {
    day.attractions.forEach((attraction) => {
      points.push({
        name: attraction.name,
        type: 'attraction',
        description: attraction.description,
        location: attraction.location,
      })
    })

    day.dinings.forEach((dining) => {
      points.push({
        name: dining.name,
        type: 'dining',
        description: dining.address,
        location: dining.location,
      })
    })

    if (day.recommended_hotel?.location) {
      points.push({
        name: day.recommended_hotel.name,
        type: 'hotel',
        description: day.recommended_hotel.address,
        location: day.recommended_hotel.location,
      })
    }
  })

  return points.filter((point): point is MapPoint & { location: LocationType } => Boolean(point.location))
})

const mapCenter = computed((): LocationType | undefined => {
  return allPoints.value[0]?.location
})

const getActivityColor = (type: string): string => {
  const colorMap: Record<string, string> = {
    attraction: '#409eff',
    dining: '#67c23a',
    hotel: '#e6a23c',
    transport: '#909399',
  }
  return colorMap[type] || '#909399'
}

const getActivityIcon = (type: string): string => {
  const iconMap: Record<string, string> = {
    attraction: '馃幆',
    dining: '馃嵔锔?',
    hotel: '馃彣',
    transport: '馃殫',
  }
  return iconMap[type] || '馃搷'
}

const goBack = () => {
  router.push({ name: 'Home' })
}

const goEdit = () => {
  if (tripPlan.value) {
    tripStore.startEditing(tripPlan.value, 'result')
  }

  router.push({
    name: 'EditPlan',
    query: {
      returnTo: 'result',
    },
  })
}
</script>

<style scoped lang="scss">
.result-container {
  position: relative;
  min-height: 100vh;
  padding: 0;
  background: linear-gradient(to bottom, #f8f9fa 0%, #e9ecef 100%);

  // 鑳屾櫙瑁呴グ
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

  .city-support-alert {
    margin-bottom: 16px;
  }

  // 澶撮儴鍖哄煙
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

  // 涓昏鍐呭
  .main-content {
    // 閫氱敤鍗＄墖澶撮儴
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
              position: relative;

              .attraction-number-badge {
                position: absolute;
                top: 8px;
                left: 8px;
                z-index: 10;
                width: 28px;
                height: 28px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 14px;
                font-weight: bold;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
                border: 2px solid white;
              }

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

              .image-fallback {
                background-image: url('https://images.unsplash.com/photo-1508261306211-45a1c5c2a5c5?auto=format&fit=crop&w=900&q=80');
                background-size: cover;
                background-position: center;
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

// 鍝嶅簲寮忚璁?
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
