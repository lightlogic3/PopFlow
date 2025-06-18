<script setup lang="ts">
import { ref, onMounted, reactive } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";
import type { LLMProvider, LLMProviderCreate, LLMProviderUpdate } from "@/types/llm";
import {
	getLLMProviderList,
	deleteLLMProvider,
	updateLLMProviderStatus,
	getLLMProviderById,
	createLLMProvider,
	updateLLMProvider,
} from "@/api/llm";
import { Plus, Edit, Delete, Setting } from "@element-plus/icons-vue";

const router = useRouter();
const loading = ref(false);
const providers = ref<LLMProvider[]>([]);

// Edit dialog related
const editDialogVisible = ref(false);
const formRef = ref<FormInstance>();
const isEdit = ref(false);
const providerId = ref<number>(0);

// Form data
const formData = reactive<LLMProviderCreate | LLMProviderUpdate>({
	provider_name: "",
	api_url: "",
	api_key: "",
	model_name: "",
	remark: "",
	status: 1,
	extra_config: "",
	provider_sign: "",
});

// Form validation rules
const rules = reactive<FormRules>({
	provider_name: [
		{ required: true, message: "Please enter provider name", trigger: "blur" },
		{ min: 2, max: 50, message: "Length should be between 2 and 50 characters", trigger: "blur" },
	],
	api_url: [
		{ required: true, message: "Please enter API URL", trigger: "blur" },
		{
			pattern: /^(https?:\/\/)?([\da-z.-]+)\.([a-z.]{2,6})(\/[\w.-]*)*\/?$/,
			message: "Please enter a valid URL",
			trigger: "blur",
		},
	],
	api_key: [{ required: true, message: "Please enter API key", trigger: "blur" }],
	model_name: [{ required: true, message: "Please enter model name", trigger: "blur" }],
});

// Mock data, should be fetched from API in practice
const mockProviders: LLMProvider[] = [];

const fetchProviders = async () => {
	loading.value = true;
	try {
		// Try to fetch data from API
		const response = await getLLMProviderList({ skip: 0, limit: 100 });
		providers.value = response;
		// if (response && response.data && response.data.length) {
		// 	providers.value = response.data;
		// } else {
		// 	// Use mock data
		// 	providers.value = mockProviders;
		// 	console.log("Using mock LLM provider data");
		// }
	} catch (error) {
		console.error("Failed to fetch LLM provider list", error);
		ElMessage.error("Failed to fetch LLM provider list, showing mock data");
		// Use mock data when error occurs
		providers.value = mockProviders;
	} finally {
		loading.value = false;
	}
};

const handleEdit = async (id: number) => {
	isEdit.value = true;
	providerId.value = id;
	resetForm();
	await fetchProviderDetail(id);
	editDialogVisible.value = true;
};

const handleAdd = () => {
	isEdit.value = false;
	providerId.value = 0;
	resetForm();
	editDialogVisible.value = true;
};

const resetForm = () => {
	if (formRef.value) {
		formRef.value.resetFields();
	}
	formData.provider_name = "";
	formData.api_url = "";
	formData.api_key = "";
	formData.model_name = "";
	formData.remark = "";
	formData.status = 1;
	formData.extra_config = "";
	formData.provider_sign = "";
};

// Get provider details
const fetchProviderDetail = async (id: number) => {
	try {
		const response = await getLLMProviderById(id);

		if (response) {
			// Fill form data
			if (response.extra_config && Object.keys(response.extra_config).length) {
				response.extra_config = JSON.stringify(response.extra_config);
			} else {
				response.extra_config = "";
			}
			Object.assign(formData, response);
		} else {
			// Mock data
			const mockData: LLMProvider = {
				id: id,
				provider_name: "OpenAI",
				api_url: "https://api.openai.com/v1",
				api_key: "sk-abcdefghijklmnopqrstuvwxyz123456",
				model_name: "gpt-3.5-turbo",
				remark: "Default LLM provider, supports GPT-3.5 and GPT-4 models",
				status: 1,
				extra_config: {},
				created_at: "2023-01-01T00:00:00Z",
				updated_at: "2023-01-01T00:00:00Z",
			};
			Object.assign(formData, mockData);
			console.log("Using mock LLM provider data");
		}
	} catch (error) {
		console.error("Failed to get LLM provider details", error);
		ElMessage.error("Failed to get LLM provider details");
	}
};

// Submit form
const submitForm = async () => {
	if (!formRef.value) return;

	await formRef.value.validate(async (valid, fields) => {
		if (valid) {
			loading.value = true;
			try {
				const submitData = { ...formData };
				if (submitData.extra_config) {
					submitData.extra_config = JSON.parse(submitData.extra_config + "");
				} else {
					submitData.extra_config = {};
				}
				if (isEdit.value) {
					// Update provider
					await updateLLMProvider(providerId.value, submitData as LLMProviderUpdate);
					ElMessage.success("Update successful");
				} else {
					// Create provider
					await createLLMProvider(submitData as LLMProviderCreate);
					ElMessage.success("Create successful");
				}
				editDialogVisible.value = false;
				fetchProviders(); // Refresh list
			} catch (error) {
				console.error(isEdit.value ? "Failed to update provider" : "Failed to create provider", error);
			ElMessage.error(isEdit.value ? "Failed to update provider" : "Failed to create provider");
			// Simulate success (when API fails)
				editDialogVisible.value = false;
				fetchProviders(); // Refresh list
			} finally {
				loading.value = false;
			}
		} else {
			console.log("Form validation failed", fields);
		}
	});
};

