<script setup lang="ts">
import { ref, onMounted, onBeforeMount, watch } from "vue";
import { useRoute } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import type { World, WorldKnowledge, WorldKnowledgeCreate } from "@/types/world";
import {
	getWorldDetail,
	getKnowledgeByWorld,
	getKnowledgeByWorldPaginated,
	createWorldKnowledge,
	updateWorldKnowledge,
	deleteWorldKnowledge,
	bulkCreateWorldKnowledge,
	getWorldKnowledgeDetailByIds,
} from "@/api/world";
import { getRolesByWorldId, getRolesByWorldKnowledgeId, createRoleWorld, deleteRoleWorld } from "@/api/roleWorld";
import { getRoleList } from "@/api/role";
import { getConfig_value } from "@/api/system";

// 导入拆分的组件
import WorldInfo from "./components/WorldInfo.vue";
import KnowledgeList from "./components/KnowledgeList.vue";
import RelatedRoles from "./components/RelatedRoles.vue";
import BindRoleDialog from "./components/BindRoleDialog.vue";
import KnowledgeDialog from "./components/KnowledgeDialog.vue";

const route = useRoute();
const worldId = ref(route.params.id as string);
const loading = ref(false);
const knowledgeLoading = ref(false);
const rolesLoading = ref(false);

// World details
const world = ref<World>({
	id: worldId.value,
	title: "",
	type: "",
	description: "",
	image_url: "",
	knowledge_count: 0,
	created_at: "",
	updated_at: "",
});

// Knowledge fragment related
const knowledgeList = ref<WorldKnowledge[]>([]);
const selectedKnowledge = ref<WorldKnowledge | null>(null);
// Knowledge pagination related
const knowledgeTotal = ref(0);
const knowledgeCurrentPage = ref(1);
const knowledgePageSize = ref(10);

// Related characters
const rolesList = ref<any[]>([]);
const rolesTotal = ref(0);
const rolesCurrentPage = ref(1);
const rolesPageSize = ref(10);
const isShowingKnowledgeRoles = ref(false);
const currentKnowledgeId = ref<string>("");

// Add bind character related states
const bindRoleDialogVisible = ref(false);
const allRolesList = ref<any[]>([]);
const allRolesLoading = ref(false);
const allRolesTotal = ref(0);
const allRolesCurrentPage = ref(1);
const allRolesPageSize = ref(20);
const selectedRoleIds = ref<string[]>([]);
const roleSearchKeyword = ref("");

// Add knowledge
const knowledgeDialogVisible = ref(false);
const knowledgeDialogType = ref<"add" | "edit">("add");
const currentEditKnowledge = ref<number>(0); // Current editing knowledge ID
const newKnowledge = ref<WorldKnowledgeCreate>({
	id: "",
	worlds_id: worldId.value,
	text: "",
	type: "base",
	title: "",
	source: "",
	tags: "",
	grade: 5,
	relations: "",
	relations_role: "",
});

// Multi-text input - temporary frontend use
const knowledgeTextList = ref<string[]>([""]);

// Add AI enhancement related data
const enhancePrompt = ref(`Your task is to enhance the semantic meaning of the following content to facilitate vector database retrieval. Please follow these guidelines:

1. Content should be detailed and specific, avoiding abstraction. Each block should be independent and complete, making it easier to return relevant context when retrieved from the vector database.
2. Natural language expression: Describe information in a coherent narrative way, allowing vector embeddings to better capture semantic relationships.

Output requirements: Separate each block with two line breaks`);

// Add platform and model selection
const platforms = ref([{ label: "Kimi", value: "kimi" }]);
const selectedPlatform = ref("kimi");

const models = ref<Record<string, Array<{ label: string; value: string }>>>({
	kimi: [
		{ label: "Moonshot-v1-8k", value: "moonshot-v1-8k" },
		{ label: "Moonshot-v1-32k", value: "moonshot-v1-32k" },
	],
});
const selectedModel = ref("moonshot-v1-8k");

