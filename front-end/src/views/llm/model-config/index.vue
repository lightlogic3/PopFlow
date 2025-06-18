<script setup lang="ts">
import { ref, reactive, onMounted, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import {
	getModelConfigsByProvider,
	updateModelConfigStatus,
	deleteModelConfig,
	getModelConfigDetail,
	createModelConfig,
	updateModelConfig,
} from "@/api/llm_model_config_api";
import { Plus, Edit, Delete, ArrowLeft } from "@element-plus/icons-vue";
import ModelSelector from "@/components/ModelSelector/index.vue";

const router = useRouter();
const route = useRoute();
const providerId = ref<number>(parseInt(route.query.providerId as string) || 0);
const providerName = ref<string>((route.query.providerName as string) || "Unknown Provider");
const loading = ref(false);
const modelConfigs = ref<any[]>([]);

// Edit dialog related
const editDialogVisible = ref(false);
const configId = ref<number>(0);
const isEdit = ref(false);
const saving = ref(false);
const showModelSelector = ref(false);
const formRef = ref();

// Form data
const formData = reactive({
	id: 0,
	provider_id: providerId.value,
	model_name: "",
	model_id: "",
	model_type: "chat",
	capabilities: "",
	api_version: "",
	api_url: "",
	api_key: "",
	input_price: 0,
	output_price: 0,
	token_limit: 0,
	introduction: "",
	extra_params: "",
	status: 1,
	version: "",
	max_tokens: 4096,
	params: "",
});

// Form validation rules
const rules = reactive({
	model_id: [{ required: true, message: "Please enter model ID", trigger: "blur" }],
	model_type: [{ required: true, message: "Please select model type", trigger: "change" }],
	model_name: [{ required: true, message: "Please enter display name", trigger: "blur" }],
});

// Model type options
const modelTypeOptions = [
	{ value: "chat", label: "Conversation" },
	{ value: "multimodal", label: "Multimodal" },
];

const selectedModelInfo = reactive({
	id: "",
	name: "",
	type: "",
	provider: "",
	introduction: "",
	capabilities: [],
});

// Capability options
const capabilitiesOptions = [
	{
		value: "Function Call",
		label: "Function Call",
	},
	{
		value: "Role Playing",
		label: "Role Playing",
	},
	{
		value: "Deep Thinking",
		label: "Deep Thinking",
	},
	{
		value: "Code Generation",
		label: "Code Generation",
	},
	{
		value: "Image Understanding",
		label: "Image Understanding",
	},
];

// Capability multi-select values
const capabilitiesValue = ref<string[]>([]);

// Watch formData.capabilities changes, update capabilitiesValue
watch(
	() => formData.capabilities,
	(newVal) => {
		if (newVal) {
			capabilitiesValue.value = newVal.split(",").filter(Boolean);
		} else {
			capabilitiesValue.value = [];
		}
	},
	{ immediate: true },
);

// Watch capabilitiesValue changes, update formData.capabilities
watch(
	() => capabilitiesValue.value,
	(newVal) => {
		formData.capabilities = newVal.join(",");
	},
	{ deep: true },
);

const fetchModelConfigs = async () => {
	if (!providerId.value) {
		ElMessage.error("Provider ID cannot be empty");
		return;
	}

	loading.value = true;
	try {
		const response = await getModelConfigsByProvider(providerId.value);
		if (response && Array.isArray(response)) {
			modelConfigs.value = response;
		} else {
			modelConfigs.value = [];
		}
	} catch (error) {
		console.error("Failed to get model configuration list", error);
		ElMessage.error("Failed to get model configuration list");
		modelConfigs.value = [];
	} finally {
		loading.value = false;
	}
};

const handleEdit = (id: number) => {
	configId.value = id;
	isEdit.value = true;
	resetForm();
	fetchModelConfig(id);
	editDialogVisible.value = true;
};

const handleAdd = () => {
	configId.value = 0;
	isEdit.value = false;
	resetForm();
	formData.provider_id = providerId.value;
	editDialogVisible.value = true;
};

const resetForm = () => {
	if (formRef.value) {
		formRef.value.resetFields();
	}
	Object.assign(formData, {
		id: 0,
		provider_id: providerId.value,
		model_name: "",
		model_id: "",
		model_type: "chat",
		capabilities: "",
		api_version: "",
		api_url: "",
		api_key: "",
		input_price: 0,
		output_price: 0,
		token_limit: 0,
		introduction: "",
		extra_params: "",
		status: 1,
		version: "",
		max_tokens: 4096,
		params: "",
	});

	// Reset capabilities multi-select values
	capabilitiesValue.value = [];

	// Reset selected model information
	Object.assign(selectedModelInfo, {
		id: "",
		name: "",
		type: "",
		provider: "",
		introduction: "",
		capabilities: [],
	});
};

// Load model configuration details
const fetchModelConfig = async (id: number) => {
	loading.value = true;
	try {
		const response = await getModelConfigDetail(id);
		if (response) {
			if (response.params && typeof response.params === "object") {
				response.params = JSON.stringify(response.params);
			}
			Object.assign(formData, response);

			// Update selected model information card
			selectedModelInfo.id = response.model_id;
			selectedModelInfo.name = response.model_name;
			selectedModelInfo.type = response.model_type;
			selectedModelInfo.introduction = response.introduction;

			// Parse capabilities
			if (response.capabilities) {
				const caps = response.capabilities.split(",").filter(Boolean);
				selectedModelInfo.capabilities = caps;
				capabilitiesValue.value = caps; // Update multi-select values
			} else {
				capabilitiesValue.value = [];
			}
		}
	} catch (error) {
		console.error("Failed to get model configuration details", error);
		ElMessage.error("Failed to get model configuration details");
	} finally {
		loading.value = false;
	}
};

// Save model configuration
const saveModelConfig = async () => {
	if (!formRef.value) return;

	await formRef.value.validate(async (valid) => {
		if (!valid) {
			return;
		}

		saving.value = true;
		try {
			const submitData: any = { ...formData };
			if (submitData.params) {
				try {
					submitData.params = JSON.parse(submitData.params);
				} catch (e) {
					ElMessage.error("Parameter format is incorrect, please enter valid JSON");
					saving.value = false;
					return;
				}
			} else {
				submitData.params = {};
			}

			if (isEdit.value) {
				await updateModelConfig(submitData.id, submitData);
				ElMessage.success("Update successful");
			} else {
				await createModelConfig(submitData);
				ElMessage.success("Creation successful");
			}
			editDialogVisible.value = false;
			fetchModelConfigs(); // Refresh list
		} catch (error) {
			console.error(isEdit.value ? "Failed to update model configuration" : "Failed to create model configuration", error);
			ElMessage.error(isEdit.value ? "Failed to update model configuration" : "Failed to create model configuration");
		} finally {
			saving.value = false;
		}
	});
};

const handleDelete = (id: number) => {
	ElMessageBox.confirm("Are you sure you want to delete this model configuration?", "Prompt", {
		confirmButtonText: "Confirm",
		cancelButtonText: "Cancel",
		type: "warning",
	})
		.then(async () => {
			try {
				await deleteModelConfig(id);
				ElMessage.success("Delete successful");
				fetchModelConfigs();
			} catch (error) {
				console.error("Delete failed", error);
				ElMessage.error("Delete failed");
			}
		})
		.catch(() => {
			// User cancelled operation
		});
};

const toggleStatus = async (config: any) => {
	const newStatus = config.status === 1 ? 0 : 1;
	try {
		await updateModelConfigStatus(config.id, newStatus);
		ElMessage.success(`${newStatus === 1 ? "Enable" : "Disable"} successful`);
		// Update local status
		config.status = newStatus;
	} catch (error) {
		console.error("Status update failed", error);
		ElMessage.error("Status update failed");
	}
};

const goBack = () => {
	router.push("/llm/list");
};

const getStatusClass = (status: number) => {
	return status === 1 ? "status-active" : "status-inactive";
};

const getStatusText = (status: number) => {
	return status === 1 ? "Enabled" : "Disabled";
};

const getModelTypeText = (type: string) => {
	switch (type) {
		case "chat":
			return "Conversation";
		case "multimodal":
			return "Multimodal";
		default:
			return type || "Unknown";
	}
};

// Open model selector
const openModelSelector = () => {
	showModelSelector.value = true;
};

// Model selection callback
const handleModelSelect = (modelInfo: any) => {
	console.log("Selected model information:", modelInfo);

	// Update selected model information card
	selectedModelInfo.id = modelInfo.model_id || modelInfo.model_name;
	selectedModelInfo.name = modelInfo.model_name;
	selectedModelInfo.type = modelInfo.model_type;
	selectedModelInfo.provider = modelInfo.vendor;
	selectedModelInfo.introduction = modelInfo.introduction || modelInfo.introduction;

	// Handle capabilities
	let capabilitiesArray: string[] = [];
	if (typeof modelInfo.capabilities === "string") {
		capabilitiesArray = modelInfo.capabilities.split(",").filter(Boolean);
	} else if (Array.isArray(modelInfo.capabilities)) {
		capabilitiesArray = modelInfo.capabilities;
	}
	selectedModelInfo.capabilities = capabilitiesArray;

	// Update capabilitiesValue
	capabilitiesValue.value = capabilitiesArray;

	// Fill model information into form
	formData.model_id = selectedModelInfo.id;
	formData.model_name = selectedModelInfo.name;
	formData.introduction = selectedModelInfo.introduction;
	formData.model_type = selectedModelInfo.type;
	formData.capabilities = capabilitiesArray.join(",");
	formData.version = modelInfo.model_version;

	// If user hasn't filled in display name, use model name
	if (!formData.model_name) {
		formData.model_name = formData.model_id;
	}
};

onMounted(() => {
	fetchModelConfigs();
});
</script>

<template>
	<div class="model-config-container">
		<div class="model-config-header">
			<div class="header-left">
				<el-button plain @click="goBack">
					<el-icon><ArrowLeft /></el-icon>
					Back
				</el-button>
				<h1 class="title">{{ providerName }} - Model Configuration</h1>
			</div>
			<el-button type="primary" size="small" @click="handleAdd">
				<el-icon><Plus /></el-icon>
				Add Model Configuration
			</el-button>
		</div>

		<div class="model-config-grid" v-loading="loading">
			<el-empty v-if="modelConfigs.length === 0" description="No model configuration data" size="small" />
			<el-card v-for="config in modelConfigs" :key="config.id" class="model-config-card" shadow="hover">
				<div class="model-config-header">
					<h3 class="model-config-name">{{ config.model_name || config.model_id }}</h3>
					<el-tag
						:type="config.status === 1 ? 'success' : 'danger'"
						effect="light"
						@click="toggleStatus(config)"
						class="model-config-status"
						:class="getStatusClass(config.status)"
						style="cursor: pointer"
					>
						{{ getStatusText(config.status) }}
					</el-tag>
				</div>
				<div class="model-config-info">
					<div class="info-item">
						<span class="info-label">Model ID:</span>
						<span>{{ config.model_id }}</span>
					</div>
					<div class="info-item">
						<span class="info-label">Type:</span>
						<span>{{ getModelTypeText(config.model_type) }}</span>
					</div>
					<div class="info-item">
						<span class="info-label">Features:</span>
						<span class="capabilities-container">
							<template v-if="config.capabilities">
								<el-tag
									v-for="cap in config.capabilities.split(',').filter(Boolean).slice(0, 2)"
									:key="cap"
									size="small"
									class="capability-tag"
								>
									{{ cap }}
								</el-tag>
								<el-tag size="small" type="info" v-if="config.capabilities.split(',').filter(Boolean).length > 2">
									+{{ config.capabilities.split(",").filter(Boolean).length - 2 }}
								</el-tag>
							</template>
							<span v-else>Not set</span>
						</span>
					</div>
					<div class="info-item">
						<span class="info-label">Input Price:</span>
						<span>{{ config.input_price }} / 1K tokens</span>
					</div>
					<div class="info-item">
						<span class="info-label">Output Price:</span>
						<span>{{ config.output_price }} / 1K tokens</span>
					</div>
				</div>
				<div class="model-config-introduction" v-if="config.introduction">
					{{ config.introduction }}
				</div>
				<template #footer>
					<div class="model-config-actions">
						<el-button type="primary" size="small" @click="handleEdit(config.id)">
							<el-icon><Edit /></el-icon>
							Edit
						</el-button>
						<el-button type="danger" size="small" @click="handleDelete(config.id)">
							<el-icon><Delete /></el-icon>
							Delete
						</el-button>
					</div>
				</template>
			</el-card>
		</div>

		<!-- Model configuration edit dialog -->
		<el-dialog
			:title="isEdit ? 'Edit Model Configuration' : 'Add Model Configuration'"
			v-model="editDialogVisible"
			width="70%"
			destroy-on-close
			:close-on-click-modal="false"
		>
			<!-- Model selection card area -->
			<div class="model-card-section">
				<div class="section-title">Select Model:</div>
				<div class="model-cards">
					<div
						class="model-card"
						:class="{ selected: formData.model_id === selectedModelInfo.id }"
						@click="openModelSelector"
					>
						<div class="model-card-header">
							<img class="model-logo" src="@/assets/images/model-logos/baidu.svg" alt="Wenxin" />
							<div class="model-card-type">
								<el-tag size="small" type="success" v-if="selectedModelInfo.type === 'multimodal'">Multimodal</el-tag>
								<el-tag size="small" type="info" v-else>Conversation</el-tag>
							</div>
						</div>
						<div class="model-card-body">
							<div class="model-card-name">{{ selectedModelInfo.name || "Wenxin Large Model" }}</div>
							<div class="model-card-id">{{ selectedModelInfo.id || "Ernie-Bot-4" }}</div>

							<div
								class="model-capabilities"
								v-if="selectedModelInfo.capabilities && selectedModelInfo.capabilities.length > 0"
							>
								<el-tag
									v-for="cap in selectedModelInfo.capabilities.slice(0, 2)"
									:key="cap"
									size="small"
									class="capability-tag"
								>
									{{ cap }}
								</el-tag>
								<el-tag size="small" type="info" v-if="selectedModelInfo.capabilities.length > 2">
									+{{ selectedModelInfo.capabilities.length - 2 }}
								</el-tag>
							</div>
						</div>
						<div class="model-card-footer">
							<span class="provider-name">{{ selectedModelInfo.provider || "Baidu" }}</span>
						</div>
					</div>
					<div class="model-card add-card" @click="openModelSelector">
						<el-icon><Plus /></el-icon>
						<span>More Models</span>
					</div>
				</div>
			</div>

			<el-form
				ref="formRef"
				:model="formData"
				:rules="rules"
				label-width="100px"
				size="small"
				class="model-config-form"
			>
				<el-tabs>
					<el-tab-pane label="Basic Information">
						<el-form-item label="Model ID" prop="model_id">
							<el-input v-model="formData.model_id" placeholder="Please enter model ID" :disabled="isEdit" />
						</el-form-item>

						<el-form-item label="Display Name" prop="model_name">
							<el-input v-model="formData.model_name" placeholder="Please enter display name, if empty will use model ID" />
						</el-form-item>

						<el-form-item label="Model Type" prop="model_type">
							<el-select v-model="formData.model_type" placeholder="Please select model type">
								<el-option
									v-for="option in modelTypeOptions"
									:key="option.value"
									:label="option.label"
									:value="option.value"
								/>
							</el-select>
						</el-form-item>

						<el-form-item label="Model Version" prop="version">
							<el-input v-model="formData.version" placeholder="Please enter model version" />
						</el-form-item>

						<el-form-item label="Max Tokens" prop="max_tokens">
							<el-input-number v-model="formData.max_tokens" :min="0" :step="1" placeholder="Maximum tokens supported by the model" />
						</el-form-item>

						<el-form-item label="Features" prop="capabilities">
							<el-select
								v-model="capabilitiesValue"
								multiple
								filterable
								allow-create
								default-first-option
								:reserve-keyword="false"
								placeholder="Select or add features supported by the model"
								style="width: 100%"
							>
								<el-option
									v-for="item in capabilitiesOptions"
									:key="item.value"
									:label="item.label"
									:value="item.value"
								/>
							</el-select>
						</el-form-item>
					</el-tab-pane>

					<el-tab-pane label="Price and Description">
						<el-form-item label="Input Price" prop="input_price">
							<el-input-number
								v-model="formData.input_price"
								:precision="4"
								:step="0.0001"
								:min="0"
								placeholder="Price per thousand characters input"
							/>
						</el-form-item>

						<el-form-item label="Output Price" prop="output_price">
							<el-input-number
								v-model="formData.output_price"
								:precision="4"
								:step="0.0001"
								:min="0"
								placeholder="Price per thousand characters output"
							/>
						</el-form-item>

						<el-form-item label="Description" prop="introduction">
							<el-input v-model="formData.introduction" type="textarea" :rows="3" placeholder="Please enter model description" />
						</el-form-item>

						<el-form-item label="Status">
							<el-switch
								v-model="formData.status"
								:active-value="1"
								:inactive-value="0"
								active-text="Enable"
								inactive-text="Disable"
							/>
						</el-form-item>
					</el-tab-pane>

					<el-tab-pane label="Advanced Configuration">
						<el-form-item label="Parameter Config" prop="params">
							<el-input
								v-model="formData.params"
								type="textarea"
								:rows="6"
								placeholder="Please enter JSON format parameter configuration (optional)"
							/>
							<div class="form-help-text">
								Parameter configuration supports JSON format, used to set default parameters for the model, for example:<br />
								{"temperature": 0.7, "top_p": 1, "frequency_penalty": 0, "presence_penalty": 0}
							</div>
						</el-form-item>
					</el-tab-pane>
				</el-tabs>
			</el-form>

			<template #footer>
				<span class="dialog-footer">
					<el-button size="small" @click="editDialogVisible = false">Cancel</el-button>
					<el-button type="primary" size="small" :loading="saving" @click="saveModelConfig">Save</el-button>
				</span>
			</template>
		</el-dialog>

		<!-- Model selector -->
		<ModelSelector
			v-model:visible="showModelSelector"
			@confirm="handleModelSelect"
			@cancel="() => console.log('Model selection canceled')"
		/>
	</div>
</template>

<style scoped>
.model-config-container {
	padding: 16px;
}

.model-config-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 20px;
}

