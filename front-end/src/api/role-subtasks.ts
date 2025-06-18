import request from "@/utils/request";

/**
 * 获取角色子任务列表
 * @param {string} taskId - 主任务ID
 * @param {object} params - 分页参数
 * @returns {Promise<any>} 子任务列表
 */
export const getSubtaskList = (taskId: string, params?: any) => {
	return request({
		url: `role-subtasks/by-task/${taskId}`,
		method: "get",
		params,
	});
};

/**
 * 获取子任务详情
 * @param {string} subtaskId - 子任务ID
 * @returns {Promise<any>} 子任务详情
 */
export const getSubtaskById = (subtaskId: string) => {
	return request({
		url: `role-subtasks/${subtaskId}`,
		method: "get",
	});
};

/**
 * 创建子任务
 * @param {object} data - 子任务数据
 * @returns {Promise<any>} 创建的子任务
 */
export const addSubtask = (data: any) => {
	return request({
		url: "role-subtasks",
		method: "post",
		data,
	});
};

/**
 * 更新子任务
 * @param {string} subtaskId - 子任务ID
 * @param {object} data - 更新数据
 * @returns {Promise<any>} 更新后的子任务
 */
export const updateSubtask = (subtaskId: string, data: any) => {
	return request({
		url: `role-subtasks/${subtaskId}`,
		method: "put",
		data,
	});
};

/**
 * 删除子任务
 * @param {string} subtaskId - 子任务ID
 * @returns {Promise<boolean>} 是否成功删除
 */
export const deleteSubtask = (subtaskId: string) => {
	return request({
		url: `role-subtasks/${subtaskId}`,
		method: "delete",
	});
};

/**
 * 删除主任务所有子任务
 * @param {string} taskId - 主任务ID
 * @returns {Promise<boolean>} 是否成功删除
 */
export const deleteSubtasksByTaskId = (taskId: string) => {
	return request({
		url: `role-subtasks/by-task/${taskId}`,
		method: "delete",
	});
};

/**
 * 自动生成任务
 * @param {object} data - 自动任务生成数据
 * @returns {Promise<any>} 生成结果
 */
export const autoGenerateTask = (data: any) => {
	return request({
		url: "role-subtasks/auto_task",
		method: "post",
		data,
	});
};
