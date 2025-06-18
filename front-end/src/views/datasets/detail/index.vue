<template>
	<div class="dataset-detail-container">
		<div class="dataset-detail-header">
			<el-page-header @back="goBack">
				<template #content>
					<span class="page-header-title">{{ dataset.name || "数据集详情" }}</span>
				</template>
			</el-page-header>
			<div class="dataset-detail-actions">
				<el-button-group>
					<el-button type="success" @click="handleExport">
						<el-icon><Download /></el-icon>
						导出
					</el-button>
					<el-button type="warning" @click="handleImport">
						<el-icon><Upload /></el-icon>
						导入
					</el-button>
				</el-button-group>
			</div>
		</div>

		<el-row :gutter="20" class="dataset-detail-content">
			<el-col :span="24">
				<!-- 基本信息组件 -->
				<dataset-base-info :dataset="dataset" :editable="true" @update="handleDatasetUpdate" />

				<!-- 统计信息组件 -->
				<dataset-stats :dataset-id="datasetId" :dataset-type="dataset.type" />
			</el-col>
		</el-row>

		<!-- 数据条目列表 -->
		<div class="dataset-data-section">
			<el-card class="dataset-data-card">
				<template #header>
					<div class="card-header">
						<span>数据条目</span>
						<el-button type="primary" @click="handleAddData">
							<el-icon><Plus /></el-icon>
							添加数据
						</el-button>
					</div>
				</template>

				<div class="data-search">
					<el-input
						v-model="dataQuery.keyword"
						placeholder="搜索关键词"
						clearable
						@keyup.enter="handleDataFilter"
						@clear="handleDataFilter"
						class="data-search-input"
					>
						<template #prefix>
							<el-icon><Search /></el-icon>
						</template>
					</el-input>
					<el-button type="primary" @click="handleDataFilter">查询</el-button>
					<el-button @click="resetDataFilter">重置</el-button>
				</div>

				<!-- SFT数据表格 -->
				<div v-if="dataset.type === DatasetType.SFT">
					<sft-data-table
						:loading="dataLoading"
						:data-list="dataList"
						@edit="handleEditData"
						@delete="handleDeleteData"
					/>
				</div>

				<!-- DPO数据表格 -->
				<div v-else-if="dataset.type === DatasetType.DPO">
					<dpo-data-table
						:loading="dataLoading"
						:data-list="dataList"
						@edit="handleEditData"
						@delete="handleDeleteData"
					/>
				</div>

				<!-- 会话数据表格 -->
				<div v-else-if="dataset.type === DatasetType.CONVERSATION">
					<conversation-data-table
						:loading="dataLoading"
						:data-list="dataList"
						@view="handleViewConversation"
						@edit="handleEditData"
						@delete="handleDeleteData"
					/>
				</div>

				<el-pagination
					v-if="dataTotal > 0"
					class="data-pagination"
					:current-page="dataQuery.page"
					:page-sizes="[10, 20, 30, 50]"
					:page-size="dataQuery.limit"
					layout="total, sizes, prev, pager, next, jumper"
					:total="dataTotal"
					@size-change="handleDataSizeChange"
					@current-change="handleDataCurrentChange"
				/>

				<el-empty v-else description="暂无数据" />
			</el-card>
		</div>

		<!-- 数据表单对话框 -->
		<el-dialog :title="dialogTitle" v-model="dialogVisible" width="60%" destroy-on-close>
			<!-- SFT数据表单 -->
			<sft-form v-if="dataset.type === DatasetType.SFT" ref="dataFormRef" :form-data="dataForm" :edit-mode="editMode" />

			<!-- DPO数据表单 -->
			<dpo-form
				v-else-if="dataset.type === DatasetType.DPO"
				ref="dataFormRef"
				:form-data="dataForm"
				:edit-mode="editMode"
			/>

			<!-- 会话数据表单 -->
			<conversation-form
				v-else-if="dataset.type === DatasetType.CONVERSATION"
				ref="dataFormRef"
				:form-data="dataForm"
				:edit-mode="editMode"
			/>

			<template #footer>
				<span class="dialog-footer">
					<el-button @click="dialogVisible = false">取消</el-button>
					<el-button type="primary" @click="submitDataForm">确定</el-button>
				</span>
			</template>
		</el-dialog>

		<!-- 导入对话框 -->
		<el-dialog title="导入数据" v-model="importDialogVisible" width="500px">
			<el-form ref="importFormRef" :model="importForm" label-width="80px">
				<el-form-item label="文件">
					<el-upload
						class="upload-demo"
						drag
						action="#"
						:auto-upload="false"
						:on-change="handleFileChange"
						:limit="1"
						:file-list="fileList"
					>
						<el-icon class="el-icon--upload"><Upload /></el-icon>
						<div class="el-upload__text">拖拽文件到此处或 <em>点击上传</em></div>
						<template #tip>
							<div class="el-upload__tip">支持JSON、CSV或JSONL格式，最大10MB</div>
						</template>
					</el-upload>
				</el-form-item>
			</el-form>
			<template #footer>
				<span class="dialog-footer">
					<el-button @click="importDialogVisible = false">取消</el-button>
					<el-button type="primary" @click="submitImport" :disabled="!importForm.file">导入</el-button>
				</span>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, defineAsyncComponent } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { Download, Upload, Plus, Search } from "@element-plus/icons-vue";
