/**
 * 数据集API封装
 */
import request from "@/utils/request";
import {
	Dataset,
	DatasetListQuery,
	DatasetListResponse,
	CreateDatasetRequest,
	UpdateDatasetRequest,
	SftEntry,
	DpoEntry,
	ConversationEntry,
	DatasetStats,
	DataQuery,
	SftFormData,
	DpoFormData,
	ConversationFormData,
} from "@/types/dataset";

/**
 * 获取数据集列表
 * @param params 查询参数
 * @returns 数据集列表和总数
 */
export function getDatasetList(params: DatasetListQuery): Promise<DatasetListResponse> {
	return request({
		url: "/plugIn/datasets/datasets/",
		method: "get",
		params: {
			skip: (params.page - 1) * params.limit,
			limit: params.limit,
			...params,
		},
	});
}

/**
 * 获取数据集详情
 * @param id 数据集ID
 * @returns 数据集详情
 */
export function getDatasetDetail(id: number): Promise<Dataset> {
	return request({
		url: `/plugIn/datasets/datasets/${id}`,
		method: "get",
	});
}

/**
 * 创建数据集
 * @param data 创建数据集请求
 * @returns 创建的数据集
 */
export function createDataset(data: CreateDatasetRequest): Promise<Dataset> {
	return request({
		url: "/plugIn/datasets/datasets/",
		method: "post",
		data,
	});
}

/**
 * 更新数据集
 * @param id 数据集ID
 * @param data 更新数据集请求
 * @returns 更新后的数据集
 */
export function updateDataset(id: number, data: UpdateDatasetRequest): Promise<Dataset> {
	return request({
		url: `/plugIn/datasets/datasets/${id}`,
		method: "put",
		data,
	});
}

/**
 * 删除数据集
 * @param id 数据集ID
 * @returns 是否删除成功
 */
export function deleteDataset(id: number): Promise<boolean> {
	return request({
		url: `/plugIn/datasets/datasets/${id}`,
		method: "delete",
	});
}

/**
 * 获取数据集统计信息
 * @param id 数据集ID
 * @returns 数据集统计信息
 */
export function getDatasetStats(id: number): Promise<DatasetStats> {
	return request({
		url: `/plugIn/datasets/datasets/${id}/stats`,
		method: "get",
	});
}

/**
 * 导出数据集
 * @param id 数据集ID
 * @param format 导出格式
 * @returns 导出的数据
 */
export function exportDataset(id: number, format: string = "json"): Promise<Blob> {
	return request({
		url: `/plugIn/datasets/datasets/${id}/export`,
		method: "get",
		params: { format },
		responseType: "blob",
	});
}

/**
 * 导入数据集
 * @param id 数据集ID
 * @param formData 表单数据
 * @returns 导入结果
 */
export function importDataset(id: number, formData: FormData): Promise<any> {
	return request({
		url: `/plugIn/datasets/datasets/${id}/import`,
		method: "post",
		data: formData,
		headers: {
			"Content-Type": "multipart/form-data",
		},
	});
}

/**
 * 获取SFT条目列表
 * @param datasetId 数据集ID
 * @param params 查询参数
 * @returns SFT条目列表
 */
export function getSftEntries(datasetId: number, params: DataQuery): Promise<{ items: SftEntry[]; total: number }> {
	return request({
		url: `/plugIn/datasets/sft/dataset/${datasetId}`,
		method: "get",
		params: {
			skip: (params.page - 1) * params.limit,
			limit: params.limit,
			keyword: params.keyword,
		},
	});
}

/**
 * 创建SFT条目
 * @param data SFT表单数据
 * @returns 创建的SFT条目
 */
export function createSftEntry(data: SftFormData & { datasetId: number }): Promise<SftEntry> {
	return request({
		url: "/plugIn/datasets/sft/entries",
		method: "post",
		data: {
			dataset_id: data.datasetId,
			instruction: data.instruction,
			input: data.input || null,
			output: data.output,
			raw_data: {},
		},
	});
}

/**
 * 更新SFT条目
 * @param id 条目ID
 * @param data SFT表单数据
 * @returns 更新后的SFT条目
 */
