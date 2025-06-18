<template>
	<div class="validation-tab">
		<h3>表单验证规则</h3>

		<div class="empty-state" v-if="!hasFields">
			<el-empty description="请先添加字段，然后设置验证规则" />
		</div>

		<div v-else class="field-validation-list">
			<el-collapse v-model="activeNames">
				<el-collapse-item
					v-for="field in availableFields"
					:key="field.name"
					:title="`${field.label || field.name} (${field.type})`"
					:name="field.name"
				>
					<div class="field-validation-content">
						<div class="validation-header">
							<strong>{{ field.label || field.name }}</strong>
							<el-button type="primary" size="small" @click="addValidationRule(field.name)">添加规则</el-button>
						</div>

						<el-empty
							v-if="!getFieldRules(field.name) || getFieldRules(field.name).length === 0"
							description="未设置验证规则"
						/>

						<div v-else class="rules-list">
							<div
								v-for="(rule, index) in getFieldRules(field.name)"
								:key="`${field.name}-rule-${index}`"
								class="rule-item"
							>
								<div class="rule-header">
									<strong>规则 {{ index + 1 }}</strong>
									<el-button type="danger" size="small" @click="removeValidationRule(field.name, index)"
										>删除</el-button
									>
								</div>

								<el-form label-width="100px">
									<el-form-item label="规则类型">
										<el-select
											v-model="rule.type"
											placeholder="选择规则类型"
											@change="updateRuleType(field.name, index)"
										>
											<el-option label="必填" value="required" />
											<el-option label="最小长度" value="min" />
											<el-option label="最大长度" value="max" />
											<el-option label="模式匹配" value="pattern" />
											<el-option label="邮箱" value="email" />
											<el-option label="URL" value="url" />
											<el-option label="数字" value="number" />
											<el-option label="自定义" value="custom" />
										</el-select>
									</el-form-item>

									<el-form-item label="提示信息">
										<el-input v-model="rule.message" placeholder="验证失败提示信息" />
									</el-form-item>

									<el-form-item
										v-if="['min', 'max'].includes(rule.type)"
										:label="rule.type === 'min' ? '最小值' : '最大值'"
									>
										<el-input-number v-model="rule.value" :min="0" :max="rule.type === 'min' ? 1000 : 10000" />
									</el-form-item>

									<el-form-item v-if="rule.type === 'pattern'" label="正则表达式">
										<el-input v-model="rule.pattern" placeholder="输入正则表达式，例如：^[a-zA-Z0-9]+$" />
									</el-form-item>

									<el-form-item v-if="rule.type === 'custom'" label="自定义验证">
										<el-input
											type="textarea"
											v-model="rule.validator"
											placeholder="输入验证函数代码 (如: (val) => val.length > 3 || '长度必须大于3')"
											:rows="4"
										/>
										<div class="helper-text">
											<small>自定义验证函数接收值作为参数，返回布尔值或错误信息</small>
										</div>
									</el-form-item>

									<el-form-item label="触发方式">
										<el-select v-model="rule.trigger" placeholder="选择触发方式">
											<el-option label="变更时" value="change" />
											<el-option label="失焦时" value="blur" />
											<el-option label="提交时" value="submit" />
										</el-select>
									</el-form-item>
								</el-form>

								<el-divider v-if="index < getFieldRules(field.name).length - 1" />
							</div>
						</div>
					</div>
				</el-collapse-item>
			</el-collapse>
		</div>
	</div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits, computed, ref, onMounted } from "vue";

// 定义属性
const props = defineProps({
	validationSchema: {
		type: Object,
		required: true,
	},
	configSchema: {
		type: Object,
		required: true,
	},
});

// 定义事件
const emit = defineEmits(["update:validationSchema"]);

// 展开的字段
const activeNames = ref([]);

// 计算属性：判断是否有字段
const hasFields = computed(() => {
	return availableFields.value.length > 0;
});

