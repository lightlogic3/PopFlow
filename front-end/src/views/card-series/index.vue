<template>
	<div class="card-series-container">
		<!-- 页面头部 -->
		<div class="header fade-in">
			<h1 class="title">Card Series Management</h1>
			<div class="header-actions">
				<el-button type="primary" @click="handleCreate" class="create-btn">
					<el-icon><Plus /></el-icon>
					Add Series
				</el-button>
			</div>
		</div>

		<!-- 搜索栏 -->
		<div class="search-box fade-in-up" style="animation-delay: 200ms">
			<el-row :gutter="20">
				<el-col :span="6">
					<el-input
						v-model="filters.name"
						placeholder="Series Name"
						clearable
						@change="handleSearch"
						class="filter-input"
					/>
				</el-col>
				<el-col :span="6">
					<el-input
						v-model="filters.code"
						placeholder="Series Code"
						clearable
						@change="handleSearch"
						class="filter-input"
					/>
				</el-col>
				<el-col :span="6">
					<el-select v-model="filters.status" placeholder="Status" clearable @change="handleSearch" class="filter-select">
						<el-option label="All" value="" />
						<el-option label="Enabled" :value="1" />
						<el-option label="Disabled" :value="0" />
					</el-select>
				</el-col>
				<el-col :span="6">
					<el-button type="primary" @click="handleSearch">Search</el-button>
					<el-button @click="resetFilters">Reset</el-button>
				</el-col>
			</el-row>
		</div>

		<!-- 卡片网格 - 使用新风格 -->
		<div class="series-gallery-wrapper fade-in-up" style="animation-delay: 400ms">
			<el-row :gutter="16" v-loading="loading" class="series-gallery">
				<el-col :xs="12" :sm="8" :md="6" :lg="4" :xl="3" v-for="series in seriesList" :key="series.id">
					<div
						class="series-card-wrapper"
						:class="{ selected: selectedSeriesId === series.id }"
						@click="selectSeries(series.id)"
					>
						<div class="series-card-inner" @click="handleView(series)">
							<div class="series-status-badge">
								{{ series.status === 1 ? "Enabled" : "Disabled" }}
							</div>
							<div class="series-code-badge">{{ series.code }}</div>

							<div class="series-icon-container">
								<div class="series-icon">
									<el-icon><Tickets /></el-icon>
								</div>
							</div>

							<div class="series-info">
								<div class="series-name">
									{{ series.name }}
								</div>

								<div class="series-description">
									{{ series.description || "No description" }}
								</div>

								<div class="series-stats">
									<div class="stat-item">
										<span>Sort: {{ series.sort_order }}</span>
									</div>
									<div class="stat-item">
										<span>Created: {{ formatDate(series.create_time) }}</span>
									</div>
								</div>
							</div>

							<div class="series-actions">
								<el-button
									type="warning"
									size="small"
									circle
									@click.stop="handleEdit(series)"
									class="action-btn edit-btn"
								>
									<el-icon><Edit /></el-icon>
								</el-button>
								<el-button
									type="danger"
									size="small"
									circle
									@click.stop="handleDelete(series)"
									class="action-btn delete-btn"
								>
									<el-icon><Delete /></el-icon>
								</el-button>
							</div>

							<div class="select-indicator">View Details</div>
						</div>
					</div>
				</el-col>

				<!-- 空数据提示 -->
				<el-col v-if="!loading && seriesList.length === 0" :span="24">
					<div class="empty-state">
						<el-empty description="No card series">
							<el-button type="primary" @click="handleCreate">Create Now</el-button>
						</el-empty>
					</div>
				</el-col>
			</el-row>
		</div>

		<!-- 分页 -->
		<div class="pagination" v-if="total > 0">
			<el-pagination
				v-model:current-page="currentPage"
				v-model:page-size="pageSize"
				:total="total"
				:page-sizes="[12, 24, 48, 96]"
				layout="total, sizes, prev, pager, next"
				@size-change="handleSizeChange"
				@current-change="handleCurrentChange"
			/>
		</div>

		<!-- 创建/编辑对话框 -->
		<el-dialog
			v-model="dialogVisible"
			:title="editingId ? 'Edit Series' : 'Add Series'"
			width="600px"
			:before-close="handleDialogClose"
		>
			<el-form ref="formRef" :model="formData" :rules="formRules" label-width="120px" class="series-form">
				<el-form-item label="Series Name" prop="name">
					<el-input v-model="formData.name" placeholder="Please enter series name" />
				</el-form-item>
				<el-form-item label="Series Code" prop="code">
					<el-input v-model="formData.code" placeholder="Please enter series code" />
				</el-form-item>
				<el-form-item label="Description" prop="description">
					<el-input v-model="formData.description" type="textarea" :rows="3" placeholder="Please enter series description" />
				</el-form-item>
				<el-form-item label="Sort Order" prop="sort_order">
					<el-input-number v-model="formData.sort_order" :min="0" />
				</el-form-item>
				<el-form-item label="Status" prop="status">
					<el-radio-group v-model="formData.status">
						<el-radio :label="1">Enabled</el-radio>
						<el-radio :label="0">Disabled</el-radio>
					</el-radio-group>
				</el-form-item>
			</el-form>
			<template #footer>
				<span class="dialog-footer">
					<el-button @click="dialogVisible = false">Cancel</el-button>
					<el-button type="primary" @click="handleSubmit" :loading="submitLoading">
						{{ editingId ? "Update" : "Create" }}
					</el-button>
				</span>
			</template>
		</el-dialog>
	</div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { Plus, Edit, Delete, Tickets } from "@element-plus/icons-vue";
