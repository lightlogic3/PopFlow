<script setup lang="ts">
import { ref, onMounted, reactive } from "vue";
import { useRouter, useRoute  } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import type { Role, RoleCreate, RoleUpdate } from "@/types/role";
import type { Page } from "@/types/api";
import { getRoleList, createRole, updateRole, deleteRole } from "@/api/role";
import { Delete, Edit, Plus, Document } from "@element-plus/icons-vue";
import { getLLMProviderList } from "@/api/llm";
import type { LLMProvider, LLMModel } from "@/api/llm";
import { getConfig_value } from "@/api/system";
import { getRolePrompts } from "@/api/role_manage";
import ModelCascader from "@/components/ModelCascader.vue";
import FileUploader from "@/components/FileUploader/index.vue";
const router = useRouter();
const route = useRoute();
const loading = ref(false);
const roles = ref<Role[]>([]);
const roleFormRef = ref();

// Pagination related
const currentPage = ref(1);
const pageSize = ref(20);
const total = ref(0);

// Dialog related
const dialogVisible = ref(false);
const dialogTitle = ref("Add Role");
const formLoading = ref(false);
const isEdit = ref(false);
const form = reactive<{
	id?: string;
	name: string;
	role_id: string;
	sort: number;
	image_url: string;
	role_tags: string[];
	role_type: string;
	llm_choose: string;
	worldview_control: string;
}>({
	name: "",
	role_id: "role0001",
	sort: 1,
	image_url: "https://picsum.photos/400/300?random=1",
	role_tags: [],
	role_type: "main",
	llm_choose: "doubao-lite-32k-character-241015",
	worldview_control: "system_prompt",
});

// Add current selected role id
const selectedRoleId = ref<string>("");

// Form validation rules
const rules = {
	name: [{ required: true, message: "Please enter role name", trigger: "blur" }],
	role_id: [{ required: true, message: "Please enter role ID", trigger: "blur" }],
};

const fetchRoles = async () => {
	loading.value = true;
	try {
		const response: Page<Role> = await getRoleList({
			page: currentPage.value,
			size: pageSize.value,
		});
		if (response && response.items) {
			// 格式化数据，适配前端显示
			roles.value = response.items.map((item: Role) => ({
				...item,
				level: item.sort || 1,
				imageUrl: item.image_url,
				knowledgeCount: item.knowledge_count || 0,
			}));
			total.value = response.total;
		} else {
			ElMessage.warning("No role data retrieved");
			roles.value = [];
			total.value = 0;
		}
	} catch (error) {
		console.error("Failed to get role list", error);
		ElMessage.error("Failed to get role list");
		roles.value = [];
		total.value = 0;
	} finally {
		loading.value = false;
	}
};

// Pagination handling functions
const handleSizeChange = (size: number) => {
	pageSize.value = size;
	currentPage.value = 1;
	fetchRoles();
};

const handleCurrentChange = (page: number) => {
	currentPage.value = page;
	fetchRoles();
};

const goToDetail = (roleId: string, config_id: string) => {
	selectedRoleId.value = config_id; // Set selected role
	router.push(`/role/detail/${roleId}?config_id=${config_id}`);
};

// Select role
const selectRole = (roleId: string) => {
	selectedRoleId.value = roleId;
};

// Open add role dialog
const addRole = () => {
	isEdit.value = false;
	dialogTitle.value = "Add Role";
	// Reset form
	form.name = "";
	form.role_id = "";
	form.sort = 1;
	form.image_url = "https://picsum.photos/400/300?random=1";
	form.role_tags = [];
	delete form.id;
	dialogVisible.value = true;
};

// Open edit role dialog
const editRole = (role: Role) => {
	isEdit.value = true;
	dialogTitle.value = "Edit Role";
	// Fill form
	form.id = role.id;
	form.name = role.name;
	form.role_id = role.role_id;
	form.sort = role.sort || role.level || 1;
	form.image_url = role.image_url || role.imageUrl || "https://picsum.photos/400/300?random=1";
	form.role_type = role.role_type;
	form.llm_choose = role.llm_choose;
	form.role_tags = role.tags?.split(",");
	form.worldview_control = role.worldview_control;
	dialogVisible.value = true;
};

