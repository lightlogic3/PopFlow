import request from "@/utils/request";

/**
 * 用户登录
 * @param data 登录信息
 * @returns 登录结果
 */
export function login(data: { username: string; password: string }) {
	return request({
		url: "/auth/login",
		method: "post",
		data,
	});
}

/**
 * 退出登录
 */
export function logout() {
	return request({
		url: "/auth/logout",
		method: "post",
	});
}

/**
 * 获取当前用户信息
 */
export function getUserInfo() {
	return request({
		url: "/auth/user/info",
		method: "get",
	});
}

/**
 * 获取用户菜单
 */
export function getUserMenu() {
	return request({
		url: "/auth/user/menu",
		method: "get",
	});
}

/**
 * 获取用户列表
 * @param params 查询参数
 */
export function getUserList(params: any) {
	return request({
		url: "/system/users",
		method: "get",
		params,
	});
}

/**
 * 获取用户详情
 * @param id 用户ID
 */
export function getUserDetail(id: number) {
	return request({
		url: `/system/users/${id}`,
		method: "get",
	});
}

/**
 * 创建用户
 * @param data 用户信息
 */
export function createUser(data: any) {
	return request({
		url: "/system/users",
		method: "post",
		data,
	});
}

/**
 * 更新用户
 * @param id 用户ID
 * @param data 用户信息
 */
export function updateUser(id: number, data: any) {
	return request({
		url: `/system/users/${id}`,
		method: "put",
		data,
	});
}

/**
 * 删除用户
 * @param id 用户ID
 */
export function deleteUser(id: number) {
	return request({
		url: `/system/users/${id}`,
		method: "delete",
	});
}

/**
 * 重置用户密码
 * @param id 用户ID
 * @param password 新密码
 */
export function resetUserPassword(id: number, password: string) {
	return request({
		url: `/system/users/${id}/password`,
		method: "put",
		params: { password },
	});
}

/**
 * 修改用户状态
 * @param id 用户ID
 * @param status 状态(0正常 1停用)
 */
export function changeUserStatus(id: number, status: number) {
	return request({
		url: `/system/users/${id}/status`,
		method: "put",
		params: { status },
	});
}

/**
 * 获取用户角色
 * @param id 用户ID
 */
export function getUserRoles(id: number) {
	return request({
		url: `/system/users/${id}/roles`,
		method: "get",
	});
}

/**
 * 分配用户角色
 * @param id 用户ID
 * @param roleIds 角色ID列表
 */
export function assignUserRoles(id: number, roleIds: number[]) {
	return request({
		url: `/system/users/${id}/roles`,
		method: "put",
		data: { role_ids: roleIds },
	});
}
