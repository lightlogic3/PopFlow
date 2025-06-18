import request from "@/utils/request";

/**
 * 创建新的游戏会话
 * @param {object} data - 会话数据
 * @returns {Promise<any>} 创建的会话
 */
export function createSession(data: any) {
	return request({
		url: "task-game-sessions/",
		method: "post",
		data,
	});
}

/**
 * 获取单个会话
 * @param {string} sessionId - 会话ID
 * @returns {Promise<any>} 找到的会话
 */
export function getSession(sessionId: string) {
	return request({
		url: `task-game-sessions/${sessionId}`,
		method: "get",
	});
}

/**
 * 获取会话列表（分页）
 * @param {object} params - 分页参数
 * @returns {Promise<any>} 会话列表
 */
export function listSessions(params: { page?: number; size?: number }) {
	return request({
		url: "task-game-sessions/",
		method: "get",
		params,
	});
}

/**
 * 获取用户的所有会话（分页）
 * @param {string} userId - 用户ID
 * @param {object} params - 分页参数
 * @returns {Promise<any>} 会话列表
 */
export function getSessionsByUser(userId: string, params: { page?: number; size?: number } = {}) {
	return request({
		url: `task-game-sessions/user/${userId}`,
		method: "get",
		params,
	});
}

/**
 * 根据条件过滤会话（分页）
 * @param {object} filters - 过滤条件
 * @returns {Promise<any>} 过滤后的会话列表
 */
export function filterSessions(filters: {
	user_id?: string;
	game_id?: string;
	task_id?: string;
	status?: string;
	start_date?: string;
	end_date?: string;
	page?: number;
	size?: number;
}) {
	return request({
		url: "task-game-sessions/filter",
		method: "post",
		data: filters,
	});
}

/**
 * 更新会话
 * @param {string} sessionId - 会话ID
 * @param {object} data - 更新数据
 * @returns {Promise<any>} 更新后的会话
 */
export function updateSession(sessionId: string, data: any) {
	return request({
		url: `task-game-sessions/${sessionId}`,
		method: "put",
		data,
	});
}

/**
 * 删除会话
 * @param {string} sessionId - 会话ID
 * @returns {Promise<any>} 删除结果
 */
export function deleteSession(sessionId: string) {
	return request({
		url: `task-game-sessions/${sessionId}`,
		method: "delete",
	});
}

/**
 * 获取会话统计数据
 * @param {object} params - 统计参数
 * @returns {Promise<any>} 统计数据
 */
export function getSessionStatistics(params: { user_id?: string; start_date?: string; end_date?: string }) {
	return request({
		url: "task-game-sessions/statistics/summary",
		method: "get",
		params,
	});
}
