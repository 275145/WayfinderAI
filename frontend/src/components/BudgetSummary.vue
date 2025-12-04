<template>
  <div class="budget-summary">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>💰 预算明细</h3>
          <div class="total-budget">
            <span>总预算：</span>
            <span class="amount">¥{{ totalBudget.toFixed(2) }}</span>
          </div>
        </div>
      </template>

      <!-- 预算概览 -->
      <div class="budget-overview">
        <el-row :gutter="16">
          <el-col :span="6" v-for="category in budgetCategories" :key="category.name">
            <div class="category-card">
              <div class="category-icon">{{ category.icon }}</div>
              <div class="category-name">{{ category.name }}</div>
              <div class="category-amount">¥{{ category.amount.toFixed(2) }}</div>
              <div class="category-percent">{{ category.percent }}%</div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 详细列表 -->
      <el-divider />
      
      <div class="budget-details">
        <el-collapse v-model="activeCollapse">
          <el-collapse-item
            v-for="detail in budgetDetails"
            :key="detail.category"
            :name="detail.category"
          >
            <template #title>
              <div class="collapse-title">
                <span class="title-text">{{ detail.category }}</span>
                <span class="title-amount">¥{{ detail.amount.toFixed(2) }}</span>
              </div>
            </template>
            
            <el-table :data="detail.items" :show-header="true" size="small">
              <el-table-column prop="name" label="项目" />
              <el-table-column prop="cost" label="费用" align="right">
                <template #default="scope">
                  ¥{{ scope.row.cost.toFixed(2) }}
                </template>
              </el-table-column>
            </el-table>
          </el-collapse-item>
        </el-collapse>
      </div>

      <!-- 预算建议 -->
      <el-alert
        v-if="budgetTip"
        :title="budgetTip"
        type="info"
        :closable="false"
        class="budget-tip"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { TripPlanResponse, BudgetDetail } from '@/types'

interface Props {
  tripPlan: TripPlanResponse
}

const props = defineProps<Props>()
const activeCollapse = ref<string[]>([])

// 计算总预算
const totalBudget = computed(() => props.tripPlan.total_budget || 0)

// 计算各类别预算
const budgetDetails = computed((): BudgetDetail[] => {
  const details: BudgetDetail[] = []
  
  // 1. 景点门票费用
  const attractionCost = props.tripPlan.days.reduce((sum, day) => {
    return sum + day.activities
      .filter(act => act.type === 'attraction')
      .reduce((s, act) => s + (act.cost || 0), 0)
  }, 0)
  
  if (attractionCost > 0) {
    const attractionItems = props.tripPlan.days.flatMap(day =>
      day.activities
        .filter(act => act.type === 'attraction' && act.cost > 0)
        .map(act => ({ name: act.name, cost: act.cost }))
    )
    details.push({
      category: '景点门票',
      amount: attractionCost,
      items: attractionItems
    })
  }
  
  // 2. 餐饮费用
  const diningCost = props.tripPlan.days.reduce((sum, day) => {
    return sum + day.activities
      .filter(act => act.type === 'dining')
      .reduce((s, act) => s + (act.cost || 0), 0)
  }, 0)
  
  if (diningCost > 0) {
    const diningItems = props.tripPlan.days.flatMap(day =>
      day.activities
        .filter(act => act.type === 'dining' && act.cost > 0)
        .map(act => ({ name: act.name, cost: act.cost }))
    )
    details.push({
      category: '餐饮美食',
      amount: diningCost,
      items: diningItems
    })
  }
  
  // 3. 酒店住宿费用
  const hotelCost = props.tripPlan.hotels.reduce((sum, hotel) => {
    const price = typeof hotel.price === 'number' ? hotel.price : 0
    return sum + price
  }, 0)
  
  if (hotelCost > 0) {
    const hotelItems = props.tripPlan.hotels
      .filter(h => typeof h.price === 'number' && h.price > 0)
      .map(h => ({ name: h.name, cost: h.price as number }))
    details.push({
      category: '酒店住宿',
      amount: hotelCost,
      items: hotelItems
    })
  }
  
  // 4. 其他费用
  const otherCost = totalBudget.value - attractionCost - diningCost - hotelCost
  if (otherCost > 0) {
    details.push({
      category: '交通及其他',
      amount: otherCost,
      items: [{ name: '预估费用', cost: otherCost }]
    })
  }
  
  return details
})

// 计算预算分类概览
const budgetCategories = computed(() => {
  const categories = [
    { name: '景点', icon: '🎫', key: '景点门票' },
    { name: '餐饮', icon: '🍽️', key: '餐饮美食' },
    { name: '住宿', icon: '🏨', key: '酒店住宿' },
    { name: '其他', icon: '🚗', key: '交通及其他' }
  ]
  
  return categories.map(cat => {
    const detail = budgetDetails.value.find(d => d.category === cat.key)
    const amount = detail?.amount || 0
    const percent = totalBudget.value > 0 
      ? Math.round((amount / totalBudget.value) * 100) 
      : 0
    
    return {
      name: cat.name,
      icon: cat.icon,
      amount,
      percent
    }
  })
})

// 预算建议
const budgetTip = computed(() => {
  if (totalBudget.value < 500) {
    return '💡 经济出行，建议选择公共交通和经济型酒店'
  } else if (totalBudget.value < 2000) {
    return '💡 中等预算，可以体验当地特色美食和舒适住宿'
  } else if (totalBudget.value < 5000) {
    return '💡 宽裕预算，可以享受更好的服务和体验'
  } else {
    return '💡 豪华出行，尽情享受高品质的旅行体验'
  }
})
</script>

<style scoped lang="scss">
.budget-summary {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    h3 {
      margin: 0;
      font-size: 20px;
      color: #303133;
    }

    .total-budget {
      font-size: 14px;
      color: #606266;

      .amount {
        font-size: 24px;
        font-weight: bold;
        color: #f56c6c;
        margin-left: 8px;
      }
    }
  }

  .budget-overview {
    margin: 20px 0;

    .category-card {
      text-align: center;
      padding: 16px;
      background: #f5f7fa;
      border-radius: 8px;
      transition: all 0.3s;

      &:hover {
        background: #ecf5ff;
        transform: translateY(-2px);
      }

      .category-icon {
        font-size: 32px;
        margin-bottom: 8px;
      }

      .category-name {
        font-size: 14px;
        color: #606266;
        margin-bottom: 8px;
      }

      .category-amount {
        font-size: 18px;
        font-weight: bold;
        color: #303133;
        margin-bottom: 4px;
      }

      .category-percent {
        font-size: 12px;
        color: #909399;
      }
    }
  }

  .budget-details {
    .collapse-title {
      width: 100%;
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-right: 20px;

      .title-text {
        font-weight: 500;
      }

      .title-amount {
        font-weight: bold;
        color: #f56c6c;
      }
    }
  }

  .budget-tip {
    margin-top: 20px;
  }
}
</style>
