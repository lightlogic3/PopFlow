import request from "@/utils/request";

// 盲盒卡牌关联接口类型定义
export interface BlindBoxCard {
	id: number;
	blind_box_id: number;
	card_id: number;
	probability: number;
	weight: number;
	is_special_reward: number;
	creator_id?: number;
	updater_id?: number;
	create_time: string;
	update_time: string;
}

export interface BlindBoxCardCreate {
	blind_box_id: number;
	card_id: number;
	probability: number;
	weight?: number;
	is_special_reward?: number;
}

export interface BlindBoxCardUpdate {
	probability?: number;
	weight?: number;
	is_special_reward?: number;
}

// 盲盒卡牌配置接口
export interface BlindBoxCardConfig {
	card_id: number;
	probability: number;
	weight: number;
	is_special_reward: boolean;
}

// 已绑定卡片项
export interface BoundCardItem {
	blind_box_card_id: number;
	card_id: number;
	name: string;
	description?: string;
	image_url?: string;
	rarity: number;
	probability: number;
	weight: number;
	is_special_reward: boolean;
}

// 未绑定卡片项
export interface UnboundCardItem {
	id: number;
	name: string;
	description?: string;
	image_url?: string;
	rarity: number;
}

// 卡片绑定状态接口
export interface CardBindingStatusResponse {
	bound_cards: BoundCardItem[];
	unbound_cards: {
		items: UnboundCardItem[];
		total: number;
	};
}

// 卡片绑定状态查询参数
export interface CardBindingStatusParams {
	name?: string;
	rarity?: number;
	page?: number;
	size?: number;
}

/**
 * 创建盲盒卡牌关联
 */
export function createBlindBoxCard(data: BlindBoxCardCreate) {
	return request({
		url: "blind-box-card/",
		method: "post",
		data,
	});
}

/**
 * 获取盲盒关联的卡牌列表
 */
export function getBlindBoxCards(blindBoxId: number) {
	return request({
		url: `blind-box-card/blind-box/${blindBoxId}`,
		method: "get",
	});
}

/**
 * 获取盲盒已绑定和未绑定的卡牌
 */
export function getCardBindingStatus(blindBoxId: number, params?: CardBindingStatusParams) {
	return request<CardBindingStatusResponse>({
		url: `blind-box-card/blind-box/${blindBoxId}/card-status`,
		method: "get",
		params,
	});
}

/**
 * 更新盲盒卡牌关联
 */
export function updateBlindBoxCard(cardId: number, data: BlindBoxCardUpdate) {
	return request({
		url: `blind-box-card/${cardId}`,
		method: "put",
		data,
	});
}

/**
 * 删除盲盒卡牌关联
 */
export function deleteBlindBoxCard(cardId: number) {
	return request({
		url: `blind-box-card/${cardId}`,
		method: "delete",
	});
}

/**
 * 删除指定盲盒和卡牌的关联
 */
export function deleteBlindBoxCardRelation(blindBoxId: number, cardId: number) {
	return request({
		url: `blind-box-card/blind-box/${blindBoxId}/card/${cardId}`,
		method: "delete",
	});
}

/**
 * 批量创建盲盒卡牌关联
 */
export function batchCreateBlindBoxCards(blindBoxId: number, cardConfigs: BlindBoxCardConfig[]) {
	return request({
		url: `blind-box-card/blind-box/${blindBoxId}/batch`,
		method: "post",
		data: cardConfigs,
	});
}

/**
 * 清空盲盒卡牌关联
 */
export function clearBlindBoxCards(blindBoxId: number) {
	return request({
		url: `blind-box-card/blind-box/${blindBoxId}/clear`,
		method: "delete",
	});
}
