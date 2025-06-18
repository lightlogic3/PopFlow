<script setup lang="ts">
import { ref, reactive, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
	getModelConfigsByProvider,
	updateModelConfigStatus,
	deleteModelConfig,
	getModelConfigDetail,
	createModelConfig,
	updateModelConfig,
} from "@/api/llm_model_config_api";
import { Plus, Edit, Delete } from "@element-plus/icons-vue";

const props = defineProps({
	providerId: {
		type: Number,
		required: true,
	},
	providerName: {
		type: String,
		required: true,
	},
});

const emit = defineEmits(["refresh"]);

const loading = ref(false);
const modelConfigs = ref<any[]>([]);
const editDialogVisible = ref(false);
const currentConfigId = ref<number>(0);
const isEdit = ref(false);

// 表单数据
const formData = reactive({
	model_id: "",
	display_name: "",
	model_type: "chat",
	max_tokens: 4096,
	capabilities: "",
	price_per_1k_input_tokens: 0,
	price_per_1k_output_tokens: 0,
	provider_id: 0,
	status: 1,
	description: "",
	version: "",
	params: "",
});

// 表单规则
const rules = reactive({
	model_id: [{ required: true, message: "请输入模型ID", trigger: "blur" }],
	display_name: [{ required: true, message: "请输入显示名称", trigger: "blur" }],
	model_type: [{ required: true, message: "请选择模型类型", trigger: "change" }],
});

const formRef = ref();

const fetchModelConfigs = async () => {
	if (!props.providerId) {
		ElMessage.error("供应商ID不能为空");
		return;
	}

	loading.value = true;
	try {
		const response = await getModelConfigsByProvider(props.providerId);
		if (response && Array.isArray(response)) {
			modelConfigs.value = response;
		} else {
			modelConfigs.value = [];
		}
	} catch (error) {
		console.error("获取模型配置列表失败", error);
		ElMessage.error("获取模型配置列表失败");
		modelConfigs.value = [];
	} finally {
		loading.value = false;
	}
};

const handleEdit = (id: number) => {
	isEdit.value = true;
	currentConfigId.value = id;
	resetForm();
	fetchConfigDetail(id);
	editDialogVisible.value = true;
};

const handleAdd = () => {
	isEdit.value = false;
	currentConfigId.value = 0;
	resetForm();
	formData.provider_id = props.providerId;
	editDialogVisible.value = true;
};

const resetForm = () => {
	if (formRef.value) {
		formRef.value.resetFields();
	}
	formData.model_id = "";
	formData.display_name = "";
	formData.model_type = "chat";
	formData.max_tokens = 4096;
	formData.capabilities = "";
	formData.price_per_1k_input_tokens = 0;
	formData.price_per_1k_output_tokens = 0;
	formData.provider_id = props.providerId;
	formData.status = 1;
	formData.description = "";
	formData.version = "";
	formData.params = "";
};

const fetchConfigDetail = async (id: number) => {
	try {
		const response = await getModelConfigDetail(id);
		if (response) {
			if (response.params && typeof response.params === "object") {
				response.params = JSON.stringify(response.params);
			}
			Object.assign(formData, response);
		}
	} catch (error) {
		console.error("获取模型配置详情失败", error);
		ElMessage.error("获取模型配置详情失败");
	}
};

const submitForm = async () => {
	if (!formRef.value) return;

	await formRef.value.validate(async (valid) => {
		if (valid) {
			loading.value = true;
			try {
				const submitData: any = { ...formData };
				if (submitData.params) {
					try {
						submitData.params = JSON.parse(submitData.params);
					} catch (e) {
						ElMessage.error("参数格式不正确，请输入有效的JSON");
						loading.value = false;
						return;
					}
				} else {
					submitData.params = {};
				}

				if (isEdit.value) {
					await updateModelConfig(currentConfigId.value, submitData);
					ElMessage.success("更新成功");
				} else {
					await createModelConfig(submitData);
					ElMessage.success("创建成功");
				}
				editDialogVisible.value = false;
				fetchModelConfigs();
				emit("refresh");
			} catch (error) {
				console.error(isEdit.value ? "更新模型配置失败" : "创建模型配置失败", error);
				ElMessage.error(isEdit.value ? "更新模型配置失败" : "创建模型配置失败");
			} finally {
				loading.value = false;
			}
		}
	});
};

