<template>
	<div class="task-game-sessions">
		<div class="header fade-in">
			<h1 class="title">Game Task Sessions</h1>
			<div class="date-selector">
				<el-date-picker
					v-model="dateRange"
					type="daterange"
					range-separator="to"
					start-placeholder="Start Date"
					end-placeholder="End Date"
					:shortcuts="dateShortcuts"
					@change="handleDateChange"
				/>
			</div>
		</div>

		<!-- Statistics cards -->
		<div class="statistics-cards fade-in-up">
			<el-row :gutter="20">
				<el-col :span="6" :class="{ 'animated-card': true }" style="animation-delay: 0ms">
					<el-card class="stat-card">
						<template #header>
							<div class="card-header">
								<span>Total Sessions</span>
								<el-tooltip content="Total number of all game task sessions" placement="top">
									<el-icon><InfoFilled /></el-icon>
								</el-tooltip>
							</div>
						</template>
						<div class="card-content">
							<div class="card-value">{{ formatNumber(animatedStats.total_sessions) }}</div>
							<div class="card-unit">sessions</div>
						</div>
					</el-card>
				</el-col>
				<el-col :span="6" :class="{ 'animated-card': true }" style="animation-delay: 100ms">
					<el-card class="stat-card">
						<template #header>
							<div class="card-header">
								<span>Active Sessions</span>
								<el-tooltip content="Number of current ongoing sessions" placement="top">
									<el-icon><InfoFilled /></el-icon>
								</el-tooltip>
							</div>
						</template>
						<div class="card-content">
							<div class="card-value">{{ formatNumber(animatedStats.in_progress_sessions) }}</div>
							<div class="card-unit">sessions</div>
						</div>
					</el-card>
				</el-col>
				<el-col :span="6" :class="{ 'animated-card': true }" style="animation-delay: 200ms">
					<el-card class="stat-card">
						<template #header>
							<div class="card-header">
								<span>Completed Sessions</span>
								<el-tooltip content="Number of completed sessions" placement="top">
									<el-icon><InfoFilled /></el-icon>
								</el-tooltip>
							</div>
						</template>
						<div class="card-content">
							<div class="card-value">{{ formatNumber(animatedStats.completed_sessions) }}</div>
							<div class="card-unit">sessions</div>
						</div>
					</el-card>
				</el-col>
				<el-col :span="6" :class="{ 'animated-card': true }" style="animation-delay: 300ms">
					<el-card class="stat-card">
						<template #header>
							<div class="card-header">
								<span>Average Rounds</span>
								<el-tooltip content="Average number of rounds per session" placement="top">
									<el-icon><InfoFilled /></el-icon>
								</el-tooltip>
							</div>
						</template>
						<div class="card-content">
							<div class="card-value">{{ formatNumber(animatedStats.average_rounds, 1) }}</div>
							<div class="card-unit">rounds</div>
						</div>
					</el-card>
				</el-col>
			</el-row>
		</div>

		<!-- Search bar -->
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
						v-model="filters.task_id"
						placeholder="Task ID"
						clearable
						@change="handleSearch"
						class="filter-input"
					/>
				</el-col>
				<el-col :span="6">
					<el-select
						v-model="filters.status"
						placeholder="Session Status"
						clearable
						@change="handleSearch"
						class="filter-select"
					>
						<el-option label="All" value="" />
						<el-option label="In Progress" value="in_progress" />
						<el-option label="Completed" value="completed" />
						<el-option label="Aborted" value="aborted" />
						<el-option label="Timeout" value="timeout" />
					</el-select>
				</el-col>
				<el-col :span="6">
					<el-button type="primary" @click="handleSearch">Search</el-button>
					<el-button @click="resetFilters">Reset</el-button>
				</el-col>
			</el-row>
		</div>

		<!-- Data table -->
		<div class="table-container fade-in-up" style="animation-delay: 500ms">
			<el-table
				v-loading="loading"
				:data="tableData"
				style="width: 100%"
				border
				stripe
				:highlight-current-row="true"
				@row-click="handleRowClick"
				:row-class-name="tableRowClassName"
			>
				<el-table-column prop="id" label="Session ID" width="220" show-overflow-tooltip />
				<el-table-column prop="user_id" label="User ID" width="150" show-overflow-tooltip />
				<el-table-column prop="task_id" label="Task ID" width="150" show-overflow-tooltip />
				<el-table-column prop="subtask_id" label="Subtask ID" width="150" show-overflow-tooltip />
				<el-table-column prop="status" label="Status" width="100">
					<template #default="scope">
						<el-tag :type="getStatusType(scope.row.status)">
							{{ formatStatus(scope.row.status) }}
						</el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="current_score" label="Current Score" width="100">
					<template #default="scope">
						<span
							:class="{ 'positive-score': scope.row.current_score > 0, 'zero-score': scope.row.current_score === 0 }"
						>
							{{ scope.row.current_score }}
						</span>
					</template>
				</el-table-column>
				<el-table-column label="Rounds" width="100">
					<template #default="scope"> {{ scope.row.current_round }} / {{ scope.row.max_rounds }} </template>
				</el-table-column>
				<el-table-column
					prop="create_time"
					label="Start Time"
					width="180"
					:formatter="(row: any) => formatDate(row.create_time)"
				/>
				<el-table-column
					prop="last_message_time"
					label="Last Activity"
					width="180"
					:formatter="(row: any) => formatDate(row.last_message_time)"
				/>
				<el-table-column label="Actions" fixed="right" width="200">
					<template #default="{ row }">
						<el-button-group>
							<el-button type="primary" link @click="viewSessionDetail(row.id)">
								<el-icon><Tickets /></el-icon>
								Message Records
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

		<!-- Pagination -->
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
	</div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { InfoFilled, Tickets, Delete } from "@element-plus/icons-vue";
