<script setup lang="ts">
import { defineEmits, defineProps, onBeforeMount, onMounted, reactive, ref, watch } from "vue";
import { ElMessage, ElMessageBox, FormInstance, type FormRules } from "element-plus";
import { Delete, Edit, Plus, Search, User, UserFilled } from "@element-plus/icons-vue";
import type { Role, RoleKnowledge, RoleKnowledgeCreate } from "@/types/role";
import { createRoleKnowledge, deleteRoleKnowledge, getRoleList, updateRoleKnowledge } from "@/api/role";
import { enhanceContentTokenStream } from "@/api/llm";
import { getConfig_value } from "@/api/system";
import AvatarEditor from "@/components/AvatarEditor/AvatarEditor.vue";
import ModelCascader from "@/components/ModelCascader.vue";
import KnowledgeSearchDialog from "./KnowledgeSearchDialog.vue";
import { rolePrompt } from "@/utils/editorButton";

/**
 * Component property definition
 * @typedef {Object} Props
 * @property {RoleKnowledge[]} knowledgeList - Knowledge fragment list
 * @property {boolean} loading - Loading status
 * @property {string} roleId - Character ID
 */
const props = defineProps<{
	knowledgeList: RoleKnowledge[];
	knowledgeJoinList: RoleKnowledge[];
	loading: boolean;
	roleId: string;
}>();

onMounted(() => {
	get_role_list();
});
/**
 * Component event definition
 */
const emit = defineEmits<{
	(e: "refresh"): void;
}>();

// Knowledge base related
const knowledgeDialogVisible = ref(false);
const knowledgeDialogType = ref("add"); // Dialog type: add or edit
const currentEditKnowledge = ref<number>(0); // Current editing knowledge ID
const newKnowledge = ref<RoleKnowledgeCreate>({
	role_id: props.roleId,
	type: "base",
	title: "",
	text: "",
	grade: 1,
	source: "",
	tags: "",
});

// Multiple text input - frontend temporary use
const knowledgeTextList = ref<string[]>([""]);

// Add AI enhancement related data
const enhancePrompt = ref(`Your task is to enhance the following content semantically to facilitate retrieval from the vector database. Please follow these guidelines:

1. Content should be detailed and specific, avoiding abstraction. Each block should be independent and complete, making it easier to return relevant context during vector database retrieval.
2. Natural language expression: Describe information in a coherent narrative way, allowing vector embeddings to better capture semantic relationships.

Output requirements: Separate each block with two line breaks`);
const isEnhancing = ref(false);
const enhancedResults = ref<string[]>([]);

// Model selection
const selectedModelId = ref("");

const selectKnowledgeType = ref([
	{ label: "Basic Information", value: "base" },
	{ label: "Shared Memory", value: "join" },
]);

function loadKnowledgeConfig() {
	getConfig_value("WEB_ROLE_KNOWLEDGE_TYPE").then((res) => {
		selectKnowledgeType.value = JSON.parse(res.config_value);
	});
}

loadKnowledgeConfig();
/**
 * Get AI settings from local storage before component mounting
 */
onBeforeMount(() => {
	const savedPrompt = localStorage.getItem("aiEnhancePrompt");
	if (savedPrompt) {
		enhancePrompt.value = savedPrompt;
	}

	// Get saved model settings
	const savedModelId = localStorage.getItem("aiEnhanceModelId");
	if (savedModelId) {
		selectedModelId.value = savedModelId;
	}
});

/**
 * Watch prompt changes, save to localStorage
 */
watch(enhancePrompt, (newVal) => {
	localStorage.setItem("aiEnhancePrompt", newVal);
});

/**
 * Watch model changes, save to localStorage
 */
watch(selectedModelId, (newVal) => {
	localStorage.setItem("aiEnhanceModelId", newVal);
});

/**
 * AI content enhancement method
 */
