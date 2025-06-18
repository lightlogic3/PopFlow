<template>
	<div class="prompt-edit">
		<div class="header">
			<el-button link @click="handleBack">
				<el-icon><ArrowLeft /></el-icon>
				Back to List
			</el-button>
			<h1 class="title">{{ isEdit ? "Edit Prompt Template" : "Add Prompt Template" }}</h1>
		</div>

		<div class="form-container">
			<div class="form-section">
				<el-form ref="formRef" :model="form" :rules="rules" label-width="100px" label-position="top">
					<FormItem label="Template Role" prop="role" tooltipKey="role">
						<el-select v-model="form.type" placeholder="Please select template role" :disabled="!!route.params.id">
							<el-option v-for="(key, value) in promptType" :key="key" :label="key" :value="value" />
						</el-select>
					</FormItem>
					<FormItem label="Title" prop="title" tooltipKey="title">
						<el-input v-model="form.title" placeholder="Please enter template title" />
					</FormItem>
					<FormItem label="Template ID" prop="role_id" tooltipKey="role_id">
						<el-input
							:disabled="form.role_id === 'system_prompt'"
							v-model="form.role_id"
							placeholder="Please enter template ID (English) separated by underscores"
						/>
					</FormItem>
					<FormItem label="Level" prop="level" tooltipKey="level">
						<el-input-number v-model="form.level" :min="1" :max="10" />
					</FormItem>
					<FormItem label="Status" prop="status" tooltipKey="status">
						<el-switch v-model="form.status" :active-value="1" :inactive-value="0" />
					</FormItem>
					<FormItem label="Prompt Content" prop="prompt_text" tooltipKey="prompt_text">
						<AvatarEditor
							:users="form.type === 'task' ? taskPrompt : globalPrompt"
							:max-length="3000"
							:min-length="10"
							v-model="form.prompt_text"
						/>
					</FormItem>
					<el-form-item>
						<el-button type="primary" @click="handleSubmit">Save</el-button>
						<el-button @click="handleCancel">Cancel</el-button>
					</el-form-item>
				</el-form>
			</div>

			<div class="preview-section">
				<h2 class="preview-title">Preview Effect</h2>
				<div class="preview-prompt_text">
					{{ form.prompt_text }}
				</div>
			</div>
		</div>
	</div>
</template>

<script lang="ts" setup>
import { ref, reactive, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { ArrowLeft } from "@element-plus/icons-vue";
import type { FormInstance } from "element-plus";
import { updatePrompt, getPromptDetail, createPromptSystem } from "@/api/prompt";
import AvatarEditor from "@/components/AvatarEditor/AvatarEditor.vue";
import { globalPrompt, taskPrompt } from "@/utils/editorButton";
import { getConfig_value } from "@/api/system";
const route = useRoute();
const router = useRouter();
const formRef = ref<FormInstance>();

const isEdit = computed(() => route.params.id);

interface FormData {
	role_id: string;
	// role: string;
	level: number;
	status: number;
	prompt_text: string;
	title: string;
	type: string;
}

const form = reactive<FormData>({
	role_id: "",
	// role: "",
	level: 1,
	status: 1,
	prompt_text: "",
	title: "",
	type: "system",
});

const rules = {
	role_id: [{ required: true, message: "Please enter template name", trigger: "blur" }],
	title: [{ required: true, message: "Please enter template name", trigger: "blur" }],
	level: [{ required: true, message: "Please enter level", trigger: "blur" }],
	prompt_text: [{ required: true, message: "Please enter prompt content", trigger: "blur" }],
};

// Get details
const getDetail = async (id: number): Promise<void> => {
	try {
		const res = await getPromptDetail(id);
		form.role_id = res.role_id;
		// form.role = res.role;
		form.level = res.level;
		form.status = res.status;
		form.prompt_text = res.prompt_text;
		form.title = res.title;
		form.type = res.type;
	} catch (error) {
		console.error("Failed to get prompt template details:", error);
	}
};

// Back to list
const handleBack = (): void => {
	router.push("/prompt/list");
};

// Submit form
const handleSubmit = async (): Promise<void> => {
	if (!formRef.value) return;

	await formRef.value.validate(async (valid) => {
		if (valid) {
			try {
				if (isEdit.value) {
					await updatePrompt(Number(route.params.id), form);
					ElMessage.success("Update successful");
				} else {
					await createPromptSystem(form);
					ElMessage.success("Add successful");
				}
				handleBack();
			} catch (error) {
				console.error("Failed to submit prompt template:", error);
			}
		}
	});
};

const promptType = ref<any>([]);
function getConfig() {
	getConfig_value("FUNCTION_PROMPT_TEMPLATE").then((res) => {
		promptType.value = JSON.parse(res.config_value);
		console.log(promptType.value);
	});
}
// Cancel
const handleCancel = (): void => {
	handleBack();
};

onMounted(() => {
	if (isEdit.value) {
		getDetail(Number(route.params.id));
	}
	getConfig();
});
</script>

<style lang="scss" scoped>
.prompt-edit {
	padding: 20px;
	background-color: #f5f6fa;
	min-height: 100%;

	.header {
		display: flex;
		align-items: center;
		margin-bottom: 20px;

		.title {
			font-size: 24px;
			color: #2c3e50;
			margin: 0 0 0 20px;
		}
	}

	.form-container {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 30px;
	}

	.form-section {
		background: #fff;
		border-radius: 10px;
		padding: 20px;
	}

	.preview-section {
		background: #fff;
		border-radius: 10px;
		padding: 20px;

		.preview-title {
			font-size: 18px;
			color: #2c3e50;
			margin: 0 0 20px;
		}

		.preview-prompt_text {
			background: #f5f6fa;
			border-radius: 8px;
			padding: 20px;
			min-height: 300px;
			font-size: 14px;
			line-height: 1.6;
			color: #7f8c8d;
			white-space: pre-wrap;
		}
	}
}
</style>
