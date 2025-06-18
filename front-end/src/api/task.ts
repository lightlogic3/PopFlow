import request from "@/utils/request";

/**
 * 获取任务列表（分页）
 */
export function getTaskList(params?: { page?: number; size?: number }) {
	return request({
		url: "tasks/",
		method: "get",
		params,
	});
}

/**
 * 获取任务详情
 */
export function getTaskDetail(taskId: number) {
	return request({
		url: `tasks/${taskId}`,
		method: "get",
	});
}

/**
 * 创建任务
 */
export function createTask(data: {
	title: string;
	description: string;
	setting?: string;
	hidden_settings?: string;
	max_dialogue_rounds?: number;
	goal?: string;
	goal_score?: number;
	score_range?: string;
	status?: number;
	task_type: string;
	difficulty: string;
	time_period?: string;
	required_user_level?: number;
	game_type?: string;
	game_play_type_id?: number;
	rule_data?: object;
	role_relations?: Array<{
		role_id: string;
		character_level: number;
	}>;
}) {
	return request({
		url: "tasks/",
		method: "post",
		data,
	});
}

/**
 * 更新任务
 */
export function updateTask(
	taskId: number,
	data: {
		title?: string;
		description?: string;
		setting?: string;
		hidden_settings?: string;
		max_dialogue_rounds?: number;
		goal?: string;
		goal_score?: number;
		score_range?: string;
		status?: number;
		task_type?: string;
		difficulty?: string;
		time_period?: string;
		required_user_level?: number;
		game_type?: string;
		game_play_type_id?: number;
		rule_data?: object;
		role_relations?: Array<{
			role_id: string;
			character_level: number;
		}>;
	},
) {
	return request({
		url: `tasks/${taskId}`,
		method: "put",
		data,
	});
}

/**
 * 删除任务
 */
export function deleteTask(taskId: number) {
	return request({
		url: `tasks/${taskId}`,
		method: "delete",
	});
}

/**
 * 获取任务的角色关联
 */
export function getTaskRelations(taskId: number) {
	return request({
		url: `tasks/${taskId}/relations`,
		method: "get",
	});
}

/**
 * 模拟任务对话（测试用）
 */
export function simulateTaskChat(data: {
	task_id: number;
	user_message: string;
	user_data: {
		name: string;
		background: string;
		role_relations: Record<string, number>;
	};
}) {
	return request({
		url: "tasks/chat/simulate",
		method: "post",
		data,
	});
}

/**
 * 更新任务角色关联
 */
export function updateTaskRelation(relationId: number, data: any) {
	return request({
		url: `tasks/relations/${relationId}`,
		method: "put",
		data,
	});
}
