<!-- KnowledgeDialog.vue - Add/Edit Knowledge Dialog Component -->
<script setup lang="ts">
import { ref, watch, onMounted, reactive } from "vue";
import { ElMessage, FormInstance, type FormRules } from "element-plus";
import { Delete, Plus } from "@element-plus/icons-vue";
import { Magnet as Magic } from "@element-plus/icons-vue";
import { enhanceContentTokenStream } from "@/api/llm";
import type { WorldKnowledgeCreate, World } from "@/types/world";
import {
	getWorldList,
	getKnowledgeByWorld,
	getWorldKnowledgeDetailByIds,
	getWorldKnowledgeDetailByWorldIds,
} from "@/api/world";
import { rolePrompt } from "@/utils/editorButton";
import AvatarEditor from "@/components/AvatarEditor/AvatarEditor.vue";
import ModelCascader from "@/components/ModelCascader.vue";

/**
 * Component props interface
 */
interface Props {
	visible: boolean;
	dialogType: "add" | "edit";
	worldId: string;
	currentKnowledge: WorldKnowledgeCreate;
	selectKnowledgeType: any[];
	allRolesList: any[];
	allRolesLoading: boolean;
}

const props = defineProps<Props>();

/**
 * Define component emitted events
 */
const emit = defineEmits<{
	"update:visible": [value: boolean];
	confirm: [knowledge: WorldKnowledgeCreate, textList: string[]];
	search: [keyword: string];
}>();

/**
 * Multiple text input list
 */
const knowledgeTextList = ref<string[]>([""]);

// ===== Related knowledge =====
/**
 * World list
 */
const worldList = ref<World[]>([]);
/**
 * World loading state
 */
const worldLoading = ref(false);
/**
 * Knowledge loading state
 */
const knowledgeLoading = ref(false);
/**
 * Selected related knowledge
 */
const selectedRelations = ref<string[]>([]);
const knowledgeList = ref<any[]>([]);
/**
 * Cascader configuration
 */

const lazyLoad = async (node: any, resolve: (nodes: any[]) => void) => {
	const { level, value } = node;
	// First level loads all worlds
	if (level === 0) {
		worldLoading.value = true;
		try {
			const response = await getWorldList({ page: 1, size: 100 });
			if (response) {
				const nodes = response.items.map((world: World) => ({
					value: world.id,
					label: `${world.title} (${world.type})`,
					leaf: false, // First level is not a leaf node, can be expanded
				}));
				resolve(nodes);
			} else {
				resolve([]);
			}
		} catch (error) {
			console.error("Failed to load world list:", error);
			resolve([]);
		} finally {
			worldLoading.value = false;
		}
	}
	// Second level loads knowledge
	else if (level === 1) {
		knowledgeLoading.value = true;
		try {
			const response = await getKnowledgeByWorld(value);
			if (response) {
				const nodes = response.map((item: any) => ({
					value: item.id,
					label: item.title,
					leaf: true,
				}));
				resolve(nodes);
			} else {
				resolve([]);
			}
		} catch (error) {
			console.error("Failed to load knowledge list:", error);
			resolve([]);
		} finally {
			knowledgeLoading.value = false;
		}
	}
};

const cascaderProps = ref({
	lazy: true,
	multiple: true,
	checkStrictly: false, // Only allow selecting leaf nodes
	emitPath: true, // Return full path when selecting
	lazyLoad: lazyLoad,
});
/**
 * Cascader selected values
 */
const cascaderValue = ref<any[]>([]);

/**
 * Watch cascader value changes, update related knowledge
 */
watch(cascaderValue, (newVal) => {
	// Since checkStrictly is set to false, only leaf nodes will be selected
	// Each selected item is an array, like [worldId, knowledgeId]
	const knowledgeIds = newVal.map((path) => path[1]); // Take the second value of each path (knowledge ID)

	// Update selectedRelations and newKnowledge.relations
	selectedRelations.value = knowledgeIds;
	newKnowledge.value.relations = knowledgeIds.join(",");
});

/**
 * Initialize from cascader selected value, display related knowledge
 */
