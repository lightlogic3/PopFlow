<template>
	<div class="app-container">
		<el-card class="box-card">
			<!-- 搜索区域 -->
			<div class="filter-container">
				<el-form :inline="true" :model="queryParams">
					<FormItem label="用户名" tooltipKey="username">
						<el-input v-model="queryParams.username" placeholder="请输入用户名" clearable />
					</FormItem>
					<FormItem label="昵称" tooltipKey="nickname">
						<el-input v-model="queryParams.nickname" placeholder="请输入昵称" clearable />
					</FormItem>
					<FormItem label="手机号" tooltipKey="mobile">
						<el-input v-model="queryParams.mobile" placeholder="请输入手机号" clearable />
					</FormItem>
					<FormItem label="状态" tooltipKey="status">
						<el-select v-model="queryParams.status" placeholder="请选择状态" clearable>
							<el-option :value="0" label="正常" />
							<el-option :value="1" label="停用" />
						</el-select>
					</FormItem>
					<el-form-item>
						<el-button type="primary" @click="handleQuery">
							<el-icon><Search /></el-icon>
							查询
						</el-button>
						<el-button @click="resetQuery">
							<el-icon><Refresh /></el-icon>
							重置
						</el-button>
					</el-form-item>
				</el-form>
			</div>

			<!-- 操作区域 -->
			<div class="mb-2">
				<el-button v-if="hasPermission('system:user:add')" type="primary" @click="handleAdd">
					<el-icon><Plus /></el-icon>
					新增
				</el-button>
			</div>

			<!-- 表格区域 -->
			<el-table v-loading="loading" :data="userList" border style="width: 100%" row-key="id">
				<el-table-column prop="id" label="ID" width="80" />
				<el-table-column prop="username" label="用户名" width="120" />
				<el-table-column prop="nickname" label="昵称" width="120">
					<template #default="scope">
						<router-link :to="'/system/role/detail/' + scope.row.id" class="user-link">
							{{ scope.row.nickname }}
						</router-link>
					</template>
				</el-table-column>
				<el-table-column prop="email" label="邮箱" />
				<el-table-column prop="mobile" label="手机号" width="120" />
				<el-table-column label="性别" width="80">
					<template #default="scope">
						<el-tag v-if="scope.row.sex === 1" type="success">男</el-tag>
						<el-tag v-else-if="scope.row.sex === 2" type="danger">女</el-tag>
						<el-tag v-else type="info">未知</el-tag>
					</template>
				</el-table-column>
				<el-table-column label="状态" width="80">
					<template #default="scope">
						<el-switch
							v-model="scope.row.status"
							:active-value="0"
							:inactive-value="1"
							@change="handleStatusChange(scope.row)"
							:disabled="!hasPermission('system:user:edit')"
						/>
					</template>
				</el-table-column>
				<el-table-column prop="login_date" label="最后登录时间" width="180">
					<template #default="scope">
						{{ formatDate(scope.row.login_date) }}
					</template>
				</el-table-column>
				<el-table-column label="操作" width="340" fixed="right">
					<template #default="scope">
						<el-button v-if="hasPermission('system:user:edit')" type="primary" link @click="handleEdit(scope.row)">
							编辑
						</el-button>
						<el-button
							v-if="hasPermission('system:user:resetPwd')"
							type="warning"
							link
							@click="handleResetPwd(scope.row)"
						>
							重置密码
						</el-button>
						<el-button
							v-if="hasPermission('system:user:edit')"
							type="success"
							link
							@click="handleAssignRoles(scope.row)"
						>
							分配角色
						</el-button>
						<el-button v-if="hasPermission('system:user:remove')" type="danger" link @click="handleDelete(scope.row)">
							删除
						</el-button>
					</template>
				</el-table-column>
			</el-table>

			<!-- 分页组件 -->
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

		<!-- 用户表单对话框 -->
		<el-dialog :title="dialog.title" v-model="dialog.visible" width="600px" append-to-body>
			<el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
				<FormItem label="用户名" prop="username" tooltipKey="username">
					<el-input v-model="form.username" placeholder="请输入用户名" :disabled="form.id !== undefined" />
				</FormItem>
				<FormItem label="昵称" prop="nickname" tooltipKey="nickname">
					<el-input v-model="form.nickname" placeholder="请输入昵称" />
				</FormItem>
				<FormItem label="密码" prop="password" v-if="form.id === undefined" tooltipKey="password">
					<el-input v-model="form.password" placeholder="请输入密码" type="password" show-password />
				</FormItem>
				<FormItem label="邮箱" prop="email" tooltipKey="email">
					<el-input v-model="form.email" placeholder="请输入邮箱" />
				</FormItem>
				<FormItem label="手机号" prop="mobile" tooltipKey="mobile">
					<el-input v-model="form.mobile" placeholder="请输入手机号" />
				</FormItem>
				<FormItem label="性别" prop="sex" tooltipKey="sex">
					<el-radio-group v-model="form.sex">
						<el-radio :label="0">未知</el-radio>
						<el-radio :label="1">男</el-radio>
						<el-radio :label="2">女</el-radio>
					</el-radio-group>
				</FormItem>
				<FormItem label="状态" prop="status" tooltipKey="status">
					<el-radio-group v-model="form.status">
						<el-radio :label="0">正常</el-radio>
						<el-radio :label="1">停用</el-radio>
					</el-radio-group>
				</FormItem>
				<FormItem label="备注" prop="remark" tooltipKey="remark">
					<el-input v-model="form.remark" type="textarea" placeholder="请输入备注" />
				</FormItem>
			</el-form>
			<template #footer>
				<el-button @click="dialog.visible = false">取 消</el-button>
				<el-button type="primary" @click="submitForm">确 定</el-button>
			</template>
		</el-dialog>

		<!-- 重置密码对话框 -->
		<el-dialog title="重置密码" v-model="pwdDialog.visible" width="500px" append-to-body>
			<el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="100px">
				<FormItem label="新密码" prop="password" tooltipKey="password">
					<el-input v-model="pwdForm.password" placeholder="请输入新密码" type="password" show-password />
				</FormItem>
				<FormItem label="确认密码" prop="confirmPassword" tooltipKey="confirmPassword">
					<el-input v-model="pwdForm.confirmPassword" placeholder="请确认密码" type="password" show-password />
				</FormItem>
			</el-form>
			<template #footer>
				<el-button @click="pwdDialog.visible = false">取 消</el-button>
				<el-button type="primary" @click="submitResetPwd">确 定</el-button>
			</template>
		</el-dialog>

		<!-- 分配角色对话框 -->
		<el-dialog title="分配角色" v-model="roleDialog.visible" width="500px" append-to-body>
			<el-form label-width="80px">
				<FormItem label="用户名" tooltipKey="username">
					<el-input v-model="roleDialog.username" disabled />
				</FormItem>
				<FormItem label="角色列表" tooltipKey="checkedRoleIds">
					<el-checkbox-group v-model="roleDialog.checkedRoleIds">
						<el-checkbox v-for="role in roleDialog.roleList" :key="role.id" :label="role.id">
							{{ role.name }}
						</el-checkbox>
					</el-checkbox-group>
				</FormItem>
			</el-form>
			<template #footer>
				<el-button @click="roleDialog.visible = false">取 消</el-button>
				<el-button type="primary" @click="submitRoleAssign">确 定</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from "vue";