// Submit form
const submitForm = async (formEl: any) => {
	if (!formEl) return;
	await formEl.validate(async (valid: boolean) => {
		if (valid) {
			formLoading.value = true;
			try {
				if (isEdit.value && form.role_id) {
				// Edit role
				const data: RoleUpdate = {
					name: form.name,
					sort: form.sort,
					image_url: form.image_url,
					tags: form.role_tags?.join(","),
					role_type: form.role_type,
					llm_choose: form.llm_choose,
					worldview_control: form.worldview_control,
				};
				await updateRole(form.role_id, data);
				ElMessage.success("Role updated successfully");
			} else {
				// Add role
				const data: RoleCreate = {
					name: form.name,
					sort: form.sort,
					image_url: form.image_url,
					role_id: form.role_id,
					tags: form.role_tags?.join(","),
					role_type: form.role_type,
					llm_choose: form.llm_choose,
					worldview_control: form.worldview_control,
				};
				await createRole(data);
				ElMessage.success("Role added successfully");
			}
				dialogVisible.value = false;
			fetchRoles(); // Refresh list
		} catch (error) {
			console.error("Failed to submit role data", error);
			ElMessage.error(isEdit.value ? "Failed to update role" : "Failed to add role");
			} finally {
				formLoading.value = false;
			}
		}
	});
};

// Delete role
const handleDelete = (roleId: string) => {
	ElMessageBox.confirm("Are you sure you want to delete this role? This operation cannot be undone", "Warning", {
		confirmButtonText: "Confirm",
		cancelButtonText: "Cancel",
		type: "warning",
	})
		.then(async () => {
			try {
				await deleteRole(roleId);
				ElMessage.success("Deleted successfully");
				fetchRoles(); // Refresh list
			} catch (error) {
				console.error("Failed to delete role", error);
				ElMessage.error("Failed to delete role");
			}
		})
		.catch(() => {
			// Cancel delete
		});
};
const providers = ref<LLMProvider[]>([]);
const configRoleTypes = ref([]);
const system_prompts = ref([]);
const fetchProviders = async () => {
	try {
		// 尝试调用API获取数据
		const response = await getLLMProviderList({ skip: 0, limit: 100 });
		providers.value = response;
	} catch (error) {
		console.error("Failed to get LLM provider list", error);
		ElMessage.error("Failed to get LLM provider list, showing mock data");
	}
};
function getConfig() {
	getConfig_value("WEB_ROLE_TYPE").then((res) => {
		configRoleTypes.value = JSON.parse(res.config_value);
	});
	getRolePrompts({ types: ["system"] }).then((res) => {
		system_prompts.value = res;
	});
}

function roleTypeForMat(value: string) {
	for (const item of configRoleTypes.value) {
		if (item.value === value) {
			return item.label;
		}
	}
	return value;
}

function handleModelChange(modelInfo: LLMModel & { provider_name: string; provider_id: number }) {
	console.log("Selected model info:", modelInfo);
	// Here you can perform other operations based on the selected model information
	// For example, update interface display or save additional model information
}

const openAddRole = () => {
	if (route.query.auto && route.query.auto == "openAddRole") {
		addRole()
	}
}

onMounted(() => {
	fetchRoles();
	fetchProviders();
	getConfig();
	openAddRole();
});
</script>

