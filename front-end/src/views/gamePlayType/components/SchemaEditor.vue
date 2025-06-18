<template>
	<div class="schema-editor-container">
		<div class="editor-layout">
			<!-- 左侧编辑区域 -->
			<div class="editor-panel">
				<div class="tab-header">
					<div class="tab-buttons">
						<el-button
							:type="activeTabName === 'form-structure' ? 'primary' : 'default'"
							@click="activeTabName = 'form-structure'"
							>Form Structure</el-button
						>
						<el-button
							:type="activeTabName === 'ui-settings' ? 'primary' : 'default'"
							@click="activeTabName = 'ui-settings'"
							>UI Settings</el-button
						>
						<el-button
							:type="activeTabName === 'validation' ? 'primary' : 'default'"
							@click="activeTabName = 'validation'"
							>Validation Rules</el-button
						>
						<el-button
							:type="activeTabName === 'json-editor' ? 'primary' : 'default'"
							@click="activeTabName = 'json-editor'"
							>JSON Editor</el-button
						>
					</div>
				</div>

				<!-- 表单结构 -->
				<div v-if="activeTabName === 'form-structure'">
					<form-structure-tab v-model="localSchema" @update:model-value="handleSchemaChange" />
				</div>

				<!-- UI配置 -->
				<div v-else-if="activeTabName === 'ui-settings'">
					<ui-settings-tab v-model="localUiSchema" :all-fields="allFields" @update:model-value="handleUiSchemaChange" />
				</div>

				<!-- 验证规则 -->
				<div v-else-if="activeTabName === 'validation'">
					<validation-tab
						:validation-schema="localValidationSchema"
						:config-schema="localSchema"
						@update:validation-schema="handleValidationSchemaChange"
					/>
				</div>

				<!-- JSON编辑器 -->
				<div v-else-if="activeTabName === 'json-editor'">
					<div class="json-editor-layout">
						<div class="json-editor-panel">
							<div class="json-editor-tab-header">
								<div class="tab-buttons">
									<el-button
										:type="activeJsonTab === 'schema' ? 'primary' : 'default'"
										@click="activeJsonTab = 'schema'"
										>Form Schema</el-button
									>
									<el-button
										:type="activeJsonTab === 'uiSchema' ? 'primary' : 'default'"
										@click="activeJsonTab = 'uiSchema'"
										>UI Schema</el-button
									>
									<el-button
										:type="activeJsonTab === 'validationSchema' ? 'primary' : 'default'"
										@click="activeJsonTab = 'validationSchema'"
										>Validation Schema</el-button
									>
								</div>
							</div>

							<div v-if="activeJsonTab === 'schema'">
								<el-button type="primary" size="small" @click="formatJson('schema')">Format</el-button>
								<el-button type="success" size="small" @click="applyJsonChanges('schema')">Apply Changes</el-button>
								<div class="json-editor-container">
									<el-input
										v-model="schemaJson"
										type="textarea"
										:rows="20"
										placeholder="Edit Form Schema JSON"
										@input="onJsonChange('schema')"
									/>
								</div>
							</div>

							<div v-else-if="activeJsonTab === 'uiSchema'">
								<el-button type="primary" size="small" @click="formatJson('uiSchema')">Format</el-button>
								<el-button type="success" size="small" @click="applyJsonChanges('uiSchema')">Apply Changes</el-button>
								<div class="json-editor-container">
									<el-input
										v-model="uiSchemaJson"
										type="textarea"
										:rows="20"
										placeholder="Edit UI Schema JSON"
										@input="onJsonChange('uiSchema')"
									/>
								</div>
							</div>

							<div v-else-if="activeJsonTab === 'validationSchema'">
								<el-button type="primary" size="small" @click="formatJson('validationSchema')">Format</el-button>
								<el-button type="success" size="small" @click="applyJsonChanges('validationSchema')"
									>Apply Changes</el-button
								>
								<div class="json-editor-container">
									<el-input
										v-model="validationSchemaJson"
										type="textarea"
										:rows="20"
										placeholder="Edit Validation Schema JSON"
										@input="onJsonChange('validationSchema')"
									/>
								</div>
							</div>
						</div>
						<div class="json-preview-panel">
							<div class="json-preview-header">
								<h3>JSON Preview</h3>
							</div>
							<div class="json-preview-content">
								<pre>{{ formattedJsonPreview }}</pre>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- 右侧预览区域 -->
			<div class="preview-panel">
				<div class="preview-header">
					<h3>Form Preview</h3>
					<div class="preview-actions">
						<el-button type="primary" size="small" @click="syncPreview" :icon="RefreshRight" style="margin-right: 10px"
							>Sync Preview</el-button
						>
						<el-switch v-model="showPreview" active-text="Show Preview" inactive-text="Hide Preview" />
					</div>
				</div>

				<div v-if="showPreview" class="preview-content">
					<dynamic-form
						:schema="previewSchema"
						:ui-schema="previewUiSchema || defaultUiSchema"
						:validation-schema="previewValidationSchema || {}"
						:form-data="previewFormData"
						:key="previewKey"
						:lazy="true"
					/>
				</div>
				<div v-else class="preview-placeholder">
					<el-empty description="Preview Hidden" />
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { RefreshRight } from "@element-plus/icons-vue";
import DynamicForm from "@/components/DynamicForm.vue";
import FormStructureTab from "./FormStructureTab.vue";
import UiSettingsTab from "./UiSettingsTab.vue";
import ValidationTab from "./ValidationTab.vue";