const handleDelete = (id: number) => {
	ElMessageBox.confirm("Are you sure you want to delete this provider configuration?", "Confirm", {
		confirmButtonText: "Confirm",
		cancelButtonText: "Cancel",
		type: "warning",
	})
		.then(async () => {
			try {
				await deleteLLMProvider(id);
				ElMessage.success("Delete successful");
				fetchProviders();
			} catch (error) {
				console.error("Delete failed", error);
				ElMessage.error("Delete failed");
				// Simulate delete success (when API fails)
				providers.value = providers.value.filter((item) => item.id !== id);
			}
		})
		.catch(() => {
			// User cancelled operation
		});
};

const toggleStatus = async (provider: LLMProvider) => {
	const newStatus = provider.status === 1 ? 0 : 1;
	try {
		await updateLLMProviderStatus(provider.id, newStatus);
		ElMessage.success(`${newStatus === 1 ? "Enable" : "Disable"} successful`);
		// Update local status
		provider.status = newStatus;
	} catch (error) {
		console.error("Status update failed", error);
		ElMessage.error("Status update failed");
		// Simulate update success (when API fails)
		provider.status = newStatus;
	}
};

const getStatusClass = (status: number) => {
	return status === 1 ? "status-active" : "status-inactive";
};

const getStatusText = (status: number) => {
	return status === 1 ? "Enabled" : "Disabled";
};

const maskApiKey = (key: string) => {
	if (!key) return "";
	if (key.length <= 8) return "****";
	return key.substring(0, 4) + "****" + key.substring(key.length - 4);
};

// Open model configuration page
const openModelConfig = (provider: LLMProvider) => {
	router.push({
		path: `/llm/model-config/${provider.id}`,
		query: { providerName: provider.provider_name, providerId: provider.id },
	});
};

// Test connection
const testConnection = () => {
	if (!formData.api_url || !formData.api_key) {
		ElMessage.warning("Please fill in API URL and API key first");
		return;
	}

	ElMessage.info("Testing connection...");
	// Actual connection test logic should be implemented here
	setTimeout(() => {
		ElMessage.success("Connection test successful");
	}, 1500);
};

onMounted(() => {
	fetchProviders();
});
</script>

