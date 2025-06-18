<template>
	<div class="role-subtasks">
		<div class="header fade-in">
			<h1 class="title">Role Task Management</h1>
			<div class="actions">
				<el-button class="btn-fix" type="primary" disabled @click="handleAddTask">
					<el-icon><Plus /></el-icon>
					Add Main Task
				</el-button>
				<el-button type="success" @click="openRandomTaskChat">
					<el-icon><ChatLineRound /></el-icon>
					Random Task
				</el-button>
			</div>
		</div>

		<!-- Main Task Table -->
		<div class="table-container fade-in-up">
			<el-table
				v-loading="loading"
				:data="tableData"
				style="width: 100%"
				row-key="id"
				border
				:expand-row-keys="expandedRows"
				@expand-change="handleExpandChange"
				stripe
				:highlight-current-row="true"
			>
				<!-- Expandable Column -->
				<el-table-column type="expand">
					<template #default="props">
						<div class="subtasks-container">
							<div class="subtasks-header">
								<h3>Subtask List</h3>
								<el-button type="primary" size="small" @click="handleAddSubtask(props.row)">
									<el-icon><Plus /></el-icon>
									Add Subtask
								</el-button>
							</div>

							<!-- Subtask Table -->
							<el-table
								:data="subtasksMap[props.row.id]?.list || []"
								style="width: 100%"
								border
								stripe
								v-loading="subtasksMap[props.row.id]?.loading"
							>
								<el-table-column prop="task_personality" label="Subtask Character Setting" show-overflow-tooltip />
								<el-table-column prop="task_goal_judge" label="Referee Judgment Standard" show-overflow-tooltip />
								<el-table-column prop="hide_designs" label="Hidden Settings" show-overflow-tooltip />
								<el-table-column prop="task_level" label="Difficulty Level" width="100" />
								<el-table-column prop="prologues" label="Opening Lines" show-overflow-tooltip />
								<el-table-column label="Actions" width="220">
									<template #default="scope">
										<el-button-group>
											<el-button type="primary" link @click="handleEditSubtask(scope.row)">
												<el-icon><Edit /></el-icon>
												Edit
											</el-button>
											<el-button type="danger" link @click="handleDeleteSubtask(scope.row)">
												<el-icon><Delete /></el-icon>
												Delete
											</el-button>
										</el-button-group>
									</template>
								</el-table-column>
							</el-table>

							<!-- Subtask Pagination -->
							<div class="subtasks-pagination">
								<el-pagination
									:current-page="subtasksMap[props.row.id]?.page || 1"
									:page-size="subtasksMap[props.row.id]?.size || 10"
									:total="subtasksMap[props.row.id]?.total || 0"
									:page-sizes="[10, 20, 50, 100]"
									layout="total, sizes, prev, pager, next"
									@size-change="(size) => handleSubtaskSizeChange(props.row.id, size)"
									@current-change="(page) => handleSubtaskPageChange(props.row.id, page)"
								/>
							</div>
						</div>
					</template>
				</el-table-column>
				<el-table-column prop="title" label="Task Title" />
				<el-table-column prop="description" label="Task Description" show-overflow-tooltip />
				<el-table-column prop="task_goal" label="Task Goal" show-overflow-tooltip />
				<el-table-column prop="max_rounds" label="Max Rounds" width="100" />
				<el-table-column prop="target_score" label="Target Score" width="100" />
				<el-table-column prop="task_level" label="Difficulty Level" width="100" />
				<el-table-column
					prop="create_time"
					label="Creation Time"
					width="180"
					:formatter="(row: any) => formatDate(row.create_time)"
				/>
				<el-table-column label="Actions" width="200" fixed="right">
					<template #default="{ row }">
						<el-button-group>
							<el-button type="primary" link @click="handleAutoTask(row)">
								<el-icon><Connection /></el-icon>
								Generate
							</el-button>
							<el-button type="primary" link @click="handleEditTask(row)">
								<el-icon><Edit /></el-icon>
								Edit
							</el-button>
							<el-button type="danger" link @click="handleDeleteTask(row)">
								<el-icon><Delete /></el-icon>
								Delete
							</el-button>
						</el-button-group>
					</template>
				</el-table-column>
			</el-table>
		</div>

		<!-- Main Task Pagination -->
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

		<!-- Main Task Form Dialog -->
		<el-dialog v-model="taskDialogVisible" :title="taskFormMode === 'add' ? 'Add Main Task' : 'Edit Main Task'" width="800px">
			<el-form :model="taskForm" label-width="120px" ref="taskFormRef" :rules="taskFormRules">
				<el-form-item label="Task Title" prop="title">
					<el-input v-model="taskForm.title" placeholder="Please enter task title" />
				</el-form-item>
				<el-form-item label="Task Description" prop="description">
					<el-input v-model="taskForm.description" type="textarea" placeholder="Please enter task description" />
				</el-form-item>
				<el-form-item label="Task Goal" prop="task_goal">
					<el-input v-model="taskForm.task_goal" type="textarea" placeholder="Please enter task goal" />
				</el-form-item>
				<el-form-item label="Referee Judgment Standard" prop="task_goal_judge">
					<el-input v-model="taskForm.task_goal_judge" type="textarea" placeholder="Please enter referee judgment standard" />
				</el-form-item>
				<el-form-item label="Opening Lines" prop="prologues">
					<el-input v-model="taskForm.prologues" type="textarea" placeholder="Please enter opening lines, separate multiple with commas" />
				</el-form-item>
				<el-form-item label="Max Dialog Rounds" prop="max_rounds">
					<el-input-number v-model="taskForm.max_rounds" :min="1" :max="100" />
				</el-form-item>
				<el-form-item label="Target Score" prop="target_score">
					<el-input-number v-model="taskForm.target_score" :min="0" :max="1000" />
				</el-form-item>
				<el-form-item label="Score Range" prop="score_range">
					<el-input v-model="taskForm.score_range" placeholder="Example: -10~+10" />
				</el-form-item>
				<el-form-item label="Task Difficulty Level" prop="task_level">
					<el-rate v-model="taskForm.task_level" :max="5" />
				</el-form-item>
				<el-form-item label="Task Character Setting" prop="task_personality">
					<el-input v-model="taskForm.task_personality" type="textarea" placeholder="Please enter task character setting" />
				</el-form-item>
				<el-form-item label="Hidden Settings" prop="hide_designs">
					<el-input v-model="taskForm.hide_designs" type="textarea" placeholder="Please enter hidden settings, separate multiple with commas" />
				</el-form-item>
				<el-form-item label="Task Type" prop="task_type">
					<el-select v-model="taskForm.task_type" placeholder="Please select task type">
						<el-option label="Standard Task" value="standard" />
						<el-option label="Story Task" value="story" />
						<el-option label="Challenge Task" value="challenge" />
					</el-select>
				</el-form-item>
				<el-form-item label="User Level Required" prop="user_level_required">
					<el-input-number v-model="taskForm.user_level_required" :min="1" :max="100" />
				</el-form-item>
				<el-form-item label="Associated Role ID" prop="role_id">
					<el-input v-model="taskForm.role_id" placeholder="Please enter associated role ID" />
				</el-form-item>
			</el-form>
			<template #footer>
				<div class="dialog-footer">
					<el-button @click="taskDialogVisible = false">Cancel</el-button>
					<el-button type="primary" @click="submitTaskForm">Confirm</el-button>
				</div>
			</template>
		</el-dialog>

		<!-- Subtask Form Dialog -->
		<el-dialog
			v-model="subtaskDialogVisible"
			:title="subtaskFormMode === 'add' ? 'Add Subtask' : 'Edit Subtask'"
			width="800px"
		>
			<el-form :model="subtaskForm" label-width="120px" ref="subtaskFormRef" :rules="subtaskFormRules">
				<el-form-item label="Main Task ID" prop="task_id">
					<el-input v-model="subtaskForm.task_id" placeholder="Main Task ID" disabled />
				</el-form-item>
				<el-form-item label="Subtask Character Setting" prop="task_personality">
					<el-input v-model="subtaskForm.task_personality" type="textarea" placeholder="Please enter subtask character setting" />
				</el-form-item>
				<el-form-item label="Referee Judgment Standard" prop="task_goal_judge">
					<el-input v-model="subtaskForm.task_goal_judge" type="textarea" placeholder="Please enter referee judgment standard" />
				</el-form-item>
				<el-form-item label="Hidden Settings" prop="hide_designs">
					<el-input v-model="subtaskForm.hide_designs" type="textarea" placeholder="Please enter hidden settings, separate multiple with commas" />
				</el-form-item>
				<el-form-item label="Difficulty Level" prop="task_level">
					<el-rate v-model="subtaskForm.task_level" :max="5" />
				</el-form-item>
				<el-form-item label="Opening Lines" prop="prologues">
					<el-input v-model="subtaskForm.prologues" type="textarea" placeholder="Please enter opening lines, separate multiple with commas" />
				</el-form-item>
			</el-form>
			<template #footer>
				<div class="dialog-footer">
					<el-button @click="subtaskDialogVisible = false">Cancel</el-button>
					<el-button type="primary" @click="submitSubtaskForm">Confirm</el-button>
				</div>
			</template>
		</el-dialog>

		<!-- Auto Generate Task Dialog -->
		<el-dialog v-model="autoTaskDialogVisible" title="Auto Generate Task" width="500px">
			<el-form :model="autoTaskForm" label-width="120px" ref="autoTaskFormRef" :rules="autoTaskFormRules">
				<el-form-item label="Task ID" prop="task_id">
					<el-input v-model="autoTaskForm.task_id" placeholder="Task ID" disabled />
				</el-form-item>
				<el-form-item label="Task Quantity" prop="number">
					<el-input-number v-model="autoTaskForm.number" :min="1" :max="100" />
				</el-form-item>
				<el-form-item label="Scheduled Task" prop="regular_time">
					<el-switch v-model="autoTaskForm.regular_time" />
				</el-form-item>
				<el-form-item label="Daily Execution Time" prop="daily_time" v-if="autoTaskForm.regular_time">
					<el-time-picker
						v-model="autoTaskForm.daily_time"
						format="HH:mm"
						placeholder="Select daily execution time"
						:clearable="false"
						value-format="YYYY-MM-DDTHH:mm:ss.000Z"
					/>
				</el-form-item>
			</el-form>
			<template #footer>
				<div class="dialog-footer">
					<el-button @click="autoTaskDialogVisible = false">Cancel</el-button>
					<el-button type="primary" @click="submitAutoTaskForm">Confirm</el-button>
				</div>
			</template>
		</el-dialog>

		<!-- Random Task Chat Dialog -->
		<chat-dialog
			v-model:visible="randomTaskDialogVisible"
			:role-select-mode="true"
			@task-completed="handleRandomTaskCompleted"
			@task-skipped="handleRandomTaskSkipped"
		/>
	</div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Plus, Edit, Delete, Connection, ChatLineRound } from "@element-plus/icons-vue";
