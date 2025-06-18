/**
 * 数据集模块工具函数
 */
import { DatasetType } from "@/types/dataset";

/**
 * 格式化时间戳为可读的日期时间字符串
 * @param timestamp 时间戳（秒或毫秒）
 * @returns 格式化后的日期时间字符串
 */
export function formatTimestamp(timestamp: string | number | undefined): string {
	if (!timestamp) return "-";

	// 确保timestamp是数字
	const ts = typeof timestamp === "string" ? parseInt(timestamp) : timestamp;

	// 如果时间戳是秒级的，则转换为毫秒
	const date = new Date(ts < 10000000000 ? ts * 1000 : ts);

	return date.toLocaleString("zh-CN", {
		year: "numeric",
		month: "2-digit",
		day: "2-digit",
		hour: "2-digit",
		minute: "2-digit",
		second: "2-digit",
	});
}

/**
 * 获取数据集类型的标签样式
 * @param type 数据集类型
 * @returns 对应的Element Plus标签类型
 */
export function getDatasetTypeTag(type: DatasetType | string | undefined): string {
	if (!type) return "";

	const typeMap: Record<string, string> = {
		[DatasetType.SFT]: "success",
		[DatasetType.DPO]: "warning",
		[DatasetType.CONVERSATION]: "info",
	};

	return typeMap[type] || "primary";
}

/**
 * 获取数据集类型的显示文本
 * @param type 数据集类型
 * @returns 数据集类型的中文描述
 */
export function getDatasetTypeLabel(type: DatasetType | string | undefined): string {
	if (!type) return "";

	const labelMap: Record<string, string> = {
		[DatasetType.SFT]: "SFT(指令微调)",
		[DatasetType.DPO]: "DPO(直接偏好优化)",
		[DatasetType.CONVERSATION]: "对话",
	};

	return labelMap[type] || String(type);
}

/**
 * 获取统计数据项的标签
 * @param key 统计数据的键名
 * @returns 统计数据的中文描述
 */
export function getStatLabel(key: any): string {
	const labelMap: Record<string, string> = {
		entryCount: "总条目数",
		tokenCount: "总Token数",
		avgTokensPerEntry: "平均Token数",
		instructionTokens: "指令Token数",
		outputTokens: "输出Token数",
		promptTokens: "提示Token数",
		chosenTokens: "优选回复Token数",
		rejectedTokens: "拒绝回复Token数",
		messageCount: "消息数量",
	};

	return labelMap[key] || key;
}

/**
 * 截断文本
 * @param text 需要截断的文本
 * @param maxLength 最大长度
 * @returns 截断后的文本
 */
export function truncateText(text: string | null | undefined, maxLength = 100): string {
	if (!text) return "";

	if (text.length <= maxLength) {
		return text;
	}

	return `${text.substring(0, maxLength)}...`;
}

/**
 * 获取文件类型图标
 * @param filename 文件名
 * @returns 对应的Element Plus图标名称
 */
export function getFileTypeIcon(filename: string): string {
	const extension = filename.split(".").pop()?.toLowerCase();

	const iconMap: Record<string, string> = {
		json: "document",
		csv: "tickets",
		txt: "document",
		xlsx: "grid",
		xls: "grid",
	};

	return iconMap[extension || ""] || "document";
}

/**
 * 计算文件大小的可读字符串
 * @param size 文件大小（字节）
 * @returns 格式化后的文件大小字符串
 */
export function formatFileSize(size: number): string {
	if (size < 1024) {
		return `${size} B`;
	} else if (size < 1024 * 1024) {
		return `${(size / 1024).toFixed(2)} KB`;
	} else if (size < 1024 * 1024 * 1024) {
		return `${(size / (1024 * 1024)).toFixed(2)} MB`;
	} else {
		return `${(size / (1024 * 1024 * 1024)).toFixed(2)} GB`;
	}
}
