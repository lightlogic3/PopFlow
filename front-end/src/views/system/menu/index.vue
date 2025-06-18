<template>
	<div class="app-container">
		<el-card class="box-card">
			<!-- Search Area -->
			<div class="filter-container">
				<el-form :inline="true" :model="queryParams">
					<FormItem label="Menu Name" tooltipKey="name">
						<el-input v-model="queryParams.name" placeholder="Please enter menu name" clearable />
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
				<el-button v-if="hasPermission('system:menu:add')" type="primary" @click="handleAdd">
					<el-icon><Plus /></el-icon>
					Add
				</el-button>
				<el-button @click="toggleExpandAll">
					<el-icon><Operation /></el-icon>
					{{ isExpandAll ? "Collapse" : "Expand" }}
				</el-button>
			</div>

			<!-- Table Area -->
			<el-table
				v-loading="loading"
				:data="menuList"
				row-key="id"
				:tree-props="{ children: 'children' }"
				border
				:expand-row-keys="expandRowKeys"
				style="width: 100%"
			>
				<el-table-column prop="name" label="Menu Name" width="220" />
				<el-table-column prop="icon" label="Icon" align="center" width="80">
					<template #default="scope">
						<el-icon v-if="scope.row.icon"><component :is="scope.row.icon" /></el-icon>
						<span v-else>{{ scope.row.icon }}</span>
					</template>
				</el-table-column>
				<el-table-column prop="sort" label="Sort" width="60" align="center" />
				<el-table-column prop="permission" label="Permission" />
				<el-table-column prop="path" label="Route Path" />
				<el-table-column prop="component" label="Component Path" />
				<el-table-column label="Type" width="80" align="center">
					<template #default="scope">
						<el-tag v-if="scope.row.type === 0" type="primary">Directory</el-tag>
						<el-tag v-else-if="scope.row.type === 1" type="success">Menu</el-tag>
						<el-tag v-else-if="scope.row.type === 2" type="warning">Button</el-tag>
					</template>
				</el-table-column>
				<el-table-column label="Visible" width="80" align="center">
					<template #default="scope">
						<el-tag type="success" v-if="scope.row.visible">Show</el-tag>
						<el-tag type="info" v-else>Hide</el-tag>
					</template>
				</el-table-column>
				<el-table-column label="Status" width="80" align="center">
					<template #default="scope">
						<el-switch
							v-model="scope.row.status"
							:active-value="0"
							:inactive-value="1"
							@change="handleStatusChange(scope.row)"
							:disabled="!hasPermission('system:menu:edit')"
						/>
					</template>
				</el-table-column>
				<el-table-column label="Actions" width="200" fixed="right">
					<template #default="scope">
						<el-button
							v-if="scope.row.type !== 2 && hasPermission('system:menu:add')"
							type="primary"
							link
							@click="handleAddChild(scope.row)"
						>
							Add
						</el-button>
						<el-button v-if="hasPermission('system:menu:edit')" type="primary" link @click="handleEdit(scope.row)">
							Edit
						</el-button>
						<el-button v-if="hasPermission('system:menu:remove')" type="danger" link @click="handleDelete(scope.row)">
							Delete
						</el-button>
					</template>
				</el-table-column>
			</el-table>
		</el-card>

		<!-- Menu Form Dialog -->
		<el-dialog :title="dialog.title" v-model="dialog.visible" width="700px" append-to-body>
			<el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
				<FormItem label="Parent Menu" tooltipKey="parent_id">
					<el-tree-select
						v-model="form.parent_id"
						:data="menuOptions"
						:props="{ label: 'name', children: 'children', value: 'id' }"
						node-key="id"
						placeholder="Select parent menu"
						check-strictly
						clearable
					/>
				</FormItem>
				<FormItem label="Menu Type" prop="type" tooltipKey="type">
					<el-radio-group v-model="form.type">
						<el-radio :label="0">Directory</el-radio>
						<el-radio :label="1">Menu</el-radio>
						<el-radio :label="2">Button</el-radio>
					</el-radio-group>
				</FormItem>
				<FormItem v-if="form.type !== 2" label="Menu Icon" prop="icon" tooltipKey="icon">
					<el-input v-model="form.icon" placeholder="Please enter menu icon" clearable />
				</FormItem>
				<FormItem label="Menu Name" prop="name" tooltipKey="name">
					<el-input v-model="form.name" placeholder="Please enter menu name" />
				</FormItem>
				<FormItem label="Sort" prop="sort" tooltipKey="sort">
					<el-input-number v-model="form.sort" :min="0" :max="999" />
				</FormItem>

				<FormItem v-if="form.type !== 2" label="Route Path" prop="path" tooltipKey="path">
					<el-input v-model="form.path" placeholder="Please enter route path" />
				</FormItem>

				<FormItem v-if="form.type === 1" label="Component Path" prop="component" tooltipKey="component">
					<el-input v-model="form.component" placeholder="Please enter component path" />
				</FormItem>

				<FormItem v-if="form.type === 1" label="Component Name" prop="component_name" tooltipKey="component_name">
					<el-input v-model="form.component_name" placeholder="Please enter component name" />
				</FormItem>

				<FormItem v-if="form.type !== 0" label="Permission" prop="permission" tooltipKey="permission">
					<el-input v-model="form.permission" placeholder="Please enter permission" />
				</FormItem>

				<FormItem v-if="form.type !== 2" label="Display Status" prop="visible" tooltipKey="visible">
					<el-radio-group v-model="form.visible">
						<el-radio :label="true">Show</el-radio>
						<el-radio :label="false">Hide</el-radio>
					</el-radio-group>
				</FormItem>

				<FormItem v-if="form.type !== 2" label="Menu Status" prop="status" tooltipKey="status">
					<el-radio-group v-model="form.status">
						<el-radio :label="0">Normal</el-radio>
						<el-radio :label="1">Disabled</el-radio>
					</el-radio-group>
				</FormItem>

				<FormItem v-if="form.type === 1" label="Keep Alive" prop="keep_alive" tooltipKey="keep_alive">
					<el-radio-group v-model="form.keep_alive">
						<el-radio :label="true">Cache</el-radio>
						<el-radio :label="false">No Cache</el-radio>
					</el-radio-group>
				</FormItem>

				<FormItem v-if="form.type === 1" label="Always Show" prop="always_show" tooltipKey="always_show">
					<el-radio-group v-model="form.always_show">
						<el-radio :label="true">Yes</el-radio>
						<el-radio :label="false">No</el-radio>
					</el-radio-group>
				</FormItem>
			</el-form>
			<template #footer>
				<el-button @click="dialog.visible = false">Cancel</el-button>
				<el-button type="primary" @click="submitForm">Confirm</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from "vue";
