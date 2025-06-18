<template>
	<div class="ui-settings-tab">
		<!-- 布局设置 -->
		<div class="settings-section">
			<h3>布局设置</h3>
			<el-form label-width="120px">
				<el-form-item label="表单布局">
					<el-radio-group v-model="modelValue.layout" @change="updateUiSchema">
						<el-radio-button label="horizontal">水平</el-radio-button>
						<el-radio-button label="vertical">垂直</el-radio-button>
						<el-radio-button label="inline">行内</el-radio-button>
					</el-radio-group>
				</el-form-item>

				<el-form-item label="标签宽度">
					<el-input-number v-model="modelValue.labelWidth" :min="0" :step="10" @change="updateUiSchema" />
				</el-form-item>

				<el-form-item label="标签位置">
					<el-radio-group v-model="modelValue.labelPosition" @change="updateUiSchema">
						<el-radio-button label="left">左侧</el-radio-button>
						<el-radio-button label="top">顶部</el-radio-button>
						<el-radio-button label="right">右侧</el-radio-button>
					</el-radio-group>
				</el-form-item>

				<el-form-item label="栅格列数">
					<el-input-number v-model="modelValue.gridColumnCount" :min="1" :max="24" @change="updateUiSchema" />
				</el-form-item>
			</el-form>
		</div>

		<!-- 主题设置 -->
		<div class="settings-section">
			<h3>主题设置</h3>
			<el-form label-width="120px">
				<el-form-item label="主题">
					<el-select v-model="modelValue.theme" @change="updateUiSchema">
						<el-option label="默认" value="default" />
						<el-option label="简约" value="simple" />
						<el-option label="暗色" value="dark" />
					</el-select>
				</el-form-item>

				<el-form-item label="CSS类名">
					<el-input v-model="modelValue.cssClass" @change="updateUiSchema" />
				</el-form-item>
			</el-form>
		</div>

		<!-- 条件显示规则 -->
		<div class="settings-section">
			<div class="section-header">
				<h3>条件显示规则</h3>
				<el-button type="primary" size="small" @click="addRule">添加规则</el-button>
			</div>

			<div v-if="modelValue.conditionalRules && modelValue.conditionalRules.length > 0">
				<div v-for="(rule, index) in modelValue.conditionalRules" :key="index" class="rule-item">
					<el-form label-width="120px">
						<div class="rule-header">
							<span>规则 #{{ index + 1 }}</span>
							<el-button type="danger" size="small" :icon="Delete" circle @click="removeRule(index)" />
						</div>

						<el-form-item label="目标字段">
							<el-select v-model="rule.targetField" placeholder="选择目标字段" @change="updateUiSchema">
								<el-option v-for="field in allFields" :key="field.name" :label="field.label" :value="field.name" />
							</el-select>
						</el-form-item>

						<el-form-item label="源字段">
							<el-select v-model="rule.sourceField" placeholder="选择源字段" @change="updateUiSchema">
								<el-option v-for="field in allFields" :key="field.name" :label="field.label" :value="field.name" />
							</el-select>
						</el-form-item>

						<el-form-item label="条件">
							<el-select v-model="rule.condition" placeholder="选择条件" @change="updateUiSchema">
								<el-option label="等于" value="equals" />
								<el-option label="不等于" value="notEquals" />
								<el-option label="大于" value="greaterThan" />
								<el-option label="小于" value="lessThan" />
								<el-option label="包含" value="contains" />
								<el-option label="不包含" value="notContains" />
							</el-select>
						</el-form-item>

						<el-form-item label="值">
							<el-input v-model="rule.value" placeholder="输入比较值" @change="updateUiSchema" />
						</el-form-item>
					</el-form>
					<el-divider v-if="index < modelValue.conditionalRules.length - 1" />
				</div>
			</div>
			<el-empty v-else description="暂无条件显示规则" />
		</div>
	</div>
</template>

