import request from "@/utils/request";

interface UserCardModel {
	id: number;
	user_id: number;
	card_id: number;
	obtain_type: string;
	obtain_time: string;
	use_count: number;
	last_use_time: string | null;
	is_favorite: boolean;
	creator_id: number | null;
	create_time: string;
	update_time: string;
}

interface UserCardCreate {
	user_id: number;
	card_id: number;
	obtain_type: string;
	obtain_time?: string;
	use_count?: number;
	last_use_time?: string | null;
	is_favorite?: boolean;
	creator_id?: number | null;
}

interface UserCardUpdate {
	use_count?: number;
	last_use_time?: string | null;
	is_favorite?: boolean;
}

// 创建用户卡牌记录
export function createUserCard(data: UserCardCreate) {
	return request({
		url: "user_cards",
		method: "post",
		data,
	});
}

// 获取所有用户卡牌记录（不分页）
export function getAllUserCards(limit = 100) {
	return request<UserCardModel[]>({
		url: "user_cards/all",
		method: "get",
		params: { limit },
	});
}

// 获取单个用户卡牌记录
export function getUserCard(id: number) {
	return request<UserCardModel>({
		url: `user_cards/${id}`,
		method: "get",
	});
}

// 获取用户卡牌记录列表（分页）
export function getUserCards(params: any) {
	return request<{
		items: UserCardModel[];
		total: number;
		page: number;
		size: number;
		pages: number;
	}>({
		url: "user_cards",
		method: "get",
		params,
	});
}

// 获取指定用户的所有卡牌
export function getUserCardsByUserId(userId: number) {
	return request<UserCardModel[]>({
		url: `user_cards/user/${userId}`,
		method: "get",
	});
}

// 更新用户卡牌记录
export function updateUserCard(id: number, data: UserCardUpdate) {
	return request<UserCardModel>({
		url: `user_cards/${id}`,
		method: "put",
		data,
	});
}

// 更新用户卡牌收藏状态
export function updateUserCardFavorite(userId: number, cardId: number, isFavorite: boolean) {
	return request<UserCardModel>({
		url: `user_cards/favorite/${userId}/${cardId}`,
		method: "put",
		params: { is_favorite: isFavorite },
	});
}

// 增加卡牌使用次数
export function incrementCardUseCount(userId: number, cardId: number) {
	return request<UserCardModel>({
		url: `user_cards/increment_use/${userId}/${cardId}`,
		method: "put",
	});
}

// 删除用户卡牌记录
export function deleteUserCard(id: number) {
	return request<boolean>({
		url: `user_cards/${id}`,
		method: "delete",
	});
}

// 根据用户ID和卡牌ID删除用户卡牌记录
export function deleteUserCardByIds(userId: number, cardId: number) {
	return request<boolean>({
		url: `user_cards/user/${userId}/card/${cardId}`,
		method: "delete",
	});
}
