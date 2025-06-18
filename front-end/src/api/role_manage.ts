import request from "@/utils/request";

/**
 * 获取角色列表
 * @param params 查询参数
 */
export function getRoleList(params: { page: number; size: number; name?: string; code?: string; status?: number }) {
	return request({
		url: "/system/roles",
		method: "get",
		params,
	});
}

/**
 * 获取角色详情
 * @param id 角色ID
 */
export function getRoleDetail(id: number) {
	return request({
		url: `/system/roles/${id}`,
		method: "get",
	});
}

/**
 * 创建角色
 * @param data 角色信息
 */
export function createRole(data: any) {
	return request({
		url: "/system/roles",
		method: "post",
		data,
	});
}

/**
 * 更新角色
 * @param id 角色ID
 * @param data 角色信息
 */
export function updateRole(id: number, data: any) {
	return request({
		url: `/system/roles/${id}`,
		method: "put",
		data,
	});
}

/**
 * 删除角色
 * @param id 角色ID
 */
export function deleteRole(id: number) {
	return request({
		url: `/system/roles/${id}`,
		method: "delete",
	});
}

/**
 * 获取角色菜单权限
 * @param id 角色ID
 */
export function getRoleMenus(id: number) {
	return request({
		url: `/system/roles/${id}/menus`,
		method: "get",
	});
}

/**
 * 分配角色菜单权限
 * @param id 角色ID
 * @param menuIds 菜单ID列表
 */
export function assignRoleMenus(id: number, menuIds: number[]) {
	return request({
		url: `/system/roles/${id}/menus`,
		method: "put",
		data: { menu_ids: menuIds },
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
export function getRolePrompts(params: { types?: Array<string> }) {
	return request({
		url: "role_prompt/character-prompt-config/search",
		method: "post",
		data: params,
	});
}