<script setup lang="ts">
import { Delete } from "@element-plus/icons-vue";
import { onMounted } from "vue";

// 定义字段接口
interface Field {
	name: string;
	label: string;
	type: string;
}

// 定义条件规则接口
interface ConditionalRule {
	targetField: string;
	sourceField: string;
	condition: string;
	value: string | number;
}

// 定义UI Schema接口
interface UiSchema {
	layout: string;
	labelWidth: number;
	labelPosition: string;
	gridColumnCount: number;
	theme: string;
	cssClass: string;
	cssClasses?: any; // 添加cssClasses属性
	conditionalRules: ConditionalRule[];
	conditionalDisplay?: any[]; // 添加兼容DynamicForm的属性
}

// 定义Props
const props = defineProps({
	modelValue: {
		type: Object as () => UiSchema,
		required: true,
	},
	allFields: {
		type: Array as () => Field[],
		required: true,
	},
});

// 定义事件
const emit = defineEmits(["update:modelValue"]);

// 初始化默认值
function initializeDefaults() {
	console.log("UiSettingsTab - 初始化时的数据:", props.modelValue);

	// 确保必要的属性存在
	if (!props.modelValue.layout) {
		props.modelValue.layout = "tabs";
	}

	if (!props.modelValue.theme) {
		props.modelValue.theme = "light";
	}

	if (!props.modelValue.labelPosition) {
		props.modelValue.labelPosition = "top";
	}

	if (!props.modelValue.cssClasses) {
		props.modelValue.cssClasses = {
			formContainer: "game-form-container",
			section: "game-form-section",
			field: "game-form-field",
		};
	}

	if (!props.modelValue.conditionalRules) {
		props.modelValue.conditionalRules = [];
	}

	if (!props.modelValue.conditionalDisplay) {
		props.modelValue.conditionalDisplay = [];
	}

	// 同步更新
	updateUiSchema();
}

// 更新UI Schema
const updateUiSchema = () => {
	// 确保conditionalDisplay字段存在
	if (!props.modelValue.conditionalDisplay) {
		props.modelValue.conditionalDisplay = [];
	}

	// 从conditionalRules转换到conditionalDisplay格式
	props.modelValue.conditionalDisplay = [];
	if (props.modelValue.conditionalRules && props.modelValue.conditionalRules.length > 0) {
		props.modelValue.conditionalRules.forEach((rule) => {
			if (rule.sourceField && rule.targetField && rule.condition) {
				props.modelValue.conditionalDisplay.push({
					if: {
						field: rule.sourceField,
						operator: rule.condition,
						value: rule.value,
					},
					then: {
						action: "show",
						fields: [rule.targetField],
					},
				});
			}
		});
	}

	emit("update:modelValue", props.modelValue);
};

// 添加条件规则
const addRule = () => {
	if (!props.modelValue.conditionalRules) {
		props.modelValue.conditionalRules = [];
	}

	props.modelValue.conditionalRules.push({
		targetField: "",
		sourceField: "",
		condition: "equals",
		value: "",
	});

	updateUiSchema();
};

// 删除条件规则
const removeRule = (index: number) => {
	props.modelValue.conditionalRules.splice(index, 1);
	updateUiSchema();
};

// 在组件挂载时初始化
onMounted(() => {
	console.log("UiSettingsTab 组件挂载 - 初始数据:", JSON.stringify(props.modelValue));
	initializeDefaults();
});
</script>

<style scoped>
.ui-settings-tab {
	padding: 10px;
}

.settings-section {
	margin-bottom: 20px;
	border: 1px solid rgba(235, 238, 245, 0.42);
	border-radius: 4px;
	padding: 15px;
}

.section-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 15px;
}

.rule-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 10px;
	padding: 5px 0;
	font-weight: bold;
}

.rule-item {
	margin-bottom: 10px;
	padding: 10px;
	border-radius: 4px;
}
.el-form-item {
	margin-bottom: 10px;
}
</style>
