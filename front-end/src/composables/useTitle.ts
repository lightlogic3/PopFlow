import { ComputedRef, onMounted, watch } from "vue";
import { RouteRecordRaw } from "vue-router";
import { siteTitle } from "@/config/settings";

/**
 * @description:设置 html Title  composables
 * @param routeItem 当前路由item
 * @author LiQingSong
 */
export const useTitle = (routeItem: ComputedRef<RouteRecordRaw>): void => {
	const setTitle = (): void => {
		document.title = `${siteTitle}`;
	};

	watch(routeItem, () => {
		setTitle();
	});

	onMounted(() => {
		setTitle();
	});
};