import {
	getCardSeriesList,
	createCardSeries,
	updateCardSeries,
	deleteCardSeries,
	type CardSeries,
	type CardSeriesCreate,
	type CardSeriesUpdate,
} from "@/api/card-series";
import { formatDate } from "@/utils";

// 响应式数据
const router = useRouter();
const loading = ref(false);
const submitLoading = ref(false);
const seriesList = ref<CardSeries[]>([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(12);
const selectedSeriesId = ref<number | null>(null); // 添加选中状态

// 搜索过滤条件
const filters = reactive({
	name: "",
	code: "",
	status: "",
});

// 对话框相关
const dialogVisible = ref(false);
const editingId = ref<number | null>(null);
const formRef = ref();

// 表单数据
const formData = reactive<CardSeriesCreate & { status: number }>({
	name: "",
	code: "",
	description: "",
	sort_order: 0,
	status: 1,
});

// 表单验证规则
const formRules = {
	name: [{ required: true, message: "Please enter series name", trigger: "blur" }],
	code: [{ required: true, message: "Please enter series code", trigger: "blur" }],
};

// 选择系列
function selectSeries(seriesId: number) {
	selectedSeriesId.value = seriesId;
}

// 数据加载
function loadSeriesList() {
	loading.value = true;
	const params = {
		...filters,
		page: currentPage.value,
		size: pageSize.value,
	};

	getCardSeriesList(params)
		.then((res) => {
			seriesList.value = res.items || [];
			total.value = res.total || 0;
		})
		.catch((err) => {
			ElMessage.error(`Failed to load series list: ${err.message}`);
		})
		.finally(() => {
			loading.value = false;
		});
}

// 搜索处理
function handleSearch() {
	currentPage.value = 1;
	loadSeriesList();
}

function resetFilters() {
	filters.name = "";
	filters.code = "";
	filters.status = "";
	handleSearch();
}

// 分页处理
function handleSizeChange(val: number) {
	pageSize.value = val;
	loadSeriesList();
}

function handleCurrentChange(val: number) {
	currentPage.value = val;
	loadSeriesList();
}

// 操作处理
function handleCreate() {
	editingId.value = null;
	resetForm();
	dialogVisible.value = true;
}

function handleEdit(series: CardSeries) {
	editingId.value = series.id;
	formData.name = series.name;
	formData.code = series.code;
	formData.description = series.description || "";
	formData.sort_order = series.sort_order;
	formData.status = series.status;
	dialogVisible.value = true;
}

function handleView(series: CardSeries) {
	router.push(`/bink/card-series/${series.id}/cards`);
}

function handleDelete(series: CardSeries) {
	ElMessageBox.confirm(`Are you sure to delete series "${series.name}"? This operation cannot be undone.`, "Warning", {
		confirmButtonText: "Confirm",
		cancelButtonText: "Cancel",
		type: "warning",
	})
		.then(() => {
			deleteCardSeries(series.id)
				.then(() => {
					ElMessage.success("Deleted successfully");
					loadSeriesList();
				})
				.catch((err) => {
					ElMessage.error(`Delete failed: ${err.message}`);
				});
		})
		.catch(() => {
			// 取消删除
		});
}

// 表单处理
function resetForm() {
	formData.name = "";
	formData.code = "";
	formData.description = "";
	formData.sort_order = 0;
	formData.status = 1;
	if (formRef.value) {
		formRef.value.clearValidate();
	}
}

function handleDialogClose() {
	resetForm();
	dialogVisible.value = false;
}

function handleSubmit() {
	if (!formRef.value) return;

	formRef.value.validate((valid: boolean) => {
		if (!valid) return;

		submitLoading.value = true;
		const request = editingId.value
			? updateCardSeries(editingId.value, formData as CardSeriesUpdate)
			: createCardSeries(formData);

		request
			.then(() => {
				ElMessage.success(editingId.value ? "Updated successfully" : "Created successfully");
				dialogVisible.value = false;
				loadSeriesList();
			})
			.catch((err) => {
				ElMessage.error(`Operation failed: ${err.message}`);
			})
			.finally(() => {
				submitLoading.value = false;
			});
	});
}

// 初始化
onMounted(() => {
	loadSeriesList();
});
</script>

<style lang="scss" scoped>
.card-series-container {
	padding: 20px;
	min-height: 100vh;
	background: #f3f3f3;

	.header {
		background: rgba(5, 36, 73, 0.91);
		border-bottom: 3px solid #2563eb;
		padding: 20px;
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 20px;

		.title {
			font-size: 24px;
			margin: 0;
			color: #ffffff;
			font-weight: bold;
			text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
		}

		.create-btn {
			font-weight: 600;
			padding: 10px 20px;
			border-radius: 20px;
		}
	}

	.search-box {
		margin-bottom: 20px;
		padding: 15px;
		background-color: #f5f7fa;
		border-radius: 4px;

		.filter-input,
		.filter-select {
			width: 100%;
		}
	}

	// 新的卡片系列样式，参考角色列表
	.series-gallery-wrapper {
		padding: 20px;
		background: transparent;
	}

	.series-card-wrapper {
		margin-bottom: 20px;
		position: relative;
		border-radius: 8px;
		transition: all 0.3s ease;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
		overflow: hidden;
		background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
		border: 2px solid #e2e8f0;
		height: 210px;
	}

	.series-card-wrapper:hover {
		transform: translateY(-3px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
		border-color: #2563eb;
		z-index: 10;
	}

	.series-card-wrapper.selected {
		border-color: #2563eb;
		box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.3), 0 4px 12px rgba(0, 0, 0, 0.15);
	}

	.series-card-wrapper.selected .select-indicator {
		opacity: 1;
		transform: translateY(0);
	}

	.series-card-inner {
		position: relative;
		height: 100%;
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 15px 10px;
		cursor: pointer;
		text-align: center;
	}

	.series-status-badge {
		position: absolute;
		top: 5px;
		left: 5px;
		background: linear-gradient(135deg, #031528, #1e293b);
		color: #fff;
		padding: 2px 6px;
		border-radius: 12px;
		font-size: 10px;
		font-weight: bold;
		z-index: 5;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
		border: 1px solid #2563eb;
	}

	.series-code-badge {
		position: absolute;
		top: 5px;
		left: 70px;
		background: linear-gradient(135deg, #4f46e5, #3b82f6);
		color: #fff;
		padding: 2px 6px;
		border-radius: 12px;
		font-size: 10px;
		font-weight: bold;
		z-index: 5;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
		border: 1px solid #60a5fa;
	}

	.series-icon-container {
		margin-top: 15px;
		margin-bottom: 10px;
	}

	.series-icon {
		width: 80px;
		height: 80px;
		border-radius: 50%;
		background: linear-gradient(135deg, #60a5fa, #3b82f6);
		display: flex;
		align-items: center;
		justify-content: center;
		border: 3px solid #fff;
		box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
		transition: transform 0.3s;

		.el-icon {
			font-size: 40px;
			color: white;
		}
	}

	.series-card-wrapper:hover .series-icon {
		transform: scale(1.05);
	}

	.series-info {
		flex: 1;
		width: 100%;
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.series-name {
		font-size: 16px;
		margin: 5px 0 2px 0;
		color: var(--el-text-color-primary);
		font-weight: 600;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		width: 100%;
	}

	.series-description {
		font-size: 12px;
		color: #8492a6;
		margin-bottom: 8px;
		max-height: 36px;
		overflow: hidden;
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
	}

	.series-stats {
		display: flex;
		justify-content: center;
		gap: 10px;
		margin: 8px 0;
	}

	.stat-item {
		display: flex;
		align-items: center;
		gap: 3px;
		color: var(--el-text-color-secondary);
		font-size: 10px;
	}

	.series-actions {
		position: absolute;
		top: 5px;
		right: 5px;
		display: flex;
		gap: 5px;
		z-index: 5;
		opacity: 0;
		transition: opacity 0.3s;
	}

	.series-card-wrapper:hover .series-actions {
		opacity: 1;
	}

	.action-btn {
		box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.2);
		transform: scale(0.85);
	}

	.select-indicator {
		position: absolute;
		bottom: 0;
		left: 0;
		width: 100%;
		text-align: center;
		background: #2563eb;
		color: white;
		padding: 4px 0;
		font-size: 12px;
		font-weight: 600;
		opacity: 0;
		transform: translateY(100%);
		transition: all 0.3s;
	}

	.empty-state {
		padding: 60px 20px;
		background: #ffffff;
		border-radius: 8px;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
		margin: 20px 0;
		text-align: center;
	}

	.pagination {
		display: flex;
		justify-content: center;
		margin-top: 20px;
		padding: 20px 0;
	}

	.pagination :deep(.el-pagination) {
		background: #ffffff;
		padding: 15px 20px;
		border-radius: 8px;
		border: 1px solid #e2e8f0;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	}

	.pagination :deep(.el-pager li) {
		background: transparent;
		color: #64748b;
		border: 1px solid #e2e8f0;
		margin: 0 2px;
		border-radius: 4px;
	}

	.pagination :deep(.el-pager li:hover),
	.pagination :deep(.el-pager li.is-active) {
		background: #2563eb;
		color: #ffffff;
		border-color: #2563eb;
	}
}

// 表单样式
.series-form {
	.el-form-item {
		margin-bottom: 24px;
	}
}

// 动画效果
.fade-in {
	animation: fadeIn 0.5s ease-out forwards;
}

.fade-in-up {
	animation: fadeInUp 0.5s ease-out forwards;
	opacity: 0;
}

@keyframes fadeIn {
	from {
		opacity: 0;
	}
	to {
		opacity: 1;
	}
}

@keyframes fadeInUp {
	from {
		opacity: 0;
		transform: translateY(20px);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}

@media (max-width: 768px) {
	.series-gallery {
		justify-content: center;
	}
}
</style>
