<template>
	<div class="task-manage">
		<div class="header fade-in">
			<h1 class="title">Scheduled Task Management</h1>
			<div class="actions">
				<el-button type="primary" @click="handleAddTask">
					<el-icon><Plus /></el-icon>
					Add Task
				</el-button>
			</div>
		</div>

		<el-tabs v-model="activeTab" class="task-tabs">
			<el-tab-pane label="Scheduled Tasks" name="scheduled">
				<!-- Sub panel selection -->
				<el-radio-group v-model="scheduledSubPanel" class="sub-panel-selector">
					<el-radio-button label="system-temp">System Temporary Tasks</el-radio-button>
					<el-radio-button label="regular">Regular Scheduled Tasks</el-radio-button>
				</el-radio-group>

				<!-- Regular scheduled tasks panel -->
				<div v-if="scheduledSubPanel === 'regular'" class="panel-container">
					<!-- Search box -->
					<div class="search-container fade-in">
						<el-form :inline="true" class="search-form">
							<el-form-item label="Task ID">
								<el-input
									v-model="scheduledSearchParams.taskIds"
									placeholder="Multiple IDs separated by commas"
									clearable
									@keyup.enter="loadRegularTasks"
								/>
							</el-form-item>
							<el-form-item label="Task Status">
								<el-select v-model="scheduledSearchParams.status" placeholder="Select status" clearable>
									<el-option v-for="(label, value) in statusOptions" :key="value" :label="label" :value="value" />
								</el-select>
							</el-form-item>
							<el-form-item label="Task Type">
								<el-select v-model="scheduledSearchParams.taskType" placeholder="Select type" clearable>
									<el-option v-for="type in taskTypes" :key="type" :label="type" :value="type" />
								</el-select>
							</el-form-item>
							<el-form-item>
								<el-button type="primary" @click="loadRegularTasks">
									<el-icon><Search /></el-icon>
									Search
								</el-button>
								<el-button @click="resetScheduledSearch">
									<el-icon><Refresh /></el-icon>
									Refresh
								</el-button>
							</el-form-item>
						</el-form>
					</div>

					<!-- Regular scheduled tasks table -->
					<div class="table-container fade-in-up">
						<el-table
							v-loading="regularTasksLoading"
							:data="regularTasksData"
							style="width: 100%"
							row-key="id"
							border
							stripe
							:highlight-current-row="true"
						>
							<el-table-column prop="name" label="Task Name" min-width="120" />
							<el-table-column prop="task_type" label="Task Type" min-width="100" />
							<el-table-column label="Task Status" min-width="100">
								<template #default="{ row }">
									<el-tag :type="getStatusType(row.status)" effect="plain">
										{{ getStatusLabel(row.status) }}
									</el-tag>
								</template>
							</el-table-column>
							<el-table-column label="Trigger Type" min-width="100">
								<template #default="{ row }">
									<el-tag :type="getTriggerType(row.trigger_type)" effect="plain">
										{{ getTriggerLabel(row.trigger_type) }}
									</el-tag>
								</template>
							</el-table-column>
							<el-table-column prop="func_path" label="Execute Function" min-width="200" show-overflow-tooltip />
							<el-table-column prop="description" label="Task Description" min-width="180" show-overflow-tooltip />
							<el-table-column label="Next Run Time" min-width="160">
								<template #default="{ row }">
									{{ row.next_run_time ? formatDate(row.next_run_time) : "Not Scheduled" }}
								</template>
							</el-table-column>
							<el-table-column prop="max_instances" label="Max Instances" min-width="100" />
							<el-table-column
								prop="create_time"
								label="Created Time"
								min-width="160"
								:formatter="(row: any) => formatDate(row.create_time)"
							/>
							<el-table-column label="Actions" min-width="280" fixed="right">
								<template #default="{ row }">
									<el-button-group>
										<el-button type="primary" link @click="handleViewLogs(row)">
											<el-icon><Document /></el-icon>
											Logs
										</el-button>
										<el-button type="success" link @click="handleTriggerTask(row)">
											<el-icon><VideoPlay /></el-icon>
											Trigger
										</el-button>
										<el-button
											:type="row.status === TaskStatus.PAUSED ? 'warning' : 'info'"
											link
											@click="handlePauseResumeTask(row)"
										>
											<el-icon>
												<component :is="row.status === TaskStatus.PAUSED ? 'VideoPlay' : 'VideoPause'" />
											</el-icon>
											{{ row.status === TaskStatus.PAUSED ? "Resume" : "Pause" }}
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

					<!-- 分页 -->
					<div class="pagination">
						<el-pagination
							v-model:current-page="regularCurrentPage"
							v-model:page-size="regularPageSize"
							:total="regularTotal"
							:page-sizes="[10, 20, 50, 100]"
							layout="total, sizes, prev, pager, next"
							@size-change="handleRegularSizeChange"
							@current-change="handleRegularCurrentChange"
						/>
					</div>
				</div>

				<!-- System temporary tasks panel -->
				<div v-if="scheduledSubPanel === 'system-temp'" class="panel-container">
					<!-- Search box -->
					<div class="search-container fade-in">
						<el-form :inline="true" class="search-form">
							<el-form-item label="Task ID">
								<el-input
									v-model="systemTempSearchParams.taskIds"
									placeholder="Multiple IDs separated by commas"
									clearable
									@keyup.enter="loadSystemTempTasks"
								/>
							</el-form-item>
							<el-form-item label="Task Status">
								<el-select v-model="systemTempSearchParams.status" placeholder="Select status" clearable>
									<el-option v-for="(label, value) in statusOptions" :key="value" :label="label" :value="value" />
								</el-select>
							</el-form-item>
							<el-form-item>
								<el-button type="primary" @click="loadSystemTempTasks">
									<el-icon><Search /></el-icon>
									Search
								</el-button>
								<el-button @click="resetSystemTempSearch">
									<el-icon><Refresh /></el-icon>
									Refresh
								</el-button>
							</el-form-item>
						</el-form>
					</div>

					<!-- System temporary tasks table -->
					<div class="table-container fade-in-up">
						<el-table
							v-loading="systemTempTasksLoading"
							:data="systemTempTasksData"
							style="width: 100%"
							row-key="id"
							border
							stripe
							:highlight-current-row="true"
						>
							<el-table-column prop="id" label="Task ID" min-width="150" show-overflow-tooltip />
							<el-table-column prop="name" label="Task Name" min-width="120" />
							<el-table-column prop="description" label="Task Description" min-width="180" show-overflow-tooltip />
							<el-table-column label="Task Status" min-width="100">
								<template #default="{ row }">
									<el-tag :type="getStatusType(row.status)" effect="plain">
										{{ getStatusLabel(row.status) }}
									</el-tag>
								</template>
							</el-table-column>
							<el-table-column label="Created Time" min-width="160">
								<template #default="{ row }">
									{{ formatDate(row.create_time) }}
								</template>
							</el-table-column>
							<el-table-column label="Next Run Time" min-width="160">
								<template #default="{ row }">
									{{ row.next_run_time ? formatDate(row.next_run_time) : "Not Scheduled" }}
								</template>
							</el-table-column>
							<el-table-column prop="func_path" label="Execute Function" min-width="200" show-overflow-tooltip />
							<el-table-column label="Actions" min-width="120" fixed="right">
								<template #default="{ row }">
									<el-button-group>
										<el-button type="primary" link @click="handleViewLogs(row)">
											<el-icon><Document /></el-icon>
											Logs
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

					<!-- 分页 -->
					<div class="pagination">
						<el-pagination
							v-model:current-page="systemTempCurrentPage"
							v-model:page-size="systemTempPageSize"
							:total="systemTempTotal"
							:page-sizes="[10, 20, 50, 100]"
							layout="total, sizes, prev, pager, next"
							@size-change="handleSystemTempSizeChange"
							@current-change="handleSystemTempCurrentChange"
						/>
					</div>
				</div>
			</el-tab-pane>

			<el-tab-pane label="Runtime Tasks" name="temporary">
				<!-- Temporary task search box -->
				<div class="search-container fade-in">
					<el-form :inline="true" class="search-form">
						<el-form-item label="Task ID">
							<el-input
								v-model="tempSearchParams.taskIds"
								placeholder="Multiple IDs separated by commas"
								clearable
								@keyup.enter="loadTempTasks"
							/>
						</el-form-item>
						<el-form-item label="Task Status">
							<el-select v-model="tempSearchParams.status" placeholder="Select status" clearable>
								<el-option v-for="(label, value) in tempStatusOptions" :key="value" :label="label" :value="value" />
							</el-select>
						</el-form-item>
						<el-form-item>
							<el-button type="primary" @click="loadTempTasks">
								<el-icon><Search /></el-icon>
								Search
							</el-button>
							<el-button>
								<el-icon><Refresh /></el-icon>
								Reset
							</el-button>
						</el-form-item>
					</el-form>
				</div>

				<!-- Temporary tasks table -->
				<div class="table-container fade-in-up">
					<el-table
						v-loading="tempTasksLoading"
						:data="tempTasksData"
						style="width: 100%"
						row-key="id"
						border
						stripe
						:highlight-current-row="true"
					>
						<el-table-column prop="id" label="Task ID" min-width="150" show-overflow-tooltip />
						<el-table-column prop="description" label="Task Description" min-width="180" show-overflow-tooltip />
						<el-table-column label="Task Status" min-width="100">
							<template #default="{ row }">
								<el-tag :type="getTempTaskStatusType(row.status)" effect="plain">
									{{ getTempTaskStatusLabel(row.status) }}
								</el-tag>
							</template>
						</el-table-column>
						<el-table-column label="Start Time" min-width="160">
							<template #default="{ row }">
								{{ row.start_time ? formatDate(row.start_time * 1000) : "Not Started" }}
							</template>
						</el-table-column>
						<el-table-column label="End Time" min-width="160">
							<template #default="{ row }">
								{{ row.end_time ? formatDate(row.end_time * 1000) : "Not Ended" }}
							</template>
						</el-table-column>
						<el-table-column label="Duration" min-width="120">
							<template #default="{ row }">
								{{ row.duration !== null ? `${row.duration.toFixed(2)}s` : "Calculating..." }}
							</template>
						</el-table-column>
						<el-table-column prop="error_message" label="Error Message" min-width="200" show-overflow-tooltip />
						<el-table-column label="Actions" min-width="120" fixed="right">
							<template #default="{ row }">
								<el-button-group>
									<el-button type="primary" link @click="handleViewTempLogs(row)">
										<el-icon><Document /></el-icon>
										Logs
									</el-button>
									<el-button
										v-if="row.status === 'pending' || row.status === 'running'"
										type="danger"
										link
										@click="handleCancelTempTask(row)"
									>
										<el-icon><Delete /></el-icon>
										Cancel
									</el-button>
								</el-button-group>
							</template>
						</el-table-column>
					</el-table>
				</div>
			</el-tab-pane>
		</el-tabs>

		<!-- Task form dialog -->
		<el-dialog
			v-model="dialogVisible"
			:title="formMode === 'add' ? 'Add Task' : 'Edit Task'"
			width="800px"
			destroy-on-close
		>
			<el-form :model="form" label-width="120px" ref="formRef" :rules="formRules">
				<el-form-item label="Task Name" prop="name">
					<el-input v-model="form.name" placeholder="Please enter task name" />
				</el-form-item>
				<el-form-item label="Task Type" prop="task_type">
					<el-input v-model="form.task_type" placeholder="Please enter task type, e.g.: notification" />
				</el-form-item>
				<el-form-item label="Trigger Type" prop="trigger_type">
					<el-select v-model="form.trigger_type" placeholder="Please select trigger type" style="width: 100%">
						<el-option label="Date Trigger" :value="TriggerType.DATE" />
						<el-option label="Interval Trigger" :value="TriggerType.INTERVAL" />
						<el-option label="Cron Trigger" :value="TriggerType.CRON" />
					</el-select>
				</el-form-item>

				<!-- Display different parameter forms based on trigger type -->
				<template v-if="form.trigger_type === TriggerType.DATE">
					<el-form-item label="Execute Time" prop="trigger_date">
						<el-date-picker
							v-model="triggerDate"
							type="datetime"
							placeholder="Select execute time"
							format="YYYY-MM-DD HH:mm:ss"
							value-format="YYYY-MM-DDTHH:mm:ss"
							style="width: 100%"
							@change="updateTriggerArgs"
						/>
					</el-form-item>
				</template>

				<template v-if="form.trigger_type === TriggerType.INTERVAL">
					<el-form-item label="Interval Settings">
						<el-row :gutter="10">
							<el-col :span="6">
								<el-form-item label="Days" label-width="30px">
									<el-input-number v-model="intervalDays" :min="0" @change="updateTriggerArgs" />
								</el-form-item>
							</el-col>
							<el-col :span="6">
								<el-form-item label="Hours" label-width="30px">
									<el-input-number v-model="intervalHours" :min="0" :max="23" @change="updateTriggerArgs" />
								</el-form-item>
							</el-col>
							<el-col :span="6">
								<el-form-item label="Minutes" label-width="30px">
									<el-input-number v-model="intervalMinutes" :min="0" :max="59" @change="updateTriggerArgs" />
								</el-form-item>
							</el-col>
							<el-col :span="6">
								<el-form-item label="Seconds" label-width="30px">
									<el-input-number v-model="intervalSeconds" :min="0" :max="59" @change="updateTriggerArgs" />
								</el-form-item>
							</el-col>
						</el-row>
					</el-form-item>
				</template>

				<template v-if="form.trigger_type === TriggerType.CRON">
					<el-form-item label="Cron Expression">
						<el-row :gutter="10">
							<el-col :span="4">
								<el-form-item label="Minute" label-width="30px">
									<el-input v-model="cronMinute" placeholder="0-59" @change="updateTriggerArgs" />
								</el-form-item>
							</el-col>
							<el-col :span="4">
								<el-form-item label="Hour" label-width="30px">
									<el-input v-model="cronHour" placeholder="0-23" @change="updateTriggerArgs" />
								</el-form-item>
							</el-col>
							<el-col :span="4">
								<el-form-item label="Day" label-width="30px">
									<el-input v-model="cronDay" placeholder="1-31" @change="updateTriggerArgs" />
								</el-form-item>
							</el-col>
							<el-col :span="4">
								<el-form-item label="Month" label-width="30px">
									<el-input v-model="cronMonth" placeholder="1-12" @change="updateTriggerArgs" />
								</el-form-item>
							</el-col>
							<el-col :span="8">
								<el-form-item label="Week" label-width="30px">
									<el-input v-model="cronDayOfWeek" placeholder="0-6 (0=Sunday)" @change="updateTriggerArgs" />
								</el-form-item>
							</el-col>
						</el-row>
					</el-form-item>
				</template>

				<el-form-item label="Execute Function Path" prop="func_path">
					<el-select
						v-model="form.func_path"
						filterable
						placeholder="Please select execute function"
						style="width: 100%"
						@change="handleFunctionChange"
					>
						<el-option
							v-for="task in registeredTasks"
							:key="task.func_path"
							:label="`${task.name} (${task.func_path})`"
							:value="task.func_path"
						>
							<div style="display: flex; justify-content: space-between; align-items: center">
								<span>{{ task.name }}</span>
								<span style="color: #8492a6; font-size: 13px">{{ task.func_path }}</span>
							</div>
							<div style="font-size: 12px; color: #8492a6; margin-top: 5px">{{ task.description }}</div>
						</el-option>
					</el-select>
				</el-form-item>
				<el-form-item label="Function Arguments" prop="func_args_str">
					<el-input
						v-model="funcArgsStr"
						type="textarea"
						:rows="4"
						placeholder="Please enter function arguments in JSON format, e.g.: {}"
						@change="updateFuncArgs"
					/>
				</el-form-item>
				<el-form-item label="Max Instances" prop="max_instances">
					<el-input-number v-model="form.max_instances" :min="1" :max="10" />
				</el-form-item>
				<el-form-item label="Task Description" prop="description">
					<el-input v-model="form.description" type="textarea" :rows="3" placeholder="Please enter task description" />
				</el-form-item>
			</el-form>
			<template #footer>
				<div class="dialog-footer">
					<el-button @click="dialogVisible = false">Cancel</el-button>
					<el-button type="primary" @click="submitForm">Confirm</el-button>
				</div>
			</template>
		</el-dialog>

		<!-- Task execution logs dialog -->
		<el-dialog v-model="logsDialogVisible" title="Task Execution Logs" width="900px">
			<div v-if="selectedTask" class="selected-task-info">
				<h3>{{ selectedTask.name }}</h3>
				<p>{{ selectedTask.description || "No Description" }}</p>
			</div>

			<div class="logs-table">
				<el-table v-loading="logsLoading" :data="executionLogs" style="width: 100%" border stripe>
					<el-table-column prop="id" label="Log ID" width="80" show-overflow-tooltip />
					<el-table-column label="Start Time" width="180">
						<template #default="{ row }">
							{{ formatDate(row.start_time) }}
						</template>
					</el-table-column>
					<el-table-column label="End Time" width="180">
						<template #default="{ row }">
							{{ row.end_time ? formatDate(row.end_time) : "Executing..." }}
						</template>
					</el-table-column>
					<el-table-column label="Status" width="100">
						<template #default="{ row }">
							<el-tag :type="getStatusType(row.status)" effect="plain">
								{{ getStatusLabel(row.status) }}
							</el-tag>
						</template>
					</el-table-column>
					<el-table-column label="Execution Result" min-width="200">
						<template #default="{ row }">
							<div v-if="row.result" class="result-content">
								<el-tooltip effect="dark" placement="top" :content="row.result">
									<el-button link type="primary" @click="showResultDetails(row.result)"> View Details </el-button>
								</el-tooltip>
							</div>
							<span v-else>{{ row.status === TaskStatus.RUNNING ? "Executing..." : "No Result" }}</span>
						</template>
					</el-table-column>
					<el-table-column label="Error Message" min-width="200">
						<template #default="{ row }">
							<span v-if="row.error" class="error-message">{{ row.error }}</span>
							<span v-else>No Error</span>
						</template>
					</el-table-column>
				</el-table>
			</div>

			<!-- Log pagination -->
			<div class="logs-pagination">
				<el-pagination
					v-model:current-page="logsCurrentPage"
					v-model:page-size="logsPageSize"
					:total="logsTotal"
					:page-sizes="[10, 20, 50, 100]"
					layout="total, sizes, prev, pager, next"
					@size-change="handleLogsSizeChange"
					@current-change="handleLogsPageChange"
				/>
			</div>
		</el-dialog>

		<!-- Result details dialog -->
		<el-dialog v-model="resultDialogVisible" title="Execution Result Details" width="600px">
			<pre class="result-details">{{ resultDetails }}</pre>
		</el-dialog>
	</div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Plus, Edit, Delete, VideoPlay, Document, Refresh, Search } from "@element-plus/icons-vue";