import type { FormInstance, FormRules } from "element-plus";
import * as TaskApi from "@/api/role-tasks";
import * as SubtaskApi from "@/api/role-subtasks";
import ChatDialog from "./ChatDialog.vue";
import { getTaskLists } from "@/api/role-tasks";
import { getSubtaskList } from "@/api/role-subtasks";
import { useRouter } from "vue-router";

// Type definitions
interface RoleTask {
	id: string;
	title: string;
	description: string;
	task_goal: string;
	task_goal_judge: string;
	prologues: string;
	max_rounds: number;
	target_score: number;
	score_range: string;
	task_level: number;
	task_personality: string;
	hide_designs: string;
	task_type: string;
	user_level_required: number;
	role_id: string;
	create_time: string;
	update_time: string;
}

interface RoleSubtask {
	id: string;
	task_id: string;
	task_personality: string;
	task_goal_judge: string;
	hide_designs: string;
	task_level: number;
	prologues: string;
	create_time: string;
	update_time: string;
}

interface SubtaskPagination {
	list: RoleSubtask[];
	page: number;
	size: number;
	total: number;
	loading: boolean;
}

// Data definitions
const loading = ref(false);
const tableData = ref<RoleTask[]>([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(10);
const expandedRows = ref<string[]>([]);
const subtasksMap = reactive<Record<string, SubtaskPagination>>({});

// Form related
const taskDialogVisible = ref(false);
const subtaskDialogVisible = ref(false);
const taskFormMode = ref<"add" | "edit">("add");
const subtaskFormMode = ref<"add" | "edit">("add");
const taskFormRef = ref<FormInstance>();
const subtaskFormRef = ref<FormInstance>();

// Form data
const taskForm = reactive({
	id: "",
	title: "",
	description: "",
	task_goal: "",
	task_goal_judge: "",
	prologues: "",
	max_rounds: 5,
	target_score: 100,
	score_range: "-10~+10",
	task_level: 1,
	task_personality: "",
	hide_designs: "",
	task_type: "standard",
	user_level_required: 1,
	role_id: "",
});

const subtaskForm = reactive({
	id: "",
	task_id: "",
	task_personality: "",
	task_goal_judge: "",
	hide_designs: "",
	task_level: 1,
	prologues: "",
});

// Form validation rules
const taskFormRules = reactive<FormRules>({
	title: [{ required: true, message: "Please enter task title", trigger: "blur" }],
	description: [{ required: true, message: "Please enter task description", trigger: "blur" }],
	task_goal: [{ required: true, message: "Please enter task goal", trigger: "blur" }],
	role_id: [{ required: true, message: "Please enter associated role ID", trigger: "blur" }],
});

const subtaskFormRules = reactive<FormRules>({
	task_id: [{ required: true, message: "Main task ID cannot be empty", trigger: "blur" }],
});

// Auto generate task form
const autoTaskDialogVisible = ref(false);
const autoTaskFormRef = ref<FormInstance>();
const autoTaskForm = reactive({
	task_id: "",
	number: 1,
	regular_time: false,
	daily_time: null as Date | null,
});

const autoTaskFormRules = reactive<FormRules>({
	task_id: [{ required: true, message: "Task ID cannot be empty", trigger: "blur" }],
	number: [{ required: true, message: "Task quantity cannot be empty", trigger: "blur" }],
	daily_time: [
		{
			required: true,
			message: "Scheduled task must set execution time",
			trigger: "blur",
			validator: (rule, value, callback) => {
				if (autoTaskForm.regular_time && !value) {
					callback(new Error("Scheduled task must set execution time"));
				} else {
					callback();
				}
			},
		},
	],
});

// Random task chat
const randomTaskDialogVisible = ref(false);

// Lifecycle hooks
onMounted(() => {
	loadTasks();
});

// Load main task data
const loadTasks = async () => {
	loading.value = true;
	try {
		const res = await getTaskLists({
			page: currentPage.value,
			size: pageSize.value,
		});
		tableData.value = res.items;
		total.value = res.total;
	} catch (error) {
		console.error("Failed to load tasks", error);
		ElMessage.error("Failed to load tasks");
	} finally {
		loading.value = false;
	}
};

// Load subtask data
const loadSubtasks = async (taskId: string, page = 1, size = 10) => {
	// Initialize or update subtask pagination information
	if (!subtasksMap[taskId]) {
		subtasksMap[taskId] = {
			list: [],
			page: page,
			size: size,
			total: 0,
			loading: false,
		};
	} else {
		subtasksMap[taskId].page = page;
		subtasksMap[taskId].size = size;
	}

	subtasksMap[taskId].loading = true;
	try {
		const res = await getSubtaskList(taskId, {
			page: page,
			size: size,
		});
		subtasksMap[taskId].list = res.items;
		subtasksMap[taskId].total = res.total;
	} catch (error) {
		console.error("Failed to load subtasks", error);
		ElMessage.error("Failed to load subtasks");
	} finally {
		subtasksMap[taskId].loading = false;
	}
};

// Main task pagination handling
const handleSizeChange = (size: number) => {
	pageSize.value = size;
	loadTasks();
};

const handleCurrentChange = (page: number) => {
	currentPage.value = page;
	loadTasks();
};

// Subtask pagination handling
const handleSubtaskSizeChange = (taskId: string, size: number) => {
	if (subtasksMap[taskId]) {
		subtasksMap[taskId].size = size;
		loadSubtasks(taskId, subtasksMap[taskId].page, size);
	}
};

const handleSubtaskPageChange = (taskId: string, page: number) => {
	if (subtasksMap[taskId]) {
		loadSubtasks(taskId, page, subtasksMap[taskId].size);
	}
};

// Expand row handling
const handleExpandChange = (row: RoleTask, expanded: boolean) => {
	if (expanded) {
		expandedRows.value = [row.id];
		// Load subtask data
		loadSubtasks(row.id);
	} else {
		expandedRows.value = [];
	}
};

// Add main task
const handleAddTask = () => {
	taskFormMode.value = "add";
	resetTaskForm();
	taskDialogVisible.value = true;
};

// Edit main task
const handleEditTask = (row: RoleTask) => {
	taskFormMode.value = "edit";
	Object.assign(taskForm, row);
	taskDialogVisible.value = true;
};

// Delete main task
const handleDeleteTask = (row: RoleTask) => {
	ElMessageBox.confirm("Are you sure you want to delete this task? This will also delete all subtasks!", "Warning", {
		confirmButtonText: "Confirm",
		cancelButtonText: "Cancel",
		type: "warning",
	})
		.then(async () => {
			try {
				await TaskApi.deleteTask(row.id);
				ElMessage.success("Deleted successfully");
				loadTasks();
			} catch (error) {
				console.error("Failed to delete task", error);
				ElMessage.error("Failed to delete task");
			}
		})
		.catch(() => {
			// Cancel deletion
		});
};

// Add subtask
const handleAddSubtask = (row: RoleTask) => {
	subtaskFormMode.value = "add";
	resetSubtaskForm();
	subtaskForm.task_id = row.id;
	subtaskDialogVisible.value = true;
};

// Edit subtask
const handleEditSubtask = (row: RoleSubtask) => {
	subtaskFormMode.value = "edit";
	Object.assign(subtaskForm, row);
	subtaskDialogVisible.value = true;
};

// Delete subtask
const handleDeleteSubtask = (row: RoleSubtask) => {
	ElMessageBox.confirm("Are you sure you want to delete this subtask?", "Warning", {
		confirmButtonText: "Confirm",
		cancelButtonText: "Cancel",
		type: "warning",
	})
		.then(async () => {
			try {
				await SubtaskApi.deleteSubtask(row.id);
				ElMessage.success("Deleted successfully");
				// Reload subtasks for this main task
				loadSubtasks(row.task_id, subtasksMap[row.task_id].page, subtasksMap[row.task_id].size);
			} catch (error) {
				console.error("Failed to delete subtask", error);
				ElMessage.error("Failed to delete subtask");
			}
		})
		.catch(() => {
			// Cancel deletion
		});
};

// Submit main task form
const submitTaskForm = async () => {
	if (!taskFormRef.value) return;

	await taskFormRef.value.validate(async (valid) => {
		if (valid) {
			try {
				if (taskFormMode.value === "add") {
					await TaskApi.addTask(taskForm);
					ElMessage.success("Added successfully");
				} else {
					await TaskApi.updateTask(taskForm.id, taskForm);
					ElMessage.success("Updated successfully");
				}
				taskDialogVisible.value = false;
				loadTasks();
			} catch (error) {
				console.error("Failed to save task", error);
				ElMessage.error("Failed to save task");
			}
		}
	});
};

// Submit subtask form
const submitSubtaskForm = async () => {
	if (!subtaskFormRef.value) return;

	await subtaskFormRef.value.validate(async (valid) => {
		if (valid) {
			try {
				if (subtaskFormMode.value === "add") {
				await SubtaskApi.addSubtask(subtaskForm);
				ElMessage.success("Added successfully");
			} else {
				await SubtaskApi.updateSubtask(subtaskForm.id, subtaskForm);
				ElMessage.success("Updated successfully");
			}
			subtaskDialogVisible.value = false;
			// Reload subtasks for this main task
			loadSubtasks(subtaskForm.task_id, subtasksMap[subtaskForm.task_id].page, subtasksMap[subtaskForm.task_id].size);
		} catch (error) {
			console.error("Failed to save subtask", error);
			ElMessage.error("Failed to save subtask");
			}
		}
	});
};
const router = useRouter();
// Submit auto-generate task form
const submitAutoTaskForm = async () => {
	if (!autoTaskFormRef.value) return;

	await autoTaskFormRef.value.validate(async (valid) => {
		if (valid) {
			try {
				// Prepare data to send to backend
				const formData = { ...autoTaskForm };

				// If it's a scheduled task, ensure correct time passing
				if (formData.regular_time && formData.daily_time) {
					// Keep daily_time format unchanged, ensure it contains hour and minute information
					// Backend will extract hour and minute
				}

				await SubtaskApi.autoGenerateTask(formData);
				ElMessage.success("Auto task has been submitted, please manually refresh later to view results");
				autoTaskDialogVisible.value = false;

				ElMessageBox.confirm("Do you want to view the task execution plan?", "Warning", {
					confirmButtonText: "Go",
					cancelButtonText: "Cancel",
					type: "warning",
				})
					.then(() => {
						router.push("/system/task-manage");
					})
					.catch(() => {});
			} catch (error) {
				console.error("Failed to submit auto task", error);
				ElMessage.error("Failed to submit auto task");
			}
		}
	});
};

// Reset forms
const resetTaskForm = () => {
	if (taskFormRef.value) {
		taskFormRef.value.resetFields();
	}
	taskForm.id = "";
	taskForm.title = "";
	taskForm.description = "";
	taskForm.task_goal = "";
	taskForm.task_goal_judge = "";
	taskForm.prologues = "";
	taskForm.max_rounds = 5;
	taskForm.target_score = 100;
	taskForm.score_range = "-10~+10";
	taskForm.task_level = 1;
	taskForm.task_personality = "";
	taskForm.hide_designs = "";
	taskForm.task_type = "standard";
	taskForm.user_level_required = 1;
	taskForm.role_id = "";
};

const resetSubtaskForm = () => {
	if (subtaskFormRef.value) {
		subtaskFormRef.value.resetFields();
	}
	subtaskForm.id = "";
	subtaskForm.task_id = "";
	subtaskForm.task_personality = "";
	subtaskForm.task_goal_judge = "";
	subtaskForm.hide_designs = "";
	subtaskForm.task_level = 1;
	subtaskForm.prologues = "";
};

// Format date
const formatDate = (dateStr: string) => {
	if (!dateStr) return "";
	const date = new Date(dateStr);
	return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(
		2,
		"0",
	)} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}:${String(
		date.getSeconds(),
	).padStart(2, "0")}`;
};

// Auto generate task
const handleAutoTask = (row: RoleTask) => {
	autoTaskForm.task_id = row.id;
	autoTaskDialogVisible.value = true;
};

// Open random task chat
const openRandomTaskChat = () => {
	randomTaskDialogVisible.value = true;
};

// Handle random task completion
const handleRandomTaskCompleted = (result) => {
	console.log("Random task completed", result);
	// Can perform some operations, such as saving records, displaying results, etc.
};

// Handle random task skipped
const handleRandomTaskSkipped = () => {
	console.log("Random task skipped");
	ElMessage({
		type: "info",
		message: "Current random task has been skipped",
	});
};
</script>

<style scoped lang="scss">
.role-subtasks {
	padding: 20px;
}

.header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 20px;
}

.title {
	font-size: 24px;
	font-weight: bold;
	margin: 0;
}

.table-container {
	margin-bottom: 20px;
}

.pagination {
	display: flex;
	justify-content: flex-end;
	margin-top: 20px;
}

.subtasks-container {
	padding: 20px;
	background-color: #f9f9f9;
	border-radius: 4px;
}

.subtasks-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 15px;
}

.subtasks-header h3 {
	margin: 0;
	font-size: 16px;
}

.subtasks-pagination {
	margin-top: 15px;
	display: flex;
	justify-content: flex-end;
}

/* 动画效果 */
.fade-in {
	animation: fadeIn 0.5s ease-in-out;
}

.fade-in-up {
	animation: fadeInUp 0.5s ease-in-out;
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

@import '@/layouts/WriterLayout/css/extra.scss';

.btn-fix {
	color: #fff;
	background-color: $btn-bg-color0;
	border-color: $btn-bg-color0;
}
</style>
