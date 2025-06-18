<template>
	<el-dialog v-model="dialogVisible" title="Knowledge Base Search" width="80%" draggable>
		<div class="search-container">
			<!-- Search form -->
			<el-form :model="searchForm" label-width="100px" class="search-form">
				<el-form-item label="Search Content">
					<el-input
						v-model="searchForm.query"
						type="textarea"
						:rows="3"
						placeholder="Please enter content to search..."
						clearable
					/>
				</el-form-item>
				<el-row :gutter="16">
					<el-col :span="12">
						<el-form-item label="Results Count">
							<el-input-number v-model="searchForm.top_k" :min="1" :max="50" :step="1" placeholder="Number of results" />
						</el-form-item>
					</el-col>
					<el-col :span="12">
						<el-form-item label="Similarity Threshold">
							<el-input-number
								v-model="searchForm.threshold"
								:min="0"
								:max="2"
								:step="0.01"
								:precision="2"
								placeholder="Score threshold (lower means more similar)"
							/>
							<div class="threshold-hint">Results with scores higher than this will be filtered out</div>
						</el-form-item>
					</el-col>
				</el-row>
				<el-form-item>
					<el-button type="primary" @click="handleSearch" :loading="loading" :disabled="!searchForm.query.trim()">
						<el-icon>
							<Search />
						</el-icon>
						Search
					</el-button>
					<el-button @click="clearResults">Clear Results</el-button>
				</el-form-item>
			</el-form>

			<!-- Search results -->
			<div class="search-results" v-if="filteredResults.length > 0">
				<el-divider content-position="left">
					<span class="results-title">
						Search Results ({{ filteredResults.length }} items)
						<span v-if="searchResults.length > filteredResults.length" class="filtered-info">
							/ Total {{ searchResults.length }} items, {{ searchResults.length - filteredResults.length }} filtered out
						</span>
					</span>
				</el-divider>

				<el-tabs v-model="activeTab" class="results-tabs">
					<el-tab-pane label="Character Knowledge" name="role">
						<div class="results-list">
							<el-empty v-if="filteredRoleResults.length === 0" description="No character knowledge results" />
							<el-card
								v-for="(result, index) in filteredRoleResults"
								:key="`role-${index}`"
								class="result-card"
								shadow="hover"
							>
								<div class="result-header">
									<div class="result-info">
										<el-tag type="success" size="small">Character Knowledge</el-tag>
										<el-tag :type="getScoreType(result.score)" size="small" class="score-tag">
											Similarity Score: {{ result.score.toFixed(4) }}
										</el-tag>
									</div>
									<div class="result-meta">
										<span class="result-grade">Level: {{ result.grade || "N/A" }}</span>
									</div>
								</div>
								<div class="result-title">{{ result.title || "No Title" }}</div>
								<div class="result-content">{{ result.text }}</div>
								<div class="result-footer">
									<span class="result-source">Source: {{ result.source || "Unknown" }}</span>
									<span class="result-role">Character ID: {{ result.role_id }}</span>
								</div>
							</el-card>
						</div>
					</el-tab-pane>
					<el-tab-pane label="World Settings" name="world">
						<div class="results-list">
							<el-empty v-if="filteredWorldResults.length === 0" description="No world settings results" />
							<el-card
								v-for="(result, index) in filteredWorldResults"
								:key="`world-${index}`"
								class="result-card"
								shadow="hover"
							>
								<div class="result-header">
									<div class="result-info">
										<el-tag type="warning" size="small">World Settings</el-tag>
										<el-tag :type="getScoreType(result.score)" size="small" class="score-tag">
											Similarity Score: {{ result.score.toFixed(4) }}
										</el-tag>
									</div>
									<div class="result-meta">
										<span class="result-grade">Level: {{ result.grade || "N/A" }}</span>
									</div>
								</div>
								<div class="result-title">{{ result.title || "No Title" }}</div>
								<div class="result-content">{{ result.text }}</div>
								<div class="result-footer">
									<span class="result-source">Source: {{ result.source || "Unknown" }}</span>
									<span class="result-world">World ID: {{ result.world_id }}</span>
								</div>
							</el-card>
						</div>
					</el-tab-pane>
				</el-tabs>
			</div>

			<!-- No results display -->
			<div v-else-if="searchResults.length > 0" class="no-results">
				<el-empty description="All results were filtered by threshold, please adjust threshold settings" />
			</div>
		</div>

		<template #footer>
			<span class="dialog-footer">
				<el-button @click="handleClose">Close</el-button>
			</span>
		</template>
	</el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, defineProps, defineEmits } from "vue";
import { ElMessage } from "element-plus";
import { Search } from "@element-plus/icons-vue";
import { queryRoleKnowledge, queryWorldKnowledge } from "@/api/knowledge";

const props = defineProps<{
	visible: boolean;
	roleId: string;
}>();

const emit = defineEmits<{
	(e: "update:visible", visible: boolean): void;
}>();

// Dialog visibility status
const dialogVisible = computed({
	get: () => props.visible,
	set: (value) => emit("update:visible", value),
});

// Search form
const searchForm = ref({
	query: "",
	top_k: 10,
	threshold: 1.0, // Default threshold set to 1.0
});

