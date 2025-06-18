import request from "@/utils/request";

/**
 * 创建新的游戏消息
 * @param {object} data - 消息数据
 * @returns {Promise<any>} 创建的消息
 */
export function createMessage(data: any) {
	return request({
		url: "task-game-messages/",
		method: "post",
		data,
	});
}

/**
 * 获取单个消息
 * @param {number} messageId - 消息ID
 * @returns {Promise<any>} 找到的消息
 */
export function getMessage(messageId: number) {
	return request({
		url: `task-game-messages/${messageId}`,
		method: "get",
	});
}

/**
 * 获取消息列表（分页）
 * @param {object} params - 分页参数
 * @returns {Promise<any>} 消息列表
 */
export function listMessages(params: { page?: number; size?: number }) {
	return request({
		url: "task-game-messages/",
		method: "get",
		params,
	});
}

/**
 * 获取会话的所有消息（分页）
 * @param {string} sessionId - 会话ID
 * @param {object} params - 分页参数
 * @returns {Promise<any>} 消息列表
 */
export function getMessagesBySession(sessionId: string, params: { page?: number; size?: number } = {}) {
	return request({
		url: `task-game-messages/session/${sessionId}`,
		method: "get",
		params,
	});
}

/**
 * 获取会话特定轮次的消息
 * @param {string} sessionId - 会话ID
 * @param {number} roundNum - 轮次号
 * @returns {Promise<any>} 消息列表
 */
export function getMessagesByRound(sessionId: string, roundNum: number) {
	return request({
		url: `task-game-messages/session/${sessionId}/round/${roundNum}`,
		method: "get",
	});
}

/**
 * 获取会话最新的消息
 * @param {string} sessionId - 会话ID
 * @param {number} limit - 限制消息数量
 * @returns {Promise<any>} 消息列表
 */
export function getLatestMessages(sessionId: string, limit: number = 1) {
	return request({
		url: `task-game-messages/session/${sessionId}/latest`,
		method: "get",
		params: { limit },
	});
}

/**
 * 根据条件过滤消息（分页）
 * @param {object} filters - 过滤条件
 * @returns {Promise<any>} 过滤后的消息列表
 */
export function filterMessages(filters: {
	session_id?: string;
	user_id?: string;
	message_type?: string;
	round_num?: number;
	start_date?: string;
	end_date?: string;
	page?: number;
	size?: number;
}) {
	return request({
		url: "task-game-messages/filter",
		method: "post",
		data: filters,
	});
}

/**
 * 更新消息
 * @param {number} messageId - 消息ID
 * @param {object} data - 更新数据
 * @returns {Promise<any>} 更新后的消息
 */
export function updateMessage(messageId: number, data: any) {
	return request({
		url: `task-game-messages/${messageId}`,
		method: "put",
		data,
	});
}

/**
 * 删除消息
 * @param {number} messageId - 消息ID
 * @returns {Promise<any>} 删除结果
 */
export function deleteMessage(messageId: number) {
	return request({
		url: `task-game-messages/${messageId}`,
		method: "delete",
	});
}

/**
 * 删除会话的所有消息
 * @param {string} sessionId - 会话ID
 * @returns {Promise<any>} 删除的消息数量
 */
export function deleteSessionMessages(sessionId: string) {
	return request({
		url: `task-game-messages/session/${sessionId}`,
		method: "delete",
	});
}

/**
 * 获取消息统计数据
 * @param {object} params - 统计参数
 * @returns {Promise<any>} 统计数据
 */
export function getMessageStatistics(params: { session_id?: string; start_date?: string; end_date?: string }) {
	return request({
		url: "task-game-messages/statistics/summary",
		method: "get",
		params,
	});
}
