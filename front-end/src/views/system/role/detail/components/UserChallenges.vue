<template>
	<div class="user-challenges-container">
		<div class="stats-cards">
			<el-card class="stats-card">
				<template #header>
					<div class="card-header">
						<span>挑战统计</span>
					</div>
				</template>
				<div class="stats-content">
					<div class="stat-item">
						<div class="stat-value">{{ stats.totalChallenges }}</div>
						<div class="stat-label">总挑战次数</div>
					</div>
					<div class="stat-item">
						<div class="stat-value">{{ stats.totalPoints }}</div>
						<div class="stat-label">获得积分</div>
					</div>
					<div class="stat-item">
						<div class="stat-value">{{ stats.avgPointsPerChallenge.toFixed(1) }}</div>
						<div class="stat-label">平均积分/次</div>
					</div>
				</div>
			</el-card>
		</div>

		<div class="filter-row">
			<el-select v-model="filterStatus" placeholder="筛选状态" clearable @change="handleFilter">
				<el-option label="全部状态" value="" />
				<el-option label="进行中" value="in_progress" />
				<el-option label="已完成" value="completed" />
			</el-select>

			<el-select v-model="sortBy" placeholder="排序方式" @change="handleSort">
				<el-option label="开始时间 (新→旧)" value="start_time_desc" />
				<el-option label="开始时间 (旧→新)" value="start_time_asc" />
				<el-option label="获得积分 (多→少)" value="points_desc" />
				<el-option label="获得积分 (少→多)" value="points_asc" />
			</el-select>
		</div>

		<el-table
			v-loading="loading"
			:data="filteredChallenges"
			style="width: 100%; margin-top: 20px"
			:header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
		>
			<el-table-column label="卡牌" width="120">
				<template #default="scope">
					<div class="card-info">
						<el-avatar shape="square" :size="40" :src="getCardImageUrl(scope.row.card_id)">
							{{ getCardName(scope.row.card_id).charAt(0) }}
						</el-avatar>
						<div class="card-name">{{ getCardName(scope.row.card_id) }}</div>
					</div>
				</template>
			</el-table-column>

			<el-table-column label="开始时间" width="180">
				<template #default="scope">
					{{ formatDate(scope.row.start_time) }}
				</template>
			</el-table-column>

			<el-table-column label="结束时间" width="180">
				<template #default="scope">
					{{ scope.row.end_time ? formatDate(scope.row.end_time) : "进行中" }}
				</template>
			</el-table-column>

			<el-table-column label="持续时间">
				<template #default="scope">
					{{ calculateDuration(scope.row.start_time, scope.row.end_time) }}
				</template>
			</el-table-column>

			<el-table-column label="获得积分" width="120">
				<template #default="scope">
					<el-tag v-if="scope.row.points_earned" type="success"> +{{ scope.row.points_earned }} </el-tag>
					<el-tag v-else type="info">未结算</el-tag>
				</template>
			</el-table-column>

			<el-table-column label="状态" width="100">
				<template #default="scope">
					<el-tag v-if="scope.row.end_time" type="success">已完成</el-tag>
					<el-tag v-else type="warning">进行中</el-tag>
				</template>
			</el-table-column>
		</el-table>

		<div class="pagination-container">
			<el-pagination
				v-model:currentPage="currentPage"
				v-model:page-size="pageSize"
				:page-sizes="[10, 20, 50, 100]"
				layout="total, sizes, prev, pager, next, jumper"
				:total="filteredChallenges.length"
				@size-change="handleSizeChange"
				@current-change="handleCurrentChange"
			/>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from "vue";
import { getUserUsageTypeRecords, getUserUsageStatistics } from "@/api/card-usage-record";
import { ElMessage } from "element-plus";
import { formatDate } from "@/utils";
const props = defineProps({
	userId: {
		type: Number,
		required: true,
	},
});

// 数据状态
const loading = ref(true);
const challenges = ref<any[]>([]);
const stats = ref({
	totalChallenges: 0,
	totalPoints: 0,
	avgPointsPerChallenge: 0,
});

// 分页状态
const currentPage = ref(1);
const pageSize = ref(10);

// 筛选和排序状态
const filterStatus = ref("");
const sortBy = ref("start_time_desc");

