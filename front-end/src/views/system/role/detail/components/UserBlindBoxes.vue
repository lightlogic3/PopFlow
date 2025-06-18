<template>
	<div class="user-blind-boxes-container">
		<div class="stats-section">
			<el-row :gutter="20">
				<el-col :span="8">
					<el-card class="stats-card" shadow="hover">
						<template #header>
							<div class="card-header">
								<span>盲盒统计</span>
							</div>
						</template>
						<div v-if="loading" class="stats-loading">
							<el-skeleton :rows="3" animated />
						</div>
						<div v-else class="stats-content">
							<div class="stat-row">
								<div class="stat-label">总抽取次数</div>
								<div class="stat-value">{{ stats.total_count || 0 }}</div>
							</div>
							<div class="stat-row">
								<div class="stat-label">获得积分</div>
								<div class="stat-value">{{ stats.total_points_gained || 0 }}</div>
							</div>
							<div class="stat-row">
								<div class="stat-label">重复卡牌</div>
								<div class="stat-value">
									{{ stats.duplicate_count || 0 }}
									<span class="stat-rate">({{ formatRate(stats.duplicate_rate) }})</span>
								</div>
							</div>
						</div>
					</el-card>
				</el-col>
				<el-col :span="8">
					<el-card class="stats-card" shadow="hover">
						<template #header>
							<div class="card-header">
								<span>特殊获取</span>
							</div>
						</template>
						<div v-if="loading" class="stats-loading">
							<el-skeleton :rows="3" animated />
						</div>
						<div v-else class="stats-content">
							<div class="stat-row">
								<div class="stat-label">保底触发</div>
								<div class="stat-value">
									{{ stats.guaranteed_count || 0 }}
									<span class="stat-rate">({{ formatRate(stats.guaranteed_rate) }})</span>
								</div>
							</div>
							<div class="stat-row">
								<div class="stat-label">特殊奖励</div>
								<div class="stat-value">
									{{ stats.special_count || 0 }}
									<span class="stat-rate">({{ formatRate(stats.special_rate) }})</span>
								</div>
							</div>
						</div>
					</el-card>
				</el-col>
				<el-col :span="8">
					<el-card class="stats-card" shadow="hover">
						<template #header>
							<div class="card-header">
								<span>来源分布</span>
							</div>
						</template>
						<div v-if="loading" class="stats-loading">
							<el-skeleton :rows="3" animated />
						</div>
						<div v-else class="stats-content">
							<div v-for="(count, type) in stats.source_counts" :key="type" class="stat-row">
								<div class="stat-label">{{ getSourceTypeLabel(type) }}</div>
								<div class="stat-value">
									{{ count }}
									<span class="stat-rate">({{ formatRate(count / stats.total_count) }})</span>
								</div>
							</div>
							<div v-if="!stats.source_counts || Object.keys(stats.source_counts).length === 0" class="no-data">
								暂无数据
							</div>
						</div>
					</el-card>
				</el-col>
			</el-row>
		</div>

		<div class="filter-section">
			<el-form :inline="true" class="filter-form">
				<el-form-item label="盲盒类型" style="width: 200px">
					<el-select v-model="filterBoxId" placeholder="全部" clearable @change="handleFilter">
						<el-option label="全部" value="" />
						<el-option v-for="box in blindBoxes" :key="box.id" :label="box.name" :value="box.id" />
					</el-select>
				</el-form-item>
				<el-form-item label="来源类型" style="width: 200px">
					<el-select v-model="filterSourceType" placeholder="全部" clearable @change="handleFilter">
						<el-option label="全部" value="" />
						<el-option label="购买" value="purchase" />
						<el-option label="奖励" value="reward" />
						<el-option label="礼物" value="gift" />
					</el-select>
				</el-form-item>
				<el-form-item label="特殊类型" style="width: 200px">
					<el-select v-model="filterSpecialType" placeholder="全部" clearable @change="handleFilter">
						<el-option label="全部" value="" />
						<el-option label="保底触发" value="guaranteed" />
						<el-option label="特殊奖励" value="special" />
						<el-option label="重复卡牌" value="duplicate" />
					</el-select>
				</el-form-item>
			</el-form>
		</div>

		<el-table
			v-loading="loading"
			:data="filteredRecords"
			style="width: 100%"
			:header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
		>
			<el-table-column label="抽取时间" width="180" sortable prop="create_time">
				<template #default="scope">
					{{ formatDateTime(scope.row.create_time) }}
				</template>
			</el-table-column>
			<el-table-column label="盲盒" width="180">
				<template #default="scope">
					{{ getBlindBoxName(scope.row.blind_box_id) }}
				</template>
			</el-table-column>
			<el-table-column label="获得卡牌">
				<template #default="scope">
					<div class="card-info">
						<el-avatar shape="square" :size="40" :src="getCardImageUrl(scope.row.card_id)">
							{{ getCardName(scope.row.card_id).charAt(0) }}
						</el-avatar>
						<span class="card-name">{{ getCardName(scope.row.card_id) }}</span>
					</div>
				</template>
			</el-table-column>
			<el-table-column label="卡牌类型" width="100">
				<template #default="scope">
					<el-tag :type="getCardRarityType(scope.row.card_id)" size="small">
						{{ getCardRarityLabel(scope.row.card_id) }}
					</el-tag>
				</template>
			</el-table-column>
			<el-table-column label="来源" width="100">
				<template #default="scope">
					{{ getSourceTypeLabel(scope.row.source_type) }}
				</template>
			</el-table-column>
			<el-table-column label="积分" width="100" align="center">
				<template #default="scope">
					<span v-if="scope.row.is_duplicate && scope.row.points_gained">
						<el-tag type="success">+{{ scope.row.points_gained }}</el-tag>
					</span>
					<span v-else>-</span>
				</template>
			</el-table-column>
			<el-table-column label="特殊情况" width="120">
				<template #default="scope">
					<el-tag v-if="scope.row.is_guaranteed" type="warning" effect="dark" size="small">保底</el-tag>
					<el-tag v-else-if="scope.row.is_special_reward" type="danger" effect="dark" size="small">特殊</el-tag>
					<el-tag v-else-if="scope.row.is_duplicate" type="info" effect="dark" size="small">重复</el-tag>
					<span v-else>-</span>
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
	</div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from "vue";
