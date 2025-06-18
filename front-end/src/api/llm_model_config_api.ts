import request from "@/utils/request";

/**
 * 获取提示词配置列表
 */
export function getPromptList(params: { page?: number; size?: number }) {
	return request({
		url: "role_prompt/character-prompt-config/",
		method: "get",
		params,
	});
}

/**
 * 获取模型列表
 * @param params 分页参数
 */
export function getModelList(params: { page?: number; size?: number }) {
	return request({
		url: "llm-model-config/getList/models",
		method: "get",
		params,
	});
}

/**
 * 获取模型版本列表
 * @param model_name 模型名称
 */
export function getModelVersions(model_name: string) {
	return request({
		url: "llm-model-config/getList/model_versions",
		method: "get",
		params: { model_name },
	});
}

/**
 * 获取所有模型配置列表
 * @param {object} params - 查询参数
 * @returns {Promise<any>} 返回模型配置列表
 */
export function getModelConfigList(params: any) {
	return request({
		url: "llm-model-config/model-config/list",
		method: "get",
		params,
	});
}

/**
 * 根据供应商ID获取模型配置列表
 * @param provider_id 供应商ID
 */
export function getModelConfigsByProvider(provider_id: number) {
	return request({
		url: `llm-model-config/by-provider/${provider_id}`,
		method: "get",
	});
}

/**
 * 获取指定ID的模型配置详情
 * @param {string} id - 模型配置ID
 * @returns {Promise<any>} 返回模型配置详情
 */
export function getModelConfigDetail(id: any) {
	return request({
		url: `/llm-model-config/${id}`,
		method: "get",
	});
}

/**
 * 创建模型配置
 * @param data 模型配置数据
 */
export function createModelConfig(data: any) {
	return request({
		url: "llm-model-config/",
		method: "post",
		data,
	});
}

/**
 * 更新模型配置
 * @param config_id 配置ID
 * @param data 模型配置数据
 */
export function updateModelConfig(config_id: number, data: any) {
	return request({
		url: `llm-model-config/${config_id}`,
		method: "put",
		data,
	});
}

/**
 * 更新模型配置状态
 * @param config_id 配置ID
 * @param status 状态：1-启用 0-禁用
 */
export function updateModelConfigStatus(config_id: number, status: number) {
	return request({
		url: `llm-model-config/${config_id}/status`,
		method: "patch",
		params: { status },
	});
}

/**
 * 删除模型配置
 * @param config_id 配置ID
 */
export function deleteModelConfig(config_id: number) {
	return request({
		url: `llm-model-config/${config_id}`,
		method: "delete",
	});
}

/**
 * 获取所有启用状态的模型配置
 */
export function getActiveModelConfigs() {
	return request({
		url: "llm-model-config/active/list",
		method: "get",
	});
}
