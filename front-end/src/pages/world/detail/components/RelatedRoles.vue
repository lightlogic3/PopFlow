<!-- RelatedRoles.vue - 关联角色列表组件 -->
<script setup lang="ts">
import { Collection, InfoFilled, Link } from "@element-plus/icons-vue";
import { useRouter } from "vue-router";
import type { WorldKnowledge } from "@/types/world";
import { ref, watch } from "vue";

const props = defineProps<{
	rolesList: any[];
	rolesLoading: boolean;
	rolesTotal: number;
	rolesCurrentPage: number;
	rolesPageSize: number;
	isShowingKnowledgeRoles: boolean;
	selectedKnowledge: WorldKnowledge | null;
	relateKnowList: any[];
}>();

/**
 * Define events triggered by component
 */
const emit = defineEmits<{
	bindRole: [];
	unbindRole: [relationId: number];
	resetToWorldRoles: [];
	pageChange: [page: number];
	"update:selectedKnowledge": [value: WorldKnowledge | null];
}>();

const router = useRouter();

/**
 * Open bind role dialog
 */
const openBindRoleDialog = () => {
	emit("bindRole");
};

/**
 * Unbind role
 * @param {number} relationId - Relation record ID
 */
const unbindRoleFromKnowledge = (relationId: number) => {
	emit("unbindRole", relationId);
};

/**
 * Reset to show world-related roles
 */
const resetToWorldRoles = () => {
	emit("resetToWorldRoles");
};

/**
 * Handle page change
 * @param {number} page - New page number
 */
const handlePageChange = (page: number) => {
	emit("pageChange", page);
};

const activeName = ref("role");

const selectedKnowledge = ref<WorldKnowledge | null>(props.selectedKnowledge);

watch(selectedKnowledge, (newVal) => {
	emit("update:selectedKnowledge", newVal);
});
</script>

<template>
	<el-card class="section-card">
		<template #header>
			<div class="section-header">
				<div class="section-title-container">
					<h3 class="section-title">
						{{ isShowingKnowledgeRoles ? "Knowledge-Related Roles" : "World-Related Roles" }}
					</h3>
					<el-tag v-if="isShowingKnowledgeRoles" type="info" closable @close="resetToWorldRoles">
						{{ selectedKnowledge?.title || "Current Knowledge" }}
					</el-tag>
				</div>
				<div v-if="isShowingKnowledgeRoles">
					<el-button type="primary" size="small" @click="openBindRoleDialog">
						<el-icon><Link /></el-icon> Bind Role
					</el-button>
				</div>
			</div>
		</template>
		<div class="related-roles" v-loading="rolesLoading">
			<el-empty
				v-if="rolesList.length === 0"
				:description="isShowingKnowledgeRoles ? 'No related roles for current knowledge' : 'No related roles for current world'"
			/>
			<el-tabs v-model="activeName" class="demo-tabs" style="width: 100%">
				<el-tab-pane label="Related Roles" name="role">
					<el-row :gutter="16" v-if="rolesList.length > 0">
						<el-col :xs="12" :sm="8" :md="6" :lg="4" v-for="role in rolesList" :key="role.id">
							<el-card class="role-card" shadow="hover">
								<div class="role-avatar-container">
									<el-avatar
										:size="50"
										:src="
											role.image_url ||
											role.avatar ||
											'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'
										"
									/>
								</div>
								<div class="role-content">
									<h4 class="role-name">{{ role.name }}</h4>
									<p class="role-id">ID: {{ role.role_id }}</p>
									<div class="role-actions">
										<el-button type="primary" size="small" @click="router.push(`/role/detail/${role.role_id}`)">
											View Details
										</el-button>
										<el-button
											v-if="isShowingKnowledgeRoles"
											type="danger"
											size="small"
											@click="unbindRoleFromKnowledge(role.relation_id)"
										>
											Unbind
										</el-button>
									</div>
								</div>
							</el-card>
						</el-col>
					</el-row>
					<el-empty v-else description="No related roles" />
				</el-tab-pane>
				<el-tab-pane label="Related Knowledge" name="second">
					<el-empty v-if="relateKnowList.length === 0" description="No knowledge fragments" />
					<el-row :gutter="20" v-else>
						<el-col :xs="24" :sm="12" :md="8" v-for="knowledge in relateKnowList" :key="knowledge.id">
							<el-card
								class="knowledge-card"
								shadow="hover"
								:class="{ 'selected-knowledge': selectedKnowledge && selectedKnowledge.id === knowledge.id }"
								@click="selectedKnowledge = knowledge"
							>
								<div class="knowledge-header">
									<div class="knowledge-level">Level: {{ knowledge.grade }}</div>
									<el-tag :type="knowledge.type === 'scene' ? 'success' : 'warning'">
										{{ knowledge.type }}
									</el-tag>
								</div>
								<h4 class="knowledge-title">{{ knowledge.title }}</h4>
								<div class="knowledge-preview">
									{{ knowledge.text }}
								</div>
								<div class="knowledge-meta">
									<span v-if="knowledge.tags" class="meta-item">
										<el-icon>
											<Collection />
										</el-icon>
										<span>Tags: {{ knowledge.tags }}</span>
									</span>
								</div>
								<div class="knowledge-card-footer">
									<div class="knowledge-source" v-if="knowledge.source">
										<el-icon>
											<InfoFilled />
										</el-icon>
										<span>Source: {{ knowledge.source }}</span>
									</div>
								</div>
							</el-card>
						</el-col>
					</el-row>
				</el-tab-pane>
			</el-tabs>

			<!-- Pagination -->
			<div class="pagination-container" v-if="rolesTotal > rolesPageSize">
				<el-pagination
					:current-page="rolesCurrentPage"
					:page-size="rolesPageSize"
					layout="prev, pager, next, total"
					:total="rolesTotal"
					@current-change="handlePageChange"
					background
				/>
			</div>
		</div>
	</el-card>
</template>

<style scoped>
.section-card {
	margin-bottom: 24px;
	background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
	border: 1px solid #e2e8f0;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
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
	color: #1e293b;
	font-weight: 600;
}

/* Role card styles */
.role-card {
	margin-bottom: 16px;
	display: flex;
	flex-direction: column;
	align-items: center;
	padding: 12px;
	transition: all 0.3s;
	background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
	border: 1px solid #e2e8f0;
	height: 160px;
}

.role-card:hover {
	transform: translateY(-3px);
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
	border-color: #2563eb;
}

.role-avatar-container {
	margin-bottom: 8px;
	display: flex;
	justify-content: center;
}

.role-content {
	text-align: center;
	width: 100%;
}

.role-name {
	font-size: 14px;
	margin: 0 0 4px 0;
	color: #1e293b;
	font-weight: 600;
	line-height: 1.2;
}

.role-id {
	font-size: 11px;
	color: #64748b;
	margin: 0 0 8px 0;
	line-height: 1.2;
}

.role-actions {
	margin-top: 8px;
	display: flex;
	flex-direction: column;
	gap: 4px;
	width: 100%;
}

.role-actions .el-button {
	font-size: 12px;
	padding: 4px 8px;
}

.pagination-container {
	margin-top: 20px;
	display: flex;
	justify-content: center;
}
</style>
