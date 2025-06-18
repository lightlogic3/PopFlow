import request from "@/utils/request";

/**
 * 获取系统配置列表
 */
export function getSystemConfigList(params: { keyword?: string; skip?: number; limit?: number }) {
	return request({
		url: "system/configs/",
		method: "get",
		params,
	});
}

/**
 * 创建系统配置
 */
export function createSystemConfig(data: { config_key: string; config_value?: string; description?: string }) {
	return request({
		url: "system/configs/",
		method: "post",
		data,
	});
}

/**
 * 更新系统配置
 */
export function updateSystemConfig(
	configId: number,
	data: {
		config_key?: string;
		config_value?: string;
		description?: string;
	},
) {
	return request({
		url: `system/configs/${configId}`,
		method: "put",
		data,
	});
}

/**
 * 删除系统配置
 */
export function deleteSystemConfig(configId: number) {
	return request({
		url: `system/configs/${configId}`,
		method: "delete",
	});
}

/**
 * 获取系统配置字典
 */
export function getSystemConfigDict() {
	return request({
		url: "system/configs/as-dict",
		method: "get",
	});
}

/**
 * 批量更新系统配置
 */
export function bulkUpdateSystemConfig(data: {
	configs: Array<{
		config_key: string;
		config_value?: string;
		description?: string;
	}>;
}) {
	return request({
		url: "system/configs/bulk-upsert",
		method: "post",
		data,
	});
}

export function getConfig_value(config_key: string) {
	return request({
		url: `system/configs/by-key/${config_key}`,
		method: "get",
	});
}