export function updateSftEntry(id: number, data: SftFormData): Promise<SftEntry> {
	return request({
		url: `/plugIn/datasets/sft/entries/${id}`,
		method: "put",
		data: {
			instruction: data.instruction,
			input: data.input || null,
			output: data.output,
		},
	});
}

/**
 * 删除SFT条目
 * @param id 条目ID
 * @returns 是否删除成功
 */
export function deleteSftEntry(id: number): Promise<boolean> {
	return request({
		url: `/plugIn/datasets/sft/entries/${id}`,
		method: "delete",
	});
}

/**
 * 获取DPO条目列表
 * @param datasetId 数据集ID
 * @param params 查询参数
 * @returns DPO条目列表
 */
export function getDpoEntries(datasetId: number, params: DataQuery): Promise<{ items: DpoEntry[]; total: number }> {
	return request({
		url: `/plugIn/datasets/dpo/dataset/${datasetId}`,
		method: "get",
		params: {
			skip: (params.page - 1) * params.limit,
			limit: params.limit,
			keyword: params.keyword,
		},
	});
}

/**
 * 创建DPO条目
 * @param data DPO表单数据
 * @returns 创建的DPO条目
 */
export function createDpoEntry(data: DpoFormData & { datasetId: number }): Promise<DpoEntry> {
	return request({
		url: "/plugIn/datasets/dpo/entries",
		method: "post",
		data: {
			dataset_id: data.datasetId,
			query: data.prompt,
			chosen_response: data.chosen,
			rejected_response: data.rejected,
			raw_data: {},
		},
	});
}

/**
 * 更新DPO条目
 * @param id 条目ID
 * @param data DPO表单数据
 * @returns 更新后的DPO条目
 */
export function updateDpoEntry(id: number, data: DpoFormData): Promise<DpoEntry> {
	return request({
		url: `/plugIn/datasets/dpo/entries/${id}`,
		method: "put",
		data: {
			query: data.prompt,
			chosen_response: data.chosen,
			rejected_response: data.rejected,
		},
	});
}

/**
 * 删除DPO条目
 * @param id 条目ID
 * @returns 是否删除成功
 */
export function deleteDpoEntry(id: number): Promise<boolean> {
	return request({
		url: `/plugIn/datasets/dpo/entries/${id}`,
		method: "delete",
	});
}

/**
 * 获取会话列表
 * @param datasetId 数据集ID
 * @param params 查询参数
 * @returns 会话列表
 */
export function getConversations(
	datasetId: number,
	params: DataQuery,
): Promise<{ items: ConversationEntry[]; total: number }> {
	return request({
		url: `/plugIn/datasets/conversations/dataset/${datasetId}`,
		method: "get",
		params: {
			skip: (params.page - 1) * params.limit,
			limit: params.limit,
			keyword: params.keyword,
		},
	});
}

/**
 * 获取会话详情
 * @param conversationId 会话ID
 * @returns 会话消息列表
 */
export function getConversationDetail(conversationId: string): Promise<ConversationEntry> {
	return request({
		url: `/plugIn/datasets/conversations/conversation/${conversationId}`,
		method: "get",
	});
}

/**
 * 创建会话
 * @param data 会话表单数据
 * @returns 创建的会话
 */
export function createConversation(data: ConversationFormData & { datasetId: number }): Promise<ConversationEntry> {
	return request({
		url: "/plugIn/datasets/conversations/batch",
		method: "post",
		data: {
			dataset_id: data.datasetId,
			title: data.title,
			messages: data.messages.map((msg, index) => ({
				role: msg.role,
				content: msg.content,
				sequence_order: index,
			})),
		},
	});
}

/**
 * 更新会话
 * @param id 会话ID
 * @param data 会话表单数据
 * @returns 更新后的会话
 */
export function updateConversation(id: string, data: ConversationFormData): Promise<ConversationEntry> {
	return request({
		url: `/plugIn/datasets/conversations/conversation/${id}`,
		method: "put",
		data: {
			title: data.title,
			messages: data.messages.map((msg, index) => ({
				role: msg.role,
				content: msg.content,
				sequence_order: index,
			})),
		},
	});
}

/**
 * 删除会话
 * @param id 会话ID
 * @returns 是否删除成功
 */
export function deleteConversation(id: string): Promise<boolean> {
	return request({
		url: `/plugIn/datasets/conversations/conversation/${id}`,
		method: "delete",
	});
}