import type { FormInstance, FormRules } from "element-plus";
import * as TaskManageApi from "@/api/task_manage";
import { TaskStatus, TriggerType, TaskManage as ITaskManage, TaskExecutionLog } from "@/types/task-manage";

// 标签页
const activeTab = ref("scheduled");
// 子面板选择
const scheduledSubPanel = ref("system-temp");

// 常规定时任务数据
const regularTasksLoading = ref(false);
const regularTasksData = ref<ITaskManage[]>([]);
const regularTotal = ref(0);
const regularCurrentPage = ref(1);
const regularPageSize = ref(10);

// 系统临时任务数据
const systemTempTasksLoading = ref(false);
const systemTempTasksData = ref<any[]>([]);
const systemTempTotal = ref(0);
const systemTempCurrentPage = ref(1);
const systemTempPageSize = ref(10);

// 任务类型列表
const taskTypes = ref<string[]>([]);

// 定时任务搜索参数
const scheduledSearchParams = reactive({
	taskIds: "",
	status: undefined as TaskStatus | undefined,
	taskType: undefined as string | undefined,
});

// 系统临时任务搜索参数
const systemTempSearchParams = reactive({
	taskIds: "",
	status: undefined as TaskStatus | undefined,
});

// 临时任务搜索参数
const tempSearchParams = reactive({
	taskIds: "",
	status: undefined as string | undefined,
});

