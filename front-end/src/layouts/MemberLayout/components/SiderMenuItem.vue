<script lang="ts" setup>
import { toRefs, computed } from "vue";
import { RouteRecordRaw } from "vue-router";

import { isArray } from "@/utils/is";
import { hasChildRoute, hasPermissionRoles } from "@/utils/router";

import ALink from "@/components/ALink/index.vue";
import Icon from "@/components/IconSvg/index.vue";

import { useI18n } from "@/composables/useI18n";
import locales from "../locales";

interface Props {
	routeItem: RouteRecordRaw;
	userRoles?: string[];
}

const props = withDefaults(defineProps<Props>(), {
	userRoles: () => {
		return [];
	},
});

const { routeItem, userRoles } = toRefs(props);

const t = useI18n(locales);

// Computed property: Determine if the current menu item should be displayed
const shouldShowMenuItem = computed(() => {
	const item = routeItem.value as any;

	// Filter conditions:
	// 1. Menu is not hidden (meta.hidden !== true)
	// 2. Menu has permission
	// 3. Menu visible is 1
	// 4. Menu type is not 2 (button type)
	return (
		!item.meta?.hidden && hasPermissionRoles(userRoles.value, item.meta?.roles) && item.visible === 1 && item.type !== 2
	);
});

// Filter child menus, remove items that should not be displayed
const filteredChildren = computed(() => {
	if (!routeItem.value.children) return [];

	return routeItem.value.children.filter((child: any) => {
		return !child.meta?.hidden && child.visible === 1 && child.type !== 2;
	});
});

// Determine if there are visible child menus
const hasVisibleChildren = computed(() => {
	return filteredChildren.value.length > 0 && hasChildRoute(filteredChildren.value);
});
</script>
<template>
	<template v-if="shouldShowMenuItem">
		<template v-if="routeItem.children && isArray(routeItem.children) && hasVisibleChildren">
			<el-sub-menu :index="routeItem.path" popper-class="member-layout-menu-popper">
				<template #title>
					<Icon v-if="routeItem.meta?.icon" :name="routeItem.meta?.icon" class="icon" />
					<span>{{ t(routeItem.meta?.title || "") }}</span>
				</template>
				<SiderMenuItem
					v-for="item2 in filteredChildren"
					:key="item2.path"
					:route-item="item2"
					:user-roles="userRoles"
				/>
			</el-sub-menu>
		</template>
		<template v-else>
			<ALink :to="routeItem.path">
				<el-menu-item :index="routeItem.path">
					<Icon v-if="routeItem.meta?.icon" :name="routeItem.meta?.icon" class="icon" />
					<template #title>{{ t(routeItem.meta?.title || "") }}</template>
				</el-menu-item>
			</ALink>
		</template>
	</template>
</template>
