<!-- KnowledgeList.vue - Knowledge fragment list component -->
<script setup lang="ts">
import { InfoFilled, Edit, Delete, Plus } from "@element-plus/icons-vue";
import { ElMessageBox } from "element-plus";
import type { WorldKnowledge } from "@/types/world";
import { computed } from "vue";
import "@/assets/css/knowledge.scss";

const props = defineProps<{
	knowledgeList: WorldKnowledge[];
	knowledgeLoading: boolean;
	selectedKnowledge: WorldKnowledge | null;
	// Pagination related props
	total: number;
	currentPage: number;
	pageSize: number;
}>();

/**
 * Define component emitted events
 */
const emit = defineEmits<{
	add: [];
	edit: [knowledge: WorldKnowledge];
	delete: [knowledge: WorldKnowledge];
	select: [knowledge: WorldKnowledge];
	// Pagination related events
	"page-change": [page: number];
	"size-change": [size: number];
}>();

// Computed property: whether to display pagination component (only when data exceeds 10 items)
const showPagination = computed(() => props.total > 10);

/**
 * Add new knowledge
 */
const addNewKnowledge = () => {
	emit("add");
};

/**
 * Edit knowledge
 * @param {WorldKnowledge} knowledge - Knowledge item
 */
const editKnowledge = (knowledge: WorldKnowledge) => {
	emit("edit", knowledge);
};

/**
 * Delete knowledge
 * @param {WorldKnowledge} knowledge - Knowledge item
 */
const deleteKnowledge = (knowledge: WorldKnowledge) => {
	ElMessageBox.confirm("Are you sure you want to delete this knowledge fragment?", "Confirmation", {
		confirmButtonText: "Confirm",
		cancelButtonText: "Cancel",
		type: "warning",
	})
		.then(() => {
			emit("delete", knowledge);
		})
		.catch(() => {
			// Cancel operation
		});
};

/**
 * Select knowledge and display related roles
 * @param {WorldKnowledge} knowledge - Knowledge item
 */
const selectKnowledge = (knowledge: WorldKnowledge) => {
	emit("select", knowledge);
};

/**
 * Handle page number change
 */
const handleCurrentChange = (page: number) => {
	emit("page-change", page);
};

/**
 * Handle page size change
 */
const handleSizeChange = (size: number) => {
	emit("size-change", size);
};
</script>

<template>
	<el-card class="section-card">
		<template #header>
			<div class="section-header">
				<h3 class="section-title">Knowledge Fragments</h3>
				<el-button type="primary" size="small" @click="addNewKnowledge">
					<el-icon><Plus /></el-icon>
					Add Knowledge
				</el-button>
			</div>
		</template>
		<div class="knowledge-list" v-loading="knowledgeLoading">
			<el-empty v-if="knowledgeList.length === 0" description="No knowledge fragments yet" />
			<!--			<el-row :gutter="20" v-else>-->
			<!--				<el-col :xs="24" :sm="12" :md="8" v-for="knowledge in knowledgeList" :key="knowledge.id">-->
			<div class="knowledge-grid">
				<el-card
					v-for="knowledge in knowledgeList"
					:key="knowledge.id"
					class="knowledge-card"
					shadow="never"
					:class="{ 'selected-knowledge': selectedKnowledge && selectedKnowledge.id === knowledge.id }"
					@click="selectKnowledge(knowledge)"
				>
					<div class="knowledge-header">
						<h4 class="knowledge-title">
							{{ knowledge.title }}
							<div class="knowledge-content">(v{{ knowledge.grade }})</div>
						</h4>
						<el-tag :type="knowledge.type === 'scene' ? 'success' : 'warning'">
							{{ knowledge.type === "scene" ? "Scene" : "Basic" }}
						</el-tag>
					</div>
					<div class="knowledge-preview">
						{{ knowledge.text }}
					</div>
					<div class="knowledge-meta">
						<span class="meta-item">
							<span
								>Tags:
								<el-tag
									size="small"
									v-for="tag in (knowledge.tags || 'Not added').split(',')"
									:key="tag"
									style="margin-left: 5px"
								>
									{{ tag }}
								</el-tag>
							</span>
						</span>
					</div>
					<template #footer>
						<div class="knowledge-card-footer">
							<div class="knowledge-source" v-if="knowledge.source">
								<el-icon>
									<InfoFilled />
								</el-icon>
								<span>Source: {{ knowledge.source }}</span>
							</div>
							<div class="knowledge-actions">
								<el-button type="primary" link @click.stop="editKnowledge(knowledge)">
									<el-icon>
										<Edit />
									</el-icon>
									Edit
								</el-button>
								<el-button type="danger" link @click.stop="deleteKnowledge(knowledge)">
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

			<!--				</el-col>-->
			<!--			</el-row>-->
		</div>

		<!-- Pagination component (only displayed when data exceeds 10 items) -->
		<div v-if="showPagination" class="pagination-container">
			<el-pagination
				:current-page="props.currentPage"
				:page-size="props.pageSize"
				:total="props.total"
				:page-sizes="[10, 20, 50, 100]"
				layout="total, sizes, prev, pager, next"
				@size-change="handleSizeChange"
				@current-change="handleCurrentChange"
			/>
		</div>
	</el-card>
</template>

<style scoped>
.section-card {
	margin-bottom: 24px;
	background: #ffffff;
	border: 1px solid #e2e8f0;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.section-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.section-title {
	margin: 0;
	font-size: 18px;
	color: #1e293b;
	font-weight: 600;
}

.knowledge-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
	gap: 16px;
	margin-bottom: 20px;
}

.knowledge-card {
	cursor: pointer;
	transition: all 0.3s ease;
	background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
	border: 1px solid #e2e8f0;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	height: 280px;
	overflow: hidden;
}

.knowledge-card:hover {
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
	border-color: #2563eb;
}

.selected-knowledge {
	border: 2px solid #2563eb;
	background: linear-gradient(135deg, #dbeafe 0%, #eff6ff 100%);
	box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2);
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
	color: #1e293b;
	font-weight: 600;
	display: flex;
	line-height: 1.4;
}

.knowledge-preview {
	color: #64748b;
	font-size: 14px;
	line-height: 1.5;
	margin-bottom: 12px;
	display: -webkit-box;
	-webkit-line-clamp: 4;
	-webkit-box-orient: vertical;
	overflow: hidden;
	text-overflow: ellipsis;
	max-height: 84px;
}

.knowledge-meta {
	display: flex;
	flex-wrap: wrap;
	gap: 12px;
	font-size: 12px;
	color: #64748b;
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
	color: #64748b;
}

.knowledge-actions {
	display: flex;
	align-items: center;
	gap: 5px;
}

.knowledge-content {
	font-size: 14px;
	line-height: 26px;
	margin-left: 3px;
	color: #2563eb;
	font-weight: 500;
}
.meta-item {
	display: flex;
	justify-content: space-around;
	align-items: center;
}

.pagination-container {
	margin-top: 20px;
	display: flex;
	justify-content: center;
}

.pagination-container :deep(.el-pagination) {
	background: #ffffff;
	padding: 15px 20px;
	border-radius: 8px;
	border: 1px solid #e2e8f0;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.pagination-container :deep(.el-pager li) {
	background: transparent;
	color: #64748b;
	border: 1px solid #e2e8f0;
	margin: 0 2px;
	border-radius: 4px;
}

.pagination-container :deep(.el-pager li:hover),
.pagination-container :deep(.el-pager li.is-active) {
	background: #2563eb;
	color: #ffffff;
	border-color: #2563eb;
}
</style>