// 定义属性
const props = defineProps({
	schema: {
		type: Object,
		required: true,
	},
	uiSchema: {
		type: Object,
		required: true,
	},
	validationSchema: {
		type: Object,
		required: true,
	},
});

// 定义事件
const emit = defineEmits(["update:schema", "update:uiSchema", "update:validationSchema", "schema-error"]);

// 本地状态
const localSchema = ref(JSON.parse(JSON.stringify(props.schema || {})));
const localUiSchema = ref(JSON.parse(JSON.stringify(props.uiSchema || {})));
const localValidationSchema = ref(JSON.parse(JSON.stringify(props.validationSchema || {})));

// 活动选项卡
const activeTabName = ref("form-structure");
const activeJsonTab = ref("schema");

// JSON编辑器相关状态
const schemaJson = ref("");
const uiSchemaJson = ref("");
const validationSchemaJson = ref("");
const jsonHasError = ref(false);
const jsonErrorMessage = ref("");

// Formatted JSON preview
const formattedJsonPreview = computed(() => {
	switch (activeJsonTab.value) {
		case "schema":
			return schemaJson.value ? formatJsonText(schemaJson.value) : "";
		case "uiSchema":
			return uiSchemaJson.value ? formatJsonText(uiSchemaJson.value) : "";
		case "validationSchema":
			return validationSchemaJson.value ? formatJsonText(validationSchemaJson.value) : "";
		default:
			return "";
	}
});

// Preview related
const showPreview = ref(true);
const previewFormData = ref({});
const previewKey = ref(0);
const previewSchema = ref({});
const previewUiSchema = ref({});
const previewValidationSchema = ref({});

// Default UI Schema
const defaultUiSchema = {
	layout: "tabs",
	theme: "dark",
	cssClasses: {
		formContainer: "game-form-container",
		section: "game-form-section",
		field: "game-form-field",
	},
	conditionalDisplay: [],
};

// Get all fields
const allFields = computed(() => {
	const fields = [];
	if (localSchema.value.components) {
		localSchema.value.components.forEach((section) => {
			if (section.fields) {
				section.fields.forEach((field) => {
					fields.push(field);
				});
			}
		});
	}
	return fields;
});

// Add debounce flags
const isUpdatingSchema = ref(false);
const isUpdatingUiSchema = ref(false);
const isUpdatingValidationSchema = ref(false);

// Watch Schema in props, update local data
watch(
	() => props.schema,
	(newVal) => {
		// Only update local state when value actually changes
		if (JSON.stringify(newVal) !== JSON.stringify(localSchema.value)) {
			isUpdatingSchema.value = true;
			localSchema.value = JSON.parse(JSON.stringify(newVal || {}));
			nextTick(() => {
				isUpdatingSchema.value = false;
			});
		}
	},
	{ immediate: true, deep: true },
);

// Watch UI Schema in props, update local data
watch(
	() => props.uiSchema,
	(newVal) => {
		// 只有当值真正变化时才更新本地状态
		if (JSON.stringify(newVal) !== JSON.stringify(localUiSchema.value)) {
			isUpdatingUiSchema.value = true;
			localUiSchema.value = JSON.parse(JSON.stringify(newVal || {}));
			nextTick(() => {
				isUpdatingUiSchema.value = false;
			});
		}
	},
	{ immediate: true, deep: true },
);

