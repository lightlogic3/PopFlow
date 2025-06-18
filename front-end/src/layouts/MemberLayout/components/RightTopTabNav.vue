<script lang="ts" setup>
import { computed, nextTick, onBeforeMount, onBeforeUnmount, onMounted, ref, toRefs, watch } from "vue";
import { useRouter, useRoute, RouteRecordRaw } from "vue-router";
import { debounce } from "lodash";
import { IPathKeyRouter } from "@/@types/vue-router";
import { equalTabNavRoute } from "@/utils/router";

import { homePath } from "@/config/settings";

import IconSvg from "@/components/IconSvg/index.vue";

import { useI18n } from "@/composables/useI18n";
import locales from "../locales";

import { useMlRightTopTabNavStore } from "../store/rightTopTabNav";

interface Props {
	routeItem: RouteRecordRaw;
	pathKeyRouter: IPathKeyRouter;
}

const props = withDefaults(defineProps<Props>(), {});

const { routeItem, pathKeyRouter } = toRefs(props);

const t = useI18n(locales);

const router = useRouter();
const route = useRoute();

const mlRightTopTabNavStore = useMlRightTopTabNavStore();
// Initialize default value pathKeyRouter
const setPathKeyRouter = () => {
	mlRightTopTabNavStore.pathKeyRouter = pathKeyRouter.value;
};
watch(pathKeyRouter, () => {
	setPathKeyRouter();
});
onBeforeMount(() => {
	setPathKeyRouter();
});
const tabNavListLen = computed<number>(() => mlRightTopTabNavStore.tabNavList.length);

// tabnav-box - x position value
const translateX = ref<number>(0);
const scrollBox = ref<HTMLDivElement>();
const scrollContent = ref<HTMLDivElement>();
const translateXLeftMaxVal = ref<number>(0);

// tabnav-box - scroll mouse wheel - slide box
const handleScroll = (offset: number): void => {
	const boxWidth = scrollBox.value ? scrollBox.value.clientWidth : 0;
	const contentWidth = scrollContent.value ? scrollContent.value.clientWidth : 0;
	if (offset > 0) {
		translateX.value = Math.min(0, translateX.value + offset);
	} else {
		if (boxWidth < contentWidth) {
			if (translateX.value >= -(contentWidth - boxWidth)) {
				translateX.value = Math.max(translateX.value + offset, boxWidth - contentWidth);
			}
		} else {
			translateX.value = 0;
		}
	}
};

// Mouse scroll event on tabNav
const handleRolling = (e: any) => {
	e.preventDefault();
	const type = e.type;
	let delta = 0;
	if (type === "DOMMouseScroll" || type === "mousewheel") {
		delta = e.wheelDelta ? e.wheelDelta : -(e.detail || 0) * 40;
	}
	handleScroll(delta);
};

// navItem - slide to corresponding position
const moveToView = (index: number): void => {
	const itemDom: any = scrollContent.value?.children[index];
	if (!itemDom) {
		return;
	}
	const boxWidth = scrollBox.value ? scrollBox.value.clientWidth : 0;
	const contentWidth = scrollContent.value ? scrollContent.value.clientWidth : 0;
	const itemOffsetLeft = itemDom.offsetLeft;
	const itemClientWidth = itemDom.clientWidth + 1;
	// console.log("width", boxWidth, contentWidth, itemOffsetLeft, itemClientWidth, translateX.value);

	translateXLeftMaxVal.value = boxWidth - contentWidth; // Set maximum left scroll distance

	if (contentWidth < boxWidth || itemOffsetLeft === 0) {
		// console.log("moveToView 1");
		// All items collection length is less than box width or current is the first item
		translateX.value = 0;
	} else if (itemOffsetLeft < -translateX.value) {
		// console.log("moveToView 2");
		// Tag is on the left side of the visible area
		translateX.value = -itemOffsetLeft;
	} else if (itemOffsetLeft > -translateX.value && itemOffsetLeft + itemClientWidth < -translateX.value + boxWidth) {
		// console.log("moveToView 3");
		// Tag is in the visible area
		translateX.value = Math.min(0, boxWidth - itemClientWidth - itemOffsetLeft);
	} else {
		// console.log("moveToView 4", itemOffsetLeft);
		// Tag is on the right side of the visible area
		translateX.value = -(itemOffsetLeft - (boxWidth - itemClientWidth));
	}
};

// navItem - click to navigate
const clickTabNavItem = (to: any) => {
	router.push(to);
};

// Set tabNav
const setTabNavList = () => {
	const index = mlRightTopTabNavStore.setTabNavList(route, routeItem.value);
	if (typeof index !== "undefined") {
		nextTick(() => {
			moveToView(index || 0);
		});
	}
};

// Close current tabNav
const closeCurrentTabNav = (item: any, index: number): void => {
	if (item.meta.tabNavCloseBefore && typeof item.meta.tabNavCloseBefore === "function") {
		item.meta.tabNavCloseBefore(() => {
			mlRightTopTabNavStore.closeTabNav(item, index, router);
		});
	} else {
		mlRightTopTabNavStore.closeTabNav(item, index, router);
	}
};

