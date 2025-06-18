<template>
	<div class="point-record-container">
		<!-- 统计卡片区域 -->
		<div class="statistics-cards">
			<el-row :gutter="16">
				<el-col :span="6">
					<el-card class="stat-card income-card">
						<div class="stat-content">
							<div class="stat-icon">
								<el-icon><TrendCharts /></el-icon>
							</div>
							<div class="stat-info">
								<div class="stat-value">{{ formatNumber(statistics.total_income) }}</div>
								<div class="stat-label">Total Income Points</div>
							</div>
						</div>
					</el-card>
				</el-col>
				<el-col :span="6">
					<el-card class="stat-card expense-card">
						<div class="stat-content">
							<div class="stat-icon">
								<el-icon><Bottom /></el-icon>
							</div>
							<div class="stat-info">
								<div class="stat-value">{{ formatNumber(statistics.total_expense) }}</div>
								<div class="stat-label">Total Expense Points</div>
							</div>
						</div>
					</el-card>
				</el-col>
				<el-col :span="6">
					<el-card class="stat-card records-card">
						<div class="stat-content">
							<div class="stat-icon">
								<el-icon><Document /></el-icon>
							</div>
							<div class="stat-info">
								<div class="stat-value">{{ formatNumber(statistics.total_records) }}</div>
								<div class="stat-label">Total Records</div>
							</div>
						</div>
					</el-card>
				</el-col>
				<el-col :span="6">
					<el-card class="stat-card net-card">
						<div class="stat-content">
							<div class="stat-icon">
								<el-icon><Money /></el-icon>
							</div>
							<div class="stat-info">
								<div class="stat-value">{{ formatNumber(statistics.net_change) }}</div>
								<div class="stat-label">Net Change</div>
							</div>
						</div>
					</el-card>
				</el-col>
			</el-row>
		</div>

		<!-- 搜索和操作区域 -->
		<el-card class="search-card">
			<div class="search-form">
				<el-form :model="searchForm" inline>
					<el-form-item label="User ID">
						<el-input v-model="searchForm.user_id" placeholder="Enter user ID" clearable style="width: 160px" />
					</el-form-item>
					<el-form-item label="Change Type">
						<el-select v-model="searchForm.change_type" placeholder="Select change type" clearable style="width: 180px">
							<el-option v-for="type in changeTypes" :key="type.code" :label="type.display_name" :value="type.code" />
						</el-select>
					</el-form-item>
					<el-form-item label="Point Range">
						<el-input v-model="searchForm.min_amount" placeholder="Min value" style="width: 120px" />
						<span style="margin: 0 8px">-</span>
						<el-input v-model="searchForm.max_amount" placeholder="Max value" style="width: 120px" />
					</el-form-item>
					<el-form-item label="Time Range">
						<el-date-picker
							v-model="searchForm.dateRange"
							type="datetimerange"
							range-separator="to"
							start-placeholder="Start time"
							end-placeholder="End time"
							format="YYYY-MM-DD HH:mm:ss"
							value-format="YYYY-MM-DD HH:mm:ss"
							style="width: 360px"
						/>
					</el-form-item>
					<el-form-item>
						<el-button type="primary" @click="handleSearch">
							<el-icon><Search /></el-icon>
							Search
						</el-button>
						<el-button @click="handleReset">
							<el-icon><Refresh /></el-icon>
							Reset
						</el-button>
					</el-form-item>
				</el-form>
			</div>

			<div class="action-buttons">
				<el-button type="success" @click="showQuickActionDialog('reward')">
					<el-icon><Plus /></el-icon>
					Quick Reward
				</el-button>
				<el-button type="warning" @click="showQuickActionDialog('deduct')">
					<el-icon><Minus /></el-icon>
					Quick Deduct
				</el-button>
				<el-button type="info" @click="showStatisticsDialog">
					<el-icon><DataAnalysis /></el-icon>
					Statistical Analysis
				</el-button>
				<el-button type="primary" @click="showRankingDialog">
					<el-icon><Trophy /></el-icon>
					Point Ranking
				</el-button>
			</div>
		</el-card>

		<!-- 数据表格 -->
		<el-card class="table-card">
			<el-table v-loading="tableLoading" :data="tableData" stripe style="width: 100%" @sort-change="handleSortChange">
				<el-table-column prop="id" label="ID" width="80" />
				<el-table-column prop="user_id" label="User ID" width="100" />
				<el-table-column label="Point Change" width="150">
					<template #default="{ row }">
						<el-tag :type="row.is_income ? 'success' : 'danger'" class="amount-tag">
							{{ row.is_income ? "+" : "" }}{{ formatNumber(row.change_amount) }}
						</el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="current_amount" label="Balance After" width="150">
					<template #default="{ row }">
						<span class="current-amount">{{ formatNumber(row.current_amount) }}</span>
					</template>
				</el-table-column>
				<el-table-column label="Change Type" width="120">
					<template #default="{ row }">
						<el-tag :type="getChangeTypeColor(row.change_type)">
							{{ row.change_type_display }}
						</el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="related_id" label="Related ID" width="100" />
				<el-table-column prop="card_id" label="Card ID" width="100" />
				<el-table-column label="Description" min-width="200">
					<template #default="{ row }">
						<span class="description">{{ row.description || "-" }}</span>
					</template>
				</el-table-column>
				<el-table-column label="Created Time" width="180" sortable="custom" prop="create_time">
					<template #default="{ row }">
						<span>{{ formatDateTime(row.create_time) }}</span>
					</template>
				</el-table-column>
				<el-table-column label="Actions" width="120" fixed="right">
					<template #default="{ row }">
						<el-button size="small" @click="viewDetail(row)">
							<el-icon><View /></el-icon>
							Details
						</el-button>
					</template>
				</el-table-column>
			</el-table>

			<!-- 分页 -->
			<div class="pagination-container">
				<el-pagination
					v-model:current-page="pagination.page"
					v-model:page-size="pagination.size"
					:total="pagination.total"
					:page-sizes="[10, 20, 50, 100]"
					layout="total, sizes, prev, pager, next, jumper"
					@size-change="handleSizeChange"
					@current-change="handleCurrentChange"
				/>
			</div>
		</el-card>

		<!-- Quick Action Dialog -->
		<el-dialog
			v-model="quickActionDialog.visible"
			:title="quickActionDialog.type === 'reward' ? 'Quick Reward Points' : 'Quick Deduct Points'"
			width="500px"
		>
			<el-form ref="quickActionFormRef" :model="quickActionForm" :rules="quickActionRules" label-width="100px">
				<el-form-item label="User ID" prop="user_id">
					<el-input v-model="quickActionForm.user_id" placeholder="Please enter user ID" />
				</el-form-item>
				<el-form-item label="Point Amount" prop="amount">
					<el-input-number
						v-model="quickActionForm.amount"
						:min="1"
						:max="999999"
						placeholder="Please enter point amount"
						style="width: 100%"
					/>
				</el-form-item>
				<el-form-item label="Change Type" prop="change_type">
					<el-select v-model="quickActionForm.change_type" placeholder="Please select change type" style="width: 100%">
						<el-option v-for="type in changeTypes" :key="type.code" :label="type.display_name" :value="type.code" />
					</el-select>
				</el-form-item>
				<el-form-item label="Description">
					<el-input
						v-model="quickActionForm.description"
						type="textarea"
						:rows="3"
						placeholder="Please enter operation description (optional)"
					/>
				</el-form-item>
				<el-form-item label="Related ID">
					<el-input v-model="quickActionForm.related_id" placeholder="Related business ID (optional)" />
				</el-form-item>
				<el-form-item label="Card ID">
					<el-input v-model="quickActionForm.card_id" placeholder="Related card ID (optional)" />
				</el-form-item>
			</el-form>

			<template #footer>
				<span class="dialog-footer">
					<el-button @click="quickActionDialog.visible = false">Cancel</el-button>
					<el-button type="primary" :loading="quickActionLoading" @click="handleQuickAction">
						Confirm {{ quickActionDialog.type === "reward" ? "Reward" : "Deduct" }}
					</el-button>
				</span>
			</template>
		</el-dialog>

		<!-- Statistical Analysis Dialog -->
		<el-dialog v-model="statisticsDialog.visible" title="Point Statistical Analysis" width="900px">
			<el-tabs v-model="statisticsDialog.activeTab">
				<!-- Daily Statistics -->
				<el-tab-pane label="Daily Statistics" name="daily">
					<div ref="dailyChartRef" style="height: 400px"></div>
				</el-tab-pane>

				<!-- Type Distribution -->
				<el-tab-pane label="Type Distribution" name="distribution">
					<div ref="distributionChartRef" style="height: 400px"></div>
				</el-tab-pane>
			</el-tabs>
		</el-dialog>

		<!-- Point Ranking Dialog -->
		<el-dialog v-model="rankingDialog.visible" title="Point Income Ranking" width="600px">
			<el-table :data="rankingData" style="width: 100%">
				<el-table-column prop="rank" label="Rank" width="80">
					<template #default="{ row }">
						<el-tag :type="row.rank <= 3 ? 'warning' : 'info'" effect="dark"> #{{ row.rank }} </el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="user_id" label="User ID" width="100" />
				<el-table-column prop="total_earned" label="Income Points" width="150">
					<template #default="{ row }">
						<span class="earning-amount">{{ formatNumber(row.total_earned) }}</span>
					</template>
				</el-table-column>
			</el-table>
		</el-dialog>

		<!-- Detail Dialog -->
		<el-dialog v-model="detailDialog.visible" title="Point Record Details" width="500px">
			<el-descriptions :column="1" border>
				<el-descriptions-item label="Record ID">{{ detailData.id }}</el-descriptions-item>
				<el-descriptions-item label="User ID">{{ detailData.user_id }}</el-descriptions-item>
				<el-descriptions-item label="Point Change">
					<el-tag :type="detailData.is_income ? 'success' : 'danger'">
						{{ detailData.is_income ? "+" : "" }}{{ formatNumber(detailData.change_amount) }}
					</el-tag>
				</el-descriptions-item>
				<el-descriptions-item label="Balance After">{{ formatNumber(detailData.current_amount) }}</el-descriptions-item>
				<el-descriptions-item label="Change Type">
					<el-tag :type="getChangeTypeColor(detailData.change_type)">
						{{ detailData.change_type_display }}
					</el-tag>
				</el-descriptions-item>
				<el-descriptions-item label="Related ID">{{ detailData.related_id || "-" }}</el-descriptions-item>
				<el-descriptions-item label="Card ID">{{ detailData.card_id || "-" }}</el-descriptions-item>
				<el-descriptions-item label="Description">{{ detailData.description || "-" }}</el-descriptions-item>
				<el-descriptions-item label="Creator ID">{{ detailData.creator_id || "-" }}</el-descriptions-item>
				<el-descriptions-item label="Created Time">{{ formatDateTime(detailData.create_time) }}</el-descriptions-item>
			</el-descriptions>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from "vue";