import { ElMessage, ElMessageBox, FormInstance } from "element-plus";
import { Search, Plus, Refresh, Operation } from "@element-plus/icons-vue";
import { getMenuList, getMenuTree, getMenuDetail, createMenu, updateMenu, deleteMenu } from "@/api/menu";
import { hasPermission } from "@/utils/permission";
import { deepClone } from "@/utils";

// Query parameters
const queryParams = reactive({
	name: "",
	status: undefined,
});

// Expand/Collapse all
const isExpandAll = ref(false);
const expandRowKeys = ref<string[]>([]);

const toggleExpandAll = () => {
	isExpandAll.value = !isExpandAll.value;
	if (isExpandAll.value) {
		// Expand all nodes
		expandRowKeys.value = menuList.value.map((item) => item.id.toString());
	} else {
		// Collapse all nodes
		expandRowKeys.value = [];
	}
};

// Table data
const loading = ref(false);
const menuList = ref<any[]>([]);

const getMenuData = () => {
	loading.value = true;
	// Build request parameters, ensure undefined values are not passed
	const params: { status?: number } = {};
	if (queryParams.status !== undefined) {
		params.status = queryParams.status;
	}

	getMenuTree(params)
		.then((res) => {
			menuList.value = res || [];
			loading.value = false;
		})
		.catch(() => {
			loading.value = false;
		});
};

