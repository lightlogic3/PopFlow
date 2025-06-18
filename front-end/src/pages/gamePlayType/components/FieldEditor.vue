<template>
	<div class="field-editor">
		<el-form :model="localField" label-width="120px">
			<!-- Basic Properties -->
			<h3>Basic Properties</h3>
			<el-form-item label="Field Name" required>
				<el-input
					v-model="localField.name"
					placeholder="Enter field name (e.g.: roles.wolf)"
					:disabled="!isNew && disableNameEdit"
					@input="validateName"
				/>
				<div v-if="nameError" class="error-text">{{ nameError }}</div>
			</el-form-item>

			<el-form-item label="Display Label" required>
				<el-input v-model="localField.label" placeholder="Enter the label displayed in the form (e.g.: Wolf Count)" />
			</el-form-item>

			<el-form-item label="Field Type" required>
				<el-select v-model="localField.type" placeholder="Select field type" @change="handleTypeChange">
					<el-option label="Text Input" value="text" />
					<el-option label="Number Input" value="number" />
					<el-option label="Text Area" value="textarea" />
					<el-option label="Dropdown Select" value="select" />
					<el-option label="Checkbox" value="checkbox" />
					<el-option label="Radio Group" value="radio" />
					<el-option label="Switch" value="switch" />
					<el-option label="Slider" value="slider" />
					<el-option label="Date Picker" value="date-picker" />
					<el-option label="Time Picker" value="time-picker" />
					<el-option label="Dynamic Tags" value="dynamic-tags" />
					<el-option label="Color Picker" value="color" />
				</el-select>
			</el-form-item>

			<el-form-item label="Required Field">
				<el-switch v-model="localField.required" />
			</el-form-item>

			<el-form-item label="Field Description">
				<el-input v-model="localField.placeholder" placeholder="Enter field prompt text" />
			</el-form-item>

			<!-- Type-specific Properties -->
			<template v-if="localField.type">
				<h3>Type-specific Properties</h3>

				<!-- Text Input -->
				<template v-if="localField.type === 'text'">
					<el-form-item label="Default Value">
						<el-input v-model="localField.default" placeholder="Default text" />
					</el-form-item>
					<el-form-item label="Max Length">
						<el-input-number v-model="localField.maxLength" :min="0" />
					</el-form-item>
				</template>

				<!-- Number Input -->
				<template v-if="localField.type === 'number'">
					<el-form-item label="Min Value">
						<el-input-number v-model="localField.min" />
					</el-form-item>
					<el-form-item label="Max Value">
						<el-input-number v-model="localField.max" />
					</el-form-item>
					<el-form-item label="Step">
						<el-input-number v-model="localField.step" :min="0.001" :step="0.001" :precision="3" />
					</el-form-item>
					<el-form-item label="Default Value">
						<el-input-number
							v-model="localField.default"
							:min="localField.min"
							:max="localField.max"
							:step="localField.step"
						/>
					</el-form-item>
				</template>

				<!-- Text Area -->
				<template v-if="localField.type === 'textarea'">
					<el-form-item label="Default Value">
						<el-input v-model="localField.default" type="textarea" placeholder="Default text" />
					</el-form-item>
					<el-form-item label="Rows">
						<el-input-number v-model="localField.rows" :min="2" :max="10" />
					</el-form-item>
					<el-form-item label="Max Length">
						<el-input-number v-model="localField.maxLength" :min="0" />
					</el-form-item>
				</template>

				<!-- Dropdown Select -->
				<template v-if="localField.type === 'select'">
					<el-form-item label="Options List" required>
						<div class="options-editor">
							<div v-for="(option, index) in localField.options" :key="index" class="option-item">
								<el-input v-model="option.label" placeholder="Option label" class="option-label" />
								<el-input v-model="option.value" placeholder="Option value" class="option-value" />
								<el-button type="danger" icon="Delete" circle @click="removeOption(index)" />
							</div>
							<el-button type="primary" @click="addOption">Add Option</el-button>
						</div>
					</el-form-item>
					<el-form-item label="Default Value">
						<el-select v-model="localField.default" placeholder="Select default value" clearable>
							<el-option
								v-for="option in localField.options"
								:key="option.value"
								:label="option.label"
								:value="option.value"
							/>
						</el-select>
					</el-form-item>
					<el-form-item label="Allow Multiple">
						<el-switch v-model="localField.multiple" />
					</el-form-item>
					<el-form-item v-if="localField.multiple" label="Default Value (Multiple)">
						<el-select v-model="localField.defaultMultiple" multiple placeholder="Select default values" clearable>
							<el-option
								v-for="option in localField.options"
								:key="option.value"
								:label="option.label"
								:value="option.value"
							/>
						</el-select>
					</el-form-item>
				</template>

				<!-- Checkbox -->
				<template v-if="localField.type === 'checkbox'">
					<el-form-item label="Default Checked">
						<el-switch v-model="localField.default" />
					</el-form-item>
				</template>

				<!-- Radio Group -->
				<template v-if="localField.type === 'radio'">
					<el-form-item label="Options List" required>
						<div class="options-editor">
							<div v-for="(option, index) in localField.options" :key="index" class="option-item">
								<el-input v-model="option.label" placeholder="Option label" class="option-label" />
								<el-input v-model="option.value" placeholder="Option value" class="option-value" />
								<el-button type="danger" icon="Delete" circle @click="removeOption(index)" />
							</div>
							<el-button type="primary" @click="addOption">Add Option</el-button>
						</div>
					</el-form-item>
					<el-form-item label="Default Value">
						<el-select v-model="localField.default" placeholder="Select default value" clearable>
							<el-option
								v-for="option in localField.options"
								:key="option.value"
								:label="option.label"
								:value="option.value"
							/>
						</el-select>
					</el-form-item>
				</template>

				<!-- Switch -->
				<template v-if="localField.type === 'switch'">
					<el-form-item label="Default Value">
						<el-switch v-model="localField.default" />
					</el-form-item>
					<el-form-item label="On Text">
						<el-input v-model="localField.activeText" placeholder="E.g.: Yes" />
					</el-form-item>
					<el-form-item label="Off Text">
						<el-input v-model="localField.inactiveText" placeholder="E.g.: No" />
					</el-form-item>
				</template>

				<!-- Slider -->
				<template v-if="localField.type === 'slider'">
					<el-form-item label="Min Value">
						<el-input-number v-model="localField.min" />
					</el-form-item>
					<el-form-item label="Max Value">
						<el-input-number v-model="localField.max" />
					</el-form-item>
					<el-form-item label="Step">
						<el-input-number v-model="localField.step" :min="1" />
					</el-form-item>
					<el-form-item label="Default Value">
						<el-slider
							v-model="localField.default"
							:min="localField.min"
							:max="localField.max"
							:step="localField.step"
							show-input
						/>
					</el-form-item>
					<el-form-item label="Show Stops">
						<el-switch v-model="localField.showStops" />
					</el-form-item>
				</template>

				<!-- Date Picker -->
				<template v-if="localField.type === 'date-picker'">
					<el-form-item label="Date Type">
						<el-select v-model="localField.dateType" placeholder="Select date type">
							<el-option label="Date" value="date" />
							<el-option label="Date Range" value="daterange" />
							<el-option label="Month" value="month" />
							<el-option label="Year" value="year" />
						</el-select>
					</el-form-item>
					<el-form-item label="Format">
						<el-input v-model="localField.format" placeholder="E.g.: YYYY-MM-DD" />
					</el-form-item>
				</template>

				<!-- Time Picker -->
				<template v-if="localField.type === 'time-picker'">
					<el-form-item label="Format">
						<el-input v-model="localField.format" placeholder="E.g.: HH:mm:ss" />
					</el-form-item>
				</template>

				<!-- Dynamic Tags -->
				<template v-if="localField.type === 'dynamic-tags'">
					<el-form-item label="Default Tags">
						<el-select
							v-model="localField.default"
							multiple
							filterable
							allow-create
							default-first-option
							placeholder="Input and press Enter to add default tags"
						/>
					</el-form-item>
				</template>

				<!-- Color Picker -->
				<template v-if="localField.type === 'color'">
					<el-form-item label="Default Color">
						<el-color-picker v-model="localField.default" show-alpha />
					</el-form-item>
				</template>
			</template>

			<!-- Advanced Properties -->
			<el-collapse>
				<el-collapse-item title="Advanced Properties" name="advanced">
					<el-form-item label="Disable Field">
						<el-switch v-model="localField.disabled" />
					</el-form-item>
					<el-form-item label="Auto Focus">
						<el-switch v-model="localField.autofocus" />
					</el-form-item>
					<el-form-item label="CSS Class">
						<el-input v-model="localField.className" placeholder="Custom CSS class" />
					</el-form-item>
				</el-collapse-item>
			</el-collapse>
		</el-form>
	</div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";

