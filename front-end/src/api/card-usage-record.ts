import request from "@/utils/request";

interface CardUsageRecordModel {
	id: number;
	user_id: number;
	card_id: number;
	usage_type: string;
	related_id: number | null;
	start_time: string;
	end_time: string | null;
	points_earned: number | null;
	creator_id: number | null;
	create_time: string;
}

interface CardUsageRecordCreate {
	user_id: number;
	card_id: number;
	usage_type: string;
	related_id?: number | null;
	start_time: string;
	end_time?: string | null;
	points_earned?: number | null;
	creator_id?: number | null;
}

interface CardUsageRecordUpdate {
	end_time?: string | null;
	points_earned?: number | null;
}

// 创建卡牌使用记录
export function createCardUsageRecord(data: CardUsageRecordCreate) {
	return request({
		url: "card_usage_records",
		method: "post",
		data,
	});
}

// 获取所有卡牌使用记录（不分页）
export function getAllCardUsageRecords(limit = 100) {
	return request<CardUsageRecordModel[]>({
		url: "card_usage_records/all",
		method: "get",
		params: { limit },
	});
}

// 获取单个卡牌使用记录
export function getCardUsageRecord(id: number) {
	return request<CardUsageRecordModel>({
		url: `card_usage_records/${id}`,
		method: "get",
	});
}

// 获取卡牌使用记录列表（分页）
export function getCardUsageRecords(params: any) {
	return request<{
		items: CardUsageRecordModel[];
		total: number;
		page: number;
		size: number;
		pages: number;
	}>({
		url: "card_usage_records",
		method: "get",
		params,
	});
}

// 获取用户的所有卡牌使用记录
export function getUserCardUsageRecords(userId: number, limit = 100) {
	return request<CardUsageRecordModel[]>({
		url: `card_usage_records/user/${userId}`,
		method: "get",
		params: { limit },
	});
}

// 获取特定卡牌的所有使用记录
export function getCardSpecificUsageRecords(cardId: number, limit = 100) {
	return request<CardUsageRecordModel[]>({
		url: `card_usage_records/card/${cardId}`,
		method: "get",
		params: { limit },
	});
}

// 获取用户特定卡牌的所有使用记录
export function getUserCardSpecificUsageRecords(userId: number, cardId: number, limit = 100) {
	return request<CardUsageRecordModel[]>({
		url: `card_usage_records/user/${userId}/card/${cardId}`,
		method: "get",
		params: { limit },
	});
}

// 获取特定使用类型的所有记录
export function getUsageTypeRecords(usageType: string, limit = 100) {
	return request<CardUsageRecordModel[]>({
		url: `card_usage_records/type/${usageType}`,
		method: "get",
		params: { limit },
	});
}

// 获取用户特定类型的所有使用记录
export function getUserUsageTypeRecords(userId: number, usageType: string, limit = 100) {
	return request<CardUsageRecordModel[]>({
		url: `card_usage_records/user/${userId}/type/${usageType}`,
		method: "get",
		params: { limit },
	});
}

// 获取用户卡牌使用统计信息
export function getUserUsageStatistics(userId: number) {
	return request<{
		total_count: number;
		type_counts: Record<string, number>;
		total_points: number;
		card_counts: Record<string, number>;
	}>({
		url: `card_usage_records/user/${userId}/stats`,
		method: "get",
	});
}

// 更新卡牌使用记录
export function updateCardUsageRecord(id: number, data: CardUsageRecordUpdate) {
	return request<CardUsageRecordModel>({
		url: `card_usage_records/${id}`,
		method: "put",
		data,
	});
}

// 结束卡牌使用（更新结束时间）
export function endCardUsage(id: number, endTime?: string) {
	return request<CardUsageRecordModel>({
		url: `card_usage_records/${id}/end`,
		method: "put",
		params: endTime ? { end_time: endTime } : {},
	});
}

// 更新卡牌使用获得的积分
export function updateRecordPoints(id: number, pointsEarned: number) {
	return request<CardUsageRecordModel>({
		url: `card_usage_records/${id}/points`,
		method: "put",
		params: { points_earned: pointsEarned },
	});
}

// 删除卡牌使用记录
export function deleteCardUsageRecord(id: number) {
	return request<boolean>({
		url: `card_usage_records/${id}`,
		method: "delete",
	});
}
