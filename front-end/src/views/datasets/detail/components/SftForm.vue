<template>
	<div class="sft-form">
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

			<el-form-item label="回复内容" prop="completion">
				<el-input
					v-model="form.completion"
					type="textarea"
					:rows="5"
					placeholder="请输入高质量回复内容"
					maxlength="15000"
					show-word-limit
				/>
				<template #tip>
					<div class="form-tip">输入与提示词相匹配的高质量回复，用于训练模型生成类似的回复</div>
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
 * SFT表单数据类型定义
 */
interface SftFormData {
	id?: string | number;
	prompt: string;
	completion: string;
	systemPrompt?: string;
	metadata?: string;
}

/**
 * SFT数据表单组件
 * @description 用于添加或编辑SFT类型的数据集条目，用于监督微调训练
 */

// 定义props
const props = defineProps<{
	formData: SftFormData;
	editMode: boolean;
}>();

// 表单引用
const formRef = ref<FormInstance>();

// 是否显示系统提示和元数据
const showSystemPrompt = ref(!!props.formData.systemPrompt);
const showMetadata = ref(!!props.formData.metadata);

// 表单数据
const form = reactive<SftFormData>({
	id: props.formData.id,
	prompt: props.formData.prompt || "",
	completion: props.formData.completion || "",
	systemPrompt: props.formData.systemPrompt || "",
	metadata: props.formData.metadata || "",
});

// 表单验证规则
const rules = reactive<FormRules>({
	prompt: [
		{ required: true, message: "请输入提示词内容", trigger: "blur" },
		{ min: 1, message: "提示词不能为空", trigger: "blur" },
	],
	completion: [
		{ required: true, message: "请输入回复内容", trigger: "blur" },
		{ min: 1, message: "回复内容不能为空", trigger: "blur" },
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
		if (!form.completion.trim()) {
			ElMessage.error("回复内容不能为空");
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
const getFormData = (): SftFormData => {
	return {
		id: form.id,
		prompt: form.prompt.trim(),
		completion: form.completion.trim(),
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
.sft-form {
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
