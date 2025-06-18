<script setup lang="ts">
import { ref, defineProps, defineEmits, reactive } from "vue";
import { ElMessage, ElMessageBox, FormInstance, type FormRules } from "element-plus";
import { Edit, Delete, Plus, Timer } from "@element-plus/icons-vue";
import { createRelationshipLevel, updateRelationshipLevel, deleteRelationshipLevel } from "@/api/relationship_level";
import AvatarEditor from "@/components/AvatarEditor/AvatarEditor.vue";
import { rolePrompt } from "@/utils/editorButton";

/**
 * Component properties definition
 * @typedef {Object} Props
 * @property {Array} relationshipLevels - Relationship levels list
 * @property {boolean} loading - Loading status
 * @property {string} roleId - Character ID
 */
const props = defineProps<{
	relationshipLevels: any[];
	loading: boolean;
	roleId: string;
}>();

/**
 * Component events definition
 */
const emit = defineEmits<{
	(e: "refresh"): void;
}>();

// Relationship level related
const relationshipLevelDialogVisible = ref(false);
const relationshipLevelDialogType = ref("add"); // Dialog type: add or edit
const currentEditRelationshipLevel = ref(0); // Current editing relationship level ID
const relationshipLevelForm = ref({
	role_id: props.roleId,
	relationship_name: "",
	relationship_level: 1,
	prompt_text: "",
	status: 1,
	created_at: "",
	updated_at: "",
});

/**
 * Add new relationship level
 */
const addNewRelationshipLevel = () => {
	relationshipLevelDialogType.value = "add";
	relationshipLevelForm.value = {
		role_id: props.roleId,
		relationship_name: "",
		relationship_level: 1,
		prompt_text: "",
		status: 1,
		created_at: "",
		updated_at: "",
	};
	relationshipLevelDialogVisible.value = true;
};

/**
 * Edit relationship level
 * @param {Object} relationshipLevel - Relationship level object to edit
 */
const editRelationshipLevel = (relationshipLevel) => {
	relationshipLevelDialogType.value = "edit";
	currentEditRelationshipLevel.value = relationshipLevel.id;
	relationshipLevelForm.value = {
		role_id: relationshipLevel.role_id,
		relationship_name: relationshipLevel.relationship_name,
		relationship_level: relationshipLevel.relationship_level,
		prompt_text: relationshipLevel.prompt_text,
		status: relationshipLevel.status,
		created_at: relationshipLevel.created_at,
		updated_at: relationshipLevel.updated_at,
	};
	relationshipLevelDialogVisible.value = true;
};

/**
 * Delete relationship level
 * @param {Object} relationshipLevel - Relationship level object to delete
 */
const deleteRelationshipLevelItem = (relationshipLevel) => {
	ElMessageBox.confirm("Are you sure you want to delete this relationship level?", "Tip", {
		confirmButtonText: "Confirm",
		cancelButtonText: "Cancel",
		type: "warning",
	})
		.then(async () => {
			try {
				await deleteRelationshipLevel(relationshipLevel.id);
				ElMessage.success("Deleted successfully");
				emit("refresh");
			} catch (error) {
				console.error("Failed to delete relationship level", error);
				ElMessage.error("Failed to delete relationship level");
			}
		})
		.catch(() => {
			// Cancel operation
		});
};

/**
 * Submit relationship level form
 */
const submitRelationshipLevel = async (formEl: FormInstance | undefined) => {
	if (!relationshipLevelForm.value.relationship_name) {
		ElMessage.warning("Please enter relationship name");
		return;
	}

	if (!formEl) return;
	await formEl.validate(async (valid, fields) => {
		if (valid) {
			try {
				if (relationshipLevelDialogType.value === "add") {
					await createRelationshipLevel(relationshipLevelForm.value);
					ElMessage.success("Relationship level added successfully");
				} else {
					await updateRelationshipLevel(currentEditRelationshipLevel.value, relationshipLevelForm.value);
					ElMessage.success("Relationship level updated successfully");
				}
				relationshipLevelDialogVisible.value = false;
				emit("refresh");
			} catch (error) {
				console.error(relationshipLevelDialogType.value === "add" ? "Failed to add relationship level" : "Failed to update relationship level", error);
				ElMessage.error(relationshipLevelDialogType.value === "add" ? "Failed to add relationship level" : "Failed to update relationship level");
			}
		} else {
			console.log("error submit!", fields);
		}
	});
};

const ruleFormRef = ref<FormInstance>();
const formRules = reactive<FormRules>({
	relationship_name: [
		{ required: true, message: "Please enter relationship name", trigger: "blur" },
		{ min: 1, max: 10, message: "Length should be between 1 and 10 characters", trigger: "blur" },
	],
	prompt_text: [
		{ required: true, message: "Please enter relationship prompt", trigger: "blur" },
		{ min: 2, max: 1000, message: "Length should be between 1 and 1000 characters", trigger: "blur" },
	],
});
</script>

