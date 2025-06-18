<script lang="ts" setup>
	import { computed, defineProps, nextTick, onMounted, ref } from "vue";
	import { useRoute, useRouter } from "vue-router";
	import { ElIcon } from "element-plus";
	import * as Icons from "@element-plus/icons-vue";
	import { getRoleList } from "@/api/role";
	import { watch } from 'vue';

	interface MenuItem {
		path : string;
		name ?: string;
		meta ?: {
			title ?: string;
			icon ?: string;
			hidden ?: boolean;
		};
		children ?: MenuItem[];
		type ?: number;
		visible ?: number;
		hidden ?: boolean;
		icon ?: string;
	}

	const props = defineProps({
		menuData: {
			type: Array as () => MenuItem[],
			default: () => [],
		},
		routeItem: {
			type: Object,
			default: () => ({}),
		},
		collapsed: {
			type: Boolean,
			default: false,
		},
	});

	const route = useRoute();
	const router = useRouter();
	const role_list = ref(null)
	const choose_role_idx = ref(-1)
	const current_url = ref('')
	const current_btn_id = ref(-1)

	onMounted(() => {
		nextTick(() => {
			getRoleListFunction()
		})
	})

	// 用于存储每个父菜单选中的子菜单
	const selectedSubMenus = ref<Record<string, string>>({});

	const getRoleListFunction = () => {
		getRoleList({ page: 1, size: 100 }).then((res) => {
			// console.log(JSON.stringify(res.items))
			role_list.value = res.items
		});
	}

	// 动态获取图标组件
	const getIcon = (iconName : string) => {
		if (!iconName) return Icons.Document;
		const icon = (Icons as any)[iconName.charAt(0).toUpperCase() + iconName.slice(1)] || Icons.Document;
		return icon;
	};

	// 过滤顶级菜单项，只显示可见的和非隐藏的
	const visibleTopMenuItems = computed(() => {
		return (props.menuData || []).filter((item : MenuItem) => {
			return !item.hidden && item.visible !== 0;
		});
	});

	// 获取菜单项的第一个可见子菜单
	const getFirstVisibleChild = (menuItem : MenuItem) : MenuItem | null => {
		if (!menuItem.children || menuItem.children.length === 0) {
			return null;
		}

		// 查找第一个可见的子菜单（type=1是菜单，type=0是目录，type=2是按钮）
		const visibleChild = menuItem.children.find((child) => !child.hidden && child.visible !== 0 && child.type !== 2);

		return visibleChild || null;
	};

	// 处理菜单项点击
	const handleMenuClick = (menuItem : MenuItem) => {
		// 如果有子菜单，导航到第一个可见子菜单或保存的子菜单
		if (menuItem.children && menuItem.children.length > 0) {
			// 检查是否有保存的子菜单选择
			const savedSubMenuPath = selectedSubMenus.value[menuItem.path];

			// 如果有保存的有效路径，直接导航到该路径
			if (savedSubMenuPath) {
				// 检查这个保存的路径是否仍然是有效的子菜单
				const isValidSavedPath = menuItem.children.some(
					(child) => child.path === savedSubMenuPath && !child.hidden && child.visible !== 0 && child.type !== 2,
				);

				if (isValidSavedPath) {
					router.push(savedSubMenuPath);
					return;
				}
			}

			// 没有保存的路径或保存的路径无效，找到第一个可见子菜单
			const firstVisibleChild = getFirstVisibleChild(menuItem);

			if (firstVisibleChild) {
				// 保存选择以便下次使用
				selectedSubMenus.value[menuItem.path] = firstVisibleChild.path;
				router.push(firstVisibleChild.path);
			}
		} else {
			// 没有子菜单，直接导航到路径
			router.push(menuItem.path);
		}
	};

	// 判断菜单项是否处于激活状态
	const isActiveItem = (item : MenuItem) : boolean => {
		// 当前路径
		const currentPath = router.currentRoute.value.path;

		// 直接匹配当前路径
		if (currentPath === item.path) {
			return true;
		}

		// 检查是否为当前路径的父路径
		if (currentPath.startsWith(item.path + "/")) {
			return true;
		}

		// 检查子菜单是否匹配当前路径
		if (item.children && item.children.length > 0) {
			return item.children.some((child) => {
				// 直接匹配子菜单路径
				if (currentPath === child.path) {
					// 保存选中的子菜单
					selectedSubMenus.value[item.path] = child.path;
					return true;
				}

				// 检查是否为子菜单路径的子路径
				if (currentPath.startsWith(child.path + "/")) {
					// 保存选中的子菜单
					selectedSubMenus.value[item.path] = child.path;
					return true;
				}

				return false;
			});
		}

		return false;
	};
	const handleNavigateToReplace = (item : any) => {
		if (current_url.value == item.nav_url && !(item.nav_url == 'role/detail')) return
		choose_role_idx.value = -1
		current_btn_id.value = item.btn_id
		if (item.nav_url == 'home') {
			router.replace(`/${item.nav_url}`)
			current_url.value = item.nav_url
		}
		else {
			if (!(item.choose_role_idx == undefined)) choose_role_idx.value = item.choose_role_idx
			// router.replace(`/home`)
			if (item.nav_url == 'role/detail') router.replace(`/${item.nav_url}/${item.role_id}?config_id=${item.id}&role_id=${item.role_id}`);
			else if (item.nav_url == 'role/list') router.replace('/role/list')
			else router.replace(`/${item.nav_url}`)
			current_url.value = item.nav_url
		}
	}
	
	const getBtnActive = (id: number) => {
		return current_btn_id.value == id
	}
