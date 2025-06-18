/**
 * 角色类型定义
 */

// 角色信息
export interface Role {
	id: string;
	name: string;
	role_id: string;
	level?: number; // 在API中是sort
	sort?: number; // API字段
	imageUrl?: string; // 前端使用
	image_url?: string; // API字段
	knowledgeCount?: number; // 前端使用
	knowledge_count?: number; // API字段
	completeness?: number;
	created_at?: string;
	updated_at?: string;
	role_tags?: string[];
	role_type: string;
	llm_choose: string;
	tags: string;
	worldview_control: string;
}

// 创建角色的请求数据
export interface RoleCreate {
	name: string;
	sort?: number;
	image_url?: string;
	knowledge_count?: number;
	role_id: string;
	role_type: string;
	llm_choose: string;
	tags: string;
	worldview_control: string;
}

// 更新角色的请求数据
export interface RoleUpdate {
	name?: string;
	sort?: number;
	image_url?: string;
	knowledge_count?: number;
	role_type: string;
	llm_choose: string;
	tags: string;
	worldview_control: string;
}

// 角色提示词
export interface RolePrompt {
	id: number;
	role_id: string;
	level: number;
	prompt_text: string;
	status: number;
	created_at: string;
	updated_at: string;
}

// 角色知识 - 新API
export interface RoleKnowledge {
	id: number;
	text: string;
	role_id: string;
	type: string; // 基本经历，角色经历，共同经历
	title: string;
	grade: number;
	source?: string;
	tags?: any;
	relations?: string;
	relations_role?: string;
	created_at: string;
	updated_at: string;
}

// 创建角色知识的请求数据
export interface RoleKnowledgeCreate {
	text: string;
	role_id: string;
	type: string;
	title: string;
	grade: number;
	source?: string;
	tags?: any;
	relations?: string;
	relations_role?: string;
	relations_roles?: Array<string>;
}

// 更新角色知识的请求数据
export interface RoleKnowledgeUpdate {
	text?: string;
	role_id?: string;
	type?: string;
	title?: string;
	grade?: number;
	source?: string;
	tags?: Array<string>;
	relations?: string;
	relations_role?: string;
	relations_roles?: Array<string>;
}
