<template>
	<div class="dataset-list-container">
		<div class="dataset-list-header">
			<h1>数据集管理</h1>
			<el-button type="primary" @click="handleCreateDataset">创建数据集</el-button>
		</div>

		<el-card class="dataset-list-card">
			<div class="dataset-list-search">
				<el-input
					v-model="listQuery.name"
					placeholder="数据集名称"
					clearable
					@keyup.enter="handleFilter"
					@clear="handleFilter"
				>
					<template #prefix>
						<el-icon><Search /></el-icon>
					</template>
				</el-input>
				<el-select v-model="listQuery.type" placeholder="数据集类型" clearable @change="handleFilter">
					<el-option v-for="type in datasetTypes" :key="type.value" :label="type.label" :value="type.value" />
				</el-select>
				<el-button type="primary" @click="handleFilter">查询</el-button>
				<el-button @click="resetFilter">重置</el-button>
			</div>

			<el-table v-loading="listLoading" :data="list" border fit highlight-current-row element-loading-text="加载中...">
				<el-table-column label="ID" prop="id" width="80" align="center" />
				<el-table-column label="名称" prop="name" min-width="80" />
				<el-table-column label="描述" prop="description">
					<template #default="scope">
						<span>{{ scope.row.description || "暂无描述" }}</span>
					</template>
				</el-table-column>
				<el-table-column label="类型" prop="type" width="200" align="center">
					<template #default="scope">
						<el-tag :type="getDatasetTypeTag(scope.row.type) as any">
							{{ getDatasetTypeLabel(scope.row.type) }}
						</el-tag>
					</template>
				</el-table-column>
				<el-table-column label="条目数量" prop="entryCount" width="100" align="center" />
				<el-table-column label="创建时间" width="160" align="center">
					<template #default="scope">
						<span>{{ formatTimestamp(scope.row.createdAt) }}</span>
					</template>
				</el-table-column>
				<el-table-column label="更新时间" width="160" align="center">
					<template #default="scope">
						<span>{{ formatTimestamp(scope.row.updatedAt) }}</span>
					</template>
				</el-table-column>
				<el-table-column label="操作" width="220" align="center">
					<template #default="scope">
						<el-button type="primary" size="small" @click="handleView(scope.row)">查看</el-button>
						<el-button type="success" size="small" @click="handleEdit(scope.row)">编辑</el-button>
						<el-button type="danger" size="small" @click="handleDelete(scope.row)">删除</el-button>
					</template>
				</el-table-column>
			</el-table>

			<el-pagination
				v-if="total > 0"
				class="dataset-list-pagination"
				:current-page="listQuery.page"
				:page-sizes="[10, 20, 30, 50]"
				:page-size="listQuery.limit"
				layout="total, sizes, prev, pager, next, jumper"
				:total="total"
				@size-change="handleSizeChange"
				@current-change="handleCurrentChange"
			/>
		</el-card>

		<!-- 数据集表单对话框 -->
		<el-dialog :title="dialogTitle" v-model="dialogVisible" width="50%">
			<el-form ref="datasetFormRef" :model="datasetForm" :rules="datasetRules" label-width="100px">
				<el-form-item label="名称" prop="name">
					<el-input v-model="datasetForm.name" placeholder="请输入数据集名称" maxlength="50" show-word-limit />
					<template #tip>
						<div class="form-tip">数据集名称，用于标识数据集</div>
					</template>
				</el-form-item>
				<el-form-item label="描述" prop="description">
					<el-input
						v-model="datasetForm.description"
						type="textarea"
						placeholder="请输入数据集描述"
						:rows="3"
						maxlength="200"
						show-word-limit
					/>
					<template #tip>
						<div class="form-tip">对数据集的详细描述，帮助理解数据集用途和内容</div>
					</template>
				</el-form-item>
				<el-form-item label="类型" prop="type">
					<el-select v-model="datasetForm.type" placeholder="请选择数据集类型">
						<el-option v-for="type in datasetTypes" :key="type.value" :label="type.label" :value="type.value" />
					</el-select>
					<template #tip>
						<div class="form-tip">SFT用于指令微调训练，DPO用于偏好优化训练，CONVERSATION用于对话训练</div>
					</template>
				</el-form-item>
				<el-form-item label="标签" prop="tags">
					<el-input v-model="datasetForm.tags" placeholder="多个标签请用逗号分隔" maxlength="100" show-word-limit />
					<template #tip>
						<div class="form-tip">为数据集添加标签，方便分类和筛选，多个标签用逗号分隔</div>
					</template>
				</el-form-item>
			</el-form>
			<template #footer>
				<span class="dialog-footer">
					<el-button @click="dialogVisible = false">取消</el-button>
					<el-button type="primary" @click="submitDatasetForm">确定</el-button>
				</span>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { Search } from "@element-plus/icons-vue";
