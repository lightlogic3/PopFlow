<template>
	<div v-if="!hideTitle" class="form-section" :class="sectionClass">
		<h3 v-if="section.title" class="section-title">{{ section.title }}</h3>

		<!-- 默认标签位置：top -->
		<el-form
			v-if="!labelPosition || labelPosition === 'top'"
			:model="localValue"
			label-position="top"
			:disabled="readOnly"
		>
			<div
				v-for="field in section.fields"
				:key="field.name"
				class="form-field"
				:class="fieldClass"
				:data-field="field.name"
			>
				<form-field
					:field="field"
					:model-value="getFieldValue(field.name)"
					:validation-rules="getValidationRules(field.name)"
					:validation-error="getValidationError(field.name)"
					:read-only="readOnly"
					@update:model-value="updateField(field.name, $event)"
				/>
			</div>
		</el-form>

		<!-- 标签位置：left -->
		<el-form v-else-if="labelPosition === 'left'" :model="localValue" label-position="left" :disabled="readOnly">
			<div
				v-for="field in section.fields"
				:key="field.name"
				class="form-field"
				:class="fieldClass"
				:data-field="field.name"
			>
				<form-field
					:field="field"
					:model-value="getFieldValue(field.name)"
					:validation-rules="getValidationRules(field.name)"
					:validation-error="getValidationError(field.name)"
					:read-only="readOnly"
					@update:model-value="updateField(field.name, $event)"
				/>
			</div>
		</el-form>

		<!-- 标签位置：right -->
		<el-form v-else-if="labelPosition === 'right'" :model="localValue" label-position="right" :disabled="readOnly">
			<div
				v-for="field in section.fields"
				:key="field.name"
				class="form-field"
				:class="fieldClass"
				:data-field="field.name"
			>
				<form-field
					:field="field"
					:model-value="getFieldValue(field.name)"
					:validation-rules="getValidationRules(field.name)"
					:validation-error="getValidationError(field.name)"
					:read-only="readOnly"
					@update:model-value="updateField(field.name, $event)"
				/>
			</div>
		</el-form>
	</div>

	<!-- 当hideTitle为true时，直接显示字段内容，不显示分组框 -->
	<div v-else>
		<!-- 默认标签位置：top -->
		<el-form
			v-if="!labelPosition || labelPosition === 'top'"
			:model="localValue"
			label-position="top"
			:disabled="readOnly"
		>
			<div
				v-for="field in section.fields"
				:key="field.name"
				class="form-field"
				:class="fieldClass"
				:data-field="field.name"
			>
				<form-field
					:field="field"
					:model-value="getFieldValue(field.name)"
					:validation-rules="getValidationRules(field.name)"
					:validation-error="getValidationError(field.name)"
					:read-only="readOnly"
					@update:model-value="updateField(field.name, $event)"
				/>
			</div>
		</el-form>

		<!-- 标签位置：left -->
		<el-form v-else-if="labelPosition === 'left'" :model="localValue" label-position="left" :disabled="readOnly">
			<div
				v-for="field in section.fields"
				:key="field.name"
				class="form-field"
				:class="fieldClass"
				:data-field="field.name"
			>
				<form-field
					:field="field"
					:model-value="getFieldValue(field.name)"
					:validation-rules="getValidationRules(field.name)"
					:validation-error="getValidationError(field.name)"
					:read-only="readOnly"
					@update:model-value="updateField(field.name, $event)"
				/>
			</div>
		</el-form>

		<!-- 标签位置：right -->
		<el-form v-else-if="labelPosition === 'right'" :model="localValue" label-position="right" :disabled="readOnly">
			<div
				v-for="field in section.fields"
				:key="field.name"
				class="form-field"
				:class="fieldClass"
				:data-field="field.name"
			>
				<form-field
					:field="field"
					:model-value="getFieldValue(field.name)"
					:validation-rules="getValidationRules(field.name)"
					:validation-error="getValidationError(field.name)"
					:read-only="readOnly"
					@update:model-value="updateField(field.name, $event)"
				/>
			</div>
		</el-form>
	</div>
</template>

<script setup lang="ts">
import { watch, ref } from "vue";
import FormField from "./FormField.vue";

// 定义属性
const props = defineProps({
	section: {
		type: Object,
		required: true,
	},
	value: {
		type: Object,
		default: () => ({}),
	},
	validationSchema: {
		type: Object,
		default: () => ({}),
	},
	validationErrors: {
		type: Object,
		default: () => ({}),
	},
	sectionClass: {
		type: String,
		default: "",
	},
	fieldClass: {
		type: String,
		default: "",
	},
	readOnly: {
		type: Boolean,
		default: false,
	},
	hideTitle: {
		type: Boolean,
		default: false,
	},
	labelPosition: {
		type: String,
		default: "top",
	},
});

// 定义事件
const emit = defineEmits(["update:value"]);

// 本地表单数据
const localValue = ref({ ...props.value });

// 获取字段值
function getFieldValue(fieldName) {
	if (fieldName.includes(".")) {
		const parts = fieldName.split(".");
		let value = localValue.value;
		for (const part of parts) {
			if (value === undefined || value === null) {
				return undefined;
			}
			value = value[part];
		}
		return value;
	}
	return localValue.value[fieldName];
}

// 获取验证规则
function getValidationRules(fieldName) {
	const rules = props.validationSchema[fieldName] || [];
	console.log(`FormSection 获取字段 ${fieldName} 的验证规则:`, rules, "完整验证Schema:", props.validationSchema);
	return rules;
}

// 获取验证错误
function getValidationError(fieldName) {
	return props.validationErrors[fieldName];
}

// 更新字段值
function updateField(fieldName, value) {
	// 使用路径更新嵌套对象
	if (fieldName.includes(".")) {
		const parts = fieldName.split(".");
		let current = localValue.value;

		// 确保路径上的对象存在
		for (let i = 0; i < parts.length - 1; i++) {
			if (!current[parts[i]]) {
				current[parts[i]] = {};
			}
			current = current[parts[i]];
		}

		// 设置值
		current[parts[parts.length - 1]] = value;
	} else {
		localValue.value[fieldName] = value;
	}

	emit("update:value", fieldName, value);
}

// 监听值变化
watch(
	() => props.value,
	(newValue) => {
		localValue.value = { ...newValue };
	},
	{ deep: true },
);
</script>

<style scoped lang="scss">
.form-section {
	margin-bottom: 30px;
	padding: 20px;
	border-radius: 8px;
	background-color: rgba(255, 255, 255, 0.05);
	box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);

	.section-title {
		margin-top: 0;
		margin-bottom: 20px;
		font-size: 18px;
		font-weight: 500;
		color: #409eff;
		padding-bottom: 10px;
		border-bottom: 1px solid rgba(64, 158, 255, 0.2);
	}

	.form-field {
		margin-bottom: 20px;

		&:last-child {
			margin-bottom: 0;
		}
	}
}

:deep(.el-form-item__label) {
	font-weight: 500;
}
</style>
