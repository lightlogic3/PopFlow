<template>
	<div class="ui-settings-tab">
		<!-- Layout Settings -->
		<div class="settings-section">
			<h3>Layout Settings</h3>
			<el-form label-width="120px">
				<el-form-item label="Form Layout">
					<el-radio-group v-model="modelValue.layout" @change="updateUiSchema">
						<el-radio-button label="horizontal">Horizontal</el-radio-button>
						<el-radio-button label="vertical">Vertical</el-radio-button>
						<el-radio-button label="inline">Inline</el-radio-button>
					</el-radio-group>
				</el-form-item>

				<el-form-item label="Label Width">
					<el-input-number v-model="modelValue.labelWidth" :min="0" :step="10" @change="updateUiSchema" />
				</el-form-item>

				<el-form-item label="Label Position">
					<el-radio-group v-model="modelValue.labelPosition" @change="updateUiSchema">
						<el-radio-button label="left">Left</el-radio-button>
						<el-radio-button label="top">Top</el-radio-button>
						<el-radio-button label="right">Right</el-radio-button>
					</el-radio-group>
				</el-form-item>

				<el-form-item label="Grid Columns">
					<el-input-number v-model="modelValue.gridColumnCount" :min="1" :max="24" @change="updateUiSchema" />
				</el-form-item>
			</el-form>
		</div>

		<!-- Theme Settings -->
		<div class="settings-section">
			<h3>Theme Settings</h3>
			<el-form label-width="120px">
				<el-form-item label="Theme">
					<el-select v-model="modelValue.theme" @change="updateUiSchema">
						<el-option label="Default" value="default" />
						<el-option label="Simple" value="simple" />
						<el-option label="Dark" value="dark" />
					</el-select>
				</el-form-item>

				<el-form-item label="CSS Class">
					<el-input v-model="modelValue.cssClass" @change="updateUiSchema" />
				</el-form-item>
			</el-form>
		</div>

		<!-- Conditional Display Rules -->
		<div class="settings-section">
			<div class="section-header">
				<h3>Conditional Display Rules</h3>
				<el-button type="primary" size="small" @click="addRule">Add Rule</el-button>
			</div>

			<div v-if="modelValue.conditionalRules && modelValue.conditionalRules.length > 0">
				<div v-for="(rule, index) in modelValue.conditionalRules" :key="index" class="rule-item">
					<el-form label-width="120px">
						<div class="rule-header">
							<span>Rule #{{ index + 1 }}</span>
							<el-button type="danger" size="small" :icon="Delete" circle @click="removeRule(index)" />
						</div>

						<el-form-item label="Target Field">
							<el-select v-model="rule.targetField" placeholder="Select target field" @change="updateUiSchema">
								<el-option v-for="field in allFields" :key="field.name" :label="field.label" :value="field.name" />
							</el-select>
						</el-form-item>

						<el-form-item label="Source Field">
							<el-select v-model="rule.sourceField" placeholder="Select source field" @change="updateUiSchema">
								<el-option v-for="field in allFields" :key="field.name" :label="field.label" :value="field.name" />
							</el-select>
						</el-form-item>

						<el-form-item label="Condition">
							<el-select v-model="rule.condition" placeholder="Select condition" @change="updateUiSchema">
								<el-option label="Equals" value="equals" />
								<el-option label="Not Equals" value="notEquals" />
								<el-option label="Greater Than" value="greaterThan" />
								<el-option label="Less Than" value="lessThan" />
								<el-option label="Contains" value="contains" />
								<el-option label="Not Contains" value="notContains" />
							</el-select>
						</el-form-item>

						<el-form-item label="Value">
							<el-input v-model="rule.value" placeholder="Enter comparison value" @change="updateUiSchema" />
						</el-form-item>
					</el-form>
					<el-divider v-if="index < modelValue.conditionalRules.length - 1" />
				</div>
			</div>
			<el-empty v-else description="No conditional display rules yet" />
		</div>
	</div>
</template>

<script setup lang="ts">
import { Delete } from "@element-plus/icons-vue";
import { onMounted } from "vue";

// Define Field interface
interface Field {
	name: string;
	label: string;
	type: string;
}

// Define Conditional Rule interface
interface ConditionalRule {
	targetField: string;
	sourceField: string;
	condition: string;
	value: string | number;
}

// Define UI Schema interface
interface UiSchema {
	layout: string;
	labelWidth: number;
	labelPosition: string;
	gridColumnCount: number;
	theme: string;
	cssClass: string;
	cssClasses?: any; // Add cssClasses property
	conditionalRules: ConditionalRule[];
	conditionalDisplay?: any[]; // Add property compatible with DynamicForm
}

// Define Props
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

// Define events
const emit = defineEmits(["update:modelValue"]);

// Initialize default values
function initializeDefaults() {
	console.log("UiSettingsTab - Data at initialization:", props.modelValue);

	// Ensure necessary properties exist
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

	// Sync update
	updateUiSchema();
}

// Update UI Schema
const updateUiSchema = () => {
	// Ensure conditionalDisplay field exists
	if (!props.modelValue.conditionalDisplay) {
		props.modelValue.conditionalDisplay = [];
	}

	// Convert from conditionalRules to conditionalDisplay format
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

// Add conditional rule
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

// Remove conditional rule
const removeRule = (index: number) => {
	props.modelValue.conditionalRules.splice(index, 1);
	updateUiSchema();
};

// Initialize on component mount
onMounted(() => {
	console.log("UiSettingsTab component mounted - Initial data:", JSON.stringify(props.modelValue));
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
