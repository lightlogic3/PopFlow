<template>
	<div class="game-play-type-detail">
		<div class="main-content">
			<div class="header">
				<h1 class="title">
					{{ isCreateMode ? "Create Game Play Type" : isEditMode ? "Edit Game Play Type" : "Game Play Type Details" }}
				</h1>
				<div class="subtitle">
					{{ isCreateMode ? "Design new game play configuration" : isEditMode ? "Modify existing game play" : "View play details" }}
				</div>
			</div>

			<div class="nav-actions">
				<el-button class="back-btn" @click="goBack">
					<el-icon><ArrowLeft /></el-icon>
					Back to List
				</el-button>
				<template v-if="!isCreateMode && !isEditMode">
					<el-button type="primary" class="save-btn" @click="handleEdit">
						<el-icon><Edit /></el-icon>
						Edit
					</el-button>
					<el-button type="danger" class="delete-btn" @click="handleDelete">
						<el-icon><Delete /></el-icon>
						Delete
					</el-button>
				</template>
				<template v-else>
					<el-button type="primary" class="save-btn" @click="handleSave" :loading="saving">
						<el-icon><Check /></el-icon>
						Save
					</el-button>
					<el-button v-if="isEditMode" class="reset-btn" @click="resetForm">
						<el-icon><RefreshRight /></el-icon>
						Reset
					</el-button>
				</template>
			</div>

			<div v-loading="loading" class="content">
				<template v-if="!isCreateMode && !isEditMode">
					<!-- Detail View -->
					<div class="form-section">
						<h2 class="section-title">Basic Information</h2>
						<el-descriptions :column="1" border>
							<el-descriptions-item label="ID">{{ typeData.id }}</el-descriptions-item>
							<el-descriptions-item label="Game Name">{{ typeData.name }}</el-descriptions-item>
							<el-descriptions-item label="Game Type Code">{{ typeData.game_play_type }}</el-descriptions-item>
							<el-descriptions-item label="Description">{{ typeData.description }}</el-descriptions-item>
							<el-descriptions-item label="Game Setting">{{ typeData.setting }}</el-descriptions-item>
							<el-descriptions-item label="Reference Case">{{ typeData.reference_case }}</el-descriptions-item>
							<el-descriptions-item label="Version">{{ typeData.version }}</el-descriptions-item>
							<el-descriptions-item label="Number of Players"
								>{{ typeData.game_number_min }}-{{ typeData.game_number_max }}</el-descriptions-item
							>
							<el-descriptions-item label="Status">{{ typeData.status === 1 ? "Enabled" : "Disabled" }}</el-descriptions-item>
							<el-descriptions-item label="Additional Content">{{ typeData.additional_content }}</el-descriptions-item>
							<el-descriptions-item label="Created At">{{ formatDate(typeData.created_at) }}</el-descriptions-item>
							<el-descriptions-item label="Updated At">{{ formatDate(typeData.updated_at) }}</el-descriptions-item>
						</el-descriptions>
					</div>

					<!-- Character Relationship Information -->
					<div class="form-section role-section">
						<h2 class="section-title">Character Relationships</h2>
						<div v-if="roleRelations.length > 0" class="role-list">
							<div v-for="(role, index) in roleRelations" :key="index" class="role-item">
								<div class="role-avatar" v-if="!role.image_url">
									{{ getRoleInitial(role.role_name || role.role_id) }}
								</div>
								<div class="role-avatar-img" v-else>
									<img :src="role.image_url" :alt="role.role_name || role.role_id" />
								</div>
								<div class="role-info">
									<div class="role-name">{{ role.role_name || role.role_id }}</div>
									<div class="role-model" v-if="role.llm_provider">Provider: {{ role.llm_provider }}</div>
									<div class="role-model" v-if="role.llm_model">Model: {{ role.llm_model }}</div>
									<div class="role-voice" v-if="role.voice">Voice: {{ role.voice }}</div>
								</div>
							</div>
						</div>
						<div v-else class="empty-roles">
							<el-empty description="No related characters" />
						</div>
					</div>

					<!-- Game Play Configuration Preview -->
					<div class="form-section schema-section">
						<h2 class="section-title">Gameplay Configuration Schema</h2>
						<el-tabs v-model="previewActiveTab" :lazy="true">
							<el-tab-pane label="Form Preview" name="form-preview">
								<dynamic-form
									:schema="typeData.form_schema"
									:uiSchema="typeData.ui_schema || defaultUiSchema"
									:validationSchema="typeData.validation_schema || {}"
									:formData="{}"
									:readOnly="true"
									lazy="true"
								/>
							</el-tab-pane>
							<el-tab-pane label="Schema Data" name="schema-data">
								<el-card>
									<json-viewer :value="typeData.form_schema" copyable boxed sort theme="jv-light" />
								</el-card>
							</el-tab-pane>
							<el-tab-pane label="UI Schema" name="ui-schema">
								<el-card>
									<json-viewer :value="typeData.ui_schema || defaultUiSchema" copyable boxed sort theme="jv-light" />
								</el-card>
							</el-tab-pane>
							<el-tab-pane label="Validation Rules" name="validation-schema">
								<el-card>
									<json-viewer :value="typeData.validation_schema || {}" copyable boxed sort theme="jv-light" />
								</el-card>
							</el-tab-pane>
						</el-tabs>
					</div>
				</template>

				<template v-else>
					<!-- Edit/Create Form -->
					<el-form ref="formRef" :model="form" :rules="rules" label-width="120px" class="type-form">
						<div class="form-section">
							<h2 class="section-title">Basic Information</h2>
							<div class="form-grid">
								<el-form-item label="Game Name" prop="name" class="form-item-highlight">
									<el-input v-model="form.name" placeholder="Please enter game name" />
								</el-form-item>

								<el-form-item label="Game Type Code" prop="game_play_type" class="form-item-highlight">
									<el-input v-model="form.game_play_type" placeholder="Please enter game type code" />
								</el-form-item>

								<el-form-item label="Description" prop="description" class="form-item-highlight">
									<el-input v-model="form.description" type="textarea" :rows="3" placeholder="Please enter description" />
								</el-form-item>

								<el-form-item label="Game Setting" prop="setting" class="form-item-highlight">
									<el-input v-model="form.setting" type="textarea" :rows="3" placeholder="Please enter game setting" />
								</el-form-item>

								<el-form-item label="Reference Case" prop="reference_case" class="form-item-highlight">
									<el-input v-model="form.reference_case" type="textarea" :rows="3" placeholder="Please enter reference case" />
								</el-form-item>

								<el-form-item label="Number of Players" prop="game_number" class="form-item-highlight">
									<div class="game-number-setting">
										<el-input-number
											v-model="form.game_number_min"
											:min="1"
											:max="form.game_number_max || 100"
											placeholder="Min players"
											size="default"
											class="number-input"
										/>
										<span class="range-separator">to</span>
										<el-input-number
											v-model="form.game_number_max"
											:min="form.game_number_min || 1"
											:max="100"
											placeholder="Max players"
											size="default"
											class="number-input"
										/>
										<span class="range-unit">players</span>
									</div>
								</el-form-item>

								<el-form-item label="Status" prop="status" class="form-item-highlight">
									<el-radio-group v-model="form.status">
										<el-radio :label="1">Enabled</el-radio>
										<el-radio :label="0">Disabled</el-radio>
									</el-radio-group>
								</el-form-item>
							</div>
						</div>

						<div v-if="isCreateMode" class="form-section">
							<h2 class="section-title">Template Selection</h2>
							<p class="section-desc">Choose a preset template to start quickly, or use a blank template for custom design</p>

							<div class="template-options">
								<div
									v-for="template in templates"
									:key="template.value"
									class="template-card"
									:class="{ selected: selectedTemplate === template.value }"
									@click="applyTemplate(template.value)"
								>
									<div class="template-name">{{ template.label }}</div>
									<div class="template-desc">{{ template.description }}</div>
								</div>
							</div>
						</div>

						<!-- Advanced Settings Collapse Panel -->
						<el-divider content-position="center">Advanced Settings</el-divider>
						<el-collapse v-model="activeCollapse">
							<el-collapse-item title="Advanced Configuration Options" name="advanced">
								<el-form-item label="Version" prop="version">
									<el-input v-model="form.version" placeholder="Please enter version number, e.g.: 1.0.0" />
								</el-form-item>

								<el-form-item label="Additional Content" prop="additional_content_json">
									<div class="additional-content-editor">
										<div v-for="(item, index) in additionalContentItems" :key="index" class="content-item">
											<div class="item-header">
												<el-input
													v-model="item.displayName"
													placeholder="Display name"
													class="display-name-input"
													@input="updateAdditionalContent"
												/>
												<el-input
													v-model="item.key"
													placeholder="Key name (English)"
													class="key-input"
													@input="updateAdditionalContent"
												/>
												<el-select
													v-model="item.type"
													placeholder="Type"
													class="display-name-input"
													@change="updateAdditionalContent"
												>
													<el-option label="Text" value="text" />
													<el-option label="Model" value="model" />
												</el-select>
												<el-button
													type="danger"
													size="small"
													circle
													@click="removeAdditionalContentItem(index)"
													class="remove-btn"
												>
													<el-icon><Delete /></el-icon>
												</el-button>
											</div>
											<div v-if="item.type === 'model'">
												<ModelCascader
													v-model="item.value"
													style="width: 100%"
													class="model-task"
													@change="updateAdditionalContent"
												/>
											</div>
											<div v-else>
												<el-input
													v-model="item.value"
													type="textarea"
													:rows="3"
													placeholder="Value"
													class="value-input"
													@input="updateAdditionalContent"
												/>
											</div>
										</div>
										<div class="add-item">
											<el-button type="primary" @click="addAdditionalContentItem">
												<el-icon><Plus /></el-icon> Add Configuration Item
											</el-button>
										</div>
										<div class="json-preview">
											<el-collapse>
												<el-collapse-item title="JSON Preview" name="json-preview">
													<pre>{{
														JSON.stringify(
															form.additional_content_json ? JSON.parse(form.additional_content_json) : {},
															null,
															2,
														)
													}}</pre>
												</el-collapse-item>
											</el-collapse>
										</div>
									</div>
									<div v-if="additionalContentError" class="error-message">
										<el-alert :title="additionalContentError" type="error" :closable="false" />
									</div>
								</el-form-item>

								<el-form-item label="Configuration Schema" prop="form_schema">
									<schema-editor
										v-model:schema="form.form_schema"
										v-model:uiSchema="form.ui_schema"
										v-model:validationSchema="form.validation_schema"
										@schema-error="handleSchemaError"
										lazy="true"
									/>
									<div v-if="schemaError" class="schema-error">
										<el-alert :title="schemaError" type="error" :closable="false" />
									</div>
								</el-form-item>
							</el-collapse-item>
						</el-collapse>

						<!-- Character Relationship Section -->
						<div class="form-section role-section">
							<h2 class="section-title">Character Relationships</h2>
							<p class="section-desc">Associate characters with this game play type. You can add multiple characters and set character properties</p>

							<div class="role-list">
								<div v-for="(role, index) in roleRelations" :key="index" class="role-item">
									<div class="role-actions">
										<el-button type="primary" circle size="small" class="edit-role-btn" @click="editRoleSettings(role)">
											<el-icon><Setting /></el-icon>
										</el-button>
										<el-button type="danger" circle size="small" class="delete-role-btn" @click="removeRole(index)">
											<el-icon><Delete /></el-icon>
										</el-button>
									</div>

									<div class="role-avatar" v-if="!role.image_url">
										{{ getRoleInitial(role.role_name || role.role_id) }}
									</div>
									<div class="role-avatar-img" v-else>
										<img :src="role.image_url" alt="Character Avatar" />
									</div>
									<div class="role-info">
										<div class="role-name">{{ role.role_name || role.role_id }}</div>
										<div class="role-model" v-if="role.llm_provider">Provider: {{ role.llm_provider }}</div>
										<div class="role-model" v-if="role.llm_model">Model: {{ role.llm_model }}</div>
										<div class="role-voice" v-if="role.voice">Voice: {{ role.voice }}</div>
									</div>
								</div>

								<div class="add-role" @click="showRoleSelector = true">
									<el-icon><Plus /></el-icon>
									<span>Add Character</span>
								</div>
							</div>
						</div>
					</el-form>
				</template>
			</div>
		</div>

		<!-- Delete Confirmation Dialog -->
		<el-dialog v-model="deleteDialogVisible" title="Delete Confirmation" width="30%" destroy-on-close>
			<span>Are you sure you want to delete the game type "{{ typeData.name }}"? This action cannot be undone!</span>
			<template #footer>
				<span class="dialog-footer">
					<el-button @click="deleteDialogVisible = false">Cancel</el-button>
					<el-button type="danger" @click="confirmDelete">Confirm Delete</el-button>
				</span>
			</template>
		</el-dialog>

		<!-- Character Selection Dialog -->
		<el-dialog v-model="showRoleSelector" title="Add Character" width="600px" class="role-dialog">
			<div class="role-selector">
				<el-form>
					<el-form-item label="Select Characters">
						<el-select
							v-model="selectedRoleIds"
							placeholder="Please select characters (multiple selection available)"
							filterable
							multiple
							collapse-tags
							collapse-tags-tooltip
							style="width: 100%"
						>
							<el-option
								v-for="role in filteredAvailableRoles"
								:key="role.role_id"
								:label="role.name"
								:value="role.role_id"
							>
								<div class="role-option">
									<div class="role-option-avatar" v-if="!role.image_url">
										{{ getRoleInitial(role.name) }}
									</div>
									<div class="role-option-avatar-img" v-else>
										<img :src="role.image_url" alt="Character Avatar" />
									</div>
									<div class="role-option-info">
										<div class="role-option-name">{{ role.name }}</div>
										<div class="role-option-desc">{{ role.tags || "No tags" }}</div>
									</div>
								</div>
							</el-option>
						</el-select>
					</el-form-item>
				</el-form>

				<!-- Selected Characters List -->
				<div class="selected-roles-container" v-if="selectedRoleIds.length > 0">
					<h4 class="selected-roles-title">Selected Characters</h4>
					<div class="selected-roles-list">
						<div v-for="roleId in selectedRoleIds" :key="roleId" class="selected-role-item">
							<template v-if="getRoleById(roleId)">
								<div class="role-avatar" v-if="!getRoleById(roleId).image_url">
									{{ getRoleInitial(getRoleById(roleId).name) }}
								</div>
								<div class="role-avatar-img" v-else>
									<img :src="getRoleById(roleId).image_url" alt="Character Avatar" />
								</div>
								<div class="role-name">{{ getRoleById(roleId).name }}</div>
								<div class="role-remove" @click.stop="removeSelectedRole(roleId)">
									<el-icon><Delete /></el-icon>
								</div>
							</template>
						</div>
					</div>
				</div>
			</div>
			<template #footer>
				<div class="dialog-footer">
					<el-button @click="showRoleSelector = false">Cancel</el-button>
					<el-button type="primary" @click="addSelectedRoles" :disabled="selectedRoleIds.length === 0">
						Add ({{ selectedRoleIds.length }})
					</el-button>
				</div>
			</template>
		</el-dialog>

		<!-- Character Settings Dialog -->
		<el-dialog v-model="showRoleSettings" title="Character Settings" width="600px" class="role-dialog">
			<div class="role-settings" v-if="currentRole">
				<div class="role-header">
					<div class="role-avatar-large" v-if="!currentRole.image_url">
						{{ getRoleInitial(currentRole.role_name || currentRole.role_id) }}
					</div>
					<div class="role-avatar-img-large" v-else>
						<img :src="currentRole.image_url" alt="Character Avatar" />
					</div>
					<div class="role-title">{{ currentRole.role_name || currentRole.role_id }}</div>
				</div>

				<el-form :model="roleSettings" label-position="top">
					<el-form-item label="Language Model">
						<ModelCascader v-model="roleSettings.llm_model" style="width: 100%" />
					</el-form-item>

					<el-form-item label="Voice Settings">
						<el-select v-model="roleSettings.voice" placeholder="Select voice" filterable clearable style="width: 100%">
							<el-option v-for="voice in voices" :key="voice.speaker_id" :label="voice.alias" :value="voice.speaker_id">
								<div class="option-with-detail">
									<div class="option-name">{{ voice.alias }}</div>
									<div class="option-detail">{{ voice.speaker_id }}</div>
									<div class="option-action" v-if="voice.audition">
										<el-button size="small" @click.stop="playVoice(voice.audition)">Listen</el-button>
									</div>
								</div>
							</el-option>
						</el-select>
					</el-form-item>

					<el-form-item label="Character Settings">
						<el-input
							v-model="roleSettings.character_setting"
							type="textarea"
							:rows="4"
							placeholder="Enter character's special settings..."
						/>
					</el-form-item>
				</el-form>
			</div>
			<template #footer>
				<div class="dialog-footer">
					<el-button @click="showRoleSettings = false">Cancel</el-button>
					<el-button type="primary" @click="saveRoleSettings" :loading="savingRoleSettings">Save</el-button>
				</div>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick, reactive } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElForm } from "element-plus";
