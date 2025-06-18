/**
 * 聊天会话相关类型定义
 */

// 聊天会话
export interface ChatSession {
	session_id: string;
	user_id: string;
	role_id: string;
	type_session: string;
	session_name: string | null;
	session_summary: string | null;
	model_name: string;
	session_status: "active" | "archived" | "deleted";
	first_message_time: string | null;
	last_message_time: string | null;
	message_count: number;
	total_tokens: number;
	created_at: string;
	updated_at: string;
}

// 聊天消息
export interface ChatMessage {
	id: string;
	session_id: string;
	role: "user" | "assistant";
	content: string;
	timestamp: string;
}

// 记忆类型选项
export const MEMORY_TYPES = [
	{ value: "buffer_window", label: "Buffer Window" },
	{ value: "summary", label: "Summary" },
	{ value: "entity", label: "Entity" },
	{ value: "knowledge_graph", label: "Knowledge Graph" },
];

// 创建会话请求
export interface CreateSessionRequest {
	user_id: string;
	session_name: string;
}

// 更新会话请求
export interface UpdateSessionRequest {
	title?: string;
	memory_type?: string;
	summary?: string;
}

// 创建消息请求
export interface CreateMessageRequest {
	session_id: string;
	role: "user" | "assistant";
	content: string;
}

// RAG聊天相关类型

// 聊天输入请求
export interface RagChatInput {
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
}

// RAG消息类型
export interface RagMessage {
	role: "system" | "user" | "assistant";
	content: string;
}

// 会话响应
export interface SessionResponse {
	session_id: string;
	memory_type: string;
	history?: RagMessage[];
	created_at: string;
	message_count: number;
}

// 本地缓存的聊天设置
export interface ChatSettings {
	roleId: string;
	level: number;
	userLevel: number;
	topK: number;
	temperature: number;
	templateType: string;
	includeSources: boolean;
}
