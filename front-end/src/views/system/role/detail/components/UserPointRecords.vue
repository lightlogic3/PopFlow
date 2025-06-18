<template>
	<div class="user-point-records-container">
		<div class="stats-section">
			<el-row :gutter="20">
				<el-col :span="8">
					<el-card class="stats-card" shadow="hover">
						<template #header>
							<div class="card-header">
								<span>积分统计</span>
							</div>
						</template>
						<div v-if="props.loading" class="stats-loading">
							<el-skeleton :rows="3" animated />
						</div>
						<div v-else class="stats-content">
							<div class="stat-row">
								<div class="stat-label">当前积分</div>
								<div class="stat-value">{{ pointSummary.current_amount || 0 }}</div>
							</div>
							<div class="stat-row">
								<div class="stat-label">累计获得</div>
								<div class="stat-value">{{ pointSummary.total_income || 0 }}</div>
							</div>
							<div class="stat-row">
								<div class="stat-label">累计消费</div>
								<div class="stat-value">{{ pointSummary.total_expense || 0 }}</div>
							</div>
						</div>
					</el-card>
				</el-col>
				<el-col :span="16">
					<el-card class="stats-card" shadow="hover">
						<template #header>
							<div class="card-header">
								<span>积分记录</span>
								<div class="card-actions">
									<el-button type="success" size="small" @click="showQuickActionDialog('reward')">
										<el-icon><Plus /></el-icon>快速奖励
									</el-button>
									<el-button type="danger" size="small" @click="showQuickActionDialog('deduct')">
										<el-icon><Minus /></el-icon>快速扣除
									</el-button>
								</div>
							</div>
						</template>
						<div v-if="props.loading" class="stats-loading">
							<el-skeleton :rows="3" animated />
						</div>
						<div v-else class="stats-content">
							<div class="stat-row">
								<div class="stat-label">记录总数</div>
								<div class="stat-value">{{ pointSummary.total_records || 0 }}</div>
							</div>
							<div class="stat-row">
								<div class="stat-label">净变化</div>
								<div class="stat-value">
									{{ pointSummary.net_change || 0 }}
								</div>
							</div>
							<div class="stat-row">
								<div class="stat-label">最后变动时间</div>
								<div class="stat-value">
									{{ formatDateTime(pointSummary.last_change_time) || "无" }}
								</div>
							</div>
						</div>
					</el-card>
				</el-col>
			</el-row>
		</div>

		<div class="filter-section">
			<el-form :inline="true" class="filter-form">
				<el-form-item label="变动类型" style="width: 200px">
					<el-select v-model="filterChangeType" placeholder="全部" clearable @change="handleFilter">
						<el-option label="全部" value="" />
						<el-option
							v-for="(displayName, type) in POINT_CHANGE_TYPE_DISPLAY"
							:key="type"
							:label="displayName"
							:value="type"
						/>
					</el-select>
				</el-form-item>
				<el-form-item label="时间范围">
					<el-date-picker
						v-model="dateRange"
						type="daterange"
						range-separator="至"
						start-placeholder="开始日期"
						end-placeholder="结束日期"
						@change="handleFilter"
					/>
				</el-form-item>
			</el-form>
		</div>

		<el-table
			v-loading="props.loading"
			:data="paginatedRecords"
			style="width: 100%"
			:header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
		>
			<el-table-column label="时间" width="180" sortable prop="create_time">
				<template #default="scope">
					{{ formatDateTime(scope.row.create_time) }}
				</template>
			</el-table-column>
			<el-table-column label="变动类型" width="150">
				<template #default="scope">
					{{ getChangeTypeLabel(scope.row.change_type) }}
				</template>
			</el-table-column>
			<el-table-column label="变动积分" width="120" align="center">
				<template #default="scope">
					<span :class="scope.row.change_amount > 0 ? 'text-success' : 'text-danger'">
						{{ scope.row.change_amount > 0 ? "+" : "" }}{{ scope.row.change_amount }}
					</span>
				</template>
			</el-table-column>
			<el-table-column label="变动后积分" width="120" align="center">
				<template #default="scope">
					{{ scope.row.current_amount }}
				</template>
			</el-table-column>
			<el-table-column label="相关卡牌" width="150">
				<template #default="scope">
					<span v-if="scope.row.card_id">卡牌ID: {{ scope.row.card_id }}</span>
					<span v-else>-</span>
				</template>
			</el-table-column>
			<el-table-column label="描述">
				<template #default="scope">
					{{ scope.row.description || "-" }}
				</template>
			</el-table-column>
		</el-table>

		<div class="pagination-section">
			<el-pagination
				v-model:current-page="currentPage"
				v-model:page-size="pageSize"
				:page-sizes="[10, 20, 50, 100]"
				layout="total, sizes, prev, pager, next"
				:total="totalRecords"
				@size-change="handleSizeChange"
				@current-change="handleCurrentChange"
			/>
		</div>

		<!-- 快速操作对话框 -->
		<el-dialog
			v-model="quickActionDialog.visible"
			:title="quickActionDialog.type === 'reward' ? '快速奖励积分' : '快速扣除积分'"
			width="500px"
		>
			<el-form ref="quickActionFormRef" :model="quickActionForm" :rules="quickActionRules" label-width="100px">
				<el-form-item label="积分数量" prop="amount">
					<el-input-number
						v-model="quickActionForm.amount"
						:min="1"
						:max="999999"
						placeholder="请输入积分数量"
						style="width: 100%"
					/>
				</el-form-item>
				<el-form-item label="变动类型" prop="change_type">
					<el-select v-model="quickActionForm.change_type" placeholder="请选择变动类型" style="width: 100%">
						<el-option
							v-for="(displayName, type) in POINT_CHANGE_TYPE_DISPLAY"
							:key="type"
							:label="displayName"
							:value="type"
						/>
					</el-select>
				</el-form-item>
				<el-form-item label="描述">
					<el-input
						v-model="quickActionForm.description"
						type="textarea"
						:rows="3"
						placeholder="请输入操作描述（可选）"
					/>
				</el-form-item>
				<el-form-item label="关联ID">
					<el-input v-model="quickActionForm.related_id" placeholder="关联业务ID（可选）" />
				</el-form-item>
				<el-form-item label="卡牌ID">
					<el-input v-model="quickActionForm.card_id" placeholder="关联卡牌ID（可选）" />
				</el-form-item>
			</el-form>

			<template #footer>
				<span class="dialog-footer">
					<el-button @click="quickActionDialog.visible = false">取消</el-button>
					<el-button type="primary" :loading="quickActionLoading" @click="handleQuickAction">
						确认{{ quickActionDialog.type === "reward" ? "奖励" : "扣除" }}
					</el-button>
				</span>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed, reactive } from "vue";
