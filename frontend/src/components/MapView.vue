<template>
  <div class="map-container">
    <div id="amap-container" ref="mapContainer"></div>
    
    <div class="map-controls">
      <el-button-group>
        <el-button size="small" @click="fitView">
          <el-icon><FullScreen /></el-icon>
          适应视野
        </el-button>
        <el-button size="small" @click="toggleRouteVisible">
          <el-icon><Guide /></el-icon>
          {{ routeVisible ? '隐藏' : '显示' }}路线
        </el-button>
      </el-button-group>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import AMapLoader from '@amap/amap-jsapi-loader'
import { ElMessage } from 'element-plus'
import { FullScreen, Guide } from '@element-plus/icons-vue'
import type { Activity, Location } from '@/types'

// 高德地图 Key - 从环境变量读取
const AMAP_KEY = import.meta.env.VITE_AMAP_KEY || 'YOUR_AMAP_KEY'
const AMAP_SECURITY_CODE = import.meta.env.VITE_AMAP_SECURITY_CODE || ''

interface Props {
  activities?: Activity[]
  center?: Location
}

const props = defineProps<Props>()

const mapContainer = ref<HTMLDivElement>()
const map = ref<any>(null)
const markers = ref<any[]>([])
const polyline = ref<any>(null)
const routeVisible = ref(true)

// 初始化地图
const initMap = async () => {
  try {
    // 设置安全密钥
    if (AMAP_SECURITY_CODE) {
      (window as any)._AMapSecurityConfig = {
        securityJsCode: AMAP_SECURITY_CODE
      }
    }

    const AMap = await AMapLoader.load({
      key: AMAP_KEY,
      version: '2.0',
      plugins: [
        'AMap.Scale', 
        'AMap.ToolBar', 
        'AMap.Marker', 
        'AMap.Polyline', 
        'AMap.InfoWindow',
        'AMap.MarkerCluster' // 添加点聚合插件
      ]
    })

    const centerLng = props.center?.lng
    const centerLat = props.center?.lat
    const isValidCenter = centerLng != null && centerLat != null && !isNaN(Number(centerLng)) && !isNaN(Number(centerLat))

    // 创建地图实例
    map.value = new AMap.Map(mapContainer.value, {
      zoom: 12,
      center: isValidCenter ? [Number(centerLng), Number(centerLat)] : [116.397428, 39.90923],
      viewMode: '2D',
      pitch: 0,
      // 优化地图性能
      resizeEnable: true,
      dragEnable: true,
      zoomEnable: true,
      doubleClickZoom: true,
      scrollWheel: true,
      touchZoom: true,
      // 添加流畅的动画效果
      animateEnable: true,
      jogEnable: true
    })

    // 添加比例尺和工具条
    map.value.addControl(new AMap.Scale())
    map.value.addControl(new AMap.ToolBar())

    // 加载活动标记
    if (props.activities && props.activities.length > 0) {
      await nextTick()
      loadMarkers()
    }
  } catch (error: any) {
    console.error('地图加载失败:', error)
    if (error?.message) {
      ElMessage.error(`地图加载失败: ${error.message}`)
    } else {
      ElMessage.error('地图加载失败，请检查控制台')
    }
  }
}

// 获取活动类型图标
const getActivityIcon = (type: string): string => {
  const iconMap: Record<string, string> = {
    attraction: '🎯',
    dining: '🍽️',
    hotel: '🏨',
    transport: '🚗',
    other: '📍'
  }
  return iconMap[type] || '📍'
}

// 获取活动类型颜色
const getActivityColor = (type: string): string => {
  const colorMap: Record<string, string> = {
    attraction: '#4a90e2',
    dining: '#67c23a',
    hotel: '#f39c12',
    transport: '#95a5a6',
    other: '#909399'
  }
  return colorMap[type] || '#909399'
}

// 加载标记点
const loadMarkers = () => {
  if (!map.value || !props.activities) return

  // 清除旧标记
  clearMarkers()

  const points: [number, number][] = []
  
  props.activities.forEach((activity, index) => {
    if (!activity.location) return

    const { lng, lat } = activity.location
    // 校验经纬度
    if (
      typeof lng !== 'number' ||
      typeof lat !== 'number' ||
      isNaN(lng) ||
      isNaN(lat) ||
      lng < -180 || lng > 180 ||
      lat < -90 || lat > 90
    ) {
      console.warn('跳过无效位置的活动:', activity.name, { lng, lat })
      return
    }

    points.push([lng, lat])

    const activityIcon = getActivityIcon(activity.type)
    const activityColor = getActivityColor(activity.type)

    // 创建自定义HTML标记
    const markerContent = `
      <div class="custom-marker" style="--marker-color: ${activityColor}">
        <div class="marker-icon">${activityIcon}</div>
        <div class="marker-number">${index + 1}</div>
        <div class="marker-pulse"></div>
      </div>
    `

    // 创建标记
    const marker = new (window as any).AMap.Marker({
      position: [lng, lat],
      content: markerContent,
      offset: new (window as any).AMap.Pixel(-20, -40),
      anchor: 'bottom-center'
    })

    // 添加信息窗口
    const infoWindow = new (window as any).AMap.InfoWindow({
      content: `
        <div class="info-window">
          <div class="info-header">
            <span class="info-icon">${activityIcon}</span>
            <h4>${activity.name}</h4>
          </div>
          <div class="info-body">
            <p><span class="info-label">时间:</span> ${activity.time}</p>
            <p><span class="info-label">类型:</span> ${getActivityTypeText(activity.type)}</p>
            ${activity.details ? `<p class="info-details">${activity.details}</p>` : ''}
            ${activity.cost ? `<p class="info-cost"><span class="info-label">费用:</span> <strong>¥${activity.cost}</strong></p>` : ''}
          </div>
        </div>
      `,
      offset: new (window as any).AMap.Pixel(0, -10),
      autoMove: true
    })

    // 添加点击事件
    marker.on('click', () => {
      infoWindow.open(map.value, marker.getPosition())
    })

    // 添加鼠标悬停效果
    marker.on('mouseover', () => {
      marker.setTop(true)
    })

    map.value.add(marker)
    markers.value.push(marker)
  })

  // 绘制路线
  if (points.length > 1 && routeVisible.value) {
    drawRoute(points)
  }

  // 自动调整视野
  if (points.length > 0) {
    fitView()
  }
}

