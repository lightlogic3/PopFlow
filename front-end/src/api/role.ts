import request from "@/utils/request";

/**
 * 获取角色列表（分页）
 */
export function getRoleList(params:any) {
	return request({
		url: "roles/",
		method: "get",
		params,
	});
}

/**
 * 获取角色详情
 */
export function getRoleDetail(roleId: string) {
	return request({
		url: `roles/${roleId}`,
		method: "get",
	});
}

/**
 * 创建角色
 */
export function createRole(data: {
	name: string;
	role_id: string;
	sort?: number;
	image_url?: string;
	knowledge_count?: number;
}) {
	return request({
		url: "roles/",
		method: "post",
		data,
	});
}

/**
 * 更新角色
 */
export function updateRole(
	roleId: string,
	data: {
		name?: string;
		sort?: number;
		image_url?: string;
		knowledge_count?: number;
	},
) {
	return request({
		url: `roles/${roleId}`,
		method: "put",
		data,
	});
}

/**
 * 删除角色
 */
export function deleteRole(roleId: string) {
	return request({
		url: `roles/${roleId}`,
		method: "delete",
	});
}

/**
 * 新API: 获取角色知识列表
 */
export function getRoleKnowledgeList(params: {
	keyword?: string;
	role_id?: string;
	type_name?: string;
	skip?: number;
	limit?: number;
}) {
	return request({
		url: "role-knowledge/",
		method: "get",
		params,
	});
}

/**
 * 新API: 获取角色的知识列表
 */
export function getRoleKnowledgeByRoleId(roleId: string, params: { skip?: number; limit?: number }) {
	return request({
		url: `role-knowledge/role/${roleId}`,
		method: "get",
		params,
	});
}

export function getRoleKnowledgeByShareRoleId(roleId: string, params: { skip?: number; limit?: number }) {
	return request({
		url: `role-knowledge/role/share/${roleId}`,
		method: "get",
		params,
	});
}

/**
 * 新API: 根据类型获取知识列表
 */
export function getRoleKnowledgeByType(type: string, params: { skip?: number; limit?: number }) {
	return request({
		url: `role-knowledge/type/${type}`,
		method: "get",
		params,
	});
}

/**
 * 新API: 获取单个知识详情
 */
export function getRoleKnowledgeDetail(knowledgeId: number) {
	return request({
		url: `role-knowledge/${knowledgeId}`,
		method: "get",
	});
}

/**
 * 新API: 创建角色知识
 */
export function createRoleKnowledge(data: {
	text: string;
	role_id: string;
	type: string;
	title: string;
	grade: number;
	source?: string;
	tags?: string;
	relations?: string;
	relations_role?: string;
}) {
	return request({
		url: "role-knowledge/",
		method: "post",
		data,
	});
}

/**
 * 新API: 更新角色知识
 */
export function updateRoleKnowledge(
	knowledgeId: number,
	data: {
		text?: string;
		role_id?: string;
		type?: string;
		title?: string;
		grade?: number;
		source?: string;
		tags?: string;
		relations?: string;
		relations_role?: string;
	},
) {
	return request({
		url: `role-knowledge/${knowledgeId}`,
		method: "put",
		data,
	});
}

/**
 * 新API: 删除角色知识
 */
export function deleteRoleKnowledge(knowledgeId: number) {
	return request({
		url: `role-knowledge/${knowledgeId}`,
		method: "delete",
	});
}

/**
 * 新API: 批量创建角色知识
 */
export function bulkCreateRoleKnowledge(data: {
	items: Array<{
		text: string;
		role_id: string;
		type: string;
		title: string;
		grade: number;
		source?: string;
		tags?: string;
		relations?: string;
		relations_role?: string;
	}>;
}) {
	return request({
		url: "role-knowledge/bulk",
		method: "post",
		data,
	});
}

/**
 * 新API: 统计角色知识数量
 */
export function countRoleKnowledge(roleId: string) {
	return request({
		url: `role-knowledge/count/role/${roleId}`,
		method: "get",
	});
}

/**
 * 添加角色提示词
 */
export function addRolePrompt(data: { role_id: string; level: number; prompt_text: string; status?: number }) {
	return request({
		url: "role_prompt/character-prompt-config/",
		method: "post",
		data,
	});
}

/**
 * 获取角色提示词列表
 */
export function getRolePrompts(params: { skip?: number; limit?: number; role_ids?: Array<string> }) {
	return request({
		url: "role_prompt/character-prompt-config/search",
		method: "post",
		data: params,
	});
}

// 角色接口
export interface Role {
	id: string;
	name: string;
	description?: string;
	avatar?: string;
	status: number;
	created_at?: string;
	updated_at?: string;
}

// 获取所有角色（不分页）
export function getAllRoles() {
	return request({
		url: "/roles/all",
		method: "get",
	});
}

// 获取角色详情，避免与已有函数重名
export function getRoleById(id: string) {
	return request({
		url: `/roles/${id}`,
		method: "get",
	});
}
