<script lang="ts" setup>
import { ref, defineProps, defineEmits, computed } from "vue";
import { ElIcon, ElDropdown, ElDropdownMenu, ElDropdownItem } from "element-plus";
import { Menu, Plus, ArrowDown } from "@element-plus/icons-vue";
import { useRouter } from "vue-router";
import { useUserStore } from "@/store/user";

interface BreadCrumb {
	path: string;
	title: string;
}

interface MenuItem {
	path: string;
	name?: string;
	meta?: {
		title?: string;
		icon?: string;
		hidden?: boolean;
	};
	children?: MenuItem[];
	type?: number;
	visible?: number;
	hidden?: boolean;
}

const props = defineProps({
	routeItem: {
		type: Object,
		default: () => ({}),
	},
	breadCrumbs: {
		type: Array as () => BreadCrumb[],
		default: () => [],
	},
	menuData: {
		type: Array as () => MenuItem[],
		default: () => [],
	},
});

const emit = defineEmits(["toggle-sidebar"]);

const userStore = useUserStore();
const router = useRouter();

// 切换侧边栏
const toggleSidebar = () => {
	emit("toggle-sidebar");
};

// 用户操作下拉菜单
const handleCommand = (command: string) => {
	if (command === "logout") {
		// 清除所有相关的token和用户数据
		userStore.logout();

		// 手动清除admin-element-vue-token缓存
		localStorage.removeItem("admin-element-vue-token");
		localStorage.removeItem("token");
		localStorage.removeItem("user_role");

		// 清除可能存在的其他相关缓存
		sessionStorage.removeItem("user_role");

		console.log("已清除所有登录相关缓存");

		// 跳转到writer登录页
		router.push("/user/login/writer");
	} else if (command === "profile") {
		// 跳转到个人资料页
		router.push("/profile");
	}
};

// 获取用户名首字母(用于头像)
const getUserInitial = () => {
	const userName = userStore.name || "User";
	return userName.charAt(0).toUpperCase();
};

// 当前时间
const currentTime = ref(new Date());
const formattedDate = ref(formatDateTime(currentTime.value));

// 格式化日期时间
function formatDateTime(date: Date) {
	const hours = date.getHours();
	const minutes = date.getMinutes();
	const ampm = hours >= 12 ? "PM" : "AM";
	const formattedHours = hours % 12 || 12;
	const formattedMinutes = minutes < 10 ? `0${minutes}` : minutes;

	const days = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];
	const dayOfWeek = days[date.getDay()];

	return {
		time: `${formattedHours}:${formattedMinutes} ${ampm}`,
		date: `${date.getFullYear()}-${date.getMonth() + 1}-${date.getDate()}`,
		day: dayOfWeek,
	};
}

// 更新时间
setInterval(() => {
	currentTime.value = new Date();
	formattedDate.value = formatDateTime(currentTime.value);
}, 60000);

// 获取当前活动的一级菜单
const activeTopLevelMenu = computed(() => {
	const currentPath = router.currentRoute.value.path;
	return props.menuData.find((item: MenuItem) => {
		// 直接匹配
		if (currentPath === item.path) {
			return true;
		}

		// 是否为当前路径的父路径
		if (currentPath.startsWith(item.path + "/")) {
			return true;
		}

		// 检查子菜单
		if (item.children && item.children.length > 0) {
			return item.children.some((child) => {
				return currentPath === child.path || currentPath.startsWith(child.path + "/");
			});
		}

		return false;
	});
});

// 获取当前活动菜单的可用子菜单
const activeSubMenus = computed(() => {
	if (!activeTopLevelMenu.value || !activeTopLevelMenu.value.children) {
		return [];
	}

	// 过滤出可见的子菜单
	return activeTopLevelMenu.value.children.filter((child) => !child.hidden && child.visible !== 0 && child.type !== 2);
});

// 是否显示子菜单下拉
const shouldShowSubMenu = computed(() => {
	return activeSubMenus.value.length >= 2;
});

// 处理子菜单选择
const handleSubMenuSelect = (path: string) => {
	if (path) {
		router.push(path);
	}
};
</script>

