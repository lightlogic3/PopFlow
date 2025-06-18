<template>
	<div class="dataset-base-info">
		<el-card class="dataset-base-info-card">
			<template #header>
				<div class="card-header">
					<span>基本信息</span>
					<el-button type="primary" link @click="handleEdit" v-if="editable">
						<el-icon><Edit /></el-icon>
						编辑
					</el-button>
				</div>
			</template>
			<div class="dataset-info-content">
				<el-descriptions :column="2" border size="large">
					<el-descriptions-item label="ID">{{ dataset.id }}</el-descriptions-item>
					<el-descriptions-item label="名称">{{ dataset.name }}</el-descriptions-item>
					<el-descriptions-item label="类型">
						<el-tag :type="getDatasetTypeTag(dataset.type) as any">
							{{ getDatasetTypeLabel(dataset.type) }}
						</el-tag>
					</el-descriptions-item>
					<el-descriptions-item label="数据条目数">{{ dataset.entryCount || 0 }}</el-descriptions-item>
					<el-descriptions-item label="创建时间">{{ formatTimestamp(dataset.createdAt) }}</el-descriptions-item>
					<el-descriptions-item label="更新时间">{{ formatTimestamp(dataset.updatedAt) }}</el-descriptions-item>
					<el-descriptions-item label="标签" :span="2">
						<div v-if="dataset.tags" class="dataset-tags">
							<el-tag v-for="tag in dataset.tags.split(',')" :key="tag" size="small" class="dataset-tag">
								{{ tag.trim() }}
							</el-tag>
						</div>
						<span v-else>无标签</span>
					</el-descriptions-item>
					<el-descriptions-item label="描述" :span="2">
						<div class="dataset-description">
							{{ dataset.description || "暂无描述" }}
						</div>
					</el-descriptions-item>
				</el-descriptions>
			</div>
		</el-card>

		<!-- 编辑对话框 -->
		<el-dialog title="编辑数据集信息" v-model="dialogVisible" width="500px" destroy-on-close>
			<el-form ref="formRef" :model="form" :rules="rules" label-width="80px" @submit.prevent>
				<el-form-item label="名称" prop="name">
					<el-input v-model="form.name" placeholder="请输入数据集名称" maxlength="50" show-word-limit />
				</el-form-item>
				<el-form-item label="描述" prop="description">
					<el-input
						v-model="form.description"
						type="textarea"
						:rows="4"
						placeholder="请输入数据集描述"
						maxlength="200"
						show-word-limit
					/>
				</el-form-item>
				<el-form-item label="标签" prop="tags">
					<el-input v-model="form.tags" placeholder="多个标签请用逗号分隔" maxlength="100" show-word-limit />
				</el-form-item>
			</el-form>
			<template #footer>
				<span class="dialog-footer">
					<el-button @click="dialogVisible = false">取消</el-button>
					<el-button type="primary" @click="submitForm">确认</el-button>
				</span>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, defineProps, defineEmits } from "vue";
import { ElMessage } from "element-plus";
import { Edit } from "@element-plus/icons-vue";
import type { FormInstance, FormRules } from "element-plus";
import { updateDataset } from "@/api/datasets";
import { formatTimestamp, getDatasetTypeTag, getDatasetTypeLabel } from "@/utils/dataset";
import { Dataset } from "@/types/dataset";

/**
 * 数据集基本信息组件
 * @description 显示数据集基本信息，并支持编辑
 */

// 定义props
const props = defineProps<{
	dataset: Dataset;
	editable?: boolean;
}>();

// 定义emits
const emit = defineEmits<{
	(e: "update", dataset: Dataset): void;
}>();

// 响应式状态
const dialogVisible = ref(false);
const formRef = ref<FormInstance>();
const form = reactive({
	name: "",
	description: "",
	tags: "",
});

// 表单验证规则
const rules = reactive<FormRules>({
	name: [
		{ required: true, message: "请输入数据集名称", trigger: "blur" },
		{ min: 2, max: 50, message: "长度在 2 到 50 个字符", trigger: "blur" },
	],
});

/**
 * 编辑按钮处理函数
 */
const handleEdit = () => {
	form.name = props.dataset.name;
	form.description = props.dataset.description || "";
	form.tags = props.dataset.tags || "";
	dialogVisible.value = true;
};

/**
 * 提交表单
 */
const submitForm = async () => {
	if (!formRef.value) return;

	try {
		await formRef.value.validate(async (valid) => {
			if (valid) {
				try {
					const response = await updateDataset(props.dataset.id, {
						name: form.name,
						description: form.description,
						tags: form.tags,
					});

					emit("update", response);
					dialogVisible.value = false;

					ElMessage({
						type: "success",
						message: "更新数据集信息成功",
					});
				} catch (error) {
					if (error instanceof Error) {
						ElMessage.error(`更新失败: ${error.message}`);
					} else {
						ElMessage.error("更新失败");
					}
				}
			}
		});
	} catch (error) {
		console.error("表单验证错误:", error);
	}
};
</script>

<style lang="scss" scoped>
.dataset-base-info {
	margin-bottom: 20px;

	.dataset-base-info-card {
		.card-header {
			display: flex;
			justify-content: space-between;
			align-items: center;
		}

		.dataset-info-content {
			.dataset-tags {
				display: flex;
				flex-wrap: wrap;
				gap: 5px;

				.dataset-tag {
					margin-right: 5px;
				}
			}

			.dataset-description {
				white-space: pre-line;
				line-height: 1.5;
			}
		}
	}
}
</style>