import { filterSessions, getSessionStatistics, deleteSession } from "@/api/task_game_sessions";
import { formatDate } from "@/utils";

// Type definitions
interface TaskGameSession {
	id: string;
	user_id: string;
	subtask_id: string;
	task_id: string;
	status: number;
	current_score: number;
	current_round: number;
	max_rounds: number;
	target_score: number;
	last_message_time: string | null;
	summary: string | null;
	create_time: string;
	update_time: string;
}

interface Statistics {
	total_sessions: number;
	completed_sessions: number;
	interrupted_sessions: number;
	timed_out_sessions: number;
	in_progress_sessions: number;
	average_score: number;
	average_rounds: number;
	sessions_by_task: Record<string, number>;
	sessions_by_status: Record<string, number>;
}

interface FilterOptions {
	user_id: string;
	task_id: string;
	subtask_id: string;
	status: string;
	start_date?: string;
	end_date?: string;
}

// Data definitions
const router = useRouter();
const loading = ref(false);
const tableData = ref<TaskGameSession[]>([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(10);

// Animated number statistics
const animatedStats = reactive({
	total_sessions: 0,
	in_progress_sessions: 0,
	completed_sessions: 0,
	average_rounds: 0,
});

const statistics = reactive<Statistics>({
	total_sessions: 0,
	completed_sessions: 0,
	interrupted_sessions: 0,
	timed_out_sessions: 0,
	in_progress_sessions: 0,
	average_score: 0,
	average_rounds: 0,
	sessions_by_task: {},
	sessions_by_status: {},
});

// Filter conditions
const filters = reactive<FilterOptions>({
	user_id: "",
	task_id: "",
	subtask_id: "",
	status: "",
});

// Date range selection
const dateRange = ref<[Date, Date] | null>(null);
const dateShortcuts = [
	{
		text: "Last Week",
		value: (() => {
			const end = new Date();
			const start = new Date();
			start.setTime(start.getTime() - 3600 * 1000 * 24 * 7);
			return [start, end];
		})(),
	},
	{
		text: "Last Month",
		value: (() => {
			const end = new Date();
			const start = new Date();
			start.setTime(start.getTime() - 3600 * 1000 * 24 * 30);
			return [start, end];
		})(),
	},
	{
		text: "Last 3 Months",
		value: (() => {
			const end = new Date();
			const start = new Date();
			start.setTime(start.getTime() - 3600 * 1000 * 24 * 90);
			return [start, end];
		})(),
	},
];

// Number animation
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

function formatStatus(status: number) {
	switch (status) {
		case 0:
			return "In Progress";
		case 1:
			return "Completed";
		case 2:
			return "Aborted";
		case 3:
			return "Timeout";
		default:
			return "Unknown";
	}
}

function getStatusType(status: number) {
	switch (status) {
		case 0:
			return "warning";
		case 1:
			return "success";
		case 2:
			return "danger";
		case 3:
			return "info";
		default:
			return "info";
	}
}

// Table row style
function tableRowClassName({ row }: { row: TaskGameSession }) {
	if (row.status === 1) {
		// Completed
		return "success-row";
	}
	if (row.status === 2) {
		// Aborted
		return "error-row";
	}
	return "";
}

// Event handlers
function handleRowClick(row: TaskGameSession) {
	viewSessionDetail(row.id);
}

function viewSessionDetail(sessionId: string) {
	router.push(`/bink/task-game-messages/${sessionId}`);
}

function handleDateChange() {
	if (dateRange.value) {
		filters.start_date = dateRange.value[0].toISOString();
		filters.end_date = dateRange.value[1].toISOString();
	} else {
		filters.start_date = undefined;
		filters.end_date = undefined;
	}
	handleSearch();
}

function handleSearch() {
	currentPage.value = 1;
	loadSessions();
}

function resetFilters() {
	filters.user_id = "";
	filters.task_id = "";
	filters.subtask_id = "";
	filters.status = "";
	dateRange.value = null;
	filters.start_date = undefined;
	filters.end_date = undefined;
	handleSearch();
}

function handleSizeChange(val: number) {
	pageSize.value = val;
	loadSessions();
}

function handleCurrentChange(val: number) {
	currentPage.value = val;
	loadSessions();
}

function handleDelete(row: TaskGameSession) {
	ElMessageBox.confirm(`Are you sure you want to delete session ${row.id}? This action cannot be undone.`, "Warning", {
		confirmButtonText: "Confirm",
		cancelButtonText: "Cancel",
		type: "warning",
	})
		.then(() => {
			deleteSession(row.id)
				.then(() => {
					ElMessage.success("Deleted successfully");
					loadSessions();
				})
				.catch((err) => {
					ElMessage.error(`Delete failed: ${err.message}`);
				});
		})
		.catch(() => {
			// Cancel deletion
		});
}

// Data loading
function loadSessions() {
	loading.value = true;
	const params = {
		...filters,
		page: currentPage.value,
		size: pageSize.value,
	};

	filterSessions(params)
		.then((res) => {
			tableData.value = res.items || [];
			total.value = res.total || 0;
			loadStatistics();
		})
		.catch((err) => {
			ElMessage.error(`Failed to load session records: ${err.message}`);
		})
		.finally(() => {
			loading.value = false;
		});
}

function loadStatistics() {
	const params = {
		user_id: filters.user_id,
		start_date: filters.start_date,
		end_date: filters.end_date,
	};

	getSessionStatistics(params)
		.then((res) => {
			// Check if there is data and assign values
			if (res) {
				statistics.total_sessions = res.total_sessions || 0;
				statistics.in_progress_sessions = res.in_progress_sessions || 0;
				statistics.completed_sessions = res.completed_sessions || 0;
				statistics.interrupted_sessions = res.interrupted_sessions || 0;
				statistics.timed_out_sessions = res.timed_out_sessions || 0;
				statistics.average_score = res.average_score || 0;
				statistics.average_rounds = res.average_rounds || 0;
				statistics.sessions_by_task = res.sessions_by_task || {};
				statistics.sessions_by_status = res.sessions_by_status || {};

				// Animate statistics display
				animateValue(animatedStats, "total_sessions", 0, statistics.total_sessions, 1000);
				animateValue(animatedStats, "in_progress_sessions", 0, statistics.in_progress_sessions, 1000);
				animateValue(animatedStats, "completed_sessions", 0, statistics.completed_sessions, 1000);
				animateValue(animatedStats, "average_rounds", 0, statistics.average_rounds, 1000);
			}
		})
		.catch((err) => {
			console.error(`Failed to load statistics: ${err.message}`);
		});
}

// Initialize
onMounted(() => {
	loadSessions();
});
</script>

<style lang="scss" scoped>
.task-game-sessions {
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

		.date-selector {
			width: 400px;
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

		.filter-input,
		.filter-select {
			width: 100%;
		}
	}

	.table-container {
		margin-bottom: 20px;

		.positive-score {
			color: #67c23a;
			font-weight: bold;
		}

		.zero-score {
			color: #909399;
		}
	}

	.pagination {
		display: flex;
		justify-content: flex-end;
		margin-top: 20px;
	}
}

// Animation effects
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

/* Table row styles */
:deep(.success-row) {
	--el-table-tr-bg-color: var(--el-color-success-light-9);
}

:deep(.error-row) {
	--el-table-tr-bg-color: var(--el-color-danger-light-9);
}
</style>
