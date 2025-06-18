/**
 * WriterLayout 路由
 */
import { RouteRecordRaw } from "vue-router";

const WriterLayoutRoutes: RouteRecordRaw[] = [
	{
		path: "/home",
		name: "home",
		component: () => import("@/pages/home/index.vue"),
		meta: {
			title: "首页",
			icon: "home",
		},
	},
];

export default WriterLayoutRoutes;
