<template>
	<div class="app-container">
		<el-card class="box-card">
			<!-- Search Area -->
			<div class="filter-container">
				<el-form :inline="true" :model="queryParams">
					<FormItem label="Role Name" tooltipKey="name">
						<el-input v-model="queryParams.name" placeholder="Please enter role name" clearable />
					</FormItem>
					<FormItem label="Role Code" tooltipKey="code">
						<el-input v-model="queryParams.code" placeholder="Please enter role code" clearable />
					</FormItem>
					<FormItem label="Status" tooltipKey="status">
						<el-select v-model="queryParams.status" placeholder="Please select status" clearable>
							<el-option :value="0" label="Normal" />
							<el-option :value="1" label="Disabled" />
						</el-select>
					</FormItem>
					<el-form-item>
						<el-button type="primary" @click="handleQuery">
							<el-icon><Search /></el-icon>
							Search
						</el-button>
						<el-button @click="resetQuery">
							<el-icon><Refresh /></el-icon>
							Reset
						</el-button>
					</el-form-item>
				</el-form>
			</div>

			<!-- Action Area -->
			<div class="mb-2">
				<el-button v-if="hasPermission('system:role:add')" type="primary" @click="handleAdd">
					<el-icon><Plus /></el-icon>
					Add
				</el-button>
			</div>

			<!-- Table Area -->
			<el-table v-loading="loading" :data="roleList" border style="width: 100%" row-key="id">
				<el-table-column prop="id" label="ID" width="80" />
				<el-table-column prop="name" label="Role Name" width="150" />
				<el-table-column prop="code" label="Role Code" width="150" />
				<el-table-column prop="sort" label="Sort" width="80" />
				<el-table-column label="Status" width="80">
					<template #default="scope">
						<el-switch
							v-model="scope.row.status"
							:active-value="0"
							:inactive-value="1"
							@change="handleStatusChange(scope.row)"
							:disabled="!hasPermission('system:role:edit')"
						/>
					</template>
				</el-table-column>
				<el-table-column prop="remark" label="Remarks" />
				<el-table-column
					prop="create_time"
					label="Create Time"
					width="180"
					:formatter="(row: any, column: any, cellValue: any)=>formatDate(cellValue)"
				/>
				<el-table-column label="Actions" width="240" fixed="right">
					<template #default="scope">
						<el-button v-if="hasPermission('system:role:edit')" type="primary" link @click="handleEdit(scope.row)">
							Edit
						</el-button>
						<el-button
							v-if="hasPermission('system:role:edit')"
							type="success"
							link
							@click="handleAssignMenus(scope.row)"
						>
							Assign Permissions
						</el-button>
						<el-button v-if="hasPermission('system:role:remove')" type="danger" link @click="handleDelete(scope.row)">
							Delete
						</el-button>
					</template>
				</el-table-column>
			</el-table>

			<!-- Pagination Component -->
			<div class="pagination-container">
				<el-pagination
					v-model:current-page="queryParams.skip"
					v-model:page-size="queryParams.limit"
					:page-sizes="[10, 20, 50, 100]"
					layout="total, sizes, prev, pager, next, jumper"
					:total="total"
					@size-change="handleSizeChange"
					@current-change="handleCurrentChange"
				/>
			</div>
		</el-card>

		<!-- Role Form Dialog -->
		<el-dialog :title="dialog.title" v-model="dialog.visible" width="600px" append-to-body>
			<el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
				<FormItem label="Role Name" prop="name" tooltipKey="name">
					<el-input v-model="form.name" placeholder="Please enter role name" />
				</FormItem>
				<FormItem label="Role Code" prop="code" tooltipKey="code">
					<el-input v-model="form.code" placeholder="Please enter role code" />
				</FormItem>
				<FormItem label="Role Sort" prop="sort" tooltipKey="sort">
					<el-input-number v-model="form.sort" :min="0" :max="9999" />
				</FormItem>
				<FormItem label="Data Scope" prop="data_scope" tooltipKey="data_scope">
					<el-select v-model="form.data_scope">
						<el-option :value="1" label="All Data Permission" />
						<el-option :value="2" label="Custom Data Permission" />
					</el-select>
				</FormItem>
				<FormItem label="Role Status" prop="status" tooltipKey="status">
					<el-radio-group v-model="form.status">
						<el-radio :label="0">Normal</el-radio>
						<el-radio :label="1">Disabled</el-radio>
					</el-radio-group>
				</FormItem>
				<FormItem label="Role Type" prop="type" tooltipKey="type">
					<el-select v-model="form.type">
						<el-option :value="1" label="System Role" />
						<el-option :value="2" label="Business Role" />
					</el-select>
				</FormItem>
				<FormItem label="Remarks" prop="remark" tooltipKey="remark">
					<el-input v-model="form.remark" type="textarea" placeholder="Please enter remarks" />
				</FormItem>
			</el-form>
			<template #footer>
				<el-button @click="dialog.visible = false">Cancel</el-button>
				<el-button type="primary" @click="submitForm">Confirm</el-button>
			</template>
		</el-dialog>

		<!-- Assign Permissions Dialog -->
		<el-dialog title="Assign Permissions" v-model="menuDialog.visible" width="600px" append-to-body>
			<el-form label-width="80px">
				<FormItem label="Role Name" tooltipKey="roleName">
					<el-input v-model="menuDialog.roleName" disabled />
				</FormItem>
				<FormItem label="Menu Permissions">
					<el-tree
						ref="menuTreeRef"
						:data="menuDialog.menuTree"
						:props="{ label: 'name', children: 'children' }"
						show-checkbox
						node-key="id"
						:default-checked-keys="menuDialog.checkedMenuIds"
						highlight-current
					/>
				</FormItem>
			</el-form>
			<template #footer>
				<el-button @click="menuDialog.visible = false">Cancel</el-button>
				<el-button type="primary" @click="submitMenuAssign">Confirm</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from "vue";
