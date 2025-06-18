import request from "@/utils/request";
import { createStreamRequest, executeStreamRequest } from "@/utils/streamRequest";
import type {
	ChatSession,
	ChatMessage,
	CreateSessionRequest,
	UpdateSessionRequest,
	CreateMessageRequest,
} from "@/types/chat";

/**
 * 获取聊天会话列表
 */
export function getChatSessions(params?: { page?: number; size?: number }): Promise<ChatSession[]> {
	return request({
		url: "sessions/get_list_user",
		method: "get",
		params,
	});
}

/**
 * 获取单个聊天会话详情
 */
export function getChatSessionById(id: string): Promise<ChatSession> {
	return request({
		url: `sessions/get_session/${id}`,
		method: "get",
	});
}

/**
 * 创建聊天会话
 */
export function createChatSession(data: CreateSessionRequest) {
	return request({
		url: "sessions",
		method: "post",
		data,
	});
}

/**
 * 更新聊天会话
 */
export function updateChatSession(id: string, data: UpdateSessionRequest) {
	return request({
		url: `chat/sessions/${id}`,
		method: "put",
		data,
	});
}

/**
 * 删除聊天会话
 */
export function deleteChatSession(id: string) {
	return request({
		url: `chat/sessions/${id}`,
		method: "delete",
	});
}

/**
 * 清空聊天会话
 */
export function clearChatSession(id: string) {
	return request({
		url: `chat/sessions/${id}/clear`,
		method: "post",
	});
}

/**
 * 获取聊天会话消息列表
 */
export function getChatMessages(sessionId: string): Promise<ChatMessage[]> {
	return request({
		url: `conversations/session/${sessionId}`,
		method: "get",
	});
}

/**
 * 创建聊天消息
 */
export function createChatMessage(data: CreateMessageRequest) {
	return request({
		url: "chat/messages",
		method: "post",
		data,
	});
}

/**
 * RAG聊天（流式）- 基于request的原始实现
 */
export function ragChatStreamWithRequest(data: {
	message: string;
	role_id: string;
	level: number;
	user_level: number;
	session_id?: string;
	stream?: boolean;
	top_k?: number;
	temperature?: number;
	template_type?: string;
	include_sources?: boolean;
}) {
	return request({
		url: "rag/chat/stream",
		method: "post",
		data,
		responseType: "stream",
	});
}

/**
 * RAG聊天（流式）- 使用统一流式处理
 * @param data 请求参数
 * @param onData 数据处理回调
 * @param onError 错误处理回调
 * @returns 返回Response对象的Promise
 */
export function ragChatStream(
	data: {
		message: string;
		role_id: string;
		level: number;
		user_level: number;
		session_id?: string;
		stream?: boolean;
		top_k?: number;
		temperature?: number;
		template_type?: string;
		include_sources?: boolean;
		user_id?: string;
	},
	onData: (data: any) => void,
	onError?: (error: Error) => void,
): Promise<Response> {
	return executeStreamRequest("rag/chat/stream", data, onData, onError);
}

/**
 * RAG聊天（流式）- 高级控制
 * @param data 请求参数
 * @param options 流式处理选项
 * @returns 流请求控制器
 */
export function ragChatStreamAdvanced(
	data: {
		message: string;
		role_id: string;
		level: number;
		user_level: number;
		session_id?: string;
		stream?: boolean;
		top_k?: number;
		temperature?: number;
		template_type?: string;
		include_sources?: boolean;
		user_id?: string;
	},
	options?: {
		dataType?: "text" | "json" | "sse";
		delimiter?: string;
		debug?: boolean;
	},
) {
	return createStreamRequest("rag/chat/stream", "post", data, options);
}

/**
 * 获取会话详情
 */
export function getSessionInfo(sessionId: string) {
	return request({
		url: `/api/rag/session/${sessionId}`,
		method: "get",
	});
}

/**
 * 清空RAG会话历史
 */
export function clearRagSession(sessionId: string) {
	return request({
		url: `/api/rag/session/${sessionId}/clear`,
		method: "delete",
	});
}

/**
 * 删除RAG会话
 */
export function deleteRagSession(sessionId: string) {
	return request({
		url: `/api/rag/session/${sessionId}`,
		method: "delete",
	});
}

/**
 * 更改会话记忆类型
 */
export function changeMemoryType(sessionId: string, memoryType: string) {
	return request({
		url: `/api/rag/session/${sessionId}/memory`,
		method: "put",
		params: { memory_type: memoryType },
	});
}

/**
 * 获取所有会话列表
 */
export function getRagSessions() {
	return request({
		url: "/sessions/get_list_admin",
		method: "get",
		params: {
			skip: 0,
			limit: 5,
		},
	});
}

/**
 * RAG聊天（流式）- 逐字符显示版本
 * @param data 请求参数
 * @param onToken 处理后的token回调
 * @param onRawChunk 原始数据块回调（可选）
 * @param onError 错误处理回调（可选）
 * @returns 返回Response对象的Promise
 */
export function ragChatTokenStream(
	data: {
		message: string;
		role_id: string;
		level: number;
		user_level: number;
		session_id?: string;
		stream?: boolean;
		top_k?: number;
		temperature?: number;
		template_type?: string;
		include_sources?: boolean;
		user_id?: string;
		way?: string;
	},
	onToken: (token: string) => void,
	onRawChunk?: (chunk: string) => void,
	onError?: (error: Error) => void,
): Promise<Response> {
	const streamRequest = createStreamRequest("rag/chat/stream", "post", data, {
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
		} else if (data.choices && data.choices[0]?.delta?.content) {
			onToken(data.choices[0].delta.content);
		} else if (data.delta && data.delta.content) {
			onToken(data.delta.content);
		}
	});

	if (onError) {
		streamRequest.onError(onError);
	}

	return streamRequest.execute();
}