<template>
	<div class="relationship-section">
		<div class="section-toolbar">
			<el-button class="btn-fix" type="primary" size="small" @click="addNewRelationshipLevel">
				<el-icon>
					<Plus />
				</el-icon>
				Add Relationship
			</el-button>
		</div>
		<div class="relationship-level-list" v-loading="loading">
			<el-empty v-if="relationshipLevels.length === 0" description="No relationship levels yet" />
			<div class="relationship-level-grid" v-else>
				<el-card v-for="item in relationshipLevels" :key="item.id" class="relationship-level-card" shadow="hover">
					<div class="relationship-level-header">
						<div class="relationship-level-name">{{ item.relationship_name }}</div>
						<el-tag :type="item.status === 1 ? 'success' : 'danger'">
							{{ item.status === 1 ? "Enabled" : "Disabled" }}
						</el-tag>
					</div>
					<div class="relationship-level-info">
						<div class="relationship-level-level">Level: {{ item.relationship_level }}</div>
					</div>
					<div class="relationship-level-preview">
						{{ item.prompt_text }}
					</div>
					<div class="relationship-level-card-footer">
						<div class="relationship-level-update-time">
							<el-icon>
								<Timer />
							</el-icon>
							<span>Updated: {{ new Date(item.updated_time).toLocaleString() }}</span>
						</div>
						<div class="relationship-level-actions">
							<el-button class="btn-fix" type="primary" link @click="editRelationshipLevel(item)">
								<el-icon>
									<Edit />
								</el-icon>
								Try out
							</el-button>
							<el-button type="danger" link @click="deleteRelationshipLevelItem(item)">
								<el-icon>
									<Delete />
								</el-icon>
								Delete
							</el-button>
						</div>
					</div>
				</el-card>
			</div>
		</div>

		<!-- Add/Edit relationship level dialog -->
		<el-dialog
			v-model="relationshipLevelDialogVisible"
			:title="relationshipLevelDialogType === 'add' ? 'Add Character Relationship Level' : 'Edit Character Relationship Level'"
			width="50%"
		>
			<div class="relationship-level-dialog-content">
				<div class="relationship-level-form-container">
					<el-form :model="relationshipLevelForm" label-width="130px" :rules="formRules" ref="ruleFormRef">
						<FormItem label="Relationship Name" prop="relationship_name" tooltipKey="relationship_name">
							<el-input v-model="relationshipLevelForm.relationship_name" placeholder="Please enter relationship name" />
						</FormItem>
						<FormItem label="Relationship Level" tooltipKey="relationship_level">
							<el-input-number v-model="relationshipLevelForm.relationship_level" :min="0" :max="10" />
						</FormItem>
						<FormItem label="Relationship Prompt" prop="prompt_text" tooltipKey="relationshipLevelForm">
							<AvatarEditor
								:users="rolePrompt"
								:max-length="3000"
								:min-length="10"
								placeholder="Please enter relationship temperature prompt..."
								v-model="relationshipLevelForm.prompt_text"
							/>
						</FormItem>
						<FormItem label="Status" tooltipKey="status">
							<el-switch v-model="relationshipLevelForm.status" :active-value="1" :inactive-value="0" />
						</FormItem>
					</el-form>
				</div>
			</div>
			<template #footer>
				<span class="dialog-footer">
					<el-button @click="relationshipLevelDialogVisible = false">Cancel</el-button>
					<el-button type="primary" @click="submitRelationshipLevel(ruleFormRef)">Confirm</el-button>
				</span>
			</template>
		</el-dialog>
	</div>
</template>

<style scoped lang="scss">
.relationship-section {
	padding: 0;
}

.section-toolbar {
	display: flex;
	justify-content: flex-end;
	align-items: center;
	margin-bottom: 20px;
	padding: 0 4px;
}

/* Relationship level card styles */
.relationship-level-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
	gap: 16px;
	margin-bottom: 20px;
}

.relationship-level-card {
	position: relative;
	background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
	border: 1px solid #e2e8f0;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	transition: all 0.3s ease;
	height: 280px;
	overflow: hidden;
}

.relationship-level-card:hover {
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
	border-color: #2563eb;
}

.relationship-level-header {
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
	margin-bottom: 15px;
}

.relationship-level-name {
	font-size: 16px;
	font-weight: 600;
	color: #1e293b;
	margin: 0;
	line-height: 1.4;
}

.relationship-level-info {
	display: flex;
	gap: 12px;
	margin-bottom: 12px;
	font-size: 12px;
	color: #64748b;
}

.relationship-level-level {
	font-size: 12px;
	color: #64748b;
}

.relationship-level-preview {
	background: #f8fafc;
	border-radius: 6px;
	padding: 12px;
	margin-bottom: 12px;
	font-size: 14px;
	line-height: 1.5;
	color: #64748b;
	height: 90px;
	overflow: hidden;
	position: relative;
	border: 1px solid #e2e8f0;
}

.relationship-level-preview::after {
	content: "";
	position: absolute;
	bottom: 0;
	left: 0;
	right: 0;
	height: 30px;
	background: linear-gradient(transparent, #f8fafc);
}

.relationship-level-card-footer {
	position: absolute;
	bottom: 12px;
	left: 20px;
	right: 20px;
	display: flex;
	justify-content: space-between;
	align-items: center;
	background: rgba(255, 255, 255, 0.9);
	padding: 8px 0;
}

.relationship-level-update-time {
	display: flex;
	align-items: center;
	gap: 5px;
	font-size: 12px;
	color: #64748b;
}

.relationship-level-actions {
	display: flex;
	gap: 10px;
}

.relationship-level-dialog-content {
	display: flex;
	gap: 20px;
}

.relationship-level-form-container {
	flex: 1;
}

@import '@/layouts/WriterLayout/css/extra.scss';
.btn-fix {
	color: #fff;
	background-color: $btn-bg-color0;
	border-color: $btn-bg-color0;
}
</style>
