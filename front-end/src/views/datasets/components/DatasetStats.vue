<template>
	<div class="dataset-stats">
		<el-card class="stats-card">
			<template #header>
				<div class="card-header">
					<span>数据统计</span>
					<el-button type="primary" link @click="refreshStats">
						<el-icon><Refresh /></el-icon>
						刷新
					</el-button>
				</div>
			</template>
			<div class="stats-content" v-loading="loading">
				<el-row :gutter="20">
					<el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="(value, key) in statsData" :key="key">
						<div class="stat-item">
							<div class="stat-icon" :class="getStatIconClass(key)">
								<el-icon>
									<component :is="getStatIcon(key)" />
								</el-icon>
							</div>
							<div class="stat-info">
								<div class="stat-label">{{ getStatLabel(key) }}</div>
								<div class="stat-value">{{ value }}</div>
							</div>
						</div>
					</el-col>
				</el-row>

				<div class="no-data" v-if="Object.keys(statsData).length === 0 && !loading">
					<el-empty description="暂无统计数据" />
				</div>

				<div class="last-updated" v-if="lastUpdated">
					<span>最后更新时间: {{ lastUpdated }}</span>
				</div>
			</div>
		</el-card>
	</div>
</template>

<script setup lang="ts">
import { ref, onMounted, defineProps } from "vue";
import { ElMessage } from "element-plus";
import { Refresh, DataLine, ChatDotRound, Document, Collection } from "@element-plus/icons-vue";
import { getDatasetStats } from "@/api/datasets";
import { getStatLabel } from "@/utils/dataset";
import { DatasetType, DatasetStats } from "@/types/dataset";

/**
 * 数据集统计信息组件
 * @description 展示数据集的统计信息和指标
 */

// 定义props
const props = defineProps<{
	datasetId: number;
	datasetType?: DatasetType | string;
}>();

// 响应式状态
const loading = ref(false);
const statsData = ref<DatasetStats>({} as DatasetStats);
const lastUpdated = ref("");

// 统计图标映射
const iconMap: Record<string, any> = {
	entryCount: Collection,
	tokenCount: Document,
	avgTokensPerEntry: DataLine,
	messageCount: ChatDotRound,
	default: DataLine,
};

// 统计图标颜色类映射
const iconClassMap: Record<string, string> = {
	entryCount: "blue",
	tokenCount: "green",
	avgTokensPerEntry: "orange",
	messageCount: "purple",
	default: "blue",
};

/**
 * 获取统计项的图标
 */
const getStatIcon = (key: any): any => {
	return iconMap[key] || iconMap.default;
};

/**
 * 获取统计项的图标样式类
 */
const getStatIconClass = (key: any): string => {
	return `stat-icon-${iconClassMap[key] || iconClassMap.default}`;
};

/**
 * 设置最后更新时间
 */
const updateTimestamp = () => {
	const now = new Date();
	lastUpdated.value = now.toLocaleString("zh-CN", {
		year: "numeric",
		month: "2-digit",
		day: "2-digit",
		hour: "2-digit",
		minute: "2-digit",
		second: "2-digit",
	});
};

/**
 * 获取数据集统计信息
 */
const fetchStats = async () => {
	if (!props.datasetId) return;

	loading.value = true;
	statsData.value = {} as DatasetStats;

	try {
		const response = await getDatasetStats(props.datasetId);

		// 清空当前数据并设置新数据
		Object.keys(statsData.value).forEach((key) => delete statsData.value[key as keyof DatasetStats]);
		Object.assign(statsData.value, response);

		updateTimestamp();
	} catch (error) {
		if (error instanceof Error) {
			ElMessage.error(`获取统计信息失败: ${error.message}`);
		} else {
			ElMessage.error("获取统计信息失败");
		}
		console.error("获取统计信息失败:", error);
	} finally {
		loading.value = false;
	}
};

/**
 * 刷新统计数据
 */
const refreshStats = () => {
	fetchStats();
};

// 生命周期钩子
onMounted(() => {
	fetchStats();
});
</script>

<style lang="scss" scoped>
.dataset-stats {
	margin-bottom: 20px;

	.stats-card {
		.card-header {
			display: flex;
			justify-content: space-between;
			align-items: center;
		}

		.stats-content {
			min-height: 100px;

			.stat-item {
				display: flex;
				align-items: center;
				margin-bottom: 20px;
				padding: 15px;
				border-radius: 8px;
				background-color: var(--el-fill-color-light);
				transition: all 0.3s;

				&:hover {
					transform: translateY(-3px);
					box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
				}

				.stat-icon {
					width: 50px;
					height: 50px;
					border-radius: 50%;
					color: white;
					display: flex;
					align-items: center;
					justify-content: center;
					margin-right: 15px;

					i {
						font-size: 24px;
					}

					&.stat-icon-blue {
						background-color: var(--el-color-primary);
					}

					&.stat-icon-green {
						background-color: var(--el-color-success);
					}

					&.stat-icon-orange {
						background-color: var(--el-color-warning);
					}

					&.stat-icon-purple {
						background-color: #8e44ad;
					}
				}

				.stat-info {
					flex: 1;

					.stat-label {
						font-size: 14px;
						color: var(--el-text-color-secondary);
						margin-bottom: 5px;
					}

					.stat-value {
						font-size: 24px;
						font-weight: bold;
						color: var(--el-text-color-primary);
					}
				}
			}

			.no-data {
				padding: 30px 0;
			}

			.last-updated {
				color: var(--el-text-color-secondary);
				font-size: 12px;
				text-align: right;
				margin-top: 10px;
			}
		}
	}
}
</style>