import { ElMessage, ElMessageBox, FormInstance, FormItemRule } from "element-plus";
import { Search, Plus, Refresh } from "@element-plus/icons-vue";
import {
	getUserList,
	getUserDetail,
	createUser,
	updateUser,
	deleteUser,
	resetUserPassword,
	changeUserStatus,
	getUserRoles,
	assignUserRoles,
} from "@/api/user";
import { hasPermission } from "@/utils/permission";
import { formatDate } from "@/utils";

// 用户权限判断

// 查询参数
const queryParams = reactive({
	skip: 1,
	limit: 10,
	username: "",
	nickname: "",
	mobile: "",
	status: undefined,
});

// 分页逻辑
const total = ref(0);
const loading = ref(false);
const userList = ref([]);

const handleQuery = () => {
	loading.value = true;
	getUserList({
		skip: (queryParams.skip - 1) * queryParams.limit,
		limit: queryParams.limit,
		username: queryParams.username || undefined,
		nickname: queryParams.nickname || undefined,
		mobile: queryParams.mobile || undefined,
		status: queryParams.status,
	})
		.then((res) => {
			userList.value = res.items || [];
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
		username: "",
		nickname: "",
		mobile: "",
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

// 新增、编辑对话框
const dialog = reactive({
	visible: false,
	title: "添加用户",
});

const formRef = ref<FormInstance>();
const form = reactive({
	id: undefined,
	username: "",
	nickname: "",
	password: "",
	email: "",
	mobile: "",
	sex: 0,
	status: 0,
	remark: "",
});

const rules = ref<Record<string, FormItemRule[]>>({
	username: [
		{ required: true, message: "请输入用户名", trigger: "blur" },
		{ min: 3, max: 20, message: "长度在 3 到 20 个字符", trigger: "blur" },
	],
	nickname: [
		{ required: true, message: "请输入昵称", trigger: "blur" },
		{ min: 2, max: 20, message: "长度在 2 到 20 个字符", trigger: "blur" },
	],
	password: [
		{ required: true, message: "请输入密码", trigger: "blur" },
		{ min: 6, max: 20, message: "长度在 6 到 20 个字符", trigger: "blur" },
	],
	email: [{ type: "email", message: "请输入正确的邮箱地址", trigger: "blur" }],
	mobile: [{ pattern: /^1[3-9]\d{9}$/, message: "请输入正确的手机号码", trigger: "blur" }],
});

const handleAdd = () => {
	resetForm();
	dialog.title = "添加用户";
	dialog.visible = true;
};

const handleEdit = (row: any) => {
	resetForm();
	dialog.title = "编辑用户";
	getUserDetail(row.id).then((res) => {
		Object.assign(form, res);
		dialog.visible = true;
	});
};

const resetForm = () => {
	form.id = undefined;
	form.username = "";
	form.nickname = "";
	form.password = "";
	form.email = "";
	form.mobile = "";
	form.sex = 0;
	form.status = 0;
	form.remark = "";
	if (formRef.value) {
		formRef.value.resetFields();
	}
};

const submitForm = () => {
	formRef.value?.validate((valid) => {
		if (valid) {
			if (form.id !== undefined) {
				updateUser(form.id, form).then(() => {
					ElMessage.success("修改成功");
					dialog.visible = false;
					handleQuery();
				});
			} else {
				createUser(form).then(() => {
					ElMessage.success("新增成功");
					dialog.visible = false;
					handleQuery();
				});
			}
		}
	});
};

// 删除用户
const handleDelete = (row: any) => {
	ElMessageBox.confirm(`确定要删除用户"${row.username}"吗？`, "警告", {
		confirmButtonText: "确定",
		cancelButtonText: "取消",
		type: "warning",
	})
		.then(() => {
			deleteUser(row.id).then(() => {
				ElMessage.success("删除成功");
				handleQuery();
			});
		})
		.catch(() => {});
};

// 修改用户状态
const handleStatusChange = (row: any) => {
	const text = row.status === 0 ? "启用" : "停用";
	changeUserStatus(row.id, row.status)
		.then(() => {
			ElMessage.success(`${text}成功`);
		})
		.catch(() => {
			row.status = row.status === 0 ? 1 : 0;
		});
};

// 重置密码
const pwdDialog = reactive({
	visible: false,
	userId: 0,
});

const pwdFormRef = ref<FormInstance>();
const pwdForm = reactive({
	password: "",
	confirmPassword: "",
});

const pwdRules = ref<Record<string, FormItemRule[]>>({
	password: [
		{ required: true, message: "请输入新密码", trigger: "blur" },
		{ min: 6, max: 20, message: "长度在 6 到 20 个字符", trigger: "blur" },
	],
	confirmPassword: [
		{ required: true, message: "请确认密码", trigger: "blur" },
		{
			validator: (rule: any, value: string, callback: any) => {
				if (value !== pwdForm.password) {
					callback(new Error("两次输入密码不一致"));
				} else {
					callback();
				}
			},
			trigger: "blur",
		},
	],
});

const handleResetPwd = (row: any) => {
	pwdDialog.userId = row.id;
	pwdForm.password = "";
	pwdForm.confirmPassword = "";
	pwdDialog.visible = true;
	if (pwdFormRef.value) {
		pwdFormRef.value.resetFields();
	}
};

const submitResetPwd = () => {
	pwdFormRef.value?.validate((valid) => {
		if (valid) {
			resetUserPassword(pwdDialog.userId, pwdForm.password).then(() => {
				ElMessage.success("重置密码成功");
				pwdDialog.visible = false;
			});
		}
	});
};

// 分配角色
const roleDialog = reactive({
	visible: false,
	userId: 0,
	username: "",
	roleList: [] as any[],
	checkedRoleIds: [] as number[],
});

const handleAssignRoles = (row: any) => {
	roleDialog.userId = row.id;
	roleDialog.username = row.username;
	roleDialog.checkedRoleIds = [];
	roleDialog.visible = true;
	getUserRoles(row.id).then((res) => {
		roleDialog.roleList = res.roles || [];
		roleDialog.checkedRoleIds = res.roles.filter((role: any) => role.selected).map((role: any) => role.id);
	});
};

const submitRoleAssign = () => {
	assignUserRoles(roleDialog.userId, roleDialog.checkedRoleIds).then(() => {
		ElMessage.success("分配角色成功");
		roleDialog.visible = false;
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
.user-link {
	color: #409eff;
	text-decoration: none;
	font-weight: 500;

	&:hover {
		text-decoration: underline;
		color: #66b1ff;
	}
}
</style>