import {
	getGamePlayType,
	createGamePlayType,
	updateGamePlayType,
	deleteGamePlayType,
	getGameRelations,
	updateGameRelations,
} from "@/api/gamePlayType";
import { getRoleList } from "@/api/role";
import { getActiveLLMProviders } from "@/api/llm";
import { listAudioTimbres } from "@/api/audio-timbre";
import type { GamePlayType } from "@/api/gamePlayType";
import SchemaEditor from "./components/SchemaEditor.vue";
import DynamicForm from "@/components/DynamicForm.vue";
import { ArrowLeft, Edit, Delete, Check, RefreshRight, Plus, Setting } from "@element-plus/icons-vue";

// Import styles directly to ensure they are correctly applied
import "@/assets/css/GamePlayTypeDetail.scss";
import ModelCascader from "@/components/ModelCascader.vue";
import { Role } from "@/types/role";

// Extending GamePlayType type with UI Schema and validation Schema fields
// This is a temporary extension, the type definition should actually be modified in api/gamePlayType.ts
interface ExtendedGamePlayType extends GamePlayType {
	ui_schema?: Record<string, any>;
	validation_schema?: Record<string, any>;
	setting?: string;
	reference_case?: string;
	version?: string;
	status?: number;
	additional_content?: any;
	game_number_max?: number;
	game_number_min?: number;
	game_play_type: string;
	role_relations: any;
}