const initCascaderValue = async () => {
	knowledgeList.value = [];
	cascaderProps.value.lazyLoad = async (node: any, resolve: (nodes: any[]) => void) => {
		return lazyLoad(node, resolve);
	};
	if (!props.currentKnowledge.relations) {
		cascaderValue.value = [];
		return;
	}
	const relationIds = props.currentKnowledge.relations.split(",");
	selectedRelations.value = relationIds;
	const allWorlds = await getWorldList({ page: 1, size: 100 });
	const idsList = await getWorldKnowledgeDetailByIds(props.currentKnowledge.relations);
	const idsListWorldIds = idsList.map((item) => item.worlds_id.toString());
	const allWorldKnowledge = await getWorldKnowledgeDetailByWorldIds(idsListWorldIds.join(","));
	// debugger;
	for (const world of allWorlds.items) {
		const data = {
			value: world.id,
			label: world.title,
			leaf: false,
			children: allWorldKnowledge
				.filter((item) => {
					return (
						item.worlds_id.toString() === world.id.toString() &&
						props.currentKnowledge.id.toString() !== item.id.toString()
					);
				})
				.map((item) => {
					return {
						value: item.id.toString(),
						label: item.title,
						leaf: true,
					};
				}),
		};

		knowledgeList.value.push(data);
	}

	cascaderProps.value.lazyLoad = async (node: any, resolve: (nodes: any[]) => void) => {
		const { level, value } = node;
		// First level loads all worlds
		if (level === 0) {
			worldLoading.value = true;
			try {
				resolve(knowledgeList.value);
			} catch (error) {
				console.error("Failed to get world list", error);
				resolve([]);
			} finally {
				worldLoading.value = false;
			}
		}
		// Second level loads knowledge items of the selected world
		else if (level === 1) {
			knowledgeLoading.value = true;
			try {
				const response = await getKnowledgeByWorld(value);
				if (response) {
					// Filter out the knowledge currently being edited (can't link to itself)
					const filteredKnowledge = response.filter(
						(item) => props.dialogType !== "edit" || item.id.toString() !== newKnowledge.value.id?.toString(),
					);
					const nodes = filteredKnowledge.map((knowledge: any) => ({
						value: knowledge.id.toString(),
						label: knowledge.title,
						leaf: true, // Second level is leaf node, can be selected
						// Add additional data for display
						data: {
							type: knowledge.type,
							preview: knowledge.text.substring(0, 50) + "...",
						},
					}));
					resolve(nodes);
				} else {
					resolve([]);
				}
			} catch (error) {
				console.error("Failed to get world knowledge list", error);
				resolve([]);
			} finally {
				knowledgeLoading.value = false;
			}
		} else {
			resolve([]);
		}
	};

	cascaderValue.value = idsList.map((item) => [item.worlds_id, item.id.toString()]);
	console.log(cascaderValue.value);
};

/**
 * Load world list
 */
const fetchWorldList = async () => {
	worldLoading.value = true;
	try {
		const response = await getWorldList({ page: 1, size: 100 });
		if (response) {
			worldList.value = response.items;
		}
	} catch (error) {
		console.error("Failed to get world list", error);
	} finally {
		worldLoading.value = false;
	}
};

/**
 * AI enhancement related data
 */
const enhancePrompt = ref(`Your task is to enhance the following content semantically for better vector database retrieval. Please follow these guidelines:

1. Content should be detailed and specific, avoiding excessive abstraction. Each block should be independent and complete, facilitating relevant context return during vector database retrieval.
2. Natural language expression: Describe information in a coherent narrative style to help vector embeddings better capture semantic relationships.

Output requirements: Separate each block with two line breaks`);

const isEnhancing = ref(false);
const enhancedResults = ref<string[]>([]);

/**
 * Model selection - use unified modelId
 */
const selectedModelId = ref("");

/**
 * Initialize component
 */
function init() {
	// Get prompt from local storage
	const savedPrompt = localStorage.getItem("aiEnhancePrompt");
	if (savedPrompt) {
		enhancePrompt.value = savedPrompt;
	}

	// Get saved model settings
	const savedModelId = localStorage.getItem("aiEnhanceModelId");
	if (savedModelId) {
		selectedModelId.value = savedModelId;
	}
}

// Call initialization
init();

/**
 * Watch dialog visibility, initialize data when shown
 */
watch(
	() => props.visible,
	async (newVal) => {
		if (newVal) {
			// Copy current knowledge to local state
			newKnowledge.value = { ...props.currentKnowledge };

			// If edit mode, put text in first text box
			if (props.dialogType === "edit") {
				knowledgeTextList.value = [props.currentKnowledge.text || ""];
				newKnowledge.value.relations_roles = props.currentKnowledge.relations_role?.split(",");
			} else {
				// Add mode, initialize with one empty text box
				knowledgeTextList.value = [""];
			}

			// Reset enhancement results
			enhancedResults.value = [];

			// Initialize related knowledge
			await initCascaderValue();
		}
	},
);

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
 * AI enhance content method
 */