// Status options
const statusOptions = {
	[TaskStatus.PENDING]: "Pending",
	[TaskStatus.RUNNING]: "Running",
	[TaskStatus.PAUSED]: "Paused",
	[TaskStatus.COMPLETED]: "Completed",
	[TaskStatus.FAILED]: "Failed",
};

// Temporary task status options
const tempStatusOptions = {
	pending: "Pending",
	running: "Running",
	completed: "Completed",
	failed: "Failed",
	timeout: "Timeout",
	cancelled: "Cancelled",
};

// 临时任务相关
const tempTasksLoading = ref(false);
const tempTasksData = ref<any[]>([]);

// 表单相关
const dialogVisible = ref(false);
const formMode = ref<"add" | "edit">("add");
const formRef = ref<FormInstance>();

// 初始化表单数据
const resetForm = () => ({
	id: "",
	name: "",
	task_type: "",
	status: TaskStatus.PENDING,
	trigger_type: TriggerType.INTERVAL,
	trigger_args: {},
	func_path: "",
	func_args: {},
	max_instances: 1,
	description: "",
});

// 表单数据
const form = reactive(resetForm());

// 触发器参数辅助变量
const triggerDate = ref("");
const intervalDays = ref(0);
const intervalHours = ref(0);
const intervalMinutes = ref(0);
const intervalSeconds = ref(0);
const cronMinute = ref("*");
const cronHour = ref("*");
const cronDay = ref("*");
const cronMonth = ref("*");
const cronDayOfWeek = ref("*");