// Dropdown menu operations
const handleTabNavDropdown = async (command: string) => {
	switch (command) {
		case "refreshCurrent":
			// Refresh current page
			mlRightTopTabNavStore.refreshCurrentTabNav(router);
			break;
		case "closeOther":
			// Close others
			mlRightTopTabNavStore.closeOtherTabNav(router);
			break;
		case "closeAll":
			// Close all
			mlRightTopTabNavStore.closeAllTabNav(router);
			break;
		case "closeToLeft":
			// Close to the left
			mlRightTopTabNavStore.closeToLRTabNav("left", router);
			break;
		case "closeToRight":
			// Close to the right
			mlRightTopTabNavStore.closeToLRTabNav("right", router);
			break;
		default:
			break;
	}
};

// Watch route and current route's corresponding routeItem
watch([route, routeItem], () => {
	setTabNavList();
});

// Browser resize
const resizeHandler = debounce(() => {
	setTimeout(() => {
		setTabNavList();
	}, 200);
}, 100);
// Initialize
onMounted(() => {
	setTabNavList();

	// Browser resize - add
	window.addEventListener("resize", resizeHandler);
});
// Component unmount preparation
onBeforeUnmount(() => {
	window.removeEventListener("resize", resizeHandler);
});
</script>

<template>
	<div class="member-layout-right-tabnav">
		<div v-if="translateX >= 0" class="member-layout-right-tabnav-icon disabled">
			<IconSvg name="arrow-left" />
		</div>
		<div v-else class="member-layout-right-tabnav-icon" @click="handleScroll(200)">
			<IconSvg name="arrow-left" />
		</div>

		<div
			class="member-layout-right-tabnav-box"
			ref="scrollBox"
			@DOMMouseScroll="handleRolling"
			@mousewheel="handleRolling"
		>
			<div
				class="member-layout-right-tabnav-item-box"
				ref="scrollContent"
				:style="{ transform: `translateX(${translateX}px)` }"
			>
				<template v-for="(item, index) in mlRightTopTabNavStore.tabNavList" :key="`tab-nav-${index}`">
					<div
						v-if="equalTabNavRoute(item, route, route.meta?.tabNavType)"
						class="member-layout-right-tabnav-item active"
					>
						<el-dropdown trigger="contextmenu" @command="handleTabNavDropdown">
							<div class="item-box">
								<span class="text">{{ t(item.meta.title || "") }}</span>
								<span v-if="item.path !== homePath" class="icon" @click.stop="closeCurrentTabNav(item, index)">
									<IconSvg name="close" />
								</span>
							</div>
							<template #dropdown>
								<el-dropdown-menu>
									<el-dropdown-item command="refreshCurrent">Refresh Current Page</el-dropdown-item>
									<el-dropdown-item command="closeToLeft" :disabled="index < 2">Close to Left</el-dropdown-item>
									<el-dropdown-item command="closeToRight" :disabled="index === tabNavListLen - 1">
										Close to Right
									</el-dropdown-item>
									<el-dropdown-item
										command="closeOther"
										:disabled="tabNavListLen === 1 || (tabNavListLen === 2 && item.path !== homePath)"
									>
										Close Others
									</el-dropdown-item>
									<el-dropdown-item command="closeAll" :disabled="tabNavListLen === 1">Close All</el-dropdown-item>
								</el-dropdown-menu>
							</template>
						</el-dropdown>
					</div>
					<div v-else class="member-layout-right-tabnav-item" @click="clickTabNavItem(item)">
						<div class="item-box">
							<span class="text">{{ t(item.meta.title || "") }}</span>
							<span v-if="item.path !== homePath" class="icon" @click.stop="closeCurrentTabNav(item, index)">
								<IconSvg name="close" />
							</span>
						</div>
					</div>
				</template>
			</div>
		</div>
		<div v-if="translateXLeftMaxVal >= translateX" class="member-layout-right-tabnav-icon disabled">
			<IconSvg name="arrow-right" />
		</div>
		<div v-else class="member-layout-right-tabnav-icon" @click="handleScroll(-200)">
			<IconSvg name="arrow-right" />
		</div>
		<el-dropdown @command="handleTabNavDropdown">
			<div class="member-layout-right-tabnav-icon">
				<IconSvg name="more" />
			</div>
			<template #dropdown>
				<el-dropdown-menu>
					<el-dropdown-item command="refreshCurrent">Refresh Current Page</el-dropdown-item>
					<el-dropdown-item
						command="closeOther"
						:disabled="tabNavListLen === 1 || (tabNavListLen === 2 && route.path !== homePath)"
						>Close Others</el-dropdown-item
					>
					<el-dropdown-item command="closeAll" :disabled="tabNavListLen === 1">Close All</el-dropdown-item>
				</el-dropdown-menu>
			</template>
		</el-dropdown>
	</div>
</template>
