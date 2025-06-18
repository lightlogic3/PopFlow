import request from "@/utils/request";

/**
 * 游戏类型接口定义
 */
export interface GamePlayType {
	id: string | number;
	name: string;
	description?: string;
	setting?: string;
	reference_case?: string;
	form_schema?: any;
	ui_schema?: any;
	validation_schema?: any;
	version?: string;
	additional_content?: any;
	player_count?: string;
	status?: number;
	created_at?: string;
	updated_at?: string;
}

/**
 * 获取游戏类型列表
 */
export function getGamePlayTypes(params?: { skip?: number; limit?: number }) {
	return request({
		url: "game_play_types/",
		method: "get",
		params,
	});
}

/**
 * 获取游戏类型详情
 */
export function getGamePlayType(gamePlayTypeId: number | string) {
	return request({
		url: `game_play_types/${gamePlayTypeId}`,
		method: "get",
	});
}

/**
 * 创建游戏类型
 */
export function createGamePlayType(data: {
	name: string;
	description?: string;
	setting?: string;
	reference_case?: string;
	form_schema?: any;
	ui_schema?: any;
	validation_schema?: any;
	version?: string;
	additional_content?: any;
	player_count?: string;
	status?: number;
}) {
	return request({
		url: "game_play_types/",
		method: "post",
		data,
	});
}

/**
 * 更新游戏类型
 */
export function updateGamePlayType(
	gamePlayTypeId: number | string,
	data: {
		name?: string;
		description?: string;
		setting?: string;
		reference_case?: string;
		form_schema?: any;
		ui_schema?: any;
		validation_schema?: any;
		version?: string;
		additional_content?: any;
		player_count?: string;
		status?: number;
	},
) {
	return request({
		url: `game_play_types/${gamePlayTypeId}`,
		method: "put",
		data,
	});
}

/**
 * 删除游戏类型
 */
export function deleteGamePlayType(gamePlayTypeId: number | string) {
	return request({
		url: `game_play_types/${gamePlayTypeId}`,
		method: "delete",
	});
}

export function getGameRelations(gamePlayTypeId: number | string) {
	return request({
		url: `game_play_types/${gamePlayTypeId}/relations`,
		method: "get",
	});
}

export function updateGameRelations(relation_id: number | string, data: any) {
	return request({
		url: `game_play_types/relations/${relation_id}`,
		method: "put",
		data,
	});
}
