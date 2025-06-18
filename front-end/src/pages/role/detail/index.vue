<script setup lang="ts">
	import { ref, onMounted, watch } from "vue";
	import { useRoute, useRouter } from "vue-router";
	import { ArrowLeft } from "@element-plus/icons-vue";
	import type { Role, RolePrompt, RoleKnowledge } from "@/types/role";
	import { getRoleDetail, getRolePrompts, getRoleKnowledgeByRoleId, getRoleKnowledgeByShareRoleId } from "@/api/role";
	import { getRelationshipLevelByRoleId } from "@/api/relationship_level";
	// Import split components, add prefix to avoid naming conflicts
	import RoleInfoDetail from "./components/RoleInfo.vue";
	import RolePromptsDetail from "./components/RolePrompts.vue";
	import RoleRelationshipsDetail from "./components/RoleRelationships.vue";
	import RoleKnowledgeDetail from "./components/RoleKnowledge.vue";
	import RoleWorldKnowledge from "./components/RoleWorldKnowledge.vue";
	import RoleTaskChat from "./components/RoleTaskChat.vue";

	/**
	 * Role Details Page
	 * Responsible for retrieving role-related data and passing it to child components
	 */

	const route = useRoute();
	const router = useRouter();
	const roleId = ref(route.params.id as string);
	const loading = ref(false);
	const role = ref<Role>(null);

	// Tabs related
	const activeTab = ref(localStorage.getItem("roleDetailActiveTab") || "prompts");

	// Prompts related
	const promptsLoading = ref(false);
	const prompts = ref<RolePrompt[]>([]);

	// Knowledge fragments related
	const knowledgeLoading = ref(false);
	const knowledgeList = ref<RoleKnowledge[]>([]);
	const knowledgeJoinList = ref<RoleKnowledge[]>([]);

	// Relationship level related
	const relationshipLevelsLoading = ref(false);
	const relationshipLevels = ref([]);

	// Role-world association related
	const roleWorldLoading = ref(false);

	// Task chat related
	const roleTaskChatLoading = ref(false);



	watch(() => route.query, (newVal, oldVal) => {
		roleId.value = `${newVal.role_id}`
		fetchRoleDetail();
		fetchPrompts();
		fetchKnowledge();
		fetchRelationshipLevels();
		fetchShareKnowledge();
	}, { deep: true });
	/**
	 * Get role details
	 */
	const fetchRoleDetail = async () => {
		loading.value = true;
		try {
			// Since there is no actual API, use mock data directly
			const response = await getRoleDetail(roleId.value);
			role.value = response;
			// Default values already set
			console.log("Using mock role details data");
		} catch (error) {
			console.error("Failed to get role details", error);
			// Use default values
		} finally {
			loading.value = false;
		}
	};

	/**
	 * Get prompt list
	 */
	const fetchPrompts = async () => {
		promptsLoading.value = true;
		try {
			// Try to call API to get data
			const response = await getRolePrompts({ skip: 0, limit: 100, role_ids: [roleId.value] });
			if (response) {
				prompts.value = response;
			} else {
				// Use default values
				console.log("Using mock prompt data");
			}
		} catch (error) {
			console.error("Failed to get prompts", error);
			// Use default values
		} finally {
			promptsLoading.value = false;
		}
	};

	/**
	 * Get knowledge fragment list
	 */
	const fetchKnowledge = async () => {
		knowledgeLoading.value = true;
		try {
			// Try to call API to get data
			const response = await getRoleKnowledgeByRoleId(roleId.value, { skip: 0, limit: 100 });
			if (response) {
				knowledgeList.value = response;
			} else {
				// Use default values
				console.log("Using mock knowledge base data");
			}
		} catch (error) {
			console.error("Failed to get knowledge fragments", error);
			// Use default values
		} finally {
			knowledgeLoading.value = false;
		}
	};

	const fetchShareKnowledge = async () => {
		knowledgeLoading.value = true;
		try {
			// Try to call API to get data
			const response = await getRoleKnowledgeByShareRoleId(roleId.value, { skip: 0, limit: 100 });
			if (response) {
				knowledgeJoinList.value = response;
			} else {
				// Use default values
				console.log("Using mock knowledge base data");
			}
		} catch (error) {
			console.error("Failed to get knowledge fragments", error);
			// Use default values
		} finally {
			knowledgeLoading.value = false;
		}
	};

	const reloadData = () => {
		fetchShareKnowledge();
		fetchKnowledge();
	};

	/**
	 * Get relationship levels list
	 */
	const fetchRelationshipLevels = async () => {
		relationshipLevelsLoading.value = true;
		try {
			const response = await getRelationshipLevelByRoleId(roleId.value);
			if (response) {
				relationshipLevels.value = response;
			} else {
				console.log("Using mock relationship level data");
			}
		} catch (error) {
			console.error("Failed to get relationship levels", error);
			// Use default values
		} finally {
			relationshipLevelsLoading.value = false;
		}
	};

	/**
	 * Return to role list page
	 */
	const goBack = () => {
		router.push("/role/list");
	};

	/**
	 * Watch tab changes, cache to localStorage
	 */
	watch(activeTab, (newTab) => {
		localStorage.setItem("roleDetailActiveTab", newTab);
	});

	/**
	 * Handle tab switching
	 */
	const handleTabChange = (tabName : string) => {
		activeTab.value = tabName;
	};

	/**
	 * Load data when component is mounted
	 */
	onMounted(() => {
		fetchRoleDetail();
		fetchPrompts();
		fetchKnowledge();
		fetchRelationshipLevels();
		fetchShareKnowledge();
	});