import {
	getUserPointRecords,
	getUserPointSummary,
	POINT_CHANGE_TYPE_DISPLAY,
	PointChangeType,
	quickRewardPoints,
	quickDeductPoints,
} from "@/api/pointRecord";
import { ElMessage } from "element-plus";
import { Plus, Minus } from "@element-plus/icons-vue";

const props = defineProps({
	userId: {
		type: Number,
		required: true,
	},
	loading: {
		type: Boolean,
		default: false,
	},
});

// 数据状态
const records = ref<any[]>([]);
const pointSummary = ref<any>({});
const isLoading = ref(false);

// 分页状态
const currentPage = ref(1);
const pageSize = ref(10);
const totalRecords = ref(0);

// 筛选状态
const filterChangeType = ref("");
const dateRange = ref<any>(null);

// 计算属性：分页数据
const paginatedRecords = computed(() => {
	const startIndex = (currentPage.value - 1) * pageSize.value;
	const endIndex = startIndex + pageSize.value;
	return records.value.slice(startIndex, endIndex);
});

// 快速操作
const quickActionLoading = ref(false);
const quickActionDialog = reactive({
	visible: false,
	type: "reward" as "reward" | "deduct",
});

const quickActionForm = reactive({
	amount: null as number | null,
	change_type: "",
	description: "",
	related_id: "",
	card_id: "",
});

const quickActionFormRef = ref();
const quickActionRules = {
	amount: [{ required: true, message: "请输入积分数量", trigger: "blur" }],
	change_type: [{ required: true, message: "请选择变动类型", trigger: "change" }],
};

// 监听用户ID变化，重新加载数据
watch(
	() => props.userId,
	(newVal) => {
		if (newVal) {
			loadPointRecords();
			loadPointSummary();
		}
	},
);