import { ElMessage } from "element-plus";
import {
	Search,
	Refresh,
	Plus,
	Minus,
	DataAnalysis,
	Trophy,
	View,
	TrendCharts,
	Bottom,
	Document,
	Money,
} from "@element-plus/icons-vue";

// API导入
import {
	getPointRecords,
	getPointRecordStatistics,
	quickRewardPoints,
	quickDeductPoints,
	getAllChangeTypes,
	PointChangeType,
	type PointRecord,
	type PointRecordStatistics,
	type TopEarner,
	type ChangeTypeInfo,
} from "@/api/pointRecord";

// 响应式数据
const tableLoading = ref(false);
const quickActionLoading = ref(false);
const tableData = ref<PointRecord[]>([]);
const changeTypes = ref<ChangeTypeInfo[]>([]);

// 统计数据
const statistics = ref<PointRecordStatistics>({
	total_records: 0,
	total_income: 0,
	total_expense: 0,
	net_change: 0,
	most_common_type: "",
	avg_change_amount: 0,
	daily_stats: [],
	type_distribution: {},
});

// 分页数据
const pagination = reactive({
	page: 1,
	size: 20,
	total: 0,
});

// 搜索表单
const searchForm = reactive({
	user_id: "",
	change_type: "",
	min_amount: "",
	max_amount: "",
	dateRange: null as string[] | null,
});

