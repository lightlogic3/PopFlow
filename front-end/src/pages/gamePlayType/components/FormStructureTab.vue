<template>
	<div class="form-structure-tab">
		<div class="form-structure-actions">
			<el-button type="primary" @click="handleAddComponent">Add Field</el-button>
			<el-button type="primary" @click="addSection">Add Group</el-button>
			<el-button type="success" @click="quickCreateGameConfig">Quick Create Game Config</el-button>
		</div>

		<div v-if="!hasComponents" class="empty-state">
			<el-empty description="No components yet, please add fields or groups" />
		</div>

		<div v-else class="components-container">
			<div
				v-for="(section, sectionIndex) in modelValue.components"
				:key="`section-${sectionIndex}`"
				class="section-item"
			>
				<div class="section-header">
					<el-input v-model="section.title" size="small" placeholder="Group Title" />
					<div class="section-actions">
						<el-button type="primary" size="small" @click="addFieldToSection(sectionIndex)">Add Field</el-button>
						<el-button type="danger" size="small" @click="removeSection(sectionIndex)">Delete Group</el-button>
					</div>
				</div>

				<el-empty v-if="!section.fields || section.fields.length === 0" description="No fields yet, please add fields" />

				<el-collapse v-else v-model="activeField">
					<el-collapse-item
						v-for="(field, fieldIndex) in section.fields"
						:key="`field-${sectionIndex}-${fieldIndex}`"
						:name="`${sectionIndex}-${fieldIndex}`"
					>
						<template #title>
							<div class="field-header">
								<span>{{ field.label || field.name || "Unnamed Field" }} ({{ field.type }})</span>
							</div>
						</template>

						<div class="field-content">
							<el-form label-width="120px">
								<el-form-item label="Field Name">
									<el-input v-model="field.name" placeholder="Unique identifier" @input="validateFieldName(field)" />
									<div class="helper-text">
										<small>Field name must be unique, only supports letters, numbers, and underscores</small>
									</div>
								</el-form-item>

								<el-form-item label="Field Type">
									<el-select v-model="field.type" placeholder="Select field type">
										<el-option label="Text Input" value="input" />
										<el-option label="Text Area" value="textarea" />
										<el-option label="Number Input" value="number" />
										<el-option label="Select" value="select" />
										<el-option label="Radio" value="radio" />
										<el-option label="Checkbox" value="checkbox" />
										<el-option label="Switch" value="switch" />
										<el-option label="Slider" value="slider" />
										<el-option label="Date Picker" value="date" />
										<el-option label="Time Picker" value="time" />
										<el-option label="Rating" value="rate" />
										<el-option label="Color Picker" value="color" />
										<el-option label="Upload" value="upload" />
									</el-select>
								</el-form-item>

								<el-form-item label="Label Text">
									<el-input v-model="field.label" placeholder="Field display name" />
								</el-form-item>

								<el-form-item label="Placeholder">
									<el-input v-model="field.placeholder" placeholder="Placeholder text" />
								</el-form-item>

								<el-form-item label="Default Value">
									<el-input v-model="field.default" placeholder="Default value" />
								</el-form-item>

								<el-form-item label="Help Text">
									<el-input v-model="field.hint" placeholder="Help text content" />
								</el-form-item>

								<el-form-item label="Required">
									<el-switch v-model="field.required" />
								</el-form-item>

								<!-- Option Configuration (for select, radio, checkbox) -->
								<template v-if="['select', 'radio', 'checkbox'].includes(field.type)">
									<el-divider content-position="left">Option Configuration</el-divider>

									<div v-if="!field.options">
										<el-button type="primary" size="small" @click="initOptions(field)">Initialize Options</el-button>
									</div>

									<div v-else class="options-container">
										<div
											v-for="(option, optionIndex) in field.options"
											:key="`option-${optionIndex}`"
											class="option-item"
										>
											<el-input v-model="option.label" placeholder="Option label" class="option-input" />
											<el-input v-model="option.value" placeholder="Option value" class="option-input" />
											<el-button
												type="danger"
												size="small"
												icon="Delete"
												@click="removeOption(field, optionIndex)"
												circle
											/>
										</div>
										<el-button type="primary" size="small" @click="addOption(field)">Add Option</el-button>
									</div>
								</template>

								<!-- Number input specific configuration -->
								<template v-if="field.type === 'number'">
									<el-divider content-position="left">Number Configuration</el-divider>
									<el-form-item label="Minimum">
										<el-input-number v-model="field.min" :min="-Infinity" />
									</el-form-item>
									<el-form-item label="Maximum">
										<el-input-number v-model="field.max" :min="-Infinity" />
									</el-form-item>
									<el-form-item label="Step">
										<el-input-number v-model="field.step" :min="0" :precision="2" />
									</el-form-item>
								</template>

								<!-- Field Operations -->
								<el-divider content-position="left">Field Operations</el-divider>
								<div class="field-actions">
									<el-button type="danger" @click="removeField(sectionIndex, fieldIndex)">Delete Field</el-button>

									<el-button v-if="fieldIndex > 0" type="primary" plain @click="moveFieldUp(sectionIndex, fieldIndex)"
										>Move Up</el-button
									>

									<el-button
										v-if="fieldIndex < section.fields.length - 1"
										type="primary"
										plain
										@click="moveFieldDown(sectionIndex, fieldIndex)"
										>Move Down</el-button
									>
								</div>
							</el-form>
						</div>
					</el-collapse-item>
				</el-collapse>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits, computed, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";

