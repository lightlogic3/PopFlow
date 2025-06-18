import request from "@/utils/request";

// 积分变动类型枚举
export enum PointChangeType {
	REGISTER = "register",
	AI_CHALLENGE = "ai_challenge",
	UNLOCK_CARD = "unlock_card",
	DUPLICATE_CARD = "duplicate_card",
	BUY_BLIND_BOX = "buy_blind_box",
	ADMIN_ADJUST = "admin_adjust",
	SYSTEM_REWARD = "system_reward",
	DAILY_CHECK = "daily_check",
	TASK_REWARD = "task_reward",
	EVENT_REWARD = "event_reward",
	CARD_SELL = "card_sell",
	CARD_UPGRADE = "card_upgrade",
	SHOP_PURCHASE = "shop_purchase",
	REFUND = "refund",
	PENALTY = "penalty",
}

// 积分记录接口
export interface PointRecord {
	id: number;
	user_id: number;
	change_amount: number;
	current_amount: number;
	change_type: PointChangeType;
	related_id?: number;
	card_id?: number;
	description?: string;
	creator_id?: number;
	create_time: string;
	change_type_display?: string;
	is_income: boolean;
}

// 积分记录创建
export interface PointRecordCreate {
	user_id: number;
	change_amount: number;
	current_amount: number;
	change_type: PointChangeType;
	related_id?: number;
	card_id?: number;
	description?: string;
}

// 积分记录更新
export interface PointRecordUpdate {
	description?: string;
}

// 积分记录过滤
export interface PointRecordFilter {
	user_id?: number;
	change_type?: PointChangeType;
	card_id?: number;
	related_id?: number;
	min_amount?: number;
	max_amount?: number;
	start_time?: string;
	end_time?: string;
}

// 积分记录统计
export interface PointRecordStatistics {
	total_records: number;
	total_income: number;
	total_expense: number;
	net_change: number;
	most_common_type: string;
	avg_change_amount: number;
	daily_stats: Array<{
		date: string;
		income: number;
		expense: number;
		net: number;
		count: number;
	}>;
	type_distribution: Record<
		string,
		{
			count: number;
			total_amount: number;
			avg_amount: number;
			display_name: string;
		}
	>;
}

// 用户积分汇总
export interface UserPointSummary {
	user_id: number;
	total_income: number;
	total_expense: number;
	net_change: number;
	total_records: number;
	current_amount: number;
	last_change_time?: string;
}

// 批量创建积分记录
export interface PointRecordBatchCreate {
	records: PointRecordCreate[];
	description?: string;
}

// 积分收入排行
export interface TopEarner {
	user_id: number;
	total_earned: number;
	rank: number;
}

// 变动类型信息
export interface ChangeTypeInfo {
	code: string;
	display_name: string;
	description: string;
}

// 基础CRUD操作

/**
 * 创建积分记录
 */
export function createPointRecord(data: PointRecordCreate, autoUpdateUserDetail = true) {
	return request({
		url: "point-record/",
		method: "post",
		data,
		params: { auto_update_user_detail: autoUpdateUserDetail },
	});
}

/**
 * 批量创建积分记录
 */
export function batchCreatePointRecords(data: PointRecordBatchCreate) {
	return request({
		url: "point-record/batch",
		method: "post",
		data,
	});
}

/**
 * 获取积分记录详情
 */
export function getPointRecord(id: number) {
	return request({
		url: `point-record/${id}`,
		method: "get",
	});
}

/**
 * 获取积分记录列表（分页）
 */
export function getPointRecords(
	params: PointRecordFilter & {
		page?: number;
		size?: number;
	} = {},
) {
	return request({
		url: "point-record/",
		method: "get",
		params,
	});
}

/**
 * 更新积分记录
 */
export function updatePointRecord(id: number, data: PointRecordUpdate) {
	return request({
		url: `point-record/${id}`,
		method: "put",
		data,
	});
}

/**
 * 删除积分记录
 */
export function deletePointRecord(id: number) {
	return request({
		url: `point-record/${id}`,
		method: "delete",
	});
}

// 用户相关接口

/**
 * 获取用户积分记录
 */