const handleQuery = () => {
	if (queryParams.name) {
		// If there are search conditions, use normal list query
		loading.value = true;
		getMenuList({
			name: queryParams.name || undefined,
			status: queryParams.status,
		})
			.then((res) => {
				menuList.value = res.items || [];
				loading.value = false;
			})
			.catch(() => {
				loading.value = false;
			});
	} else {
		// No search conditions, use tree structure
		getMenuData();
	}
};

const resetQuery = () => {
	queryParams.name = "";
	queryParams.status = undefined;
	handleQuery();
};

// Menu form
const dialog = reactive({
	visible: false,
	title: "Add Menu",
});

const formRef = ref<FormInstance>();
const form = reactive({
	id: undefined,
	name: "",
	parent_id: 0,
	sort: 0,
	path: "",
	component: "",
	component_name: "",
	permission: "",
	type: 0,
	visible: true,
	icon: "",
	status: 0,
	keep_alive: true,
	always_show: true,
	meta: "",
});

const rules = reactive({
	name: [{ required: true, message: "Please enter menu name", trigger: "blur" }],
	sort: [{ required: true, message: "Please enter sort order", trigger: "blur" }],
	path: [{ required: true, message: "Please enter route path", trigger: "blur" }],
});

// Parent menu dropdown options
const menuOptions = ref<any[]>([]);

const getMenuSelectOptions = () => {
	// Build menu dropdown options
	const options = [{ id: 0, name: "Main Directory", children: [] as any[] }];
	menuList.value.forEach((item) => {
		if (item.type !== 2) {
			// Exclude button type
			options[0].children.push(deepClone(item));
		}
	});
	menuOptions.value = options;
};

// Add menu
const handleAdd = () => {
	resetForm();
	getMenuSelectOptions();
	dialog.title = "Add Menu";
	dialog.visible = true;
};

// Add child menu
const handleAddChild = (row: any) => {
	resetForm();
	getMenuSelectOptions();
	form.parent_id = row.id;

	if (row.type === 0) {
		// Parent node is directory, child node can be menu
		form.type = 1;
	} else if (row.type === 1) {
		// Parent node is menu, child node can only be button
		form.type = 2;
	}

	dialog.title = "Add Menu";
	dialog.visible = true;
};

// Edit menu
const handleEdit = (row: any) => {
	resetForm();
	getMenuSelectOptions();
	dialog.title = "Edit Menu";
	getMenuDetail(row.id).then((res) => {
		Object.assign(form, res);
		dialog.visible = true;
	});
};

// Reset form
const resetForm = () => {
	form.id = undefined;
	form.name = "";
	form.parent_id = 0;
	form.sort = 0;
	form.path = "";
	form.component = "";
	form.component_name = "";
	form.permission = "";
	form.type = 0;
	form.visible = true;
	form.icon = "";
	form.status = 0;
	form.keep_alive = true;
	form.always_show = true;
	form.meta = "";

	if (formRef.value) {
		formRef.value.resetFields();
	}
};

// Submit form
const submitForm = () => {
	formRef.value?.validate((valid) => {
		if (valid) {
			if (form.id !== undefined) {
				updateMenu(form.id, form).then(() => {
					ElMessage.success("Update successful");
					dialog.visible = false;
					handleQuery();
				});
			} else {
				createMenu(form).then(() => {
					ElMessage.success("Add successful");
					dialog.visible = false;
					handleQuery();
				});
			}
		}
	});
};

// Delete menu
const handleDelete = (row: any) => {
	ElMessageBox.confirm(`Are you sure you want to delete menu "${row.name}"?`, "Warning", {
		confirmButtonText: "Confirm",
		cancelButtonText: "Cancel",
		type: "warning",
	})
		.then(() => {
			deleteMenu(row.id).then(() => {
				ElMessage.success("Delete successful");
				handleQuery();
			});
		})
		.catch(() => {});
};

// Change menu status
const handleStatusChange = (row: any) => {
	const text = row.status === 0 ? "Enable" : "Disable";
	const data = { status: row.status };
	updateMenu(row.id, data)
		.then(() => {
			ElMessage.success(`${text} successful`);
		})
		.catch(() => {
			row.status = row.status === 0 ? 1 : 0;
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
</style>
