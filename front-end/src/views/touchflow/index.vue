<script lang="ts">
import { defineComponent, onMounted, ref, computed } from 'vue';

export default defineComponent({
  name: 'TouchFlowView',
  setup() {
    const iframeLoaded = ref(false);
    const loading = ref(true);

    // 生成带有时间戳的URL，防止缓存
    const touchflowUrl = computed(() => {
      const timestamp = new Date().getTime();
      return `http://34.217.22.246:9999/touchflow/html/touchflow-game-interface.html?t=${timestamp}`;
      // return `http://127.0.0.1:9999/touchflow/html/touchflow-game-interface.html?t=${timestamp}`;
    });

    // iframe加载完成后的处理
    const handleIframeLoad = () => {
      iframeLoaded.value = true;
      loading.value = false;

      // 向iframe传递token
      const iframeElement = document.querySelector('.touchflow-iframe') as HTMLIFrameElement;
      if (iframeElement && iframeElement.contentWindow) {
        try {
          const authToken = localStorage.getItem('admin-element-vue-token');
          iframeElement.contentWindow.postMessage({
            type: 'AUTH_TOKEN',
            token: authToken
          }, '*');
        } catch (err) {
          console.error('unableToPassTokenToIframe', err);
        }
      }
    };

    onMounted(() => {
      // 设置超时，如果iframe加载时间过长，也隐藏加载状态
      setTimeout(() => {
        loading.value = false;
      }, 3000);
    });

    return {
      handleIframeLoad,
      loading,
      iframeLoaded,
      touchflowUrl
    };
  }
});
</script>

<template>
  <div class="touchflow-container">
    <!-- 加载状态 -->
    <div class="loading-overlay" v-if="loading">
      <div class="loading-spinner"></div>
      <div class="loading-text">Loading TouchFlow...</div>
    </div>

    <!-- TouchFlow iframe -->
    <iframe
      :src="touchflowUrl"
      @load="handleIframeLoad"
      class="touchflow-iframe"
      frameborder="0"
      allow="fullscreen; scripts"
      allowfullscreen
      referrerpolicy="no-referrer-when-downgrade"
      sandbox="allow-scripts allow-same-origin allow-popups allow-forms allow-downloads allow-top-navigation"
    ></iframe>
<!--    <iframe -->
<!--      src="/touchflow/index.html"-->
<!--      @load="handleIframeLoad"-->
<!--      class="touchflow-iframe"-->
<!--      frameborder="0"-->
<!--      allow="fullscreen"-->
<!--    ></iframe>-->
  </div>
</template>

<style scoped>
.touchflow-container {
  position: relative;
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

.touchflow-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s ease-in-out infinite;
  margin-bottom: 20px;
}

.loading-text {
  color: #fff;
  font-size: 18px;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