// Loading status
const loading = ref(false);

// Search results
const searchResults = ref<any[]>([]);
const activeTab = ref("role");

// Results filtered based on threshold
const filteredResults = computed(() => {
	return searchResults.value.filter((item) => item.score <= searchForm.value.threshold);
});

// Categorized filtered results
const filteredRoleResults = computed(() => filteredResults.value.filter((item) => item.source_type === "role"));

const filteredWorldResults = computed(() => filteredResults.value.filter((item) => item.source_type === "world"));

/**
 * Get tag type corresponding to similarity score
 * Note: Lower score indicates higher similarity
 */
const getScoreType = (score: number) => {
	if (score <= 0.3) return "success"; // Very similar
	if (score <= 0.6) return "warning"; // Moderately similar
	return "danger"; // Not very similar
};

/**
 * Execute search
 */
const handleSearch = async () => {
	if (!searchForm.value.query.trim()) {
		ElMessage.warning("Please enter search content");
		return;
	}

	loading.value = true;
	try {
		// Build request parameters
		const searchParams = {
			query: searchForm.value.query,
			top_k: searchForm.value.top_k,
			role_id: props.roleId,
		};

		// Request two APIs simultaneously
		const [roleResponse, worldResponse] = await Promise.all([
			queryRoleKnowledge(searchParams),
			queryWorldKnowledge(searchParams),
		]);
		// Merge results and add source identifiers
		const roleData = roleResponse || [];
		const worldData = worldResponse || [];

		const combinedResults = [
			...roleData.map((item: any) => ({ ...item, source_type: "role" })),
			...worldData.map((item: any) => ({ ...item, source_type: "world" })),
		];

		// Sort by similarity (lower score means more similar, so sort in ascending order)
		combinedResults.sort((a, b) => (a.score || 999) - (b.score || 999));

		searchResults.value = combinedResults;

		if (combinedResults.length === 0) {
			ElMessage.info("No relevant results found");
		} else {
			const filteredCount = filteredResults.value.length;
			if (filteredCount === 0) {
				ElMessage.warning(`Found ${combinedResults.length} results, but all were filtered by threshold, please adjust threshold settings`);
			} else if (filteredCount < combinedResults.length) {
				ElMessage.success(
					`Found ${combinedResults.length} results, displaying ${filteredCount} (${
						combinedResults.length - filteredCount
					} filtered by threshold)`,
				);
			} else {
				ElMessage.success(`Found ${combinedResults.length} relevant results`);
			}
		}
	} catch (error) {
		console.error("Search failed:", error);
		ElMessage.error("Search failed, please try again later");
	} finally {
		loading.value = false;
	}
};

/**
 * Clear search results
 */
const clearResults = () => {
	searchResults.value = [];
	searchForm.value.query = "";
};

/**
 * Close dialog
 */
const handleClose = () => {
	dialogVisible.value = false;
};
</script>

<style scoped>
.search-container {
	padding: 10px 0;
}

.search-form {
	margin-bottom: 20px;
}

.threshold-hint {
	font-size: 12px;
	color: var(--el-text-color-secondary);
	margin-top: 4px;
}

.search-results {
	margin-top: 20px;
}

.results-title {
	font-weight: bold;
	color: var(--el-text-color-primary);
}

.filtered-info {
	font-size: 12px;
	color: var(--el-text-color-secondary);
	font-weight: normal;
}

.results-tabs {
	margin-top: 16px;
}

.results-list {
	max-height: 500px;
	overflow-y: auto;
}

.result-card {
	margin-bottom: 16px;
}

.result-header {
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
	margin-bottom: 12px;
}

.result-info {
	display: flex;
	gap: 8px;
	align-items: center;
}

.score-tag {
	font-weight: bold;
}

.result-meta {
	display: flex;
	gap: 12px;
	font-size: 14px;
	color: var(--el-text-color-secondary);
}

.result-grade {
	font-weight: 500;
}

.result-title {
	font-size: 16px;
	font-weight: bold;
	color: var(--el-text-color-primary);
	margin-bottom: 8px;
	line-height: 1.4;
}

.result-content {
	font-size: 14px;
	line-height: 1.6;
	color: var(--el-text-color-regular);
	margin-bottom: 12px;
	white-space: pre-wrap;
	word-break: break-word;
}

.result-footer {
	display: flex;
	justify-content: space-between;
	font-size: 12px;
	color: var(--el-text-color-secondary);
	border-top: 1px solid var(--el-border-color-lighter);
	padding-top: 8px;
}

.result-source,
.result-role,
.result-world {
	display: flex;
	align-items: center;
}

.no-results {
	margin-top: 20px;
	text-align: center;
}

.dialog-footer {
	display: flex;
	justify-content: flex-end;
}

/* Scrollbar styles */
.results-list::-webkit-scrollbar {
	width: 6px;
}

.results-list::-webkit-scrollbar-track {
	background: var(--el-fill-color-lighter);
	border-radius: 3px;
}

.results-list::-webkit-scrollbar-thumb {
	background: var(--el-fill-color-dark);
	border-radius: 3px;
}

.results-list::-webkit-scrollbar-thumb:hover {
	background: var(--el-fill-color-darker);
}
</style>