// 快速操作
const quickActionDialog = reactive({
	visible: false,
	type: "reward" as "reward" | "deduct",
});

const quickActionForm = reactive({
	user_id: "",
	amount: null as number | null,
	change_type: "",
	description: "",
	related_id: "",
	card_id: "",
});

const quickActionFormRef = ref();
const quickActionRules = {
	user_id: [{ required: true, message: "Please enter user ID", trigger: "blur" }],
	amount: [{ required: true, message: "Please enter point amount", trigger: "blur" }],
	change_type: [{ required: true, message: "Please select change type", trigger: "change" }],
};

// 统计对话框
const statisticsDialog = reactive({
	visible: false,
	activeTab: "daily",
});

// 排行榜对话框
const rankingDialog = reactive({
	visible: false,
});
const rankingData = ref<TopEarner[]>([]);

// 详情对话框
const detailDialog = reactive({
	visible: false,
});
const detailData = ref<PointRecord>({} as PointRecord);

// 图表引用
const dailyChartRef = ref();
const distributionChartRef = ref();

// 方法
const formatNumber = (num: number): string => {
	return new Intl.NumberFormat("zh-CN").format(num);
};

const formatDateTime = (dateStr: string): string => {
	return new Date(dateStr).toLocaleString("zh-CN");
};