// Define properties
const props = defineProps({
	modelValue: {
		type: Object,
		required: true,
	},
});

// Define events
const emit = defineEmits(["update:modelValue"]);

// Current active field
const activeField = ref([]);

// Computed property: check if components exist
const hasComponents = computed(() => {
	console.log("FormStructureTab - Checking component status:", props.modelValue);
	return props.modelValue && props.modelValue.components && props.modelValue.components.length > 0;
});

// Add field
function handleAddComponent() {
	// Check if components exist, create default group if not
	if (!props.modelValue.components || props.modelValue.components.length === 0) {
		addSection();
	}

	// Add field to the first group
	addFieldToSection(0);
}

// Add group
function addSection() {
	if (!props.modelValue.components) {
		props.modelValue.components = [];
	}

	// Find the highest group number
	let maxSectionNumber = 0;
	props.modelValue.components.forEach((section) => {
		const match = section.title?.match(/Group(\d+)/);
		if (match && parseInt(match[1]) > maxSectionNumber) {
			maxSectionNumber = parseInt(match[1]);
		}
	});

	// Create new group, number+1
	const newSection = {
		title: `Group${maxSectionNumber + 1}`,
		fields: [],
	};

	props.modelValue.components.push(newSection);
	emit("update:modelValue", props.modelValue);
}

// Remove group
function removeSection(sectionIndex) {
	// If the group has fields, show confirmation dialog
	if (props.modelValue.components[sectionIndex].fields && props.modelValue.components[sectionIndex].fields.length > 0) {
		ElMessageBox.confirm("This group contains fields. Deleting the group will also delete all fields in it. Continue?", "Warning", {
			confirmButtonText: "Confirm",
			cancelButtonText: "Cancel",
			type: "warning",
		})
			.then(() => {
				props.modelValue.components.splice(sectionIndex, 1);
				emit("update:modelValue", props.modelValue);
			})
			.catch(() => {
				// User canceled
			});
	} else {
		// If no fields, delete directly
		props.modelValue.components.splice(sectionIndex, 1);
		emit("update:modelValue", props.modelValue);
	}
}

