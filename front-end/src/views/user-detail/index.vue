<template>
	<div class="user-detail-container">
		<div class="header fade-in">
			<h1 class="title">User Detail Management</h1>
			<div class="header-actions">
				<el-button @click="loadStatistics">
					<el-icon><Refresh /></el-icon>
					Refresh Statistics
				</el-button>
			</div>
		</div>

		<!-- 统计卡片 -->
		<div class="statistics-cards fade-in-up">
			<el-row :gutter="20">
				<el-col :span="6" :class="{ 'animated-card': true }" style="animation-delay: 0ms">
					<el-card class="stat-card">
						<template #header>
							<div class="card-header">
								<span>Total Users</span>
								<el-tooltip content="Total number of user detail records in the system" placement="top">
									<el-icon><InfoFilled /></el-icon>
								</el-tooltip>
							</div>
						</template>
						<div class="card-content">
							<div class="card-value">{{ formatNumber(animatedStats.total_users) }}</div>
							<div class="card-unit">people</div>
						</div>
					</el-card>
				</el-col>
				<el-col :span="6" :class="{ 'animated-card': true }" style="animation-delay: 100ms">
					<el-card class="stat-card">
						<template #header>
							<div class="card-header">
								<span>Total Points in System</span>
								<el-tooltip content="Sum of all user points" placement="top">
									<el-icon><InfoFilled /></el-icon>
								</el-tooltip>
							</div>
						</template>
						<div class="card-content">
							<div class="card-value">{{ formatNumber(animatedStats.total_points_in_system) }}</div>
							<div class="card-unit">points</div>
						</div>
					</el-card>
				</el-col>
				<el-col :span="6" :class="{ 'animated-card': true }" style="animation-delay: 200ms">
					<el-card class="stat-card">
						<template #header>
							<div class="card-header">
								<span>Average Challenge Success Rate</span>
								<el-tooltip content="Average success rate of all user AI challenges" placement="top">
									<el-icon><InfoFilled /></el-icon>
								</el-tooltip>
							</div>
						</template>
						<div class="card-content">
							<div class="card-value">{{ formatNumber(animatedStats.average_challenge_success_rate, 1) }}</div>
							<div class="card-unit">%</div>
						</div>
					</el-card>
				</el-col>
				<el-col :span="6" :class="{ 'animated-card': true }" style="animation-delay: 300ms">
					<el-card class="stat-card">
						<template #header>
							<div class="card-header">
								<span>Total Cards</span>
								<el-tooltip content="Total number of cards owned by all users in the system" placement="top">
									<el-icon><InfoFilled /></el-icon>
								</el-tooltip>
							</div>
						</template>
						<div class="card-content">
							<div class="card-value">{{ formatNumber(animatedStats.total_cards_in_system) }}</div>
							<div class="card-unit">cards</div>
						</div>
					</el-card>
				</el-col>
			</el-row>
		</div>

		<!-- 搜索栏 -->
		<div class="search-box fade-in-up" style="animation-delay: 400ms">
			<el-row :gutter="20">
				<el-col :span="6">
					<el-input
						v-model="filters.user_id"
						placeholder="User ID"
						clearable
						@change="handleSearch"
						class="filter-input"
					/>
				</el-col>
				<el-col :span="6">
					<el-input
						v-model="filters.min_total_points"
						placeholder="Minimum Total Points"
						clearable
						@change="handleSearch"
						class="filter-input"
						type="number"
					/>
				</el-col>
				<el-col :span="6">
					<el-input
						v-model="filters.min_login_count"
						placeholder="Minimum Login Count"
						clearable
						@change="handleSearch"
						class="filter-input"
						type="number"
					/>
				</el-col>
				<el-col :span="6">
					<el-button type="primary" @click="handleSearch">Search</el-button>
					<el-button @click="resetFilters">Reset</el-button>
					<el-button @click="showRankingDialog = true">Ranking</el-button>
				</el-col>
			</el-row>
		</div>

		<!-- 数据表格 -->
		<div class="table-container fade-in-up" style="animation-delay: 500ms">
			<el-table
				v-loading="loading"
				:data="tableData"
				style="width: 100%"
				border
				stripe
				:highlight-current-row="true"
				@row-click="handleRowClick"
			>
				<el-table-column prop="id" label="ID" width="80" />
				<el-table-column prop="user_id" label="User ID" width="100">
					<template #default="scope">
						<router-link :to="'/system/role/detail/' + scope.row.user_id" class="user-link">
							{{ scope.row.user_id }}
						</router-link>
					</template>
				</el-table-column>
				<el-table-column prop="total_points" label="Total Points" width="120" sortable>
					<template #default="scope">
						<span class="points-value">{{ formatNumber(scope.row.total_points) }}</span>
					</template>
				</el-table-column>
				<el-table-column prop="available_points" label="Available Points" width="120" sortable>
					<template #default="scope">
						<span class="available-points">{{ formatNumber(scope.row.available_points) }}</span>
					</template>
				</el-table-column>
				<el-table-column prop="total_login_count" label="Login Count" width="100" sortable />
				<el-table-column label="Challenge Stats" width="150">
					<template #default="scope">
						<div class="challenge-stats">
							<div>Total: {{ scope.row.total_ai_challenge_count }}</div>
							<div>Success: {{ scope.row.total_ai_challenge_success_count }}</div>
							<div v-if="scope.row.challenge_success_rate !== null" class="success-rate">
								Success Rate: {{ scope.row.challenge_success_rate }}%
							</div>
						</div>
					</template>
				</el-table-column>
				<el-table-column prop="total_card_count" label="Card Count" width="100" />
				<el-table-column prop="total_blind_box_opened" label="Blind Box Count" width="100" />
				<el-table-column prop="last_active_time" label="Last Active" width="180">
					<template #default="scope">
						{{ formatDate(scope.row.last_active_time) }}
					</template>
				</el-table-column>
				<el-table-column label="Actions" fixed="right">
					<template #default="{ row }">
						<el-button-group>
							<el-button type="success" link @click="showActionsDialog(row)">
								<el-icon><Setting /></el-icon>
								Actions
							</el-button>
							<el-button type="danger" link @click="handleDelete(row)">
								<el-icon><Delete /></el-icon>
								Delete
							</el-button>
						</el-button-group>
					</template>
				</el-table-column>
			</el-table>
		</div>

		<!-- 分页 -->
		<div class="pagination">
			<el-pagination
				v-model:current-page="currentPage"
				v-model:page-size="pageSize"
				:total="total"
				:page-sizes="[10, 20, 50, 100]"
				layout="total, sizes, prev, pager, next"
				@size-change="handleSizeChange"
				@current-change="handleCurrentChange"
			/>
		</div>

		<!-- 用户操作对话框 -->
		<el-dialog v-model="showUserActionsDialog" title="User Game Actions" width="500px">
			<div class="user-actions">
				<h4>User ID: {{ currentUser?.user_id }}</h4>
				<el-divider />

				<div class="action-item">
					<h5>Points Action</h5>
					<el-row :gutter="10">
						<el-col :span="8">
							<el-input v-model.number="pointsChange" placeholder="Points Amount" type="number" />
						</el-col>
						<el-col :span="8">
							<el-button type="success" @click="handlePointsAction(true)" :loading="actionLoading">
								Add Points
							</el-button>
						</el-col>
						<el-col :span="8">
							<el-button type="warning" @click="handlePointsAction(false)" :loading="actionLoading">
								Consume Points
							</el-button>
						</el-col>
					</el-row>
				</div>

				<el-divider />

				<div class="action-item">
					<h5>Challenge Action</h5>
					<el-row :gutter="10">
						<el-col :span="12">
							<el-button type="primary" @click="handleChallengeAction(true)" :loading="actionLoading">
								Success Challenge
							</el-button>
						</el-col>
						<el-col :span="12">
							<el-button type="info" @click="handleChallengeAction(false)" :loading="actionLoading">
								Fail Challenge
							</el-button>
						</el-col>
					</el-row>
				</div>

				<el-divider />

				<div class="action-item">
					<h5>Other Actions</h5>
					<el-row :gutter="10">
						<el-col :span="8">
							<el-button @click="handleLoginAction" :loading="actionLoading"> 模拟登录 </el-button>
						</el-col>
						<el-col :span="8">
							<el-button @click="handleBlindBoxAction" :loading="actionLoading"> Open Blind Box </el-button>
						</el-col>
						<el-col :span="8">
							<el-input v-model.number="cardChange" placeholder="Card Count Change" type="number" size="small" />
						</el-col>
					</el-row>
					<el-row :gutter="10" style="margin-top: 10px">
						<el-col :span="12">
							<el-button @click="handleCardAction" :loading="actionLoading" :disabled="!cardChange">
								Update Card Count
							</el-button>
						</el-col>
					</el-row>
				</div>
			</div>
		</el-dialog>

		<!-- 排行榜对话框 -->
		<el-dialog v-model="showRankingDialog" title="User Ranking" width="800px">
			<el-tabs v-model="activeRankingTab">
				<el-tab-pane label="Points Ranking" name="points">
					<el-table :data="pointsRanking" style="width: 100%">
						<el-table-column label="排名" type="index" width="80" />
						<el-table-column prop="user_id" label="用户ID" width="100" />
						<el-table-column prop="total_points" label="总积分" sortable />
						<el-table-column prop="available_points" label="可用积分" />
						<el-table-column prop="challenge_success_rate" label="挑战成功率" width="120">
							<template #default="scope"> {{ scope.row.challenge_success_rate }}% </template>
						</el-table-column>
					</el-table>
				</el-tab-pane>
				<el-tab-pane label="挑战排行榜" name="challenges">
					<el-table :data="challengesRanking" style="width: 100%">
						<el-table-column label="排名" type="index" width="80" />
						<el-table-column prop="user_id" label="用户ID" width="100" />
						<el-table-column prop="total_ai_challenge_count" label="挑战次数" sortable />
						<el-table-column prop="total_ai_challenge_success_count" label="成功次数" />
						<el-table-column prop="challenge_success_rate" label="成功率" width="100">
							<template #default="scope"> {{ scope.row.challenge_success_rate }}% </template>
						</el-table-column>
					</el-table>
				</el-tab-pane>
				<el-tab-pane label="活跃排行榜" name="active">
					<el-table :data="activeRanking" style="width: 100%">
						<el-table-column label="排名" type="index" width="80" />
						<el-table-column prop="user_id" label="用户ID" width="100" />
						<el-table-column prop="total_login_count" label="登录次数" sortable />
						<el-table-column prop="last_active_time" label="最后活跃时间" width="180">
							<template #default="scope">
								{{ formatDate(scope.row.last_active_time) }}
							</template>
						</el-table-column>
					</el-table>
				</el-tab-pane>
			</el-tabs>
		</el-dialog>
	</div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { InfoFilled, Refresh, Setting, Delete } from "@element-plus/icons-vue";
