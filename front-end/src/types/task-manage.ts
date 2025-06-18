import { Ref } from "vue";

export enum TaskStatus {
	PENDING = "pending",
	RUNNING = "running",
	PAUSED = "paused",
	COMPLETED = "completed",
	FAILED = "failed",
}

export enum TriggerType {
	DATE = "date",
	INTERVAL = "interval",
	CRON = "cron",
}

export interface TaskTriggerArgs {
	[key: string]: any;
}

export interface TaskFuncArgs {
	[key: string]: any;
}

export interface TaskManage {
	id: string;
	name: string;
	task_type: string;
	status: TaskStatus;
	trigger_type: TriggerType;
	trigger_args: TaskTriggerArgs;
	func_path: string;
	func_args: TaskFuncArgs;
	next_run_time?: string;
	max_instances: number;
	description?: string;
	create_time: string;
	update_time: string;
}

export interface TaskExecutionLog {
	id: string;
	task_id: string;
	start_time: string;
	end_time?: string;
	status: TaskStatus;
	result?: string;
	error?: string;
}

export interface TaskForm {
	id: string;
	name: string;
	task_type: string;
	status: TaskStatus;
	trigger_type: TriggerType;
	trigger_args: TaskTriggerArgs;
	func_path: string;
	func_args: TaskFuncArgs;
	next_run_time?: string;
	max_instances: number;
	description?: string;
}

export interface TaskFormState {
	form: TaskForm;
	rules: any;
}

export interface TaskManageState {
	loading: Ref<boolean>;
	tableData: Ref<TaskManage[]>;
	total: Ref<number>;
	currentPage: Ref<number>;
	pageSize: Ref<number>;
	dialogVisible: Ref<boolean>;
	formMode: Ref<"add" | "edit">;
	form: TaskForm;
	formRules: any;
	executionLogs: Ref<TaskExecutionLog[]>;
	logsDialogVisible: Ref<boolean>;
	selectedTask: Ref<TaskManage | null>;
	logsLoading: Ref<boolean>;
	logsTotal: Ref<number>;
	logsCurrentPage: Ref<number>;
	logsPageSize: Ref<number>;
}
