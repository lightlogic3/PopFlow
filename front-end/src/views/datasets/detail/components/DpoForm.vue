<template>
	<div class="dpo-form">
		<el-form ref="formRef" :model="form" :rules="rules" label-width="100px" @submit.prevent>
			<el-form-item label="提示词" prop="prompt">
				<el-input
					v-model="form.prompt"
					type="textarea"
					:rows="3"
					placeholder="请输入提示词内容"
					maxlength="5000"
					show-word-limit
				/>
				<template #tip>
					<div class="form-tip">输入用户的问题或指令，作为模型的输入</div>
				</template>
			</el-form-item>

			<el-form-item label="首选回答" prop="chosen">
				<el-input
					v-model="form.chosen"
					type="textarea"
					:rows="5"
					placeholder="请输入更好的、首选的回答"
					maxlength="15000"
					show-word-limit
				/>
				<template #tip>
					<div class="form-tip">输入高质量的回答，作为模型学习的积极示例</div>
				</template>
			</el-form-item>

			<el-form-item label="拒绝回答" prop="rejected">
				<el-input
					v-model="form.rejected"
					type="textarea"
					:rows="5"
					placeholder="请输入质量较差的、被拒绝的回答"
					maxlength="15000"
					show-word-limit
				/>
				<template #tip>
					<div class="form-tip">输入质量较差的回答，作为模型学习的消极示例</div>
				</template>
			</el-form-item>

			<el-form-item v-if="showSystemPrompt" label="系统提示" prop="systemPrompt">
				<el-input
					v-model="form.systemPrompt"
					type="textarea"
					:rows="3"
					placeholder="请输入系统提示内容（可选）"
					maxlength="2000"
					show-word-limit
				/>
				<template #tip>
					<div class="form-tip">可选字段，设置模型的行为指南或角色定位</div>
				</template>
			</el-form-item>

			<el-form-item>
				<el-switch v-model="showSystemPrompt" class="block" active-text="添加系统提示" />
				<el-switch v-model="showMetadata" class="block ml-20" active-text="添加元数据" />
			</el-form-item>

			<el-form-item v-if="showMetadata" label="元数据" prop="metadata">
				<el-input
					v-model="form.metadata"
					type="textarea"
					:rows="3"
					placeholder="请输入JSON格式的元数据（可选）"
					maxlength="2000"
					show-word-limit
				/>
				<template #tip>
					<div class="form-tip">可选字段，以JSON格式添加额外信息，如数据类别、来源等</div>
				</template>
			</el-form-item>
		</el-form>
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, defineProps, defineExpose } from "vue";
import { ElMessage } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";

/**
 * DPO表单数据类型定义
 */
interface DpoFormData {
	id?: string | number;
	prompt: string;
	chosen: string;
	rejected: string;
	systemPrompt?: string;
	metadata?: string;
}

/**
 * DPO数据表单组件
 * @description 用于添加或编辑DPO类型的数据集条目，用于直接偏好优化训练
 */

// 定义props
const props = defineProps<{
	formData: DpoFormData;
	editMode: boolean;
}>();

// 表单引用
const formRef = ref<FormInstance>();

// 是否显示系统提示和元数据
const showSystemPrompt = ref(!!props.formData.systemPrompt);
const showMetadata = ref(!!props.formData.metadata);

// 表单数据
const form = reactive<DpoFormData>({
	id: props.formData.id,
	prompt: props.formData.prompt || "",
	chosen: props.formData.chosen || "",
	rejected: props.formData.rejected || "",
	systemPrompt: props.formData.systemPrompt || "",
	metadata: props.formData.metadata || "",
});

// 表单验证规则
const rules = reactive<FormRules>({
	prompt: [
		{ required: true, message: "请输入提示词内容", trigger: "blur" },
		{ min: 1, message: "提示词不能为空", trigger: "blur" },
	],
	chosen: [
		{ required: true, message: "请输入首选回答", trigger: "blur" },
		{ min: 1, message: "首选回答不能为空", trigger: "blur" },
	],
	rejected: [
		{ required: true, message: "请输入拒绝回答", trigger: "blur" },
		{ min: 1, message: "拒绝回答不能为空", trigger: "blur" },
	],
	metadata: [
		{
			validator: (rule, value, callback) => {
				if (!value || value.trim() === "") {
					callback();
					return;
				}
				try {
					JSON.parse(value);
					callback();
				} catch (error) {
					callback(new Error("请输入有效的JSON格式"));
				}
			},
			trigger: "blur",
		},
	],
});

/**
 * 表单验证
 */
const validate = async (): Promise<boolean> => {
	if (!formRef.value) return false;

	try {
		await formRef.value.validate();
		if (!form.prompt.trim()) {
			ElMessage.error("提示词不能为空");
			return false;
		}
		if (!form.chosen.trim()) {
			ElMessage.error("首选回答不能为空");
			return false;
		}
		if (!form.rejected.trim()) {
			ElMessage.error("拒绝回答不能为空");
			return false;
		}
		return true;
	} catch (error) {
		return false;
	}
};

/**
 * 获取表单数据
 */
const getFormData = (): DpoFormData => {
	return {
		id: form.id,
		prompt: form.prompt.trim(),
		chosen: form.chosen.trim(),
		rejected: form.rejected.trim(),
		systemPrompt: showSystemPrompt.value && form.systemPrompt.trim() !== "" ? form.systemPrompt.trim() : undefined,
		metadata: showMetadata.value && form.metadata.trim() !== "" ? form.metadata.trim() : undefined,
	};
};

// 暴露方法
defineExpose({
	validate,
	getFormData,
});
</script>

<style lang="scss" scoped>
.dpo-form {
	.form-tip {
		color: var(--el-text-color-secondary);
		font-size: 12px;
		line-height: 1.5;
		margin-top: 2px;
	}

	.ml-20 {
		margin-left: 20px;
	}
}
</style>
