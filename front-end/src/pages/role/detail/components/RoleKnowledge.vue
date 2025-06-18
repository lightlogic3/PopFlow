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
 * Component props definition
 * @typedef {Object} Props
 * @property {RoleKnowledge[]} knowledgeList - Knowledge fragment list
 * @property {boolean} loading - Loading state
 * @property {string} roleId - Role ID
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
 * Component events definition
 */
const emit = defineEmits<{
	(e: "refresh"): void;
}>();

// Knowledge base related
const knowledgeDialogVisible = ref(false);
const knowledgeDialogType = ref("add"); // Dialog type: add or edit
const currentEditKnowledge = ref<number>(0); // Current knowledge ID being edited
const newKnowledge = ref<RoleKnowledgeCreate>({
	role_id: props.roleId,
	type: "base",
	title: "",
	text: "",
	grade: 1,
	source: "",
	tags: "",
});

// Multiple text inputs - for frontend temporary use
const knowledgeTextList = ref<string[]>([""]);

// Add AI enhancement related data
const enhancePrompt = ref(`Your task is to enhance the semantic content of the following text to facilitate vector database retrieval. Please follow these guidelines:

1. Content should be detailed and specific, avoiding excessive abstraction. Each block should be independent and complete, facilitating relevant context retrieval from the vector database.
2. Natural language expression: Describe information in a coherent narrative way so that vector embeddings can better capture semantic relationships.

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
		ElMessage.warning("Please enter at least one piece of knowledge content");
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
		// Process processed tokens
		() => {},
		// Process raw data blocks
		(rawChunk) => {
			currentBuffer += rawChunk;
			rawChunks.push(rawChunk);
			// Detect paragraph separators, add complete paragraphs to results
			const parts = rawChunks.join("").split("\n\n");
			// Add all complete paragraphs to results except the last part
			// for (let i = 0; i < parts.length; i++) {
			enhancedResults.value[parts.length - 1] = parts[parts.length - 1];
			// Keep the last part for continuation in buffer
			// currentBuffer = parts[parts.length - 1];
		},
		// Handle errors
		(error) => {
			console.error("Request error:", error);
			ElMessage.error("Content enhancement request failed");
		},
	)
		.then((response: any) => {
			// Request complete, check if there's residual content in buffer
			if (currentBuffer.trim()) {
				enhancedResults.value.push(currentBuffer.trim());
			}

			// If needed, view all received raw data
			console.log("All raw data blocks:", rawChunks);
			enhancedResults.value = rawChunks.join("").split("\n\n");
			console.log("Response status:", response.status);
			console.log("Response headers:", Object.fromEntries(response.headers.entries()));
			isEnhancing.value = false;
		})
		.catch((error) => {
			console.error("Failed to execute request:", error);
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
 * Method to remove content item
 * @param {number} index - Index of the item to remove
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
				ElMessage.success("Delete successful");
				emit("refresh");
			} catch (error) {
				console.error("Failed to delete knowledge fragment", error);
				ElMessage.error("Failed to delete knowledge fragment");
			}
		})
		.catch(() => {
			// Operation canceled
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
	knowledgeTextList.value = [""];
	knowledgeDialogVisible.value = true;
};

/**
 * Submit knowledge form
 */
const submitKnowledge = async (formEl: FormInstance | undefined) => {
	if (!newKnowledge.value.title) {
		ElMessage.warning("Please enter a title");
		return;
	}
	if (!formEl) return;
	if (knowledgeTextList.value.length === 0) {
		ElMessage.warning("Please make sure to input at least one content item!");
		return;
	}
	for (let valueElement of knowledgeTextList.value) {
		if (valueElement.length < 2 || valueElement.length > 1000) {
			ElMessage.warning("Each fragment must be between 2 and 1000 characters!");
			return;
		}
	}
	if (newKnowledge.value.type === "join" && newKnowledge.value.relations_roles.length <= 1) {
		ElMessage.warning("When selecting shared memory, you must select multiple roles!");
		return;
	}

	await formEl.validate(async (valid, fields) => {
		if (valid) {
			// Filter empty content
			const validTexts = knowledgeTextList.value.filter((text) => text.trim() !== "");

			if (validTexts.length === 0) {
				ElMessage.warning("Please enter at least one valid content");
				return;
			}

			try {
				const baseData: any = {
					role_id: newKnowledge.value.role_id,
					type: newKnowledge.value.type,
					grade: newKnowledge.value.grade,
					source: "Knowledge Platform Entry" || undefined,
					tags: (newKnowledge.value.tags || []).join(","),
					relations_role: (newKnowledge.value.relations_roles || []).join(","),
				};

				if (knowledgeDialogType.value === "add") {
					// Add mode: add each content as a separate knowledge entry
					const baseTitle = newKnowledge.value.title;
					// If there's only one content, use the original title
					if (validTexts.length === 1) {
						baseData["text"] = validTexts[0];
						baseData["title"] = baseTitle;
						await createRoleKnowledge(baseData);
					} else {
						// Multiple contents, create separate knowledge entries for each content, add sequence number to titles
						const promises = validTexts.map((text, index) => {
							baseData["text"] = text;
							baseData["title"] = `${baseTitle}${index + 1}`;
							return createRoleKnowledge(baseData);
						});
						await Promise.all(promises);
					}
					ElMessage.success("Knowledge added successfully");
				} else {
					baseData["text"] = knowledgeTextList.value[0];
					baseData["title"] = newKnowledge.value.title;
					// Edit mode: only modify the currently selected knowledge entry
					await updateRoleKnowledge(currentEditKnowledge.value, baseData);
					ElMessage.success("Knowledge updated successfully");
				}
				knowledgeDialogVisible.value = false;
				emit("refresh");
			} catch (error) {
				console.error(knowledgeDialogType.value === "add" ? "Failed to add knowledge" : "Failed to update knowledge", error);
				ElMessage.error(knowledgeDialogType.value === "add" ? "Failed to add knowledge" : "Failed to update knowledge");
			}
		} else {
			console.log("error submit!", fields);
		}
	});
};

function handleTypeChange() {
	newKnowledge.value.relations_roles = [props.roleId];
}

const role_list = ref<Role[]>([]);
const role_list_total = ref(0);

async function get_role_list() {
	try {
		const response = await getRoleList({ page: 1, size: 100 });
		if (response && response.items) {
			role_list.value = response.items;
			role_list_total.value = response.total;
		} else {
			role_list.value = [];
			role_list_total.value = 0;
		}
	} catch (error) {
		console.error("Failed to get role list (for selection):", error);
		role_list.value = [];
		role_list_total.value = 0;
	}
}

const activeName = ref("base");

const ruleFormRef = ref<FormInstance>();
const formRules = reactive<FormRules>({
	title: [
		{ required: true, message: "Please enter a relationship name", trigger: "blur" },
		{ min: 1, max: 10, message: "Length should be between 1 and 10 characters", trigger: "blur" },
	],
});

// Knowledge base search dialog
const searchDialogVisible = ref(false);

/**
 * Open knowledge base search dialog
 */
const openSearchDialog = () => {
	searchDialogVisible.value = true;
};
</script>

<template>
	<div class="knowledge-section">
		<div class="custom-tabs-container">
			<!-- Left tab area -->
			<div class="tabs-sidebar">
				<!-- Top: tabs -->
				<div class="tabs-nav">
					<div class="tab-item" :class="{ active: activeName === 'base' }" @click="activeName = 'base'">
						<el-icon>
							<User />
						</el-icon>
						<span>Role Memory</span>
					</div>
					<div class="tab-item" :class="{ active: activeName === 'join' }" @click="activeName = 'join'">
						<el-icon>
							<UserFilled />
						</el-icon>
						<span>Shared Experience</span>
					</div>
				</div>

				<!-- Bottom: action buttons -->
				<div class="tabs-actions">
					<div>
						<el-button type="info" size="small" @click="openSearchDialog" class="action-btn">
							<el-icon>
								<Search />
							</el-icon>
							Search Similarity
						</el-button>
					</div>
					<div>
						<el-button  type="primary" size="small" @click="addNewKnowledge" class="action-btn btn-fix">
							<el-icon>
								<Plus />
							</el-icon>
							Add Knowledge
						</el-button>
					</div>
				</div>
			</div>

			<!-- Right content area -->
			<div class="tabs-content">
				<!-- Role memory content -->
				<div v-show="activeName === 'base'" class="tab-pane">
					<div class="knowledge-list" v-loading="loading">
						<el-empty v-if="knowledgeList.length === 0" description="No knowledge fragments available" />
						<div class="knowledge-grid" v-else>
							<el-card v-for="knowledge in knowledgeList" :key="knowledge.id" class="knowledge-card" shadow="hover">
								<div class="card-content">
									<div class="knowledge-header">
										<div class="knowledge-title">
											{{ knowledge.title }} <span class="knowledge-grade">V{{ knowledge.grade }}</span>
										</div>
										<el-tag
											:type="
												knowledge.type === '基本经历' ? 'success' : knowledge.type === '角色经历' ? 'warning' : 'info'
											"
										>
											{{ knowledge.type }}
										</el-tag>
									</div>
									<div class="knowledge-preview">
										{{ knowledge.text }}
									</div>
									<div class="knowledge-tags">
										Tags:
										<el-tag
											size="small"
											v-for="tag in (knowledge.tags || 'Empty').split(',')"
											:key="tag"
											style="margin-left: 5px"
										>
											{{ tag }}
										</el-tag>
									</div>
								</div>
								<template #footer>
									<div class="knowledge-meta">
										<div class="knowledge-source">Source: {{ knowledge.source }}</div>
										<div class="knowledge-actions">
											<el-button type="primary" link @click="editKnowledge(knowledge)">
												<el-icon>
													<Edit />
												</el-icon>
												Edit
											</el-button>
											<el-button type="danger" link @click="deleteKnowledge(knowledge)">
												<el-icon>
													<Delete />
												</el-icon>
												Delete
											</el-button>
										</div>
									</div>
								</template>
							</el-card>
						</div>
					</div>
				</div>

				<!-- Shared experience content -->
				<div v-show="activeName === 'join'" class="tab-pane">
					<div class="knowledge-list" v-loading="loading">
						<el-empty v-if="knowledgeJoinList.length === 0" description="No knowledge fragments available" />
						<div class="knowledge-grid" v-else>
							<el-card v-for="knowledge in knowledgeJoinList" :key="knowledge.id" class="knowledge-card" shadow="hover">
								<div class="card-content">
									<div class="knowledge-header">
										<div class="knowledge-title">
											{{ knowledge.title }} <span class="knowledge-grade">V{{ knowledge.grade }}</span>
										</div>
										<el-tag
											:type="
												knowledge.type === '基本经历' ? 'success' : knowledge.type === '角色经历' ? 'warning' : 'info'
											"
										>
											{{ knowledge.type }}
										</el-tag>
									</div>
									<div class="knowledge-preview">
										{{ knowledge.text }}
									</div>
								</div>
								<template #footer>
									<div class="knowledge-meta">
										<div class="knowledge-source">Source: {{ knowledge.source }}</div>
										<div class="knowledge-actions">
											<el-button type="primary" link @click="editKnowledge(knowledge)">
												<el-icon>
													<Edit />
												</el-icon>
												Edit
											</el-button>
											<el-button type="danger" link @click="deleteKnowledge(knowledge)">
												<el-icon>
													<Delete />
												</el-icon>
												Delete
											</el-button>
										</div>
									</div>
								</template>
							</el-card>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- Add knowledge dialog -->
		<el-dialog
			v-model="knowledgeDialogVisible"
			:title="knowledgeDialogType === 'add' ? 'Add Knowledge Fragment' : 'Edit Knowledge Fragment'"
			width="80%"
		>
			<div class="knowledge-dialog-content">
				<div class="knowledge-form-container">
					<el-form :model="newKnowledge" :rules="formRules" ref="ruleFormRef" label-width="100px">
						<FormItem label="Type" tooltipKey="type">
							<el-select
								v-model="newKnowledge.type"
								:disabled="knowledgeDialogType !== 'add'"
								@change="handleTypeChange"
								placeholder="Please select type"
							>
								<el-option
									v-for="type in selectKnowledgeType"
									:key="type.value"
									:label="type.label"
									:value="type.value"
								/>
							</el-select>
						</FormItem>
						<FormItem label="Title" prop="title" tooltipKey="title">
							<el-input v-model="newKnowledge.title" placeholder="Please enter title" />
						</FormItem>
						<FormItem label="Content" required tooltipKey="knowledgeTextList[index]">
							<div v-for="(text, index) in knowledgeTextList" :key="index" class="text-item-container">
								<AvatarEditor
									:users="rolePrompt"
									:max-length="3000"
									:min-length="10"
									min-height="100px"
									placeholder="Please enter knowledge content..."
									v-model="knowledgeTextList[index]"
								/>
								<div class="text-item-actions">
									<el-button
										type="danger"
										circle
										size="small"
										@click="removeTextItem(index)"
										:disabled="knowledgeTextList.length === 1"
									>
										<el-icon>
											<Delete />
										</el-icon>
									</el-button>
								</div>
							</div>
							<div class="add-text-button">
								<el-button type="primary" plain size="small" @click="addTextItem" v-if="knowledgeDialogType === 'add'">
									<el-icon>
										<Plus />
									</el-icon>
									Add Content Item
								</el-button>
							</div>
						</FormItem>
						<FormItem label="Level" tooltipKey="grade">
							<el-input-number v-model="newKnowledge.grade" :precision="1" :min="0" :max="100" :step="0.1" />
						</FormItem>
						<!--						<FormItem label="Source" tooltipKey="source">-->
						<!--							<el-input v-model="newKnowledge.source" placeholder="Please enter source" />-->
						<!--						</FormItem>-->
						<FormItem label="Tags" tooltipKey="tags">
							<el-input-tag v-model="newKnowledge.tags" :max="6" placeholder="Please enter tags" />
						</FormItem>
						<FormItem label="Select Roles" v-if="newKnowledge.type === 'join'" tooltipKey="relations_roles">
							<el-select v-model="newKnowledge.relations_roles" multiple>
								<el-option
									v-for="role in role_list"
									:key="role.id"
									:label="`${role.name}(${role.role_id})`"
									:value="role.role_id"
									:disabled="role.role_id === props.roleId"
								/>
							</el-select>
						</FormItem>
					</el-form>
				</div>

				<div class="knowledge-enhance-container" v-if="knowledgeDialogType === 'add'">
					<h4 class="enhance-title">AI Enhanced Knowledge Fragment</h4>
					<el-divider />

					<el-form>
						<FormItem label="Prompt" tooltipKey="enhancePrompt">
							<el-input v-model="enhancePrompt" type="textarea" :rows="3" placeholder="Please enter AI enhancement prompt" />
							<div class="prompt-hint">Prompt will be saved in your local browser</div>
						</FormItem>

						<FormItem label="Model" tooltipKey="selectedModelId">
							<ModelCascader v-model="selectedModelId" />
						</FormItem>

						<el-form-item>
							<el-button
								type="primary"
								@click="handleEnhanceContent"
								:loading="isEnhancing"
								:disabled="!knowledgeTextList.some((text) => text.trim() !== '')"
							>
								<el-icon>
									<Magic />
								</el-icon>
								Enhance Content
							</el-button>
						</el-form-item>
					</el-form>

					<div class="enhanced-results" v-if="enhancedResults.length > 0">
						<h5>Enhancement Results:</h5>
						<el-scrollbar height="200px">
							<div
								v-for="(result, index) in enhancedResults"
								:key="index"
								class="enhanced-result-item"
								@click="selectEnhancedContent(result)"
							>
								<p>{{ result }}</p>
								<el-divider />
							</div>
						</el-scrollbar>
						<div class="result-hint">Click any result to apply it to the content field on the left</div>
					</div>
				</div>
			</div>

			<template #footer>
				<span class="dialog-footer">
					<el-button @click="knowledgeDialogVisible = false">Cancel</el-button>
					<el-button type="primary" @click="submitKnowledge(ruleFormRef)">Confirm</el-button>
				</span>
			</template>
		</el-dialog>

		<!-- Knowledge base search dialog -->
		<KnowledgeSearchDialog v-model:visible="searchDialogVisible" :role-id="roleId" />
	</div>
</template>

<style scoped lang="scss">
.knowledge-section {
	padding: 0;
	height: 100%;
}

/* Custom tab container */
.custom-tabs-container {
	display: flex;
	height: 500px;
	border: 1px solid #e2e8f0;
	border-radius: 8px;
	overflow: hidden;
	background: #ffffff;
}

/* Left tab area */
.tabs-sidebar {
	width: 200px;
	background: #f8fafc;
	border-right: 1px solid #e2e8f0;
	display: flex;
	flex-direction: column;
	justify-content: space-between;
}

/* Tab navigation area */
.tabs-nav {
	padding: 12px 0;
	border-bottom: 1px solid #e2e8f0;
}

.tab-item {
	display: flex;
	align-items: center;
	gap: 8px;
	padding: 12px 16px;
	margin: 2px 8px;
	border-radius: 6px;
	cursor: pointer;
	transition: all 0.3s ease;
	color: #64748b;
	font-size: 14px;
	font-weight: 500;
}

.tab-item:hover {
	background: #e2e8f0;
	color: #1e293b;
}

.tab-item.active {
	background: #2563eb;
	color: #ffffff;
	box-shadow: 0 2px 4px rgba(37, 99, 235, 0.3);
}

.tab-item .el-icon {
	font-size: 16px;
}

/* Action buttons area */
.tabs-actions {
	padding: 16px 8px;
	display: flex;
	flex-direction: column;
	gap: 8px;
}

.action-btn {
	width: 100%;
	justify-content: flex-start;
	padding: 8px 12px;
	border-radius: 6px;
	font-size: 13px;
}

.action-btn .el-icon {
	margin-right: 6px;
}

/* Right content area */
.tabs-content {
	flex: 1;
	background: #ffffff;
	overflow: hidden;
}

.tab-pane {
	height: 100%;
	padding: 20px;
	overflow-y: auto;
}

/* Knowledge list */
.knowledge-list {
	height: 100%;
	overflow-y: auto;
}

/* Knowledge card styles */
.knowledge-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
	gap: 16px;
	padding-bottom: 20px;
}

.knowledge-card {
	position: relative;
	background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
	border: 1px solid #e2e8f0;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	transition: all 0.3s ease;
	min-height: 260px;
	height: auto;
	display: flex;
	flex-direction: column;
}

.knowledge-card:hover {
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
	border-color: #2563eb;
}

.knowledge-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 15px;
}

.knowledge-grade {
	font-size: 12px;
	color: #64748b;
	margin-left: 5px;
	font-weight: normal;
}

.knowledge-title {
	font-size: 16px;
	margin: 0 0 12px 0;
	color: #1e293b;
	font-weight: 600;
	line-height: 1.4;
	display: flex;
	align-items: center;
}

.knowledge-preview {
	background: #f8fafc;
	border-radius: 6px;
	padding: 12px;
	margin-bottom: 12px;
	font-size: 14px;
	line-height: 1.5;
	color: #64748b;
	max-height: 90px;
	overflow: hidden;
	position: relative;
	border: 1px solid #e2e8f0;
	flex: 1;
}

.knowledge-preview::after {
	content: "";
	position: absolute;
	bottom: 0;
	left: 0;
	right: 0;
	height: 30px;
	background: linear-gradient(transparent, #f8fafc);
}

.card-content {
	display: flex;
	flex-direction: column;
	height: 100%;
	min-height: 200px;
}

.knowledge-tags {
	margin-top: 8px;
	margin-bottom: 8px;
}

.knowledge-meta {
	display: flex;
	flex-wrap: wrap;
	font-size: 12px;
	color: #64748b;
	justify-content: space-between;
	margin-bottom: 12px;
	margin-top: auto;
}

.knowledge-source {
	display: flex;
	align-items: center;
	gap: 5px;
	font-size: 12px;
	color: #64748b;
}

.knowledge-actions {
	display: flex;
	gap: 10px;
}

/* Knowledge dialog styles */
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

.result-hint {
	font-size: 12px;
	color: var(--el-text-color-secondary);
	margin-top: 8px;
	text-align: center;
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

/* Responsive design */
@media (max-width: 1200px) {
	.tabs-sidebar {
		width: 180px;
	}

	.knowledge-grid {
		grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
	}
}

@media (max-width: 768px) {
	.custom-tabs-container {
		height: 600px;
		flex-direction: column;
	}

	.tabs-sidebar {
		width: 100%;
		height: 120px;
		border-right: none;
		border-bottom: 1px solid #e2e8f0;
		flex-direction: row;
	}

	.tabs-nav {
		display: flex;
		padding: 8px;
		border-bottom: none;
		border-right: 1px solid #e2e8f0;
		flex: 1;
	}

	.tab-item {
		margin: 0 4px;
		white-space: nowrap;
	}

	.tabs-actions {
		padding: 8px;
		flex-direction: row;
		width: 180px;
		gap: 4px;
	}

	.action-btn {
		width: auto;
		font-size: 12px;
		padding: 6px 8px;
	}

	.knowledge-grid {
		grid-template-columns: 1fr;
	}
}

@import '@/layouts/WriterLayout/css/extra.scss';
.btn-fix {
	color: #fff;
	background-color: $btn-bg-color0;
	border-color: $btn-bg-color0;
}
</style>