import type { FormInstance, FormRules } from "element-plus";
import { getDatasetList, createDataset, updateDataset, deleteDataset } from "@/api/datasets";
import { formatTimestamp, getDatasetTypeTag, getDatasetTypeLabel } from "@/utils/dataset";
import { Dataset, DatasetType, DatasetListQuery } from "@/types/dataset";

/**
 * 数据集列表组件
 * @description 用于展示和管理数据集列表
 */

// 路由实例
const router = useRouter();

// 数据集类型列表
const datasetTypes = [
	{ label: "SFT(指令微调)", value: DatasetType.SFT },
	{ label: "DPO(直接偏好优化)", value: DatasetType.DPO },
	{ label: "CONVERSATION(对话)", value: DatasetType.CONVERSATION },
];

// 响应式状态
const list = ref<any>([]);
const total = ref(0);
const listLoading = ref(false);
const listQuery = reactive<DatasetListQuery>({
	page: 1,
	limit: 10,
	name: undefined,
	type: undefined,
});

// 对话框相关状态
const dialogVisible = ref(false);
const dialogTitle = ref("");
const editMode = ref(false);
const datasetFormRef = ref<FormInstance>();
const datasetForm = reactive({
	id: undefined as number | undefined,
	name: "",
	description: "",
	type: "" as DatasetType | string,
	tags: "",
});

// 表单验证规则
const datasetRules = reactive<FormRules>({
	name: [
		{ required: true, message: "请输入数据集名称", trigger: "blur" },
		{ min: 2, max: 50, message: "长度在 2 到 50 个字符", trigger: "blur" },
	],
	type: [{ required: true, message: "请选择数据集类型", trigger: "change" }],
});

// 生命周期钩子
onMounted(() => {
	fetchDatasetList();
});

/**
 * 获取数据集列表
 */
const fetchDatasetList = async () => {
	listLoading.value = true;
	try {
		const response = await getDatasetList(listQuery);
		if (response) {
			list.value = response;
			total.value = response.total;
		} else {
			list.value = [];
			total.value = 0;
		}
	} catch (error) {
		if (error instanceof Error) {
			ElMessage.error(`获取数据集列表失败: ${error.message}`);
		} else {
			ElMessage.error("获取数据集列表失败");
		}
		console.error("获取数据集列表失败:", error);
	} finally {
		listLoading.value = false;
	}
};

/**
 * 处理查询
 */
const handleFilter = () => {
	listQuery.page = 1;
	fetchDatasetList();
};

/**
 * 重置查询条件
 */
const resetFilter = () => {
	listQuery.page = 1;
	listQuery.limit = 10;
	listQuery.name = undefined;
	listQuery.type = undefined;
	fetchDatasetList();
};

/**
 * 处理每页数量变化
 */
const handleSizeChange = (val: number) => {
	listQuery.limit = val;
	fetchDatasetList();
};

/**
 * 处理页码变化
 */
