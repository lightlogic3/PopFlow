import request from "@/utils/request";
import type { TaskManage, TaskExecutionLog } from "@/types/task-manage";

// 由于没有看到完整的类型定义，暂时使用any来定义创建和更新接口
type TaskManageCreate = any;
type TaskManageUpdate = any;

/**
 * 获取任务列表
 */
export function getTaskList(params: any) {
	return request<TaskManage[]>({
		url: "/task-manage/",
		method: "get",
		params,
	});
}

/**
 * 获取注册的任务函数列表
 */
export function getRegisteredTasks() {
	return request<any[]>({
		url: "/task-manage/registered-tasks",
		method: "get",
	});
}

/**
 * 获取单个任务
 */
export function getTask(id: string) {
	return request<TaskManage>({
		url: `/task-manage/${id}`,
		method: "get",
	});
}

/**
 * 创建任务
 */
export function addTask(data: TaskManageCreate) {
	return request<TaskManage>({
		url: "/task-manage/",
		method: "post",
		data,
	});
}

/**
 * 更新任务
 */
export function updateTask(id: string, data: TaskManageUpdate) {
	return request<TaskManage>({
		url: `/task-manage/${id}`,
		method: "put",
		data,
	});
}

/**
 * 删除任务
 */
export function deleteTask(id: string) {
	return request<boolean>({
		url: `/task-manage/${id}`,
		method: "delete",
	});
}

/**
 * 暂停任务
 */
export function pauseTask(id: string) {
	return request<boolean>({
		url: `/task-manage/${id}/pause`,
		method: "post",
	});
}

/**
 * 恢复任务
 */
export function resumeTask(id: string) {
	return request<boolean>({
		url: `/task-manage/${id}/resume`,
		method: "post",
	});
}

/**
 * 立即触发任务
 */
export function triggerTask(id: string) {
	return request<boolean>({
		url: `/task-manage/${id}/trigger`,
		method: "post",
	});
}

/**
 * 获取任务执行日志
 */
export function getTaskLogs(id: string, params: any) {
	return request<TaskExecutionLog[]>({
		url: `/task-manage/${id}/logs`,
		method: "get",
		params,
	});
}

/**
 * 获取临时任务列表
 */
export function getTempTasks(params?: any) {
	return request<any[]>({
		url: "/task-manage/temp-tasks",
		method: "get",
		params,
	});
}

/**
 * 获取单个临时任务
 */
export function getTempTask(id: string) {
	return request<any>({
		url: `/task-manage/temp-tasks/${id}`,
		method: "get",
	});
}

/**
 * 取消临时任务
 */
export function cancelTempTask(id: string) {
	return request<boolean>({
		url: `/task-manage/temp-tasks/${id}/cancel`,
		method: "post",
	});
}

/**
 * 获取临时任务执行日志
 */
export function getTempTaskLogs(id: string, params: any) {
	return request<TaskExecutionLog[]>({
		url: `/task-manage/temp-tasks/${id}/logs`,
		method: "get",
		params,
	});
}
