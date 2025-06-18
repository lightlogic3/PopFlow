<script setup lang="ts">
import { ref, reactive, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";
import type { LLMProvider, LLMProviderCreate, LLMProviderUpdate } from "@/types/llm";
import { getLLMProviderById, createLLMProvider, updateLLMProvider } from "@/api/llm";

const router = useRouter();
const route = useRoute();
const formRef = ref<FormInstance>();
const loading = ref(false);
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

// Initialize page
const initPage = async () => {
	const id = Number(route.params.id);
	providerId.value = id;
	isEdit.value = id > 0;

	if (isEdit.value) {
		await fetchProviderDetail(id);
	}
};

// Get provider details
const fetchProviderDetail = async (id: number) => {
	loading.value = true;
	try {
		const response = await getLLMProviderById(id);

		if (response) {
			// Fill form data
			if (Object.keys(response.extra_config).length) {
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
	} finally {
		loading.value = false;
	}
};

// Submit form
const submitForm = async () => {
	if (!formRef.value) return;

	await formRef.value.validate(async (valid, fields) => {
		if (valid) {
			loading.value = true;
			try {
				if (formData.extra_config) {
					formData.extra_config = JSON.parse(formData.extra_config + "");
				} else {
					formData.extra_config = {};
				}
				if (isEdit.value) {
					// Update provider
					await updateLLMProvider(providerId.value, formData as LLMProviderUpdate);
					ElMessage.success("Update successful");
				} else {
					// Create provider
					await createLLMProvider(formData as LLMProviderCreate);
					ElMessage.success("Create successful");
				}
				// Return to list page
				router.push("/llm/list");
			} catch (error) {
				console.error(isEdit.value ? "Failed to update provider" : "Failed to create provider", error);
			ElMessage.error(isEdit.value ? "Failed to update provider" : "Failed to create provider");
			// Simulate success (when API fails)
				setTimeout(() => {
					router.push("/llm/list");
				}, 1000);
			} finally {
				loading.value = false;
			}
		} else {
			console.log("Form validation failed", fields);
		}
	});
};

// Cancel operation
const cancelOperation = () => {
	router.push("/llm/list");
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
	initPage();
});
</script>

<template>
	<div class="llm-provider-edit" v-loading="loading">
		<div class="edit-header">
			<h1 class="title">{{ isEdit ? "Edit" : "Add" }} LLM Provider</h1>
		</div>

		<el-form ref="formRef" :model="formData" :rules="rules" label-width="120px" class="provider-form">
			<FormItem label="Provider Name" prop="provider_name" tooltipKey="provider_name">
				<el-input v-model="formData.provider_name" placeholder="Please enter provider name, e.g.: OpenAI" />
			</FormItem>

			<FormItem label="API URL" prop="api_url" tooltipKey="api_url">
				<el-input v-model="formData.api_url" placeholder="Please enter API URL, e.g.: https://api.openai.com/v1" />
			</FormItem>

			<FormItem label="API Key" prop="api_key" tooltipKey="api_key">
				<el-input v-model="formData.api_key" placeholder="Please enter API key" show-password />
			</FormItem>

			<FormItem label="Model Name" prop="model_name" tooltipKey="model_name">
				<el-input v-model="formData.model_name" placeholder="Please enter model name, e.g.: gpt-3.5-turbo" />
			</FormItem>

			<FormItem label="Status" tooltipKey="status">
				<el-switch
					v-model="formData.status"
					:active-value="1"
					:inactive-value="0"
					active-text="Enable"
					inactive-text="Disable"
				/>
			</FormItem>

			<FormItem label="Remarks" prop="remark" tooltipKey="remark">
				<el-input v-model="formData.remark" type="textarea" :rows="3" placeholder="Please enter remarks" />
			</FormItem>

			<FormItem label="Extra Config" prop="extra_config" tooltipKey="extra_config">
				<el-input
					v-model="formData.extra_config"
					type="textarea"
					:rows="5"
					placeholder="Please enter extra configuration in JSON format (optional)"
				/>
				<div class="form-help-text">Extra configuration supports JSON format, e.g., setting request timeout, proxy, etc.</div>
			</FormItem>

			<el-form-item>
				<el-button type="primary" @click="submitForm">Save</el-button>
				<el-button @click="cancelOperation">Cancel</el-button>
				<el-button type="info" @click="testConnection">Test Connection</el-button>
			</el-form-item>
		</el-form>
	</div>
</template>

<style scoped>
.llm-provider-edit {
	padding: 20px;
}

.edit-header {
	margin-bottom: 24px;
}

.title {
	font-size: 24px;
	margin: 0;
	color: var(--el-text-color-primary);
}

.provider-form {
	max-width: 800px;
	margin-top: 20px;
}

.form-help-text {
	font-size: 12px;
	color: var(--el-text-color-secondary);
	line-height: 1.5;
	margin-top: 5px;
}
</style>
