<template>
	<div class="dynamic-form" :class="getFormClass()">
		<template v-if="schema && schema.title">
			<h2 class="form-title">{{ schema.title }}</h2>
			<p v-if="schema.description" class="form-description">{{ schema.description }}</p>
		</template>

		<!-- 布局渲染 -->
		<div class="form-container">
			<template v-if="uiSchema.layout === 'tabs'">
				<!-- 多个分组时使用标签页 -->
				<template v-if="schema.components && schema.components.length > 1">
					<el-tabs v-model="activeTab" :lazy="true">
						<el-tab-pane
							v-for="section in schema.components"
							:key="section.title"
							:label="section.title"
							:name="section.title"
						>
							<form-section
								:section="section"
								:value="formData"
								:validation-schema="validationSchema"
								:validation-errors="validationErrors"
								:read-only="readOnly"
								:label-position="uiSchema.labelPosition"
								@update:value="updateFormData"
							/>
						</el-tab-pane>
					</el-tabs>
				</template>
				<!-- 单个分组时直接显示内容 -->
				<template v-else-if="schema.components && schema.components.length === 1">
					<form-section
						:section="schema.components[0]"
						:value="formData"
						:validation-schema="validationSchema"
						:validation-errors="validationErrors"
						:read-only="readOnly"
						:hide-title="true"
						:label-position="uiSchema.labelPosition"
						@update:value="updateFormData"
					/>
				</template>
				<el-empty v-else description="the form content is empty" />
			</template>

			<template v-else-if="uiSchema.layout === 'steps'">
				<el-steps :active="activeStep" finish-status="success" class="form-steps">
					<el-step v-for="section in schema.components" :key="section.title" :title="section.title" />
				</el-steps>

				<div class="step-content">
					<form-section
						v-if="schema.components[activeStep]"
						:section="schema.components[activeStep]"
						:value="formData"
						:validation-schema="validationSchema"
						:validation-errors="validationErrors"
						:read-only="readOnly"
						:label-position="uiSchema.labelPosition"
						@update:value="updateFormData"
					/>

					<div class="step-buttons">
						<el-button v-if="activeStep > 0" @click="prevStep">上一步</el-button>
						<el-button v-if="activeStep < schema.components.length - 1" type="primary" @click="nextStep">
							下一步
						</el-button>
						<el-button v-else type="success" @click="submitForm" :disabled="readOnly"> 提交 </el-button>
					</div>
				</div>
			</template>

			<template v-else>
				<!-- 默认布局：分组 -->
				<div class="sections-container">
					<template v-if="schema.components && schema.components.length === 1">
						<!-- 单个分组时直接渲染内容，不显示分组标题 -->
						<form-section
							:section="schema.components[0]"
							:value="formData"
							:validation-schema="validationSchema"
							:validation-errors="validationErrors"
							:read-only="readOnly"
							:hide-title="true"
							:label-position="uiSchema.labelPosition"
							@update:value="updateFormData"
						/>
					</template>
					<template v-else-if="schema.components && schema.components.length > 1">
						<!-- 多个分组时显示标题 -->
						<form-section
							v-for="section in schema.components"
							:key="section.title"
							:section="section"
							:value="formData"
							:validation-schema="validationSchema"
							:validation-errors="validationErrors"
							:read-only="readOnly"
							:label-position="uiSchema.labelPosition"
							@update:value="updateFormData"
						/>
					</template>
					<el-empty v-else description="表单内容为空" />
				</div>

				<div v-if="!readOnly" class="form-buttons">
					<el-button type="primary" @click="submitForm">Submit</el-button>
					<el-button @click="resetForm">Reset</el-button>
				</div>
			</template>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, nextTick, onMounted, defineExpose } from "vue";
import FormSection from "./FormSection.vue";

// 定义属性
const props = defineProps({
	schema: {
		type: Object,
		required: true,
	},
	uiSchema: {
		type: Object,
		default: () => ({
			layout: "sections",
			theme: "light",
			cssClasses: {
				formContainer: "",
				section: "",
				field: "",
			},
			conditionalDisplay: [],
		}),
	},
	validationSchema: {
		type: Object,
		default: () => ({}),
	},
	formData: {
		type: Object,
		default: () => ({}),
	},
	readOnly: {
		type: Boolean,
		default: false,
	},
});

watch(
	props.validationSchema,
	(newVal, oldVal) => {
		console.log("DynamicForm 验证Schema变化:", newVal, "旧值:", oldVal);
	},
	{ immediate: true, deep: true },
);

// 定义事件
const emit = defineEmits(["update:formData", "submit", "reset", "validation"]);

// 本地状态 - 使用函数创建初始值以避免直接引用
const localFormData = reactive(
	(() => {
		// 深拷贝以避免引用问题
		return JSON.parse(JSON.stringify(props.formData || {}));
	})(),
);
const activeTab = ref("");
const activeStep = ref(0);
const validationErrors = ref({});