const handleDelete = (id: number) => {
	ElMessageBox.confirm("确定要删除该模型配置吗？", "提示", {
		confirmButtonText: "确定",
		cancelButtonText: "取消",
		type: "warning",
	})
		.then(async () => {
			try {
				await deleteModelConfig(id);
				ElMessage.success("删除成功");
				fetchModelConfigs();
				emit("refresh");
			} catch (error) {
				console.error("删除失败", error);
				ElMessage.error("删除失败");
			}
		})
		.catch(() => {
			// 用户取消操作
		});
};

const toggleStatus = async (config: any) => {
	const newStatus = config.status === 1 ? 0 : 1;
	try {
		await updateModelConfigStatus(config.id, newStatus);
		ElMessage.success(`${newStatus === 1 ? "启用" : "禁用"}成功`);
		// 更新本地状态
		config.status = newStatus;
		emit("refresh");
	} catch (error) {
		console.error("状态更新失败", error);
		ElMessage.error("状态更新失败");
	}
};

const getStatusClass = (status: number) => {
	return status === 1 ? "status-active" : "status-inactive";
};

const getStatusText = (status: number) => {
	return status === 1 ? "已启用" : "已禁用";
};

const getModelTypeText = (type: string) => {
	switch (type) {
		case "chat":
			return "对话型";
		case "multimodal":
			return "多模态";
		default:
			return type || "未知";
	}
};

onMounted(() => {
	fetchModelConfigs();
});
</script>