</script>

<template>
	<aside class="writer-sidebar" :class="{ expanded: !collapsed }">
		<!-- 使用内联样式强制应用布局 -->
		<div class="writer-sidebar-logo"
			style="height: 60px; margin-bottom: 20px; display: flex; align-items: center; justify-content: center"
			@click="handleNavigateToReplace({nav_url: 'home'})">
			<div class="logo-name" v-if="!collapsed"><img src="../../../assets/images/logo.png" alt="Logo"
					style="max-height: 35px" />PopFlow <br />
				Second Life AI Engine</div>
			<div class="logo-icon" v-else style="
					width: 40px;
					height: 40px;
					border-radius: 10px;
					background: linear-gradient(135deg, #00a0d1, #0080a0);
					display: flex;
					align-items: center;
					justify-content: center;
					color: white;
					font-weight: bold;
					font-size: 20px;
					box-shadow: 0 4px 12px rgba(0, 160, 209, 0.3);
				">
				W
			</div>
		</div>

		<!-- <div class="writer-sidebar-menu"
			style="width: 100%; padding-top: 5px; display: flex; flex-direction: column; align-items: center">
			<div v-for="item in visibleTopMenuItems" :key="item.path" class="menu-item"
				:class="{ active: isActiveItem(item) }" @click="handleMenuClick(item)" style="
					width: 85%;
					height: 50px;
					margin: 6px 0;
					padding: 0 10px;
					display: flex;
					align-items: center;
					cursor: pointer;
					transition: all 0.3s ease;
					border-radius: 12px;
					position: relative;
				" :style="{
					background: isActiveItem(item) ? 'rgba(0, 160, 209, 0.1)' : 'transparent',
					boxShadow: isActiveItem(item) ? '0 4px 12px rgba(0, 160, 209, 0.2)' : 'none',
					color: isActiveItem(item) ? '#00a0d1' : 'rgba(255, 255, 255, 0.8)',
					justifyContent: collapsed ? 'center' : 'flex-start',
					paddingLeft: collapsed ? '10px' : '15px',
				}">
				<el-icon class="icon" style="font-size: 22px">
					<component :is="getIcon(item.meta?.icon || item.icon)" />
				</el-icon>
				<span class="title" :style="{
						display: collapsed ? 'none' : 'block',
						marginLeft: '10px',
						fontSize: '14px',
						fontWeight: '500',
					}">
					{{ item.meta?.title || item.name }}
				</span>

				子菜单指示器
				<span v-if="!collapsed && item.children && item.children.length > 0" style="
						position: absolute;
						right: 12px;
						width: 4px;
						height: 4px;
						border-radius: 50%;
						background-color: #00a0d1;
					"></span>
			</div>
		</div> -->

		<div class="role-list-box">
			<el-button type="primary" @click="handleNavigateToReplace({ nav_url: 'role/list', btn_id: 0 })" class="role-list-head" :style="getBtnActive(0) ? 'background-color: rgba(198, 100, 60, 1); border-color: rgba(198, 100, 60, 1)':''">
				<img src="../../../assets/images/letter/R.png" class="role-list-head-letter" /><span
					class="role-list-head-text" v-show="!collapsed">Role Generator</span>
			</el-button>

			<div class="role-list-panel">
				<div :class="choose_role_idx == idx ? 'role-list-item active': 'role-list-item'"
					v-for="(item, idx) in role_list" :key="idx"
					@click.stop="handleNavigateToReplace({...item, nav_url: 'role/detail', choose_role_idx: idx})">
					<div class="role-list-left"><el-avatar :size="80" :src="item.image_url"
							class="role-list-left-avatar" />
					</div>
					<div class="role-list-right" v-show="!collapsed">{{item.name}}</div>
				</div>
			</div>


			<el-button type="primary" class="role-list-head" @click="handleNavigateToReplace({ nav_url: 'chat/tasks', btn_id: 1})" :style="getBtnActive(1) ? 'background-color: rgba(198, 100, 60, 1); border-color: rgba(198, 100, 60, 1)':''">
				<img src="../../../assets/images/letter/P.png" class="role-list-head-letter" /><span
					class="role-list-head-text" v-show="!collapsed">Play With Them</span>
			</el-button>
			<!-- 			<div class="role-list-panel">
				<div class="role-list-item"  @click="handleNavigateToReplace({ nav_url: 'chat/tasks'})">
					<div class="role-list-left"><el-avatar :size="80" src="src/assets/images/logo.png" class="role-list-left-avatar" />
					</div>
					<div class="role-list-right" v-show="!collapsed">Task</div>
				</div>
			</div> -->


			<el-button type="primary" class="role-list-head point-event-none">
				<img src="../../../assets/images/letter/G.png" class="role-list-head-letter" /><span
					class="role-list-head-text size12" v-show="!collapsed">Gaming Challenge</span>
			</el-button>
			
			<div class="role-list-panel">
				<div class="role-list-item" @click="handleNavigateToReplace({ nav_url: 'touchflow', btn_id: 2})"  :style="getBtnActive(2) ? 'background-color: rgba(77, 102, 225, 1); border-color: rgba(77, 102, 225, 1)':''">
					<div class="role-list-left"><el-avatar :size="80" src="src/assets/images/logo.png"
							class="role-list-left-avatar" />
					</div>
					<div class="role-list-right" v-show="!collapsed">Task Challenge</div>
				</div>
			</div>
			<div class="role-list-panel">
				<div class="role-list-item" @click="handleNavigateToReplace({ nav_url: 'role/task', btn_id: 4})"  :style="getBtnActive(4) ? 'background-color: rgba(77, 102, 225, 1); border-color: rgba(77, 102, 225, 1)':''">
					<div class="role-list-left"><el-avatar :size="80" src="src/assets/images/logo.png"
							class="role-list-left-avatar" />
					</div>
					<div class="role-list-right" v-show="!collapsed">Task Editor</div>
				</div>
			</div>
			
			<el-button type="primary" class="role-list-head"  @click="handleNavigateToReplace({ nav_url: 'world/list', btn_id: 3})" :style="getBtnActive(3) ? 'background-color: rgba(198, 100, 60, 1); border-color: rgba(198, 100, 60, 1)':''">
				<img src="../../../assets/images/letter/W.png" class="role-list-head-letter" /><span
					class="role-list-head-text" v-show="!collapsed">World</span>
			</el-button>

			<!-- <div class="role-list-panel">
				<div class="role-list-item" @click="handleNavigateToReplace({ nav_url: 'world/list'})">
					<div class="role-list-left"><el-avatar :size="80" src="src/assets/images/logo.png"
							class="role-list-left-avatar" />
					</div>
					<div class="role-list-right" v-show="!collapsed">World Book</div>
				</div>
			</div> -->
		</div>
	</aside>