<template>
	<div class="role-list-container">
		<div class="role-list-header">
			<h1 class="title">Role Knowledge Base Management</h1>
			<el-button type="primary" @click="addRole" class="add-role-btn btn-fix">
				<el-icon><Plus /></el-icon>
				Add Role
			</el-button>
		</div>

		<div class="role-gallery-wrapper">
			<el-row :gutter="16" v-loading="loading" class="role-gallery">
				<el-col :xs="12" :sm="8" :md="6" :lg="4" :xl="3" v-for="role in roles" :key="role.id">
					<div class="role-card-wrapper" :class="{ selected: selectedRoleId === role.id }" @click="selectRole(role.id)">
						<div class="role-card-inner" @click="goToDetail(role.role_id, role.id)">
							<div class="role-level-badge">{{ roleTypeForMat(role.role_type) }}</div>
							<div class="role-level-badge role-level-badge-count">
								<div class="stat-item knowledge">
									<el-icon><Document /></el-icon>
									<span>{{ role.knowledgeCount }}</span>
								</div>
							</div>
							<div class="role-avatar-container">
								<el-avatar :size="80" :src="role.imageUrl" class="role-avatar" />
							</div>
							<div class="role-info">
								<div class="role-name">
									{{ role.name }}
									<div class="role-id">(#{{ role.role_id }})</div>
								</div>

								<div class="role-stats">
									<div>
										<el-tag size="small" type="warning" style="margin-right: 5px">
								{{ role.llm_choose || "Doubao Role Playing" }}
							</el-tag>
							<el-tag
								v-for="tag in role.tags?.split(',')"
								:key="tag"
								class="tag"
								size="small"
								style="margin-right: 5px"
							>
								{{ tag || "Not Added" }}
							</el-tag>
									</div>
								</div>
							</div>

							<div class="role-actions">
								<el-button type="primary" size="small" circle @click.stop="editRole(role)" class="action-btn edit-btn">
									<el-icon><Edit /></el-icon>
								</el-button>
								<el-button
									type="danger"
									size="small"
									circle
									@click.stop="handleDelete(role.role_id)"
									class="action-btn delete-btn"
								>
									<el-icon><Delete /></el-icon>
								</el-button>
							</div>

							<div class="select-indicator">Select</div>
						</div>
					</div>
				</el-col>
			</el-row>
		</div>

		<!-- Pagination component -->
		<div class="pagination" v-if="total > 10">
			<el-pagination
				v-model:current-page="currentPage"
				v-model:page-size="pageSize"
				:total="total"
				:page-sizes="[10, 20, 50, 100]"
				layout="total, sizes, prev, pager, next"
				@size-change="handleSizeChange"
				@current-change="handleCurrentChange"
			/>
		</div>

		<!-- Role form dialog -->
		<el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
			<el-form
				ref="roleFormRef"
				:model="form"
				:rules="rules"
				label-width="100px"
				v-loading="formLoading"
				label-position="top"
			>
				<FormItem label="Role Name" prop="name" tooltipKey="name">
					<el-input v-model="form.name" placeholder="Please enter role name" />
				</FormItem>
				<FormItem label="Role ID" prop="role_id" tooltipKey="role_id">
					<el-input v-model="form.role_id" placeholder="Please enter role ID (role0001)" :disabled="isEdit" />
				</FormItem>
				<FormItem label="Role Tags" prop="role_tags" tooltipKey="role_tags">
					<el-input-tag v-model="form.role_tags" placeholder="Please enter role tags" />
				</FormItem>
				<div class="flex-form">
					<FormItem label="Role Type" prop="role_type" style="width: 100%" tooltipKey="role_type">
						<el-select v-model="form.role_type">
							<el-option v-for="item in configRoleTypes" :key="item.value" :label="item.label" :value="item.value" />
						</el-select>
					</FormItem>
				</div>
				<FormItem label="Role Image" prop="image_url" tooltipKey="image_url">
					<FileUploader v-model="form.image_url" accept="image/*" folder="images" :max-size="10" />
				</FormItem>
				<el-collapse>
					<el-collapse-item title="Advanced Settings" name="1">
						<FormItem label="Worldview Control" prop="worldview_control" tooltipKey="worldview_control">
							<el-select v-model="form.worldview_control">
								<el-option v-for="item in system_prompts" :key="item.id" :label="item.title" :value="item.role_id" />
							</el-select>
						</FormItem>
						<FormItem label="Dialogue Model" prop="llm_choose" style="width: 100%" tooltipKey="llm_choose">
							<div class="model-select-container">
								<ModelCascader v-model="form.llm_choose" @change="handleModelChange" style="width: 100%" />
								<!--                <ModelCascader-->
								<!--                  v-model="form.llm_choose"-->
								<!--                  @change="handleModelChange"-->
								<!--                  filterCapability="ABC"-->
								<!--                />-->
							</div>
						</FormItem>
					</el-collapse-item>
				</el-collapse>
			</el-form>
			<template #footer>
				<el-button @click="dialogVisible = false">Cancel</el-button>
				<el-button class="btn-fix" type="primary" @click="submitForm(roleFormRef)" :loading="formLoading"> Confirm </el-button>
			</template>
		</el-dialog>
	</div>
</template>

<style scoped lang="scss">
.role-list-container {
	background: #f3f3f3;
	min-height: 100vh;
	padding: 0;
	position: relative;
}

.role-list-header {
	background: rgba(5, 36, 73, 0.91);
	border-bottom: 3px solid #2563eb;
	padding: 20px;
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 0;
}

.title {
	font-size: 24px;
	margin: 0;
	color: #ffffff;
	font-weight: bold;
	text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
}

.add-role-btn {
	font-weight: 600;
	padding: 10px 20px;
	border-radius: 20px;
}

.model-select-container {
	display: flex;
	flex-direction: column;
	gap: 8px;
	width: 100%;
}

.model-filter-input {
	margin-bottom: 8px;
}

.role-gallery-wrapper {
	padding: 20px;
	background: transparent;
}

.role-card-wrapper {
	margin-bottom: 20px;
	position: relative;
	border-radius: 8px;
	transition: all 0.3s ease;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	overflow: hidden;
	background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
	border: 2px solid #e2e8f0;
	height: 210px;
}

.role-card-wrapper:hover {
	transform: translateY(-3px);
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
	border-color: #2563eb;
	z-index: 10;
}

.role-card-wrapper.selected {
	border-color: #2563eb;
	box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.3), 0 4px 12px rgba(0, 0, 0, 0.15);
}

