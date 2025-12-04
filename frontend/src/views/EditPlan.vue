<template>
  <div class="edit-plan-container" v-if="editablePlan">
    <!-- 头部操作栏 -->
    <el-card class="header-card">
      <div class="header-content">
        <h2>✏️ 编辑行程</h2>
        <div class="actions">
          <el-button @click="goBack">取消</el-button>
          <el-button type="primary" @click="saveAndPreview">保存并预览</el-button>
        </div>
      </div>
    </el-card>

    <!-- 编辑内容 -->
    <el-row :gutter="20" class="edit-content">
      <!-- 左侧：行程列表编辑 -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="section-header">
              <h3>行程安排</h3>
              <el-button type="primary" size="small" @click="addDay">
                <el-icon><Plus /></el-icon>
                添加一天
              </el-button>
            </div>
          </template>

          <!-- 每日行程编辑 -->
          <el-collapse v-model="activeDay" accordion>
            <el-collapse-item
              v-for="(day, dayIndex) in editablePlan.days"
              :key="dayIndex"
              :name="dayIndex"
            >
              <template #title>
                <div class="day-title">
                  <span>第 {{ day.day }} 天 - {{ day.theme }}</span>
                  <el-button
                    type="danger"
                    size="small"
                    text
                    @click.stop="removeDay(dayIndex)"
                    v-if="editablePlan.days.length > 1"
                  >
                    删除
                  </el-button>
                </div>
              </template>

              <!-- 当日主题 -->
              <el-form-item label="当日主题">
                <el-input v-model="day.theme" placeholder="例如：探索古都文化" />
              </el-form-item>

              <!-- 活动列表 -->
              <div class="activities-section">
                <div class="section-title">
                  <h4>活动安排</h4>
                  <el-button size="small" @click="addActivity(dayIndex)">
                    <el-icon><Plus /></el-icon>
                    添加活动
                  </el-button>
                </div>

                <div
                  v-for="(activity, actIndex) in day.activities"
                  :key="actIndex"
                  class="activity-item"
                >
                  <el-card>
                    <el-form label-width="80px" size="small">
                      <el-row :gutter="16">
                        <el-col :span="12">
                          <el-form-item label="活动名称">
                            <el-input v-model="activity.name" />
                          </el-form-item>
                        </el-col>
                        <el-col :span="12">
                          <el-form-item label="时间段">
                            <el-input v-model="activity.time" placeholder="09:00-12:00" />
                          </el-form-item>
                        </el-col>
                      </el-row>

                      <el-row :gutter="16">
                        <el-col :span="12">
                          <el-form-item label="类型">
                            <el-select v-model="activity.type" style="width: 100%">
                              <el-option label="景点" value="attraction" />
                              <el-option label="餐饮" value="dining" />
                              <el-option label="酒店" value="hotel" />
                              <el-option label="交通" value="transport" />
                            </el-select>
                          </el-form-item>
                        </el-col>
                        <el-col :span="12">
                          <el-form-item label="费用">
                            <el-input-number
                              v-model="activity.cost"
                              :min="0"
                              :precision="2"
                              style="width: 100%"
                            />
                          </el-form-item>
                        </el-col>
                      </el-row>

                      <el-form-item label="详细描述">
                        <el-input
                          v-model="activity.details"
                          type="textarea"
                          :rows="2"
                          placeholder="描述活动的详细信息"
                        />
                      </el-form-item>

                      <el-form-item>
                        <el-button
                          type="danger"
                          size="small"
                          @click="removeActivity(dayIndex, actIndex)"
                        >
                          删除此活动
                        </el-button>
                      </el-form-item>
                    </el-form>
                  </el-card>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>
        </el-card>
      </el-col>

      <!-- 右侧：地图预览和酒店 -->
      <el-col :span="8">
        <!-- 地图预览 -->
        <el-card class="preview-card">
          <template #header>
            <h3>🗺️ 路线预览</h3>
          </template>
          <MapView :activities="allActivities" />
        </el-card>

        <!-- 酒店信息编辑 -->
        <el-card class="hotels-edit-card">
          <template #header>
            <div class="section-header">
              <h3>🏨 酒店信息</h3>
              <el-button type="primary" size="small" @click="addHotel">
                <el-icon><Plus /></el-icon>
                添加酒店
              </el-button>
            </div>
          </template>

          <div v-for="(hotel, index) in editablePlan.hotels" :key="index" class="hotel-edit-item">
            <el-form label-width="70px" size="small">
              <el-form-item label="酒店名称">
                <el-input v-model="hotel.name" />
              </el-form-item>
              <el-form-item label="地址">
                <el-input v-model="hotel.address" />
              </el-form-item>
              <el-form-item label="价格/晚">
                <el-input-number
                  v-model="hotel.price"
                  :min="0"
                  style="width: 100%"
                />
              </el-form-item>
              <el-button type="danger" size="small" text @click="removeHotel(index)">
                删除
              </el-button>
            </el-form>
            <el-divider v-if="index < editablePlan.hotels.length - 1" />
          </div>
        </el-card>

        <!-- 预算统计 -->
        <el-card>
          <template #header>
            <h3>💰 预算统计</h3>
          </template>
          <el-statistic title="总预算" :value="totalBudget" prefix="¥" :precision="2" />
        </el-card>
      </el-col>
    </el-row>
  </div>

  <el-empty v-else description="暂无可编辑的行程" />
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import MapView from '@/components/MapView.vue'
import type { TripPlanResponse, DailyPlan, Activity, Hotel } from '@/types'

