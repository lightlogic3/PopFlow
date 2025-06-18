import request from "@/utils/request";

/**
 * 用户详情API接口
 */

// 数据类型定义
export interface UserDetailCreate {
	user_id: number;
	total_points?: number;
	available_points?: number;
	total_login_count?: number;
	total_ai_challenge_count?: number;
	total_ai_challenge_success_count?: number;
	total_points_earned?: number;
	total_points_spent?: number;
	total_card_count?: number;
	total_blind_box_opened?: number;
	last_active_time?: string;
	creator_id?: number;
	updater_id?: number;
}

export interface UserDetailUpdate {
	total_points?: number;
	available_points?: number;
	total_login_count?: number;
	total_ai_challenge_count?: number;
	total_ai_challenge_success_count?: number;
	total_points_earned?: number;
	total_points_spent?: number;
	total_card_count?: number;
	total_blind_box_opened?: number;
	last_active_time?: string;
	updater_id?: number;
}

export interface UserDetailResponse {
	id: number;
	user_id: number;
	total_points: number;
	available_points: number;
	total_login_count: number;
	total_ai_challenge_count: number;
	total_ai_challenge_success_count: number;
	total_points_earned: number;
	total_points_spent: number;
	total_card_count: number;
	total_blind_box_opened: number;
	last_active_time?: string;
	creator_id?: number;
	updater_id?: number;
	create_time: string;
	update_time: string;
	challenge_success_rate?: number;
	points_usage_rate?: number;
}

export interface UserDetailStatistics {
	total_users: number;
	total_points_in_system: number;
	average_points_per_user: number;
	total_challenges: number;
	average_challenge_success_rate: number;
	total_cards_in_system: number;
	total_blind_boxes_opened: number;
	most_active_users: Array<{
		user_id: number;
		login_count: number;
	}>;
}

// CRUD 操作
/**
 * 创建用户详情
 */
export function createUserDetail(data: UserDetailCreate) {
	return request({
		url: "user-detail/",
		method: "post",
		data,
	});
}

/**
 * 获取用户详情列表（分页）
 */
export function getUserDetailList(params: {
	page: number;
	size: number;
	user_id?: number;
	min_total_points?: number;
	max_total_points?: number;
	min_login_count?: number;
	min_challenge_count?: number;
}) {
	return request({
		url: "user-detail/",
		method: "get",
		params,
	});
}

/**
 * 获取用户详情
 */
export function getUserDetail(detailId: number) {
	return request({
		url: `user-detail/${detailId}`,
		method: "get",
	});
}

/**
 * 根据用户ID获取用户详情
 */
export function getUserDetailByUserId(userId: number) {
	return request({
		url: `user-detail/by-user/${userId}`,
		method: "get",
	});
}

/**
 * 更新用户详情
 */
export function updateUserDetail(detailId: number, data: UserDetailUpdate) {
	return request({
		url: `user-detail/${detailId}`,
		method: "put",
		data,
	});
}

/**
 * 根据用户ID更新用户详情
 */
export function updateUserDetailByUserId(userId: number, data: UserDetailUpdate) {
	return request({
		url: `user-detail/by-user/${userId}`,
		method: "put",
		data,
	});
}

/**
 * 删除用户详情
 */
export function deleteUserDetail(detailId: number) {
	return request({
		url: `user-detail/${detailId}`,
		method: "delete",
	});
}

// 统计相关接口
/**
 * 获取用户详情统计数据
 */
export function getUserDetailStatistics() {
	return request({
		url: "user-detail/statistics/overview",
		method: "get",
	});
}

/**
 * 获取积分排行榜
 */
export function getPointsRanking(limit: number = 10) {
	return request({
		url: "user-detail/ranking/points",
		method: "get",
		params: { limit },
	});
}

/**
 * 获取挑战次数排行榜
 */
export function getChallengesRanking(limit: number = 10) {
	return request({
		url: "user-detail/ranking/challenges",
		method: "get",
		params: { limit },
	});
}

/**
 * 获取最活跃用户排行榜
 */
export function getActiveRanking(limit: number = 10) {
	return request({
		url: "user-detail/ranking/active",
		method: "get",
		params: { limit },
	});
}

// 游戏行为更新接口
/**
 * 更新用户登录次数
 */
export function updateLoginCount(userId: number) {
	return request({
		url: `user-detail/actions/login/${userId}`,
		method: "post",
	});
}

/**
 * 更新用户挑战统计
 */
export function updateChallengeStats(userId: number, success: boolean = false) {
	return request({
		url: `user-detail/actions/challenge/${userId}`,
		method: "post",
		params: { success },
	});
}

/**
 * 更新用户积分
 */
export function updatePoints(userId: number, pointsChange: number, isEarned: boolean = true) {
	return request({
		url: `user-detail/actions/points/${userId}`,
		method: "post",
		params: {
			points_change: pointsChange,
			is_earned: isEarned,
		},
	});
}

/**
 * 更新用户卡牌数量
 */
export function updateCardCount(userId: number, countChange: number) {
	return request({
		url: `user-detail/actions/cards/${userId}`,
		method: "post",
		params: { count_change: countChange },
	});
}

/**
 * 更新用户开启盲盒次数
 */
export function updateBlindBoxCount(userId: number) {
	return request({
		url: `user-detail/actions/blind-box/${userId}`,
		method: "post",
	});
}
