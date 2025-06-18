/**
 * @description: 全局 store
 * @author LiQingSong
 */
import { defineStore } from "pinia";
import { theme, menuLayout, menuStyle, isTabsNav, isLayoutFooter } from "@/config/settings";
import { TTheme, TMenuLayout, TMenuStyle } from "@/@types/config.settings";
import { getActiveLLMProvidersWithModels } from "@/api/llm";
import type { LLMProviderHierarchy } from "@/api/llm";

// state ts类型
export interface IGlobalState {
	/* 以下是针对所有 Layout 扩展字段 */
	// 左侧展开收起
	collapsed: boolean;
	// 模板主题
	theme: TTheme;

	/* 以下是针对 MemberLayout 扩展字段 */
	// 菜单导航布局
	menuLayout: TMenuLayout;
	// 菜单导航风格
	menuStyle: TMenuStyle;
	// 是否启用多标签Tab页
	isTabsNav: boolean;
	// 是否启用底部
	isLayoutFooter: boolean;

	// 新增动态菜单相关状态
	dynamicMenus: any[]; // 存储从后端获取的菜单数据
	dynamicRoutesLoaded: boolean; // 标记动态路由是否已加载

	// LLM 提供商和模型数据
	llmProviderModels: LLMProviderHierarchy[];
	llmProviderModelsLoading: boolean;
	llmProviderModelsLoaded: boolean;
}

export const useGlobalStore = defineStore("useGlobalStore", {
	state: (): IGlobalState => {
		return {
			collapsed: false,
			theme: theme,
			menuLayout: menuLayout,
			menuStyle: menuStyle,
			isTabsNav: isTabsNav,
			isLayoutFooter: isLayoutFooter,
			dynamicMenus: [] as any[],
			dynamicRoutesLoaded: false,
			llmProviderModels: [],
			llmProviderModelsLoading: false,
			llmProviderModelsLoaded: false,
		};
	},
	getters: {},
	actions: {
		// 设置动态菜单数据
		setDynamicMenus(menus: any[]) {
			this.dynamicMenus = menus;
		},

		// 设置动态路由加载状态
		setDynamicRoutesLoaded(loaded: boolean) {
			this.dynamicRoutesLoaded = loaded;
		},

		/**
		 * @description 获取LLM提供商和模型数据
		 * @returns {Promise<LLMProviderHierarchy[]>} 返回提供商和模型数据
		 */
		async fetchLLMProviderModels() {
			// 如果已经在加载中，返回当前数据
			if (this.llmProviderModelsLoading) {
				return this.llmProviderModels;
			}

			// 如果数据已加载，直接返回
			if (this.llmProviderModelsLoaded && this.llmProviderModels.length > 0) {
				return this.llmProviderModels;
			}

			this.llmProviderModelsLoading = true;
			try {
				const result = await getActiveLLMProvidersWithModels();
				this.llmProviderModels = result;
				this.llmProviderModelsLoaded = true;
				return result;
			} catch (error) {
				console.error("获取模型层级数据失败", error);
				throw error;
			} finally {
				this.llmProviderModelsLoading = false;
			}
		},

		/**
		 * @description 重置LLM提供商和模型数据的加载状态
		 */
		resetLLMProviderModelsLoadedState() {
			this.llmProviderModelsLoaded = false;
		},
	},
});
