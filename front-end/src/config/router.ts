/**
 * @description: 路由配置入口
 * @author LiQingSong
 */
import NProgress from "nprogress"; // progress bar
import "nprogress/nprogress.css"; // progress bar style
NProgress.configure({ showSpinner: false }); // NProgress Configuration

import { createRouter, createWebHashHistory, RouteRecordRaw } from "vue-router";
import { h } from "vue";
import { RouterView } from "vue-router";

/* SecurityLayout */
import SecurityLayout from "@/layouts/SecurityLayout.vue";

/* MemberLayout */
import MemberLayout from "@/layouts/MemberLayout/index.vue";

/* WriterLayout - 新增writer角色布局 */
import WriterLayout from "@/layouts/WriterLayout/index.vue";

/* UserLayout */
import UserLayout from "@/layouts/UserLayout/index.vue";

/* 请求消除器 */
// import { requestCanceler } from "@/utils/request";
import { getToken } from "@/utils/localToken";
import { getUserMenus } from "@/api/menu";
import { useGlobalStore } from "@/store/global";
import { useUserStore } from "@/store/user";

// 判断是否为writer角色
const checkWriterRole = () => {
	// 如果URL中有forceLogin=admin参数，则强制使用普通登录页
	const urlParams = new URLSearchParams(window.location.search);
	if (urlParams.get("forceLogin") === "admin") {
		return false;
	}

	// 优先从localStorage读取用户角色
	const storedRole = localStorage.getItem("user_role");
	if (storedRole === "writer") {
		return true;
	}

	// 检查URL参数（仅作为备选方案）
	if (urlParams.get("role") === "writer") {
		// 保存用户角色到localStorage
		localStorage.setItem("user_role", "writer");
		return true;
	}

	return false;
};

// 静态路由 - 不需要权限的路由
export const constantRoutes: RouteRecordRaw[] = [
	// UserLayout相关路由
	{
		path: "/user/login",
		name: "login",
		component: UserLayout,
		children: [
			{
				path: "",
				name: "default-login",
				component: () => {
					// 根据URL参数判断用户角色
					if (checkWriterRole()) {
						// 使用默认登录组件
						return import("@/pages/user/login/index.vue");
					} else {
						return import("@/pages/user/login/writer-login.vue");
					}
				},
			},
			// 添加显式的writer登录路由
			{
				path: "writer",
				name: "writer-login",
				component: () => import("@/pages/user/login/writer-login.vue"),
			},
		],
	},
	// 用户详情页路由
	{
		path: "/system/role/detail/:id",
		name: "user-detail",
		component: () => import("@/views/system/role/detail/index.vue"),
		meta: {
			title: "用户详情",
			requiresAuth: true,
		},
	},
	{
		path: "/:pathMatch(.*)*",
		component: () => import("@/pages/404/index.vue"),
	},
];

// 动态路由基础结构 - 不包含实际菜单，菜单将从数据库加载
export const asyncRoutes: RouteRecordRaw[] = [
	// 基础布局结构
	{
		path: "/",
		component: SecurityLayout,
		children: [
			{
				path: "/",
				component: MemberLayout,
				children: [], // 动态加载的菜单将放在这里
			},
		],
	},
];

const router = createRouter({
	scrollBehavior() {
		return { left: 0, top: 0 };
	},
	history: createWebHashHistory(import.meta.env.BASE_URL),
	routes: constantRoutes,
});

// 路由加载状态
let isRoutesLoaded = false;

// 预加载所有可能的组件
// 使用Vite的glob导入功能，这样就不需要硬编码维护组件列表
const viewsModules = import.meta.glob("../views/**/*.vue");
const pagesModules = import.meta.glob("../pages/**/*.vue");

// 仅在开发环境打印一次可用的组件路径，用于调试
let pathsLogged = false;