// Watch validation Schema in props, update local data
watch(
	() => props.validationSchema,
	(newVal) => {
		// 只有当值真正变化时才更新本地状态
		if (JSON.stringify(newVal) !== JSON.stringify(localValidationSchema.value)) {
			isUpdatingValidationSchema.value = true;
			localValidationSchema.value = JSON.parse(JSON.stringify(newVal || {}));
			nextTick(() => {
				isUpdatingValidationSchema.value = false;
			});
		}
	},
	{ immediate: true, deep: true },
);

// Watch local Schema changes, trigger update events
watch(
	() => localSchema.value,
	(newVal) => {
		// Only trigger events when value actually changes and not in update process
		if (!isUpdatingSchema.value && JSON.stringify(newVal) !== JSON.stringify(props.schema)) {
			emit("update:schema", JSON.parse(JSON.stringify(newVal)));
		}
	},
	{ deep: true },
);

// Watch local UI Schema changes, trigger update events
watch(
	() => localUiSchema.value,
	(newVal) => {
		// 只有当值真正变化且不在更新过程中时才触发事件
		if (!isUpdatingUiSchema.value && JSON.stringify(newVal) !== JSON.stringify(props.uiSchema)) {
			emit("update:uiSchema", JSON.parse(JSON.stringify(newVal)));
		}
	},
	{ deep: true },
);

// Watch local validation Schema changes, trigger update events
watch(
	() => localValidationSchema.value,
	(newVal) => {
		// 只有当值真正变化且不在更新过程中时才触发事件
		if (!isUpdatingValidationSchema.value && JSON.stringify(newVal) !== JSON.stringify(props.validationSchema)) {
			emit("update:validationSchema", JSON.parse(JSON.stringify(newVal)));
		}
	},
	{ deep: true },
);

// Initialize JSON editor content
watch(
	() => localSchema.value,
	(newVal) => {
		schemaJson.value = JSON.stringify(newVal, null, 2);
	},
	{ immediate: true, deep: true },
);

watch(
	() => localUiSchema.value,
	(newVal) => {
		uiSchemaJson.value = JSON.stringify(newVal, null, 2);
	},
	{ immediate: true, deep: true },
);

watch(
	() => localValidationSchema.value,
	(newVal) => {
		validationSchemaJson.value = JSON.stringify(newVal, null, 2);
	},
	{ immediate: true, deep: true },
);

// Handle Schema changes
function handleSchemaChange(schema) {
	localSchema.value = schema;
	emit("update:schema", JSON.parse(JSON.stringify(schema)));
	emit("schema-error", "");
}

// Handle UI Schema changes
function handleUiSchemaChange(uiSchema) {
	localUiSchema.value = uiSchema;
	emit("update:uiSchema", JSON.parse(JSON.stringify(uiSchema)));
}

// Handle validation Schema changes
function handleValidationSchemaChange(validationSchema) {
	localValidationSchema.value = validationSchema;
	emit("update:validationSchema", JSON.parse(JSON.stringify(validationSchema)));
}

// Format JSON
function formatJson(type: string) {
	try {
		switch (type) {
			case "schema":
				if (schemaJson.value) {
					const parsed = JSON.parse(schemaJson.value);
					schemaJson.value = JSON.stringify(parsed, null, 2);
				}
				break;
			case "uiSchema":
				if (uiSchemaJson.value) {
					const parsed = JSON.parse(uiSchemaJson.value);
					uiSchemaJson.value = JSON.stringify(parsed, null, 2);
				}
				break;
			case "validationSchema":
				if (validationSchemaJson.value) {
					const parsed = JSON.parse(validationSchemaJson.value);
					validationSchemaJson.value = JSON.stringify(parsed, null, 2);
				}
				break;
		}
		jsonHasError.value = false;
		jsonErrorMessage.value = "";
	} catch (error: any) {
		jsonHasError.value = true;
		jsonErrorMessage.value = error.message;
		ElMessage.error(`JSON formatting error: ${error.message}`);
	}
}

// Format JSON text for preview
function formatJsonText(jsonText: string) {
	try {
		const parsed = JSON.parse(jsonText);
		return JSON.stringify(parsed, null, 2);
	} catch (error) {
		return jsonText;
	}
}

