import request from "@/utils/request";
import { createStreamRequest, executeStreamRequest } from "@/utils/streamRequest";
import type { LLMProviderCreate, LLMProviderUpdate } from "@/types/llm";

/**
 * LLM提供商类型定义
 */
export interface LLMProvider {
	id: number;
	provider_name: string;
	provider_sign?: string;
	model_name: string;
	api_url: string;
	api_key: string;
	remark?: string;
	status: number;
	total_price?: number;
	created_at: string;
	updated_at: string;
}

/**
 * LLM模型类型定义
 */
export interface LLMModel {
	id: number;
	model_name: string;
	model_id: string;
	model_type: string;
	provider_sign?: string;
	status: number;
	capabilities: string;
	introduction: string;
	icon_url: string;
	input_price: number;
	output_price: number;
}

/**
 * LLM提供商层级结构类型定义
 */
export interface LLMProviderHierarchy {
	id: number;
	provider_name: string;
	provider_sign?: string;
	model_name: string;
	api_url: string;
	status: number;
	remark: string;
	models: LLMModel[];
}

/**
 * 获取LLM提供商配置列表
 */
export function getLLMProviderList(params: { skip?: number; limit?: number }) {
	return request({
		url: "llm_config_router/llm-provider-config/",
		method: "get",
		params,
	});
}

/**
 * 获取启用状态的提供商配置
 */
export function getActiveLLMProviders() {
	return request({
		url: "llm_config_router/llm-provider-config/active/list",
		method: "get",
	});
}

/**
 * 获取所有提供商及其子模型的层级结构
 */
export function getLLMProvidersWithModels() {
	return request({
		url: "llm_config_router/llm-provider-config/hierarchy/all",
		method: "get",
	});
}

/**
 * 获取所有启用状态的提供商及其启用状态的子模型的层级结构
 */
export function getActiveLLMProvidersWithModels() {
	return request({
		url: "llm_config_router/llm-provider-config/hierarchy/active",
		method: "get",
	});
}

/**
 * 获取单个提供商配置
 */
export function getLLMProviderById(id: number) {
	return request({
		url: `llm_config_router/llm-provider-config/${id}`,
		method: "get",
	});
}

/**
 * 根据名称获取提供商配置
 */
export function getLLMProviderByName(name: string) {
	return request({
		url: `llm_config_router/llm-provider-config/by-name/${name}`,
		method: "get",
	});
}

/**
 * 创建提供商配置
 */
export function createLLMProvider(data: LLMProviderCreate) {
	return request({
		url: "llm_config_router/llm-provider-config/",
		method: "post",
		data,
	});
}

/**
 * 更新提供商配置
 */
export function updateLLMProvider(id: number, data: LLMProviderUpdate) {
	return request({
		url: `llm_config_router/llm-provider-config/${id}`,
		method: "put",
		data,
	});
}

/**
 * 删除提供商配置
 */
export function deleteLLMProvider(id: number) {
	return request({
		url: `llm_config_router/llm-provider-config/${id}`,
		method: "delete",
	});
}

/**
 * 更新提供商状态
 */
export function updateLLMProviderStatus(id: number, status: number) {
	return request({
		url: `llm_config_router/llm-provider-config/${id}/status`,
		method: "patch",
		params: { status },
	});
}

/**
 * 使用LLM增强内容（非流式请求）
 * @param data 增强请求参数
 */
export function enhanceContent(data: { prompt: string; enhance_context: string; platform: string; model: string }) {
	return request({
		url: "/llm/enhance",
		method: "post",
		data,
	});
}

/**
 * 使用LLM增强内容 - 基于request的流式响应
 * 注意：这个方法依赖于request的流式支持，实际效果需要测试
 * @param data 增强请求参数
 */
export function enhanceContentStreamWithRequest(data: {
	prompt: string;
	enhance_context: string;
	platform: string;
	model: string;
}) {
	return request({
		url: "/llm/enhance",
		method: "post",
		data,
		responseType: "stream", // 使用stream类型，实际会转为blob
	});
}

/**
 * 使用LLM增强内容 - 使用统一流式处理
 * @param data 增强请求参数
 * @param onData 数据处理回调
 * @param onError 错误处理回调
 * @returns 返回Response对象的Promise
 */
export function enhanceContentStream(
	data: {
		prompt: string;
		enhance_context: string;
		platform: string;
		model: string;
	},
	onData: (data: any) => void,
	onError?: (error: Error) => void,
): Promise<Response> {
	return executeStreamRequest("/llm/enhance", data, onData, onError);
}

/**
 * 高级流式请求 - 提供更多控制选项
 * @param data 增强请求参数
 * @param options 流式处理选项
 */
export function enhanceContentStreamAdvanced(
	data: {
		prompt: string;
		enhance_context: string;
		platform: string;
		model: string;
	},
	options?: {
		dataType?: "text" | "json" | "sse";
		delimiter?: string;
		debug?: boolean;
	},
) {
	return createStreamRequest("/llm/enhance", "post", data, options);
}

/**
 * 基础流式请求方法，支持不同URL的通用实现
 * @param data 请求数据
 * @param url 请求URL
 * @param onToken 处理后的token回调
 * @param onRawChunk 原始数据块回调（可选）
 * @param onError 错误处理回调（可选）
 * @returns 返回Response对象的Promise
 */
