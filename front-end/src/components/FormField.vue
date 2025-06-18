<template>
	<el-form-item :label="field.label" :prop="field.name" :required="field.required" :rules="validationRules">
		<!-- 文本输入框 -->
		<el-input
			v-if="field.type === 'text'"
			v-model="fieldValue"
			:placeholder="field.placeholder"
			:maxlength="field.maxLength"
			:disabled="field.disabled || readOnly"
			:autofocus="field.autofocus"
			:class="field.className"
			clearable
			@change="updateValue"
		/>

		<!-- 数字输入框 -->
		<el-input-number
			v-else-if="field.type === 'number'"
			v-model="fieldValue"
			:min="field.min"
			:max="field.max"
			:step="field.step"
			:disabled="field.disabled || readOnly"
			:placeholder="field.placeholder"
			:class="field.className"
			@change="updateValue"
		/>

		<!-- 多行文本框 -->
		<el-input
			v-else-if="field.type === 'textarea'"
			v-model="fieldValue"
			type="textarea"
			:rows="field.rows || 3"
			:placeholder="field.placeholder"
			:maxlength="field.maxLength"
			:disabled="field.disabled || readOnly"
			:autofocus="field.autofocus"
			:class="field.className"
			@change="updateValue"
		/>

		<!-- 下拉选择框 -->
		<el-select
			v-else-if="field.type === 'select'"
			v-model="fieldValue"
			:placeholder="field.placeholder"
			:disabled="field.disabled || readOnly"
			:multiple="field.multiple"
			:class="field.className"
			clearable
			@change="updateValue"
		>
			<el-option v-for="option in field.options" :key="option.value" :label="option.label" :value="option.value" />
		</el-select>

		<!-- 复选框 -->
		<template v-else-if="field.type === 'checkbox'">
			<!-- 多选项复选框 -->
			<el-checkbox-group
				v-if="field.options && field.options.length > 0"
				v-model="fieldValue"
				:disabled="field.disabled || readOnly"
				:class="field.className"
				@change="updateValue"
			>
				<el-checkbox v-for="option in field.options" :key="option.value" :label="option.value">
					{{ option.label }}
				</el-checkbox>
			</el-checkbox-group>

			<!-- 单选项复选框 -->
			<el-checkbox
				v-else
				v-model="fieldValue"
				:disabled="field.disabled || readOnly"
				:class="field.className"
				@change="updateValue"
			>
				{{ field.placeholder || field.label }}
			</el-checkbox>
		</template>

		<!-- 单选框组 -->
		<el-radio-group
			v-else-if="field.type === 'radio'"
			v-model="fieldValue"
			:disabled="field.disabled || readOnly"
			:class="field.className"
			@change="updateValue"
		>
			<el-radio v-for="option in field.options" :key="option.value" :label="option.value">
				{{ option.label }}
			</el-radio>
		</el-radio-group>

		<!-- 开关 -->
		<el-switch
			v-else-if="field.type === 'switch'"
			v-model="fieldValue"
			:disabled="field.disabled || readOnly"
			:active-text="field.activeText"
			:inactive-text="field.inactiveText"
			:class="field.className"
			@change="updateValue"
		/>

		<!-- 滑块 -->
		<el-slider
			v-else-if="field.type === 'slider'"
			v-model="fieldValue"
			:min="field.min"
			:max="field.max"
			:step="field.step"
			:disabled="field.disabled || readOnly"
			:show-stops="field.showStops"
			:show-input="true"
			:class="field.className"
			@change="updateValue"
		/>

		<!-- 日期选择器 -->
		<el-date-picker
			v-else-if="field.type === 'date-picker'"
			v-model="fieldValue"
			:type="field.dateType || 'date'"
			:placeholder="field.placeholder"
			:disabled="field.disabled || readOnly"
			:format="field.format"
			:class="field.className"
			@change="updateValue"
		/>

		<!-- 时间选择器 -->
		<el-time-picker
			v-else-if="field.type === 'time-picker'"
			v-model="fieldValue"
			:placeholder="field.placeholder"
			:disabled="field.disabled || readOnly"
			:format="field.format"
			:class="field.className"
			@change="updateValue"
		/>

		<!-- 颜色选择器 -->
		<el-color-picker
			v-else-if="field.type === 'color'"
			v-model="fieldValue"
			:disabled="field.disabled || readOnly"
			:show-alpha="true"
			:class="field.className"
			@change="updateValue"
		/>

		<!-- 动态标签 -->
		<template v-else-if="field.type === 'dynamic-tags'">
			<div class="dynamic-tags-container">
				<el-tag
					v-for="tag in fieldValue"
					:key="tag"
					closable
					:disable-transitions="false"
					:class="field.className"
					@close="removeTag(tag)"
				>
					{{ tag }}
				</el-tag>
				<el-input
					v-model="tagInputValue"
					:disabled="field.disabled || readOnly"
					:placeholder="field.placeholder || '输入标签后回车添加'"
					size="small"
					@keyup.enter="addTag"
				/>
			</div>
		</template>

		<!-- 默认文本显示 -->
		<div v-else>
			{{ fieldValue }}
		</div>

		<!-- 字段帮助信息 -->
		<template v-if="field.help" #default>
			<div class="field-help">{{ field.help }}</div>
		</template>

		<!-- 验证错误信息 -->
		<div v-if="validationError" class="form-field-error">{{ validationError }}</div>
	</el-form-item>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";