import {
	getDatasetDetail,
	exportDataset,
	importDataset,
	getSftEntries,
	getDpoEntries,
	getConversations,
	getConversationDetail,
	createSftEntry,
	updateSftEntry,
	deleteSftEntry,
	createDpoEntry,
	updateDpoEntry,
	deleteDpoEntry,
	createConversation,
	updateConversation,
	deleteConversation,
} from "@/api/datasets";
import { Dataset, DatasetType, DataQuery, ConversationEntry } from "@/types/dataset";

// 导入组件
const DatasetBaseInfo = defineAsyncComponent(() => import("../components/DatasetBaseInfo.vue"));
const DatasetStats = defineAsyncComponent(() => import("../components/DatasetStats.vue"));
const SftDataTable = defineAsyncComponent(() => import("./components/SftDataTable.vue"));
const DpoDataTable = defineAsyncComponent(() => import("./components/DpoDataTable.vue"));
const ConversationDataTable = defineAsyncComponent(() => import("./components/ConversationDataTable.vue"));
const SftForm = defineAsyncComponent(() => import("./components/SftForm.vue"));
const DpoForm = defineAsyncComponent(() => import("./components/DpoForm.vue"));
const ConversationForm = defineAsyncComponent(() => import("./components/ConversationForm.vue"));

/**
 * 数据集详情页面
 * @description 展示数据集详细信息和管理数据条目
 */

// 路由相关
const route = useRoute();
const router = useRouter();
const datasetId = ref<number>(parseInt(route.params.id as string));

// 响应式状态
const dataset = ref<Dataset>({} as Dataset);
const loading = ref(false);
const dataList = ref<any[]>([]);
const dataTotal = ref(0);
const dataLoading = ref(false);
const dataQuery = reactive<DataQuery>({
	page: 1,
	limit: 10,
	keyword: undefined,
});

// 对话框相关状态
const dialogVisible = ref(false);
const dialogTitle = ref("");
const editMode = ref(false);
const dataFormRef = ref<any>();
const dataForm = reactive<any>({});

// 导入对话框相关状态
const importDialogVisible = ref(false);
const importFormRef = ref();
const importForm = reactive({
	file: null as File | null,
});
const fileList = ref<any[]>([]);

/**
 * 返回上一页
 */
const goBack = () => {
	router.push("/datasets/list");
};

/**
 * 获取数据集详情
 */
const fetchDataset = async () => {
	loading.value = true;
	try {
		const response = await getDatasetDetail(datasetId.value);
		dataset.value = response;
		await fetchDataList();
	} catch (error) {
		if (error instanceof Error) {
			ElMessage.error(`获取数据集详情失败: ${error.message}`);
		} else {
			ElMessage.error("获取数据集详情失败");
		}
		console.error("获取数据集详情失败:", error);
	} finally {
		loading.value = false;
	}
};

/**
 * 处理数据集更新
 */
const handleDatasetUpdate = (updatedDataset: Dataset) => {
	dataset.value = updatedDataset;
};

/**
 * 获取数据列表
 */