// Route related
const route = useRoute();
const router = useRouter();
const typeId = computed(() => route.params.id as string);
const isCreateMode = computed(() => route.path.includes("/create"));
const isEditMode = computed(() => route.path.includes("/edit"));

// Form reference
const formRef = ref<InstanceType<typeof ElForm> | null>(null);

// Data loading status
const loading = ref(false);
const saving = ref(false);
const deleteDialogVisible = ref(false);

// Tab control
const previewActiveTab = ref("form-preview");
const activeCollapse = ref([]);

// Type data
const typeData = ref<ExtendedGamePlayType>({
	id: "",
	name: "",
	description: "",
	setting: "",
	reference_case: "",
	version: "",
	player_count: "",
	status: 1,
	additional_content: null,
	form_schema: {},
	ui_schema: {},
	validation_schema: {},
	created_at: "",
	updated_at: "",
	game_number_max: 2,
	game_number_min: 1,
	game_play_type: "",
	role_relations: [], // Character relationship list
});

// Additional content editor related data
const additionalContentItems = ref<Array<{ displayName: string; key: string; value: string; type: string }>>([]);

// Character relationship related data
const roleRelations = ref([]);
const availableRoles = ref([]);
const showRoleSelector = ref(false);
const showRoleSettings = ref(false);
const selectedRoleIds = ref([]);
const currentRole = ref(null);
const savingRoleSettings = ref(false);
const llmModels = ref([]);
const voices = ref([]);

// Pagination for available roles
const availableRolesPage = ref(1);
const availableRolesPageSize = ref(100); // Assuming a large limit for a selector
const availableRolesTotal = ref(0);

