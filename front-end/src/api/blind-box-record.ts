import request from "@/utils/request";

interface BlindBoxRecordModel {
	id: number;
	user_id: number;
	blind_box_id: number;
	card_id: number;
	is_duplicate: boolean;
	points_gained: number | null;
	is_guaranteed: boolean;
	is_special_reward: boolean;
	source_type: string;
	source_id: number | null;
	creator_id: number | null;
	create_time: string;
}

interface BlindBoxRecordCreate {
	user_id: number;
	blind_box_id: number;
	card_id: number;
	is_duplicate?: boolean;
	points_gained?: number | null;
	is_guaranteed?: boolean;
	is_special_reward?: boolean;
	source_type: string;
	source_id?: number | null;
	creator_id?: number | null;
}

interface BlindBoxRecordUpdate {
	points_gained?: number | null;
	is_special_reward?: boolean;
}

// 创建盲盒抽取记录
export function createBlindBoxRecord(data: BlindBoxRecordCreate) {
	return request({
		url: "blind_box_records",
		method: "post",
		data,
	});
}

// 获取所有盲盒抽取记录（不分页）
export function getAllBlindBoxRecords(limit = 100) {
	return request<BlindBoxRecordModel[]>({
		url: "blind_box_records/all",
		method: "get",
		params: { limit },
	});
}

// 获取单个盲盒抽取记录
export function getBlindBoxRecord(id: number) {
	return request<BlindBoxRecordModel>({
		url: `blind_box_records/${id}`,
		method: "get",
	});
}

// 获取盲盒抽取记录列表（分页）
export function getBlindBoxRecords(params: any) {
	return request<{
		items: BlindBoxRecordModel[];
		total: number;
		page: number;
		size: number;
		pages: number;
	}>({
		url: "blind_box_records",
		method: "get",
		params,
	});
}

// 获取用户的所有盲盒抽取记录
export function getUserBlindBoxRecords(userId: number, limit = 100) {
	return request<BlindBoxRecordModel[]>({
		url: `blind_box_records/user/${userId}`,
		method: "get",
		params: { limit },
	});
}

// 获取特定盲盒的所有抽取记录
export function getBoxRecords(boxId: number, limit = 100) {
	return request<BlindBoxRecordModel[]>({
		url: `blind_box_records/box/${boxId}`,
		method: "get",
		params: { limit },
	});
}

// 获取用户特定盲盒的所有抽取记录
export function getUserBoxRecords(userId: number, boxId: number, limit = 100) {
	return request<BlindBoxRecordModel[]>({
		url: `blind_box_records/user/${userId}/box/${boxId}`,
		method: "get",
		params: { limit },
	});
}

// 获取特定卡牌的所有抽取记录
export function getCardDrawRecords(cardId: number, limit = 100) {
	return request<BlindBoxRecordModel[]>({
		url: `blind_box_records/card/${cardId}`,
		method: "get",
		params: { limit },
	});
}

// 获取特定来源类型的所有抽取记录
export function getSourceTypeRecords(sourceType: string, limit = 100) {
	return request<BlindBoxRecordModel[]>({
		url: `blind_box_records/source/${sourceType}`,
		method: "get",
		params: { limit },
	});
}

// 获取用户特定来源类型的所有抽取记录
export function getUserSourceRecords(userId: number, sourceType: string, limit = 100) {
	return request<BlindBoxRecordModel[]>({
		url: `blind_box_records/user/${userId}/source/${sourceType}`,
		method: "get",
		params: { limit },
	});
}

// 获取保底触发的抽取记录
export function getGuaranteedRecords(userId?: number, limit = 100) {
	return request<BlindBoxRecordModel[]>({
		url: "blind_box_records/guaranteed",
		method: "get",
		params: userId ? { user_id: userId, limit } : { limit },
	});
}

// 获取特殊奖励的抽取记录
export function getSpecialRewardRecords(userId?: number, limit = 100) {
	return request<BlindBoxRecordModel[]>({
		url: "blind_box_records/special",
		method: "get",
		params: userId ? { user_id: userId, limit } : { limit },
	});
}

// 获取用户盲盒抽取统计信息
export function getUserStats(userId: number) {
	return request<{
		total_count: number;
		source_counts: Record<string, number>;
		duplicate_count: number;
		duplicate_rate: number;
		total_points_gained: number;
		guaranteed_count: number;
		guaranteed_rate: number;
		special_count: number;
		special_rate: number;
		box_counts: Record<string, number>;
	}>({
		url: `blind_box_records/user/${userId}/stats`,
		method: "get",
	});
}

// 获取用户最近的抽取记录
export function getUserLatestRecords(userId: number, limit = 10) {
	return request<BlindBoxRecordModel[]>({
		url: `blind_box_records/user/${userId}/latest`,
		method: "get",
		params: { limit },
	});
}

// 获取特定卡牌的总抽取次数
export function getCardDrawCount(cardId: number) {
	return request<number>({
		url: `blind_box_records/card/${cardId}/count`,
		method: "get",
	});
}

// 更新盲盒抽取记录
export function updateBlindBoxRecord(id: number, data: BlindBoxRecordUpdate) {
	return request<BlindBoxRecordModel>({
		url: `blind_box_records/${id}`,
		method: "put",
		data,
	});
}

// 删除盲盒抽取记录
export function deleteBlindBoxRecord(id: number) {
	return request<boolean>({
		url: `blind_box_records/${id}`,
		method: "delete",
	});
}
