<script lang="ts" setup>
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import LeftSider from "./components/LeftSider.vue";
import RightTop from "./components/RightTop.vue";
import Main from "./components/Main.vue";

import { useGlobalStore } from "@/store/global";
import { useUserStore } from "@/store/user";

import { formatRoutes, getBreadcrumbRoutes, preprocessMenuItem } from "@/utils/router";
import { useTitle } from "@/composables/useTitle";

const route = useRoute();
const globalStore = useGlobalStore();
const userStore = useUserStore();

// 使用动态菜单数据
const routerPathKeyRouter = ref(formatRoutes([]));

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
</script>
<template>
	<div class="member-layout" :class="{ 'light-menu': globalStore.menuStyle === 'light' }">
		<LeftSider
			v-if="globalStore.menuLayout === 'vertical'"
			:menu-data="routerPathKeyRouter.router"
			:route-item="routeItem"
			:user-roles="userStore.roles"
			:collapsed="globalStore.collapsed"
		/>
		<div class="member-layout-right">
			<RightTop
				:menu-data="routerPathKeyRouter.router"
				:route-item="routeItem"
				:path-key-router="routerPathKeyRouter.pathKeyRouter"
				:user-roles="userStore.roles"
				:bread-crumbs="breadCrumbs"
			/>

			<Main :route-item="routeItem" />

			<div v-if="globalStore.isLayoutFooter" class="member-layout-right-footer">Copyright © 2025</div>
		</div>
	</div>
</template>
<style lang="scss">
@import "./css/index.scss";
</style>