// 获取表单类
function getFormClass() {
	const classes = ["dynamic-form"];
	if (props.uiSchema.theme) {
		classes.push(`theme-${props.uiSchema.theme}`);
	}
	if (props.uiSchema.cssClasses && props.uiSchema.cssClasses.formContainer) {
		classes.push(props.uiSchema.cssClasses.formContainer);
	}
	return classes.join(" ");
}

// 更新表单数据 - 添加错误处理和优化
function updateFormData(key, value) {
	if (!key) return; // 防止空键

	try {
		// 如果值没有变化，不进行更新以避免循环
		const oldValue = getFieldValue(key);
		if (oldValue === value) return;

		// 支持嵌套路径，如 'roles.wolf'
		if (key.includes(".")) {
			const parts = key.split(".");
			let current = localFormData;
			for (let i = 0; i < parts.length - 1; i++) {
				if (!current[parts[i]]) {
					current[parts[i]] = {};
				}
				current = current[parts[i]];
			}
			current[parts[parts.length - 1]] = value;
		} else {
			localFormData[key] = value;
		}

		// 使用深拷贝向父组件发送更新
		emit("update:formData", JSON.parse(JSON.stringify(localFormData)));

		// 延迟执行条件显示逻辑检查，避免同一更新周期内重复执行
		if (!isUpdatingFormData.value) {
			isUpdatingFormData.value = true;
			nextTick(() => {
				checkConditionalDisplay();
				// 清除该字段的验证错误（如果存在）
				if (validationErrors.value[key]) {
					delete validationErrors.value[key];
				}
				setTimeout(() => {
					isUpdatingFormData.value = false;
				}, 0);
			});
		}
	} catch (e) {
		console.error("Error updating form data:", e);
	}
}

// 检查条件显示逻辑 - 增强稳定性
function checkConditionalDisplay() {
	// 多重检查防止错误
	if (
		!props.uiSchema ||
		!props.uiSchema.conditionalDisplay ||
		!Array.isArray(props.uiSchema.conditionalDisplay) ||
		props.uiSchema.conditionalDisplay.length === 0
	) {
		return;
	}

	try {
		nextTick(() => {
			props.uiSchema.conditionalDisplay.forEach((condition) => {
				// 检查条件对象结构是否完整
				if (!condition || !condition.if || !condition.then || !condition.then.fields) {
					return;
				}

				const { field, operator, value } = condition.if;

				// 字段名为空则跳过
				if (!field) return;

				const fieldValue = getFieldValue(field);

				let conditionMet = false;
				if (operator === "equals") {
					conditionMet = fieldValue === value;
				} else if (operator === "notEquals") {
					conditionMet = fieldValue !== value;
				} else if (operator === "greaterThan") {
					conditionMet = fieldValue > value;
				} else if (operator === "lessThan") {
					conditionMet = fieldValue < value;
				}

				// 确保fields是数组
				if (!Array.isArray(condition.then.fields)) {
					return;
				}

				// 执行显示或隐藏操作
				if (condition.then.action === "show") {
					condition.then.fields.forEach((targetField) => {
						if (!targetField) return;
						const fieldElement = document.querySelector(`[data-field="${targetField}"]`);
						if (fieldElement) {
							(fieldElement as HTMLElement).style.display = conditionMet ? "" : "none";
						}
					});
				} else if (condition.then.action === "hide") {
					condition.then.fields.forEach((targetField) => {
						if (!targetField) return;
						const fieldElement = document.querySelector(`[data-field="${targetField}"]`);
						if (fieldElement) {
							(fieldElement as HTMLElement).style.display = conditionMet ? "none" : "";
						}
					});
				}
			});
		});
	} catch (e) {
		console.error("Error in conditional display:", e);
	}
}

// 获取字段值
function getFieldValue(fieldPath) {
	if (fieldPath.includes(".")) {
		const parts = fieldPath.split(".");
		let value = localFormData;
		for (const part of parts) {
			if (value === undefined || value === null) {
				return undefined;
			}
			value = value[part];
		}
		return value;
	}
	return localFormData[fieldPath];
}

// 提交表单
function submitForm() {
	if (props.readOnly) return;

	// 先验证表单，然后再提交
	validate().then((valid) => {
		if (valid) {
			emit("submit", { ...localFormData });
		}
	});
}

// 重置表单
function resetForm() {
	Object.keys(localFormData).forEach((key) => {
		delete localFormData[key];
	});
	Object.assign(localFormData, props.formData);
	// 清空验证错误
	validationErrors.value = {};
	emit("reset");
	emit("update:formData", { ...localFormData });
}

// 下一步
function nextStep() {
	if (activeStep.value < props.schema.components.length - 1) {
		activeStep.value++;
	}
}

// 上一步
function prevStep() {
	if (activeStep.value > 0) {
		activeStep.value--;
	}
}

// 模式计算属性
const schema = computed(() => props.schema);