// 函数参数辅助变量
const funcArgsStr = ref("{}");

// 注册的任务列表
const registeredTasks = ref<any[]>([]);

// 更新触发器参数
const updateTriggerArgs = () => {
	if (form.trigger_type === TriggerType.DATE) {
		form.trigger_args = {
			run_date: triggerDate.value,
		};
	} else if (form.trigger_type === TriggerType.INTERVAL) {
		form.trigger_args = {
			days: intervalDays.value || undefined,
			hours: intervalHours.value || undefined,
			minutes: intervalMinutes.value || undefined,
			seconds: intervalSeconds.value || undefined,
		};
		// 移除未定义的属性
		Object.keys(form.trigger_args).forEach((key) => {
			if (form.trigger_args[key] === undefined) {
				delete form.trigger_args[key];
			}
		});
	} else if (form.trigger_type === TriggerType.CRON) {
		form.trigger_args = {
			minute: cronMinute.value,
			hour: cronHour.value,
			day: cronDay.value,
			month: cronMonth.value,
			day_of_week: cronDayOfWeek.value,
		};
	}
};

// 更新函数参数
const updateFuncArgs = () => {
	try {
		form.func_args = JSON.parse(funcArgsStr.value);
	} catch (e) {
		ElMessage.error("函数参数JSON格式错误");
	}
};