// Retrieve locally stored prompts in onBeforeMount
onBeforeMount(() => {
	const savedPrompt = localStorage.getItem("aiEnhancePrompt");
	if (savedPrompt) {
		enhancePrompt.value = savedPrompt;
	}

	// Get saved platform and model settings
	const savedPlatform = localStorage.getItem("aiEnhancePlatform");
	if (savedPlatform && platforms.value.some((p) => p.value === savedPlatform)) {
		selectedPlatform.value = savedPlatform;

		// Get saved model settings
		const savedModel = localStorage.getItem("aiEnhanceModel");
		if (savedModel && models.value[selectedPlatform.value].some((m) => m.value === savedModel)) {
			selectedModel.value = savedModel;
		} else {
			// If the corresponding model is not found or not saved, set to the first model of the current platform
			selectedModel.value = models.value[selectedPlatform.value][0].value;
		}
	}

	loadKnowledgeConfig();
});

// Monitor prompt changes and save to localStorage
watch(enhancePrompt, (newVal) => {
	localStorage.setItem("aiEnhancePrompt", newVal);
});

// Monitor platform changes, update model selection and save to localStorage
watch(selectedPlatform, (newVal) => {
	// If the currently selected model is not in the new platform's model list, reset to the first model of the new platform
	if (!models.value[newVal].some((model) => model.value === selectedModel.value)) {
		selectedModel.value = models.value[newVal][0].value;
	}

	// Save platform selection
	localStorage.setItem("aiEnhancePlatform", newVal);
});

// Monitor model changes and save to localStorage
watch(selectedModel, (newVal) => {
	localStorage.setItem("aiEnhanceModel", newVal);
});

// Get knowledge repository list
const fetchKnowledge = async () => {
	knowledgeLoading.value = true;
	try {
		// Use new pagination interface
		const response = await getKnowledgeByWorldPaginated(worldId.value, {
			page: knowledgeCurrentPage.value,
			size: knowledgePageSize.value,
		});
		if (response && response.items) {
			knowledgeList.value = response.items || [];
			knowledgeTotal.value = response.total || 0;
		} else {
			console.log("No knowledge items found");
			knowledgeList.value = [];
			knowledgeTotal.value = 0;
		}
	} catch (error) {
		console.error("Failed to fetch knowledge list", error);
		ElMessage.error("Failed to fetch knowledge list");
		knowledgeList.value = [];
		knowledgeTotal.value = 0;
	} finally {
		knowledgeLoading.value = false;
	}
};

// Get related character list
const fetchRoles = async () => {
	rolesLoading.value = true;
	try {
		// Decide which API to use based on current state
		let response;
		if (isShowingKnowledgeRoles.value && currentKnowledgeId.value) {
			// Get characters related to specific knowledge point
			response = await getRolesByWorldKnowledgeId(currentKnowledgeId.value, {
				skip: (rolesCurrentPage.value - 1) * rolesPageSize.value,
				limit: rolesPageSize.value,
			});
		} else {
			// Get characters related to world view
			response = await getRolesByWorldId(worldId.value, {
				skip: (rolesCurrentPage.value - 1) * rolesPageSize.value,
				limit: rolesPageSize.value,
			});
		}

		if (response) {
			rolesList.value = response.roles || [];
			rolesTotal.value = response.total || 0;
		} else {
			console.log("No related characters found");
			rolesList.value = [];
			rolesTotal.value = 0;
		}
	} catch (error) {
		console.error("Failed to fetch related characters", error);
		ElMessage.error("Failed to fetch related characters");
		rolesList.value = [];
		rolesTotal.value = 0;
	} finally {
		rolesLoading.value = false;
	}
};

const relateKnowList = ref([]);
async function getResKnowList(knowledge: any) {
	relateKnowList.value = [];
	if (knowledge.relations) {
		relateKnowList.value = await getWorldKnowledgeDetailByIds(knowledge.relations);
	}
}

// Get all character lists (for binding)
const fetchAllRoles = async () => {
	allRolesLoading.value = true;
	try {
		// Use character API to get all characters
		const response = await getRoleList({
			page: allRolesCurrentPage.value,
			size: allRolesPageSize.value,
			keyword: roleSearchKeyword.value || undefined,
		});

		if (response && response.items) {
			allRolesList.value = response.items || [];
			allRolesTotal.value = response.total || 0;
		} else {
			allRolesList.value = [];
			allRolesTotal.value = 0;
		}
	} catch (error) {
		console.error("Failed to fetch all characters", error);
		ElMessage.error("Failed to fetch all characters");
		allRolesList.value = [];
		allRolesTotal.value = 0;
	} finally {
		allRolesLoading.value = false;
	}
};