// Handle JSON changes
function onJsonChange(type: string) {
	try {
		// Try to parse JSON, check if format is correct
		if (type === "schema" && schemaJson.value) {
			JSON.parse(schemaJson.value);
		} else if (type === "uiSchema" && uiSchemaJson.value) {
			JSON.parse(uiSchemaJson.value);
		} else if (type === "validationSchema" && validationSchemaJson.value) {
			JSON.parse(validationSchemaJson.value);
		}
		jsonHasError.value = false;
		jsonErrorMessage.value = "";
	} catch (error: any) {
		jsonHasError.value = true;
		jsonErrorMessage.value = error.message;
	}
}

// Apply JSON changes
function applyJsonChanges(type: string) {
	try {
		switch (type) {
			case "schema":
				if (schemaJson.value) {
					const parsed = JSON.parse(schemaJson.value);
					localSchema.value = parsed;
					handleSchemaChange(parsed);
					ElMessage.success("Form Schema updated");
				}
				break;
			case "uiSchema":
				if (uiSchemaJson.value) {
					const parsed = JSON.parse(uiSchemaJson.value);
					localUiSchema.value = parsed;
					handleUiSchemaChange(parsed);
					ElMessage.success("UI Schema updated");
				}
				break;
			case "validationSchema":
				if (validationSchemaJson.value) {
					const parsed = JSON.parse(validationSchemaJson.value);

					// Ensure validation rules structure is correct
					if (!parsed.rules) {
						parsed.rules = {};
					}

					// If root-level validation rules are found, move them to rules object
					Object.keys(parsed).forEach((key) => {
						if (key !== "rules" && Array.isArray(parsed[key])) {
							parsed.rules[key] = [...parsed[key]];
							delete parsed[key]; // Delete root-level rules
						}
					});

					localValidationSchema.value = parsed;
					handleValidationSchemaChange(parsed);
					ElMessage.success("Validation Schema updated");
				}
				break;
		}
	} catch (error: any) {
		ElMessage.error(`Failed to apply JSON changes: ${error.message}`);
	}
}

