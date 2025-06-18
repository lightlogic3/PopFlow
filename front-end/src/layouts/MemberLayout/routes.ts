import { RouteRecordRaw } from "vue-router";
import { homePath } from "@/config/settings";

const MemberLayoutRoutes: RouteRecordRaw[] = [
	{
		meta: {
			title: "member-layout.menu.home",
			icon: "menu-home",
		},
		path: homePath,
		component: () => import("@/pages/home/index.vue"),
	},
	{
		meta: {
			title: "知识库管理",
			icon: "menu-permission",
		},
		path: "/role",
		children: [
			{
				meta: {
					title: "角色管理",
					isKeepAlive: true,
					icon: "menu-home",
				},
				path: "list",
				component: () => import("@/views/role/list/index.vue"),
			},
			{
				meta: {
					title: "角色详情",
					isKeepAlive: true,
					hidden: true, // 在菜单中隐藏此路由
				},
				path: "detail/:id",
				component: () => import("@/views/role/detail/index.vue"),
			},
			{
				path: "/world/list",
				name: "WorldList",
				component: () => import("@/views/world/list/index.vue"),
				meta: {
					title: "世界观列表",
					icon: "menu-home",
				},
			},
			{
				path: "/world/detail/:id",
				name: "WorldDetail",
				component: () => import("@/views/world/detail/index.vue"),
				meta: {
					title: "世界观详情",
					hidden: true,
				},
			},

			{
				path: "/prompt/list",
				component: () => import("@/views/prompt/list.vue"),
				meta: {
					title: "提示词模板",
					keepAlive: true,
					icon: "menu-home",
				},
			},
			{
				path: "/prompt/edit/:id?",
				component: () => import("@/views/prompt/edit.vue"),
				meta: {
					title: "编辑提示词",
					keepAlive: true,
					hidden: true,
				},
			},
		],
	},
	{
		meta: {
			title: "系统管理",
			icon: "set",
		},
		path: "/system",
		children: [
			{
				meta: {
					title: "系统配置",
					isKeepAlive: true,
					icon: "set",
				},
				path: "config",
				component: () => import("@/views/system/config/index.vue"),
			},
			{
				meta: {
					title: "用户管理",
					isKeepAlive: true,
					icon: "user",
					permissions: ["system:user:list"],
				},
				path: "user",
				component: () => import("@/views/system/user/index.vue"),
			},
			{
				meta: {
					title: "角色管理",
					isKeepAlive: true,
					icon: "people",
					permissions: ["system:role:list"],
				},
				path: "role",
				component: () => import("@/views/system/role/index.vue"),
			},
			{
				meta: {
					title: "菜单管理",
					isKeepAlive: true,
					icon: "menu",
					permissions: ["system:menu:list"],
				},
				path: "menu",
				component: () => import("@/views/system/menu/index.vue"),
			},
			{
				path: "/llm/list",
				name: "LLMList",
				component: () => import("@/views/llm/list/index.vue"),
				meta: {
					title: "提供商列表",
					icon: "set",
				},
			},
			{
				path: "/llm/edit/:id",
				name: "LLMEdit",
				component: () => import("@/views/llm/edit/index.vue"),
				meta: {
					title: "提供商编辑",
					hidden: true,
				},
			},
			{
				path: "/memory/manager",
				name: "MemoryManager",
				component: () => import("@/views/memory/index.vue"),
				meta: {
					title: "记忆系统管理",
					icon: "data",
					isKeepAlive: true,
				},
			},
		],
	},
	// {
	// 	meta: {
	// 		title: "member-layout.menu.permission",
	// 		icon: "menu-permission",
	// 	},
	// 	path: "/permission",
	// 	children: [
	// 		{
	// 			meta: {
	// 				title: "member-layout.menu.permission.all",
	// 			},
	// 			path: "all",
	// 			component: () => import("@/pages/permission/all/index.vue"),
	// 		},
	// 		{
	// 			meta: {
	// 				title: "member-layout.menu.permission.user",
	// 				roles: ["user"],
	// 			},
	// 			path: "user",
	// 			component: () => import("@/pages/permission/user/index.vue"),
	// 		},
	// 		{
	// 			meta: {
	// 				title: "member-layout.menu.permission.test",
	// 				roles: ["test"],
	// 			},
	// 			path: "test",
	// 			component: () => import("@/pages/permission/test/index.vue"),
	// 		},
	// 	],
	// },
	{
		path: "/chat",
		name: "ChatManagement",
		meta: {
			title: "聊天会话",
			icon: "sun",
		},
		redirect: "/chat/list",
		children: [
			{
				path: "/chat/list",
				name: "ChatList",
				component: () => import("@/views/chat/list/index.vue"),
				meta: {
					title: "会话列表",
					icon: "theme",
				},
			},
			{
				path: "/chat/detail/:id",
				name: "ChatDetail",
				component: () => import("@/views/chat/detail/index.vue"),
				meta: {
					title: "会话详情",
					hidden: true,
				},
			},
			{
				meta: {
					title: "聊天功能",
					isKeepAlive: true,
					icon: "theme",
				},
				path: "/chatList",
				component: () => import("@/views/rag-chat/list/index.vue"),
			},
			{
				meta: {
					title: "聊天对话",
					isKeepAlive: true,
					hidden: true,
				},
				path: "chat",
				component: () => import("@/views/rag-chat/chat/index.vue"),
			},
			{
				path: "/chat/setup",
				name: "CharacterSetup",
				component: () => import("@/views/chat/setup/index.vue"),
				meta: {
					title: "角色设置",
					icon: "user",
				},
			},
			{
				path: "/chat/story",
				name: "InteractiveStory",
				component: () => import("@/views/chat/story/index.vue"),
				meta: {
					title: "互动剧情",
					icon: "star",
				},
			},
			{
				path: "/chat/scenarios",
				name: "ScenarioManagement",
				component: () => import("@/views/chat/scenarios/index.vue"),
				meta: {
					title: "场景管理",
					icon: "set",
				},
			},
		],
	},
];

export default MemberLayoutRoutes;