// 验证表单数据
async function validate() {
	try {
		validationErrors.value = {}; // 清空之前的错误
		let isValid = true;
		const errors = {};

		// 检查是否有验证规则
		if (!props.validationSchema || Object.keys(props.validationSchema).length === 0) {
			return true; // 没有验证规则，直接返回验证成功
		}

		// 遍历验证规则并验证
		for (const fieldName in props.validationSchema) {
			const rules = props.validationSchema[fieldName];
			if (!Array.isArray(rules)) continue;

			const fieldValue = getFieldValue(fieldName);

			// 遍历该字段的所有规则
			for (const rule of rules) {
				// 必填规则
				if (rule.required && (fieldValue === undefined || fieldValue === null || fieldValue === "")) {
					errors[fieldName] = rule.message || "此字段不能为空";
					isValid = false;
					break;
				}

				// 最小长度规则
				if (rule.min !== undefined && typeof fieldValue === "string" && fieldValue.length < rule.min) {
					errors[fieldName] = rule.message || `长度不能小于${rule.min}个字符`;
					isValid = false;
					break;
				}

				// 最大长度规则
				if (rule.max !== undefined && typeof fieldValue === "string" && fieldValue.length > rule.max) {
					errors[fieldName] = rule.message || `长度不能超过${rule.max}个字符`;
					isValid = false;
					break;
				}

				// 自定义验证器
				if (rule.validator && typeof rule.validator === "function") {
					try {
						const result = await rule.validator(fieldValue, localFormData);
						if (result !== true) {
							errors[fieldName] = typeof result === "string" ? result : rule.message || "验证失败";
							isValid = false;
							break;
						}
					} catch (e: any) {
						errors[fieldName] = e.message || rule.message || "验证失败";
						isValid = false;
						break;
					}
				}

				// 正则验证
				if (rule.pattern && !rule.pattern.test(fieldValue)) {
					errors[fieldName] = rule.message || "格式不正确";
					isValid = false;
					break;
				}
			}
		}

		validationErrors.value = errors;
		emit("validation", { valid: isValid, errors });
		return isValid;
	} catch (error) {
		console.error("表单验证错误:", error);
		emit("validation", { valid: false, errors: { _form: "表单验证过程中发生错误" } });
		return false;
	}
}

// 监听属性变化 - 使用深拷贝并添加防循环锁
const isUpdatingFormData = ref(false);
watch(
	() => props.formData,
	(newValue) => {
		if (isUpdatingFormData.value) return;

		isUpdatingFormData.value = true;
		nextTick(() => {
			// 清空当前数据
			Object.keys(localFormData).forEach((key) => {
				delete localFormData[key];
			});

			// 使用深拷贝避免引用问题
			if (newValue) {
				const safeValue = JSON.parse(JSON.stringify(newValue));
				Object.assign(localFormData, safeValue);
			}

			setTimeout(() => {
				isUpdatingFormData.value = false;
			}, 0);
		});
	},
	{ deep: false }, // 不使用深度监听，减少性能消耗和递归风险
);

// 初始化选中第一个标签，使用setTimeout避免渲染循环
watch(
	() => schema.value,
	(newSchema) => {
		if (newSchema && newSchema.components && newSchema.components.length > 0) {
			// 延迟设置activeTab，避免与scrollbar组件发生循环更新
			setTimeout(() => {
				activeTab.value = newSchema.components[0].title;
			}, 0);
		}
	},
	{ immediate: true },
);

// 仅在组件挂载时初始化条件显示
onMounted(() => {
	// 初始化时执行一次条件显示逻辑
	nextTick(() => {
		if (props.uiSchema && props.uiSchema.conditionalDisplay && props.uiSchema.conditionalDisplay.length > 0) {
			checkConditionalDisplay();
		}
	});
});

// 向父组件暴露validate方法
defineExpose({
	validate,
});
</script>

<style lang="scss" scoped>
.dynamic-form {
	width: 100%;
	height: 100%;
	box-sizing: border-box;
	position: relative;

	&.theme-dark {
		// 暗色主题样式
		color: #f0f0f0;

		:deep(.el-input__wrapper),
		:deep(.el-textarea__wrapper),
		:deep(.el-input__inner),
		:deep(.el-textarea__inner) {
			background-color: transparent !important;
			background: transparent !important;
			color: #f0f0f0 !important;
		}

		:deep(.el-form-item__label) {
			color: #f0f0f0 !important;
		}

		:deep(.form-field-error) {
			color: #ff6b6b !important;
			font-size: 12px;
			margin-top: 5px;
		}
	}

	&.theme-light {
		background-color: #fff;
		color: #333;

		:deep(.form-field-error) {
			color: #f56c6c !important;
			font-size: 12px;
			margin-top: 5px;
		}
	}
}

.form-title {
	font-size: 24px;
	margin-bottom: 10px;
}

.form-description {
	margin-bottom: 20px;
	color: #666;
}

.form-container {
	padding: 20px;
}

.sections-container {
	margin-bottom: 20px;
}

.form-buttons {
	margin-top: 20px;
	display: flex;
	justify-content: flex-end;
	gap: 10px;
}

.form-steps {
	margin-bottom: 30px;
}

.step-content {
	margin-top: 20px;
}

.step-buttons {
	margin-top: 20px;
	display: flex;
	justify-content: flex-end;
	gap: 10px;
}
</style>