// Character settings
const roleSettings = reactive({
	relation_id: null,
	llm_provider: null,
	llm_model: null,
	voice: null,
	character_setting: null,
});

// Form data
const form = ref({
	name: "",
	description: "",
	setting: "",
	reference_case: "",
	version: "",
	status: 1,
	additional_content: null,
	additional_content_json: "{}",
	form_schema: {
		title: "",
		description: "",
		components: [],
	},
	ui_schema: {
		layout: "tabs",
		theme: "light",
		cssClasses: {
			formContainer: "game-form-container",
			section: "game-form-section",
			field: "game-form-field",
		},
		conditionalDisplay: [],
	},
	validation_schema: {},
	game_number_max: 2,
	game_number_min: 1,
	game_play_type: "",
	role_relations: [], // Character relationship list
});

// Default UI Schema
const defaultUiSchema = {
	layout: "tabs",
	theme: "dark",
	cssClasses: {
		formContainer: "game-form-container",
		section: "game-form-section",
		field: "game-form-field",
	},
	conditionalDisplay: [],
};

// Form validation rules
const rules = {
	name: [
		{ required: true, message: "Please enter game name", trigger: "blur" },
		{ min: 2, max: 50, message: "Length should be 2-50 characters", trigger: "blur" },
	],
	/**
	 * Game type code validation rules
	 * @description Game type unique identifier, can only contain lowercase letters, numbers and underscores
	 * @required Required field
	 * @min Minimum 2 characters
	 * @max Maximum 50 characters
	 * @pattern Regular expression restricting character types
	 */
	game_play_type: [
		{ required: true, message: "Please enter game type code", trigger: "blur" },
		{ min: 2, max: 50, message: "Length should be 2-50 characters", trigger: "blur" },
		{ pattern: /^[a-z0-9_]+$/, message: "Only lowercase letters, numbers, and underscores are allowed", trigger: "blur" },
	],
	description: [{ max: 200, message: "Length should not exceed 200 characters", trigger: "blur" }],
	setting: [{ max: 500, message: "Length should not exceed 500 characters", trigger: "blur" }],
	reference_case: [{ max: 300, message: "Length should not exceed 300 characters", trigger: "blur" }],
	version: [{ pattern: /^\d+\.\d+\.\d+$/, message: "Version number format should be x.y.z", trigger: "blur" }],
	player_count: [{ max: 50, message: "Length should not exceed 50 characters", trigger: "blur" }],
	status: [{ required: true, message: "Please select status", trigger: "change" }],
	additional_content_json: [
		{
			validator: (rule, value, callback) => {
				if (!value || value.trim() === "") {
					callback();
					return;
				}
				try {
					JSON.parse(value);
					callback();
				} catch (error) {
					callback(new Error("JSON format error"));
				}
			},
			trigger: "blur",
		},
	],
};

// Schema editor related
const schemaJson = ref("{}");
const uiSchemaJson = ref("{}");
const validationSchemaJson = ref("{}");
const schemaError = ref("");

// Template selection
const selectedTemplate = ref<"empty" | "werewolf" | "mahjong">("empty");
const templates = [
	{
		label: "Blank Template",
		value: "empty",
		description: "Start creating a custom game play from scratch",
	},
	{
		label: "Werewolf",
		value: "werewolf",
		description: "Traditional werewolf game configuration, including roles and special skills",
	},
	{
		label: "Mahjong",
		value: "mahjong",
		description: "Standard mahjong game configuration, including rules and scoring",
	},
];

const additionalContentError = ref("");

/**
 * Format date
 */
function formatDate(date: string) {
	if (!date) return "";
	return new Date(date).toLocaleString();
}

/**
 * Return to list page
 */
function goBack() {
	router.push("/game/play/list");
}

/**
 * Load game play type data
 */
async function loadTypeData() {
	if (isCreateMode.value) return;

	loading.value = true;
	try {
		const res = await getGamePlayType(typeId.value);
		typeData.value = res;
		// Initialize form data
		if (isEditMode.value) {
			resetForm();
		}
	} catch (error) {
		console.error("Failed to load game type data", error);
		ElMessage.error("Failed to load game type data");
		router.push("/game/play/list");
	} finally {
		loading.value = false;
	}
}

/**
 * Reset form
 */
function resetForm() {
	console.log("Reset form - original data:", JSON.stringify(typeData.value, null, 2));

	form.value.name = typeData.value.name;
	form.value.description = typeData.value.description || "";
	form.value.setting = typeData.value.setting || "";
	form.value.reference_case = typeData.value.reference_case || "";
	form.value.version = typeData.value.version || "";
	form.value.status = typeData.value.status ?? 1;
	form.value.game_number_max = typeData.value.game_number_max ?? 2;
	form.value.game_number_min = typeData.value.game_number_min ?? 1;
	form.value.additional_content = typeData.value.additional_content;
	form.value.additional_content_json = typeData.value.additional_content
		? JSON.stringify(typeData.value.additional_content, null, 2)
		: "{}";
	form.value.game_play_type = typeData.value.game_play_type;

	// Parse additional content to visual editor
	parseAdditionalContent();

	// Ensure form_schema has valid structure
	const formSchema = typeData.value.form_schema || { title: "", description: "", components: [] };
	if (!formSchema.components) {
		formSchema.components = [];
	}

	form.value.form_schema = JSON.parse(JSON.stringify(formSchema));
	form.value.ui_schema = JSON.parse(JSON.stringify(typeData.value.ui_schema || defaultUiSchema));
	form.value.validation_schema = JSON.parse(JSON.stringify(typeData.value.validation_schema || {}));

	// Reset character relationship data
	roleRelations.value = [];
	loadRoleRelations();

	console.log("Reset form - set after:", {
		form_schema: form.value.form_schema,
		ui_schema: form.value.ui_schema,
		validation_schema: form.value.validation_schema,
	});

	// Update JSON editor
	updateJsonFromSchema();
	updateJsonFromUiSchema();
	updateJsonFromValidationSchema();
}

/**
 * Switch to edit mode
 */
function handleEdit() {
	router.push(`/game-play-types/${typeId.value}/edit`);
}

/**
 * Handle delete
 */
function handleDelete() {
	deleteDialogVisible.value = true;
}

/**
 * Confirm deletion
 */
async function confirmDelete() {
	try {
		await deleteGamePlayType(typeId.value);
		ElMessage.success("Delete successful");
		deleteDialogVisible.value = false;
		router.push("/game/play/list");
	} catch (error) {
		console.error("Delete failed", error);
		ElMessage.error("Delete failed");
	}
}

/**
 * Handle Schema editor errors
 */
function handleSchemaError(error: string) {
	schemaError.value = error;
}

/**
 * Update JSON from Schema object
 */
