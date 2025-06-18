import request from "@/utils/request";

export const getTaskList = (roleId: string, params?: any) => {
	return request({
		url: `role-tasks/by-role/${roleId}`,
		method: "get",
		params,
	});
};

/**
 * 获取角色任务列表
 * @param {object} params - 分页参数
 * @returns {Promise<any>} 任务列表
 */
export const getTaskLists = (params?: any) => {
	return request({
		url: "role-tasks",
		method: "get",
		params,
	});
};

/**
 * 根据角色ID获取任务列表
 * @param {string} roleId - 角色ID
 * @param {object} params - 分页参数
 * @returns {Promise<any>} 任务列表
 */
export const getTasksByRoleId = (roleId: string, params?: any) => {
	return request({
		url: `role-tasks/by-role/${roleId}`,
		method: "get",
		params,
	});
};

/**
 * 获取任务详情
 * @param {string} taskId - 任务ID
 * @returns {Promise<any>} 任务详情
 */
export const getTaskById = (taskId: string) => {
	return request({
		url: `role-tasks/${taskId}`,
		method: "get",
	});
};

/**
 * 创建任务
 * @param {object} data - 任务数据
 * @returns {Promise<any>} 创建的任务
 */
export const addTask = (data: any) => {
	return request({
		url: "role-tasks",
		method: "post",
		data,
	});
};

/**
 * 更新任务
 * @param {string} taskId - 任务ID
 * @param {object} data - 更新数据
 * @returns {Promise<any>} 更新后的任务
 */
export const updateTask = (taskId: string, data: any) => {
	return request({
		url: `role-tasks/${taskId}`,
		method: "put",
		data,
	});
};

/**
 * 删除任务
 * @param {string} taskId - 任务ID
 * @returns {Promise<boolean>} 是否成功删除
 */
export const deleteTask = (taskId: string) => {
	return request({
		url: `role-tasks/${taskId}`,
		method: "delete",
	});
};

/**
 * 删除角色的所有任务
 * @param {string} roleId - 角色ID
 * @returns {Promise<boolean>} 是否成功删除
 */
export const deleteTasksByRoleId = (roleId: string) => {
	return request({
		url: `role-tasks/by-role/${roleId}`,
		method: "delete",
	});
};
