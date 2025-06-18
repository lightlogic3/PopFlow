import request from "@/utils/request";

/**
 * 获取角色关联的世界知识点列表
 */
export function getRoleWorldList(params: {
	skip?: number;
	limit?: number;
	role_id?: string;
	world_id?: number;
	world_konwledge_id?: string;
}) {
	params.world_konwledge_id = params.world_konwledge_id + "";
	return request({
		url: "roles-world/",
		method: "get",
		params,
	});
}

/**
 * 获取特定角色的所有关联世界知识点
 */
export function getRoleWorldByRoleId(roleId: string, params: { skip?: number; limit?: number }) {
	return request({
		url: `roles-world/role/${roleId}`,
		method: "get",
		params,
	});
}

/**
 * 获取特定角色的所有关联世界知识点(包含详情)
 * 这个接口一次性返回角色关联的所有世界观知识点详情，避免多次请求
 */
export function getRoleWorldWithDetails(roleId: string, params: { skip?: number; limit?: number }) {
	return request({
		url: `roles-world/role/${roleId}/with-details`,
		method: "get",
		params,
	});
}

/**
 * 获取特定世界的所有关联角色
 */
export function getRoleWorldByWorldId(worldId: number, params: { skip?: number; limit?: number }) {
	return request({
		url: `roles-world/world/${worldId}`,
		method: "get",
		params,
	});
}

/**
 * 获取与特定世界知识点关联的所有角色
 */
export function getRoleWorldByWorldKnowledgeId(worldKnowledgeId: string, params: { skip?: number; limit?: number }) {
	return request({
		url: `roles-world/world-knowledge/${worldKnowledgeId}`,
		method: "get",
		params,
	});
}

/**
 * 获取单个角色-世界关联详情
 */
export function getRoleWorldDetail(id: number) {
	return request({
		url: `roles-world/${id}`,
		method: "get",
	});
}

/**
 * 创建角色-世界知识点关联
 */
export function createRoleWorld(data: {
	world_konwledge_id: string;
	role_id: string;
	world_id: string;
	create_at?: string;
	update_at?: string;
}) {
	data.world_konwledge_id = data.world_konwledge_id + "";
	return request({
		url: "roles-world/",
		method: "post",
		data,
	});
}

/**
 * 更新角色-世界知识点关联
 */
export function updateRoleWorld(
	id: number,
	data: {
		world_konwledge_id?: string;
		role_id?: string;
		world_id?: number;
		update_at?: string;
	},
) {
	data.world_konwledge_id = data.world_konwledge_id + "";
	return request({
		url: `roles-world/${id}`,
		method: "put",
		data,
	});
}

/**
 * 删除角色-世界知识点关联
 */
export function deleteRoleWorld(id: number) {
	return request({
		url: `roles-world/${id}`,
		method: "delete",
	});
}

/**
 * 删除角色的所有关联
 */
export function deleteRoleWorldByRoleId(roleId: string) {
	return request({
		url: `roles-world/role/${roleId}`,
		method: "delete",
	});
}

/**
 * 删除世界的所有关联
 */
export function deleteRoleWorldByWorldId(worldId: number) {
	return request({
		url: `roles-world/world/${worldId}`,
		method: "delete",
	});
}

/**
 * 删除世界知识点的所有关联
 */
export function deleteRoleWorldByWorldKnowledgeId(worldKnowledgeId: string) {
	return request({
		url: `roles-world/world-knowledge/${worldKnowledgeId}`,
		method: "delete",
	});
}

/**
 * 获取与特定世界观关联的所有角色详情(去重)
 */
export function getRolesByWorldId(worldId: string, params: { skip?: number; limit?: number }) {
	return request({
		url: `roles-world/world/${worldId}/roles`,
		method: "get",
		params,
	});
}

/**
 * 获取与特定世界观知识点关联的所有角色详情(去重)
 */
export function getRolesByWorldKnowledgeId(worldKnowledgeId: string, params: { skip?: number; limit?: number }) {
	return request({
		url: `roles-world/world-knowledge/${worldKnowledgeId}/roles`,
		method: "get",
		params,
	});
}
