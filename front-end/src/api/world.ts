import request from "@/utils/request";

/**
 * 获取世界观列表（分页）
 */
export function getWorldList(params?: { type?: string; page?: number; size?: number }) {
	return request({
		url: "worlds/",
		method: "get",
		params,
	});
}

/**
 * 获取所有世界观列表（不分页，用于下拉选择器等场景）
 */
export function getAllWorldList(params?: { type?: string }) {
	return request({
		url: "worlds/all",
		method: "get",
		params,
	});
}

/**
 * 获取世界观详情
 */
export function getWorldDetail(worldId: string) {
	return request({
		url: `worlds/${worldId}`,
		method: "get",
	});
}

/**
 * 创建世界观
 */
export function createWorld(data: {
	title: string;
	type: string;
	description: string;
	image_url?: string;
	sort?: number;
	knowledge_count?: number;
}) {
	return request({
		url: "worlds/",
		method: "post",
		data,
	});
}

/**
 * 更新世界观
 */
export function updateWorld(
	worldId: string,
	data: {
		title?: string;
		type?: string;
		description?: string;
		image_url?: string;
		sort?: number;
		knowledge_count?: number;
	},
) {
	return request({
		url: `worlds/${worldId}`,
		method: "put",
		data,
	});
}

/**
 * 删除世界观
 */
export function deleteWorld(worldId: string) {
	return request({
		url: `worlds/${worldId}`,
		method: "delete",
	});
}

/**
 * 根据类型获取世界观列表（分页）
 */
export function getWorldsByType(worldType: string) {
	return request({
		url: `worlds/type/${worldType}`,
		method: "get",
	});
}

/**
 * 添加世界观文本知识
 */
export function addWorldText(data: {
	text: string;
	type: string;
	title: string;
	grade: number;
	source?: string;
	metadata?: Record<string, any>;
	tags?: string[];
	relations?: string;
	relations_role?: string;
}) {
	return request({
		url: "text_world",
		method: "post",
		data,
	});
}

/**
 * 查询世界观知识
 */
export function queryWorldKnowledge(data: { query: string; top_k?: number; source?: string }) {
	return request({
		url: "query_world",
		method: "post",
		data,
	});
}

/**
 * 获取相关场景
 * 此接口在API文档中未提供，使用模拟数据
 */
export function getRelatedScenes(worldId: string) {
	return request({
		url: `test/scenes/${worldId}`, // 临时接口，实际不存在
		method: "get",
	});
}

/**
 * 添加场景
 * 此接口在API文档中未提供，使用模拟数据
 */
export function addScene(data: { title: string; description: string; worldId: string; imageUrl?: string }) {
	return request({
		url: "test/scenes", // 临时接口，实际不存在
		method: "post",
		data,
	});
}

/**
 * 获取世界观知识点列表
 */
export function getWorldKnowledgeList(params: { page?: number; size?: number; world_id?: string; type?: string }) {
	return request({
		url: "world-knowledge/",
		method: "get",
		params,
	});
}

/**
 * 根据世界ID获取知识点列表
 */
export function getWorldKnowledgeByWorldId(worldId: string, params: { page?: number; size?: number }) {
	return request({
		url: `world-knowledge/world/${worldId}`,
		method: "get",
		params,
	});
}

/**
 * 新API: 根据类型获取知识列表
 */
export function getWorldKnowledgeByType(type: string, params: { page?: number; size?: number } = {}) {
	return request({
		url: `world-knowledge/type/${type}`,
		method: "get",
		params,
	});
}

/**
 * 获取单个世界观知识点详情
 */
export function getWorldKnowledgeDetailByIds(ids: string) {
	return request({
		url: `world-knowledge/know_ids/${ids}`,
		method: "get",
	});
}

export function getWorldKnowledgeDetailByWorldIds(ids: string) {
	return request({
		url: `world-knowledge/world_ids/${ids}`,
		method: "get",
	});
}

export function getWorldKnowledgeDetail(knowledgeId: string) {
	return request({
		url: `world-knowledge/${knowledgeId}`,
		method: "get",
	});
}
/**
 * 新API: 创建世界知识
 */
export function createWorldKnowledge(data: any) {
	return request({
		url: "/world-knowledge/",
		method: "post",
		data,
	});
}

/**
 * 新API: 更新世界知识
 */
export function updateWorldKnowledge(knowledgeId: number, data: any) {
	return request({
		url: `/world-knowledge/${knowledgeId}`,
		method: "put",
		data,
	});
}

/**
 * 新API: 删除世界知识
 */
export function deleteWorldKnowledge(knowledgeId: number) {
	return request({
		url: `/world-knowledge/${knowledgeId}`,
		method: "delete",
	});
}

/**
 * 新API: 批量创建世界知识
 */
export function bulkCreateWorldKnowledge(data: any) {
	return request({
		url: "/world-knowledge/bulk",
		method: "post",
		data,
	});
}

/**
 * 新API: 统计世界知识数量
 */
export function countWorldKnowledge(worldId: string) {
	return request({
		url: `world-knowledge/count/world/${worldId}`,
		method: "get",
	});
}

/**
 * 获取指定世界设计的所有知识条目
 */
export function getKnowledgeByWorld(worldsId: string, params?: any) {
	return request({
		url: `/world-knowledge/world/${worldsId}`,
		method: "get",
		params,
	});
}

/**
 * 获取指定世界设计的所有知识条目（分页版本）
 */
export function getKnowledgeByWorldPaginated(worldsId: string, params?: { page?: number; size?: number }) {
	return request({
		url: `/world-knowledge/world/${worldsId}/paginated`,
		method: "get",
		params,
	});
}

/**
 * 获取指定类型的所有知识条目
 */
export function getKnowledgeByType(typeName: string, params?: any) {
	return request({
		url: `/world-knowledge/type/${typeName}`,
		method: "get",
		params,
	});
}

/**
 * 获取与指定角色关联的世界观知识条目
 */
export function getKnowledgeByRole(roleId: string, params?: any) {
	return request({
		url: `/world-knowledge/role/${roleId}`,
		method: "get",
		params,
	});
}

/**
 * 统计指定世界设计的知识条目数量
 */
export function countKnowledgeByWorld(worldsId: string) {
	return request({
		url: `/world-knowledge/count/world/${worldsId}`,
		method: "get",
	});
}

/**
 * AI增强功能 - 知识内容生成
 */
export function enhanceWithAI(data: any) {
	return request({
		url: "/llm/enhance",
		method: "post",
		data,
	});
}
