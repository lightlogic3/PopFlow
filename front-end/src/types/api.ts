/**
 * 分页响应接口
 */
export interface PaginationResponse<T> {
	items: T[];
	total: number;
	page: number;
	size: number;
}

/**
 * FastAPI-Pagination Page类型（与后端保持一致）
 */
export interface Page<T> {
	items: T[];
	total: number;
	page?: number;
	size?: number;
	pages?: number;
}

/**
 * 角色记录接口
 */
export interface RoleRecord {
	id: number;
	name: string;
	code: string;
	sort: number;
	status: number;
	data_scope?: number;
	type?: number;
	remark?: string;
	create_time?: string;
	update_time?: string;
}

/**
 * 菜单记录接口
 */
export interface MenuRecord {
	id: number;
	parent_id: number;
	name: string;
	path: string;
	component?: string;
	component_name?: string;
	redirect?: string;
	permission?: string;
	type: number; // 0-目录 1-菜单 2-按钮
	icon?: string;
	sort: number;
	visible: boolean;
	status: number; // 0-正常 1-停用
	keep_alive?: boolean;
	always_show?: boolean;
	meta?: string;
	children?: MenuRecord[];
	create_time?: string;
	update_time?: string;
}

/**
 * 用户记录接口
 */
export interface UserRecord {
	id: number;
	username: string;
	nickname: string;
	password?: string;
	email?: string;
	mobile?: string;
	avatar?: string;
	sex: number; // 0-未知 1-男 2-女
	status: number; // 0-正常 1-停用
	dept_id?: number;
	remark?: string;
	login_ip?: string;
	login_date?: string;
	create_time?: string;
	update_time?: string;
}

/**
 * 角色菜单响应
 */
export interface RoleMenuResponse {
	menus: MenuRecord[];
	checkedKeys: number[];
}

/**
 * 用户角色响应
 */
export interface UserRoleResponse {
	roles: Array<{
		id: number;
		name: string;
		selected: boolean;
	}>;
}