// 计算属性：所有可用字段，用于条件规则选择
const availableFields = computed(() => {
	const fields: any[] = [];
	if (props.configSchema && props.configSchema.components) {
		props.configSchema.components.forEach((section) => {
			if (section.fields) {
				section.fields.forEach((field) => {
					fields.push(field);
				});
			}
		});
	}
	return fields;
});

// 确保验证规则结构正确并同步更新
function syncValidationSchema() {
	const schema = props.validationSchema;

	// 确保rules对象存在
	if (!schema.rules) {
		schema.rules = {};
	}

	// 不再将rules中的规则复制到根级别
	// 移除根级别已存在的字段规则
	Object.keys(schema).forEach((key) => {
		if (key !== "rules" && Array.isArray(schema[key])) {
			delete schema[key];
		}
	});

	// 转换所有现有规则为Element Plus兼容格式
	Object.keys(schema.rules).forEach((fieldName) => {
		if (Array.isArray(schema.rules[fieldName])) {
			schema.rules[fieldName].forEach((rule) => {
				// 将type: "required" 转换为 required: true
				if (rule.type === "required") {
					rule.required = true;
				}
			});
		}
	});

	emit("update:validationSchema", schema);
}

// 确保验证规则结构正确
function ensureValidStructure() {
	// 确保rules对象存在
	if (!props.validationSchema.rules) {
		props.validationSchema.rules = {};
	}
}

// 获取字段的验证规则
function getFieldRules(fieldName: string) {
	ensureValidStructure();
	return props.validationSchema.rules[fieldName] || [];
}

// 添加验证规则
function addValidationRule(fieldName: string) {
	ensureValidStructure();

	if (!props.validationSchema.rules[fieldName]) {
		props.validationSchema.rules[fieldName] = [];
	}

	// 修改为Element Plus的验证格式
	const newRule = {
		required: true,
		message: "此字段为必填项",
		trigger: "blur",
	};

	props.validationSchema.rules[fieldName].push(newRule);

	// 不再将规则复制到根级别
	emit("update:validationSchema", props.validationSchema);
}

// 删除验证规则
function removeValidationRule(fieldName: string, index: number) {
	ensureValidStructure();

	if (
		props.validationSchema.rules &&
		props.validationSchema.rules[fieldName] &&
		props.validationSchema.rules[fieldName].length > index
	) {
		props.validationSchema.rules[fieldName].splice(index, 1);

		// 如果没有规则了，清理空数组
		if (props.validationSchema.rules[fieldName].length === 0) {
			delete props.validationSchema.rules[fieldName];
			// 确保删除根级别的规则(如果有的话)
			if (props.validationSchema[fieldName]) {
				delete props.validationSchema[fieldName];
			}
		}

		emit("update:validationSchema", props.validationSchema);
	}
}

// 添加updateRuleType函数
function updateRuleType(fieldName: string, index: number) {
	const rule = props.validationSchema.rules[fieldName][index];

	// 清除之前的规则属性
	if (rule.required !== undefined) delete rule.required;
	if (rule.min !== undefined) delete rule.min;
	if (rule.max !== undefined) delete rule.max;
	if (rule.pattern !== undefined) delete rule.pattern;
	if (rule.validator !== undefined) delete rule.validator;

	// 根据类型设置正确的验证格式
	if (rule.type === "required") {
		rule.required = true;
	} else if (rule.type === "email") {
		rule.type = "email";
	} else if (rule.type === "url") {
		rule.type = "url";
	} else if (rule.type === "number") {
		rule.type = "number";
	}

	emit("update:validationSchema", props.validationSchema);
}

// 组件挂载时同步一次验证规则结构
onMounted(() => {
	syncValidationSchema();
});
</script>

<style scoped>
.validation-tab {
	padding: 1rem;
}

.field-validation-list {
	margin-top: 1rem;
}

.field-validation-content {
	padding: 1rem;
}

.validation-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 1rem;
}

.rules-list {
	padding: 1rem;
	border: 1px solid #dcdfe6;
	border-radius: 4px;
}

.rule-item {
	margin-bottom: 1rem;
}

.rule-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 0.5rem;
}

.helper-text {
	color: #909399;
	margin-top: 0.5rem;
}
</style>