import { ElMessage, ElMessageBox, FormInstance, ElTree, FormItemRule } from "element-plus";
import { Search, Plus, Refresh } from "@element-plus/icons-vue";
import {
	getRoleList,
	getRoleDetail,
	createRole,
	updateRole,
	deleteRole,
	getRoleMenus,
	assignRoleMenus,
} from "@/api/role_manage";
import type { RoleRecord } from "@/types/api";
import { hasPermission } from "@/utils/permission";
import { formatDate } from "@/utils";

// Query parameters
const queryParams = reactive({
	skip: 1,
	limit: 10,
	name: "",
	code: "",
	status: undefined,
});

// Pagination logic
const total = ref(0);
const loading = ref(false);
const roleList = ref<RoleRecord[]>([]);

const handleQuery = () => {
	loading.value = true;
	getRoleList({
		page: queryParams.skip,
		size: queryParams.limit,
		name: queryParams.name || undefined,
		code: queryParams.code || undefined,
		status: queryParams.status,
	})
		.then((res) => {
			roleList.value = res.items || [];
			total.value = res.total || 0;
		})
		.finally(() => {
			loading.value = false;
		});
};

const resetQuery = () => {
	Object.assign(queryParams, {
		skip: 1,
		limit: 10,
		name: "",
		code: "",
		status: undefined,
	});
	handleQuery();
};

const handleSizeChange = (size: number) => {
	queryParams.limit = size;
	handleQuery();
};

const handleCurrentChange = (page: number) => {
	queryParams.skip = page;
	handleQuery();
};

// Add/Edit dialog
const dialog = reactive({
	visible: false,
	title: "Add Role",
});

const formRef = ref<FormInstance>();
const form = reactive({
	id: undefined,
	name: "",
	code: "",
	sort: 0,
	data_scope: 1,
	status: 0,
	type: 1,
	remark: "",
});

const rules = ref<Record<string, FormItemRule[]>>({
	name: [
		{ required: true, message: "Please enter role name", trigger: "blur" },
		{ min: 2, max: 20, message: "Length should be 2 to 20 characters", trigger: "blur" },
	],
	code: [
		{ required: true, message: "Please enter role code", trigger: "blur" },
		{ min: 2, max: 20, message: "Length should be 2 to 20 characters", trigger: "blur" },
	],
	sort: [{ required: true, message: "Please enter sort number", trigger: "blur" }],
	status: [{ required: true, message: "Please select status", trigger: "change" }],
});

const handleAdd = () => {
	resetForm();
	dialog.title = "Add Role";
	dialog.visible = true;
};

const handleEdit = (row: RoleRecord) => {
	resetForm();
	dialog.title = "Edit Role";
	getRoleDetail(row.id).then((res) => {
		Object.assign(form, res);
		dialog.visible = true;
	});
};

const resetForm = () => {
	form.id = undefined;
	form.name = "";
	form.code = "";
	form.sort = 0;
	form.data_scope = 1;
	form.status = 0;
	form.type = 1;
	form.remark = "";
	if (formRef.value) {
		formRef.value.resetFields();
	}
};

const submitForm = () => {
	formRef.value?.validate((valid) => {
		if (valid) {
			if (form.id !== undefined) {
				updateRole(form.id, form).then(() => {
					ElMessage.success("Update successful");
					dialog.visible = false;
					handleQuery();
				});
			} else {
				createRole(form).then(() => {
					ElMessage.success("Add successful");
					dialog.visible = false;
					handleQuery();
				});
			}
		}
	});
};

// Delete role
const handleDelete = (row: RoleRecord) => {
	ElMessageBox.confirm(`Are you sure you want to delete role "${row.name}"?`, "Warning", {
		confirmButtonText: "Confirm",
		cancelButtonText: "Cancel",
		type: "warning",
	})
		.then(() => {
			deleteRole(row.id).then(() => {
				ElMessage.success("Delete successful");
				handleQuery();
			});
		})
		.catch(() => {});
};

// Change role status
const handleStatusChange = (row: RoleRecord) => {
	const text = row.status === 0 ? "Enable" : "Disable";
	const data = { status: row.status };
	updateRole(row.id, data)
		.then(() => {
			ElMessage.success(`${text} successful`);
		})
		.catch(() => {
			row.status = row.status === 0 ? 1 : 0;
		});
};

// Assign permissions
const menuDialog = reactive({
	visible: false,
	roleId: 0,
	roleName: "",
	menuTree: [] as any[],
	checkedMenuIds: [] as number[],
});

const menuTreeRef = ref<InstanceType<typeof ElTree>>();

const handleAssignMenus = (row: RoleRecord) => {
	menuDialog.roleId = row.id;
	menuDialog.roleName = row.name;
	menuDialog.visible = true;

	getRoleMenus(row.id).then((res) => {
		menuDialog.menuTree = res.menus || [];
		menuDialog.checkedMenuIds = res.checkedKeys || [];
	});
};

const submitMenuAssign = () => {
	const checkedKeys = menuTreeRef.value?.getCheckedKeys() || [];
	const halfCheckedKeys = menuTreeRef.value?.getHalfCheckedKeys() || [];
	const menuIds = [...checkedKeys, ...halfCheckedKeys] as number[];

	assignRoleMenus(menuDialog.roleId, menuIds).then(() => {
		ElMessage.success("Permission assignment successful");
		menuDialog.visible = false;
	});
};

onMounted(() => {
	handleQuery();
});
</script>

<style scoped>
.filter-container {
	padding-bottom: 10px;
}
.pagination-container {
	padding: 10px 0;
}
</style>
