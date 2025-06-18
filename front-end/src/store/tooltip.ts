/**
 * @description: 提示信息 store
 */
import { defineStore } from "pinia";
import { getConfig_value } from "@/api/system";

// state ts类型
export interface ITooltipState {
	// 提示信息数据
	tooltipData: Record<string, string>;
	// 是否已加载
	isLoaded: boolean;
	// 是否正在加载中
	loading: boolean;
	// 上次加载时间
	lastLoadTime: number;
}

export const useTooltipStore = defineStore("useTooltipStore", {
	state: (): ITooltipState => {
		return {
			tooltipData: {},
			isLoaded: false,
			loading: false,
			lastLoadTime: 0,
		};
	},
	getters: {
		// 获取提示信息
		getTooltip: (state) => (key: string) => {
			return state.tooltipData[key] || "";
		},
	},
	actions: {
		/**
		 * @description: 获取提示信息数据
		 * @returns result code 0 成功, 1 加载中, 2 错误
		 */
		async fetchTooltipData() {
			// 返回结果对象
			const result = { code: 0, msg: "" };

			// 如果已经在加载中，直接返回
			if (this.loading) {
				result.code = 1;
				result.msg = "正在加载中";
				return result;
			}

			// 如果已经加载过且在10分钟内，不重复加载
			const now = Date.now();
			const TEN_MINUTES = 10 * 60 * 1000;
			if (this.isLoaded && now - this.lastLoadTime < TEN_MINUTES) {
				return result;
			}

			try {
				this.loading = true;
				const res = await getConfig_value("WEB_USE_TIP");
				if (res && res.config_value) {
					try {
						this.tooltipData = JSON.parse(res.config_value);
						this.isLoaded = true;
						this.lastLoadTime = now;
					} catch (parseError) {
						console.error("解析提示信息数据失败:", parseError);
						result.code = 2;
						result.msg = "解析提示信息数据失败";
					}
				}
			} catch (error: any) {
				// 判断是否为请求取消错误，如果是则不再处理
				if (error.name === "CanceledError" || error.code === "ERR_CANCELED") {
					console.debug("提示信息数据请求已取消");
					result.code = 1;
					result.msg = "请求已取消";
				} else {
					console.error("获取提示信息数据失败:", error);
					result.code = 2;
					result.msg = error.message || "网络请求失败";
				}
			} finally {
				this.loading = false;
			}

			return result;
		},

		/**
		 * @description: 设置提示信息数据
		 */
		setTooltipData(data: Record<string, string>) {
			this.tooltipData = data;
			this.isLoaded = true;
			this.lastLoadTime = Date.now();
		},

		/**
		 * @description: 重置提示信息数据
		 */
		reset() {
			this.tooltipData = {};
			this.isLoaded = false;
			this.lastLoadTime = 0;
		},

		/**
		 * @description: 检查是否需要重新加载数据
		 * @param force 是否强制重新加载
		 */
		async ensureLoaded(force = false) {
			if (force || !this.isLoaded) {
				await this.fetchTooltipData();
			}
			return this.isLoaded;
		},
	},
});