export function getUserPointRecords(
	userId: number,
	params: {
		limit?: number;
		change_type?: PointChangeType;
	} = {},
) {
	return request({
		url: `point-record/user/${userId}/records`,
		method: "get",
		params,
	});
}

/**
 * 获取用户积分汇总
 */
export function getUserPointSummary(userId: number) {
	return request({
		url: `point-record/user/${userId}/summary`,
		method: "get",
	});
}

// 统计相关接口

/**
 * 获取积分记录统计
 */
export function getPointRecordStatistics(
	params: {
		user_id?: number;
		start_time?: string;
		end_time?: string;
	} = {},
) {
	return request({
		url: "point-record/statistics/overview",
		method: "get",
		params,
	});
}

/**
 * 获取每日积分统计
 */
export function getDailyStatistics(params: { start_date: string; end_date: string; user_id?: number }) {
	return request({
		url: "point-record/statistics/daily",
		method: "get",
		params,
	});
}

/**
 * 获取类型分布统计
 */
export function getTypeDistribution(
	params: {
		user_id?: number;
		start_time?: string;
		end_time?: string;
	} = {},
) {
	return request({
		url: "point-record/statistics/type-distribution",
		method: "get",
		params,
	});
}

/**
 * 获取积分收入排行榜
 */
export function getTopEarners(
	params: {
		limit?: number;
		days?: number;
	} = {},
) {
	return request({
		url: "point-record/statistics/top-earners",
		method: "get",
		params,
	});
}

/**
 * 获取大额交易记录
 */
export function getLargeTransactions(
	params: {
		min_amount?: number;
		limit?: number;
	} = {},
) {
	return request({
		url: "point-record/statistics/large-transactions",
		method: "get",
		params,
	});
}

// 按类型查询

/**
 * 根据变动类型获取记录
 */
export function getRecordsByType(
	changeType: PointChangeType,
	params: {
		limit?: number;
		user_id?: number;
	} = {},
) {
	return request({
		url: `point-record/by-type/${changeType}`,
		method: "get",
		params,
	});
}

/**
 * 获取所有变动类型
 */
export function getAllChangeTypes() {
	return request({
		url: "point-record/types/all",
		method: "get",
	});
}

// 快速操作接口

/**
 * 快速奖励积分
 */
export function quickRewardPoints(params: {
	user_id: number;
	amount: number;
	change_type?: PointChangeType;
	description?: string;
	related_id?: number;
	card_id?: number;
}) {
	return request({
		url: "point-record/quick-actions/reward",
		method: "post",
		params,
	});
}

/**
 * 快速扣除积分
 */
export function quickDeductPoints(params: {
	user_id: number;
	amount: number;
	change_type?: PointChangeType;
	description?: string;
	related_id?: number;
	card_id?: number;
}) {
	return request({
		url: "point-record/quick-actions/deduct",
		method: "post",
		params,
	});
}

// 积分变动类型显示名称映射
export const POINT_CHANGE_TYPE_DISPLAY: Record<PointChangeType, string> = {
	[PointChangeType.REGISTER]: "注册奖励",
	[PointChangeType.AI_CHALLENGE]: "AI挑战奖励",
	[PointChangeType.UNLOCK_CARD]: "解锁卡牌",
	[PointChangeType.DUPLICATE_CARD]: "重复卡牌",
	[PointChangeType.BUY_BLIND_BOX]: "购买盲盒",
	[PointChangeType.ADMIN_ADJUST]: "管理员调整",
	[PointChangeType.SYSTEM_REWARD]: "系统奖励",
	[PointChangeType.DAILY_CHECK]: "每日签到",
	[PointChangeType.TASK_REWARD]: "任务奖励",
	[PointChangeType.EVENT_REWARD]: "活动奖励",
	[PointChangeType.CARD_SELL]: "出售卡牌",
	[PointChangeType.CARD_UPGRADE]: "卡牌升级",
	[PointChangeType.SHOP_PURCHASE]: "商店购买",
	[PointChangeType.REFUND]: "退款",
	[PointChangeType.PENALTY]: "惩罚扣除",
};