const handleEnhanceContent = () => {
	// Find the first non-empty content
	const nonEmptyContent = knowledgeTextList.value.find((text) => text.trim() !== "");

	if (!nonEmptyContent) {
		ElMessage.warning("Please fill in at least one knowledge content first");
		return;
	}

	if (!selectedModelId.value) {
		ElMessage.warning("Please select a model first");
		return;
	}

	isEnhancing.value = true;
	enhancedResults.value = []; // Clear previous results

	// Create buffer
	let currentBuffer = "";
	const rawChunks: string[] = []; // Store all raw data blocks for debugging
	// Create request data
	const requestData = {
		prompt: enhancePrompt.value,
		enhance_context: nonEmptyContent,
		model_id: selectedModelId.value,
	};
	enhancedResults.value = ["AI thinking..."];

	// Use character-by-character streaming API
	enhanceContentTokenStream(
		requestData,
		// Handle processed tokens
		() => {},
		// Handle raw data blocks
		(rawChunk) => {
			currentBuffer += rawChunk;
			rawChunks.push(rawChunk);
			// Check paragraph separators, if there are complete paragraphs, add to results
			const parts = rawChunks.join("").split("\n\n");
			// Add all complete paragraphs to the results except the last part
			// for (let i = 0; i < parts.length; i++) {
			enhancedResults.value[parts.length - 1] = parts[parts.length - 1];
			// Keep the last part for continued buffering
			// currentBuffer = parts[parts.length - 1];
		},
		// Handle errors
		(error) => {
			console.error("Request error:", error);
			ElMessage.error("Content enhancement request failed");
		},
	)
		.then((response: any) => {
			// Request completed, check for residual content in the buffer
			if (currentBuffer.trim()) {
				enhancedResults.value.push(currentBuffer.trim());
			}

			// If needed, you can view all received raw data
			console.log("All raw data blocks:", rawChunks);
			enhancedResults.value = rawChunks.join("").split("\n\n");
			console.log("Response status:", response.status);
			console.log("Response headers:", Object.fromEntries(response.headers.entries()));
			isEnhancing.value = false;
		})
		.catch((error) => {
			console.error("Execution request failed:", error);
			isEnhancing.value = false;
		});
};

/**
 * Method to select enhanced content
 * @param {string} content - Selected enhanced content
 */
const selectEnhancedContent = (content: string) => {
	knowledgeTextList.value.push(content);
	ElMessage.success("Enhanced content added");
};

/**
 * Method to add content item
 */
const addTextItem = () => {
	knowledgeTextList.value.push("");
};

/**
 * Method to delete content item
 * @param {number} index - Index of the item to delete
 */
const removeTextItem = (index: number) => {
	if (knowledgeTextList.value.length > 1) {
		knowledgeTextList.value.splice(index, 1);
	} else {
		ElMessage.warning("At least one content item must be kept");
	}
};

/**
 * Edit knowledge
 * @param {RoleKnowledge} knowledge - Knowledge object to edit
 */
const editKnowledge = (knowledge: RoleKnowledge) => {
	knowledgeDialogType.value = "edit";
	currentEditKnowledge.value = knowledge.id;

	// Put existing content in the first text box
	knowledgeTextList.value = [knowledge.text];

	newKnowledge.value = {
		role_id: knowledge.role_id,
		type: knowledge.type,
		title: knowledge.title,
		text: knowledge.text,
		grade: knowledge.grade,
		source: knowledge.source || "",
		tags: knowledge.tags || "",
	};

	knowledgeDialogVisible.value = true;
};

/**
 * Delete knowledge
 * @param {RoleKnowledge} knowledge - Knowledge object to delete
 */
const deleteKnowledge = (knowledge: RoleKnowledge) => {
	ElMessageBox.confirm("Are you sure you want to delete this knowledge fragment?", "Confirmation", {
		confirmButtonText: "Confirm",
		cancelButtonText: "Cancel",
		type: "warning",
	})
		.then(async () => {
			try {
				await deleteRoleKnowledge(knowledge.id);
				ElMessage.success("Deleted successfully");
				emit("refresh");
			} catch (error) {
				console.error("Failed to delete knowledge", error);
				ElMessage.error("Failed to delete knowledge");
			}
		})
		.catch(() => {
			// Cancel operation
		});
};

/**
 * Add new knowledge
 */