// Search characters
const searchRoles = async (query: string) => {
	roleSearchKeyword.value = query;
	allRolesCurrentPage.value = 1;
	fetchAllRoles();
};

// Open bind character dialog
const openBindRoleDialog = () => {
	if (!selectedKnowledge.value) {
		ElMessage.warning("Please select a knowledge point first");
		return;
	}
	bindRoleDialogVisible.value = true;
	selectedRoleIds.value = [];
	allRolesCurrentPage.value = 1;
	fetchAllRoles();
};

// Bind characters to currently selected knowledge point
const bindRolesToKnowledge = async (roleIds: string[]) => {
	if (!selectedKnowledge.value || roleIds.length === 0) {
		ElMessage.warning("Please select characters");
		return;
	}

	try {
		const knowledgeId = selectedKnowledge.value.id.toString();
		const worldIdVal = worldId.value;
		// Create association for each selected character
		const promises = roleIds.map((roleId) =>
			createRoleWorld({
				role_id: roleId,
				world_id: worldIdVal,
				world_konwledge_id: knowledgeId,
			}),
		);

		await Promise.all(promises);

		ElMessage.success("Characters bound successfully");
		bindRoleDialogVisible.value = false;

		// Refresh related character list
		fetchRoles();
	} catch (error) {
		console.error("Failed to bind characters", error);
		ElMessage.error("Failed to bind characters, the character may already be bound");
	}
};

// Unbind character from knowledge point
const unbindRoleFromKnowledge = async (relationId: number) => {
	if (!isShowingKnowledgeRoles.value) {
		ElMessage.warning("Please select a knowledge point first");
		return;
	}

	try {
		await ElMessageBox.confirm("Are you sure you want to unbind this character?", "Prompt", {
			confirmButtonText: "Confirm",
			cancelButtonText: "Cancel",
			type: "warning",
		});

		await deleteRoleWorld(relationId);
		ElMessage.success("Binding removed");

		// Refresh related character list
		fetchRoles();
	} catch (error) {
		if (error !== "cancel") {
			console.error("Failed to remove binding", error);
			ElMessage.error("Failed to remove binding");
		}
	}
};

// Monitor all character pagination changes
const handleAllRolesPageChange = (page: number) => {
	allRolesCurrentPage.value = page;
	fetchAllRoles();
};

// Get characters associated with knowledge points
const showKnowledgeRoles = async (knowledge: WorldKnowledge) => {
	selectedKnowledge.value = knowledge;
	isShowingKnowledgeRoles.value = true;
	currentKnowledgeId.value = knowledge.id.toString();
	rolesCurrentPage.value = 1;
	fetchRoles();
	getResKnowList(knowledge);
};

// Reset to display world view related characters
const resetToWorldRoles = () => {
	selectedKnowledge.value = null;
	isShowingKnowledgeRoles.value = false;
	currentKnowledgeId.value = "";
	rolesCurrentPage.value = 1;
	fetchRoles();
};

// Monitor character page number changes
const handleRolesPageChange = (page: number) => {
	rolesCurrentPage.value = page;
	fetchRoles();
};

// Get world view details
const fetchWorld = async () => {
	loading.value = true;
	try {
		const response = await getWorldDetail(worldId.value);
		if (response) {
			// Correctly parse nested data fields
			world.value = response || {
				id: worldId.value,
				title: "",
				type: "",
				description: "",
				image_url: "",
				knowledge_count: 0,
				created_at: "",
				updated_at: "",
			};
		}
	} catch (error) {
		console.error("Failed to get world view details:", error);
		ElMessage.error("Failed to get world view details");
	} finally {
		loading.value = false;
	}
};

