<template>
	<div class="dpo-data-table">
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
			<el-table-column label="提示" min-width="200">
				<template #default="scope">
					<el-tooltip
						effect="dark"
						:content="scope.row.query || scope.row.prompt"
						placement="top-start"
						:hide-after="0"
					>
						<div class="truncate-text">{{ scope.row.query || scope.row.prompt }}</div>
					</el-tooltip>
				</template>
			</el-table-column>

			<el-table-column label="优选回复" min-width="200">
				<template #default="scope">
					<el-tooltip
						effect="dark"
						:content="scope.row.chosen_response || scope.row.chosen"
						placement="top-start"
						:hide-after="0"
					>
						<div class="truncate-text">{{ scope.row.chosen_response || scope.row.chosen }}</div>
					</el-tooltip>
				</template>
			</el-table-column>

			<el-table-column label="拒绝回复" min-width="200">
				<template #default="scope">
					<el-tooltip
						effect="dark"
						:content="scope.row.rejected_response || scope.row.rejected"
						placement="top-start"
						:hide-after="0"
					>
						<div class="truncate-text">{{ scope.row.rejected_response || scope.row.rejected }}</div>
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
import { DpoEntry } from "@/types/dataset";

/**
 * DPO数据表格组件
 * @description 用于展示DPO类型的数据集条目
 */

// 定义props
defineProps<{
	loading: boolean;
	dataList: DpoEntry[];
}>();

// 定义emits
const emit = defineEmits<{
	(e: "edit", entry: DpoEntry): void;
	(e: "delete", entry: DpoEntry): void;
}>();

/**
 * 处理编辑按钮点击
 */
const handleEdit = (entry: DpoEntry) => {
	emit("edit", entry);
};

/**
 * 处理删除按钮点击
 */
const handleDelete = (entry: DpoEntry) => {
	emit("delete", entry);
};
</script>

<style lang="scss" scoped>
.dpo-data-table {
	.truncate-text {
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		max-width: 100%;
	}
}
</style>
