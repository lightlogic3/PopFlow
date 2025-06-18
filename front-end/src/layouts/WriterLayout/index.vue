<script lang="ts" setup>
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import Sidebar from "./components/Sidebar.vue";
import Header from "./components/Header.vue";
import Main from "./components/Main.vue";

import { useGlobalStore } from "@/store/global";

import { formatRoutes, getBreadcrumbRoutes, preprocessMenuItem } from "@/utils/router";
import { useTitle } from "@/composables/useTitle";

const route = useRoute();
const globalStore = useGlobalStore();

// 使用动态菜单数据
const routerPathKeyRouter: any = ref(formatRoutes([]));

// 监听动态菜单变化
watch(
	() => globalStore.dynamicMenus,
	(newMenus) => {
		if (newMenus && newMenus.length > 0) {
			// 预处理菜单数据，确保所有必要的字段都存在
			const processedMenus = newMenus.map(preprocessMenuItem);
			routerPathKeyRouter.value = formatRoutes(processedMenus);
		}
	},
	{ immediate: true },
);

// 当前路由 item
const routeItem = computed(() => routerPathKeyRouter.value.pathKeyRouter[route.path]);

// 面包屑导航
const breadCrumbs = computed(() => getBreadcrumbRoutes(route.path, routerPathKeyRouter.value.pathKeyRouter));

// 设置title
useTitle(routeItem);

// 侧边栏折叠状态 - 默认为展开状态，显示文字
const isSidebarCollapsed = ref(false);
const toggleSidebar = () => {
	isSidebarCollapsed.value = !isSidebarCollapsed.value;
};

// 侧边栏宽度
const sidebarWidth = computed(() => {
	return isSidebarCollapsed.value ? "80px" : "200px";
});
</script>

<template>
	<div class="writer-layout">
		<Sidebar :menu-data="routerPathKeyRouter.router" :route-item="routeItem" :collapsed="isSidebarCollapsed" />
		<div class="writer-layout-content" :style="{ marginLeft: sidebarWidth }">
			<Header
				:route-item="routeItem"
				:bread-crumbs="breadCrumbs"
				:menu-data="routerPathKeyRouter.router"
				@toggle-sidebar="toggleSidebar"
			/>
			<Main :route-item="routeItem" />
		</div>
	</div>
</template>

<style lang="scss">
@import "./css/index.scss";

.writer-layout {
	display: flex;
	width: 100%;
	height: 100vh;
	overflow: hidden;
	background-color: #1a1a1a;
	color: #ffffff;
	font-family: "Helvetica Neue", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell,
		"Fira Sans", "Droid Sans", sans-serif;
}

/* 整体内容区 */
.writer-layout-content {
	flex: 1;
	display: flex;
	flex-direction: column;
	overflow: hidden;
	transition: all 0.3s ease;
	background-color: #1a1a1a;
	height: 100vh;
	position: relative;
}

/* 全局过渡效果 */
.fade-enter-active,
.fade-leave-active {
	transition: opacity 0.25s ease;
}
.fade-enter-from,
.fade-leave-to {
	opacity: 0;
}
</style>