const router = useRouter()
const editablePlan = ref<TripPlanResponse | null>(null)
const activeDay = ref(0)

// 加载行程数据
onMounted(() => {
  const state = history.state as { tripPlan?: TripPlanResponse }
  if (state?.tripPlan) {
    // 深拷贝避免直接修改原数据
    editablePlan.value = JSON.parse(JSON.stringify(state.tripPlan))
  } else {
    const savedPlan = sessionStorage.getItem('currentTripPlan')
    if (savedPlan) {
      editablePlan.value = JSON.parse(savedPlan)
    }
  }
})

// 获取所有活动
const allActivities = computed(() => {
  if (!editablePlan.value) return []
  return editablePlan.value.days.flatMap(day => day.activities)
})

// 计算总预算
const totalBudget = computed(() => {
  if (!editablePlan.value) return 0
  
  const activityCost = editablePlan.value.days.reduce((sum, day) => {
    return sum + day.activities.reduce((s, act) => s + (act.cost || 0), 0)
  }, 0)
  
  const hotelCost = editablePlan.value.hotels.reduce((sum, hotel) => {
    return sum + (typeof hotel.price === 'number' ? hotel.price : 0)
  }, 0)
  
  return activityCost + hotelCost
})

// 添加一天
const addDay = () => {
  if (!editablePlan.value) return
  
  const newDay: DailyPlan = {
    day: editablePlan.value.days.length + 1,
    theme: '新的一天',
    activities: []
  }
  
  editablePlan.value.days.push(newDay)
  ElMessage.success('已添加新的一天')
}

// 删除一天
const removeDay = (index: number) => {
  if (!editablePlan.value || editablePlan.value.days.length <= 1) return
  
  editablePlan.value.days.splice(index, 1)
  // 重新编号
  editablePlan.value.days.forEach((day, i) => {
    day.day = i + 1
  })
  
  ElMessage.success('已删除该天行程')
}

// 添加活动
const addActivity = (dayIndex: number) => {
  if (!editablePlan.value) return
  
  const newActivity: Activity = {
    time: '09:00-12:00',
    type: 'attraction',
    name: '新活动',
    details: '',
    cost: 0
  }
  
  editablePlan.value.days[dayIndex].activities.push(newActivity)
  ElMessage.success('已添加新活动')
}

// 删除活动
const removeActivity = (dayIndex: number, actIndex: number) => {
  if (!editablePlan.value) return
  
  editablePlan.value.days[dayIndex].activities.splice(actIndex, 1)
  ElMessage.success('已删除该活动')
}

// 添加酒店
const addHotel = () => {
  if (!editablePlan.value) return
  
  const newHotel: Hotel = {
    name: '新酒店',
    address: '',
    price: 0,
    rating: 'N/A'
  }
  
  editablePlan.value.hotels.push(newHotel)
  ElMessage.success('已添加新酒店')
}

// 删除酒店
const removeHotel = (index: number) => {
  if (!editablePlan.value) return
  
  editablePlan.value.hotels.splice(index, 1)
  ElMessage.success('已删除该酒店')
}

// 返回
const goBack = () => {
  router.back()
}

// 保存并预览
const saveAndPreview = () => {
  if (!editablePlan.value) return
  
  // 更新总预算
  editablePlan.value.total_budget = totalBudget.value
  
  // 保存到 sessionStorage
  sessionStorage.setItem('currentTripPlan', JSON.stringify(editablePlan.value))
  
  ElMessage.success('保存成功！')
  
  // 跳转到结果页
  router.push({
    name: 'Result',
    state: { tripPlan: editablePlan.value }
  })
}
</script>

<style scoped lang="scss">
.edit-plan-container {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;

  .header-card {
    margin-bottom: 20px;
    
    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      h2 {
        margin: 0;
        font-size: 24px;
      }
      
      .actions {
        display: flex;
        gap: 12px;
      }
    }
  }

  .edit-content {
    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      h3 {
        margin: 0;
        font-size: 18px;
      }
    }

    .day-title {
      width: 100%;
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-right: 20px;
    }

    .activities-section {
      margin-top: 20px;
      
      .section-title {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        
        h4 {
          margin: 0;
          font-size: 16px;
        }
      }

      .activity-item {
        margin-bottom: 16px;
      }
    }

    .preview-card,
    .hotels-edit-card {
      margin-bottom: 20px;
    }

    .hotel-edit-item {
      margin-bottom: 16px;
    }
  }
}
</style>