// 创建一个简单的RouterView组件
const RouterViewComponent = {
	render: () => h(RouterView),
};
// 递归生成路由配置
function generateRoutes(menus: any[]): RouteRecordRaw[] {
	try {
		return menus.map((menu) => {
			// 记录原始字段值用于调试
			const route: any = {
				path: menu.path,
				name: menu.component_name || menu.name,
				meta: {
					title: menu.name, // 确保name字段被转为title
					icon: menu.icon, // 确保icon字段被正确传递
					hidden: !menu.visible, // 根据菜单的visible属性设置是否隐藏
					keepAlive: menu.keep_alive,
					permissions: menu.permission ? [menu.permission] : undefined,
				},
			};
			// 设置重定向属性（如果有）
			if (menu.redirect) {
				route.redirect = menu.redirect;
			}

			// 处理组件
			if (menu.component) {
				// 如果是布局组件
				if (menu.component === "Layout") {
					// 对于布局组件，我们只在第一级菜单使用MemberLayout
					// 对于子菜单的Layout组件，我们使用一个简单的包装组件
					if (menu.type === 0) {
						// 目录类型
						// 使用RouterView组件作为包装
						route.component = () => Promise.resolve(RouterViewComponent);
					} else {
						route.component = () => Promise.resolve(MemberLayout);
					}
				} else {
					// 动态导入组件
					try {
						route.component = dynamicImport(menu.component);
					} catch (error) {
						console.error(`组件导入失败: ${menu.component}`, error);
						// 使用RouterView作为备用，避免整个路由加载失败
						route.component = () => Promise.resolve(RouterViewComponent);
					}
				}
			}

			// 处理子路由
			if (menu.children && menu.children.length > 0) {
				// 过滤掉按钮类型的菜单
				const childMenus = menu.children.filter((child: any) => child.type !== 2);
				if (childMenus.length > 0) {
					try {
						route.children = generateRoutes(childMenus);
					} catch (error) {
						console.error(`生成子路由失败: ${menu.name}`, error);
						route.children = []; // 提供空子路由作为备用
					}
				}
			}

			console.log("generateRoutes - generated route:", JSON.stringify(route.meta, null, 2));
			return route as RouteRecordRaw;
		});
	} catch (error) {
		console.error("生成路由配置失败:", error);
		// 返回一个简单的路由作为备用，避免整个路由加载失败
		return [
			{
				path: "/home",
				name: "首页",
				component: MemberLayout,
				meta: {
					title: "首页",
					icon: "home",
				},
			},
		];
	}
}