function updateJsonFromSchema() {
	try {
		schemaJson.value = JSON.stringify(form.value.form_schema, null, 2);
		schemaError.value = "";
	} catch (error) {
		schemaError.value = "Failed to serialize form structure JSON: " + (error as Error).message;
	}
}

/**
 * Update JSON from UI Schema object
 */
function updateJsonFromUiSchema() {
	try {
		uiSchemaJson.value = JSON.stringify(form.value.ui_schema, null, 2);
		schemaError.value = "";
	} catch (error) {
		schemaError.value = "Failed to serialize UI configuration JSON: " + (error as Error).message;
	}
}

/**
 * Update JSON from validation Schema object
 */
function updateJsonFromValidationSchema() {
	try {
		validationSchemaJson.value = JSON.stringify(form.value.validation_schema, null, 2);
		schemaError.value = "";
	} catch (error) {
		schemaError.value = "Failed to serialize validation rules JSON: " + (error as Error).message;
	}
}

/**
 * Save form
 */
async function handleSave() {
	if (schemaError.value) {
		ElMessage.error("Please fix the schema error before saving");
		return;
	}

	// Handle additional_content
	try {
		if (form.value.additional_content_json && form.value.additional_content_json.trim() !== "") {
			form.value.additional_content = JSON.parse(form.value.additional_content_json);
		} else {
			form.value.additional_content = null;
		}
		additionalContentError.value = "";
	} catch (error) {
		additionalContentError.value = "Additional content JSON format error: " + (error as Error).message;
		ElMessage.error("Additional content JSON format error, please check");
		return;
	}

	if (!formRef.value) return;

	await formRef.value.validate(async (valid: boolean) => {
		if (!valid) {
			ElMessage.error("Form validation failed, please check input");
			return;
		}

		saving.value = true;
		try {
			// Create a data object that does not include additional_content_json
			const saveData = { ...form.value };
			delete (saveData as any).additional_content_json;

			// Add character relationship data
			saveData.role_relations = roleRelations.value.map((role) => ({
				role_id: role.role_id,
				llm_provider: role.llm_provider,
				llm_model: role.llm_model,
				voice: role.voice,
				character_setting: role.character_setting,
			}));

			if (isCreateMode.value) {
				await createGamePlayType(saveData);
				ElMessage.success("Create successful");
				router.push("/game/play/list");
			} else {
				await updateGamePlayType(typeId.value, saveData);
				ElMessage.success("Update successful");
				await loadTypeData(); // Reload data
				router.push(`/game-play-types/${typeId.value}`);
			}
		} catch (error) {
			console.error("Save failed", error);
			ElMessage.error("Save failed");
		} finally {
			saving.value = false;
		}
	});
}

// Flag to prevent circular updates
const isUpdatingSchema = ref(false);
const isUpdatingUiSchema = ref(false);
const isUpdatingValidationSchema = ref(false);

// Watch Schema changes, update JSON
watch(
	() => form.value.form_schema,
	(newVal, oldVal) => {
		// Avoid circular updates, only execute when value actually changes
		if (!isUpdatingSchema.value && JSON.stringify(newVal) !== JSON.stringify(oldVal)) {
			isUpdatingSchema.value = true;
			nextTick(() => {
				updateJsonFromSchema();
				// Use setTimeout to ensure DOM is fully updated before releasing the lock
				setTimeout(() => {
					isUpdatingSchema.value = false;
				}, 10);
			});
		}
	},
	{ deep: true },
);

// Watch UI Schema changes, update JSON
watch(
	() => form.value.ui_schema,
	(newVal, oldVal) => {
		// Avoid circular updates, only execute when value actually changes
		if (!isUpdatingUiSchema.value && JSON.stringify(newVal) !== JSON.stringify(oldVal)) {
			isUpdatingUiSchema.value = true;
			nextTick(() => {
				updateJsonFromUiSchema();
				// Use setTimeout to ensure DOM is fully updated before releasing the lock
				setTimeout(() => {
					isUpdatingUiSchema.value = false;
				}, 10);
			});
		}
	},
	{ deep: true },
);

// Watch validation Schema changes, update JSON
watch(
	() => form.value.validation_schema,
	(newVal, oldVal) => {
		// Avoid circular updates, only execute when value actually changes
		if (!isUpdatingValidationSchema.value && JSON.stringify(newVal) !== JSON.stringify(oldVal)) {
			isUpdatingValidationSchema.value = true;
			nextTick(() => {
				updateJsonFromValidationSchema();
				// Use setTimeout to ensure DOM is fully updated before releasing the lock
				setTimeout(() => {
					isUpdatingValidationSchema.value = false;
				}, 10);
			});
		}
	},
	{ deep: true },
);

/**
 * Apply selected template
 */
function applyTemplate(template: string) {
	selectedTemplate.value = template as "empty" | "werewolf" | "mahjong";
	initializeCreateMode(template as "empty" | "werewolf" | "mahjong");
}

/**
 * Initialize create mode default values
 */