// Edit knowledge
const editKnowledge = (knowledge: WorldKnowledge) => {
	knowledgeDialogType.value = "edit";
	currentEditKnowledge.value = knowledge.id;

	// Put existing content in the first textbox
	knowledgeTextList.value = [knowledge.text];

	newKnowledge.value = {
		id: knowledge.id.toString(),
		worlds_id: knowledge.worlds_id,
		type: knowledge.type,
		title: knowledge.title,
		text: knowledge.text,
		grade: knowledge.grade,
		source: knowledge.source || "",
		tags: (knowledge.tags || "").split(","),
		relations: knowledge.relations || "",
		relations_role: knowledge.relations_role || "",
	};

	knowledgeDialogVisible.value = true;
};

// Delete knowledge
const deleteKnowledge = async (knowledge: WorldKnowledge) => {
	try {
		await deleteWorldKnowledge(knowledge.id);
		ElMessage.success("Deleted successfully");
		fetchKnowledge();
	} catch (error) {
		console.error("Failed to delete knowledge fragment", error);
		ElMessage.error("Failed to delete knowledge fragment");
	}
};

const addNewKnowledge = () => {
	knowledgeDialogType.value = "add";
	newKnowledge.value = {
		id: "",
		worlds_id: worldId.value,
		type: "base",
		title: "",
		text: "",
		grade: 5,
		source: "",
		tags: "",
		relations: "",
		relations_role: "",
	};
	knowledgeTextList.value = [""];
	knowledgeDialogVisible.value = true;
};

// Handle knowledge dialog submission
const handleKnowledgeSubmit = async (knowledge: WorldKnowledgeCreate, validTexts: string[]) => {
	try {
		const baseData: any = {
			worlds_id: knowledge.worlds_id,
			type: knowledge.type,
			grade: knowledge.grade,
			source: "Management platform entry",
			tags: (knowledge.tags || []).join(","),
			relations: knowledge.relations || undefined,
			relations_role: knowledge.relations_role || undefined,
		};
		if (knowledgeDialogType.value === "add") {
			// Add mode: add each content as a separate knowledge entry
			const baseTitle = knowledge.title;
			// If there's only one content, use the original title directly
			if (validTexts.length === 1) {
				baseData["text"] = validTexts[0];
				baseData["title"] = baseTitle;
				await createWorldKnowledge(baseData);
			} else {
				// Multiple contents, create separate knowledge entries for each content, add sequence number to title
				const items = validTexts.map((text, index) => {
					const temData = JSON.parse(JSON.stringify(baseData));
					temData["title"] = validTexts.length > 1 ? `${baseTitle}${index + 1}` : baseTitle;
					temData["text"] = text;
					return temData;
				});
				await bulkCreateWorldKnowledge({ items });
			}

			ElMessage.success("Knowledge added successfully");
		} else {
			// Edit mode: only modify the currently selected knowledge entry
			baseData["text"] = validTexts[0];
			baseData["title"] = knowledge.title;
			await updateWorldKnowledge(currentEditKnowledge.value, baseData);
			ElMessage.success("Knowledge updated successfully");
		}

		knowledgeDialogVisible.value = false;
		fetchKnowledge();
	} catch (error) {
		console.error(knowledgeDialogType.value === "add" ? "Failed to add knowledge" : "Failed to update knowledge", error);
		ElMessage.error(knowledgeDialogType.value === "add" ? "Failed to add knowledge" : "Failed to update knowledge");
	}
};

const selectKnowledgeType = ref([]);

/**
 * Load knowledge type configuration
 */
function loadKnowledgeConfig() {
	getConfig_value("WEB_WORLD_KNOWLEDGE_TYPE").then((res) => {
		selectKnowledgeType.value = JSON.parse(res.config_value);
	});
}

const searchKnowledge = async (query: string) => {
	try {
		const response = await getKnowledgeByWorld(worldId.value, {
			skip: 0,
			limit: 10,
			search: query,
		});
		if (response) {
			knowledgeList.value = response;
		}
	} catch (error) {
		console.error("Failed to search knowledge:", error);
	}
};

// Handle knowledge repository pagination changes
const handleKnowledgePageChange = (page: number) => {
	knowledgeCurrentPage.value = page;
	fetchKnowledge();
};

const handleKnowledgeSizeChange = (size: number) => {
	knowledgePageSize.value = size;
	knowledgeCurrentPage.value = 1;
	fetchKnowledge();
};

onMounted(() => {
	fetchWorld();
	fetchKnowledge();
	fetchRoles();
	searchRoles("");
});
</script>

