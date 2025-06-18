import request from "@/utils/request";

// 盲盒接口类型定义
export interface BlindBox {
	id: number;
	name: string;
	description?: string;
	image_url?: string;
	price?: number;
	probability_rules: string;
	guarantee_count?: number;
	guarantee_rarity?: number;
	status: number;
	created_at?: string;
	updated_at?: string;
}

export interface BlindBoxCreate {
	name: string;
	description?: string;
	image_url?: string;
	price?: number;
	probability_rules: string;
	guarantee_count?: number;
	guarantee_rarity?: number;
	status: number;
}

export interface BlindBoxUpdate {
	name?: string;
	description?: string;
	image_url?: string;
	price?: number;
	probability_rules?: string;
	guarantee_count?: number;
	guarantee_rarity?: number;
	status?: number;
}

export interface BlindBoxQueryParams {
	name?: string;
	status?: number;
	guarantee_rarity?: number;
	page?: number;
	size?: number;
}

export interface GuaranteeRarityChoice {
	value: number;
	label: string;
}

/**
 * 获取盲盒列表
 */
export function getBlindBoxes(params?: any) {
	return request({
		url: "/blind-box",
		method: "get",
		params,
	});
}

/**
 * 获取盲盒详情
 */
export function getBlindBox(id: number) {
	return request({
		url: `/blind-box/${id}`,
		method: "get",
	});
}

/**
 * 创建盲盒
 */
export function createBlindBox(data: BlindBoxCreate) {
	return request({
		url: "/blind-box",
		method: "post",
		data,
	});
}

/**
 * 更新盲盒
 */
export function updateBlindBox(id: number, data: BlindBoxUpdate) {
	return request({
		url: `/blind-box/${id}`,
		method: "put",
		data,
	});
}

/**
 * 删除盲盒
 */
export function deleteBlindBox(id: number) {
	return request({
		url: `/blind-box/${id}`,
		method: "delete",
	});
}

/**
 * 获取启用的盲盒列表
 */
export function getActiveBlindBoxes() {
	return request({
		url: "/blind-box/active/list",
		method: "get",
	});
}

/**
 * 获取保底稀有度选项
 */
export function getGuaranteeRarityChoices() {
	return request({
		url: "/blind-box/choices/guarantee-rarity",
		method: "get",
	});
}
