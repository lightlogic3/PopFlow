<template>
	<div class="sft-data-table">
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
			<el-table-column label="指令" min-width="200">
				<template #default="scope">
					<el-tooltip effect="dark" :content="scope.row.instruction" placement="top-start" :hide-after="0">
						<div class="truncate-text">{{ scope.row.instruction }}</div>
					</el-tooltip>
				</template>
			</el-table-column>

			<el-table-column label="输入" min-width="180">
				<template #default="scope">
					<el-tooltip
						v-if="scope.row.input"
						effect="dark"
						:content="scope.row.input"
						placement="top-start"
						:hide-after="0"
					>
						<div class="truncate-text">{{ scope.row.input }}</div>
					</el-tooltip>
					<span v-else class="no-data-text">无输入</span>
				</template>
			</el-table-column>

			<el-table-column label="输出" min-width="200">
				<template #default="scope">
					<el-tooltip effect="dark" :content="scope.row.output" placement="top-start" :hide-after="0">
						<div class="truncate-text">{{ scope.row.output }}</div>
					</el-tooltip>
				</template>
			</el-table-column>

			<el-table-column label="创建时间" width="160" align="center">
				<template #default="scope">
					<span>{{ formatTimestamp(scope.row.created_at) }}</span>
				</template>
			</el-table-column>

			<el-table-column label="操作" width="160" align="center" fixed="right">
				<template #default="scope">
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
import { Edit, Delete } from "@element-plus/icons-vue";
import { formatTimestamp } from "@/utils/dataset";
import { SftEntry } from "@/types/dataset";

/**
 * SFT数据表格组件
 * @description 用于展示SFT类型的数据集条目
 */

// 定义props
defineProps<{
	loading: boolean;
	dataList: SftEntry[];
}>();

// 定义emits
const emit = defineEmits<{
	(e: "edit", entry: SftEntry): void;
	(e: "delete", entry: SftEntry): void;
}>();

/**
 * 处理编辑按钮点击
 */
const handleEdit = (entry: SftEntry) => {
	emit("edit", entry);
};

/**
 * 处理删除按钮点击
 */
const handleDelete = (entry: SftEntry) => {
	emit("delete", entry);
};
</script>

<style lang="scss" scoped>
.sft-data-table {
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