// 计算属性
const filteredChallenges = computed(() => {
	let filtered = [...challenges.value];

	// 根据状态筛选
	if (filterStatus.value === "in_progress") {
		filtered = filtered.filter((challenge) => !challenge.end_time);
	} else if (filterStatus.value === "completed") {
		filtered = filtered.filter((challenge) => challenge.end_time);
	}

	// 根据排序方式排序
	filtered.sort((a, b) => {
		switch (sortBy.value) {
			case "start_time_desc":
				return new Date(b.start_time).getTime() - new Date(a.start_time).getTime();
			case "start_time_asc":
				return new Date(a.start_time).getTime() - new Date(b.start_time).getTime();
			case "points_desc":
				return (b.points_earned || 0) - (a.points_earned || 0);
			case "points_asc":
				return (a.points_earned || 0) - (b.points_earned || 0);
			default:
				return 0;
		}
	});

	return filtered;
});

// 监听用户ID变化，重新加载数据
watch(
	() => props.userId,
	(newVal) => {
		if (newVal) {
			loadUserChallenges();
			loadUserStats();
		}
	},
);

// 方法
const loadUserChallenges = async () => {
	if (!props.userId) return;

	loading.value = true;
	try {
		// 获取AI挑战类型的使用记录
		const response = await getUserUsageTypeRecords(props.userId, "ai_challenge", 1000);
		challenges.value = response;
	} catch (error) {
		console.error("加载用户挑战记录失败", error);
		ElMessage.error("加载用户挑战记录失败");
	} finally {
		loading.value = false;
	}
};

const loadUserStats = async () => {
	if (!props.userId) return;

	try {
		const response = await getUserUsageStatistics(props.userId);

		const totalChallenges = response.type_counts?.ai_challenge || 0;
		const totalPoints = calculateTotalChallengePoints(challenges.value);

		stats.value = {
			totalChallenges,
			totalPoints,
			avgPointsPerChallenge: totalChallenges > 0 ? totalPoints / totalChallenges : 0,
		};
	} catch (error) {
		console.error("加载用户统计信息失败", error);
	}
};

const calculateTotalChallengePoints = (challenges: any[]) => {
	return challenges.reduce((sum, challenge) => sum + (challenge.points_earned || 0), 0);
};

const getCardName = (cardId: number): string => {
	const challenge = challenges.value.find((c) => c.card_id === cardId);
	return challenge?.card_detail?.name || `卡牌 #${cardId}`;
};

const getCardImageUrl = (cardId: number): string => {
	const challenge = challenges.value.find((c) => c.card_id === cardId);
	return challenge?.card_detail?.image_url || "";
};

const calculateDuration = (startTime: string, endTime: string | null): string => {
	if (!endTime) return "进行中";

	const start = new Date(startTime).getTime();
	const end = new Date(endTime).getTime();
	const diff = end - start;

	// 小于1小时
	if (diff < 3600000) {
		const minutes = Math.floor(diff / 60000);
		return `${minutes}分钟`;
	}
	// 小于1天
	else if (diff < 86400000) {
		const hours = Math.floor(diff / 3600000);
		const minutes = Math.floor((diff % 3600000) / 60000);
		return `${hours}小时${minutes}分钟`;
	}
	// 大于1天
	else {
		const days = Math.floor(diff / 86400000);
		const hours = Math.floor((diff % 86400000) / 3600000);
		return `${days}天${hours}小时`;
	}
};

const handleFilter = () => {
	currentPage.value = 1; // 重置分页到第一页
};

const handleSort = () => {
	// 排序操作已由 computed 属性处理
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
		loadUserChallenges();
		loadUserStats();
	}
});
</script>

<style scoped>
.user-challenges-container {
	padding: 20px 0;
}

.stats-cards {
	display: flex;
	margin-bottom: 20px;
	gap: 20px;
}

.stats-card {
	flex: 1;
}

.card-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.stats-content {
	display: flex;
	justify-content: space-around;
	text-align: center;
}

.stat-item {
	padding: 10px;
}

.stat-value {
	font-size: 24px;
	font-weight: bold;
	color: #409eff;
	margin-bottom: 5px;
}

.stat-label {
	font-size: 12px;
	color: #909399;
}

.filter-row {
	display: flex;
	justify-content: space-between;
	margin-bottom: 20px;
}

.card-info {
	display: flex;
	align-items: center;
	gap: 10px;
}

.card-name {
	font-size: 12px;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
	max-width: 100px;
}

.pagination-container {
	margin-top: 20px;
	display: flex;
	justify-content: flex-end;
}
</style>