// 设置触发器表单值
const setTriggerFormValues = (triggerArgs: any) => {
	if (form.trigger_type === TriggerType.DATE) {
		triggerDate.value = triggerArgs.run_date || "";
	} else if (form.trigger_type === TriggerType.INTERVAL) {
		intervalDays.value = triggerArgs.days || 0;
		intervalHours.value = triggerArgs.hours || 0;
		intervalMinutes.value = triggerArgs.minutes || 0;
		intervalSeconds.value = triggerArgs.seconds || 0;
	} else if (form.trigger_type === TriggerType.CRON) {
		cronMinute.value = triggerArgs.minute || "*";
		cronHour.value = triggerArgs.hour || "*";
		cronDay.value = triggerArgs.day || "*";
		cronMonth.value = triggerArgs.month || "*";
		cronDayOfWeek.value = triggerArgs.day_of_week || "*";
	}
};

// Form validation rules
const formRules = reactive<FormRules>({
	name: [{ required: true, message: "Please enter task name", trigger: "blur" }],
	task_type: [{ required: true, message: "Please enter task type", trigger: "blur" }],
	trigger_type: [{ required: true, message: "Please select trigger type", trigger: "change" }],
	func_path: [{ required: true, message: "Please enter execute function path", trigger: "blur" }],
});

// 日志相关
const executionLogs = ref<TaskExecutionLog[]>([]);
const logsDialogVisible = ref(false);
const selectedTask = ref<ITaskManage | null>(null);
const logsLoading = ref(false);
const logsTotal = ref(0);
const logsCurrentPage = ref(1);
const logsPageSize = ref(10);

// 结果详情
const resultDialogVisible = ref(false);
const resultDetails = ref("");

// 生命周期钩子
onMounted(() => {
	loadRegularTasks();
	loadSystemTempTasks();
	loadRegisteredTasks();
	loadTempTasks();
	extractTaskTypes();
});

