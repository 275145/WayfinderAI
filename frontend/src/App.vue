<template>
  <div id="app">
    <!-- 顶部导航栏 -->
    <header class="app-header">
      <div class="header-content">
        <div class="logo">
          <h1>🌍 智能旅行助手</h1>
        </div>
        <nav class="nav-menu">
          <router-link to="/" class="nav-item">
            <el-icon><House /></el-icon>
            首页
          </router-link>
          <router-link to="/result" class="nav-item" v-if="authStore.isAuthenticated">
            <el-icon><Document /></el-icon>
            我的行程
          </router-link>
        </nav>
        <div class="user-section">
          <UserInfo />
        </div>
      </div>
    </header>
    
    <!-- 主要内容区 -->
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import UserInfo from '@/components/UserInfo.vue'
import { House, Document } from '@element-plus/icons-vue'

const authStore = useAuthStore()

onMounted(() => {
  console.log('智能旅行助手启动成功！')
  console.log('用户认证状态:', authStore.isAuthenticated)
})
</script>

<style lang="scss">
#app {
  width: 100%;
  min-height: 100vh;
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 0 20px;
  position: sticky;
  top: 0;
  z-index: 100;

  .header-content {
    max-width: 1200px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 60px;
  }

  .logo {
    h1 {
      margin: 0;
      font-size: 20px;
      font-weight: 600;
      color: #409eff;
    }
  }

  .nav-menu {
    display: flex;
    gap: 20px;

    .nav-item {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 8px 12px;
      border-radius: 6px;
      color: #606266;
      text-decoration: none;
      transition: all 0.3s;

      &:hover {
        background: #f0f0f0;
        color: #409eff;
      }

      &.router-link-active {
        background: #409eff;
        color: white;
      }
    }
  }

  .user-section {
    display: flex;
    align-items: center;
  }
}

.main-content {
  flex: 1;
  padding: 0;
}

// 过渡动画
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

// 响应式设计
@media (max-width: 768px) {
  .app-header {
    padding: 0 15px;

    .header-content {
      .logo h1 {
        font-size: 18px;
      }

      .nav-menu {
        gap: 15px;

        .nav-item {
          padding: 6px 10px;
          font-size: 14px;
        }
      }
    }
  }
}
</style>

<style lang="scss">
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  width: 100%;
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol',
    'Noto Color Emoji';
}

#app {
  width: 100%;
  min-height: 100vh;
  background: #f5f7fa;
}

// 过渡动画
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

// 滚动条样式
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #555;
}
</style>