function initializeCreateMode(templateType: "empty" | "werewolf" | "mahjong" = "empty") {
	if (templateType === "werewolf") {
		// Werewolf game type template
		form.value = {
			name: "Werewolf",
			game_number_max: 12,
			game_number_min: 6,
			game_play_type: "werewolf",
			role_relations: [], // Character relationship list
			description: "Traditional werewolf game configuration",
			setting: "Werewolf is a multiplayer party game where players are divided into two camps: werewolves and villagers. The werewolves' goal is to eliminate all villagers, while the villagers' goal is to identify and eliminate all werewolves.",
			reference_case: "Can be used as a party game, team building activity, or online multiplayer game",
			version: "1.0.0",
			status: 1,
			additional_content: {
				victory_condition: {
					displayName: "Victory Condition",
					value: "Werewolves: Eliminate all villagers. Villagers: Eliminate all werewolves.",
				},
				game_time: {
					displayName: "Game Duration",
					value: "30-45 minutes",
				},
				difficulty: {
					displayName: "Difficulty Level",
					value: "Medium",
				},
			},
			additional_content_json: JSON.stringify(
				{
					victory_condition: {
						displayName: "Victory Condition",
						value: "Werewolves: Eliminate all villagers. Villagers: Eliminate all werewolves.",
					},
					game_time: {
						displayName: "Game Duration",
						value: "30-45 minutes",
					},
					difficulty: {
						displayName: "Difficulty Level",
						value: "Medium",
					},
				},
				null,
				2,
			),
			form_schema: {
				title: "Werewolf Rules Configuration",
				description: "Configure the characters and rules for the werewolf game",
				components: [
					{
						type: "section",
						title: "Character Configuration",
						fields: [
							{
								name: "roles.wolf",
								label: "Werewolf Count",
								type: "number",
								required: true,
								min: 1,
								default: 2,
								tempId: `field-${Date.now()}-0-0`,
							},
							{
								name: "roles.villager",
								label: "Villager Count",
								type: "number",
								required: true,
								min: 1,
								default: 3,
								tempId: `field-${Date.now()}-0-1`,
							},
							{
								name: "roles.seer",
								label: "Is There a Seer",
								type: "switch",
								default: true,
								tempId: `field-${Date.now()}-0-2`,
							},
							{
								name: "roles.witch",
								label: "Is There a Witch",
								type: "switch",
								default: true,
								tempId: `field-${Date.now()}-0-3`,
							},
						],
						tempId: `section-${Date.now()}-0`,
					},
					{
						type: "section",
						title: "Game Rules",
						fields: [
							{
								name: "rules.firstNightKill",
								label: "Can Kill on the First Night",
								type: "switch",
								default: true,
								tempId: `field-${Date.now()}-1-0`,
							},
							{
								name: "rules.poisonUsage",
								label: "Poison Usage Rules",
								type: "select",
								options: [
									{ label: "Anytime", value: "anytime" },
									{ label: "After Saving", value: "after_save" },
									{ label: "Cannot Use", value: "never" },
								],
								default: "after_save",
								tempId: `field-${Date.now()}-1-1`,
							},
							{
								name: "specialRules",
								label: "Special Rules",
								type: "dynamic-tags",
								placeholder: "Enter rules and press Enter to add",
								default: [],
								tempId: `field-${Date.now()}-1-2`,
							},
						],
						tempId: `section-${Date.now()}-1`,
					},
					{
						type: "section",
						title: "Other Settings",
						fields: [
							{
								name: "gameSettings.voteTime",
								label: "Voting Time (Seconds)",
								type: "slider",
								min: 30,
								max: 180,
								step: 15,
								default: 60,
								tempId: `field-${Date.now()}-2-0`,
							},
						],
						tempId: `section-${Date.now()}-2`,
					},
				],
			},
			ui_schema: {
				layout: "tabs",
				theme: "light",
				cssClasses: {
					formContainer: "game-form-container",
					section: "game-form-section",
					field: "game-form-field",
				},
				conditionalDisplay: [
					{
						if: {
							field: "roles.witch",
							operator: "equals",
							value: true,
						},
						then: {
							action: "show",
							fields: ["rules.poisonUsage"],
						},
					},
				],
			},
			validation_schema: {
				rules: {
					"roles.wolf": [
						{ required: true, message: "Please set werewolf count", trigger: "blur" },
						{ type: "min", value: 1, message: "Werewolves need at least 1", trigger: "blur" },
					],
					"roles.villager": [
						{ required: true, message: "Please set villager count", trigger: "blur" },
						{ type: "min", value: 2, message: "Villagers need at least 2", trigger: "blur" },
					],
					"rules.poisonUsage": [{ required: true, message: "Please select poison usage rules", trigger: "change" }],
				},
			},
		};
	} else if (templateType === "mahjong") {
		console.log("Testing");
	} else {
		// Blank template
		form.value = {
			game_number_max: 2,
			game_number_min: 1,
			game_play_type: "",
			role_relations: [], // Character relationship list
			name: "",
			description: "",
			setting: "",
			reference_case: "",
			version: "",
			status: 1,
			additional_content: null,
			additional_content_json: "{}",
			form_schema: {
				title: "",
				description: "",
				components: [],
			},
			ui_schema: defaultUiSchema,
			validation_schema: {
				rules: {},
			},
		};
	}

	updateJsonFromSchema();
	updateJsonFromUiSchema();
	updateJsonFromValidationSchema();
	parseAdditionalContent(); // Initialize additional content editor
}

/**
 * Add additional content item
 */
function addAdditionalContentItem() {
	additionalContentItems.value.push({
		displayName: "",
		key: `item_${additionalContentItems.value.length + 1}`,
		value: "",
		type: "text",
	});
	updateAdditionalContent();
}

/**
 * Remove additional content item
 */
function removeAdditionalContentItem(index) {
	additionalContentItems.value.splice(index, 1);
	updateAdditionalContent();
}

/**
 * Update additional content JSON string
 */
function updateAdditionalContent() {
	try {
		const newObj: Record<string, any> = {};
		additionalContentItems.value.forEach((item) => {
			// Only add to JSON when key is not empty
			if (item.key && item.key.trim() !== "") {
				newObj[item.key] = {
					displayName: item.displayName || "",
					value: item.value || "",
					type: item.type || "",
				};
			}
		});

		form.value.additional_content_json = JSON.stringify(newObj, null, 2);
		additionalContentError.value = "";
	} catch (error) {
		additionalContentError.value = "Additional content format error: " + (error as Error).message;
	}
}

/**
 * Parse additional content from JSON to editor data structure
 */
function parseAdditionalContent() {
	try {
		const content =
			form.value.additional_content_json && form.value.additional_content_json.trim() !== ""
				? JSON.parse(form.value.additional_content_json)
				: {};

		additionalContentItems.value = [];

		Object.entries(content).forEach(([key, value]) => {
			const item: any = typeof value === "object" ? value : { displayName: "", value: value };
			additionalContentItems.value.push({
				displayName: item.displayName || "",
				key: key,
				value: item.value || value,
				type: item.type || "",
			});
		});

		additionalContentError.value = "";
	} catch (error) {
		additionalContentError.value = "Failed to parse additional content: " + (error as Error).message;
	}
}

/**
 * Load character list
 */
async function loadRoles() {
	try {
		const response = await getRoleList({
			page: 1,
			size: 100,
		});
		availableRoles.value = response.items || [];
	} catch (error) {
		console.error("Failed to load character data", error);
		ElMessage.error("Failed to load character data");
	}
}

/**
 * Load character relationship data
 */
async function loadRoleRelations() {
	if (isCreateMode.value) return; // Not needed in create mode

	try {
		const relations = await getGameRelations(typeId.value);
		roleRelations.value = relations || [];
	} catch (error) {
		console.error("Failed to load character relationship data", error);
		ElMessage.error("Failed to load character relationship data");
	}
}

/**
 * Load LLM models
 */
async function loadLLMModels() {
	try {
		const response = await getActiveLLMProviders();
		llmModels.value = response || [];
	} catch (error) {
		console.error("Failed to load LLM model", error);
		ElMessage.error("Failed to load LLM model");
	}
}

/**
 * Load voice data
 */
async function loadVoices() {
	try {
		const response = await listAudioTimbres();
		voices.value = response || [];
	} catch (error) {
		console.error("Failed to load voice data", error);
		ElMessage.error("Failed to load voice data");
	}
}

/**
 * Play voice example
 */
function playVoice(base64Audio) {
	if (!base64Audio) {
		ElMessage.warning("No audio example");
		return;
	}

	try {
		const audio = new Audio("data:audio/wav;base64," + base64Audio);
		audio.play();
	} catch (error) {
		console.error("Failed to play audio", error);
		ElMessage.error("Failed to play audio");
	}
}