const fetchDataList = async () => {
	if (!dataset.value.type) return;

	dataLoading.value = true;

	try {
		let response: any;

		switch (dataset.value.type) {
			case DatasetType.SFT:
				response = await getSftEntries(datasetId.value, dataQuery);
				break;
			case DatasetType.DPO:
				response = await getDpoEntries(datasetId.value, dataQuery);
				break;
			case DatasetType.CONVERSATION:
				response = await getConversations(datasetId.value, dataQuery);
				break;
			default:
				throw new Error("不支持的数据集类型");
		}

		dataList.value = response || [];
		dataTotal.value = response.total || 0;
	} catch (error) {
		if (error instanceof Error) {
			ElMessage.error(`获取数据列表失败: ${error.message}`);
		} else {
			ElMessage.error("获取数据列表失败");
		}
		console.error("获取数据列表失败:", error);
	} finally {
		dataLoading.value = false;
	}
};

/**
 * 处理数据查询
 */
const handleDataFilter = () => {
	dataQuery.page = 1;
	fetchDataList();
};

/**
 * 重置数据查询
 */
const resetDataFilter = () => {
	dataQuery.page = 1;
	dataQuery.limit = 10;
	dataQuery.keyword = undefined;
	fetchDataList();
};

/**
 * 处理数据条目每页数量变化
 */
const handleDataSizeChange = (val: number) => {
	dataQuery.limit = val;
	fetchDataList();
};

/**
 * 处理数据条目页码变化
 */
const handleDataCurrentChange = (val: number) => {
	dataQuery.page = val;
	fetchDataList();
};

/**
 * 导出数据集
 */
const handleExport = () => {
	ElMessageBox.confirm("确定要导出该数据集吗?", "提示", {
		confirmButtonText: "确定",
		cancelButtonText: "取消",
		type: "info",
	})
		.then(async () => {
			try {
				const blob = await exportDataset(datasetId.value);

				// 处理下载
				const downloadLink = document.createElement("a");
				downloadLink.href = URL.createObjectURL(blob);
				downloadLink.download = `${dataset.value.name || "dataset"}_${datasetId.value}.json`;
				downloadLink.click();
				URL.revokeObjectURL(downloadLink.href);

				ElMessage({
					type: "success",
					message: "导出成功",
				});
			} catch (error) {
				if (error instanceof Error) {
					ElMessage.error(`导出失败: ${error.message}`);
				} else {
					ElMessage.error("导出失败");
				}
			}
		})
		.catch(() => {
			// 用户取消操作
		});
};

/**
 * 导入数据集
 */
const handleImport = () => {
	importDialogVisible.value = true;
	importForm.file = null;
	fileList.value = [];
};

/**
 * 处理文件变更
 */
const handleFileChange = (file: any) => {
	importForm.file = file.raw;
};

/**
 * 提交导入
 */
const submitImport = async () => {
	if (!importForm.file) {
		ElMessage.error("请选择文件");
		return;
	}

	const formData = new FormData();
	formData.append("file", importForm.file);

	try {
		await importDataset(datasetId.value, formData);
		ElMessage({
			type: "success",
			message: "导入成功",
		});
		importDialogVisible.value = false;
		fetchDataList(); // 重新加载数据
	} catch (error) {
		if (error instanceof Error) {
			ElMessage.error(`导入失败: ${error.message}`);
		} else {
			ElMessage.error("导入失败");
		}
	}
};

/**
 * 添加数据
 */
const handleAddData = () => {
	dialogTitle.value = "添加数据";
	editMode.value = false;
	resetDataForm();
	dialogVisible.value = true;
};

/**
 * 查看会话
 */
const handleViewConversation = async (row: ConversationEntry) => {
	try {
		await getConversationDetail(row.conversation_id);
		// 可以在这里显示会话详情，也可以跳转到会话详情页
		router.push({
			path: `/datasets/conversation/${row.conversation_id}`,
			query: { datasetId: datasetId.value.toString() },
		});
	} catch (error) {
		if (error instanceof Error) {
			ElMessage.error(`获取会话详情失败: ${error.message}`);
		} else {
			ElMessage.error("获取会话详情失败");
		}
	}
};

/**
 * 编辑数据
 */
const handleEditData = (row: any) => {
	dialogTitle.value = "编辑数据";
	editMode.value = true;
	resetDataForm();

	switch (dataset.value.type) {
		case DatasetType.SFT:
			dataForm.id = row.id;
			dataForm.instruction = row.instruction;
			dataForm.input = row.input || "";
			dataForm.output = row.output;
			break;
		case DatasetType.DPO:
			dataForm.id = row.id;
			dataForm.prompt = row.query || row.prompt;
			dataForm.chosen = row.chosen_response || row.chosen;
			dataForm.rejected = row.rejected_response || row.rejected;
			break;
		case DatasetType.CONVERSATION:
			dataForm.id = row.id;
			dataForm.title = row.title || "";
			dataForm.messages = row.messages || [{ role: "user", content: "" }];
			break;
	}

	dialogVisible.value = true;
};

