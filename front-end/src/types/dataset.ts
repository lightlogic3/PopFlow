/**
 * 数据集类型定义
 */

/**
 * 数据集类型枚举
 */
export enum DatasetType {
	SFT = "SFT",
	DPO = "DPO",
	CONVERSATION = "CONVERSATION",
}

/**
 * 数据集接口
 */
export interface Dataset {
	id: number;
	name: string;
	type: DatasetType;
	description: string | null;
	tags: string | null;
	entryCount?: number;
	createdAt: string;
	updatedAt: string;
}

/**
 * 数据集列表查询参数
 */
export interface DatasetListQuery {
	page: number;
	limit: number;
	name?: string;
	type?: DatasetType;
}

/**
 * 数据集列表响应
 */
export interface DatasetListResponse {
	items: Dataset[];
	total: number;
}

/**
 * 创建数据集请求
 */
export interface CreateDatasetRequest {
	name: string;
	type: DatasetType;
	description?: string;
	tags?: string;
}

/**
 * 更新数据集请求
 */
export interface UpdateDatasetRequest {
	name?: string;
	description?: string;
	tags?: string;
}

/**
 * SFT条目接口
 */
export interface SftEntry {
	id: number;
	dataset_id: number;
	instruction: string;
	input: string | null;
	output: string;
	raw_data: Record<string, any>;
	created_at: string;
}

/**
 * DPO条目接口
 */
export interface DpoEntry {
	id: number;
	dataset_id: number;
	query: string;
	chosen_response: string;
	rejected_response: string;
	raw_data: Record<string, any>;
	created_at: string;
}

/**
 * 会话消息接口
 */
export interface ConversationMessage {
	role: "user" | "assistant" | "system";
	content: string;
}

/**
 * 会话条目接口
 */
export interface ConversationEntry {
	id: number;
	dataset_id: number;
	conversation_id: string;
	title?: string;
	messageCount?: number;
	messages?: ConversationMessage[];
	createdAt: string;
}

/**
 * 数据集统计信息
 */
export interface DatasetStats {
	entryCount: number;
	tokenCount?: number;
	avgTokensPerEntry?: number;
	instructionTokens?: number;
	outputTokens?: number;
	promptTokens?: number;
	chosenTokens?: number;
	rejectedTokens?: number;
	messageCount?: number;
	[key: string]: number | undefined;
}

/**
 * 数据查询参数
 */
export interface DataQuery {
	page: number;
	limit: number;
	keyword?: string;
}

/**
 * SFT表单数据
 */
export interface SftFormData {
	id?: number;
	instruction: string;
	input?: string;
	output: string;
}

/**
 * DPO表单数据
 */
export interface DpoFormData {
	id?: number;
	prompt: string;
	chosen: string;
	rejected: string;
}

/**
 * 对话表单数据
 */
export interface ConversationFormData {
	id?: number;
	title: string;
	messages: ConversationMessage[];
}

/**
 * 导入表单数据
 */
export interface ImportFormData {
	file: File | null;
}