const getChangeTypeColor = (type: string): any => {
	const colorMap: Record<string, string> = {
		register: "success",
		ai_challenge: "primary",
		unlock_card: "warning",
		admin_adjust: "danger",
		system_reward: "success",
		daily_check: "info",
		shop_purchase: "warning",
	};
	return colorMap[type] || "info";
};

// 加载数据
const loadTableData = async () => {
	try {
		tableLoading.value = true;

		const params: any = {
			page: pagination.page,
			size: pagination.size,
		};

		// 添加搜索条件
		if (searchForm.user_id) params.user_id = parseInt(searchForm.user_id);
		if (searchForm.change_type) params.change_type = searchForm.change_type;
		if (searchForm.min_amount) params.min_amount = parseInt(searchForm.min_amount);
		if (searchForm.max_amount) params.max_amount = parseInt(searchForm.max_amount);
		if (searchForm.dateRange) {
			params.start_time = searchForm.dateRange[0];
			params.end_time = searchForm.dateRange[1];
		}

		const response = await getPointRecords(params);
		tableData.value = response.items;
		pagination.total = response.total;
	} catch (error) {
		console.error("Failed to load data:", error);
		ElMessage.error("Failed to load data");
	} finally {
		tableLoading.value = false;
	}
};

// 加载统计数据
const loadStatistics = async () => {
	try {
		const response = await getPointRecordStatistics();
		statistics.value = response;
	} catch (error) {
		console.error("Failed to load statistics data:", error);
	}
};

// 加载变动类型
const loadChangeTypes = async () => {
	try {
		const response = await getAllChangeTypes();
		changeTypes.value = response.types;
	} catch (error) {
		console.error("Failed to load change types:", error);
	}
};

// 搜索
const handleSearch = () => {
	pagination.page = 1;
	loadTableData();
};

// 重置
const handleReset = () => {
	Object.assign(searchForm, {
		user_id: "",
		change_type: "",
		min_amount: "",
		max_amount: "",
		dateRange: null,
	});
	pagination.page = 1;
	loadTableData();
};

// 分页
const handleSizeChange = (size: number) => {
	pagination.size = size;
	pagination.page = 1;
	loadTableData();
};

const handleCurrentChange = (page: number) => {
	pagination.page = page;
	loadTableData();
};