/**
 * Get character initial as avatar
 */
function getRoleInitial(name) {
	if (!name) return "?";
	return name.charAt(0).toUpperCase();
}

/**
 * Edit character settings
 */
function editRoleSettings(role) {
	currentRole.value = role;
	roleSettings.relation_id = role.relation_id;
	roleSettings.llm_provider = role.llm_provider;
	roleSettings.llm_model = role.llm_model;
	roleSettings.voice = role.voice;
	roleSettings.character_setting = role.character_setting;
	showRoleSettings.value = true;
}

/**
 * Save character settings
 */
async function saveRoleSettings() {
	if (!currentRole.value) return;

	savingRoleSettings.value = true;
	try {
		// If there's relation_id, update existing relationship
		if (roleSettings.relation_id) {
			await updateGameRelations(roleSettings.relation_id, {
				llm_provider: roleSettings.llm_provider,
				llm_model: roleSettings.llm_model,
				voice: roleSettings.voice,
				character_setting: roleSettings.character_setting,
			});
			loadRoleRelations();
			// Update local data
		}
		ElMessage.success("Character settings save successful");
		showRoleSettings.value = false;
	} catch (error) {
		console.error("Failed to save character settings", error);
		ElMessage.error("Failed to save character settings");
	} finally {
		savingRoleSettings.value = false;
	}
}

/**
 * Add selected characters
 */
function addSelectedRoles() {
	if (selectedRoleIds.value.length === 0) {
		ElMessage.warning("Please select characters");
		return;
	}

	// Get character details and add to relationship list
	for (const roleId of selectedRoleIds.value) {
		const selectedRole = availableRoles.value.find((r) => r.role_id === roleId);
		if (!selectedRole) continue;

		// Check if already added
		if (roleRelations.value.some((r) => r.role_id === roleId)) {
			continue; // Skip characters already added
		}

		// Add character relationship
		roleRelations.value.push({
			role_id: roleId,
			role_name: selectedRole.name,
			image_url: selectedRole.image_url || null,
			llm_provider: null,
			llm_model: selectedRole.llm_choose || null,
			voice: null,
			character_setting: null,
		});
	}

	// Update form data
	form.value.role_relations = [...roleRelations.value];

	ElMessage.success(`Added ${selectedRoleIds.value.length} characters`);

	// Reset selection state
	selectedRoleIds.value = [];
	showRoleSelector.value = false;
}

/**
 * Remove character from selected list
 */
function removeSelectedRole(roleId) {
	selectedRoleIds.value = selectedRoleIds.value.filter((id) => id !== roleId);
}

/**
 * Get character details by ID
 */
function getRoleById(roleId) {
	return availableRoles.value.find((r) => r.role_id === roleId);
}

/**
 * Remove character relationship
 */
function removeRole(index) {
	roleRelations.value.splice(index, 1);
	form.value.role_relations = [...roleRelations.value];
}

/**
 * Filter available characters, excluding already selected ones
 */
const filteredAvailableRoles = computed(() => {
	const existingRoleIds = roleRelations.value.map((r) => r.role_id);
	return availableRoles.value.filter((r) => !existingRoleIds.includes(r.role_id));
});

/**
 * Load available character list
 */
async function loadAvailableRoles() {
	try {
		const response = await getRoleList({
			page: availableRolesPage.value,
			size: availableRolesPageSize.value,
		});
		if (response && response.items) {
			availableRoles.value = response.items.map((role: Role) => ({
				id: role.role_id, // Use role_id as unique identifier
				name: role.name,
				image_url: role.image_url,
			}));
			availableRolesTotal.value = response.total;
		} else {
			availableRoles.value = [];
			availableRolesTotal.value = 0;
		}
	} catch (error) {
		console.error("Failed to load available character list", error);
		ElMessage.error("Failed to load available character list");
		availableRoles.value = [];
		availableRolesTotal.value = 0;
	}
}

// Initialization
onMounted(async () => {
	if (isCreateMode.value) {
		// Create mode initialization
		initializeCreateMode();
	} else {
		// Load existing data
		loadTypeData();
	}

	// Load character data
	loadRoles();
	loadLLMModels();
	loadVoices();
	await loadAvailableRoles(); // Ensure available character list is loaded on mount
});
</script>

<style scoped lang="scss">
/* 自定义Element Plus组件样式 */

:deep(.el-collapse) {
	.el-form-item {
		* {
			color: rgba(255, 255, 255, 0.66) !important;
		}
	}
	--el-collapse-header-bg-color: rgba(45, 45, 55, 0.4) !important;
	--el-collapse-header-text-color: #bcbcbc;
	--el-collapse-content-bg-color: rgba(45, 45, 55, 0.4) !important;
	--el-collapse-border-color: rgba(220, 223, 230, 0.52);

	.el-collapse-item__header {
		background-color: var(--el-collapse-header-bg-color);
		color: var(--el-collapse-header-text-color);
		font-weight: 500;
		padding-left: 16px;
		border-radius: 4px 4px 0 0;
	}

	.el-collapse-item__content {
		background-color: var(--el-collapse-content-bg-color);
		padding: 20px;
	}
	.el-select__wrapper {
		background-color: var(--el-collapse-content-bg-color);
	}
}

/* 为JSON预览折叠面板添加特殊样式 */
.json-preview {
	:deep(.el-collapse) {
		--el-collapse-header-bg-color: rgba(96, 98, 102, 0.5);
		--el-collapse-header-text-color: rgba(255, 255, 255, 0.51);
		--el-collapse-content-bg-color: rgba(96, 98, 102, 0.5);

		.el-collapse-item__header {
			font-size: 0.9em;
		}
	}
}

.additional-content-editor {
	border: 1px solid rgba(220, 223, 230, 0.2);
	border-radius: 4px;
	padding: 16px;
	margin-bottom: 16px;
	width: 100%;

	.content-item {
		margin-bottom: 16px;
		padding: 12px;
		border: 1px solid rgba(220, 223, 230, 0.2);
		border-radius: 4px;
		box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);

		.item-header {
			display: flex;
			align-items: center;
			margin-bottom: 8px;

			.display-name-input {
				flex: 1;
				margin-right: 10px;
			}

			.key-input {
				flex: 1;
				margin-right: 10px;
			}

			.remove-btn {
				flex-shrink: 0;
			}
		}

		.value-input {
			width: 100%;
		}
	}

	.add-item {
		margin-bottom: 16px;
		text-align: center;
	}

	.json-preview {
		margin-top: 16px;

		pre {
			background-color: rgba(245, 247, 250, 0.3);
			padding: 10px;
			border-radius: 4px;
			overflow-x: auto;
			font-family: monospace;
			font-size: 14px;
			color: #e6e6e6;
		}
	}
}