.role-card-wrapper.selected .select-indicator {
	opacity: 1;
	transform: translateY(0);
}

.role-card-inner {
	position: relative;
	height: 100%;
	display: flex;
	flex-direction: column;
	align-items: center;
	padding: 15px 10px;
	cursor: pointer;
	text-align: center;
}

.role-level-badge {
	position: absolute;
	top: 5px;
	left: 5px;
	background: linear-gradient(135deg, #031528, #1e293b);
	color: #fff;
	padding: 2px 6px;
	border-radius: 12px;
	font-size: 10px;
	font-weight: bold;
	z-index: 5;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
	border: 1px solid #2563eb;
}

.role-level-badge-count {
	left: 70px;
}

.role-avatar-container {
	margin-top: 15px;
	margin-bottom: 10px;
}

.role-avatar {
	border: 3px solid #fff;
	box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
	transition: transform 0.3s;
}

.role-card-wrapper:hover .role-avatar {
	transform: scale(1.05);
}

.role-info {
	flex: 1;
	width: 100%;
	display: flex;
	flex-direction: column;
	align-items: center;
}

.role-name {
	font-size: 16px;
	margin: 5px 0 2px 0;
	color: var(--el-text-color-primary);
	font-weight: 600;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
	width: 100%;
	display: flex;
	justify-content: center;
}

.role-id {
	font-size: 12px;
	color: #8492a6;
	margin-bottom: 8px;
	line-height: 20px;
}

.role-stats {
	display: flex;
	justify-content: space-between;
	margin: 8px 0;
}

.stat-item {
	display: flex;
	align-items: center;
	gap: 3px;
	color: var(--el-text-color-secondary);
	font-size: 10px;
}

.stat-item.knowledge {
	color: #67c23a;
}

.role-actions {
	position: absolute;
	top: 5px;
	right: 5px;
	display: flex;
	gap: 5px;
	z-index: 5;
	opacity: 0;
	transition: opacity 0.3s;
}

.role-card-wrapper:hover .role-actions {
	opacity: 1;
}

.action-btn {
	box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.2);
	transform: scale(0.85);
}

.select-indicator {
	position: absolute;
	bottom: 0;
	left: 0;
	width: 100%;
	text-align: center;
	background: #2563eb;
	color: white;
	padding: 4px 0;
	font-size: 12px;
	font-weight: 600;
	opacity: 0;
	transform: translateY(100%);
	transition: all 0.3s;
}

.image-preview {
	margin-top: 10px;
	width: 100%;
	display: flex;
	justify-content: center;
}

.pagination {
	display: flex;
	justify-content: center;
	margin-top: 20px;
	padding: 20px 0;
}

.pagination :deep(.el-pagination) {
	background: #ffffff;
	padding: 15px 20px;
	border-radius: 8px;
	border: 1px solid #e2e8f0;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.pagination :deep(.el-pager li) {
	background: transparent;
	color: #64748b;
	border: 1px solid #e2e8f0;
	margin: 0 2px;
	border-radius: 4px;
}

.pagination :deep(.el-pager li:hover),
.pagination :deep(.el-pager li.is-active) {
	background: #2563eb;
	color: #ffffff;
	border-color: #2563eb;
}

@media (max-width: 768px) {
	.role-gallery {
		justify-content: center;
	}
}

.remark-text {
	font-size: 10px;
	line-height: 40px;
	margin-left: 8px;
	color: rgba(96, 98, 102, 0.8);
}

@import '@/layouts/WriterLayout/css/extra.scss';

.btn-fix {
	color: #fff;
	background-color: $btn-bg-color0;
	border-color: $btn-bg-color0;
}
</style>
