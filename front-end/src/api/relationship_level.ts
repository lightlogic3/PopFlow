import request from "@/utils/request";

/**
 * 关系等级接口
 */

// 获取关系等级列表
export function getRelationshipLevels(params: any) {
	return request({
		url: "/relationship-levels/",
		method: "get",
		params,
	});
}

// 获取单个关系等级
export function getRelationshipLevel(id: number) {
	return request({
		url: `/relationship-levels/${id}`,
		method: "get",
	});
}

// 根据角色ID获取关系等级
export function getRelationshipLevelByRoleId(roleId: string) {
	return request({
		url: `/relationship-levels/role/${roleId}`,
		method: "get",
	});
}

// 根据关系名称获取关系等级
export function getRelationshipLevelByName(name: string) {
	return request({
		url: `/relationship-levels/name/${name}`,
		method: "get",
	});
}

// 创建关系等级
export function createRelationshipLevel(data: any) {
	return request({
		url: "/relationship-levels/",
		method: "post",
		data,
	});
}

// 更新关系等级
export function updateRelationshipLevel(id: number, data: any) {
	return request({
		url: `/relationship-levels/${id}`,
		method: "put",
		data,
	});
}

// 删除关系等级
export function deleteRelationshipLevel(id: number) {
	return request({
		url: `/relationship-levels/${id}`,
		method: "delete",
	});
}