import {
	getUserDetailList,
	deleteUserDetail,
	getUserDetailStatistics,
	updateLoginCount,
	updateChallengeStats,
	updatePoints,
	updateCardCount,
	updateBlindBoxCount,
	type UserDetailResponse,
	type UserDetailStatistics,
} from "@/api/userDetail";
import { formatDate } from "@/utils";

// 数据定义
const loading = ref(false);
const actionLoading = ref(false);
const tableData = ref<UserDetailResponse[]>([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(10);

// 统计数据
const animatedStats = reactive({
	total_users: 0,
	total_points_in_system: 0,
	average_challenge_success_rate: 0,
	total_cards_in_system: 0,
});

const statistics = reactive<UserDetailStatistics>({
	total_users: 0,
	total_points_in_system: 0,
	average_points_per_user: 0,
	total_challenges: 0,
	average_challenge_success_rate: 0,
	total_cards_in_system: 0,
	total_blind_boxes_opened: 0,
	most_active_users: [],
});

// 过滤条件
const filters = reactive({
	user_id: "",
	min_total_points: "",
	min_login_count: "",
});

// 对话框状态
const showUserActionsDialog = ref(false);
const showRankingDialog = ref(false);

// 用户操作相关
const currentUser = ref<UserDetailResponse | null>(null);
const pointsChange = ref(0);
const cardChange = ref(0);

// 排行榜数据
const activeRankingTab = ref("points");
const pointsRanking = ref<UserDetailResponse[]>([]);
const challengesRanking = ref<UserDetailResponse[]>([]);
const activeRanking = ref<UserDetailResponse[]>([]);

// 数字动画
function animateValue(obj: any, prop: string, start: number, end: number, duration: number) {
	const startTime = performance.now();

	function updateValue(currentTime: number) {
		const elapsedTime = currentTime - startTime;
		const progress = Math.min(elapsedTime / duration, 1);
		const easeProgress = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
		const currentValue = start + (end - start) * easeProgress;

		obj[prop] = currentValue;

		if (progress < 1) {
			requestAnimationFrame(updateValue);
		}
	}

	requestAnimationFrame(updateValue);
}

function formatNumber(num: any, decimals: number = 0) {
	if (num === undefined || num === null) return "0";
	if (typeof num === "string") {
		num = parseFloat(num);
	}
	if (decimals > 0) {
		return num.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
	}
	return Math.round(num)
		.toString()
		.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// 处理函数
function handleRowClick(row: UserDetailResponse) {
	// 可以实现行点击后的详情查看
	ElMessage.info(`点击了用户ID: ${row.user_id}`);
}

function handleSearch() {
	currentPage.value = 1;
	loadUserDetails();
}

function resetFilters() {
	filters.user_id = "";
	filters.min_total_points = "";
	filters.min_login_count = "";
	handleSearch();
}

function handleSizeChange(val: number) {
	pageSize.value = val;
	loadUserDetails();
}

function handleCurrentChange(val: number) {
	currentPage.value = val;
	loadUserDetails();
}

function showActionsDialog(row: UserDetailResponse) {
	currentUser.value = row;
	pointsChange.value = 0;
	cardChange.value = 0;
	showUserActionsDialog.value = true;
}

function handleDelete(row: UserDetailResponse) {
	ElMessageBox.confirm(`确定要删除用户 ${row.user_id} 的详情记录吗？此操作不可恢复。`, "警告", {
		confirmButtonText: "确定",
		cancelButtonText: "取消",
		type: "warning",
	})
		.then(() => {
			deleteUserDetail(row.id)
				.then(() => {
					ElMessage.success("删除成功");
					loadUserDetails();
				})
				.catch((err) => {
					ElMessage.error(`删除失败: ${err.message}`);
				});
		})
		.catch(() => {
			// 取消删除
		});
}

// 用户操作函数
async function handlePointsAction(isEarned: boolean) {
	if (!currentUser.value || pointsChange.value <= 0) {
		ElMessage.warning("请输入有效的积分数量");
		return;
	}

	actionLoading.value = true;
	try {
		await updatePoints(currentUser.value.user_id, pointsChange.value, isEarned);
		ElMessage.success(`${isEarned ? "获得" : "消费"}积分成功`);
		pointsChange.value = 0;
		loadUserDetails();
	} catch (err: any) {
		ElMessage.error(`操作失败: ${err.message}`);
	} finally {
		actionLoading.value = false;
	}
}

async function handleChallengeAction(success: boolean) {
	if (!currentUser.value) return;

	actionLoading.value = true;
	try {
		await updateChallengeStats(currentUser.value.user_id, success);
		ElMessage.success(`挑战${success ? "成功" : "失败"}记录已更新`);
		loadUserDetails();
	} catch (err: any) {
		ElMessage.error(`操作失败: ${err.message}`);
	} finally {
		actionLoading.value = false;
	}
}

async function handleLoginAction() {
	if (!currentUser.value) return;

	actionLoading.value = true;
	try {
		await updateLoginCount(currentUser.value.user_id);
		ElMessage.success("登录次数已更新");
		loadUserDetails();
	} catch (err: any) {
		ElMessage.error(`操作失败: ${err.message}`);
	} finally {
		actionLoading.value = false;
	}
}

async function handleBlindBoxAction() {
	if (!currentUser.value) return;

	actionLoading.value = true;
	try {
		await updateBlindBoxCount(currentUser.value.user_id);
		ElMessage.success("盲盒开启次数已更新");
		loadUserDetails();
	} catch (err: any) {
		ElMessage.error(`操作失败: ${err.message}`);
	} finally {
		actionLoading.value = false;
	}
}

async function handleCardAction() {
	if (!currentUser.value || cardChange.value === 0) {
		ElMessage.warning("请输入有效的卡牌数量变化");
		return;
	}

	actionLoading.value = true;
	try {
		await updateCardCount(currentUser.value.user_id, cardChange.value);
		ElMessage.success("卡牌数量已更新");
		cardChange.value = 0;
		loadUserDetails();
	} catch (err: any) {
		ElMessage.error(`操作失败: ${err.message}`);
	} finally {
		actionLoading.value = false;
	}
}

// 数据加载
function loadUserDetails() {
	loading.value = true;
	const params = {
		page: currentPage.value,
		size: pageSize.value,
		user_id: filters.user_id ? parseInt(filters.user_id) : undefined,
		min_total_points: filters.min_total_points ? parseInt(filters.min_total_points) : undefined,
		min_login_count: filters.min_login_count ? parseInt(filters.min_login_count) : undefined,
	};

	getUserDetailList(params)
		.then((res) => {
			tableData.value = res.items || [];
			total.value = res.total || 0;
		})
		.catch((err) => {
			ElMessage.error(`加载用户详情失败: ${err.message}`);
		})
		.finally(() => {
			loading.value = false;
		});
}

function loadStatistics() {
	getUserDetailStatistics()
		.then((res) => {
			Object.assign(statistics, res);

			// 动画显示统计数据
			animateValue(animatedStats, "total_users", 0, statistics.total_users, 1000);
			animateValue(animatedStats, "total_points_in_system", 0, statistics.total_points_in_system, 1000);
			animateValue(animatedStats, "average_challenge_success_rate", 0, statistics.average_challenge_success_rate, 1000);
			animateValue(animatedStats, "total_cards_in_system", 0, statistics.total_cards_in_system, 1000);
		})
		.catch((err) => {
			ElMessage.error(`加载统计数据失败: ${err.message}`);
		});
}

// 初始化
onMounted(() => {
	loadUserDetails();
	loadStatistics();
});
</script>

<style lang="scss" scoped>
.user-detail-container {
	padding: 20px;
	min-height: 100vh;

	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 20px;

		.title {
			font-size: 24px;
			font-weight: 600;
			margin: 0;
		}

		.header-actions {
			display: flex;
			gap: 10px;
		}
	}

	.statistics-cards {
		margin-bottom: 20px;

		.stat-card {
			height: 100%;
			transition: all 0.3s ease;
			box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);

			&:hover {
				transform: translateY(-5px);
				box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
			}

			.card-header {
				display: flex;
				align-items: center;
				font-weight: 600;

				.el-icon {
					margin-left: 5px;
					color: #909399;
				}
			}

			.card-content {
				text-align: center;
				padding: 15px 0;

				.card-value {
					font-size: 28px;
					font-weight: 700;
					color: #409eff;
					margin-bottom: 5px;
				}

				.card-unit {
					font-size: 14px;
					color: #606266;
				}
			}
		}
	}

	.search-box {
		margin-bottom: 20px;
		padding: 15px;
		background-color: #f5f7fa;
		border-radius: 4px;

		.filter-input {
			width: 100%;
		}
	}

	.table-container {
		margin-bottom: 20px;

		.points-value {
			color: #67c23a;
			font-weight: bold;
		}

		.available-points {
			color: #409eff;
			font-weight: bold;
		}

		.challenge-stats {
			font-size: 12px;
			line-height: 1.4;

			.success-rate {
				color: #67c23a;
				font-weight: bold;
			}
		}
	}

	.pagination {
		display: flex;
		justify-content: flex-end;
		margin-top: 20px;
	}

	.user-actions {
		.action-item {
			margin: 15px 0;

			h5 {
				margin: 10px 0;
				color: #303133;
			}
		}
	}

	.user-link {
		color: #409eff;
		text-decoration: none;
		font-weight: 500;

		&:hover {
			text-decoration: underline;
			color: #66b1ff;
		}
	}
}

// 动画效果
.fade-in {
	animation: fadeIn 0.5s ease-out forwards;
}

.fade-in-up {
	animation: fadeInUp 0.5s ease-out forwards;
	opacity: 0;
}

.animated-card {
	animation: fadeInUp 0.5s ease-out forwards;
	opacity: 0;
}

@keyframes fadeIn {
	from {
		opacity: 0;
	}
	to {
		opacity: 1;
	}
}

@keyframes fadeInUp {
	from {
		opacity: 0;
		transform: translateY(20px);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}
</style>
