<template>
	<div class="prompt-list">
		<div class="header">
			<h1 class="title">Prompt Configuration Management</h1>
			<el-button type="primary" @click="handleAdd">
				<el-icon><Plus /></el-icon>
				Add Configuration
			</el-button>
		</div>

		<el-tabs v-model="activeTab" @tab-change="handleTabChange">
			<el-tab-pane v-for="(value, key) in promptType" :key="key" :label="value" :name="key">
				<div class="prompt-grid">
					<el-card v-for="item in filteredPromptList" :key="item.id" class="prompt-card" shadow="hover">
						<div class="prompt-header">
							<h3 class="prompt-title">{{ item.title }}</h3>
							<div>
								<el-tag :type="item.status === 1 ? 'success' : 'danger'">
									{{ item.status === 1 ? "Enabled" : "Disabled" }}
								</el-tag>
								<el-tag>
									{{ promptType[item.type] || item.type }}
								</el-tag>
							</div>
						</div>
						<div class="prompt-meta">
							<div class="meta-item">
							<el-icon><Star /></el-icon>
							<span>Level: {{ item.level }}</span>
						</div>
						<div class="meta-item">
							<el-icon><Timer /></el-icon>
							<span>Updated: {{ new Date(item.updated_at).toLocaleString() }}</span>
						</div>
						</div>
						<div class="prompt-preview">
							{{ item.prompt_text }}
						</div>
						<div class="prompt-actions">
							<el-button type="primary" link @click="handleEdit(item)">
								<el-icon><Edit /></el-icon>
								Edit
							</el-button>
							<el-button type="danger" link @click="handleDelete(item)">
								<el-icon><Delete /></el-icon>
								Delete
							</el-button>
						</div>
					</el-card>
				</div>
			</el-tab-pane>
		</el-tabs>

		<div class="pagination" v-if="showPagination">
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
	</div>
</template>

<script lang="ts" setup>
import { ref, onMounted, computed } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Plus, Edit, Delete, Star, Timer } from "@element-plus/icons-vue";
import { deletePrompt, getPromptListByType } from "@/api/prompt";
import { getConfig_value } from "@/api/system";
import { useRouter } from "vue-router";
import type { Page } from "@/types/api";

interface Prompt {
	id: number;
	role_id: string;
	level: number;
	prompt_text: string;
	status: number;
	created_at: string;
	updated_at: string;
	title: string;
	type: string;
}

