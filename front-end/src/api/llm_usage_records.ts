import request from "@/utils/request";

/**
 * 创建新的LLM使用记录
 * @param {object} data - 记录数据
 * @returns {Promise<any>} 创建的记录
 */
export function createUsageRecord(data: any) {
	return request({
		url: "llm-usage-records/",
		method: "post",
		data,
	});
}

/**
 * 从LLM响应数据创建使用记录
 * @param {object} data - 响应数据及相关参数
 * @returns {Promise<any>} 创建的记录
 */
export function createFromResponse(data: any) {
	return request({
		url: "llm-usage-records/from-response",
		method: "post",
		data,
	});
}

/**
 * 获取单个使用记录
 * @param {number} recordId - 记录ID
 * @returns {Promise<any>} 找到的记录
 */
export function getUsageRecord(recordId: number) {
	return request({
		url: `llm-usage-records/${recordId}`,
		method: "get",
	});
}

/**
 * 根据请求ID获取使用记录
 * @param {string} requestId - 请求ID
 * @returns {Promise<any>} 找到的记录
 */
export function getByRequestId(requestId: string) {
	return request({
		url: `llm-usage-records/request/${requestId}`,
		method: "get",
	});
}

/**
 * 获取使用记录列表
 * @param {object} params - 分页参数
 * @returns {Promise<any>} 记录列表
 */
export function listUsageRecords(params: { page?: number; size?: number }) {
	return request({
		url: "llm-usage-records/",
		method: "get",
		params,
	});
}

/**
 * 根据条件过滤使用记录
 * @param {object} data - 过滤条件
 * @param {object} params - 分页参数
 * @returns {Promise<any>} 过滤后的记录列表
 */
export function filterUsageRecords(data: any, params: { page?: number; size?: number }) {
	return request({
		url: "llm-usage-records/filter",
		method: "post",
		data,
		params,
	});
}

/**
 * 更新使用记录
 * @param {number} recordId - 记录ID
 * @param {object} data - 更新数据
 * @returns {Promise<any>} 更新后的记录
 */
export function updateUsageRecord(recordId: number, data: any) {
	return request({
		url: `llm-usage-records/${recordId}`,
		method: "put",
		data,
	});
}

/**
 * 删除使用记录
 * @param {number} recordId - 记录ID
 * @returns {Promise<boolean>} 是否成功删除
 */
export function deleteUsageRecord(recordId: number) {
	return request({
		url: `llm-usage-records/${recordId}`,
		method: "delete",
	});
}

/**
 * 获取统计数据
 * @param {object} params - 查询参数
 * @returns {Promise<any>} 统计数据
 */
export function getStatistics(params: {
	start_date?: string;
	end_date?: string;
	vendor_type?: string;
	model_id?: string;
	application_scenario?: string;
}) {
	return request({
		url: "llm-usage-records/statistics/summary",
		method: "get",
		params,
	});
}

/**
 * 获取每日统计数据
 * @param {object} params - 查询参数
 * @returns {Promise<any>} 每日统计数据
 */
export function getDailyStatistics(params: { days?: number; vendor_type?: string; model_id?: string }) {
	return request({
		url: "llm-usage-records/statistics/daily",
		method: "get",
		params,
	});
}
