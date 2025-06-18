import request from "@/utils/request";

/**
 * 获取用户菜单权限
 */
export function getUserMenus() {
	return request({
		url: "/system/menus/user/routes",
		method: "get",
	});
}

/**
 * 获取菜单列表
 * @param params 查询参数
 */
export function getMenuList(params?: { skip?: number; limit?: number; name?: string; status?: number }) {
	return request({
		url: "/system/menus",
		method: "get",
		params,
	});
}

/**
 * 获取菜单树
 * @param params 查询参数
 */
export function getMenuTree(params?: { status?: number }) {
	return request({
		url: "/system/menus/tree",
		method: "get",
		params,
	});
}

/**
 * 获取菜单详情
 * @param id 菜单ID
 */
export function getMenuDetail(id: number) {
	return request({
		url: `/system/menus/${id}`,
		method: "get",
	});
}

/**
 * 创建菜单
 * @param data 菜单信息
 */
export function createMenu(data: any) {
	return request({
		url: "/system/menus",
		method: "post",
		data,
	});
}

/**
 * 更新菜单
 * @param id 菜单ID
 * @param data 菜单信息
 */
export function updateMenu(id: number, data: any) {
	return request({
		url: `/system/menus/${id}`,
		method: "put",
		data,
	});
}

/**
 * 删除菜单
 * @param id 菜单ID
 */
export function deleteMenu(id: number) {
	return request({
		url: `/system/menus/${id}`,
		method: "delete",
	});
}