const addNewKnowledge = () => {
	knowledgeDialogType.value = "add";
	newKnowledge.value = {
		role_id: props.roleId,
		type: "base",
		title: "",
		text: "",
		grade: 1,
		source: "",
		tags: "",
	};
	// Reset text list
	knowledgeTextList.value = [""];
	knowledgeDialogVisible.value = true;
};

const ruleFormRef = ref<FormInstance>();
const formRules = reactive<FormRules>({
	title: [
		{ required: true, message: "Please enter knowledge title", trigger: "blur" },
		{ min: 2, max: 40, message: "Length should be between 2 and 30 characters", trigger: "blur" },
	],
	text: [
		{ required: true, message: "Please enter knowledge content", trigger: "blur" },
		{ min: 2, max: 3000, message: "Length should be between 2 and 3000 characters", trigger: "blur" },
	],
	grade: [{ required: true, message: "Please enter knowledge grade", trigger: "blur" }],
});

/**
 * Get character list
 */
const targetRoles = ref<Role[]>([]);
const get_role_list = async () => {
	try {
		const res = await getRoleList({});
		targetRoles.value = res;
	} catch (error) {
		console.error("Failed to get character list", error);
		ElMessage.error("Failed to get character list");
	}
};

/**
 * Submit knowledge form
 */
const submitForm:any = async (formEl: FormInstance | undefined = undefined) => {
	// 1. Validate the first field of the list
	if (!knowledgeTextList.value[0] || knowledgeTextList.value[0].trim() === "") {
		ElMessage.warning("Please fill in at least one knowledge content");
		return;
	}

	// 2. Validate the form
	if (!newKnowledge.value.title) {
		ElMessage.warning("Please enter knowledge title");
		return;
	}

	// 3. Combine all text content
	const combinedText = knowledgeTextList.value
		.filter((text) => text.trim() !== "") // Filter out empty entries
		.join("\n\n"); // Join with double line breaks

	// 4. Create submission data
	const submitData = {
		...newKnowledge.value,
		text: combinedText, // Use combined text
	};

	try {
		if (knowledgeDialogType.value === "add") {
			// 5. Submit form using combined data
			await createRoleKnowledge(submitData);
			ElMessage.success("Knowledge added successfully");
		} else {
			await updateRoleKnowledge(currentEditKnowledge.value, submitData);
			ElMessage.success("Knowledge updated successfully");
		}
		knowledgeDialogVisible.value = false;
		emit("refresh");
	} catch (error) {
		console.error(knowledgeDialogType.value === "add" ? "Failed to add knowledge" : "Failed to update knowledge", error);
		ElMessage.error(knowledgeDialogType.value === "add" ? "Failed to add knowledge" : "Failed to update knowledge");
	}
};

// Shared memory related
// New character knowledge extraction logic
const shareRoleId = ref("");
const shareRoleKnowledgeList = ref<RoleKnowledge[]>([]);
const isLoadingShareKnowledge = ref(false);
const searchKnowledgeDialogVisible = ref(false);

/**
 * Get the name of the character by its ID
 * @param {string} roleId - Character ID
 * @returns {string} Character name
 */
const getRoleName = (roleId: string) => {
	const role = targetRoles.value.find((r) => r.id === roleId);
	return role ? role.name : roleId;
};

// Filter knowledge list
const filteredKnowledgeList = ref(props.knowledgeList);
const knowledgeSearchValue = ref("");
const knowledgeSearchType = ref("all");

/**
 * Filter local knowledge list
 */
const filterLocalKnowledge = () => {
	if (!props.knowledgeList) return;

	// If there's no search value and type is all, return all
	if (!knowledgeSearchValue.value && knowledgeSearchType.value === "all") {
		filteredKnowledgeList.value = props.knowledgeList;
		return;
	}

	// Filter by type first
	let typeFiltered = props.knowledgeList;
	if (knowledgeSearchType.value !== "all") {
		typeFiltered = props.knowledgeList.filter((item) => item.type === knowledgeSearchType.value);
	}

	// Then filter by search value
	if (knowledgeSearchValue.value) {
		const searchValue = knowledgeSearchValue.value.toLowerCase();
		filteredKnowledgeList.value = typeFiltered.filter(
			(item) =>
				item.title.toLowerCase().includes(searchValue) ||
				item.text.toLowerCase().includes(searchValue) ||
				(item.tags && item.tags.toLowerCase().includes(searchValue)) ||
				(item.source && item.source.toLowerCase().includes(searchValue)),
		);
	} else {
		filteredKnowledgeList.value = typeFiltered;
	}
};

