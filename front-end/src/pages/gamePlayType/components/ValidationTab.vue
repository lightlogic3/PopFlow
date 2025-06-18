<template>
	<div class="validation-tab">
		<h3>Form Validation Rules</h3>

		<div class="empty-state" v-if="!hasFields">
			<el-empty description="Please add fields first, then set validation rules" />
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
							<el-button type="primary" size="small" @click="addValidationRule(field.name)">Add Rule</el-button>
						</div>

						<el-empty
							v-if="!getFieldRules(field.name) || getFieldRules(field.name).length === 0"
							description="No validation rules set"
						/>

						<div v-else class="rules-list">
							<div
								v-for="(rule, index) in getFieldRules(field.name)"
								:key="`${field.name}-rule-${index}`"
								class="rule-item"
							>
								<div class="rule-header">
									<strong>Rule {{ index + 1 }}</strong>
									<el-button type="danger" size="small" @click="removeValidationRule(field.name, index)"
										>Delete</el-button
									>
								</div>

								<el-form label-width="100px">
									<el-form-item label="Rule Type">
										<el-select
											v-model="rule.type"
											placeholder="Select rule type"
											@change="updateRuleType(field.name, index)"
										>
											<el-option label="Required" value="required" />
											<el-option label="Min Length" value="min" />
											<el-option label="Max Length" value="max" />
											<el-option label="Pattern" value="pattern" />
											<el-option label="Email" value="email" />
											<el-option label="URL" value="url" />
											<el-option label="Number" value="number" />
											<el-option label="Custom" value="custom" />
										</el-select>
									</el-form-item>

									<el-form-item label="Message">
										<el-input v-model="rule.message" placeholder="Validation failure message" />
									</el-form-item>

									<el-form-item
										v-if="['min', 'max'].includes(rule.type)"
										:label="rule.type === 'min' ? 'Minimum Value' : 'Maximum Value'"
									>
										<el-input-number v-model="rule.value" :min="0" :max="rule.type === 'min' ? 1000 : 10000" />
									</el-form-item>

									<el-form-item v-if="rule.type === 'pattern'" label="Regular Expression">
										<el-input v-model="rule.pattern" placeholder="Enter regex pattern, e.g.: ^[a-zA-Z0-9]+$" />
									</el-form-item>

									<el-form-item v-if="rule.type === 'custom'" label="Custom Validation">
										<el-input
											type="textarea"
											v-model="rule.validator"
											placeholder="Enter validation function code (e.g.: (val) => val.length > 3 || 'Length must be greater than 3')"
											:rows="4"
										/>
										<div class="helper-text">
											<small>Custom validation function receives value as parameter, returns boolean or error message</small>
										</div>
									</el-form-item>

									<el-form-item label="Trigger">
										<el-select v-model="rule.trigger" placeholder="Select trigger method">
											<el-option label="On Change" value="change" />
											<el-option label="On Blur" value="blur" />
											<el-option label="On Submit" value="submit" />
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

// Define properties
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

// Define events
const emit = defineEmits(["update:validationSchema"]);

// Expanded fields
const activeNames = ref([]);

// Computed property: check if fields exist
const hasFields = computed(() => {
	return availableFields.value.length > 0;
});

// Computed property: all available fields for condition rule selection
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

// Ensure validation rule structure is correct and synchronized
function syncValidationSchema() {
	const schema = props.validationSchema;

	// Ensure rules object exists
	if (!schema.rules) {
		schema.rules = {};
	}

	// No longer copy rules from rules to root level
	// Remove field rules existing at root level
	Object.keys(schema).forEach((key) => {
		if (key !== "rules" && Array.isArray(schema[key])) {
			delete schema[key];
		}
	});

	// Convert all existing rules to Element Plus compatible format
	Object.keys(schema.rules).forEach((fieldName) => {
		if (Array.isArray(schema.rules[fieldName])) {
			schema.rules[fieldName].forEach((rule) => {
				// Convert type: "required" to required: true
				if (rule.type === "required") {
					rule.required = true;
				}
			});
		}
	});

	emit("update:validationSchema", schema);
}

// Ensure validation rule structure is correct
function ensureValidStructure() {
	// Ensure rules object exists
	if (!props.validationSchema.rules) {
		props.validationSchema.rules = {};
	}
}

// Get validation rules for a field
function getFieldRules(fieldName: string) {
	ensureValidStructure();
	return props.validationSchema.rules[fieldName] || [];
}

// Add validation rule
function addValidationRule(fieldName: string) {
	ensureValidStructure();

	if (!props.validationSchema.rules[fieldName]) {
		props.validationSchema.rules[fieldName] = [];
	}

	// Modify to Element Plus validation format
	const newRule = {
		required: true,
		message: "This field is required",
		trigger: "blur",
	};

	props.validationSchema.rules[fieldName].push(newRule);

	// No longer copy rules to root level
	emit("update:validationSchema", props.validationSchema);
}

// Delete validation rule
function removeValidationRule(fieldName: string, index: number) {
	ensureValidStructure();

	if (
		props.validationSchema.rules &&
		props.validationSchema.rules[fieldName] &&
		props.validationSchema.rules[fieldName].length > index
	) {
		props.validationSchema.rules[fieldName].splice(index, 1);

		// If no rules remain, clean up empty array
		if (props.validationSchema.rules[fieldName].length === 0) {
			delete props.validationSchema.rules[fieldName];
			// Ensure deletion of root-level rules (if any)
			if (props.validationSchema[fieldName]) {
				delete props.validationSchema[fieldName];
			}
		}

		emit("update:validationSchema", props.validationSchema);
	}
}

// Add updateRuleType function
function updateRuleType(fieldName: string, index: number) {
	const rule = props.validationSchema.rules[fieldName][index];

	// Clear previous rule properties
	if (rule.required !== undefined) delete rule.required;
	if (rule.min !== undefined) delete rule.min;
	if (rule.max !== undefined) delete rule.max;
	if (rule.pattern !== undefined) delete rule.pattern;
	if (rule.validator !== undefined) delete rule.validator;

	// Set correct validation format according to type
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

// Synchronize validation rule structure once when component is mounted
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