// Define properties
const props = defineProps({
	modelValue: {
		type: Object,
		required: true,
	},
	existingNames: {
		type: Array,
		default: () => [],
	},
	disableNameEdit: {
		type: Boolean,
		default: false,
	},
});

// Define events
const emit = defineEmits(["update:modelValue"]);

// Local state
const localField = ref(JSON.parse(JSON.stringify(props.modelValue)));
const nameError = ref("");

// Determine if it's a new field
const isNew = computed(() => {
	return !props.existingNames.includes(props.modelValue.name);
});

// Sync properties to local state
watch(
	() => props.modelValue,
	(newVal) => {
		localField.value = JSON.parse(JSON.stringify(newVal));
	},
	{ deep: true },
);

// Sync local state to properties
watch(
	() => localField.value,
	(newVal) => {
		emit("update:modelValue", JSON.parse(JSON.stringify(newVal)));
	},
	{ deep: true },
);

// Validate field name
function validateName(value) {
	nameError.value = "";

	if (!value) {
		nameError.value = "Field name cannot be empty";
		return;
	}

	// Check format - should be valid JS variable name or dot-separated path (e.g., roles.wolf)
	const namePattern = /^[a-zA-Z_$][a-zA-Z0-9_$]*(\.[a-zA-Z_$][a-zA-Z0-9_$]*)*$/;
	if (!namePattern.test(value)) {
		nameError.value = "Invalid field name format. Please use standard naming conventions, e.g.: roles.wolf, rules.firstNightKill";
		return;
	}

	// Check if name already exists
	if (isNew.value && props.existingNames.includes(value)) {
		nameError.value = "Field name already exists. Please use a different name";
		return;
	}
}

