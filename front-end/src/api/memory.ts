import request from "@/utils/request";

// 插件参数接口
export interface PluginRequest {
	plugin_name?: string;
	plugin_level?: number | string;
	custom_plugin_path?: string;
}

// 对话请求接口
export interface ConversationRequest {
	content: string;
	role?: string;
	conversation_id?: string;
	message_id?: string;
	parent_message_id?: string;
	metadata?: Record<string, any>;
}

// 查询请求接口
export interface MemoryQueryRequest {
	query: string;
	top_k?: number;
	include_history?: boolean;
}

// 聊天测试请求接口
export interface ChatTestRequest {
	model_id: string;
	query: string;
	conversation_history?: Array<Record<string, any>>;
	temperature?: number;
	max_tokens?: number;
	user_id?: string;
	role_id?: string;
	session_id?: string;
	plugin_request?: PluginRequest;
}

// 获取可用的记忆系统插件
export function getMemoryPlugins() {
	return request({
		url: "/memory/plugins",
		method: "get",
	});
}

// 测试聊天API
export function testChat(data: ChatTestRequest) {
	return request({
		url: "/memory/chat-test",
		method: "post",
		data,
	});
}

// 存储对话到记忆系统
export function storeConversation(
	data: ConversationRequest,
	userId: string,
	roleId: string,
	sessionId?: string,
	plugin?: PluginRequest,
) {
	const params: any = {
		user_id: userId,
		role_id: roleId,
	};

	if (sessionId) {
		params.session_id = sessionId;
	}

	return request({
		url: "/memory/store",
		method: "post",
		data: {
			...data,
			plugin_request: plugin,
		},
		params: params,
	});
}

// 检索相关对话
export function retrieveConversations(
	data: MemoryQueryRequest,
	userId: string,
	roleId: string,
	sessionId?: string,
	plugin?: PluginRequest,
) {
	const params: any = {
		user_id: userId,
		role_id: roleId,
	};

	if (sessionId) {
		params.session_id = sessionId;
	}

	return request({
		url: "/memory/retrieve",
		method: "post",
		data: {
			...data,
			plugin_request: plugin,
		},
		params: params,
	});
}

// 从数据库同步对话数据到记忆系统
export function syncConversations(
	userId: string,
	roleId: string,
	runInBackground: boolean = true,
	plugin?: PluginRequest,
) {
	const params: any = {
		user_id: userId,
		role_id: roleId,
		run_in_background: runInBackground,
	};

	return request({
		url: "/memory/sync",
		method: "post",
		data: {
			plugin_request: plugin,
		},
		params: params,
	});
}

// 获取同步状态
export function getSyncStatus(userId: string, roleId: string, plugin?: PluginRequest) {
	const params: any = {
		user_id: userId,
		role_id: roleId,
	};

	return request({
		url: "/memory/sync/status",
		method: "get",
		params: params,
		data: {
			plugin_request: plugin,
		},
	});
}