</template>

<style lang="scss" scoped>
	@import '@/layouts/WriterLayout/css/extra.scss';
	// 基础样式
	.writer-sidebar {
		position: fixed;
		top: 0;
		left: 0;
		height: 100vh;
		width: 80px;
		background-color: #222222;
		z-index: 100;
		overflow-y: auto;
		border-radius: 0;
		box-shadow: 0 0 20px rgba(0, 0, 0, 0.3);

		&.expanded {
			width: 200px;
		}

		.writer-sidebar-logo {
			cursor: pointer;
		}

		// 悬停效果
		.menu-item {
			&:hover {
				background-color: rgba(255, 255, 255, 0.08) !important;
				transform: translateY(-2px);
				box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
				color: #1ab6eb !important;
			}

			&:hover .icon {
				transform: scale(1.15);
			}

			&.active .icon {
				transform: scale(1.1);
				animation: pulse 2s infinite;
			}

			&.active::before {
				content: "";
				position: absolute;
				left: -10px;
				top: 12px;
				bottom: 12px;
				width: 3px;
				background-color: #00a0d1;
				border-radius: 0 2px 2px 0;
				box-shadow: 0 0 8px rgba(0, 160, 209, 0.6);
			}
		}

		.logo-name {
			display: flex;
			align-items: flex-end;

			img {
				padding: 0 10px;
			}
		}

		.logo-icon {
			transition: all 0.3s ease;

			&:hover {
				transform: scale(1.05);
				box-shadow: 0 6px 15px rgba(0, 160, 209, 0.4) !important;
			}
		}
	}

	.role-list-box {
		display: flex;
		flex-direction: column;
		align-items: center;
		width: 100%;

		.list-panel-title {
			display: flex;
			align-items: center;
			justify-content: flex-start;
			width: 100%;
			padding: 13px 0 13px 5px;
			font-weight: 800;

			.letter {
				text-transform: uppercase;
				margin-right: 10px;
				width: 25px;
				height: 25px;
				border-radius: 50%;
				background-color: #ff4d47;
				display: flex;
				align-items: center;
				justify-content: center;
			}

			&.grey {
				color: #333333;
				background-color: #dcdcdc;
			}

			&.pointer {
				cursor: pointer;
			}
		}

		.role-list-head {
			background-color: $theme-0;
			border-color: $theme-0;
			margin: 10px 0;
			padding: 0;
			width: 90%;

			.role-list-head-letter {
				width: 30px;
				width: 30px;
			}

			.letter {
				text-transform: uppercase;
				margin-right: 10px;
				width: 25px;
				height: 25px;
				border-radius: 50%;
				background-color: #c8c8c8;
				display: flex;
				align-items: center;
				justify-content: center;
				color: #3e4e94;
				font-weight: 800;
			}

			.role-list-head-text {
				margin-left: 10px;

				&.size8 {
					font-size: 8px;
				}

				&.size10 {
					font-size: 10px;
				}

				&.size12 {
					font-size: 12px;
				}

				&.size14 {
					font-size: 14px;
				}

				&.size18 {
					font-size: 18px;
				}
			}

			&.point-event-none {
				pointer-events: none;
			}
			
			&:hover {
				background-color: $theme-hover-0;
				border-color: $theme-hover-0;
			}
			
			&:active {
				background-color: $theme-hover-0;
				border-color: $theme-hover-0;
			}
		}

		.role-list-panel {
			width: 100%;
			display: flex;
			flex-direction: column;
			align-items: flex-start;

			.role-list-item {
				display: flex;
				align-items: center;
				width: 100%;
				cursor: pointer;

				.role-list-left {
					width: 35px;
					height: 35px;
					padding: 9px 10px;

					.role-list-left-avatar {
						width: 100%;
						height: 100%;
					}
				}

				.role-list-right {}


				&.active {
					background-color: $theme-2;
					border-radius: 0 2px 2px 0;
					box-shadow: 0 0 8px $theme-2;
				}

				&:hover {
					transform: scale(1.05);
					box-shadow: 0 6px 15px rgba(77, 102, 225, 0.4) !important;
				}
			}
		}
	}

	@keyframes pulse {
		0% {
			filter: drop-shadow(0 0 2px rgba(0, 160, 209, 0.4));
		}

		50% {
			filter: drop-shadow(0 0 5px rgba(0, 160, 209, 0.6));
		}

		100% {
			filter: drop-shadow(0 0 2px rgba(0, 160, 209, 0.4));
		}
	}
	
	.theme-0 {
		background-col: $theme-0;
		border-color: $theme-0;
		
		&:hover {
			background: $theme-hover-0;
			border-color: $theme-hover-0;
		}
	}
	
	.theme-1 {
		background: $theme-1;
		border-color: $theme-1;
		
		&:hover {
			background: $theme-hover-1;
			border-color: $theme-hover-1;
		}
	}
	
	.theme-2 {
		background: $theme-2;
		border-color: $theme-2;
		
		&:hover {
			background: $theme-hover-2;
			border-color: $theme-hover-2;
		}
	}
</style>