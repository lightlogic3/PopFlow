<script setup lang="ts">
import { ref, watch, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Delete, Plus } from "@element-plus/icons-vue";
import { getRoleWorldWithDetails, deleteRoleWorld, createRoleWorld } from "@/api/roleWorld";
import { getAllWorldList } from "@/api/world";
import { getWorldKnowledgeByWorldId } from "@/api/world";
import { formatDate } from "@/utils";

/**
 * Role-World Association Knowledge Component
 * Directly associates character with worldview knowledge
 */

// Receive parameters passed from parent component
const props = defineProps({
	roleId: {
		type: String,
		required: true,
	},
	loading: {
		type: Boolean,
		default: false,
	},
});

// Notify parent component to refresh data
const emit = defineEmits(["refresh"]);

// Role-world knowledge association list
const roleWorldLoading = ref(false);
const roleWorldList = ref<any[]>([]);
const knowledgeDetailsMap = ref<Record<string, any>>({});
const worldsDetailsMap = ref<Record<string, any>>({});
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);

// World list
const worldList = ref<any[]>([]);
const worldLoading = ref(false);

// Association dialog
const dialogVisible = ref(false);
const dialogLoading = ref(false);
const selectedWorld = ref<any>(null);
const worldKnowledgeList = ref<any[]>([]);
const worldKnowledgeLoading = ref(false);
const selectedWorldKnowledge = ref<any[]>([]); // Changed to array to support multiple selection
const worldKnowledgeDetail = ref("");

/**
 * Get list of world knowledge points associated with the character
 * Using optimized API to get all data at once
 */
const fetchRoleWorldList = async () => {
	roleWorldLoading.value = true;
	try {
		const response = await getRoleWorldWithDetails(props.roleId, {
			skip: (currentPage.value - 1) * pageSize.value,
			limit: pageSize.value,
		});

		// Parse the data structure returned by API
		roleWorldList.value = response.relations || [];
		total.value = response.relations?.length || 0;

		// Store knowledge points and world details
		knowledgeDetailsMap.value = response.world_knowledge || {};
		worldsDetailsMap.value = response.worlds || {};

		// If world list is empty, load world list
		if (Object.keys(worldsDetailsMap.value).length === 0 && !worldLoading.value) {
			fetchWorldList();
		}
	} catch (error) {
		console.error("Failed to get world knowledge points associated with the character", error);
		ElMessage.error("Failed to get world knowledge points associated with the character");
	} finally {
		roleWorldLoading.value = false;
	}
};

/**
 * Get world list
 */
const fetchWorldList = async () => {
	worldLoading.value = true;
	try {
		const response = await getAllWorldList(); // Use new non-paginated API
		worldList.value = response || [];
	} catch (error) {
		console.error("Failed to get world list", error);
		ElMessage.error("Failed to get world list");
	} finally {
		worldLoading.value = false;
	}
};

/**
 * Get world knowledge point list
 */
const fetchWorldKnowledgeList = async (worldId: string) => {
	if (!worldId) return;

	worldKnowledgeLoading.value = true;
	try {
		const response = await getWorldKnowledgeByWorldId(worldId, {
			page: 1,
			size: 100,
		});
		worldKnowledgeList.value = response.items || response || [];
	} catch (error) {
		console.error("Failed to get world knowledge point list", error);
		ElMessage.error("Failed to get world knowledge point list");
	} finally {
		worldKnowledgeLoading.value = false;
	}
};

/**
 * Open add association dialog
 */
const openAddDialog = async () => {
	dialogVisible.value = true;
	selectedWorld.value = null;
	selectedWorldKnowledge.value = []; // Clear to empty array
	worldKnowledgeDetail.value = "";
	worldKnowledgeList.value = [];

	dialogLoading.value = true;
	try {
		await fetchWorldList();
	} finally {
		dialogLoading.value = false;
	}
};

/**
 * Delete association
 */
const handleDelete = async (id: number) => {
	try {
		await ElMessageBox.confirm("Are you sure you want to delete this association?", "Tip", {
			confirmButtonText: "Confirm",
			cancelButtonText: "Cancel",
			type: "warning",
		});

		await deleteRoleWorld(id);
		ElMessage.success("Deleted successfully");
		emit("refresh");
		fetchRoleWorldList();
	} catch (error) {
		console.error("Failed to delete association", error);
		if (error !== "cancel") {
			ElMessage.error("Failed to delete association");
		}
	}
};

/**
 * Create character-world knowledge point association
 */