// Watch for changes to search value or type
watch([knowledgeSearchValue, knowledgeSearchType], () => {
	filterLocalKnowledge();
});

// Watch for changes to props.knowledgeList
watch(
	() => props.knowledgeList,
	(newVal) => {
		filteredKnowledgeList.value = newVal;
		filterLocalKnowledge();
	},
	{ immediate: true },
);

// Open knowledge search dialog
const openKnowledgeSearchDialog = () => {
	searchKnowledgeDialogVisible.value = true;
};

// Handle search result
const handleSearchResult = (selectedKnowledge: RoleKnowledge) => {
	// Add knowledge to text list
	knowledgeTextList.value.push(selectedKnowledge.text);
	ElMessage.success("Knowledge content added");
};

// Highlight search text
const highlightSearchText = (text: string) => {
	if (!knowledgeSearchValue.value) return text;

	const searchValue = knowledgeSearchValue.value;
	const index = text.toLowerCase().indexOf(searchValue.toLowerCase());
	if (index === -1) return text;

	const before = text.substring(0, index);
	const highlighted = text.substring(index, index + searchValue.length);
	const after = text.substring(index + searchValue.length);

	return before + '<span class="highlight">' + highlighted + "</span>" + after;
};

// Add these properties to fix linter errors
const activeName = ref("base");
const role_list = ref<Role[]>([]);
const searchDialogVisible = ref(false);

const openSearchDialog = () => {
	searchDialogVisible.value = true;
};

const handleTypeChange = () => {
	// Empty implementation to fix linter errors
};
</script>