// 绘制路线
const drawRoute = (points: [number, number][]) => {
  if (polyline.value) {
    map.value.remove(polyline.value)
  }

  polyline.value = new (window as any).AMap.Polyline({
    path: points,
    strokeColor: '#4a90e2',
    strokeWeight: 5,
    strokeOpacity: 0.8,
    lineJoin: 'round',
    lineCap: 'round',
    showDir: true,
    dirColor: '#fff',
    // 添加边框使线条更明显
    borderWeight: 1,
    isOutline: true,
    outlineColor: '#fff',
    // 添加渐变效果
    strokeStyle: 'solid'
  })

  map.value.add(polyline.value)
}

// 清除标记
const clearMarkers = () => {
  if (markers.value.length > 0) {
    map.value.remove(markers.value)
    markers.value = []
  }
  if (polyline.value) {
    map.value.remove(polyline.value)
    polyline.value = null
  }
}

// 适应视野
const fitView = () => {
  if (map.value && markers.value.length > 0) {
    map.value.setFitView(markers.value, false, [50, 50, 50, 50], 13)
  }
}

// 监视中心点变化
watch(
  () => props.center,
  (newCenter) => {
    if (map.value && newCenter && newCenter.lng != null && newCenter.lat != null) {
      const centerLng = Number(newCenter.lng)
      const centerLat = Number(newCenter.lat)
      if (!isNaN(centerLng) && !isNaN(centerLat)) {
        map.value.setCenter([centerLng, centerLat])
      }
    }
  },
  { deep: true }
)

// 切换路线显示
const toggleRouteVisible = () => {
  routeVisible.value = !routeVisible.value
  
  if (polyline.value) {
    if (routeVisible.value) {
      polyline.value.show()
    } else {
      polyline.value.hide()
    }
  }
}

// 获取活动类型文本
const getActivityTypeText = (type: string): string => {
  const typeMap: Record<string, string> = {
    attraction: '景点',
    dining: '餐饮',
    hotel: '酒店',
    transport: '交通',
    other: '其他'
  }
  return typeMap[type] || type
}

// 监听活动变化
watch(() => props.activities, () => {
  if (map.value) {
    loadMarkers()
  }
}, { deep: true })

onMounted(() => {
  initMap()
})

defineExpose({
  fitView,
  getMapInstance: () => map.value
})
</script>

<style scoped lang="scss">
.map-container {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 500px;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);

  #amap-container {
    width: 100%;
    flex: 1;
  }

  .map-controls {
    position: absolute;
    top: 16px;
    right: 16px;
    z-index: 10;
  }
}

// 自定义标记样式
:deep(.custom-marker) {
  position: relative;
  width: 40px;
  height: 50px;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    transform: scale(1.15) translateY(-3px);
    filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.3));
  }

  .marker-icon {
    position: absolute;
    top: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 40px;
    height: 40px;
    background: var(--marker-color);
    border-radius: 50% 50% 50% 0;
    transform-origin: bottom left;
    transform: rotate(-45deg) translateX(-50%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.25);
    border: 3px solid #fff;
    
    &::before {
      content: '';
      position: absolute;
      width: 8px;
      height: 8px;
      background: rgba(255, 255, 255, 0.3);
      border-radius: 50%;
      top: 6px;
      right: 6px;
    }
  }

  .marker-number {
    position: absolute;
    top: 8px;
    left: 50%;
    transform: translateX(-50%) rotate(45deg);
    background: #fff;
    color: var(--marker-color);
    width: 20px;
    height: 20px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: bold;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  }

  .marker-pulse {
    position: absolute;
    top: 0;
    left: 50%;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: var(--marker-color);
    opacity: 0;
    transform: translateX(-50%);
    animation: pulse 2s ease-out infinite;
  }
}

@keyframes pulse {
  0% {
    transform: translateX(-50%) scale(0.8);
    opacity: 0.8;
  }
  100% {
    transform: translateX(-50%) scale(2);
    opacity: 0;
  }
}

// 信息窗口样式
:deep(.info-window) {
  padding: 0;
  min-width: 240px;
  max-width: 320px;
  border-radius: 8px;
  overflow: hidden;

  .info-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 16px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;

    .info-icon {
      font-size: 24px;
    }

    h4 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      flex: 1;
    }
  }

  .info-body {
    padding: 12px 16px;

    p {
      margin: 6px 0;
      font-size: 13px;
      color: #606266;
      line-height: 1.6;

      &:first-child {
        margin-top: 0;
      }

      &:last-child {
        margin-bottom: 0;
      }
    }

    .info-label {
      color: #909399;
      font-weight: 500;
      margin-right: 4px;
    }

    .info-details {
      padding: 8px;
      background: #f5f7fa;
      border-radius: 4px;
      margin: 8px 0;
      font-size: 12px;
    }

    .info-cost {
      strong {
        color: #f56c6c;
        font-size: 16px;
      }
    }
  }
}

// 高德地图信息窗口自定义样式
:deep(.amap-info-content) {
  padding: 0;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

:deep(.amap-info-sharp) {
  border-top-color: #667eea;
}
</style>