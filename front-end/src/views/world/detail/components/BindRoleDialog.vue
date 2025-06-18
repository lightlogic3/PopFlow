<!-- BindRoleDialog.vue - Bind role dialog component -->
<script setup lang="ts">
import { ref, watch } from "vue";

interface Role {
	id: string;
	role_id: string;
	name: string;
	avatar?: string;
}

/**
 * Component props interface
 */
interface Props {
	visible: boolean;
	allRolesList: Role[];
	allRolesLoading: boolean;
	allRolesTotal: number;
	allRolesCurrentPage: number;
	allRolesPageSize: number;
}

const props = defineProps<Props>();

/**
 * Define component emitted events
 */
const emit = defineEmits<{
	"update:visible": [value: boolean];
	confirm: [roleIds: string[]];
	search: [keyword: string];
	pageChange: [page: number];
}>();

/**
 * Selected role IDs list
 */
const selectedRoleIds = ref<string[]>([]);

/**
 * Watch dialog display status, reset selected status
 */
watch(
	() => props.visible,
	(newVal) => {
		if (newVal) {
			selectedRoleIds.value = [];
		}
	},
);

/**
 * Search roles
 * @param {string} query - Search keyword
 */
const searchRoles = (query: string) => {
	emit("search", query);
};

/**
 * Bind roles
 */
const bindRoles = () => {
	emit("confirm", selectedRoleIds.value);
};

/**
 * Close dialog
 */
const closeDialog = () => {
	emit("update:visible", false);
};

/**
 * Page change handler
 * @param {number} page - New page number
 */
const handlePageChange = (page: number) => {
	emit("pageChange", page);
};

/**
 * Dialog open and close event handler
 */
const handleDialogChange = (val: boolean) => {
	emit("update:visible", val);
};
</script>

<template>
	<el-dialog :modelValue="visible" @update:model-value="handleDialogChange" title="Bind Roles to Knowledge Point" width="50%">
		<div v-loading="allRolesLoading">
			<el-form>
				<FormItem label="Select Roles" tooltipKey="selectedRoleIds">
					<el-select
						v-model="selectedRoleIds"
						multiple
						filterable
						remote
						reserve-keyword
						placeholder="Please enter role name to search"
						:remote-method="searchRoles"
						:loading="allRolesLoading"
						style="width: 100%"
					>
						<el-option
							v-for="role in allRolesList"
							:key="role.id"
							:label="`${role.name}(${role.role_id})`"
							:value="role.role_id"
						>
							<div class="role-option">
								<div class="role-option-info">
									<div class="role-option-name">{{ `${role.name}(${role.role_id})` }}</div>
								</div>
							</div>
						</el-option>
					</el-select>
				</FormItem>
			</el-form>

			<!-- Pagination -->
			<div class="pagination-container" v-if="allRolesTotal > allRolesPageSize">
				<el-pagination
					:current-page="allRolesCurrentPage"
					:page-size="allRolesPageSize"
					layout="prev, pager, next"
					:total="allRolesTotal"
					@current-change="handlePageChange"
					background
				/>
			</div>
		</div>
		<template #footer>
			<span class="dialog-footer">
				<el-button @click="closeDialog">Cancel</el-button>
				<el-button type="primary" @click="bindRoles">Confirm Binding</el-button>
			</span>
		</template>
	</el-dialog>
</template>

<style scoped>
.pagination-container {
	margin-top: 20px;
	display: flex;
	justify-content: center;
}

/* Role option style */
.role-option {
	display: flex;
	align-items: center;
	padding: 5px 0;
}

.role-option-info {
	display: flex;
	flex-direction: column;
}

.role-option-name {
	font-size: 14px;
	color: var(--el-text-color-primary);
}
</style>