// Data list
const promptList = ref<Prompt[]>([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(10);
const activeTab = ref(localStorage.getItem("promptActiveTab") || "system"); // Read cached tab from localStorage, default to system
const promptType = ref<any>({});

// Since the backend has already filtered and paginated by type, the frontend directly uses the original list
const filteredPromptList = computed(() => {
	return promptList.value;
});

// Computed property: whether to show pagination component (only show when data exceeds 10 items)
const showPagination = computed(() => total.value > 10);

const router = useRouter();

// Get configuration
const getConfig = () => {
	getConfig_value("FUNCTION_PROMPT_TEMPLATE").then((res) => {
		promptType.value = JSON.parse(res.config_value);
		console.log(promptType.value);
		// Initialize data retrieval, prioritize cached tab
		if (Object.keys(promptType.value).length > 0) {
			// Check if cached tab is in available tab list
			if (activeTab.value && Object.keys(promptType.value).includes(activeTab.value)) {
				// Use cached tab
				getListByType(activeTab.value);
			} else {
				// If cached tab is not available, use first tab
				activeTab.value = Object.keys(promptType.value)[0];
				getListByType(activeTab.value);
			}
		}
	});
};

// Get list data by type
const getListByType = async (type: string): Promise<void> => {
	try {
		const params = {
			types: [type],
			page: currentPage.value,
			size: pageSize.value,
		};
		const res: Page<Prompt> = await getPromptListByType(params);
		if (res && res.items) {
			promptList.value = res.items;
			total.value = res.total;
		} else {
			promptList.value = [];
			total.value = 0;
		}
	} catch (error) {
		console.error(`Failed to get ${promptType.value[type]} prompt configuration list:`, error);
		promptList.value = [];
		total.value = 0;
	}
};

// Tab change
const handleTabChange = (tab: string): void => {
	activeTab.value = tab;
	// Save currently selected tab to localStorage
	localStorage.setItem("promptActiveTab", tab);
	currentPage.value = 1;
	getListByType(tab);
};

// Pagination handling functions
const handleSizeChange = (val: number): void => {
	pageSize.value = val;
	currentPage.value = 1;
	getListByType(activeTab.value);
};

const handleCurrentChange = (val: number): void => {
	currentPage.value = val;
	getListByType(activeTab.value);
};

// Add
const handleAdd = (): void => {
	router.push(`/prompt/edit?type=${activeTab.value}`);
};

// Edit
const handleEdit = (row: Prompt): void => {
	router.push(`/prompt/edit/${row.id}`);
};

// Delete
const handleDelete = (row: Prompt): void => {
	ElMessageBox.confirm("Are you sure to delete this prompt configuration?", "Confirm", {
		type: "warning",
	}).then(async () => {
		try {
			await deletePrompt(row.id);
			ElMessage.success("Delete successful");
			getListByType(activeTab.value);
		} catch (error) {
			console.error("Failed to delete prompt configuration:", error);
		}
	});
};

onMounted(() => {
	getConfig();
});
</script>

<style lang="scss" scoped>
.prompt-list {
	background: #f3f3f3;
	min-height: 100vh;
	padding: 0;

	.header {
		background: rgba(5, 36, 73, 0.91);
		border-bottom: 3px solid #2563eb;
		padding: 20px;
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0;

		.title {
			font-size: 24px;
			color: #ffffff;
			font-weight: bold;
			text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
			margin: 0;
		}
	}

	.prompt-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
		gap: 16px;
	}

	.prompt-card {
		background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
		border: 1px solid #e2e8f0;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
		transition: all 0.3s ease;
		position: relative;

		&:hover {
			transform: translateY(-2px);
			box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
			border-color: #2563eb;
		}

		.prompt-header {
			display: flex;
			justify-content: space-between;
			align-items: flex-start;
			margin-bottom: 12px;

			.prompt-title {
				font-size: 16px;
				color: #1e293b;
				font-weight: 600;
				margin: 0;
			}
		}

		.prompt-meta {
			display: flex;
			gap: 12px;
			margin-bottom: 12px;
			font-size: 13px;
			color: #64748b;

			.meta-item {
				display: flex;
				align-items: center;
				gap: 4px;
			}
		}

		.prompt-preview {
			background: #f1f5f9;
			border: 1px solid #e2e8f0;
			border-radius: 6px;
			padding: 12px;
			margin-bottom: 12px;
			font-size: 13px;
			line-height: 1.4;
			color: #475569;
			height: 120px;
			overflow: hidden;
			position: relative;

			&::after {
				content: "";
				position: absolute;
				bottom: 0;
				left: 0;
				right: 0;
				height: 40px;
				background: linear-gradient(transparent, #f1f5f9);
			}
		}

		.prompt-actions {
			display: flex;
			justify-content: flex-end;
			gap: 8px;
		}
	}

	.pagination {
		display: flex;
		justify-content: center;
		margin-top: 20px;
		padding: 20px 0;

		:deep(.el-pagination) {
			background: #ffffff;
			padding: 15px 20px;
			border-radius: 8px;
			border: 1px solid #e2e8f0;
			box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
		}

		:deep(.el-pager li) {
			background: transparent;
			color: #64748b;
			border: 1px solid #e2e8f0;
			margin: 0 2px;
			border-radius: 4px;
		}

		:deep(.el-pager li:hover),
		:deep(.el-pager li.is-active) {
			background: #2563eb;
			color: #ffffff;
			border-color: #2563eb;
		}

		@media (max-width: 768px) {
			padding: 15px 0;

			:deep(.el-pagination) {
				.el-pagination__sizes {
					display: none;
				}
			}
		}
	}
}
</style>