<template>
	<div class="knowledge-section">
		<div class="section-toolbar">
			<!-- Filtering controls -->
			<div class="filter-controls">
				<el-input
					v-model="knowledgeSearchValue"
					placeholder="Search for knowledge..."
					class="search-input"
					clearable
					@clear="filterLocalKnowledge"
				>
					<template #prefix>
						<el-icon class="el-input__icon"><Search /></el-icon>
					</template>
				</el-input>
				<el-select v-model="knowledgeSearchType" @change="filterLocalKnowledge" style="width: 150px">
					<el-option label="All Types" value="all"></el-option>
					<el-option v-for="type in selectKnowledgeType" :key="type.value" :label="type.label" :value="type.value"></el-option>
				</el-select>
			</div>

			<!-- Action buttons -->
			<div>
				<el-button type="primary" size="small" @click="openKnowledgeSearchDialog">
					<el-icon>
						<Search />
					</el-icon>
					Knowledge Search
				</el-button>
				<el-button type="primary" size="small" @click="addNewKnowledge">
					<el-icon>
						<Plus />
					</el-icon>
					Add Knowledge
				</el-button>
			</div>
		</div>

		<div class="knowledge-list" v-loading="loading">
			<el-empty v-if="filteredKnowledgeList.length === 0" description="No knowledge fragments yet" />
			<div class="knowledge-grid" v-else>
				<el-card v-for="item in filteredKnowledgeList" :key="item.id" class="knowledge-card" shadow="hover">
					<div class="knowledge-card-header">
						<div class="knowledge-card-title">{{ item.title || 'Untitled' }}</div>
						<div class="knowledge-card-meta">
							<el-tag size="small" :type="item.type === 'base' ? 'primary' : 'success'">
								{{ item.type === 'base' ? 'Basic Information' : 'Shared Memory' }}
							</el-tag>
							<el-tag size="small" type="info">
								Level {{ item.grade }}
							</el-tag>
						</div>
					</div>
					<div class="knowledge-card-content" v-html="highlightSearchText(item.text)"></div>
					<div class="knowledge-card-footer">
						<div class="knowledge-card-tags" v-if="item.tags">
							<el-tag v-for="tag in item.tags.split(',')" :key="tag" size="small" type="info" class="mr-5">
								{{ tag }}
							</el-tag>
						</div>
						<div class="knowledge-card-source" v-if="item.source">
							Source: {{ item.source }}
						</div>
						<div class="knowledge-card-actions">
							<el-button type="primary" link @click="editKnowledge(item)">
								<el-icon>
									<Edit />
								</el-icon>
								Edit
							</el-button>
							<el-button type="danger" link @click="deleteKnowledge(item)">
								<el-icon>
									<Delete />
								</el-icon>
								Delete
							</el-button>
						</div>
					</div>
				</el-card>
			</div>
		</div>

		<!-- Knowledge search dialog -->
		<KnowledgeSearchDialog
			v-if="searchKnowledgeDialogVisible"
			v-model:visible="searchKnowledgeDialogVisible"
			:role-id="props.roleId"
			@select-knowledge="handleSearchResult"
		/>

		<!-- Add/Edit Knowledge Dialog -->
		<el-dialog
			v-model="knowledgeDialogVisible"
			:title="knowledgeDialogType === 'add' ? 'Add Knowledge Fragment' : 'Edit Knowledge Fragment'"
			width="70%"
		>
			<div class="knowledge-form-container">
				<el-form :model="newKnowledge" label-position="top" :rules="formRules" ref="ruleFormRef">
					<el-row :gutter="20">
						<el-col :span="8">
							<el-form-item label="Title" prop="title">
								<el-input v-model="newKnowledge.title" placeholder="Knowledge title..." />
							</el-form-item>
						</el-col>
						<el-col :span="8">
							<el-form-item label="Type">
								<el-select v-model="newKnowledge.type" @change="handleTypeChange" style="width: 100%">
									<el-option
										v-for="type in selectKnowledgeType"
										:key="type.value"
										:label="type.label"
										:value="type.value"
									></el-option>
								</el-select>
							</el-form-item>
						</el-col>
						<el-col :span="8">
							<el-form-item label="Importance Level">
								<el-rate
									v-model="newKnowledge.grade"
									:colors="['#409EFF', '#409EFF', '#409EFF']"
									:max="5"
									:texts="['Very Low', 'Low', 'Medium', 'High', 'Very High']"
									show-text
								/>
							</el-form-item>
						</el-col>
					</el-row>

					<el-divider>Content</el-divider>

					<!-- Knowledge Content -->
					<div class="knowledge-content-section">
						<div v-for="(text, index) in knowledgeTextList" :key="index" class="knowledge-text-item">
							<el-input
								v-model="knowledgeTextList[index]"
								type="textarea"
								:rows="3"
								:autosize="{ minRows: 3, maxRows: 10 }"
								:placeholder="`Knowledge content block ${index + 1}...`"
							/>
							<div class="knowledge-text-actions">
								<el-button
									v-if="knowledgeTextList.length > 1"
									type="danger"
									circle
									size="small"
									@click="removeTextItem(index)"
								>
									<el-icon><Delete /></el-icon>
								</el-button>
							</div>
						</div>
						<div class="add-text-button">
							<el-button type="primary" plain @click="addTextItem" block>
								<el-icon><Plus /></el-icon>
								Add Another Content Block
							</el-button>
						</div>
					</div>

					<el-row :gutter="20">
						<el-col :span="12">
							<el-form-item label="Tags" prop="tags">
								<el-input v-model="newKnowledge.tags" placeholder="Tags (comma separated)" />
							</el-form-item>
						</el-col>
						<el-col :span="12">
							<el-form-item label="Source" prop="source">
								<el-input v-model="newKnowledge.source" placeholder="Knowledge source" />
							</el-form-item>
						</el-col>
					</el-row>

					<!-- AI Enhancement Section -->
					<el-collapse>
						<el-collapse-item title="AI Content Enhancement" name="1">
							<div class="ai-enhance-section">
								<el-form-item label="Model Selection">
									<ModelCascader v-model="selectedModelId" />
								</el-form-item>
								<el-form-item label="Enhancement Prompt">
									<el-input
										v-model="enhancePrompt"
										type="textarea"
										:rows="3"
										:autosize="{ minRows: 3, maxRows: 6 }"
										placeholder="Instructions for AI to enhance content..."
									/>
								</el-form-item>
								<el-form-item>
									<el-button type="primary" @click="handleEnhanceContent" :loading="isEnhancing">
										<el-icon><Edit /></el-icon>
										Generate Enhanced Content
									</el-button>
								</el-form-item>

								<!-- Enhanced Results -->
								<div v-if="enhancedResults.length > 0" class="enhanced-results">
									<h4>Enhanced Content Results</h4>
									<el-card v-for="(result, index) in enhancedResults" :key="index" class="enhanced-result-card">
										<div class="result-content">{{ result }}</div>
										<div class="result-actions">
											<el-button
												type="primary"
												size="small"
												@click="selectEnhancedContent(result)"
												:disabled="!result || result === 'AI thinking...'"
											>
												Add This Content
											</el-button>
										</div>
									</el-card>
								</div>
							</div>
						</el-collapse-item>
					</el-collapse>
				</el-form>
			</div>

			<template #footer>
				<span class="dialog-footer">
					<el-button @click="knowledgeDialogVisible = false">Cancel</el-button>
					<el-button type="primary" @click="submitForm">Confirm</el-button>
				</span>
			</template>
		</el-dialog>
	</div>