// 提取系统中所有任务类型
const extractTaskTypes = async () => {
	try {
		const res: any = await TaskManageApi.getTaskList({
			page: 1,
			size: 100,
		});
		const types = new Set<string>();
		res.items.forEach((task) => {
			if (task.task_type) {
				types.add(task.task_type);
			}
		});
		taskTypes.value = Array.from(types);
	} catch (error) {
		console.error("Failed to load task types", error);
	}
};

// 监听标签页切换
watch(activeTab, (newVal) => {
	if (newVal === "temporary") {
		loadTempTasks();
	} else if (newVal === "scheduled") {
		if (scheduledSubPanel.value === "regular") {
			loadRegularTasks();
		} else {
			loadSystemTempTasks();
		}
	}
});

// 监听子面板切换
watch(scheduledSubPanel, (newVal) => {
	if (newVal === "regular") {
		loadRegularTasks();
	} else {
		loadSystemTempTasks();
	}
});

// 加载常规定时任务
const loadRegularTasks = async () => {
	regularTasksLoading.value = true;
	try {
		const params: any = {
			page: regularCurrentPage.value,
			size: regularPageSize.value,
			include_temp_tasks: false, // 不包含系统临时任务
		};

		// 添加搜索参数
		if (scheduledSearchParams.taskIds) {
			params.task_ids = scheduledSearchParams.taskIds;
		}
		if (scheduledSearchParams.status) {
			params.status = scheduledSearchParams.status;
		}
		if (scheduledSearchParams.taskType) {
			params.task_type = scheduledSearchParams.taskType;
		}

		const res: any = await TaskManageApi.getTaskList(params);
		regularTasksData.value = res.items;
		regularTotal.value = res.total;
	} catch (error) {
		console.error("Failed to load regular scheduled tasks", error);
		ElMessage.error("Failed to load regular scheduled tasks");
	} finally {
		regularTasksLoading.value = false;
	}
};

// 加载系统临时任务
const loadSystemTempTasks = async () => {
	systemTempTasksLoading.value = true;
	try {
		const params: any = {
			page: systemTempCurrentPage.value,
			size: systemTempPageSize.value,
			include_temp_tasks: true, // 包含系统临时任务
		};

		// 添加搜索参数
		if (systemTempSearchParams.taskIds) {
			params.task_ids = systemTempSearchParams.taskIds;
		}
		if (systemTempSearchParams.status) {
			params.status = systemTempSearchParams.status;
		}

		const res: any = await TaskManageApi.getTaskList(params);
		// 过滤出系统临时任务
		systemTempTasksData.value = res.items.filter(
			(task) => task.task_type === "Temporary Task" && task.id.startsWith("temp_task_"),
		);
		systemTempTotal.value = res.total;
	} catch (error) {
		console.error("Failed to load system temporary tasks", error);
		ElMessage.error("Failed to load system temporary tasks");
	} finally {
		systemTempTasksLoading.value = false;
	}
};

// 常规定时任务分页处理
const handleRegularSizeChange = (size: number) => {
	regularPageSize.value = size;
	loadRegularTasks();
};

const handleRegularCurrentChange = (page: number) => {
	regularCurrentPage.value = page;
	loadRegularTasks();
};

// 系统临时任务分页处理
const handleSystemTempSizeChange = (size: number) => {
	systemTempPageSize.value = size;
	loadSystemTempTasks();
};

const handleSystemTempCurrentChange = (page: number) => {
	systemTempCurrentPage.value = page;
	loadSystemTempTasks();
};

// 重置定时任务搜索条件
const resetScheduledSearch = () => {
	scheduledSearchParams.taskIds = "";
	scheduledSearchParams.status = undefined;
	scheduledSearchParams.taskType = undefined;
	loadRegularTasks();
};

// 重置系统临时任务搜索条件
const resetSystemTempSearch = () => {
	systemTempSearchParams.taskIds = "";
	systemTempSearchParams.status = undefined;
	loadSystemTempTasks();
};

// 加载注册的任务列表
const loadRegisteredTasks = async () => {
	try {
		registeredTasks.value = await TaskManageApi.getRegisteredTasks();
	} catch (error) {
		console.error("Failed to load registered task list", error);
		ElMessage.error("Failed to load registered task list");
	}
};

// 处理函数选择变更
const handleFunctionChange = (funcPath: string) => {
	// 查找选中的任务
	const selectedTask = registeredTasks.value.find((task) => task.func_path === funcPath);
	if (selectedTask) {
		// 如果找到，填充函数参数
		const defaultArgs = {};
		if (selectedTask.parameters) {
			// 提取默认参数
			Object.entries(selectedTask.parameters).forEach(([key, value]: [string, any]) => {
				if (value.default !== null && value.default !== undefined) {
					defaultArgs[key] = value.default;
				}
			});
		}
		// 更新函数参数
		form.func_args = defaultArgs;
		funcArgsStr.value = JSON.stringify(defaultArgs, null, 2);

		// 更新任务类型和描述
		if (!form.task_type) {
			form.task_type = selectedTask.tags && selectedTask.tags.length > 0 ? selectedTask.tags[0] : "task";
		}

		if (!form.description && selectedTask.description) {
			form.description = selectedTask.description;
		}
	}
};