<template>
	<header class="writer-header">
		<div class="writer-header-left">
			<div class="toggle-btn" @click="toggleSidebar">
				<el-icon size="20">
					<Menu />
				</el-icon>
			</div>

			<div class="breadcrumb">
				<template v-for="(item, index) in breadCrumbs" :key="index">
					<template v-if="index !== breadCrumbs.length - 1">
						<router-link :to="item.path">{{ item.title }}</router-link>
						<span class="separator">/</span>
					</template>
					<template v-else>
						<span :class="item.title == 'TouchFlow' ? 'current hidden': 'current'">{{ item.title }}</span>
					</template>
				</template>
			</div>

			<!-- 子菜单下拉框，当有2个以上子菜单时显示 -->
			<!-- <el-dropdown
				v-if="shouldShowSubMenu"
				trigger="click"
				@command="handleSubMenuSelect"
				popper-class="writer-dropdown"
				class="sub-menu-dropdown"
			>
				<div class="submenu-button">
					<span>Submenu</span>
					<el-icon class="arrow-icon">
						<ArrowDown />
					</el-icon>
				</div>
				<template #dropdown>
					<el-dropdown-menu>
						<el-dropdown-item v-for="subMenu in activeSubMenus" :key="subMenu.path" :command="subMenu.path">
							{{ subMenu.meta?.title || subMenu.name }}
						</el-dropdown-item>
					</el-dropdown-menu>
				</template>
			</el-dropdown> -->

			<!-- 保留原action-button作为备用功能 -->
			<!-- <div class="action-button" v-if="!shouldShowSubMenu">
				<el-icon><Plus /></el-icon>
			</div> -->
		</div>

<!--		<div class="writer-header-center">-->
<!--			<div class="date-time">-->
<!--				<div class="time">{{ formattedDate.time }}</div>-->
<!--				<div class="date">{{ formattedDate.date }} · {{ formattedDate.day }}</div>-->
<!--			</div>-->
<!--		</div>-->

		<div class="writer-header-right">
			<el-dropdown trigger="click" @command="handleCommand" popper-class="writer-dropdown">
				<div class="user-info">
					<div class="avatar">{{ getUserInitial() }}</div>
					<div class="name">{{ userStore.name }}</div>
				</div>
				<template #dropdown>
					<el-dropdown-menu>
						<el-dropdown-item command="profile">个人资料</el-dropdown-item>
						<el-dropdown-item command="logout">退出登录</el-dropdown-item>
					</el-dropdown-menu>
				</template>
			</el-dropdown>
		</div>
	</header>
</template>

<style lang="scss" scoped>
.writer-header {
	&-left {
		display: flex;
		align-items: center;

		.toggle-btn {
			margin-right: 16px;
		}

		.action-button {
			display: flex;
			align-items: center;
			justify-content: center;
			width: 32px;
			height: 32px;
			border-radius: 50%;
			background-color: rgba(255, 255, 255, 0.08);
			color: rgba(255, 255, 255, 0.8);
			cursor: pointer;
			margin-left: 20px;

			&:hover {
				background-color: rgba(255, 255, 255, 0.12);
				color: white;
			}
		}

		.sub-menu-dropdown {
			margin-left: 20px;

			.submenu-button {
				display: flex;
				align-items: center;
				padding: 6px 12px;
				border-radius: 12px;
				background-color: rgba(0, 160, 209, 0.15);
				color: #00a0d1;
				cursor: pointer;
				transition: all 0.3s ease;

				span {
					margin-right: 6px;
					font-size: 14px;
				}

				.arrow-icon {
					font-size: 12px;
				}

				&:hover {
					background-color: rgba(0, 160, 209, 0.25);
					transform: translateY(-2px);
					box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
				}
			}
		}
	}
}
</style>

<style lang="scss">
/* 全局样式，不使用scoped，确保能覆盖element-plus的样式 */
.writer-dropdown {
	background-color: #242424 !important; /* 使用!important确保优先级 */
	border-color: rgba(255, 255, 255, 0.1) !important;
	box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4) !important;

	.el-dropdown-menu__item {
		color: rgba(255, 255, 255, 0.8) !important;

		&:hover {
			background-color: rgba(255, 255, 255, 0.08) !important;
			color: #00a0d1 !important;
		}
	}
}

/* 使用更特定的选择器并添加!important */
.el-dropdown-menu.writer-dropdown {
	background-color: #242424 !important;
	border-color: rgba(255, 255, 255, 0.1) !important;
}

/* 针对popper容器的样式 */
.el-popper.is-light.writer-dropdown {
	background-color: #242424 !important;
	border-color: rgba(255, 255, 255, 0.1) !important;

	.el-dropdown-menu {
		background-color: #242424 !important;
	}

	.el-dropdown-menu__item {
		color: rgba(255, 255, 255, 0.8) !important;

		&:hover,
		&:focus {
			background-color: rgba(255, 255, 255, 0.08) !important;
			color: #00a0d1 !important;
		}
	}

	.el-popper__arrow::before {
		background-color: #242424 !important;
		border-color: rgba(255, 255, 255, 0.1) !important;
	}
}

.hidden {
	visibility: hidden;
}
</style>
