/**
 * 世界观类型定义
 */

// 世界观信息
export interface World {
	id: string;
	title: string;
	type: string; // 场景，世界观
	description: string;
	image_url: string;
	imageUrl?: string; // 兼容旧代码
	created_at: string;
	updated_at: string;
	knowledge_count: number;
	knowledgeCount?: number; // 兼容旧代码
	sort?: number; // 排序
	grade?: number; // 等级
	tags?: string[]; // 标签
	completeness?: number; // 完整度
}

// 创建世界观的请求数据
export interface WorldCreate {
	title: string;
	type: string;
	description: string;
	image_url?: string;
	sort?: number;
}

// 更新世界观的请求数据
export interface WorldUpdate {
	title?: string;
	type?: string;
	description?: string;
	image_url?: string;
	sort?: number;
}

// 世界观知识
export interface WorldKnowledge {
	id: number;
	worlds_id: string;
	type: any;
	title: string;
	text: string;
	grade: number;
	source?: string;
	tags?: string;
	relations?: string;
	relations_role?: string;
	created_at: string;
	updated_at: string;
}

// 创建世界观知识的请求数据
export interface WorldKnowledgeCreate {
	id: string;
	worlds_id: string;
	type: any;
	title: string;
	text: string;
	grade: number;
	source?: string;
	tags?: any;
	relations?: string;
	relations_role?: string;
	relations_roles?: string[];
}

// 更新世界观知识的请求数据
export interface WorldKnowledgeUpdate {
	worlds_id?: string;
	type?: any;
	title?: string;
	text?: string;
	grade?: number;
	source?: string;
	tags?: string;
	relations?: string;
	relations_role?: string;
}

// 新增世界观知识库相关接口
export interface WorldKnowledgeBulkCreate {
	items: WorldKnowledgeCreate[];
}

// 相关场景
export interface Scene {
	id: string;
	title: string;
	description: string;
	worldId: string;
	imageUrl: string;
}
