<template>
	<div class="tasks-container">
		<div class="header">
			<div class="title">任务管理系统</div>
		</div>

		<div class="filter-container">
			<div class="filter">
				<div class="filter-item m-r10">
					<el-select v-model="filter.type" placeholder="任务类型" clearable @change="filterTasks">
						<el-option v-for="(name, type) in taskTypes" :key="type" :label="name" :value="type" />
					</el-select>
				</div>
				<div class="filter-item m-r10">
					<el-select v-model="filter.difficulty" placeholder="难度等级" clearable @change="filterTasks">
						<el-option v-for="diff in difficulties" :key="diff" :label="diff" :value="diff" />
					</el-select>
				</div>
				<div class="filter-item m-r10">
					<el-input v-model="filter.keyword" placeholder="搜索任务..." @input="filterTasks">
						<template #prefix>
							<el-icon><Search /></el-icon>
						</template>
					</el-input>
				</div>
			</div>
			<div class="filter-item m-r10">
				<el-button type="primary" @click="createNewTask" class="create-btn">
					<el-icon><Plus /></el-icon>
					创建新任务
				</el-button>
			</div>
		</div>

		<div class="tasks-grid" v-loading="loading">
			<el-empty v-if="filteredTasks.length === 0" description="暂无任务" class="empty-tasks" />

			<div
				v-for="(task, index) in filteredTasks"
				:key="index"
				class="task-card"
				:class="{ disabled: task.status === 0 }"
			>
				<div class="task-difficulty" :class="getDifficultyClass(task.difficulty)">{{ task.difficulty }}</div>

				<div class="task-header">
					<h3 class="task-title">{{ task.title }}</h3>
					<el-tag size="small" :type="getTaskTypeTag(task.task_type)" effect="dark">
						{{ getTaskTypeName(task.task_type) }}
					</el-tag>
				</div>

				<div class="task-description">
					{{ task.description }}
				</div>

				<div class="task-details">
					<div class="detail-item" v-if="task.max_dialogue_rounds">
						<el-icon><ChatDotRound /></el-icon>
						<!--						<span>对话轮数: {{ task.max_dialogue_rounds == -1 ? "无限制" : ask.max_dialogue_rounds }}</span>-->
						<span>对话轮数: 无限制</span>
					</div>
					<div class="detail-item" v-if="task.required_user_level">
						<el-icon><UserFilled /></el-icon>
						<span>等级要求: {{ task.required_user_level }}</span>
					</div>
					<div class="detail-item" v-if="task.game_type">
						<el-icon><Collection /></el-icon>
						<span>游戏类型: {{ task.game_type }}</span>
					</div>
					<div class="detail-item" v-if="task.game_number_min && task.game_number_max">
						<el-icon><User /></el-icon>
						<span>游戏人数: {{ task.game_number_min }}-{{ task.game_number_max }}人</span>
					</div>
				</div>

				<div class="task-meta">
					<div class="meta-date">
						<el-icon><Calendar /></el-icon>
						<span>创建于 {{ formatDateTime(task.created_at) }}</span>
					</div>

					<div class="meta-status" v-if="task.status === 0">
						<el-icon><WarningFilled /></el-icon>
						<span>已禁用</span>
					</div>
				</div>

				<div class="task-actions">
					<el-tooltip content="测试任务" placement="top">
						<el-button circle class="action-button play-button" @click="startTask(task)" :disabled="task.status === 0">
							<el-icon><VideoPlay /></el-icon>
						</el-button>
					</el-tooltip>
					<el-tooltip content="编辑任务" placement="top">
						<el-button circle class="action-button edit-button" @click="editTask(task)">
							<el-icon><Edit /></el-icon>
						</el-button>
					</el-tooltip>
					<el-tooltip content="删除任务" placement="top">
						<el-button circle class="action-button delete-button" @click="deleteTask(task)">
							<el-icon><Delete /></el-icon>
						</el-button>
					</el-tooltip>
				</div>
			</div>
		</div>

		<!-- 分页组件 -->
		<div v-if="showPagination" class="pagination-container">
			<el-pagination
				v-model:current-page="currentPage"
				v-model:page-size="pageSize"
				:page-sizes="[10, 20, 50, 100]"
				:total="total"
				layout="total, sizes, prev, pager, next, jumper"
				@size-change="handleSizeChange"
				@current-change="handleCurrentChange"
			/>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import {
	Plus,
	Calendar,
	UserFilled,
	User,
	VideoPlay,
	Edit,
	Delete,
	ChatDotRound,
	Search,
	WarningFilled,
	Collection,
} from "@element-plus/icons-vue";
import { getTaskList, deleteTask as apiDeleteTask } from "@/api/task";
import type { Page } from "@/types/api";

