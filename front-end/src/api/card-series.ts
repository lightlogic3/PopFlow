import request from "@/utils/request";

// 卡牌系列接口类型定义
export interface CardSeries {
	id: number;
	name: string;
	code: string;
	description?: string;
	sort_order: number;
	status: number;
	is_deleted: number;
	creator_id?: number;
	updater_id?: number;
	create_time: string;
	update_time: string;
}

export interface CardSeriesCreate {
	name: string;
	code: string;
	description?: string;
	sort_order?: number;
	status?: number;
}

export interface CardSeriesUpdate {
	name?: string;
	code?: string;
	description?: string;
	sort_order?: number;
	status?: number;
}

export interface CardSeriesFilter {
	name?: string;
	code?: string;
	status?: number;
	page?: number;
	size?: number;
}

/**
 * 获取卡牌系列列表（分页）
 */
export function getCardSeriesList(params: any) {
	// 过滤掉空值参数
	const filteredParams: any = {};
	Object.keys(params).forEach((key) => {
		const value = (params as any)[key];
		if (value !== null && value !== undefined && value !== "") {
			filteredParams[key] = value;
		}
	});

	return request({
		url: "card-series/",
		method: "get",
		params: filteredParams,
	});
}

/**
 * 获取启用状态的卡牌系列列表
 */
export function getActiveCardSeriesList(params: { skip?: number; limit?: number }) {
	return request({
		url: "card-series/active/list",
		method: "get",
		params,
	});
}

/**
 * 获取卡牌系列详情
 */
export function getCardSeriesDetail(seriesId: number) {
	return request({
		url: `card-series/${seriesId}`,
		method: "get",
	});
}

/**
 * 通过编码获取卡牌系列
 */
export function getCardSeriesByCode(code: string) {
	return request({
		url: `card-series/code/${code}`,
		method: "get",
	});
}

/**
 * 创建卡牌系列
 */
export function createCardSeries(data: CardSeriesCreate) {
	return request({
		url: "card-series/",
		method: "post",
		data,
	});
}

/**
 * 更新卡牌系列
 */
export function updateCardSeries(seriesId: number, data: CardSeriesUpdate) {
	return request({
		url: `card-series/${seriesId}`,
		method: "put",
		data,
	});
}

/**
 * 删除卡牌系列
 */
export function deleteCardSeries(seriesId: number) {
	return request({
		url: `card-series/${seriesId}`,
		method: "delete",
	});
}