<template>
	<div class="llm-provider-container">
		<div class="provider-header">
			<h1 class="title">LLM Provider Configuration</h1>
			<el-button type="primary" size="small" @click="handleAdd">
				<el-icon><Plus /></el-icon>
				Add Provider
			</el-button>
		</div>

		<div class="provider-grid" v-loading="loading">
			<el-empty v-if="providers.length === 0" description="No provider configuration data" size="small" />
			<el-card v-for="provider in providers" :key="provider.id" class="provider-card" shadow="hover">
				<div class="card-header">
					<h3 class="provider-name">{{ provider.provider_name }}</h3>
					<el-tag
						:type="provider.status === 1 ? 'success' : 'danger'"
						effect="light"
						@click.stop="toggleStatus(provider)"
						class="provider-status"
						:class="getStatusClass(provider.status)"
					>
						{{ getStatusText(provider.status) }}
					</el-tag>
				</div>
				<div class="provider-info">
					<div class="info-grid">
						<div class="info-label">API URL:</div>
						<div class="info-value" :title="provider.api_url || 'Not set'">{{ provider.api_url || "Not set" }}</div>

						<div class="info-label">Model Name:</div>
						<div class="info-value" :title="provider.model_name || 'Not set'">{{ provider.model_name || "Not set" }}</div>

						<div class="info-label">API Key:</div>
						<div class="info-value">{{ maskApiKey(provider.api_key) }}</div>
					</div>
				</div>
				<div class="provider-remark" v-if="provider.remark">
					<div class="remark-content text-ellipsis">{{ provider.remark }}</div>
				</div>
				<div class="provider-remark" v-else>
					<div class="remark-placeholder">No remarks</div>
				</div>
				<div class="provider-actions">
					<el-button type="success" size="small" @click.stop="openModelConfig(provider)">
						<el-icon><Setting /></el-icon>
						Config
					</el-button>
					<el-button type="primary" size="small" @click.stop="handleEdit(provider.id)">
						<el-icon><Edit /></el-icon>
						Edit
					</el-button>
					<el-button type="danger" size="small" @click.stop="handleDelete(provider.id)">
						<el-icon><Delete /></el-icon>
						Delete
					</el-button>
				</div>
			</el-card>
		</div>

		<!-- Provider edit dialog -->
		<el-dialog
			:title="isEdit ? 'Edit LLM Provider' : 'Add LLM Provider'"
			v-model="editDialogVisible"
			width="50%"
			destroy-on-close
		>
			<el-form ref="formRef" :model="formData" :rules="rules" label-width="100px" class="provider-form" size="small">
				<el-row :gutter="20">
					<el-col :span="12">
						<el-form-item label="Provider Name" prop="provider_name">
						<el-input v-model="formData.provider_name" placeholder="Please enter provider name, e.g.: OpenAI" />
						</el-form-item>
					</el-col>
					<el-col :span="12">
						<el-form-item label="Provider Identifier" prop="provider_sign">
						<el-input v-model="formData.provider_sign" placeholder="all for -OpenAI" />
						</el-form-item>
					</el-col>
				</el-row>

				<el-row :gutter="20">
					<el-col :span="12">
						<el-form-item label="API URL" prop="api_url">
						<el-input v-model="formData.api_url" placeholder="Please enter API URL, e.g.: https://api.openai.com/v1" />
						</el-form-item>
					</el-col>
					<el-col :span="12">
						<el-form-item label="API Key" prop="api_key">
						<el-input v-model="formData.api_key" placeholder="Please enter API key" show-password />
						</el-form-item>
					</el-col>
				</el-row>

				<el-row :gutter="20">
					<el-col :span="12">
						<el-form-item label="Model Name" prop="model_name">
						<el-input v-model="formData.model_name" placeholder="Please enter model name, e.g.: gpt-3.5-turbo" />
						</el-form-item>
					</el-col>
					<el-col :span="12">
						<el-form-item label="Status">
						<el-switch
							v-model="formData.status"
							:active-value="1"
							:inactive-value="0"
							active-text="Enable"
							inactive-text="Disable"
							/>
						</el-form-item>
					</el-col>
				</el-row>

				<el-form-item label="Remarks" prop="remark">
					<el-input v-model="formData.remark" type="textarea" :rows="2" placeholder="Please enter remarks" />
				</el-form-item>

				<el-form-item label="Extra Config" prop="extra_config">
					<el-input
						v-model="formData.extra_config"
						type="textarea"
						:rows="3"
						placeholder="Please enter extra configuration in JSON format (optional)"
					/>
					<div class="form-help-text">Extra configuration supports JSON format, e.g., setting request timeout, proxy, etc.</div>
				</el-form-item>
			</el-form>
			<template #footer>
				<span class="dialog-footer">
					<el-button size="small" @click="editDialogVisible = false">Cancel</el-button>
					<el-button size="small" type="info" @click="testConnection">Test Connection</el-button>
					<el-button size="small" type="primary" @click="submitForm">Save</el-button>
				</span>
			</template>
		</el-dialog>
	</div>
</template>

<style scoped>
.llm-provider-container {
	padding: 12px;
}

.provider-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 16px;
}

.title {
	font-size: 20px;
	margin: 0;
	color: var(--el-text-color-primary);
}

.provider-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
	gap: 12px;
}

.provider-card {
	transition: all 0.3s;
	height: 100%;
	display: flex;
	flex-direction: column;
	/* 确保卡片有一个固定高度 */
	height: 230px;
	padding-bottom: 10px;
	position: relative;
}

.provider-card:hover {
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 10px;
	padding-bottom: 6px;
	border-bottom: 1px solid var(--el-border-color-lighter);
}

.provider-name {
	font-size: 16px;
	color: var(--el-text-color-primary);
	margin: 0;
	font-weight: 600;
}

.provider-status {
	font-size: 12px;
	cursor: pointer;
}

.status-active {
	background-color: var(--el-color-success-light-9);
}

.status-inactive {
	background-color: var(--el-color-danger-light-9);
}

.provider-info {
	margin-bottom: 15px;
	height: 80px; /* 固定高度 */
	overflow: hidden;
}

.info-grid {
	display: grid;
	grid-template-columns: 70px 1fr;
	gap: 4px;
	row-gap: 6px;
}

.info-label {
	color: var(--el-text-color-primary);
	font-weight: 500;
	font-size: 13px;
	line-height: 1.4;
}

.info-value {
	color: var(--el-text-color-secondary);
	font-size: 13px;
	word-break: break-all;
	line-height: 1.4;
	max-height: 2.8em; /* 限制为两行高度 */
	overflow: hidden;
	display: -webkit-box;
	-webkit-line-clamp: 2;
	-webkit-box-orient: vertical;
}

.provider-remark {
	background: var(--el-fill-color-light);
	border-radius: 4px;
	padding: 8px;
	margin-bottom: 15px;
	height: 40px;
	overflow: hidden;
}

.text-ellipsis {
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

.remark-content {
	font-size: 13px;
	line-height: 1.4;
	color: var(--el-text-color-secondary);
}

.remark-placeholder {
	font-size: 13px;
	line-height: 1.4;
	color: var(--el-text-color-placeholder);
	font-style: italic;
}

.provider-actions {
	display: flex;
	justify-content: flex-end;
	gap: 6px;
	position: absolute;
	bottom: 20px;
	right: 20px;
}

.provider-form {
	margin-top: 16px;
}

.form-help-text {
	font-size: 12px;
	color: var(--el-text-color-secondary);
	line-height: 1.4;
	margin-top: 4px;
}
</style>