// Add field to specific group
function addFieldToSection(sectionIndex) {
	if (!props.modelValue.components[sectionIndex].fields) {
		props.modelValue.components[sectionIndex].fields = [];
	}

	// Create a unique field name
	let fieldName = "field";
	let counter = 1;

	// Check if field name already exists
	while (isFieldNameExists(`${fieldName}${counter}`)) {
		counter++;
	}

	// Add new field
	const newField = {
		name: `${fieldName}${counter}`,
		type: "input",
		label: `Field${counter}`,
		required: false,
		placeholder: "",
		default: "",
		hint: "",
	};

	props.modelValue.components[sectionIndex].fields.push(newField);
	emit("update:modelValue", props.modelValue);

	// Automatically expand new field
	activeField.value = [`${sectionIndex}-${props.modelValue.components[sectionIndex].fields.length - 1}`];
}

// Remove field
function removeField(sectionIndex, fieldIndex) {
	props.modelValue.components[sectionIndex].fields.splice(fieldIndex, 1);
	emit("update:modelValue", props.modelValue);
}

// Move field up
function moveFieldUp(sectionIndex, fieldIndex) {
	if (fieldIndex > 0) {
		const field = props.modelValue.components[sectionIndex].fields[fieldIndex];
		props.modelValue.components[sectionIndex].fields.splice(fieldIndex, 1);
		props.modelValue.components[sectionIndex].fields.splice(fieldIndex - 1, 0, field);
		emit("update:modelValue", props.modelValue);

		// Update active field
		activeField.value = [`${sectionIndex}-${fieldIndex - 1}`];
	}
}

// Move field down
function moveFieldDown(sectionIndex, fieldIndex) {
	if (fieldIndex < props.modelValue.components[sectionIndex].fields.length - 1) {
		const field = props.modelValue.components[sectionIndex].fields[fieldIndex];
		props.modelValue.components[sectionIndex].fields.splice(fieldIndex, 1);
		props.modelValue.components[sectionIndex].fields.splice(fieldIndex + 1, 0, field);
		emit("update:modelValue", props.modelValue);

		// Update active field
		activeField.value = [`${sectionIndex}-${fieldIndex + 1}`];
	}
}

// Check if field name exists
function isFieldNameExists(name) {
	if (!props.modelValue.components) return false;

	for (const section of props.modelValue.components) {
		if (!section.fields) continue;

		for (const field of section.fields) {
			if (field.name === name) {
				return true;
			}
		}
	}

	return false;
}

// Validate field name
function validateFieldName(field) {
	// First remove invalid characters, keep only letters, numbers and underscores
	field.name = field.name.replace(/[^a-zA-Z0-9_]/g, "");

	// Ensure field name is unique
	let originalName = field.name;
	let counter = 1;

	// Check if there are duplicate field names (except itself)
	let hasDuplicate = false;

	if (props.modelValue.components) {
		for (const section of props.modelValue.components) {
			if (!section.fields) continue;

			for (const otherField of section.fields) {
				if (otherField !== field && otherField.name === field.name) {
					hasDuplicate = true;
					break;
				}
			}

			if (hasDuplicate) break;
		}
	}

	// If duplicate exists, automatically add numeric suffix
	if (hasDuplicate) {
		while (isFieldNameExists(`${originalName}${counter}`)) {
			counter++;
		}

		field.name = `${originalName}${counter}`;
		ElMessage.warning(`Field name already exists, automatically changed to ${field.name}`);
	}

	emit("update:modelValue", props.modelValue);
}

// Initialize options (for select, radio, checkbox)
function initOptions(field) {
	field.options = [
		{ label: "Option 1", value: "option1" },
		{ label: "Option 2", value: "option2" },
	];
	emit("update:modelValue", props.modelValue);
}

// Add option
function addOption(field) {
	if (!field.options) {
		field.options = [];
	}

	const newOptionIndex = field.options.length + 1;
	field.options.push({
		label: `Option ${newOptionIndex}`,
		value: `option${newOptionIndex}`,
	});

	emit("update:modelValue", props.modelValue);
}

// Remove option
function removeOption(field, optionIndex) {
	field.options.splice(optionIndex, 1);
	emit("update:modelValue", props.modelValue);
}