// Handle field type change
function handleTypeChange(type) {
	// Initialize necessary properties based on type
	if (type === "text") {
		if (!localField.value.default) localField.value.default = "";
		if (!localField.value.maxLength) localField.value.maxLength = 100;
	} else if (type === "number") {
		if (localField.value.min === undefined) localField.value.min = 0;
		if (localField.value.max === undefined) localField.value.max = 100;
		if (localField.value.step === undefined) localField.value.step = 1;
		if (localField.value.default === undefined) localField.value.default = localField.value.min;

		// Provide more suitable default value ranges for game rule type fields
		if (localField.value.name && localField.value.name.startsWith("roles.")) {
			localField.value.min = 0;
			localField.value.max = 10;
			localField.value.default = 1;
		}
	} else if (type === "textarea") {
		if (!localField.value.default) localField.value.default = "";
		if (!localField.value.rows) localField.value.rows = 3;
		if (!localField.value.maxLength) localField.value.maxLength = 500;
	} else if (type === "select" || type === "radio") {
		if (
			!localField.value.options ||
			!Array.isArray(localField.value.options) ||
			localField.value.options.length === 0
		) {
			// Provide more suitable default options for game rule type fields
			if (localField.value.name && localField.value.name.includes("rules.")) {
				localField.value.options = [
					{ label: "Allow", value: "allowed" },
					{ label: "Forbid", value: "forbidden" },
					{ label: "Optional", value: "optional" },
				];
			} else {
				localField.value.options = [
					{ label: "Option 1", value: "option1" },
					{ label: "Option 2", value: "option2" },
				];
			}
		}
		if (!localField.value.default) localField.value.default = localField.value.options[0].value;
		if (type === "select") {
			if (localField.value.multiple === undefined) localField.value.multiple = false;
			if (localField.value.multiple && !localField.value.defaultMultiple) {
				localField.value.defaultMultiple = [];
			}
		}
	} else if (type === "checkbox" || type === "switch") {
		if (localField.value.default === undefined) localField.value.default = false;
		if (type === "switch") {
			// Provide more suitable label text for game rule type fields
			if (localField.value.name && localField.value.name.includes("rules.")) {
				localField.value.activeText = "Yes";
				localField.value.inactiveText = "No";
			} else {
				if (!localField.value.activeText) localField.value.activeText = "Yes";
				if (!localField.value.inactiveText) localField.value.inactiveText = "No";
			}
		}
	} else if (type === "slider") {
		if (localField.value.min === undefined) localField.value.min = 0;
		if (localField.value.max === undefined) localField.value.max = 100;
		if (localField.value.step === undefined) localField.value.step = 1;
		if (localField.value.default === undefined) localField.value.default = localField.value.min;
		if (localField.value.showStops === undefined) localField.value.showStops = false;

		// Provide more suitable default ranges for game settings type fields
		if (localField.value.name && localField.value.name.includes("gameSettings.")) {
			if (localField.value.name.includes("Time")) {
				localField.value.min = 30;
				localField.value.max = 180;
				localField.value.step = 15;
				localField.value.default = 60;
			}
		}
	} else if (type === "date-picker") {
		if (!localField.value.dateType) localField.value.dateType = "date";
		if (!localField.value.format) localField.value.format = "YYYY-MM-DD";
	} else if (type === "time-picker") {
		if (!localField.value.format) localField.value.format = "HH:mm:ss";
	} else if (type === "dynamic-tags") {
		if (!localField.value.default) localField.value.default = [];
		if (!localField.value.placeholder) localField.value.placeholder = "Input and press Enter to add";
	} else if (type === "color") {
		if (!localField.value.default) localField.value.default = "#409EFF";
	}
}

// Add option
function addOption() {
	if (!localField.value.options) {
		localField.value.options = [];
	}
	const newIndex = localField.value.options.length + 1;
	localField.value.options.push({
		label: `Option ${newIndex}`,
		value: `option${newIndex}`,
	});
}

// Remove option
function removeOption(index) {
	localField.value.options.splice(index, 1);
}

// Handle field type on initialization
if (localField.value.type) {
	handleTypeChange(localField.value.type);
}
</script>

<style scoped lang="scss">
.field-editor {
	max-height: 60vh;
	overflow-y: auto;
	padding: 10px;

	h3 {
		margin-top: 20px;
		margin-bottom: 15px;
		padding-bottom: 5px;
		border-bottom: 1px solid #ebeef5;
		color: #409eff;
	}
}

.options-editor {
	.option-item {
		display: flex;
		align-items: center;
		margin-bottom: 10px;

		.option-label {
			flex: 2;
			margin-right: 10px;
		}

		.option-value {
			flex: 1;
			margin-right: 10px;
		}
	}
}

.error-text {
	color: #f56c6c;
	font-size: 12px;
	margin-top: 5px;
}
.el-form-item {
	margin-top: 5px;
}
</style>