/**
 * 删除数据
 */
const handleDeleteData = (row: any) => {
	ElMessageBox.confirm("确认删除该数据吗？删除后将无法恢复。", "提示", {
		confirmButtonText: "确定",
		cancelButtonText: "取消",
		type: "warning",
	})
		.then(async () => {
			try {
				switch (dataset.value.type) {
					case DatasetType.SFT:
						await deleteSftEntry(row.id);
						break;
					case DatasetType.DPO:
						await deleteDpoEntry(row.id);
						break;
					case DatasetType.CONVERSATION:
						await deleteConversation(row.conversation_id);
						break;
					default:
						throw new Error("不支持的数据集类型");
				}

				ElMessage({
					type: "success",
					message: "删除成功!",
				});
				fetchDataList();
			} catch (error) {
				if (error instanceof Error) {
					ElMessage.error(`删除失败: ${error.message}`);
				} else {
					ElMessage.error("删除失败");
				}
			}
		})
		.catch(() => {
			// 用户取消操作
		});
};

/**
 * 重置数据表单
 */
const resetDataForm = () => {
	switch (dataset.value.type) {
		case DatasetType.SFT:
			dataForm.id = undefined;
			dataForm.instruction = "";
			dataForm.input = "";
			dataForm.output = "";
			break;
		case DatasetType.DPO:
			dataForm.id = undefined;
			dataForm.prompt = "";
			dataForm.chosen = "";
			dataForm.rejected = "";
			break;
		case DatasetType.CONVERSATION:
			dataForm.id = undefined;
			dataForm.title = "";
			dataForm.messages = [{ role: "user", content: "" }];
			break;
		default:
			Object.keys(dataForm).forEach((key) => delete dataForm[key]);
	}
};

/**
 * 提交数据表单
 */
const submitDataForm = async () => {
	if (!dataFormRef.value) return;

	try {
		const valid = await dataFormRef.value.validate();

		if (valid) {
			try {
				const formData = dataFormRef.value.getFormData();

				if (editMode.value) {
					// 编辑模式
					switch (dataset.value.type) {
						case DatasetType.SFT:
							await updateSftEntry(formData.id, formData);
							break;
						case DatasetType.DPO:
							await updateDpoEntry(formData.id, formData);
							break;
						case DatasetType.CONVERSATION:
							await updateConversation(formData.id, formData);
							break;
						default:
							throw new Error("不支持的数据集类型");
					}

					ElMessage({
						type: "success",
						message: "更新成功!",
					});
				} else {
					// 创建模式
					formData.datasetId = datasetId.value;

					switch (dataset.value.type) {
						case DatasetType.SFT:
							await createSftEntry(formData);
							break;
						case DatasetType.DPO:
							await createDpoEntry(formData);
							break;
						case DatasetType.CONVERSATION:
							await createConversation(formData);
							break;
						default:
							throw new Error("不支持的数据集类型");
					}

					ElMessage({
						type: "success",
						message: "添加成功!",
					});
				}

				dialogVisible.value = false;
				fetchDataList();
			} catch (error) {
				if (error instanceof Error) {
					ElMessage.error(`操作失败: ${error.message}`);
				} else {
					ElMessage.error("操作失败");
				}
			}
		}
	} catch (error) {
		console.error("表单验证错误:", error);
	}
};

// 生命周期钩子
onMounted(() => {
	fetchDataset();
});
</script>

<style lang="scss" scoped>
.dataset-detail-container {
	.dataset-detail-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 20px;

		.page-header-title {
			font-size: 18px;
			font-weight: 600;
		}

		.dataset-detail-actions {
			display: flex;
			gap: 10px;
		}
	}

	.dataset-detail-content {
		margin-bottom: 20px;
	}

	.dataset-data-section {
		margin-bottom: 20px;

		.dataset-data-card {
			.card-header {
				display: flex;
				justify-content: space-between;
				align-items: center;
			}

			.data-search {
				display: flex;
				align-items: center;
				gap: 10px;
				margin-bottom: 20px;

				.data-search-input {
					width: 300px;
				}
			}

			.data-pagination {
				margin-top: 20px;
				text-align: right;
			}
		}
	}
}
</style>