import { getUserBlindBoxRecords, getUserStats } from "@/api/blind-box-record";
import { getActiveBlindBoxes } from "@/api/blind-box";
import { ElMessage } from "element-plus";

const props = defineProps({
	userId: {
		type: Number,
		required: true,
	},
});

// 数据状态
const loading = ref(true);
const records = ref<any[]>([]);
const stats = ref<any>({});
const blindBoxes = ref<any[]>([]);

// 分页状态
const currentPage = ref(1);
const pageSize = ref(10);
const totalRecords = ref(0);

// 筛选状态
const filterBoxId = ref("");
const filterSourceType = ref("");
const filterSpecialType = ref("");

// 计算属性：筛选记录
const filteredRecords = computed(() => {
	let filtered = [...records.value];

	// 按盲盒类型筛选
	if (filterBoxId.value) {
		filtered = filtered.filter((record) => record.blind_box_id === Number(filterBoxId.value));
	}

	// 按来源类型筛选
	if (filterSourceType.value) {
		filtered = filtered.filter((record) => record.source_type === filterSourceType.value);
	}

	// 按特殊类型筛选
	if (filterSpecialType.value) {
		if (filterSpecialType.value === "guaranteed") {
			filtered = filtered.filter((record) => record.is_guaranteed);
		} else if (filterSpecialType.value === "special") {
			filtered = filtered.filter((record) => record.is_special_reward);
		} else if (filterSpecialType.value === "duplicate") {
			filtered = filtered.filter((record) => record.is_duplicate);
		}
	}

	// totalRecords.value = filtered.length;

	// 分页
	const start = (currentPage.value - 1) * pageSize.value;
	const end = start + pageSize.value;
	return filtered.slice(start, end);
});

