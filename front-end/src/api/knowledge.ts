import request from "@/utils/request";

/**
 * 知识库查询参数
 */
export interface KnowledgeQueryParams {
	query: string;
	top_k?: number;
	role_id?: string;
	level?: number;
	user_level?: number;
}

/**
 * 知识库查询结果
 */
export interface KnowledgeResult {
	id?: string;
	title: string;
	text: string;
	score: number;
	grade?: number;
	source?: string;
	role_id?: string;
	world_id?: string;
	type?: string;
	relations_role?: string;
	source_type?: "role" | "world";
}

/**
 * 查询角色知识库
 */
export const queryRoleKnowledge = (params: KnowledgeQueryParams): Promise<KnowledgeResult[]> => {
	return request({
		url: "/knowledge/query_role_role",
		method: "post",
		data: params,
	});
};

/**
 * 查询世界知识库
 */
export const queryWorldKnowledge = (params: KnowledgeQueryParams): Promise<KnowledgeResult[]> => {
	return request({
		url: "/knowledge/query_world",
		method: "post",
		data: params,
	});
};