</script>

<template>
	<div class="role-detail-container">
		<div class="header">
			<!--  style="visibility: hidden;" -->
			<el-button type="text" @click="goBack" class="back-button" style="visibility: hidden;">
				<el-icon>
					<ArrowLeft />
				</el-icon>
				Back to List
			</el-button>
			<h1 class="title">Role Profile</h1>
		</div>

		<!-- Role information component -->
		<RoleInfoDetail :role="role" :loading="loading" />

		<!-- Tabs container -->
		<el-card class="tabs-container">
			<el-tabs v-model="activeTab" @tab-change="handleTabChange" type="border-card">
				<!-- Prompt Management -->
				<el-tab-pane label="Prompt Management" name="prompts">
					<RolePromptsDetail :prompts="prompts" :loading="promptsLoading" :roleId="roleId"
						:relationshipLevels="relationshipLevels" @refresh="fetchPrompts" />
				</el-tab-pane>

				<!-- Relationship Level Management -->
				<el-tab-pane label="Relationship Levels" name="relationships">
					<RoleRelationshipsDetail :relationshipLevels="relationshipLevels"
						:loading="relationshipLevelsLoading" :roleId="roleId" @refresh="fetchRelationshipLevels" />
				</el-tab-pane>

				<!-- Knowledge Base Management -->
				<el-tab-pane label="Knowledge Base" name="knowledge">
					<RoleKnowledgeDetail :knowledgeList="knowledgeList" :knowledgeJoinList="knowledgeJoinList"
						:loading="knowledgeLoading" :roleId="roleId" @refresh="reloadData" />
				</el-tab-pane>

				<!-- World Association Knowledge -->
				<el-tab-pane label="World Association" name="worldKnowledge">
					<RoleWorldKnowledge :roleId="roleId" :loading="roleWorldLoading" @refresh="reloadData" />
				</el-tab-pane>

				<!-- Task Chat -->
				<el-tab-pane label="Task Chat" name="taskChat">
					<RoleTaskChat :roleId="roleId" :loading="roleTaskChatLoading" @refresh="reloadData" />
				</el-tab-pane>
			</el-tabs>
		</el-card>
	</div>
</template>

<style lang="scss" scoped>
	@import '@/layouts/WriterLayout/css/index.scss';

	.role-detail-container {
		background: $custom-bg-color-0;
		min-height: 100vh;
		padding: 0;

		.title {
			color: #333;
		}
	}

	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding-right: 20px;
	}

	.page-header {
		background: rgba(5, 36, 73, 0.91);
		border-bottom: 3px solid #2563eb;
		padding: 20px;
		margin-bottom: 20px;
	}

	.header-content {
		max-width: 1400px;
		margin: 0 auto;
	}

	.title-area {
		display: flex;
		align-items: center;
		gap: 15px;
	}

	.back-button {
		display: flex;
		align-items: center;
		gap: 5px;
		color: #94a3b8;
		font-size: 14px;
		padding: 6px 12px;
		border-radius: 6px;
		transition: all 0.3s ease;
	}

	.back-button:hover {
		background: rgba(255, 255, 255, 0.1);
		color: #ffffff;
	}

	.page-title {
		font-size: 24px;
		margin: 0;
		color: #ffffff;
		font-weight: bold;
		text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
	}

	.tabs-container {
		margin: 20px;
		background: #ffffff;
		border: 1px solid #e2e8f0;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
		min-height: 800px;
	}

	/* Custom tabs style */
	.tabs-container :deep(.el-tabs--border-card) {
		border: none;
		box-shadow: none;
	}

	.tabs-container :deep(.el-tabs__header) {
		background: #f8fafc;
		border-bottom: 2px solid #e2e8f0;
		margin: 0;
	}

	.tabs-container :deep(.el-tabs__nav-wrap) {
		padding: 0 20px;
	}

	.tabs-container :deep(.el-tabs__item) {
		color: #64748b;
		border: none;
		padding: 0 20px;
		height: 50px;
		line-height: 50px;
		font-weight: 500;
		transition: all 0.3s ease;
	}

	.tabs-container :deep(.el-tabs__item:hover) {
		color: #2563eb;
	}

	.tabs-container :deep(.el-tabs__item.is-active) {
		color: #2563eb;
		background: #ffffff;
		border-bottom: 3px solid #2563eb;
	}

	.tabs-container :deep(.el-tabs__content) {
		padding: 0;
	}

	.tabs-container :deep(.el-tab-pane) {
		padding: 20px;
	}

	/* Ensure child component card styles are not affected */
	.tabs-container :deep(.el-card) {
		background: #ffffff;
		border: 1px solid #e2e8f0;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	}
</style>