/* 游戏人数设置相关样式 */
.game-number-setting {
	display: flex;
	align-items: center;
	gap: 10px;
}

.number-input {
	width: 120px;
}

.range-separator {
	color: #ddd;
	font-size: 14px;
}

.range-unit {
	color: #ddd;
	font-size: 14px;
	margin-left: 5px;
}

/* 角色关联相关样式 */
.role-section {
	background: rgba(60, 40, 60, 0.4);
}

.section-desc {
	font-size: 14px;
	color: #aaa;
	margin-bottom: 20px;
}

.role-list {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
	gap: 20px;
}

.role-item {
	position: relative;
	display: flex;
	flex-direction: column;
	align-items: center;
	padding: 20px 15px;
	background: rgba(60, 60, 70, 0.5);
	border-radius: 12px;
	transition: all 0.3s ease;
	border: 1px solid rgba(255, 255, 255, 0.1);
	overflow: hidden;
}

.role-item:hover {
	background: rgba(80, 80, 90, 0.5);
	transform: translateY(-5px);
	box-shadow: 0 8px 15px rgba(0, 0, 0, 0.3);
}

.role-avatar {
	width: 70px;
	height: 70px;
	border-radius: 50%;
	background: linear-gradient(135deg, #e91e63, #9c27b0);
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 28px;
	font-weight: bold;
	color: white;
	margin-bottom: 15px;
}

.role-avatar-img {
	width: 70px;
	height: 70px;
	border-radius: 50%;
	overflow: hidden;
	margin-bottom: 15px;
}

.role-avatar-img img {
	width: 100%;
	height: 100%;
	object-fit: cover;
}

.role-info {
	width: 100%;
	text-align: center;
}

.role-name {
	font-weight: 600;
	font-size: 16px;
	color: #fff;
	margin-bottom: 8px;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

.role-model,
.role-voice {
	font-size: 12px;
	color: #bbb;
	margin-top: 2px;
}

.role-actions {
	position: absolute;
	top: 10px;
	right: 10px;
	display: flex;
	flex-direction: column;
	gap: 8px;
	opacity: 0;
	transition: opacity 0.3s ease;
}

.role-item:hover .role-actions {
	opacity: 1;
}

.edit-role-btn {
	background: linear-gradient(45deg, #3880ff, #00c8ff);
	border: none;
	width: 32px;
	height: 32px;
	padding: 0;
	box-shadow: 0 3px 8px rgba(56, 128, 255, 0.4);
}

.delete-role-btn {
	background: linear-gradient(45deg, #f56c6c, #ff9500);
	border: none;
	width: 32px;
	height: 32px;
	padding: 0;
	box-shadow: 0 3px 8px rgba(245, 108, 108, 0.4);
}

.add-role {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 15px;
	background: rgba(60, 60, 70, 0.3);
	border-radius: 12px;
	cursor: pointer;
	gap: 10px;
	border: 1px dashed rgba(255, 255, 255, 0.2);
	transition: all 0.3s ease;
	height: 90px;
}

.add-role:hover {
	background: rgba(80, 80, 90, 0.4);
	border-color: rgba(255, 255, 255, 0.4);
}

.add-role .el-icon {
	font-size: 24px;
	color: #e91e63;
}

.add-role span {
	color: #ddd;
	font-size: 14px;
}

/* 角色选择对话框 */
:deep(.role-dialog .el-dialog__title) {
	color: #e91e63;
}

:deep(.role-dialog .el-dialog__body) {
	color: #ddd;
}

.role-option {
	display: flex;
	align-items: center;
	gap: 10px;
	padding: 5px 0;
}

.role-option-avatar {
	width: 30px;
	height: 30px;
	border-radius: 50%;
	background: linear-gradient(135deg, #9c27b0, #e91e63);
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 14px;
	font-weight: bold;
	color: white;
}

.role-option-avatar-img {
	width: 30px;
	height: 30px;
	border-radius: 50%;
	overflow: hidden;
}

.role-option-avatar-img img {
	width: 100%;
	height: 100%;
	object-fit: cover;
}

.role-option-info {
	flex: 1;
}

.role-option-name {
	font-weight: 600;
	font-size: 14px;
}

.role-option-desc {
	font-size: 12px;
	color: #999;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
	max-width: 300px;
}

.selected-roles-container {
	margin-top: 20px;
	background: rgba(50, 50, 60, 0.3);
	border-radius: 10px;
	padding: 15px;
	border: 1px solid rgba(255, 255, 255, 0.1);
}

.selected-roles-title {
	color: #fff;
	font-size: 16px;
	margin-top: 0;
	margin-bottom: 15px;
	font-weight: 500;
}

.selected-roles-list {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
	gap: 15px;
}

.selected-role-item {
	display: flex;
	flex-direction: column;
	align-items: center;
	position: relative;
	transition: all 0.3s ease;
}

.selected-role-item:hover {
	transform: translateY(-3px);
}

.selected-role-item .role-name {
	margin-top: 8px;
	font-size: 12px;
	color: #ddd;
	text-align: center;
	width: 100%;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

.selected-role-item .role-avatar,
.selected-role-item .role-avatar-img {
	width: 50px;
	height: 50px;
}

.selected-role-item .role-remove {
	position: absolute;
	top: -8px;
	right: -8px;
	width: 20px;
	height: 20px;
	background: rgba(255, 77, 79, 0.8);
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	cursor: pointer;
	color: white;
	font-size: 12px;
	opacity: 0;
	transition: opacity 0.2s ease;
}

.selected-role-item:hover .role-remove {
	opacity: 1;
}

.option-with-detail {
	display: flex;
	flex-wrap: wrap;
	align-items: center;
}

.option-name {
	font-weight: 600;
	margin-right: 8px;
}

.option-detail {
	font-size: 12px;
	color: #999;
	flex: 1;
}

.option-action {
	margin-left: auto;
}

.role-header {
	display: flex;
	flex-direction: column;
	align-items: center;
	margin-bottom: 20px;
	padding-bottom: 20px;
	border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.role-avatar-large {
	width: 100px;
	height: 100px;
	border-radius: 50%;
	background: linear-gradient(135deg, #e91e63, #9c27b0);
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 40px;
	font-weight: bold;
	color: white;
	margin-bottom: 15px;
}

.role-avatar-img-large {
	width: 100px;
	height: 100px;
	border-radius: 50%;
	overflow: hidden;
	margin-bottom: 15px;
}

.role-avatar-img-large img {
	width: 100%;
	height: 100%;
	object-fit: cover;
}

.role-title {
	font-size: 20px;
	font-weight: 600;
	color: #fff;
}

.empty-roles {
	padding: 20px;
	background: rgba(50, 50, 60, 0.2);
	border-radius: 10px;
	text-align: center;
}
</style>