const handleCurrentChange = (val: number) => {
	listQuery.page = val;
	fetchDatasetList();
};

/**
 * 重置表单
 */
const resetForm = () => {
	datasetForm.id = undefined;
	datasetForm.name = "";
	datasetForm.description = "";
	datasetForm.type = "";
	datasetForm.tags = "";

	if (datasetFormRef.value) {
		datasetFormRef.value.resetFields();
	}
};

/**
 * 创建数据集
 */
const handleCreateDataset = () => {
	dialogTitle.value = "创建数据集";
	editMode.value = false;
	resetForm();
	dialogVisible.value = true;
};

/**
 * 查看数据集详情
 */
const handleView = (row: Dataset) => {
	router.push({ path: `/datasets/detail/${row.id}` });
};

/**
 * 编辑数据集
 */
const handleEdit = (row: Dataset) => {
	dialogTitle.value = "编辑数据集";
	editMode.value = true;

	// 复制数据集信息到表单
	datasetForm.id = row.id;
	datasetForm.name = row.name;
	datasetForm.description = row.description || "";
	datasetForm.type = row.type;
	datasetForm.tags = row.tags || "";

	dialogVisible.value = true;
};

/**
 * 删除数据集
 */
const handleDelete = (row: Dataset) => {
	ElMessageBox.confirm("确认删除该数据集吗？删除后数据将无法恢复，请谨慎操作。", "删除确认", {
		confirmButtonText: "确定",
		cancelButtonText: "取消",
		type: "warning",
	})
		.then(async () => {
			try {
				await deleteDataset(row.id);
				ElMessage({
					type: "success",
					message: "删除成功!",
				});
				fetchDatasetList();
			} catch (error) {
				if (error instanceof Error) {
					ElMessage.error(`删除失败: ${error.message}`);
				} else {
					ElMessage.error("删除失败");
				}
			}
		})
		.catch(() => {
			// 用户取消删除，不做任何操作
		});
};

/**
 * 提交数据集表单
 */
const submitDatasetForm = async () => {
	if (!datasetFormRef.value) return;

	try {
		await datasetFormRef.value.validate(async (valid) => {
			if (valid) {
				try {
					if (editMode.value && datasetForm.id !== undefined) {
						// 编辑模式
						await updateDataset(datasetForm.id, {
							name: datasetForm.name,
							description: datasetForm.description,
							tags: datasetForm.tags,
						});
						ElMessage({
							type: "success",
							message: "更新成功!",
						});
					} else {
						// 创建模式
						await createDataset({
							name: datasetForm.name,
							type: datasetForm.type as DatasetType,
							description: datasetForm.description,
							tags: datasetForm.tags,
						});
						ElMessage({
							type: "success",
							message: "创建成功!",
						});
					}
					dialogVisible.value = false;
					fetchDatasetList();
				} catch (error) {
					if (error instanceof Error) {
						ElMessage.error(`操作失败: ${error.message}`);
					} else {
						ElMessage.error("操作失败");
					}
				}
			}
		});
	} catch (error) {
		console.error("表单验证错误:", error);
	}
};
</script>

<style lang="scss" scoped>
.dataset-list-container {
	.dataset-list-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 20px;

		h1 {
			margin: 0;
			font-size: 24px;
			font-weight: 600;
			color: #303133;
		}
	}

	.dataset-list-card {
		margin-bottom: 20px;

		.dataset-list-search {
			display: flex;
			margin-bottom: 20px;
			gap: 10px;
			align-items: center;
			flex-wrap: wrap;

			.el-input {
				width: 200px;
			}

			.el-select {
				width: 200px;
			}
		}

		.dataset-list-pagination {
			margin-top: 20px;
			text-align: right;
		}
	}

	:deep(.form-tip) {
		color: #909399;
		font-size: 12px;
		line-height: 1.5;
		margin-top: 2px;
	}
}
</style>