// 动态导入组件函数
function dynamicImport(componentPath: string) {
	// 获取用户角色
	const userStore = useUserStore();
	const roles = userStore.roles || [];
	// 检查是否有writer角色
	const isWriter = roles.some((role: any) => role.code === "writer");

	// 首次调用时，打印所有可用路径（仅开发环境）
	if (!pathsLogged && import.meta.env.DEV) {
		pathsLogged = true;
	}

	// 处理布局组件
	if (componentPath === "Layout") {
		// 根据角色使用不同的布局组件
		return isWriter ? () => Promise.resolve(WriterLayout) : () => Promise.resolve(MemberLayout);
	}

	// 标准化路径格式
	let path = componentPath;

	// 获取去除@/前缀后的路径
	// 例如 "@/views/system/user/index.vue" -> "views/system/user/index.vue"
	const normalizedPath = path.startsWith("@/") ? path.slice(2) : path;

	// 构建各种可能的路径格式，根据角色优先级排序
	const possiblePaths = [
		// 首先尝试原始路径
		componentPath,
	];

	// 根据角色添加可能的路径
	if (isWriter) {
		// writer角色：优先查找pages目录
		possiblePaths.push(
			`../pages/${normalizedPath}`,
			`../pages/${normalizedPath}.vue`,
			`../pages/${normalizedPath}/index.vue`,
			// 备用路径
			`../views/${normalizedPath}`,
			`../views/${normalizedPath}.vue`,
			`../views/${normalizedPath}/index.vue`,
		);
	} else {
		// admin角色：优先查找views目录
		possiblePaths.push(
			`../views/${normalizedPath}`,
			`../views/${normalizedPath}.vue`,
			`../views/${normalizedPath}/index.vue`,
			// 备用路径
			`../pages/${normalizedPath}`,
			`../pages/${normalizedPath}.vue`,
			`../pages/${normalizedPath}/index.vue`,
		);
	}

	// 尝试从每个可能的路径找到组件
	for (const possiblePath of possiblePaths) {
		if (viewsModules[possiblePath]) {
			console.log(`从views目录加载组件: ${possiblePath}`);
			return viewsModules[possiblePath];
		}
		if (pagesModules[possiblePath]) {
			console.log(`从pages目录加载组件: ${possiblePath}`);
			return pagesModules[possiblePath];
		}
	}

	// 使用映射表导入常见组件，避免动态导入失败
	const commonComponentsMap: Record<string, any> = {
		"@/pages/home/index.vue": () => import("../pages/home/index.vue"),
		"@/views/chat/list/index.vue": () => import("../views/chat/list/index.vue"),
		"@/views/chat/detail/index.vue": () => import("../views/chat/detail/index.vue"),
		"@/views/system/user/index.vue": () => import("../views/system/user/index.vue"),
		"@/views/system/role/index.vue": () => import("../views/system/role/index.vue"),
		"@/views/system/menu/index.vue": () => import("../views/system/menu/index.vue"),
		"@/views/system/config/index.vue": () => import("../views/system/config/index.vue"),
		"@/views/role/list/index.vue": () => import("../views/role/list/index.vue"),
		"@/views/role/detail/index.vue": () => import("../views/role/detail/index.vue"),
		"@/views/world/list/index.vue": () => import("../views/world/list/index.vue"),
		"@/views/world/detail/index.vue": () => import("../views/world/detail/index.vue"),
		"@/views/prompt/list.vue": () => import("../views/prompt/list.vue"),
		"@/views/prompt/edit.vue": () => import("../views/prompt/edit.vue"),
		"@/views/llm/list/index.vue": () => import("../views/llm/list/index.vue"),
		"@/views/llm/edit/index.vue": () => import("../views/llm/edit/index.vue"),
		"@/views/rag-chat/list/index.vue": () => import("../views/rag-chat/list/index.vue"),
		"@/views/rag-chat/chat/index.vue": () => import("../views/rag-chat/chat/index.vue"),
		"@/views/user-detail/index.vue": () => import("../views/user-detail/index.vue"),
		"@/views/point-record/index.vue": () => import("../views/point-record/index.vue"),
		"@views/dataset/list/index.vue": () => import("../views/datasets/list/index.vue"),
		"@views/system/audio-timbre": () => import("../views/system/audio-timbre/index.vue"),
		"@views/chat/scenarios": () => import("../views/chat/scenarios/index.vue"),
		"@views/chat/setup": () => import("../views/chat/setup/index.vue"),
		"@views/chat/story": () => import("../views/chat/story/index.vue"),
		"@views/chat/tasks/TaskList.vue": () => import("../views/chat/tasks/TaskList.vue"),
		"@views/chat/tasks/TaskDetail.vue": () => import("../views/chat/tasks/TaskDetail.vue"),
		"@views/chat/tasks/TaskChat.vue": () => import("../views/chat/tasks/TaskChat.vue"),
		"@views/datasets/detail/index.vue": () => import("../views/datasets/detail/index.vue"),
		"@views/gamePlayType/GamePlayTypeList.vue": () => import("../views/gamePlayType/GamePlayTypeList.vue"),
		"@views/gamePlayType/GamePlayTypeDetail.vue": () => import("../views/gamePlayType/GamePlayTypeDetail.vue"),
		"@views/llm/model-config/index.vue": () => import("../views/llm/model-config/index.vue"),
		"@views/system/llm-usage-records/index.vue": () => import("../views/system/llm-usage-records/index.vue"),
		"@views/role/role-subtasks/index.vue": () => import("../views/role/role-subtasks/index.vue"),
		"@views/task/task-manage/index.vue": () => import("../views/task/task-manage/index.vue"),
		"@views/task-game-messages/index.vue": () => import("../views/task-game-messages/index.vue"),
		"@views/task-game-messages/detail.vue": () => import("../views/task-game-messages/detail.vue"),
		"@views/memory/index.vue": () => import("../views/memory/index.vue"),
		// 卡片管理模块路由
		"@/views/card-series/index.vue": () => import("../views/card-series/index.vue"),
		"@/views/card-series/cards.vue": () => import("../views/card-series/cards.vue"),
		"@views/card-series/index.vue": () => import("../views/card-series/index.vue"),
		"@views/card-series/cards.vue": () => import("../views/card-series/cards.vue"),
		// 盲盒管理模块路由
		"@/views/blind-box/index.vue": () => import("../views/blind-box/index.vue"),
		"@views/blind-box/index.vue": () => import("../views/blind-box/index.vue"),
		"@/views/system/role/detail/index.vue": () => import("../views/system/role/detail/index.vue"),
	};

	// 为writer角色添加页面映射
	const writerComponentsMap: Record<string, any> = {
		"@/views/role/list/index.vue": () => import("../pages/role/list/index.vue"),
		"@/views/role/detail/index.vue": () => import("../pages/role/detail/index.vue"),
		"@/views/world/list/index.vue": () => import("../pages/world/list/index.vue"),
		"@/views/world/detail/index.vue": () => import("../pages/world/detail/index.vue"),
		"@/views/prompt/list.vue": () => import("../pages/prompt/list.vue"),
		"@/views/prompt/edit.vue": () => import("../pages/prompt/edit.vue"),
		"@/views/gamePlayType/GamePlayTypeList.vue": () => import("../pages/gamePlayType/GamePlayTypeList.vue"),
		"@/views/gamePlayType/GamePlayTypeDetail.vue": () => import("../pages/gamePlayType/GamePlayTypeDetail.vue"),
		"empty": () => import("../pages/empty/index.vue"),
		"@/views/touchflow/index.vue": () => import("../views/touchflow/index.vue"),
		"@views/touchflow/index.vue": () => import("../views/touchflow/index.vue"),
	};

	// 根据角色选择映射表
	const roleComponentsMap = isWriter ? writerComponentsMap : {};

	// 首先检查角色特定的映射
	if (isWriter && roleComponentsMap[componentPath]) {
		console.log(`使用writer角色特定映射导入组件: ${componentPath}`);
		return roleComponentsMap[componentPath];
	}

	// 然后检查通用映射
	if (commonComponentsMap[componentPath]) {
		console.log(`使用通用映射导入组件: ${componentPath}`);
		return commonComponentsMap[componentPath];
	}

	// 修正特定的路径映射错误
	const pathCorrections: Record<string, any> = {
		"/chat/tasks/create": () => import("../views/chat/tasks/TaskDetail.vue"),
		"/chat/tasks/edit": () => import("../views/chat/tasks/TaskDetail.vue"),
		"/chat/tasks/test": () => import("../views/chat/tasks/TaskChat.vue"),
	};

	// 检查是否有路径需要修正
	for (const [pattern, component] of Object.entries(pathCorrections)) {
		if (componentPath.includes(pattern)) {
			console.log(`使用路径修正导入组件: ${componentPath} -> ${pattern}`);
			return component;
		}
	}

	// 记录错误并返回空组件
	console.error(`找不到组件: ${componentPath}，尝试过以下路径:`, possiblePaths);
	// 返回一个简单的渲染函数作为备用，确保返回一个Promise
	return () =>
		import("../components/EmptyComponent.vue").catch(() => {
			console.error("加载备用组件失败，使用渲染函数");
			return Promise.resolve({
				render: () => h("div", { style: "padding: 20px; color: red;" }, [`组件 "${componentPath}" 加载失败`]),
			});
		});
}

