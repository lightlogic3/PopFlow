import request from "@/utils/request";

interface UserBlindBoxStatsModel {
	id: number;
	user_id: number;
	blind_box_id: number;
	total_draws: number;
	current_pity_count: number;
	guaranteed_trigger_count: number;
	special_reward_count: number;
	create_time: string;
	update_time: string;
}

interface UserBlindBoxStatsCreate {
	user_id: number;
	blind_box_id: number;
	total_draws?: number;
	current_pity_count?: number;
	guaranteed_trigger_count?: number;
	special_reward_count?: number;
}

interface UserBlindBoxStatsUpdate {
	total_draws?: number;
	current_pity_count?: number;
	guaranteed_trigger_count?: number;
	special_reward_count?: number;
}

// 创建用户盲盒统计记录
export function createUserBlindBoxStats(data: UserBlindBoxStatsCreate) {
	return request<UserBlindBoxStatsModel>({
		url: "user_blind_box_stats",
		method: "post",
		data,
	});
}

// 获取用户盲盒统计记录
export function getUserBlindBoxStats(id: number) {
	return request<UserBlindBoxStatsModel>({
		url: `user_blind_box_stats/${id}`,
		method: "get",
	});
}

// 获取用户所有盲盒统计记录
export function getUserAllBlindBoxStats(userId: number) {
	return request({
		url: `user_blind_box_stats/user/${userId}/all_stats`,
		method: "get",
	});
}

/**
 * 获取用户特定盲盒的统计信息
 * @param userId 用户ID
 * @param blindBoxId 盲盒ID
 * @returns 统计信息及概率信息
 */
export function getUserSpecificBlindBoxStats(userId: number, blindBoxId: number) {
	return request({
		url: `user_blind_box_stats/user/${userId}/box/${blindBoxId}`,
		method: "get",
	});
}

// 更新用户盲盒统计记录
export function updateUserBlindBoxStats(id: number, data: UserBlindBoxStatsUpdate) {
	return request<UserBlindBoxStatsModel>({
		url: `user_blind_box_stats/${id}`,
		method: "put",
		data,
	});
}

/**
 * 增加用户盲盒抽取次数和保底计数
 * @param userId 用户ID
 * @param blindBoxId 盲盒ID
 * @returns 更新后的统计信息
 */
export function incrementDrawCount(userId: number, blindBoxId: number) {
	return request({
		url: `user_blind_box_stats/user/${userId}/box/${blindBoxId}/increment`,
		method: "put",
	});
}

/**
 * 触发保底，重置保底计数并记录保底时间
 * @param userId 用户ID
 * @param blindBoxId 盲盒ID
 * @returns 更新后的统计信息
 */
export function triggerGuaranteed(userId: number, blindBoxId: number) {
	return request({
		url: `user_blind_box_stats/user/${userId}/box/${blindBoxId}/trigger-guaranteed`,
		method: "put",
	});
}

// 增加特殊奖励次数
export function addSpecialReward(userId: number, blindBoxId: number) {
	return request<UserBlindBoxStatsModel>({
		url: `user_blind_box_stats/user/${userId}/box/${blindBoxId}/add-special`,
		method: "put",
	});
}

/**
 * 重置用户盲盒保底计数
 * @param userId 用户ID
 * @param blindBoxId 盲盒ID
 * @param newCount 新的保底计数
 * @returns 更新后的统计信息
 */
export function resetPityCounter(userId: number, blindBoxId: number, newCount: number) {
	return request({
		url: `user_blind_box_stats/user/${userId}/box/${blindBoxId}/reset-pity?new_count=${newCount}`,
		method: "put",
	});
}

// 删除用户盲盒统计记录
export function deleteUserBlindBoxStats(id: number) {
	return request<boolean>({
		url: `user_blind_box_stats/${id}`,
		method: "delete",
	});
}
