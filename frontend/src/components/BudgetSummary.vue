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

// 计算总预算（后端已给出拆分字段和 total）
const totalBudget = computed(() => props.tripPlan.total_budget?.total || 0)

// 计算各类别预算（直接使用后端拆分好的字段，并按天拆成明细项）
const budgetDetails = computed((): BudgetDetail[] => {
  const details: BudgetDetail[] = []

  const total = props.tripPlan.total_budget

  // 1. 景点门票费用
  if (total.attraction_ticket_cost > 0) {
    const attractionItems: BudgetDetail['items'] = props.tripPlan.days
      .filter(day => day.budget.attraction_ticket_cost > 0)
      .map(day => ({
        name: `第 ${day.day} 天景点门票`,
        cost: day.budget.attraction_ticket_cost
      }))

    details.push({
      category: '景点门票',
      amount: total.attraction_ticket_cost,
      items: attractionItems.length ? attractionItems : [{ name: '景点门票合计', cost: total.attraction_ticket_cost }]
    })
  }

  // 2. 餐饮费用
  if (total.dining_cost > 0) {
    const diningItems: BudgetDetail['items'] = props.tripPlan.days
      .filter(day => day.budget.dining_cost > 0)
      .map(day => ({
        name: `第 ${day.day} 天餐饮`,
        cost: day.budget.dining_cost
      }))

    details.push({
      category: '餐饮美食',
      amount: total.dining_cost,
      items: diningItems.length ? diningItems : [{ name: '餐饮合计', cost: total.dining_cost }]
    })
  }

  // 3. 酒店住宿费用
  if (total.hotel_cost > 0) {
    const hotelItems: BudgetDetail['items'] = props.tripPlan.days
      .filter(day => day.budget.hotel_cost > 0)
      .map(day => ({
        name: `第 ${day.day} 天酒店`,
        cost: day.budget.hotel_cost
      }))

    details.push({
      category: '酒店住宿',
      amount: total.hotel_cost,
      items: hotelItems.length ? hotelItems : [{ name: '酒店合计', cost: total.hotel_cost }]
    })
  }

  // 4. 交通费用
  if (total.transport_cost > 0) {
    const transportItems: BudgetDetail['items'] = props.tripPlan.days
      .filter(day => day.budget.transport_cost > 0)
      .map(day => ({
        name: `第 ${day.day} 天交通`,
        cost: day.budget.transport_cost
      }))

    details.push({
      category: '交通费用',
      amount: total.transport_cost,
      items: transportItems.length ? transportItems : [{ name: '交通合计', cost: total.transport_cost }]
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
    { name: '交通', icon: '🚗', key: '交通费用' }
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