// 加载任务执行日志
const loadTaskLogs = async (taskId: string) => {
	logsLoading.value = true;
	try {
		const params = {
			page: logsCurrentPage.value,
			size: logsPageSize.value,
		};

		const res: any = await TaskManageApi.getTaskLogs(taskId, params);
		executionLogs.value = res.items;
		logsTotal.value = res.total;
	} catch (error) {
		console.error("Failed to load task execution logs", error);
		ElMessage.error("Failed to load task execution logs");
	} finally {
		logsLoading.value = false;
	}
};

// 日志分页处理
const handleLogsSizeChange = (size: number) => {
	logsPageSize.value = size;
	if (selectedTask.value) {
		loadTaskLogs(selectedTask.value.id);
	}
};

const handleLogsPageChange = (page: number) => {
	logsCurrentPage.value = page;
	if (selectedTask.value) {
		loadTaskLogs(selectedTask.value.id);
	}
};

// 添加任务
const handleAddTask = () => {
	formMode.value = "add";
	Object.assign(form, resetForm());
	funcArgsStr.value = "{}";
	dialogVisible.value = true;
};

// 编辑任务
const handleEditTask = (row: ITaskManage) => {
	formMode.value = "edit";
	Object.assign(form, row);

	// 设置函数参数
	funcArgsStr.value = JSON.stringify(row.func_args, null, 2);

	// 设置触发器参数
	setTriggerFormValues(row.trigger_args);

	dialogVisible.value = true;
};

// 删除任务
const handleDeleteTask = (row: ITaskManage) => {
	ElMessageBox.confirm("Are you sure to delete this task? This operation cannot be undone!", "Confirm", {
		confirmButtonText: "Confirm",
		cancelButtonText: "Cancel",
		type: "warning",
	})
		.then(async () => {
			try {
				await TaskManageApi.deleteTask(row.id);
				ElMessage.success("Delete successful");
			} catch (error) {
				console.error("Failed to delete task", error);
				ElMessage.error("Failed to delete task");
			}
		})
		.catch(() => {
			// 取消删除
		});
};

// 暂停/恢复任务
const handlePauseResumeTask = async (row: ITaskManage) => {
	try {
		if (row.status === TaskStatus.PAUSED) {
			await TaskManageApi.resumeTask(row.id);
			ElMessage.success("Task resumed");
		} else {
			await TaskManageApi.pauseTask(row.id);
			ElMessage.success("Task paused");
		}
	} catch (error) {
		console.error("Operation failed", error);
		ElMessage.error("Operation failed");
	}
};

// 触发任务
const handleTriggerTask = async (row: ITaskManage) => {
	try {
		await TaskManageApi.triggerTask(row.id);
		ElMessage.success("Task triggered");
	} catch (error) {
		console.error("Failed to trigger task", error);
		ElMessage.error("Failed to trigger task");
	}
};

// 查看任务日志
const handleViewLogs = (row: ITaskManage) => {
	selectedTask.value = row;
	logsCurrentPage.value = 1;
	loadTaskLogs(row.id);
	logsDialogVisible.value = true;
};

// 查看结果详情
const showResultDetails = (result: string) => {
	try {
		resultDetails.value = JSON.stringify(JSON.parse(result), null, 2);
	} catch {
		resultDetails.value = result;
	}
	resultDialogVisible.value = true;
};

// 提交表单
const submitForm = async () => {
	if (!formRef.value) return;

	await formRef.value.validate(async (valid) => {
		if (valid) {
			// 更新触发器参数和函数参数
			updateTriggerArgs();
			updateFuncArgs();

			try {
				if (formMode.value === "add") {
					await TaskManageApi.addTask(form);
					ElMessage.success("Add successful");
				} else {
					await TaskManageApi.updateTask(form.id, form);
					ElMessage.success("Update successful");
				}
				dialogVisible.value = false;
			} catch (error) {
				console.error("Failed to save task", error);
			ElMessage.error("Failed to save task");
			}
		}
	});
};

