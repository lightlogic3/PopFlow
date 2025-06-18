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
 * 根据角色ID获取分页的提示词配置列表
 */
export function getPromptsByRoleId(roleId: string, params?: { page?: number; size?: number }) {
	return request({
		url: `role_prompt/character-prompt-config/by-role/${roleId}`,
		method: "get",
		params,
	});
}

/**
 * 根据类型获取提示词配置列表
 */
export function getPromptListByType(data: { types: string[]; role_ids?: string[]; page?: number; size?: number }) {
	return request({
		url: "role_prompt/character-prompt-config/search",
		method: "post",
		data,
	});
}

/**
 * 获取单个提示词配置
 */
export function getPromptDetail(configId: number) {
	return request({
		url: `role_prompt/character-prompt-config/${configId}`,
		method: "get",
	});
}

/**
 * 创建提示词配置
 */
export function createPrompt(data: {
	role_id: string;
	level: number;
	prompt_text: string;
	status?: number;
	title?: string;
	type?: string;
	dialogue?: string;
	timbre?: string;
	prologue?: string[];
}) {
	return request({
		url: "role_prompt/character-prompt-config/",
		method: "post",
		data,
	});
}
export function createPromptSystem(data: {
	role_id: string;
	level: number;
	prompt_text: string;
	status?: number;
	title?: string;
	type?: string;
	dialogue?: string;
	timbre?: string;
}) {
	return request({
		url: "role_prompt/character-prompt-config/add_system",
		method: "post",
		data,
	});
}

/**
 * 更新提示词配置
 */
export function updatePrompt(
	configId: number,
	data: {
		prompt_text?: string;
		status?: number;
		title?: string;
		level?: number;
		dialogue?: string;
		timbre?: string;
		prologue?: string[];
	},
) {
	return request({
		url: `role_prompt/character-prompt-config/${configId}`,
		method: "put",
		data,
	});
}

/**
 * 删除提示词配置
 */
export function deletePrompt(configId: number) {
	return request({
		url: `role_prompt/character-prompt-config/${configId}`,
		method: "delete",
	});
}

/**
 * 更新提示词配置状态
 */
export function updatePromptStatus(configId: number, status: number) {
	return request({
		url: `role_prompt/character-prompt-config/${configId}/status`,
		method: "patch",
		params: { status },
	});
}
