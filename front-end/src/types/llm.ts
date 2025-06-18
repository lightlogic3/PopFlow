/**
 * LLM提供商配置类型定义
 */

// LLM提供商配置
export interface LLMProvider {
	id: number;
	provider_name: string;
	api_url: string;
	api_key: string;
	model_name: string;
	remark?: string;
	status: number; // 1-启用 0-禁用
	extra_config?: Record<string, any>;
	created_at: string;
	updated_at: string;
}

// 创建LLM提供商配置请求
export interface LLMProviderCreate {
	provider_name: string;
	api_url: string;
	api_key: string;
	model_name: string;
	remark?: string;
	status?: number;
	extra_config?: any;
	provider_sign?: string; // 提供商标识
}

// 更新LLM提供商配置请求
export interface LLMProviderUpdate {
	provider_name?: string;
	api_url?: string;
	api_key?: string;
	model_name?: string;
	remark?: string;
	status?: number;
	extra_config?: any;
	provider_sign?: string; // 提供商标识
}