const handleCreateRelation = async () => {
	if (selectedWorldKnowledge.value.length === 0) {
		ElMessage.warning("Please select at least one world knowledge point");
		return;
	}

	try {
		// Create associations for all selected knowledge points
		for (const knowledge of selectedWorldKnowledge.value) {
			try {
				await createRoleWorld({
					world_konwledge_id: knowledge.id,
					role_id: props.roleId,
					world_id: selectedWorld.value,
				});
			} catch (error) {
				console.error(`Failed to create association: ${knowledge.title || knowledge.id}`, error);
				// Continue processing the next one, don't interrupt the flow
			}
		}

		ElMessage.success("Association created successfully");
		dialogVisible.value = false;
		emit("refresh");
		fetchRoleWorldList();
	} catch (error) {
		console.error("Failed to create association", error);
		ElMessage.error("Failed to create association, some associations may already exist");
	}
};

/**
 * Get knowledge point details
 */
const getKnowledgeDetail = (knowledgeId: string) => {
	return knowledgeDetailsMap.value[knowledgeId] || null;
};

/**
 * Watch for changes in world selection
 */
watch(selectedWorld, (newVal) => {
	if (newVal) {
		selectedWorldKnowledge.value = []; // Clear to empty array
		worldKnowledgeDetail.value = "";
		fetchWorldKnowledgeList(newVal);
	} else {
		worldKnowledgeList.value = [];
	}
});

/**
 * Watch for changes in world knowledge point selection
 */
watch(selectedWorldKnowledge, (newVal) => {
	if (newVal && newVal.length > 0) {
		// Show content of first selected item
		worldKnowledgeDetail.value = newVal[0].text || "No content";
		if (newVal.length > 1) {
			worldKnowledgeDetail.value += `\n\n(${newVal.length} knowledge points selected)`;
		}
	} else {
		worldKnowledgeDetail.value = "";
	}
});

/**
 * Watch for page changes
 */
watch(currentPage, () => {
	fetchRoleWorldList();
});

/**
 * Load data when component is mounted
 */
onMounted(() => {
	fetchRoleWorldList();
});

/**
 * Get world name
 */
const getWorldName = (worldId: string) => {
	// First look in the cached world details
	if (worldsDetailsMap.value[worldId]) {
		return worldsDetailsMap.value[worldId].title;
	}

	// If not in cache, look in world list
	const world = worldList.value.find((w) => w.id == worldId);
	return world ? world.title : "Unknown World";
};
</script>

<template>
	<div class="world-knowledge-section">
		<div class="section-toolbar">
			<el-button class="btn-fix" type="primary" size="small" @click="openAddDialog">
				<el-icon>
					<Plus />
				</el-icon>
				Add Association
			</el-button>
		</div>

		<!-- Association list card view -->
		<div class="knowledge-list" v-loading="roleWorldLoading">
			<el-empty v-if="roleWorldList.length === 0" description="No associated world knowledge yet" />
			<div class="knowledge-grid" v-else>
				<el-card v-for="relation in roleWorldList" :key="relation.id" class="knowledge-card" shadow="hover">
					<div class="knowledge-header">
						<div class="knowledge-title" v-if="getKnowledgeDetail(relation.world_konwledge_id)">
							{{ getKnowledgeDetail(relation.world_konwledge_id).title || "No Title" }}
							<div class="knowledge-level">(V{{ getKnowledgeDetail(relation.world_konwledge_id).grade }})</div>
						</div>
						<div class="knowledge-title" v-else>No Data</div>
						<el-tag type="success">
							{{ getWorldName(relation.world_id) }}
						</el-tag>
					</div>

					<div class="knowledge-preview" v-if="getKnowledgeDetail(relation.world_konwledge_id)">
						{{ getKnowledgeDetail(relation.world_konwledge_id).text || "No Content" }}
					</div>
					<div class="knowledge-preview" v-else>No Content</div>
					<template #footer>
						<div class="knowledge-meta">
							<div class="knowledge-source">Created: {{ formatDate(relation.create_time) }}</div>
							<div class="knowledge-actions">
								<el-button type="danger" link @click="handleDelete(relation.id)">
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

			<!-- Pagination -->
			<div class="pagination-container">
				<el-pagination
					v-model:current-page="currentPage"
					:page-size="pageSize"
					layout="total, prev, pager, next"
					:total="total"
					background
				/>
			</div>
		</div>

		<!-- Add association dialog -->
		<el-dialog v-model="dialogVisible" title="Add Character-World Knowledge Association" width="80%" :close-on-click-modal="false">
			<div v-loading="dialogLoading">
				<el-row :gutter="20">
					<!-- World selection -->
					<el-col :span="8">
						<el-card class="selection-card">
							<template #header>
								<div class="card-header">
									<h4>Select World</h4>
								</div>
							</template>

							<el-select
								v-model="selectedWorld"
								filterable
								placeholder="Please select a world"
								style="width: 100%"
								:loading="worldLoading"
							>
								<el-option v-for="item in worldList" :key="item.id" :label="item.title" :value="item.id" />
							</el-select>
						</el-card>
					</el-col>

					<!-- World knowledge point list -->
					<el-col :span="8">
						<el-card class="selection-card">
							<template #header>
								<div class="card-header">
									<h4>Select World Knowledge Points</h4>
								</div>
							</template>

							<div class="knowledge-list" v-loading="worldKnowledgeLoading">
								<el-checkbox-group v-model="selectedWorldKnowledge">
									<div v-for="item in worldKnowledgeList" :key="item.id" class="knowledge-item">
										<el-checkbox :label="item">{{
											item.title || item.content?.substring(0, 20) || "No Title"
										}}</el-checkbox>
									</div>
								</el-checkbox-group>

								<div v-if="!selectedWorld" class="empty-tip">Please select a world first</div>
								<div v-else-if="worldKnowledgeList.length === 0 && !worldKnowledgeLoading" class="empty-tip">
									No world knowledge points yet
								</div>
							</div>
						</el-card>
					</el-col>

					<!-- Preview area -->
					<el-col :span="8">
						<el-card class="selection-card">
							<template #header>
								<div class="card-header">
									<h4>Content Preview</h4>
								</div>
							</template>

							<div class="preview-container">
								<h5>World Knowledge Point Content:</h5>
								<div class="content-preview">{{ worldKnowledgeDetail || "Please select a world knowledge point" }}</div>
							</div>
						</el-card>
					</el-col>
				</el-row>
			</div>

			<template #footer>
				<span class="dialog-footer">
					<el-button @click="dialogVisible = false">Cancel</el-button>
					<el-button type="primary" @click="handleCreateRelation">Create Association</el-button>
				</span>
			</template>
		</el-dialog>
	</div>