// 加载动态路由
async function loadAsyncRoutes() {
	// 获取全局状态
	const userStore = useUserStore();
	await userStore.getInfo();
	const globalStore = useGlobalStore();
	const roles: any = userStore.roles;

	// 确定用户角色 - 优先检查localStorage中的角色标记
	let user_role = "admin";

	// 检查localStorage中是否有writer角色标记
	if (localStorage.getItem("user_role") === "writer") {
		user_role = "writer";
	}
	// 如果localStorage中没有角色标记，则检查API返回的角色信息
	else {
		for (const role of roles) {
			if (role.code === "writer") {
				user_role = "writer";
				// 将角色信息保存到localStorage，保持一致性
				localStorage.setItem("user_role", "writer");
				break;
			}
		}
	}

	console.log("当前用户角色:", user_role);

	try {
		// 获取用户菜单权限
		const menus = await getUserMenus();
		console.log("原始菜单数据:", menus);

		// 添加首页重定向
		let hasHomeRoute = false;

		// 查找是否有首页路由
		for (const menu of menus) {
			if (menu.path === "/home") {
				hasHomeRoute = true;
				break;
			}

			// 检查子菜单
			if (menu.children && Array.isArray(menu.children)) {
				for (const child of menu.children) {
					if (child.path === "/home") {
						hasHomeRoute = true;
						break;
					}
				}
				if (hasHomeRoute) break;
			}
		}

		// 如果没有找到首页，添加一个默认的首页路由到菜单中
		if (!hasHomeRoute) {
			menus.unshift({
				path: "/home",
				name: "首页",
				component: "@/pages/home/index.vue",
				type: 1,
				visible: true,
				icon: "home",
				keep_alive: true,
			});
		}

		// 处理菜单数据，确保每个菜单项都有所需的所有属性
		const processedMenus = menus.map((item) => {
			// 确保icon字段存在
			if (!item.icon || item.icon === "#") {
				if (item.type === 0) {
					item.icon = "folder";
				} else if (item.type === 1) {
					item.icon = "document";
				} else {
					item.icon = "button";
				}
			}

			// 处理子菜单
			if (item.children && item.children.length > 0) {
				item.children = item.children.map((child) => {
					if (!child.icon || child.icon === "#") {
						if (child.type === 0) {
							child.icon = "folder";
						} else if (child.type === 1) {
							child.icon = "document";
						} else {
							child.icon = "button";
						}
					}
					return child;
				});
			}

			return item;
		});

		// 保存动态菜单到全局状态
		globalStore.setDynamicMenus(processedMenus);

		// 为根路由添加重定向到首页
		if (asyncRoutes[0] && asyncRoutes[0].children && asyncRoutes[0].children[0]) {
			asyncRoutes[0].children[0].redirect = "/home";

			// 根据用户角色设置不同的布局组件
			if (user_role === "writer") {
				asyncRoutes[0].children[0].component = WriterLayout;
			}
		}

		// 生成路由配置
		const dynamicRoutes = generateRoutes(processedMenus);

		// 将动态路由添加到应用根路由下
		if (asyncRoutes[0] && asyncRoutes[0].children && asyncRoutes[0].children[0]) {
			asyncRoutes[0].children[0].children = dynamicRoutes;
		}

		// 添加到路由器中
		asyncRoutes.forEach((route) => {
			router.addRoute(route);
		});

		// 标记路由已加载
		isRoutesLoaded = true;
		globalStore.setDynamicRoutesLoaded(true);

		return Promise.resolve(dynamicRoutes);
	} catch (error) {
		console.error("加载动态路由失败:", error);

		// 出错时添加默认首页路由
		const defaultRoute = {
			path: "/user/login",
			name: "login",
			component: () => import("../pages/user/login/index.vue"),
			meta: {
				title: "首页",
				icon: "home",
			},
		};
		// 添加到路由器中
		asyncRoutes.forEach((route) => {
			router.addRoute(route);
		});

		// 标记路由已加载
		isRoutesLoaded = true;

		// 设置默认菜单
		globalStore.setDynamicMenus([
			{
				path: "/login",
				name: "首页",
				component: "@/pages/home/index.vue",
				type: 1,
				visible: true,
				icon: "home",
				keep_alive: true,
			},
		]);
		globalStore.setDynamicRoutesLoaded(true);
		// 安全地设置重定向和子路由
		if (asyncRoutes[0] && asyncRoutes[0].children && asyncRoutes[0].children[0]) {
			asyncRoutes[0].children[0].redirect = "login";
			asyncRoutes[0].children[0].children = [defaultRoute];
		}
		return Promise.resolve([defaultRoute]);
	}
}