<template>
	<div class="world-detail-container" v-loading="loading">
		<!-- 世界观信息 -->
		<WorldInfo :world="world" :loading="loading" />

		<!-- 知识库片段列表 -->
		<KnowledgeList
			:knowledgeList="knowledgeList"
			:knowledgeLoading="knowledgeLoading"
			:selectedKnowledge="selectedKnowledge"
			:total="knowledgeTotal"
			:currentPage="knowledgeCurrentPage"
			:pageSize="knowledgePageSize"
			@add="addNewKnowledge"
			@edit="editKnowledge"
			@delete="deleteKnowledge"
			@select="showKnowledgeRoles"
			@page-change="handleKnowledgePageChange"
			@size-change="handleKnowledgeSizeChange"
		/>

		<!-- 关联角色列表 -->
		<RelatedRoles
			:rolesList="rolesList"
			:rolesLoading="rolesLoading"
			:rolesTotal="rolesTotal"
			:rolesPageSize="rolesPageSize"
			:rolesCurrentPage="rolesCurrentPage"
			:isShowingKnowledgeRoles="isShowingKnowledgeRoles"
			:selectedKnowledge="selectedKnowledge"
			:relateKnowList="relateKnowList"
			@bind-role="openBindRoleDialog"
			@unbind-role="unbindRoleFromKnowledge"
			@reset-to-world-roles="resetToWorldRoles"
			@page-change="handleRolesPageChange"
		/>

		<!-- 绑定角色对话框 -->
		<BindRoleDialog
			v-model:visible="bindRoleDialogVisible"
			:allRolesList="allRolesList"
			:allRolesLoading="allRolesLoading"
			:allRolesTotal="allRolesTotal"
			:allRolesCurrentPage="allRolesCurrentPage"
			:allRolesPageSize="allRolesPageSize"
			@search="searchRoles"
			@confirm="bindRolesToKnowledge"
			@page-change="handleAllRolesPageChange"
		/>

		<!-- 添加/编辑知识对话框 -->
		<KnowledgeDialog
			v-model:visible="knowledgeDialogVisible"
			:dialogType="knowledgeDialogType"
			:worldId="worldId"
			:currentKnowledge="newKnowledge"
			:selectKnowledgeType="selectKnowledgeType"
			:allRolesList="allRolesList"
			:allRolesLoading="allRolesLoading"
			@search="searchKnowledge"
			@confirm="handleKnowledgeSubmit"
		/>
	</div>
</template>

<style scoped lang="scss">
.world-detail-container {
	padding: 20px;
}

.header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 24px;
}

.back-button {
	display: flex;
	align-items: center;
	gap: 5px;
	color: var(--el-color-primary);
}

.title {
	font-size: 24px;
	margin: 0;
	color: var(--el-text-color-primary);
}

.world-info-card {
	margin-bottom: 24px;
}

.world-info {
	display: flex;
	gap: 24px;
}

.world-image {
	width: 300px;
	height: 200px;
	object-fit: cover;
	border-radius: 8px;
}

.world-details {
	flex: 1;
}

.world-type {
	margin-bottom: 12px;
}

.world-title {
	font-size: 24px;
	margin: 0 0 12px 0;
	color: var(--el-text-color-primary);
}

.world-description {
	margin: 0 0 16px 0;
	font-size: 16px;
	color: var(--el-text-color-secondary);
	line-height: 1.6;
}

.world-stats {
	display: flex;
	gap: 24px;
	margin-bottom: 16px;
}

.stat-item {
	display: flex;
	align-items: center;
	gap: 5px;
	color: var(--el-text-color-secondary);
	font-size: 14px;
}

.world-tags {
	display: flex;
	flex-wrap: wrap;
	gap: 8px;
}

.tag {
	margin-right: 0;
}

.section-card {
	margin-bottom: 24px;
}

.section-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.section-title-container {
	display: flex;
	align-items: center;
	gap: 10px;
}

.section-title {
	margin: 0;
	font-size: 18px;
	color: var(--el-text-color-primary);
}

.knowledge-card {
	margin-bottom: 16px;
	cursor: pointer;
	transition: all 0.3s;
}