// 方法
const loadPointRecords = async () => {
	if (!props.userId) return;

	isLoading.value = true;
	try {
		let params: any = { limit: 500 };
		if (filterChangeType.value) {
			params.change_type = filterChangeType.value as PointChangeType;
		}

		const response = await getUserPointRecords(props.userId, params);
		records.value = response;
		totalRecords.value = response.length;
	} catch (error) {
		console.error("加载用户积分记录失败", error);
		ElMessage.error("加载用户积分记录失败");
	} finally {
		isLoading.value = false;
	}
};

const loadPointSummary = async () => {
	if (!props.userId) return;

	try {
		const response = await getUserPointSummary(props.userId);
		pointSummary.value = response;
	} catch (error) {
		console.error("加载用户积分汇总信息失败", error);
	}
};

const getChangeTypeLabel = (changeType: string): string => {
	if (POINT_CHANGE_TYPE_DISPLAY[changeType as PointChangeType]) {
		return POINT_CHANGE_TYPE_DISPLAY[changeType as PointChangeType];
	}

	return changeType;
};

const formatDateTime = (dateTime: string): string => {
	if (!dateTime) return "";
	const date = new Date(dateTime);
	return date.toLocaleString();
};

const handleFilter = () => {
	loadPointRecords();
};

const handleSizeChange = (val: number) => {
	pageSize.value = val;
	currentPage.value = 1;
};

const handleCurrentChange = (val: number) => {
	currentPage.value = val;
};

// 显示快速操作对话框
const showQuickActionDialog = (type: "reward" | "deduct") => {
	quickActionDialog.type = type;
	quickActionDialog.visible = true;

	// 重置表单
	Object.assign(quickActionForm, {
		amount: null,
		change_type: type === "reward" ? PointChangeType.ADMIN_ADJUST : PointChangeType.SHOP_PURCHASE,
		description: "",
		related_id: "",
		card_id: "",
	});
};

// 处理快速操作
const handleQuickAction = async () => {
	try {
		await quickActionFormRef.value?.validate();

		const params = {
			user_id: props.userId,
			amount: quickActionForm.amount!,
			change_type: quickActionForm.change_type as PointChangeType,
			description: quickActionForm.description || undefined,
			related_id: quickActionForm.related_id ? parseInt(quickActionForm.related_id) : undefined,
			card_id: quickActionForm.card_id ? parseInt(quickActionForm.card_id) : undefined,
		};

		quickActionLoading.value = true;

		if (quickActionDialog.type === "reward") {
			await quickRewardPoints(params);
			ElMessage.success(`成功奖励用户 ${params.amount} 积分`);
		} else {
			await quickDeductPoints(params);
			ElMessage.success(`成功扣除用户 ${params.amount} 积分`);
		}

		quickActionDialog.visible = false;
		// 刷新数据
		await loadPointRecords();
		await loadPointSummary();
	} catch (error) {
		console.error("快速操作失败:", error);
		ElMessage.error("操作失败，请重试");
	} finally {
		quickActionLoading.value = false;
	}
};

// 生命周期钩子
onMounted(() => {
	if (props.userId) {
		loadPointRecords();
		loadPointSummary();
	}
});
</script>

<style scoped>
.user-point-records-container {
	padding: 20px 0;
}

.stats-section {
	margin-bottom: 30px;
}

.stats-card {
	margin-bottom: 20px;
	height: 100%;
}

.stats-loading {
	padding: 10px;
}

.card-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.card-actions {
	display: flex;
	gap: 8px;
}

.stats-content {
	padding: 10px 0;
}

.stat-row {
	display: flex;
	justify-content: space-between;
	margin-bottom: 10px;
	font-size: 14px;
	align-items: center;
}

.stat-row:last-child {
	margin-bottom: 0;
}

.stat-label {
	color: #606266;
}

.stat-value {
	font-weight: bold;
	color: #303133;
}

.stat-rate {
	font-size: 12px;
	color: #909399;
	margin-left: 5px;
	font-weight: normal;
}

.no-data {
	text-align: center;
	color: #909399;
	padding: 20px 0;
}

.filter-section {
	margin-bottom: 20px;
}

.text-success {
	color: #67c23a;
}

.text-danger {
	color: #f56c6c;
}

.pagination-section {
	margin-top: 20px;
	display: flex;
	justify-content: center;
}
</style>