/**
 * @description 路由前置，拦截
 */
router.beforeEach(async (to, from, next) => {
	// start progress bar
	NProgress.start();

	// 在跳转之前，清除所有ajax请求
	// requestCanceler.removeAllPending();

	// 判断是否有token
	const hasToken = getToken().replace("Bearer ", "").replace("null", "");

	// 检查是否为writer角色，从URL参数或已验证的用户信息获取
	const isWriter = to.query.role === "writer" || checkWriterRole();

	// 检查是否是登录路径
	const isLoginPath = to.path === "/user/login" || to.path === "/user/login/writer";

	// 提取有效的redirect参数，避免重复嵌套
	const extractValidRedirect = (query: any) => {
		if (!query || !query.redirect) return undefined;

		// 提取redirect参数
		let redirectPath = query.redirect as string;

		// 如果redirect中还包含redirect参数，提取最终目标路径
		if (redirectPath.includes("redirect=")) {
			try {
				// 尝试从URL中提取最深层的redirect
				const url = new URL(redirectPath, window.location.origin);
				while (url.searchParams.has("redirect")) {
					const nextRedirect = url.searchParams.get("redirect");
					if (!nextRedirect) break;

					// 创建新的URL对象解析下一层redirect
					try {
						const nextUrl = new URL(nextRedirect, window.location.origin);
						url.searchParams.delete("redirect");

						// 将非redirect参数合并到URL中
						nextUrl.searchParams.forEach((value, key) => {
							if (key !== "redirect") {
								url.searchParams.set(key, value);
							}
						});

						// 如果有更深层的redirect，继续迭代
						if (nextUrl.searchParams.has("redirect")) {
							url.searchParams.set("redirect", nextUrl.searchParams.get("redirect")!);
						}

						redirectPath = nextUrl.pathname + nextUrl.search;
					} catch {
						break;
					}
				}

				// 返回清理后的路径
				redirectPath = url.pathname + url.search;
			} catch {
				// 如果解析失败，尝试简单提取路径部分
				redirectPath = redirectPath.split("?")[0];
			}
		}

		// 确保不重定向到登录页面
		if (redirectPath.includes("/user/login")) {
			return "/";
		}

		return redirectPath;
	};

	// 没有登录，且访问的不是登录相关页面，跳转到登录页
	if (!hasToken && !isLoginPath) {
		// 根据角色参数确定登录页
		const loginPath = isWriter ? "/user/login/writer" : "/user/login";

		// 获取清理后的redirect参数
		const redirect = extractValidRedirect(to.query) || to.fullPath;

		// 构建跳转URL，避免嵌套redirect
		next({
			path: loginPath,
			query: {
				...to.query,
				redirect: redirect !== loginPath ? redirect : undefined,
			},
		});
		NProgress.done();
		return;
	}

	// 已登录且访问登录页，跳转到首页
	if (hasToken && isLoginPath) {
		// 获取清理后的redirect参数
		const redirect = extractValidRedirect(to.query);
		if (redirect) {
			next(redirect);
		} else {
			next("/");
		}
		NProgress.done();
		return;
	}

	// 已登录但路由未加载，加载动态路由
	if (hasToken && !isRoutesLoaded) {
		try {
			await loadAsyncRoutes();
			// 重新导航到目标路由，让路由识别新添加的路由
			next({ ...to, replace: true });
		} catch (error) {
			console.error("加载路由失败:", error);
			// 根据角色确定登录页
			const loginPath = isWriter ? "/user/login/writer" : "/user/login";
			next(loginPath);
			NProgress.done();
		}
		return;
	}

	// 正常跳转
	next();
});

/**
 * @description 路由后置，跳转结束
 */
router.afterEach(() => {
	// finish progress bar
	NProgress.done();
});

export default router;
