<template>
	<div class="conversation-data-table">
		<el-table
			v-loading="loading"
			:data="dataList"
			border
			fit
			highlight-current-row
			element-loading-text="加载中..."
			empty-text="暂无数据"
		>
			<el-table-column label="ID" prop="id" width="80" align="center" fixed />
			<el-table-column label="对话ID" prop="conversation_id" width="100" align="center" />
			<el-table-column label="标题" min-width="200">
				<template #default="scope">
					<el-tooltip effect="dark" :content="scope.row.title || '无标题'" placement="top-start" :hide-after="0">
						<div class="truncate-text">{{ scope.row.title || "无标题" }}</div>
					</el-tooltip>
				</template>
			</el-table-column>

			<el-table-column label="消息预览" min-width="280">
				<template #default="scope">
					<el-tooltip
						v-if="getMessagePreview(scope.row)"
						effect="dark"
						:content="getMessagePreview(scope.row)"
						placement="top-start"
						:hide-after="0"
					>
						<div class="truncate-text">{{ getMessagePreview(scope.row) }}</div>
					</el-tooltip>
					<span v-else class="no-data-text">无消息预览</span>
				</template>
			</el-table-column>

			<el-table-column label="消息数量" prop="messageCount" width="100" align="center">
				<template #default="scope">
					<el-tag type="info" size="small" effect="plain">
						{{ scope.row.messageCount || (scope.row.messages ? scope.row.messages.length : 0) }}
					</el-tag>
				</template>
			</el-table-column>

			<el-table-column label="创建时间" width="160" align="center">
				<template #default="scope">
					<span>{{ formatTimestamp(scope.row.createdAt || scope.row.created_at) }}</span>
				</template>
			</el-table-column>

			<el-table-column label="操作" width="200" align="center" fixed="right">
				<template #default="scope">
					<el-button type="primary" link @click="handleView(scope.row)">
						<el-icon><View /></el-icon>
						查看
					</el-button>
					<el-button type="primary" link @click="handleEdit(scope.row)">
						<el-icon><Edit /></el-icon>
						编辑
					</el-button>
					<el-button type="danger" link @click="handleDelete(scope.row)">
						<el-icon><Delete /></el-icon>
						删除
					</el-button>
				</template>
			</el-table-column>
		</el-table>
	</div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from "vue";
import { View, Edit, Delete } from "@element-plus/icons-vue";
import { formatTimestamp, truncateText } from "@/utils/dataset";
import { ConversationEntry } from "@/types/dataset";

/**
 * 会话数据表格组件
 * @description 用于展示会话类型的数据集条目
 */

// 定义props
defineProps<{
	loading: boolean;
	dataList: ConversationEntry[];
}>();

// 定义emits
const emit = defineEmits<{
	(e: "view", entry: ConversationEntry): void;
	(e: "edit", entry: ConversationEntry): void;
	(e: "delete", entry: ConversationEntry): void;
}>();

/**
 * 获取消息预览文本
 */
const getMessagePreview = (entry: ConversationEntry): string => {
	if (!entry.messages || entry.messages.length === 0) {
		return "";
	}

	// 找到第一条用户消息作为预览
	const userMessage = entry.messages.find((msg) => msg.role === "user");
	if (userMessage && userMessage.content) {
		return truncateText(userMessage.content, 150);
	}

	// 如果没有用户消息，就显示第一条消息
	return truncateText(entry.messages[0].content || "", 150);
};

/**
 * 处理查看按钮点击
 */
const handleView = (entry: ConversationEntry) => {
	emit("view", entry);
};

/**
 * 处理编辑按钮点击
 */
const handleEdit = (entry: ConversationEntry) => {
	emit("edit", entry);
};

/**
 * 处理删除按钮点击
 */
const handleDelete = (entry: ConversationEntry) => {
	emit("delete", entry);
};
</script>

<style lang="scss" scoped>
.conversation-data-table {
	.truncate-text {
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		max-width: 100%;
	}

	.no-data-text {
		color: var(--el-text-color-secondary);
		font-style: italic;
	}
}
</style>