const router = useRouter();
const loading = ref(false);
const tasks = ref([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(10);

// 筛选
const filter = reactive({
	type: "",
	difficulty: "",
	keyword: "",
});

// 任务类型映射
const taskTypes = {
	adventure: "冒险探索",
	mystery: "悬疑调查",
	training: "能力训练",
	"abyss-crisis": "深渊危机",
	"bureau-mission": "组织任务",
	other: "其他类型",
};

// 难度等级
const difficulties = ["简单", "中等", "困难", "极难"];

// 筛选后的任务
const filteredTasks = computed(() => {
	return tasks.value.filter((task) => {
		// 类型筛选
		if (filter.type && task.task_type !== filter.type) {
			return false;
		}

		// 难度筛选
		if (filter.difficulty && task.difficulty !== filter.difficulty) {
			return false;
		}

		// 关键字筛选
		if (
			filter.keyword &&
			!task.title.toLowerCase().includes(filter.keyword.toLowerCase()) &&
			!task.description.toLowerCase().includes(filter.keyword.toLowerCase())
		) {
			return false;
		}

		return true;
	});
});

// 智能分页显示
const showPagination = computed(() => total.value >= 10);

// 加载任务数据
const loadTasks = async () => {
	loading.value = true;
	try {
		const response: Page<any> = await getTaskList({
			page: currentPage.value,
			size: pageSize.value,
		});
		tasks.value = response.items || [];
		total.value = response.total || 0;
	} catch (error) {
		console.error("加载任务数据失败", error);
		ElMessage.error("加载任务数据失败");
	} finally {
		loading.value = false;
	}
};

// 处理分页大小变化
const handleSizeChange = (val: number) => {
	pageSize.value = val;
	currentPage.value = 1; // 重置到第一页
	loadTasks();
};

// 处理当前页变化
const handleCurrentChange = (val: number) => {
	currentPage.value = val;
	loadTasks();
};

// 筛选任务
const filterTasks = () => {
	// 筛选逻辑通过 computed 属性自动处理
};

// 创建新任务
const createNewTask = () => {
	router.push("/chat/tasks/create");
};

// 编辑任务
const editTask = (task) => {
	router.push(`/chat/tasks/edit/${task.id}`);
};

// 删除任务
const deleteTask = (task) => {
	ElMessageBox.confirm(`确定要删除任务 "${task.title}" 吗？此操作不可恢复。`, "删除确认", {
		confirmButtonText: "确定",
		cancelButtonText: "取消",
		type: "warning",
	})
		.then(async () => {
			try {
				await apiDeleteTask(task.id);
				ElMessage.success("任务已删除");
				loadTasks(); // 重新加载任务列表
			} catch (error) {
				console.error("删除任务失败", error);
				ElMessage.error("删除任务失败");
			}
		})
		.catch(() => {
			// 用户取消操作
		});
};

// 开始任务测试
const startTask = (task) => {
	// 将任务ID保存到localStorage
	localStorage.setItem("currentTaskId", task.id.toString());
	router.push(`/chat/tasks/test/${task.id}`);
};

// 格式化日期时间
const formatDateTime = (timestamp) => {
	if (!timestamp) return "";

	const date = new Date(timestamp);
	const year = date.getFullYear();
	const month = String(date.getMonth() + 1).padStart(2, "0");
	const day = String(date.getDate()).padStart(2, "0");
	const hours = String(date.getHours()).padStart(2, "0");
	const minutes = String(date.getMinutes()).padStart(2, "0");

	return `${year}-${month}-${day} ${hours}:${minutes}`;
};

// 获取任务类型标签
const getTaskTypeTag = (type) => {
	const typeMap = {
		adventure: "success",
		mystery: "warning",
		training: "info",
		"abyss-crisis": "danger",
		"bureau-mission": "primary",
		other: "",
	};

	return typeMap[type] || "";
};

// 获取任务类型名称
const getTaskTypeName = (type) => {
	return taskTypes[type] || "未知类型";
};

// 获取难度CSS类名
const getDifficultyClass = (difficulty) => {
	const map = {
		简单: "easy",
		中等: "medium",
		困难: "hard",
		极难: "extreme",
	};
	return map[difficulty] || "";
};

// 组件挂载时加载数据
onMounted(() => {
	loadTasks();
});
</script>

<style scoped lang="scss">
.tasks-container {
	min-height: 100vh;
	padding: 30px;
	background-color: #121212;
	background-image: linear-gradient(to bottom, rgba(30, 30, 30, 0.9), rgba(10, 10, 10, 0.95)),
		url("https://img.freepik.com/free-photo/abstract-futuristic-background-with-colorful-glowing-neon-lights_181624-34728.jpg");
	background-size: cover;
	background-position: center;
	background-attachment: fixed;
	color: #f0f0f0;
}

.header {
	margin-bottom: 30px;
}

.title {
	font-size: 24px;
	color: #e91e63;
	text-shadow: 0 0 15px rgba(233, 30, 99, 0.5);
	letter-spacing: 2px;
}

.subtitle {
	font-size: 18px;
	color: #aaa;
	font-style: italic;
	margin-bottom: 30px;
}

.create-btn {
	display: block;
	width: 200px;
	height: 48px;
	margin: 0 auto 30px;
	background: linear-gradient(45deg, #e91e63, #9c27b0);
	border: none;
	border-radius: 24px;
	box-shadow: 0 5px 15px rgba(233, 30, 99, 0.3);
	transition: all 0.3s ease;
}

.create-btn:hover {
	transform: translateY(-3px);
	box-shadow: 0 8px 20px rgba(233, 30, 99, 0.5);
}

.filter-container {
	display: flex;
	gap: 15px;
	margin-bottom: 30px;
	justify-content: space-between;
	.filter {
		display: flex;
	}
	.m-r10 {
		margin-right: 10px;
	}
}

.filter-item {
	width: 200px;
}

.tasks-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
	gap: 25px;
	margin-top: 30px;
}

.task-card {
	position: relative;
	background: rgba(40, 40, 50, 0.7);
	border-radius: 15px;
	padding: 25px;
	box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
	transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
	overflow: hidden;
	display: flex;
	flex-direction: column;
	border-top: 3px solid transparent;
}

.task-card:hover {
	transform: translateY(-10px);
	box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
	background: rgba(50, 50, 60, 0.8);
}

.task-card.disabled {
	opacity: 0.7;
	border-top-color: #f56c6c;
}

.task-difficulty {
	position: absolute;
	top: 2px;
	right: 4px;
	padding: 2px 12px;
	border-radius: 20px;
	font-size: 12px;
	font-weight: bold;
	letter-spacing: 1px;
	text-transform: uppercase;
}

.task-difficulty.easy {
	background-color: rgba(103, 194, 58, 0.2);
	color: #67c23a;
	border: 1px solid #67c23a;
}

.task-difficulty.medium {
	background-color: rgba(230, 162, 60, 0.2);
	color: #e6a23c;
	border: 1px solid #e6a23c;
}

.task-difficulty.hard {
	background-color: rgba(245, 108, 108, 0.2);
	color: #f56c6c;
	border: 1px solid #f56c6c;
}

.task-difficulty.extreme {
	background-color: rgba(144, 147, 153, 0.2);
	color: #909399;
	border: 1px solid #909399;
}

.task-header {
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
	margin-bottom: 15px;
	margin-top: 10px;
}

.task-title {
	font-size: 20px;
	color: #fff;
	margin: 0;
	font-weight: 600;
	display: -webkit-box;
	-webkit-line-clamp: 2;
	-webkit-box-orient: vertical;
	overflow: hidden;
}

.task-description {
	color: #bbb;
	font-size: 14px;
	line-height: 1.6;
	margin-bottom: 20px;
	flex-grow: 1;
	overflow: hidden;
	display: -webkit-box;
	-webkit-line-clamp: 3;
	-webkit-box-orient: vertical;
}

.task-details {
	display: flex;
	flex-wrap: wrap;
	margin-bottom: 15px;
	gap: 10px;
}

.detail-item {
	display: flex;
	align-items: center;
	gap: 5px;
	background-color: rgba(60, 60, 70, 0.6);
	padding: 5px 10px;
	border-radius: 15px;
	font-size: 12px;
	color: #ddd;
}

.task-meta {
	display: flex;
	justify-content: space-between;
	margin-bottom: 20px;
	color: #999;
	font-size: 12px;
}

.meta-date,
.meta-status {
	display: flex;
	align-items: center;
	gap: 5px;
}

.meta-status {
	color: #f56c6c;
}

.task-actions {
	display: flex;
	justify-content: center;
	gap: 15px;
}

.action-button {
	width: 45px;
	height: 45px;
	flex-shrink: 0;
	transition: all 0.3s ease;
}

.action-button:hover {
	transform: scale(1.15);
}

.play-button {
	background: linear-gradient(45deg, #3880ff, #00c8ff);
	border: none;
	color: white;
}

.edit-button {
	background: linear-gradient(45deg, #9c27b0, #673ab7);
	border: none;
	color: white;
}

.delete-button {
	background: linear-gradient(45deg, #f56c6c, #ff9500);
	border: none;
	color: white;
}

.empty-tasks {
	grid-column: 1 / -1;
	color: #999;
	padding: 100px 0;
}

.pagination-container {
	display: flex;
	justify-content: center;
	margin-top: 30px;
	padding: 20px 0;
}

.pagination-container :deep(.el-pagination) {
	--el-pagination-font-size: 14px;
	--el-pagination-bg-color: rgba(40, 40, 50, 0.8);
	--el-pagination-text-color: #f0f0f0;
	--el-pagination-border-radius: 6px;
	--el-pagination-button-color: #f0f0f0;
	--el-pagination-button-bg-color: rgba(60, 60, 70, 0.8);
	--el-pagination-hover-color: #e91e63;
}

.pagination-container :deep(.el-pagination .el-pager li) {
	background-color: rgba(60, 60, 70, 0.8);
	color: #f0f0f0;
	border-radius: 6px;
	margin: 0 2px;
}

.pagination-container :deep(.el-pagination .el-pager li.is-active) {
	background: linear-gradient(45deg, #e91e63, #9c27b0);
	color: white;
}

.pagination-container :deep(.el-pagination .el-pager li:hover) {
	color: #e91e63;
}

@media (max-width: 768px) {
	.tasks-container {
		padding: 20px;
	}

	.tasks-grid {
		grid-template-columns: 1fr;
	}

	.filter-container {
		flex-direction: column;
		align-items: center;
	}

	.filter-item {
		width: 100%;
	}

	.pagination-container {
		margin-top: 20px;
		padding: 15px 0;
	}

	.pagination-container :deep(.el-pagination) {
		--el-pagination-font-size: 12px;
	}
}
</style>