// 排序
const handleSortChange = ({ prop, order }: any) => {
	// TODO: 实现排序逻辑
	console.log("Sort field:", prop, "Sort order:", order);
	loadTableData();
};

// Quick action
const showQuickActionDialog = (type: "reward" | "deduct") => {
	quickActionDialog.type = type;
	quickActionDialog.visible = true;

	// Reset form
	Object.assign(quickActionForm, {
		user_id: "",
		amount: null,
		change_type: type === "reward" ? PointChangeType.ADMIN_ADJUST : PointChangeType.SHOP_PURCHASE,
		description: "",
		related_id: "",
		card_id: "",
	});
};

const handleQuickAction = async () => {
	try {
		await quickActionFormRef.value?.validate();

		const params = {
			user_id: parseInt(quickActionForm.user_id),
			amount: quickActionForm.amount!,
			change_type: quickActionForm.change_type as PointChangeType,
			description: quickActionForm.description || undefined,
			related_id: quickActionForm.related_id ? parseInt(quickActionForm.related_id) : undefined,
			card_id: quickActionForm.card_id ? parseInt(quickActionForm.card_id) : undefined,
		};

		quickActionLoading.value = true;

		if (quickActionDialog.type === "reward") {
			await quickRewardPoints(params);
			ElMessage.success("Reward successful");
		} else {
			await quickDeductPoints(params);
			ElMessage.success("Deduct successful");
		}

		quickActionDialog.visible = false;
		await loadTableData();
		await loadStatistics();
	} catch (error) {
		console.error("Quick action failed:", error);
		ElMessage.error("Operation failed");
	} finally {
		quickActionLoading.value = false;
	}
};

// Show statistics analysis
const showStatisticsDialog = () => {
	statisticsDialog.visible = true;
	nextTick(() => {
		// TODO: Initialize charts
	});
};

// Show ranking
const showRankingDialog = async () => {
	// try {
	// 	const response = await getTopEarners({ limit: 10, days: 30 });
	// 	rankingData.value = response;
	// 	rankingDialog.visible = true;
	// } catch (error) {
	// 	ElMessage.error("Failed to get ranking list");
	// }
	console.log("Ranking feature not yet implemented");
};

// View details
const viewDetail = (row: PointRecord) => {
	detailData.value = row;
	detailDialog.visible = true;
};

// 初始化
onMounted(() => {
	loadTableData();
	loadStatistics();
	loadChangeTypes();
});
</script>

<style scoped lang="scss">
.point-record-container {
	padding: 20px;

	.statistics-cards {
		margin-bottom: 20px;

		.stat-card {
			.stat-content {
				display: flex;
				align-items: center;

				.stat-icon {
					font-size: 40px;
					margin-right: 16px;

					.el-icon {
						color: #409eff;
					}
				}

				.stat-info {
					.stat-value {
						font-size: 24px;
						font-weight: bold;
						color: #303133;
						margin-bottom: 4px;
					}

					.stat-label {
						font-size: 14px;
						color: #909399;
					}
				}
			}

			&.income-card .stat-icon .el-icon {
				color: #67c23a;
			}

			&.expense-card .stat-icon .el-icon {
				color: #f56c6c;
			}

			&.records-card .stat-icon .el-icon {
				color: #e6a23c;
			}

			&.net-card .stat-icon .el-icon {
				color: #409eff;
			}
		}
	}

	.search-card {
		margin-bottom: 20px;

		.search-form {
			margin-bottom: 16px;

			.el-form-item {
				margin-bottom: 16px;
			}
		}

		.action-buttons {
			text-align: right;

			.el-button {
				margin-left: 8px;
			}
		}
	}

	.table-card {
		.amount-tag {
			font-weight: bold;
		}

		.current-amount {
			font-weight: 500;
			color: #409eff;
		}

		.description {
			color: #606266;
		}

		.pagination-container {
			margin-top: 20px;
			text-align: right;
		}
	}

	.earning-amount {
		font-weight: bold;
		color: #67c23a;
	}
}
</style>