// Quick create game config
function quickCreateGameConfig() {
	ElMessageBox.confirm("This will overwrite the current form configuration and create a new game configuration template. Continue?", "Warning", {
		confirmButtonText: "Confirm",
		cancelButtonText: "Cancel",
		type: "warning",
	})
		.then(() => {
			// Clear existing components
			props.modelValue.components = [];

			// Add role configuration group
			props.modelValue.components.push({
				title: "Role Configuration",
				fields: [
					{
						name: "roleName",
						type: "input",
						label: "Role Name",
						required: true,
						placeholder: "Please enter role name",
						hint: "Role name displayed in game",
					},
					{
						name: "roleCount",
						type: "number",
						label: "Role Count",
						required: true,
						min: 1,
						max: 10,
						step: 1,
						default: "1",
						hint: "Number of this role in game",
					},
					{
						name: "roleType",
						type: "select",
						label: "Role Type",
						required: true,
						options: [
							{ label: "Good", value: "good" },
							{ label: "Bad", value: "bad" },
							{ label: "Neutral", value: "neutral" },
						],
						hint: "Role faction",
					},
				],
			});

			// Add rule configuration group
			props.modelValue.components.push({
				title: "Rule Configuration",
				fields: [
					{
						name: "gameMode",
						type: "radio",
						label: "Game Mode",
						required: true,
						options: [
							{ label: "Standard Mode", value: "standard" },
							{ label: "Competitive Mode", value: "competitive" },
							{ label: "Casual Mode", value: "casual" },
						],
						default: "standard",
						hint: "Select the basic game mode",
					},
					{
						name: "maxPlayers",
						type: "slider",
						label: "Max Players",
						required: true,
						min: 2,
						max: 20,
						step: 1,
						default: "8",
						hint: "Maximum number of players supported",
					},
					{
						name: "timeLimit",
						type: "number",
						label: "Time Limit (minutes)",
						required: false,
						min: 1,
						max: 60,
						step: 1,
						default: "30",
						hint: "Game round time limit",
					},
				],
			});

			// Add settings group
			props.modelValue.components.push({
				title: "Game Settings",
				fields: [
					{
						name: "enableVoice",
						type: "switch",
						label: "Enable Voice",
						default: "true",
						hint: "Whether to enable in-game voice chat",
					},
					{
						name: "difficulty",
						type: "select",
						label: "Game Difficulty",
						required: true,
						options: [
							{ label: "Easy", value: "easy" },
							{ label: "Medium", value: "medium" },
							{ label: "Hard", value: "hard" },
						],
						default: "medium",
						hint: "Set game difficulty level",
					},
					{
						name: "gameNotes",
						type: "textarea",
						label: "Game Instructions",
						placeholder: "Please enter game instructions or notes",
						hint: "Additional game rule instructions",
					},
				],
			});

			emit("update:modelValue", props.modelValue);
			ElMessage.success("Game configuration template has been created");
		})
		.catch(() => {
			// User canceled
		});
}
</script>

<style scoped>
.form-structure-tab {
	padding: 1rem;
}

.form-structure-actions {
	margin-bottom: 1rem;
	display: flex;
	gap: 10px;
}

.empty-state {
	margin: 2rem 0;
}

.components-container {
	margin-top: 1rem;
}

.section-item {
	margin-bottom: 1.5rem;
	border: 1px solid #dcdfe6;
	border-radius: 4px;
	padding: 1rem;
}

.section-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 1rem;
}

.section-header .el-input {
	max-width: 300px;
}

.section-actions {
	display: flex;
	gap: 10px;
}

.field-header {
	display: flex;
	align-items: center;
}

.field-content {
	padding: 1rem;
}

.field-actions {
	display: flex;
	gap: 10px;
}

.options-container {
	margin-top: 1rem;
}

.option-item {
	display: flex;
	gap: 10px;
	margin-bottom: 0.5rem;
	align-items: center;
}

.option-input {
	flex: 1;
}

.helper-text {
	color: #909399;
	margin-top: 0.5rem;
}
</style>
