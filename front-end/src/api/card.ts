import request from "@/utils/request";

// 卡牌接口类型定义
export interface Card {
	id: number;
	name: string;
	series_id: number;
	rarity: number;
	description?: string;
	image_url?: string;
	sort_order: number;
	unlock_type: string; // 'both' 或 'box_only'
	points_required?: number;
	duplicate_points: number;
	status: number;
	is_limited: number;
	limited_count?: number;
	role_id?: number | string;
	blind_box_id?: number;
	box_drop_rate?: number; // 盲盒掉落概率
	victory_points?: number; // 胜利获得积分
	game_cost_points?: number; // 游戏抵扣积分
	created_at?: string;
	updated_at?: string;
}

export interface CardCreate {
	name: string;
	series_id: number;
	rarity: number;
	description?: string;
	image_url?: string;
	sort_order: number;
	unlock_type: string;
	points_required?: number;
	duplicate_points: number;
	is_limited: number;
	limited_count?: number;
	role_id?: number | string;
	blind_box_id?: number;
	box_drop_rate?: number; // 盲盒掉落概率
	victory_points?: number; // 胜利获得积分
	game_cost_points?: number; // 游戏抵扣积分
}

export interface CardUpdate {
	name?: string;
	series_id?: number;
	rarity?: number;
	description?: string;
	image_url?: string;
	sort_order?: number;
	unlock_type?: string;
	points_required?: number;
	duplicate_points?: number;
	status?: number;
	is_limited?: number;
	limited_count?: number;
	role_id?: number | string;
	blind_box_id?: number;
	box_drop_rate?: number; // 盲盒掉落概率
	victory_points?: number; // 胜利获得积分
	game_cost_points?: number; // 游戏抵扣积分
}

export interface CardFilter {
	name?: string;
	series_id?: number;
	rarity?: number;
	unlock_type?: string;
	status?: number;
	role_id?: string;
	is_limited?: number;
	page?: number;
	size?: number;
}

/**
 * 获取卡牌列表（分页）
 */
export function getCardList(params: any) {
	// 过滤掉空值参数
	const filteredParams: any = {};
	Object.keys(params).forEach((key) => {
		const value = (params as any)[key];
		if (value !== null && value !== undefined && value !== "") {
			filteredParams[key] = value;
		}
	});

	return request({
		url: "cards/",
		method: "get",
		params: filteredParams,
	});
}

/**
 * 获取卡牌详情
 */
export function getCardDetail(cardId: number) {
	return request({
		url: `cards/${cardId}`,
		method: "get",
	});
}

/**
 * 根据系列ID获取卡牌列表
 */
export function getCardsBySeriesId(
	seriesId: number,
	params: {
		skip?: number;
		limit?: number;
	},
) {
	return request({
		url: `cards/series/${seriesId}/list`,
		method: "get",
		params,
	});
}
/**
 * 创建卡牌
 */
export function createCard(data: CardCreate) {
	return request({
		url: "cards/",
		method: "post",
		data,
	});
}

/**
 * 更新卡牌
 */
export function updateCard(cardId: number, data: CardUpdate) {
	return request({
		url: `cards/${cardId}`,
		method: "put",
		data,
	});
}

/**
 * 删除卡牌
 */
export function deleteCard(cardId: number) {
	return request({
		url: `cards/${cardId}`,
		method: "delete",
	});
}

/**
 * 统计系列下的卡牌数量
 */
export function countCardsBySeries(seriesId: number) {
	return request({
		url: `cards/series/${seriesId}/count`,
		method: "get",
	});
}

/**
 * 获取稀有度选项
 */
export function getRarityChoices() {
	return request({
		url: "cards/enums/rarity",
		method: "get",
	});
}

/**
 * 获取解锁类型选项
 */
export function getUnlockTypeChoices() {
	return request({
		url: "cards/enums/unlock-type",
		method: "get",
	});
}