</template>

<style scoped>
.knowledge-section {
	padding: 0;
}

.section-toolbar {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 20px;
}

.filter-controls {
	display: flex;
	align-items: center;
	gap: 10px;
}

.search-input {
	width: 250px;
}

/* Knowledge card styles */
.knowledge-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
	gap: 16px;
}

.knowledge-card {
	display: flex;
	flex-direction: column;
	height: 100%;
	transition: all 0.3s ease;
}

.knowledge-card:hover {
	transform: translateY(-2px);
	box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}

.knowledge-card-header {
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
	margin-bottom: 8px;
}

.knowledge-card-title {
	font-weight: bold;
	font-size: 16px;
	flex: 1;
}

.knowledge-card-meta {
	display: flex;
	gap: 5px;
}

.knowledge-card-content {
	flex-grow: 1;
	background: #f8fafc;
	border-radius: 6px;
	padding: 12px;
	margin: 8px 0;
	font-size: 14px;
	line-height: 1.5;
	position: relative;
	overflow: hidden;
	max-height: 120px;
	text-overflow: ellipsis;
}

.knowledge-card-content::after {
	content: "";
	position: absolute;
	bottom: 0;
	left: 0;
	right: 0;
	height: 24px;
	background: linear-gradient(transparent, #f8fafc);
}

.knowledge-card-footer {
	margin-top: auto;
	display: flex;
	justify-content: space-between;
	align-items: center;
	flex-wrap: wrap;
}

.knowledge-card-tags {
	display: flex;
	flex-wrap: wrap;
	gap: 5px;
	margin-bottom: 8px;
}

.knowledge-card-source {
	font-size: 12px;
	color: #777;
	margin-bottom: 8px;
}

.knowledge-card-actions {
	margin-left: auto;
	display: flex;
	align-items: center;
}

/* Knowledge form styles */
.knowledge-content-section {
	margin-bottom: 20px;
}

.knowledge-text-item {
	margin-bottom: 10px;
	position: relative;
}

.knowledge-text-actions {
	position: absolute;
	right: -10px;
	top: 10px;
}

.add-text-button {
	margin-top: 10px;
}

/* AI enhancement styles */
.ai-enhance-section {
	padding: 10px 0;
}

.enhanced-results {
	margin-top: 16px;
}

.enhanced-result-card {
	margin-bottom: 10px;
}

.result-content {
	white-space: pre-wrap;
	padding: 10px;
	background: #f9f9f9;
	border-radius: 4px;
	margin-bottom: 10px;
}

.result-actions {
	display: flex;
	justify-content: flex-end;
}

/* Highlight style */
:deep(.highlight) {
	background-color: #ffeb3b;
	padding: 0 2px;
	border-radius: 2px;
}

/* Responsive styles */
@media (max-width: 768px) {
	.section-toolbar {
		flex-direction: column;
		align-items: stretch;
	}

	.filter-controls {
		margin-bottom: 10px;
		width: 100%;
	}

	.search-input {
		width: 100%;
	}

	.knowledge-grid {
		grid-template-columns: 1fr;
	}
}
</style>