<template>
	<div class="model-config-panel">
		<div class="panel-header">
			<h2>{{ providerName }} - 模型配置</h2>
			<el-button type="primary" @click="handleAdd">
				<el-icon><Plus /></el-icon>
				添加模型配置
			</el-button>
		</div>

		<div class="model-config-grid" v-loading="loading">
			<el-empty v-if="modelConfigs.length === 0" description="暂无模型配置数据" />
			<el-card v-for="config in modelConfigs" :key="config.id" class="model-config-card" shadow="hover">
				<div class="model-config-header">
					<h3 class="model-config-name">{{ config.display_name || config.model_id }}</h3>
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
						<span class="info-label">模型ID：</span>
						<span>{{ config.model_id }}</span>
					</div>
					<div class="info-item">
						<span class="info-label">类型：</span>
						<span>{{ getModelTypeText(config.model_type) }}</span>
					</div>
					<div class="info-item">
						<span class="info-label">功能：</span>
						<span>{{ config.capabilities || "未设置" }}</span>
					</div>
					<div class="info-item">
						<span class="info-label">输入价格：</span>
						<span>{{ config.price_per_1k_input_tokens }} / 1K tokens</span>
					</div>
					<div class="info-item">
						<span class="info-label">输出价格：</span>
						<span>{{ config.price_per_1k_output_tokens }} / 1K tokens</span>
					</div>
				</div>
				<div class="model-config-description" v-if="config.description">
					{{ config.description }}
				</div>
				<template #footer>
					<div class="model-config-actions">
						<el-button type="primary" size="small" @click="handleEdit(config.id)">
							<el-icon><Edit /></el-icon>
							编辑
						</el-button>
						<el-button type="danger" size="small" @click="handleDelete(config.id)">
							<el-icon><Delete /></el-icon>
							删除
						</el-button>
					</div>
				</template>
			</el-card>
		</div>

		<!-- 模型配置编辑弹窗 -->
		<el-dialog
			:title="isEdit ? '编辑模型配置' : '添加模型配置'"
			v-model="editDialogVisible"
			width="50%"
			destroy-on-close
		>
			<el-form ref="formRef" :model="formData" :rules="rules" label-width="120px">
				<el-form-item label="模型ID" prop="model_id">
					<el-input v-model="formData.model_id" placeholder="请输入模型ID，如：gpt-3.5-turbo" />
				</el-form-item>

				<el-form-item label="显示名称" prop="display_name">
					<el-input v-model="formData.display_name" placeholder="请输入显示名称，如：GPT-3.5" />
				</el-form-item>

				<el-form-item label="模型类型" prop="model_type">
					<el-select v-model="formData.model_type" placeholder="请选择模型类型">
						<el-option label="对话型" value="chat" />
						<el-option label="多模态" value="multimodal" />
					</el-select>
				</el-form-item>

				<el-form-item label="最大Token数" prop="max_tokens">
					<el-input-number v-model="formData.max_tokens" :min="0" :step="1" />
				</el-form-item>

				<el-form-item label="功能" prop="capabilities">
					<el-input v-model="formData.capabilities" placeholder="请输入功能描述" />
				</el-form-item>

				<el-form-item label="输入价格" prop="price_per_1k_input_tokens">
					<el-input-number
						v-model="formData.price_per_1k_input_tokens"
						:precision="4"
						:step="0.0001"
						:min="0"
						placeholder="每千字符输入价格"
					/>
				</el-form-item>

				<el-form-item label="输出价格" prop="price_per_1k_output_tokens">
					<el-input-number
						v-model="formData.price_per_1k_output_tokens"
						:precision="4"
						:step="0.0001"
						:min="0"
						placeholder="每千字符输出价格"
					/>
				</el-form-item>

				<el-form-item label="状态">
					<el-switch
						v-model="formData.status"
						:active-value="1"
						:inactive-value="0"
						active-text="启用"
						inactive-text="禁用"
					/>
				</el-form-item>

				<el-form-item label="描述" prop="description">
					<el-input v-model="formData.description" type="textarea" :rows="3" placeholder="请输入描述信息" />
				</el-form-item>

				<el-form-item label="版本" prop="version">
					<el-input v-model="formData.version" placeholder="请输入版本号" />
				</el-form-item>

				<el-form-item label="参数配置" prop="params">
					<el-input
						v-model="formData.params"
						type="textarea"
						:rows="5"
						placeholder="请输入JSON格式的参数配置（可选）"
					/>
					<div class="form-help-text">参数配置支持JSON格式，例如temperature、top_p等参数</div>
				</el-form-item>
			</el-form>
			<template #footer>
				<span class="dialog-footer">
					<el-button @click="editDialogVisible = false">取消</el-button>
					<el-button type="primary" @click="submitForm">保存</el-button>
				</span>
			</template>
		</el-dialog>
	</div>
</template>

<style scoped>
.model-config-panel {
	padding: 0;
}

.panel-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 24px;
}

.model-config-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
	gap: 16px;
}

.model-config-card {
	transition: all 0.3s ease;
	background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
	border: 1px solid #e2e8f0;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	height: 280px;
	overflow: hidden;
}

.model-config-card:hover {
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
	border-color: #2563eb;
}

.model-config-header {
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
	margin-bottom: 15px;
}

.model-config-name {
	font-size: 16px;
	color: #1e293b;
	margin: 0;
	font-weight: 600;
	line-height: 1.4;
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
	margin-bottom: 15px;
}

.info-item {
	display: flex;
	align-items: flex-start;
	margin-bottom: 6px;
	font-size: 12px;
	color: #64748b;
}

.info-label {
	min-width: 70px;
	color: #1e293b;
	font-weight: 500;
}

.model-config-description {
	background: #f8fafc;
	border: 1px solid #e2e8f0;
	border-radius: 6px;
	padding: 12px;
	margin-bottom: 12px;
	font-size: 14px;
	line-height: 1.5;
	height: 90px;
	color: #64748b;
	overflow: hidden;
	position: relative;
}

.model-config-description::after {
	content: "";
	position: absolute;
	bottom: 0;
	left: 0;
	right: 0;
	height: 30px;
	background: linear-gradient(transparent, #f8fafc);
}

.model-config-actions {
	display: flex;
	justify-content: flex-end;
	gap: 8px;
}

.form-help-text {
	font-size: 12px;
	color: var(--el-text-color-secondary);
	line-height: 1.5;
	margin-top: 5px;
}
</style>