// 监听用户ID变化，重新加载数据
watch(
	() => props.userId,
	(newVal) => {
		if (newVal) {
			loadUserBlindBoxRecords();
			loadUserStats();
			loadBlindBoxes();
		}
	},
);

// 方法
const loadUserBlindBoxRecords = async () => {
	if (!props.userId) return;

	loading.value = true;
	try {
		const response = await getUserBlindBoxRecords(props.userId, 1000);
		records.value = response;
		totalRecords.value = response.length;
	} catch (error) {
		console.error("加载用户盲盒记录失败", error);
		ElMessage.error("加载用户盲盒记录失败");
	} finally {
		loading.value = false;
	}
};

const loadUserStats = async () => {
	if (!props.userId) return;

	try {
		const response = await getUserStats(props.userId);
		stats.value = response;
	} catch (error) {
		console.error("加载用户盲盒统计信息失败", error);
	}
};

const loadBlindBoxes = async () => {
	try {
		const response = await getActiveBlindBoxes();
		blindBoxes.value = response;
	} catch (error) {
		console.error("加载盲盒列表失败", error);
	}
};

const getBlindBoxName = (boxId: number): string => {
	const box = blindBoxes.value.find((box) => box.id === boxId);
	return box?.name || `盲盒 #${boxId}`;
};

const getCardName = (cardId: number): string => {
	const record = records.value.find((r) => r.card_id === cardId);
	return record?.card_detail?.name || `卡牌 #${cardId}`;
};

const getCardImageUrl = (cardId: number): string => {
	const record = records.value.find((r) => r.card_id === cardId);
	return record?.card_detail?.image_url || "";
};

const getCardRarityLabel = (cardId: number): string => {
	const record = records.value.find((r) => r.card_id === cardId);
	const rarity = record?.card_detail?.rarity;

	if (!rarity) return "未知";

	switch (rarity) {
		case 1:
			return "普通";
		case 2:
			return "稀有";
		case 3:
			return "史诗";
		case 4:
			return "传说";
		case 5:
			return "SSR";
		default:
			return "未知";
	}
};

const getCardRarityType = (cardId: number): any => {
	const record = records.value.find((r) => r.card_id === cardId);
	const rarity = record?.card_detail?.rarity;

	if (!rarity) return "";

	switch (rarity) {
		case 1:
			return "info";
		case 2:
			return "success";
		case 3:
			return "warning";
		case 4:
			return "danger";
		case 5:
			return "danger";
		default:
			return "";
	}
};

const getSourceTypeLabel = (sourceType: any): any => {
	switch (sourceType) {
		case "purchase":
			return "购买";
		case "reward":
			return "奖励";
		case "gift":
			return "礼物";
		default:
			return sourceType;
	}
};

const formatDateTime = (dateTime: string): string => {
	if (!dateTime) return "";
	const date = new Date(dateTime);
	return date.toLocaleString();
};

const formatRate = (rate: number): string => {
	if (rate === undefined || rate === null) return "0%";
	return `${(rate * 100).toFixed(1)}%`;
};

const handleFilter = () => {
	currentPage.value = 1; // 重置为第一页
};

const handleSizeChange = (val: number) => {
	pageSize.value = val;
	currentPage.value = 1;
};

const handleCurrentChange = (val: number) => {
	currentPage.value = val;
};

// 生命周期钩子
onMounted(() => {
	if (props.userId) {
		loadUserBlindBoxRecords();
		loadUserStats();
		loadBlindBoxes();
	}
});
</script>

<style scoped>
.user-blind-boxes-container {
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

.card-info {
	display: flex;
	align-items: center;
	gap: 10px;
}

.card-name {
	font-size: 14px;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
	max-width: 150px;
}

.pagination-section {
	margin-top: 20px;
	display: flex;
	justify-content: center;
}
</style>