</template>

<style scoped lang="scss">
.world-knowledge-section {
	padding: 0;
}

.section-toolbar {
	display: flex;
	justify-content: flex-end;
	align-items: center;
	margin-bottom: 20px;
	padding: 0 4px;
}

/* Knowledge card styles */
.knowledge-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
	gap: 20px;
	margin-bottom: 20px;
}

.knowledge-card {
	margin-bottom: 16px;
	position: relative;
	/* Reserve space for bottom buttons */
}

.knowledge-header {
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
	margin-bottom: 15px;
}

.knowledge-level {
	font-size: 12px;
	color: #e4bb5c;
	display: inline;
	margin-top: 5px;
}

.knowledge-title {
	font-size: 16px;
	margin: 0 0 15px 0;
	color: var(--el-text-color-primary);
}

.knowledge-preview {
	background: #f5f6fa;
	border-radius: 8px;
	padding: 15px;
	margin-bottom: 15px;
	font-size: 14px;
	line-height: 1.5;
	color: #7f8c8d;
	height: 30px;
	overflow: hidden;
	position: relative;
}

.knowledge-preview::after {
	content: "";
	position: absolute;
	bottom: 0;
	left: 0;
	right: 0;
	height: 40px;
	background: linear-gradient(transparent, #f5f6fa);
}

.knowledge-meta {
	display: flex;
	flex-wrap: wrap;
	font-size: 14px;
	color: #7f8c8d;
	justify-content: space-between;
}

.knowledge-source {
	display: flex;
	align-items: center;
	gap: 5px;
	font-size: 14px;
	color: #7f8c8d;
}

.knowledge-actions {
	display: flex;
	gap: 10px;
}

.pagination-container {
	margin-top: 20px;
	display: flex;
	justify-content: center;
}

.selection-card {
	height: 100%;
	display: flex;
	flex-direction: column;
}

.card-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.card-header h3,
.card-header h4 {
	margin: 0;
}

.knowledge-list {
	overflow-y: auto;
	max-height: 300px;
}

.knowledge-item {
	margin-bottom: 8px;
	padding: 8px;
	border-bottom: 1px solid #f0f0f0;
}

.empty-tip {
	text-align: center;
	color: #909399;
	padding: 20px 0;
}

.preview-container {
	overflow-y: auto;
	max-height: 300px;
}

.content-preview {
	background-color: #f8f8f8;
	padding: 10px;
	border-radius: 4px;
	white-space: pre-wrap;
	font-size: 14px;
	max-height: 120px;
	overflow-y: auto;
}

h5 {
	margin: 10px 0;
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