// 定义属性
const props = defineProps({
	field: {
		type: Object,
		required: true,
	},
	modelValue: {
		type: [String, Number, Boolean, Array, Object],
		default: "",
	},
	validationRules: {
		type: Array,
		default: () => [],
	},
	validationError: {
		type: String,
		default: "",
	},
	readOnly: {
		type: Boolean,
		default: false,
	},
});

// 输出验证规则用于调试
console.log(`字段 ${props.field.name} 的验证规则:`, props.validationRules);

// 定义事件
const emit = defineEmits(["update:modelValue"]);

// 本地值
const fieldValue = ref(getInitialValue());
const tagInputValue = ref("");

// 获取初始值
function getInitialValue() {
	if (props.modelValue !== null && props.modelValue !== undefined) {
		return props.modelValue;
	}

	// 提供默认值
	if (props.field.default !== undefined) {
		return props.field.default;
	}

	// 根据字段类型提供默认值
	switch (props.field.type) {
		case "text":
		case "textarea":
			return "";
		case "number":
			return 0;
		case "select":
			return props.field.multiple ? [] : "";
		case "checkbox":
			// 如果有选项数组，则初始化为空数组，否则为布尔值false
			return props.field.options && props.field.options.length > 0 ? [] : false;
		case "switch":
			return false;
		case "radio":
			return "";
		case "slider":
			return props.field.min || 0;
		case "date-picker":
		case "time-picker":
			return null;
		case "dynamic-tags":
			return [];
		case "color":
			return "#409EFF";
		default:
			return null;
	}
}

// 更新值
function updateValue() {
	emit("update:modelValue", fieldValue.value);
}

// 添加标签
function addTag() {
	if (tagInputValue.value.trim()) {
		if (!Array.isArray(fieldValue.value)) {
			fieldValue.value = [];
		}
		fieldValue.value.push(tagInputValue.value.trim());
		tagInputValue.value = "";
		updateValue();
	}
}

// 删除标签
function removeTag(tag) {
	if (Array.isArray(fieldValue.value)) {
		fieldValue.value = fieldValue.value.filter((t) => t !== tag);
		updateValue();
	}
}

// 监听值变化
watch(
	() => props.modelValue,
	(newValue) => {
		fieldValue.value = newValue !== null && newValue !== undefined ? newValue : getInitialValue();
	},
	{ deep: true },
);

// 初始化时，如果有默认值且当前值为空，使用默认值
watch(
	() => props.field,
	(newField) => {
		if (newField.default !== undefined && (fieldValue.value === null || fieldValue.value === undefined)) {
			fieldValue.value = newField.default;
			updateValue();
		}
	},
	{ immediate: true },
);
</script>

<style scoped lang="scss">
.field-help {
	font-size: 12px;
	color: #909399;
	margin-top: 5px;
}

.form-field-error {
	color: #f56c6c;
	font-size: 12px;
	margin-top: 5px;
}

.el-tag {
	margin-right: 10px;
	margin-bottom: 10px;
}

.el-input {
	width: 100%;
}

.dynamic-tags-container {
	display: flex;
	flex-wrap: wrap;
	align-items: center;
	gap: 8px;
	margin-bottom: 10px;
}
</style>