.knowledge-card:hover {
	transform: translateY(-3px);
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.selected-knowledge {
	border: 2px solid var(--el-color-primary);
	background-color: var(--el-color-primary-light-9);
}

.knowledge-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 10px;
}

.knowledge-level {
	font-size: 14px;
	color: var(--el-text-color-secondary);
}

.knowledge-title {
	font-size: 16px;
	margin: 0 0 12px 0;
	color: var(--el-text-color-primary);
}

.knowledge-preview {
	margin: 0 0 12px 0;
	line-height: 1.5;
	color: var(--el-text-color-regular);
}

.knowledge-meta {
	display: flex;
	flex-wrap: wrap;
	gap: 12px;
	font-size: 12px;
	color: var(--el-text-color-secondary);
}

.knowledge-card-footer {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.knowledge-source {
	display: flex;
	align-items: center;
	gap: 5px;
	font-size: 12px;
	color: var(--el-text-color-secondary);
}

.knowledge-actions {
	display: flex;
	align-items: center;
	gap: 5px;
}

/* 角色卡片样式 */
.role-card {
	margin-bottom: 16px;
	display: flex;
	flex-direction: column;
	align-items: center;
	padding: 15px;
	transition: all 0.3s;
}

.role-card:hover {
	transform: translateY(-3px);
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.role-avatar-container {
	margin-bottom: 10px;
	display: flex;
	justify-content: center;
}

.role-content {
	text-align: center;
	width: 100%;
}

.role-name {
	font-size: 16px;
	margin: 0 0 5px 0;
	color: var(--el-text-color-primary);
}

.role-id {
	font-size: 12px;
	color: var(--el-text-color-secondary);
	margin: 0 0 10px 0;
}

.role-actions {
	margin-top: 10px;
}

.pagination-container {
	margin-top: 20px;
	display: flex;
	justify-content: center;
}

/* 其他现有样式 */
.form-tip {
	font-size: 12px;
	color: var(--el-text-color-secondary);
}

/* 知识库对话框样式 */
.knowledge-dialog-content {
	display: flex;
	gap: 20px;
}

.knowledge-form-container {
	flex: 1;
	border-right: 1px solid var(--el-border-color-lighter);
	padding-right: 20px;
}

.knowledge-enhance-container {
	flex: 1;
	padding-left: 10px;
}

.enhance-title {
	font-size: 16px;
	margin-top: 0;
	color: var(--el-text-color-primary);
}

.prompt-hint {
	font-size: 12px;
	color: var(--el-text-color-secondary);
	margin-top: 4px;
}

.enhanced-results {
	margin-top: 16px;
}

.results-container {
	max-height: 200px;
	overflow-y: auto;
}

.enhanced-result-item {
	padding: 8px;
	border-radius: 4px;
	cursor: pointer;
	transition: background-color 0.3s;
}

.enhanced-result-item:hover {
	background-color: var(--el-fill-color-light);
}

.enhanced-result-item p {
	margin: 0;
	line-height: 1.5;
}

.text-item-container {
	position: relative;
	margin-bottom: 15px;
	width: 100%;
	display: block;
}

.text-item-actions {
	position: absolute;
	top: 8px;
	right: 10px;
	z-index: 1;
}

.text-item-container .el-textarea {
	width: 100%;
}

.text-item-container .el-textarea__inner {
	padding-right: 40px;
}

.add-text-button {
	margin-top: 10px;
	display: flex;
	justify-content: center;
}

/* 角色选项样式 */
.role-option {
	display: flex;
	align-items: center;
	padding: 5px 0;
}

.role-option-avatar {
	margin-right: 10px;
}

.role-option-info {
	display: flex;
	flex-direction: column;
}

.role-option-name {
	font-size: 14px;
	color: var(--el-text-color-primary);
}

.role-option-id {
	font-size: 12px;
	color: var(--el-text-color-secondary);
}

@import '@/layouts/WriterLayout/css/extra.scss';

.btn-fix {
	color: #fff;
	background-color: $btn-bg-color0;
	border-color: $btn-bg-color0;
	
	&:hover {
		background-color: $btn-bg-hover-color0;
		border-color: $btn-bg-hover-color0;
	}
}
</style>