const handleEnhanceContent = () => {
	// Find first non-empty content
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
	const rawChunks: string[] = []; // Store all raw data chunks for debugging
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
		// Handle processed token
		() => {},
		// Handle raw data chunk
		(rawChunk) => {
			currentBuffer += rawChunk;
			rawChunks.push(rawChunk);
			// Check for paragraph separators, if complete paragraph then add to results
			const parts = rawChunks.join("").split("\n\n");
			// Add all complete paragraphs except the last part to results
			enhancedResults.value[parts.length - 1] = parts[parts.length - 1];
			// Keep last part in buffer to continue
		},
		// Handle error
		(error) => {
			console.error("Request error:", error);
			ElMessage.error("Content enhancement request failed");
		},
	)
		.then((response: any) => {
			// Request complete, check if there's remaining content in buffer
			if (currentBuffer.trim()) {
				enhancedResults.value.push(currentBuffer.trim());
			}

			// If needed, can view all raw data received
			console.log("All raw data chunks:", rawChunks);
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
 * Select enhanced content method
 * @param {string} content - Selected enhanced content
 */
const selectEnhancedContent = (content: string) => {
	knowledgeTextList.value.push(content);
	ElMessage.success("Enhanced content added");
};

/**
 * Add content item method
 */
const addTextItem = () => {
	knowledgeTextList.value.push("");
};

/**
 * Remove content item method
 * @param {number} index - Index of item to remove
 */
const removeTextItem = (index: number) => {
	if (knowledgeTextList.value.length > 1) {
		knowledgeTextList.value.splice(index, 1);
	} else {
		ElMessage.warning("At least one content item must be kept");
	}
};

/**
 * Search roles
 * @param {string} query - Search keyword
 */
const searchRoles = (query: string) => {
	emit("search", query);
};
searchRoles("");
/**
 * Submit knowledge form
 */
const submitKnowledge = async (formEl: FormInstance | undefined) => {
	if (!newKnowledge.value.title) {
		ElMessage.warning("Please enter a title");
		return;
	}

	if (!formEl) return;
	await formEl.validate((valid, fields) => {
		if (valid) {
			// Filter empty content
			const validTexts = knowledgeTextList.value.filter((text) => text.trim() !== "");

			if (validTexts.length === 0) {
				ElMessage.warning("Please fill in at least one valid content");
				return;
			}

			// Store knowledge network
			newKnowledge.value.relations = cascaderValue.value
				.map((item) => {
					return item[1];
				})
				.join(",");
			newKnowledge.value.relations_role = (newKnowledge.value.relations_roles || []).join(",");

			emit("confirm", newKnowledge.value, validTexts);
		} else {
			console.log("error submit!", fields);
		}
	});
};

/**
 * Close dialog
 */
const closeDialog = () => {
	emit("update:visible", false);
};

/**
 * Dialog open and close event handler
 */
const handleDialogChange = (val: boolean) => {
	emit("update:visible", val);
};

// Load world list after component mounting
onMounted(() => {
	fetchWorldList();
});

// Fix relations_roles type
const newKnowledge: any = ref<WorldKnowledgeCreate>({
	id: "",
	worlds_id: props.worldId,
	text: "",
	type: "base",
	title: "",
	source: "",
	tags: "",
	grade: 5,
	relations: "",
	relations_role: "",
	relations_roles: [] as string[],
});

// Fix split method usage
watch(
	() => props.currentKnowledge,
	(newVal) => {
		if (newVal) {
			newKnowledge.value = {
				...newVal,
				relations_roles: newVal.relations_role ? newVal.relations_role.split(",") : [],
			};
		}
	},
	{ immediate: true },
);

const ruleFormRef = ref<FormInstance>();
const formRules = reactive<FormRules>({
	title: [
		{ required: true, message: "Please enter a title", trigger: "blur" },
		{ min: 1, max: 64, message: "Length should be between 1 and 64 characters", trigger: "blur" },
	],
});
</script>

<template>
	<el-dialog
		:modelValue="visible"
		@update:model-value="handleDialogChange"
		:title="dialogType === 'add' ? 'Add Knowledge Fragment' : 'Edit Knowledge Fragment'"
		width="80%"
	>
		<div class="knowledge-dialog-content">
			<div class="knowledge-form-container">
				<el-form :model="newKnowledge" label-width="100px" :rules="formRules" ref="ruleFormRef">
					<FormItem label="Type" tooltipKey="type">
						<el-select v-model="newKnowledge.type" placeholder="Please select type">
							<el-option
								v-for="select in selectKnowledgeType"
								:key="select.value"
								:label="select.label"
								:value="select.value"
							/>
						</el-select>
					</FormItem>
					<FormItem label="Title" prop="title" tooltipKey="title">
						<el-input v-model="newKnowledge.title" placeholder="Please enter title" />
					</FormItem>
					<FormItem label="Content" tooltipKey="knowledgeTextList[index]">
						<div v-for="(text, index) in knowledgeTextList" :key="index" class="text-item-container">
							<AvatarEditor
								:users="rolePrompt"
								:max-length="3000"
								:min-length="10"
								min-height="100px"
								placeholder="Please enter knowledge content..."
								v-model="knowledgeTextList[index]"
							/>
							<div class="text-item-actions" v-if="dialogType === 'add'">
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
						<div class="add-text-button" v-if="dialogType === 'add'">
							<el-button type="primary" plain size="small" @click="addTextItem">
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
					<FormItem label="Tags" tooltipKey="tags">
						<el-input-tag v-model="newKnowledge.tags" :max="6" placeholder="Please enter tags" />
					</FormItem>
					<FormItem label="Related Knowledge" tooltipKey="cascaderValue">
						<el-cascader
							v-model="cascaderValue"
							placeholder="Please select related knowledge"
							clearable
							:props="cascaderProps"
							filterable
							:loading="knowledgeLoading || worldLoading"
							style="width: 100%"
						>
							<template #default="{ node, data }">
								<span v-if="node.level === 1">
									<span class="knowledge-cascader-node">
										<span class="knowledge-cascader-title">{{ data.label }}</span>
										<span class="knowledge-cascader-info" v-if="data.data">
											<el-tag size="small" :type="data.data.type === '场景' ? 'success' : 'warning'">
												{{ data.data.type === '场景' ? 'Scene' : 'Basic' }}
											</el-tag>
											<span class="knowledge-cascader-preview">{{ data.data.preview }}</span>
										</span>
									</span>
								</span>
								<span v-else>
									{{ data.label }}
								</span>
							</template>
						</el-cascader>
					</FormItem>
					<FormItem label="Related Roles" tooltipKey="relations_roles">
						<el-select
							v-model="newKnowledge.relations_roles"
							multiple
							filterable
							remote
							reserve-keyword
							placeholder="Please enter role name to search"
							:remote-method="searchRoles"
							:loading="allRolesLoading"
							style="width: 100%"
						>
							<el-option
								v-for="role in allRolesList"
								:key="role.id"
								:label="`${role.name}(${role.role_id})`"
								:value="role.role_id"
							>
								<div class="role-option">
									<div class="role-option-info">
										<div class="role-option-name">{{ `${role.name}(${role.role_id})` }}</div>
									</div>
								</div>
							</el-option>
						</el-select>
					</FormItem>
				</el-form>
			</div>

			<div class="knowledge-enhance-container" v-if="dialogType === 'add'">
				<h4 class="enhance-title">AI Enhanced Knowledge Fragment</h4>
				<el-divider />

				<el-form>
					<FormItem label="Prompt" tooltipKey="enhancePrompt">
						<el-input v-model="enhancePrompt" type="textarea" :rows="3" placeholder="Please enter AI enhancement prompt" />
						<div class="prompt-hint">Prompt will be saved in local browser</div>
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
						<div class="results-container">
							<div
								v-for="(result, index) in enhancedResults"
								:key="index"
								class="enhanced-result-item"
								@click="selectEnhancedContent(result)"
							>
								<p>{{ result }}</p>
								<el-divider />
							</div>
						</div>
					</el-scrollbar>
					<div class="result-hint">Click any result to apply to content box on the left</div>
				</div>
			</div>
		</div>

		<template #footer>
			<span class="dialog-footer">
				<el-button @click="closeDialog">Cancel</el-button>
				<el-button type="primary" @click="submitKnowledge(ruleFormRef)">Confirm</el-button>
			</span>
		</template>
	</el-dialog>
</template>

<style scoped>
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

/* Role option styles */
.role-option {
	display: flex;
	align-items: center;
	padding: 5px 0;
}

.role-option-info {
	display: flex;
	flex-direction: column;
}

.role-option-name {
	font-size: 14px;
	color: var(--el-text-color-primary);
}

/* Related knowledge selector styles */
.relation-selects {
	display: flex;
	gap: 10px;
	width: 100%;
}

.world-select {
	width: 40%;
}

.knowledge-select {
	width: 60%;
}

.knowledge-cascader-node {
	display: flex;
	align-items: center;
}

.knowledge-cascader-title {
	font-weight: bold;
	font-size: 14px;
	color: var(--el-text-color-primary);
}

.knowledge-cascader-info {
	margin-left: 8px;
}

.knowledge-cascader-preview {
	font-size: 12px;
	color: var(--el-text-color-secondary);
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}
</style>