export function baseStream(
	data: any,
	url: string,
	onToken: (token: string) => void,
	onRawChunk?: (chunk: string) => void,
	onError?: (error: Error) => void,
): Promise<Response> {
	const streamRequest = createStreamRequest(url, "post", data, {
		dataType: "token",
		realtime: true,
	});

	// 处理标准处理后的token
	streamRequest.onChunk((token) => {
		onToken(token);
	});

	// 如果提供了原始数据处理函数，则注册接收原始数据
	if (onRawChunk) {
		streamRequest.onChunk((chunk) => {
			onRawChunk(chunk);
		}, true);
	}

	// 处理JSON格式的token（如果有）
	streamRequest.onJson((data) => {
		if (typeof data === "string") {
			onToken(data);
		} else if (data.content) {
			onToken(data.content);
		} else if (data.delta && data.delta.content) {
			onToken(data.delta.content);
		}
	});

	if (onError) {
		streamRequest.onError(onError);
	}

	return streamRequest.execute();
}

/**
 * 使用LLM增强内容 - 流式响应，逐字符显示版本
 * @param data 增强请求参数
 * @param onToken 处理后的token回调
 * @param onRawChunk 原始数据块回调（可选）
 * @param onError 错误处理回调（可选）
 * @returns 返回Response对象的Promise
 */
export function enhanceContentTokenStream(
	data: {
		prompt: string;
		enhance_context: string;
		model_id: string;
	},
	onToken: (token: string) => void,
	onRawChunk?: (chunk: string) => void,
	onError?: (error: Error) => void,
): Promise<Response> {
	return baseStream(data, "/llm/enhance", onToken, onRawChunk, onError);
}

export function chatTestStream(
	data: {
		message: string; // 用户发送消息
		role_id: string; // 角色ID，可以从当前页面获取该角色
		level: string; // 编辑或者添加输入框中角色等级
		user_level: string; // 先和角色等级保持一致
		session_id: string; // 时间戳
		role_prompt: string; // 角色提示词
		role_prologue: string; // 角色开场白
		role_dialogue: string; //角色台词设定
		user_name: string;
		relationship_level: number;
		long_term_memory: boolean; // 是否开启长期记忆
		memory_level: number; // 记忆等级，6为对话记忆，7为Mem0记忆，10为对话记忆
	},
	onToken: (token: string) => void,
	onRawChunk?: (chunk: string) => void,
	onError?: (error: Error) => void,
): Promise<Response> {
	return baseStream(data, "/llm/chat/stream", onToken, onRawChunk, onError);
}

export function chatTask(data: {
	message: string; // 用户发送消息
	role_id: string; // 角色ID，可以从当前页面获取该角色
	level: string; // 编辑或者添加输入框中角色等级
	user_level: string; // 先和角色等级保持一致
	session_id: string; // 时间戳
	taskDescription: string; // 任务描述
	taskGoal: string; // 任务目标
	scoreRange: string; //分数加减范围
	maxRounds: number; // 最大轮次
	targetScore: number; // 目标分数
	taskLevel: number; // 任务等级
	taskPersonality: string; // 任务人设
	task_goal_judge: string; // 添加任务类型字段
}) {
	return request({
		url: "/llm/chat/task",
		method: "post",
		data,
	});
}

export function chatSubTask(data: {
	message: string; // 用户发送消息
	role_id: string; // 角色ID
	level: string; // 角色等级
	user_level: string; // 用户等级
	session_id: string; // 会话ID
	taskDescription: string; // 任务描述
	taskGoal: string; // 任务目标
	scoreRange: string; // 分数加减范围
	maxRounds: number; // 最大轮次
	targetScore: number; // 目标分数
	taskLevel: number; // 任务等级
	taskPersonality: string; // 任务人设
	sub_task_id: string; // 子任务ID
}) {
	return request({
		url: "/../app/rag/chat/sub/task",
		// url: "/llm/chat/sub/task",
		method: "post",
		data,
	});
}

/**
 * 初始化随机任务会话
 * @param data 参数
 * @returns 返回任务信息和会话ID
 */
export function initRandomTaskSession(data: {
	message?: string; // 用户消息，可选
	role_id?: string; // 角色ID，可选
	user_level: number; // 用户等级
	level: number; // 角色等级
	user_name: string; // 用户名称
	relationship_level: number; // 关系等级
	user_id?: string; // 用户ID，可选
	temperature?: number; // 温度，可选
	top_k?: number; // 检索文档数量，可选
	task_sup_id?: string; // 指定子任务ID，可选
}) {
	return request({
		// url: "/llm/chat/sub/task/session",
		url: "/../app/rag/chat/sub/task/session",
		method: "post",
		data: {
			message: data.message || "你好",
			role_id: data.role_id || "",
			user_level: data.user_level || 1,
			level: data.level || 1,
			user_name: data.user_name || "玩家",
			relationship_level: data.relationship_level || 1,
			user_id: data.user_id || "",
			temperature: data.temperature || 0.7,
			top_k: data.top_k || 3,
			task_sup_id: data.task_sup_id || "",
		},
	});
}

/**
 * 跳过当前子任务
 * @param data 参数
 * @returns 返回操作结果
 */
export function skipSubTask(data: { user_id: string; subtask_id: string }) {
	return request({
		url: "/llm/chat/task/skip",
		method: "put",
		data,
	});
}