// Sync preview function
function syncPreview() {
	try {
		console.log("Starting preview sync...");
		// Deep copy schema
		const schemaClone = JSON.parse(JSON.stringify(localSchema.value));

		// Deep copy validation Schema
		const validationSchemaClone = JSON.parse(JSON.stringify(localValidationSchema.value));
		console.log("Original validation Schema:", validationSchemaClone);

		// Create normalized validation Schema (format to pass to DynamicForm)
		const normalizedValidationSchema = {};

		// Only extract validation rules from rules object
		if (validationSchemaClone.rules) {
			Object.keys(validationSchemaClone.rules).forEach((fieldName) => {
				if (Array.isArray(validationSchemaClone.rules[fieldName])) {
					normalizedValidationSchema[fieldName] = [...validationSchemaClone.rules[fieldName]];
				}
			});
		}

		console.log("Normalized validation Schema:", normalizedValidationSchema);

		// Update field required attributes based on validation rules
		if (schemaClone.components && Array.isArray(schemaClone.components)) {
			schemaClone.components.forEach((section) => {
				if (section.fields && Array.isArray(section.fields)) {
					section.fields.forEach((field) => {
						// Map "input" type to "text" type
						if (field.type === "input") {
							field.type = "text";
						}

						// Check if this field has required validation rules
						const rules = normalizedValidationSchema[field.name];
						if (Array.isArray(rules)) {
							// If any rule is required or required: true, mark field as required
							const hasRequiredRule = rules.some((rule) => rule.required === true || rule.type === "required");

							if (hasRequiredRule) {
								field.required = true;
								console.log(`Field ${field.name} marked as required`);
							}
						}
					});
				}
			});
		}

		// Deep copy and process uiSchema
		const uiSchemaClone = JSON.parse(JSON.stringify(localUiSchema.value));

		// Ensure cssClasses and conditionalDisplay properties exist
		if (!uiSchemaClone.cssClasses) {
			uiSchemaClone.cssClasses = {
				formContainer: "game-form-container",
				section: "game-form-section",
				field: "game-form-field",
			};
		}

		if (!uiSchemaClone.conditionalDisplay) {
			uiSchemaClone.conditionalDisplay = [];
		}

		// If conditionalRules exist, convert to conditionalDisplay format
		if (uiSchemaClone.conditionalRules && Array.isArray(uiSchemaClone.conditionalRules)) {
			uiSchemaClone.conditionalRules.forEach((rule) => {
				if (rule.sourceField && rule.targetField && rule.condition) {
					uiSchemaClone.conditionalDisplay.push({
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

		// Update preview data
		previewSchema.value = schemaClone;
		previewUiSchema.value = uiSchemaClone;
		previewValidationSchema.value = normalizedValidationSchema;

		// Increment key to force re-render
		previewKey.value = Date.now();

		console.log("Preview sync completed");
		ElMessage.success("Preview synced");
	} catch (error) {
		console.error("Preview sync error:", error);
		ElMessage.error(`Preview sync failed: ${error instanceof Error ? error.message : String(error)}`);
	}
}

// Ensure UI Schema is initialized when component is mounted
onMounted(() => {
	console.log("SchemaEditor component mounted", {
		props: {
			schema: props.schema,
			uiSchema: props.uiSchema,
			validationSchema: props.validationSchema,
		},
		local: {
			localSchema: localSchema.value,
			localUiSchema: localUiSchema.value,
			localValidationSchema: localValidationSchema.value,
		},
	});

	// Ensure local state is properly initialized
	if (props.schema && Object.keys(props.schema).length > 0) {
		localSchema.value = JSON.parse(JSON.stringify(props.schema));
		schemaJson.value = JSON.stringify(props.schema, null, 2);
	}

	if (props.uiSchema && Object.keys(props.uiSchema).length > 0) {
		localUiSchema.value = JSON.parse(JSON.stringify(props.uiSchema));
		uiSchemaJson.value = JSON.stringify(props.uiSchema, null, 2);
	} else {
		localUiSchema.value = { ...defaultUiSchema };
		uiSchemaJson.value = JSON.stringify(defaultUiSchema, null, 2);
	}

	if (props.validationSchema && Object.keys(props.validationSchema).length > 0) {
		localValidationSchema.value = JSON.parse(JSON.stringify(props.validationSchema));
		validationSchemaJson.value = JSON.stringify(props.validationSchema, null, 2);
	}

	// Initialize preview data
	syncPreview();
});
</script>

<style scoped lang="scss">
.schema-editor-container {
	border-radius: 4px;
	padding: 15px;
	margin-bottom: 20px;
	width: 100%;
}

.editor-layout {
	display: flex;
	gap: 20px;
	min-height: 600px;
}

.editor-panel {
	flex: 3;
	border-radius: 4px;
	box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
	overflow: auto;
}

.preview-panel {
	flex: 3;
	border-radius: 4px;
	box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
	overflow: auto;
	display: flex;
	flex-direction: column;
}

.preview-header {
	padding: 15px;
	border-bottom: 1px solid #ebeef5;
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.preview-header h3 {
	margin: 0;
	color: #409eff;
}

.preview-content {
	padding: 15px;
	flex: 1;
	overflow: auto;
}

.preview-placeholder {
	display: flex;
	justify-content: center;
	align-items: center;
	height: 300px;
}

/* JSON editor related styles */
.json-editor-layout {
	display: flex;
	gap: 20px;
	min-height: 600px;
}

.json-editor-panel {
	flex: 3;
	border-radius: 4px;
	box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.json-preview-panel {
	flex: 2;
	border-radius: 4px;
	box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
	overflow: auto;
	display: flex;
	flex-direction: column;
}

.json-preview-header {
	padding: 15px;
	border-bottom: 1px solid #ebeef5;
}

.json-preview-header h3 {
	margin: 0;
	color: #409eff;
}

.json-preview-content {
	padding: 15px;
	flex: 1;
	overflow: auto;
	border-radius: 0 0 4px 4px;
}

.json-preview-content pre {
	margin: 0;
	white-space: pre-wrap;
	word-wrap: break-word;
	font-family: monospace;
}

.json-editor-container {
	margin-top: 10px;
}

.tab-header {
	margin-bottom: 15px;
	border-bottom: 1px solid #e4e7ed;
	padding-bottom: 10px;
}

.tab-buttons {
	display: flex;
	gap: 10px;
}

.json-editor-tab-header {
	margin-bottom: 15px;
}

/* Responsive styles */
@media (max-width: 1200px) {
	.editor-layout {
		flex-direction: column;
	}

	.editor-panel,
	.preview-panel {
		flex: auto;
	}

	.json-editor-layout {
		flex-direction: column;
	}

	.json-editor-panel,
	.json-preview-panel {
		flex: auto;
	}
}
</style>