// 格式化日期
const formatDate = (dateStr: any) => {
	if (!dateStr) return "";
	const date = new Date(dateStr);
	return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(
		2,
		"0",
	)} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}:${String(
		date.getSeconds(),
	).padStart(2, "0")}`;
};

// 获取状态类型
const getStatusType: any = (status: TaskStatus) => {
	const statusMap = {
		[TaskStatus.PENDING]: "info",
		[TaskStatus.RUNNING]: "primary",
		[TaskStatus.PAUSED]: "warning",
		[TaskStatus.COMPLETED]: "success",
		[TaskStatus.FAILED]: "danger",
	};
	return statusMap[status] || "info";
};

// 获取状态标签
const getStatusLabel = (status: TaskStatus) => {
	const statusMap = {
		[TaskStatus.PENDING]: "Pending",
		[TaskStatus.RUNNING]: "Running",
		[TaskStatus.PAUSED]: "Paused",
		[TaskStatus.COMPLETED]: "Completed",
		[TaskStatus.FAILED]: "Failed",
	};
	return statusMap[status] || status;
};

// 获取触发器类型
const getTriggerType: any = (triggerType: TriggerType) => {
	const triggerMap = {
		[TriggerType.DATE]: "success",
		[TriggerType.INTERVAL]: "primary",
		[TriggerType.CRON]: "warning",
	};
	return triggerMap[triggerType] || "info";
};

// 获取触发器标签
const getTriggerLabel = (triggerType: TriggerType) => {
	const triggerMap = {
		[TriggerType.DATE]: "Date",
		[TriggerType.INTERVAL]: "Interval",
		[TriggerType.CRON]: "Cron",
	};
	return triggerMap[triggerType] || triggerType;
};

// 加载临时任务
const loadTempTasks = async () => {
	tempTasksLoading.value = true;
	try {
		const params: any = {};

		// 添加搜索参数
		if (tempSearchParams.taskIds) {
			params.task_ids = tempSearchParams.taskIds;
		}
		if (tempSearchParams.status) {
			params.status = tempSearchParams.status;
		}

		const res = await TaskManageApi.getTempTasks(params);
		tempTasksData.value = res;
	} catch (error) {
		console.error("Failed to load temporary tasks", error);
		ElMessage.error("Failed to load temporary tasks");
	} finally {
		tempTasksLoading.value = false;
	}
};

// 取消临时任务
const handleCancelTempTask = (row: any) => {
	ElMessageBox.confirm("Are you sure to cancel this temporary task? This operation cannot be undone!", "Confirm", {
		confirmButtonText: "Confirm",
		cancelButtonText: "Cancel",
		type: "warning",
	})
		.then(async () => {
			try {
				await TaskManageApi.cancelTempTask(row.id);
				ElMessage.success("Cancel successful");
				loadTempTasks();
			} catch (error) {
				console.error("Failed to cancel temporary task", error);
			ElMessage.error("Failed to cancel temporary task");
			}
		})
		.catch(() => {
			// 取消操作
		});
};

// 获取临时任务状态类型
const getTempTaskStatusType: any = (status: string) => {
	const statusMap: Record<string, string> = {
		pending: "info",
		running: "primary",
		completed: "success",
		failed: "danger",
		timeout: "warning",
		cancelled: "info",
	};
	return statusMap[status] || "info";
};

// 获取临时任务状态标签
const getTempTaskStatusLabel = (status: string) => {
	const statusMap: Record<string, string> = {
		pending: "Pending",
		running: "Running",
		completed: "Completed",
		failed: "Failed",
		timeout: "Timeout",
		cancelled: "Cancelled",
	};
	return statusMap[status] || status;
};

// 查看临时任务日志
const handleViewTempLogs = (row: any) => {
	selectedTask.value = {
		id: row.id,
		name: row.description,
		description: `Temporary Task ${row.id}`,
		...row,
	};
	logsCurrentPage.value = 1;
	loadTempTaskLogs(row.id);
	logsDialogVisible.value = true;
};

// 加载临时任务执行日志
const loadTempTaskLogs = async (taskId: string) => {
	logsLoading.value = true;
	try {
		const params = {
			page: logsCurrentPage.value,
			size: logsPageSize.value,
		};

		const res: any = await TaskManageApi.getTempTaskLogs(taskId, params);
		executionLogs.value = res.items;
		logsTotal.value = res.total;
	} catch (error) {
		console.error("Failed to load temporary task execution logs", error);
		ElMessage.error("Failed to load temporary task execution logs");
	} finally {
		logsLoading.value = false;
	}
};
</script>

<style lang="scss" scoped>
.task-manage {
	padding: 20px;

	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 20px;

		.title {
			font-size: 24px;
			font-weight: bold;
			margin: 0;
		}
	}

	.task-tabs {
		margin-bottom: 20px;
	}

	.sub-panel-selector {
		margin-bottom: 20px;
		display: flex;
		justify-content: center;
	}

	.panel-container {
		margin-top: 20px;
	}

	.search-container {
		margin-bottom: 20px;
		padding: 15px;
		background-color: #f9f9f9;
		border-radius: 8px;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.03);

		.search-form {
			display: flex;
			flex-wrap: wrap;
			gap: 10px;
		}
	}

	.table-container {
		margin-bottom: 20px;
	}

	.pagination {
		display: flex;
		justify-content: flex-end;
		margin-top: 20px;
	}

	.selected-task-info {
		padding: 10px;
		margin-bottom: 15px;
		background-color: #f8f9fa;
		border-radius: 4px;

		h3 {
			margin: 0 0 5px 0;
			font-size: 18px;
		}

		p {
			margin: 0;
			color: #666;
		}
	}

	.logs-table {
		margin-bottom: 15px;
	}

	.logs-pagination {
		display: flex;
		justify-content: flex-end;
	}

	.error-message {
		color: #f56c6c;
	}

	.result-details {
		max-height: 400px;
		overflow-y: auto;
		background-color: #f8f9fa;
		padding: 10px;
		border-radius: 4px;
		font-family: monospace;
		white-space: pre-wrap;
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
}
</style>