.header-left {
	display: flex;
	align-items: center;
	gap: 12px;
}

.title {
	font-size: 20px;
	margin: 0;
	color: var(--el-text-color-primary);
}

.model-config-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
	gap: 16px;
}

.model-config-card {
	margin-bottom: 4px;
	transition: all 0.3s;
}

.model-config-card:hover {
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.model-config-header {
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
	margin-bottom: 12px;
}

.model-config-name {
	font-size: 16px;
	color: var(--el-text-color-primary);
	margin: 0;
}

.model-config-status {
	font-size: 12px;
}

.status-active {
	background-color: var(--el-color-success-light-9);
}

.status-inactive {
	background-color: var(--el-color-danger-light-9);
}

.model-config-info {
	margin-bottom: 12px;
}

.info-item {
	display: flex;
	align-items: flex-start;
	margin-bottom: 6px;
	font-size: 13px;
	color: var(--el-text-color-secondary);
}

.info-label {
	min-width: 70px;
	color: var(--el-text-color-primary);
}

.model-config-introduction {
	background: var(--el-fill-color-light);
	border-radius: 4px;
	padding: 8px;
	margin-bottom: 12px;
	font-size: 13px;
	line-height: 1.4;
	height: 26px;
	color: var(--el-text-color-secondary);
	overflow: hidden;
}

.model-config-actions {
	display: flex;
	justify-content: flex-end;
	gap: 6px;
}

.model-id-input {
	display: flex;
	gap: 10px;
}

.model-config-form {
	padding: 20px 0;
}

.form-help-text {
	font-size: 12px;
	color: var(--el-text-color-secondary);
	line-height: 1.5;
	margin-top: 5px;
}

.model-card-section {
	margin-bottom: 20px;
	border-bottom: 1px solid var(--el-border-color-light);
	padding-bottom: 20px;
}

.section-title {
	font-size: 16px;
	font-weight: 500;
	margin-bottom: 16px;
	color: var(--el-text-color-primary);
}

.model-cards {
	display: flex;
	flex-wrap: wrap;
	gap: 16px;
}

.model-card {
	width: 180px;
	height: 160px;
	border: 1px solid var(--el-border-color);
	border-radius: 8px;
	padding: 12px;
	cursor: pointer;
	transition: all 0.3s;
	display: flex;
	flex-direction: column;
	position: relative;
	background-color: var(--el-bg-color);
}

.model-card:hover {
	transform: translateY(-3px);
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
	border-color: var(--el-color-primary-light-5);
}

.model-card.selected {
	border-color: var(--el-color-primary);
	box-shadow: 0 0 0 2px var(--el-color-primary-light-8);
}

.model-card-header {
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
	margin-bottom: 12px;
}

.model-logo {
	width: 32px;
	height: 32px;
	border-radius: 4px;
	object-fit: cover;
}

.model-card-type {
	display: flex;
	align-items: center;
}

.model-card-body {
	flex: 1;
	display: flex;
	flex-direction: column;
	justify-content: center;
}

.model-card-name {
	font-size: 16px;
	font-weight: 500;
	color: var(--el-text-color-primary);
	margin-bottom: 4px;
}

.model-card-id {
	font-size: 12px;
	color: var(--el-text-color-secondary);
	margin-bottom: 8px;
}

.model-card-footer {
	font-size: 12px;
	color: var(--el-text-color-secondary);
}

.provider-name {
	background-color: var(--el-fill-color-light);
	padding: 2px 6px;
	border-radius: 4px;
}

.add-card {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	color: var(--el-text-color-secondary);
	background-color: var(--el-fill-color-lighter);
	border-style: dashed;
}

.add-card:hover {
	color: var(--el-color-primary);
	border-color: var(--el-color-primary);
	background-color: var(--el-color-primary-light-9);
}

.add-card .el-icon {
	font-size: 24px;
	margin-bottom: 8px;
}

.model-capabilities {
	margin-top: 8px;
	display: flex;
	flex-wrap: wrap;
	gap: 4px;
}

.capability-tag {
	margin-right: 4px;
	margin-bottom: 4px;
	white-space: nowrap;
}

.capabilities-container {
	display: flex;
	flex-wrap: wrap;
	gap: 4px;
	align-items: center;
}
</style>
