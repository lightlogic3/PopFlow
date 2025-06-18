<template>
	<div class="task-detail-container">
		<div class="main-content">
			<div class="header">
				<h1 class="title">{{ isEdit ? "Task Modification" : "Create Task" }}</h1>
				<div class="subtitle">{{ isEdit ? "Modify existing task parameters" : "Create new adventure challenge" }}</div>
			</div>

			<div class="nav-actions">
				<el-button class="back-btn" @click="goBack">
					<el-icon>
						<ArrowLeft />
					</el-icon>
					Back to List
				</el-button>
				<el-button type="primary" class="save-btn" @click="saveTask" :loading="saving">
					<el-icon>
						<Check />
					</el-icon>
					{{ isEdit ? "Save Changes" : "Create Task" }}
				</el-button>
			</div>

			<div class="task-form" v-loading="loading">
				<el-form :model="taskForm" label-position="top" :rules="formRules" ref="taskFormRef">
					<div class="form-section">
						<h2 class="section-title">Basic Information</h2>
						<div class="form-grid">
							<FormItem label="Task Title" prop="title" tooltipKey="title">
								<el-input v-model="taskForm.title" placeholder="Enter task title" />
							</FormItem>
							<FormItem label="Game Type" prop="game_type" tooltipKey="game_play_type">
								<el-select
									v-model="taskForm.game_type"
									placeholder="Select game type"
									style="width: 100%"
									@change="handleGamePlayTypeChange"
									filterable
									:disabled="isEdit"
								>
									<el-option
										v-for="type in gamePlayTypes"
										:key="type.id"
										:label="type.name"
										:value="type.game_play_type"
									>
										<div class="game-play-type-option">
											<div class="option-name">{{ type.name }}</div>
											<div class="option-desc">{{ type.description || "No description" }}</div>
										</div>
									</el-option>
								</el-select>
							</FormItem>
							<FormItem label="Task Type" prop="task_type" tooltipKey="task_type">
								<el-select v-model="taskForm.task_type" placeholder="Select task type" style="width: 100%">
									<el-option v-for="(name, type) in taskTypes" :key="type" :label="name" :value="type">
										<div class="type-option">
											<div class="type-icon" :class="type"></div>
											<span>{{ name }}</span>
										</div>
									</el-option>
								</el-select>
							</FormItem>

							<FormItem label="Task Difficulty" prop="difficulty" tooltipKey="difficulty">
								<el-select v-model="taskForm.difficulty" placeholder="Select task difficulty" style="width: 100%">
									<el-option
										v-for="diff in difficulties"
										:key="diff"
										:label="diff"
										:value="diff"
										:class="{
											'diff-easy': diff === 'Easy',
											'diff-medium': diff === 'Medium',
											'diff-hard': diff === 'Hard',
											'diff-extreme': diff === 'Extreme',
										}"
									/>
								</el-select>
							</FormItem>

							<FormItem label="User Level Requirement" prop="required_user_level" tooltipKey="required_user_level">
								<el-input-number
									v-model="taskForm.required_user_level"
									:min="1"
									:max="100"
									placeholder="Enter required level"
									style="width: 100%"
								/>
							</FormItem>

							<FormItem label="Game Player Count & Time Settings" tooltipKey="game_settings">
								<div class="game-settings-container">
									<div class="game-number-setting">
										<div class="setting-label">
											Player Range:
											<span v-if="getCurrentGamePlayType() && (getCurrentGamePlayType().game_number_min || getCurrentGamePlayType().game_number_max)" class="player-count-hint">
												(Allowed: {{ getCurrentGamePlayType().game_number_min || 1 }}-{{ getCurrentGamePlayType().game_number_max || 100 }} players)
											</span>
										</div>
										<el-form-item
											prop="game_number_min"
											style="display: inline-block; margin-right: 10px; margin-bottom: 0"
										>
											<el-input-number
												v-model="taskForm.game_number_min"
												:min="getMinPlayerCount()"
												:max="taskForm.game_number_max || getMaxPlayerCount()"
												placeholder="Min players"
												size="small"
												@change="validatePlayerCount"
											/>
										</el-form-item>
										<span class="range-separator">to</span>
										<el-form-item
											prop="game_number_max"
											style="display: inline-block; margin-left: 10px; margin-bottom: 0"
										>
											<el-input-number
												v-model="taskForm.game_number_max"
												:min="taskForm.game_number_min || getMinPlayerCount()"
												:max="getMaxPlayerCount()"
												placeholder="Max players"
												size="small"
												@change="validatePlayerCount"
											/>
										</el-form-item>
										<span class="range-unit">players</span>
									</div>
									<div class="time-period-setting">
										<div class="setting-label">Time Period:</div>
										<el-time-picker
											v-model="timeRange"
											is-range
											range-separator="to"
											start-placeholder="Start time"
											end-placeholder="End time"
											format="HH:mm"
											size="small"
											@change="updateTimePeriod"
										/>
									</div>
								</div>
							</FormItem>

							<FormItem label="Task Status" prop="status" tooltipKey="status">
								<el-switch
									v-model="taskForm.status"
									:active-value="1"
									:inactive-value="0"
									active-text="Enabled"
									inactive-text="Disabled"
									inline-prompt
								/>
							</FormItem>
						</div>
					</div>

					<div class="form-section content-section">
						<h2 class="section-title">Task Content</h2>
						<FormItem label="Task Description" prop="description" tooltipKey="description">
							<el-input
								v-model="taskForm.description"
								type="textarea"
								:rows="3"
								placeholder="Describe the background and goals of the task..."
							/>
						</FormItem>

						<FormItem label="Task Setting" prop="setting" tooltipKey="setting">
							<el-input
								v-model="taskForm.setting"
								type="textarea"
								:rows="4"
								placeholder="Detailed description of the task setting, including environment, characters, etc..."
							/>
						</FormItem>

						<FormItem label="Reference Case" prop="reference_case" tooltipKey="reference_case">
							<el-input
								v-model="taskForm.reference_case"
								type="textarea"
								:rows="4"
								placeholder="Provide reference cases for the task..."
							/>
						</FormItem>
					</div>

					<!-- Game Rules Configuration - Independent Card -->
					<div v-if="taskForm.game_type && gamePlayTypeSchema" class="form-section rule-section">
						<h2 class="section-title">Game Rules Configuration</h2>
						<p class="section-desc">Configure relevant game rules based on the selected game type</p>

						<dynamic-form
							ref="dynamicFormRef"
							:key="'dynamic-form-' + taskForm.game_type"
							:schema="gamePlayTypeSchema"
							:ui-schema="gamePlayTypeUiSchema || {}"
							:validation-schema="gamePlayTypeValidationSchema || {}"
							:form-data="ruleFormData"
							@update:form-data="updateRuleFormData"
							@validation="handleValidation"
						/>
					</div>

					<div class="form-section role-section">
						<h2 class="section-title">Character Association</h2>
						<p class="section-desc">Associate characters with this task, you can add multiple characters and set their properties</p>

						<div class="role-list">
							<div v-for="(role, index) in roleRelations" :key="index" class="role-item">
								<div class="role-actions">
									<el-button type="primary" circle size="small" class="edit-role-btn" @click="editRoleSettings(role)">
										<el-icon>
											<Setting />
										</el-icon>
									</el-button>
									<el-button type="danger" circle size="small" class="delete-role-btn" @click="removeRole(index)">
										<el-icon>
											<Delete />
										</el-icon>
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
									<div class="role-model" v-if="role.llm_model">Model: {{ role.llm_model }}</div>
									<div class="role-voice" v-if="role.voice">Voice: {{ role.voice }}</div>
								</div>
							</div>

							<div class="add-role" @click="showRoleSelector = true">
								<el-icon>
									<Plus />
								</el-icon>
								<span>Add Character</span>
							</div>
						</div>
					</div>
				</el-form>
			</div>
		</div>

		<!-- Character Selection Dialog -->
		<el-dialog v-model="showRoleSelector" title="Add Character" width="600px" class="role-dialog">
			<div class="role-selector">
				<el-form :model="roleSelectForm" label-position="top">
					<FormItem label="Select Character" tooltipKey="role_id">
						<el-select
							v-model="selectedRoleIds"
							placeholder="Please select characters (multiple allowed)"
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
					</FormItem>
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
									<el-icon>
										<Delete />
									</el-icon>
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
		<el-dialog v-model="showRoleSettings" title="Character Settings" width="600px" class="role-dialog" :append-to-body="true">
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
					<FormItem label="LLM Model" tooltipKey="llm_model">
						<ModelCascader v-model="roleSettings.llm_model" style="width: 100%" class="model-task" />
					</FormItem>

					<FormItem label="Voice Settings" tooltipKey="voice">
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
					</FormItem>

					<FormItem label="Character Setting" tooltipKey="character_setting">
						<el-input
							v-model="roleSettings.character_setting"
							type="textarea"
							:rows="4"
							placeholder="Enter character's special settings..."
						/>
					</FormItem>
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
import { ref, reactive, onMounted, computed, nextTick, watchEffect } from "vue";
import { useRouter, useRoute } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { ArrowLeft, Plus, Delete, Check, Setting } from "@element-plus/icons-vue";
import type { FormInstance, FormRules } from "element-plus";
import { getRoleList } from "@/api/role";
import { getTaskDetail, createTask, updateTask, getTaskRelations, updateTaskRelation } from "@/api/task";
import { getActiveLLMProviders } from "@/api/llm";
import { listAudioTimbres } from "@/api/audio-timbre";
import { getGamePlayTypes } from "@/api/gamePlayType";
import DynamicForm from "@/components/DynamicForm.vue";
import ModelCascader from "@/components/ModelCascader.vue";
import { Role } from "@/types/role";

const router = useRouter();
const route = useRoute();
const taskId = computed(() => route.params.id);
const isEdit = computed(() => !!taskId.value);
const loading = ref(false);
const saving = ref(false);
const taskFormRef = ref<FormInstance>();
const showRoleSelector = ref(false);
const showRoleSettings = ref(false);
const savingRoleSettings = ref(false);
const timeRange = ref([null, null]);
const llmModels = ref([]);
const voices = ref([]);
const currentRole = ref(null);
const selectedRoleIds = ref([]);
const dynamicFormRef = ref(null);

// Task type mapping
const taskTypes = {
	adventure: "Adventure Exploration",
	mystery: "Mystery Investigation",
	training: "Skill Training",
	"abyss-crisis": "Abyss Crisis",
	"bureau-mission": "Organization Mission",
	other: "Other Type",
};

// Difficulty levels
const difficulties = ["Easy", "Medium", "Hard", "Extreme"];

// Game play related
const gamePlayTypes = ref([]); // Game play types list
const selectedGamePlayType = ref(null); // Selected game play type
const gamePlayTypeSchema = ref(null); // Game play type Schema
const gamePlayTypeUiSchema = ref(null); // Game play type UI Schema
const gamePlayTypeValidationSchema = ref(null); // Game play type validation Schema
const ruleFormData = ref({}); // Rules form data

// Monitor validation rule changes
watchEffect(() => {
	if (gamePlayTypeValidationSchema.value) {
		console.log("Validation rules updated:", gamePlayTypeValidationSchema.value);
	}
});

// Form rules
const formRules = reactive<FormRules>({
	title: [
		{ required: true, message: "Please enter task title", trigger: "blur" },
		{ min: 2, max: 100, message: "Length should be between 2 and 100 characters", trigger: "blur" },
	],
	task_type: [{ required: true, message: "Please select task type", trigger: "change" }],
	game_type: [{ required: true, message: "Please select game type", trigger: "change" }],
	difficulty: [{ required: true, message: "Please select task difficulty", trigger: "change" }],
	description: [
		{ required: true, message: "Please enter task description", trigger: "blur" },
		{ min: 10, max: 500, message: "Length should be between 10 and 500 characters", trigger: "blur" },
	],
	game_number_min: [{ required: true, message: "Please enter minimum number of players", trigger: "blur" }],
	game_number_max: [{ required: true, message: "Please enter maximum number of players", trigger: "blur" }],
});

// Task form data
const taskForm = reactive({
	title: "",
	description: "",
	setting: "",
	max_dialogue_rounds: -1,
	status: 1, // Default enabled
	task_type: "",
	difficulty: "",
	time_period: "",
	required_user_level: null,
	reference_case: "",
	game_number_max: null,
	game_number_min: null,
	rule_data: null,
	game_type: null,
});

// Character association data
const roleRelations = ref([]);
const availableRoles = ref<Role[]>([]); // Add Role type
// Pagination for available roles
const availableRolesPage = ref(1);
const availableRolesPageSize = ref(100); // Assuming a large limit for a selector
const availableRolesTotal = ref(0);
const roleSelectForm = reactive({
	role_id: "",
	character_level: 1.0,
});

// Character settings
const roleSettings = reactive({
	relation_id: null,
	llm_model: null,
	voice: null,
	character_setting: null,
});

// Get character's first letter as avatar
const getRoleInitial = (name) => {
	if (!name) return "?";
	return name.charAt(0).toUpperCase();
};

// Get the currently selected game play type object
const getCurrentGamePlayType = () => {
	if (taskForm.game_type) {
		return gamePlayTypes.value.find((item) => item.game_play_type === taskForm.game_type);
	}
	return null;
};

// Get the minimum player count allowed by current game play type
const getMinPlayerCount = () => {
	if (taskForm.game_type) {
		const currentGamePlayType = gamePlayTypes.value.find((item) => item.game_play_type === taskForm.game_type);
		if (currentGamePlayType && currentGamePlayType.game_number_min) {
			return currentGamePlayType.game_number_min;
		}
	}
	return 1; // Default minimum 1 player
};

// Get the maximum player count allowed by current game play type
const getMaxPlayerCount = () => {
	if (taskForm.game_type) {
		const currentGamePlayType = gamePlayTypes.value.find((item) => item.game_play_type === taskForm.game_type);
		if (currentGamePlayType && currentGamePlayType.game_number_max) {
			return currentGamePlayType.game_number_max;
		}
	}
	return 100; // Default maximum 100 players
};

// Validate if the player count range meets the game play type requirements
const validatePlayerCountRange = () => {
	// Check if player count must be filled
	if (!taskForm.game_number_min || !taskForm.game_number_max) {
		throw new Error("Game player count settings cannot be empty");
	}
	
	// Basic logic validation
	if (taskForm.game_number_min > taskForm.game_number_max) {
		throw new Error("Minimum player count cannot be greater than maximum player count");
	}
	
	if (taskForm.game_number_min < 1) {
		throw new Error("Minimum player count cannot be less than 1");
	}
	
	// If a specific game play type is selected, validate the player count range
	if (taskForm.game_type) {
		// Find the corresponding game play type by game_type
		const currentGamePlayType = gamePlayTypes.value.find((item) => item.game_play_type === taskForm.game_type);
		
		console.log("Current game play type:", taskForm.game_type);
		console.log("Found game play type:", currentGamePlayType);
		
		if (currentGamePlayType && (currentGamePlayType.game_number_min || currentGamePlayType.game_number_max)) {
			const minAllowed = currentGamePlayType.game_number_min || 1;
			const maxAllowed = currentGamePlayType.game_number_max || 100;
			
			console.log(`Game play type ${currentGamePlayType.name} requires player count range: ${minAllowed}-${maxAllowed}`);
			console.log(`User set player count range: ${taskForm.game_number_min}-${taskForm.game_number_max}`);
			
			// Validate minimum player count
			if (taskForm.game_number_min < minAllowed) {
				throw new Error(`Minimum player count cannot be less than ${minAllowed} players (required by game play type "${currentGamePlayType.name}")`);
			}
			
			if (taskForm.game_number_min > maxAllowed) {
				throw new Error(`Minimum player count cannot be greater than ${maxAllowed} players (required by game play type "${currentGamePlayType.name}")`);
			}
			
			// Validate maximum player count
			if (taskForm.game_number_max < minAllowed) {
				throw new Error(`Maximum player count cannot be less than ${minAllowed} players (required by game play type "${currentGamePlayType.name}")`);
			}
			
			if (taskForm.game_number_max > maxAllowed) {
				throw new Error(`Maximum player count cannot be greater than ${maxAllowed} players (required by game play type "${currentGamePlayType.name}")`);
			}
		}
	}
	
	return true;
};

// Validate player count input
const validatePlayerCount = () => {
	if (taskFormRef.value) {
		// Validate player count fields
		setTimeout(() => {
			taskFormRef.value.validateField(["game_number_min", "game_number_max"], () => {});
		}, 100);
	}
};

// Load character data
const loadRoles = async () => {
	try {
		const response = await getRoleList({
			page: availableRolesPage.value,
			size: availableRolesPageSize.value,
		});
		if (response && response.items) {
			availableRoles.value = response.items;
			availableRolesTotal.value = response.total;
		} else {
			availableRoles.value = [];
			availableRolesTotal.value = 0;
		}
	} catch (error) {
		console.error("Failed to load character data", error);
		ElMessage.error("Failed to load character data");
		availableRoles.value = [];
		availableRolesTotal.value = 0;
	}
};

// Load task data
const loadTask = async () => {
	if (!isEdit.value) return;

	loading.value = true;
	try {
		// Load task basic information
		const taskResponse = await getTaskDetail(Number(taskId.value));
		const taskData = taskResponse;

		// Fill form
		Object.keys(taskForm).forEach((key) => {
			if (key in taskData) {
				taskForm[key] = taskData[key];
			}
		});

		// Parse time period
		parseTimePeriod();

		// If there is a game play type ID, load the corresponding game play type Schema
		if (taskData.game_type) {
			// Directly modify the game play type Schema, not triggering auto-fill through handleGamePlayTypeChange method
			loadGamePlayTypeSchema(taskData.game_type);

			// If there is rule data, set it to the form
			if (taskData.rule_data) {
				ruleFormData.value = JSON.parse(JSON.stringify(taskData.rule_data));
				console.log("Rule data loaded:", ruleFormData.value);
			}
		}

		// Load task character associations
		const relationsResponse = await getTaskRelations(Number(taskId.value));
		roleRelations.value = relationsResponse || [];
	} catch (error) {
		console.error("Failed to load task data", error);
		ElMessage.error("Failed to load task data");
	} finally {
		loading.value = false;
	}
};

// Directly load the game play type Schema, not triggering auto-fill
const loadGamePlayTypeSchema = (gamePlayType) => {
	try {
		// Find the selected game play type
		const selected = gamePlayTypes.value.find((item) => item.game_play_type === gamePlayType);
		if (!selected) return;

		selectedGamePlayType.value = selected;
		console.log("Selected game play type:", selected);

		// Clone schema to avoid modifying original data
		const formSchema = selected.form_schema ? JSON.parse(JSON.stringify(selected.form_schema)) : null;

		// Process schema conversion - convert "input" type to "text" type
		if (formSchema && formSchema.components) {
			formSchema.components.forEach((section) => {
				if (section.fields) {
					section.fields.forEach((field) => {
						// Map "input" type to "text" type
						if (field.type === "input") {
							field.type = "text";
						}
					});
				}
			});
		}

		// Process UI Schema - ensure it has the correct structure
		let uiSchema = null;
		if (selected.ui_schema) {
			uiSchema = JSON.parse(JSON.stringify(selected.ui_schema));

			// Ensure necessary properties exist
			if (!uiSchema.cssClasses) {
				uiSchema.cssClasses = {
					formContainer: "game-form-container",
					section: "game-form-section",
					field: "game-form-field",
				};
			}

			if (!uiSchema.conditionalDisplay) {
				uiSchema.conditionalDisplay = [];
			}

			if (!uiSchema.layout) {
				uiSchema.layout = "tabs";
			}

			if (!uiSchema.theme) {
				uiSchema.theme = "light";
			}
		}

		// Process validation Schema
		let validationSchema = {};

		// If it's a turtle soup type, add specific validation rules
		if (gamePlayType === "turtle_soup") {
			validationSchema = {
				soup: [
					{ required: true, message: "Please enter soup content", trigger: "blur" },
					{ min: 10, message: "Soup content must be at least 10 characters", trigger: "blur" },
				],
				answer: [
					{ required: true, message: "Please enter answer content", trigger: "blur" },
					{ min: 10, message: "Answer content must be at least 10 characters", trigger: "blur" },
				],
			};
		} else if (selected.validation_schema && selected.validation_schema.rules) {
			// Extract from original validation rules
			Object.keys(selected.validation_schema.rules).forEach((fieldName) => {
				if (Array.isArray(selected.validation_schema.rules[fieldName])) {
					validationSchema[fieldName] = [...selected.validation_schema.rules[fieldName]];
				}
			});
		}

		// Set Schema
		gamePlayTypeSchema.value = formSchema;
		gamePlayTypeUiSchema.value = uiSchema;
		gamePlayTypeValidationSchema.value = validationSchema;
	} catch (error) {
		console.error("Failed to load game play type Schema", error);
	}
};

// Back to list
const goBack = () => {
	if (isFormDirty()) {
		ElMessageBox.confirm("You have unsaved changes, are you sure you want to leave?", "Confirm", {
			confirmButtonText: "Confirm",
			cancelButtonText: "Cancel",
			type: "warning",
		})
			.then(() => {
				router.push("/chat/tasks");
			})
			.catch(() => {});
	} else {
		router.push("/chat/tasks");
	}
};

// Determine if form has changes
const isFormDirty = () => {
	// Simple judgment, actual application may require more complex comparison
	return true;
};

// Save task
const saveTask = async () => {
	if (!taskFormRef.value) return;

	await taskFormRef.value.validate(async (valid) => {
		if (!valid) {
			ElMessage.error("Please check form content");
			return;
		}

		// Force validate player count range
		try {
			validatePlayerCountRange();
		} catch (error:any) {
			ElMessage.error(error.message);
			return;
		}

		// Determine if dynamic form needs to be validated
		if (taskForm.game_type && gamePlayTypeSchema.value && dynamicFormRef.value) {
			try {
				// Validate dynamic form
				const dynamicFormValid = await dynamicFormRef.value.validate();

				if (!dynamicFormValid) {
					ElMessage.error("Please check game rules configuration form");
					return;
				}
			} catch (error) {
				console.error("Dynamic form validation error", error);
				ElMessage.error("Game rules configuration validation failed");
				return;
			}
		}

		saving.value = true;
		try {
			// Prepare submission data
			const taskData = { ...taskForm } as any; // Use type assertion to allow adding extra properties
			taskData.role_relations = roleRelations.value;

			if (isEdit.value) {
				// Update task
				await updateTask(Number(taskId.value), taskData);
				ElMessage.success("Task updated successfully");
			} else {
				// Create task
				await createTask(taskData);
				ElMessage.success("Task created successfully");
			}

			// Return to list page
			router.push("/chat/tasks");
		} catch (error) {
			console.error("Failed to save task", error);
			ElMessage.error("Failed to save task");
		} finally {
			saving.value = false;
		}
	});
};

// Load LLM models
const loadLLMModels = async () => {
	try {
		const response = await getActiveLLMProviders();
		llmModels.value = response || [];
	} catch (error) {
		console.error("Failed to load LLM models", error);
		ElMessage.error("Failed to load LLM models");
	}
};

// Load voice data
const loadVoices = async () => {
	try {
		const response = await listAudioTimbres();
		voices.value = response || [];
	} catch (error) {
		console.error("Failed to load voice data", error);
		ElMessage.error("Failed to load voice data");
	}
};

// Play voice sample
const playVoice = (base64Audio) => {
	if (!base64Audio) {
		ElMessage.warning("No audio sample");
		return;
	}

	try {
		const audio = new Audio("data:audio/wav;base64," + base64Audio);
		audio.play();
	} catch (error) {
		console.error("Failed to play audio", error);
		ElMessage.error("Failed to play audio");
	}
};

// Edit character settings
const editRoleSettings = (role) => {
	currentRole.value = role;
	roleSettings.relation_id = role.relation_id;
	roleSettings.llm_model = role.llm_model;
	roleSettings.voice = role.voice;
	roleSettings.character_setting = role.character_setting;
	showRoleSettings.value = true;
};

// Save character settings
const saveRoleSettings = async () => {
	if (!currentRole.value || !roleSettings.relation_id) return;

	savingRoleSettings.value = true;
	try {
		// Send request to save settings
		const data = await updateTaskRelation(roleSettings.relation_id, {
			llm_model: roleSettings.llm_model,
			voice: roleSettings.voice,
			character_setting: roleSettings.character_setting,
		});

		// Update local data
		const index = roleRelations.value.findIndex((r) => r.relation_id === roleSettings.relation_id);
		if (index !== -1) {
			roleRelations.value[index] = {
				...roleRelations.value[index],
				llm_model: data.llm_model,
				voice: data.voice,
				character_setting: data.character_setting,
			};
		}

		ElMessage.success("Character settings saved successfully");
		showRoleSettings.value = false;
	} catch (error) {
		console.error("Failed to save character settings", error);
		ElMessage.error("Failed to save character settings");
	} finally {
		savingRoleSettings.value = false;
	}
};

// Character related computed properties
const filteredAvailableRoles = computed(() => {
	// Filter out characters that are already in roleRelations
	const existingRoleIds = roleRelations.value.map((r) => r.role_id);
	return availableRoles.value.filter((r) => !existingRoleIds.includes(r.role_id));
});

// Add selected characters
const addSelectedRoles = () => {
	if (selectedRoleIds.value.length === 0) {
		ElMessage.warning("Please select characters");
		return;
	}

	// Get character details
	for (const roleId of selectedRoleIds.value) {
		const selectedRole = availableRoles.value.find((r) => r.role_id === roleId);
		if (!selectedRole) continue;

		// Check if already added
		if (roleRelations.value.some((r) => r.role_id === roleId)) {
			continue; // Skip already added characters
		}

		// Add character
		roleRelations.value.push({
			role_id: roleId,
			role_name: selectedRole.name,
			image_url: selectedRole.image_url || null,
			llm_model: selectedRole.llm_choose || null,
			voice: null,
			character_setting: null,
		});
	}

	ElMessage.success(`Added ${selectedRoleIds.value.length} characters`);

	// Reset form
	selectedRoleIds.value = [];
	showRoleSelector.value = false;
};

// Remove character from selected list
const removeSelectedRole = (roleId) => {
	selectedRoleIds.value = selectedRoleIds.value.filter((id) => id !== roleId);
};

// Get character details by ID
const getRoleById = (roleId) => {
	return availableRoles.value.find((r) => r.role_id === roleId);
};

// Remove character
const removeRole = (index) => {
	roleRelations.value.splice(index, 1);
};

// Update time period
const updateTimePeriod = () => {
	if (timeRange.value && timeRange.value[0] && timeRange.value[1]) {
		const startTime = timeRange.value[0];
		const endTime = timeRange.value[1];

		const formatTime = (time) => {
			const hours = time.getHours().toString().padStart(2, "0");
			const minutes = time.getMinutes().toString().padStart(2, "0");
			return `${hours}:${minutes}`;
		};

		taskForm.time_period = `${formatTime(startTime)}-${formatTime(endTime)}`;
	}
};

// Parse time period
const parseTimePeriod = () => {
	if (taskForm.time_period) {
		const [start, end] = taskForm.time_period.split("-");
		if (start && end) {
			const parseTime = (timeStr) => {
				const [hours, minutes] = timeStr.split(":").map(Number);
				const date = new Date();
				date.setHours(hours);
				date.setMinutes(minutes);
				return date;
			};

			timeRange.value = [parseTime(start), parseTime(end)];
		}
	}
};

// Load game play types list
const loadGamePlayTypes = async () => {
	try {
		const response = await getGamePlayTypes({
			skip: 0,
			limit: 100,
		});
		gamePlayTypes.value = response;
		console.log("Game play types list loaded successfully:", gamePlayTypes.value);
	} catch (error) {
		console.error("Failed to load game play types list", error);
		ElMessage.error("Failed to load game play types list");
	}
};

// Handle game play type selection change
const handleGamePlayTypeChange = async (value) => {
	if (!value) {
		gamePlayTypeSchema.value = null;
		gamePlayTypeUiSchema.value = null;
		gamePlayTypeValidationSchema.value = null;
		ruleFormData.value = {};
		selectedGamePlayType.value = null;
		return;
	}

	try {
				// Find selected game play type
		const selected = gamePlayTypes.value.find((item) => item.game_play_type === value);
		if (!selected) return;

		selectedGamePlayType.value = selected;
		console.log("Selected game play type:", selected);
		console.log("Original validation Schema:", selected.validation_schema);

		// Auto-fill related task fields
		await autoFillTaskFields(selected);

		// Clone schema to avoid modifying original data
		const formSchema = selected.form_schema ? JSON.parse(JSON.stringify(selected.form_schema)) : null;

		// Process schema conversion - convert "input" type to "text" type
		if (formSchema && formSchema.components) {
			formSchema.components.forEach((section) => {
				if (section.fields) {
					section.fields.forEach((field) => {
						// Map "input" type to "text" type
						if (field.type === "input") {
							field.type = "text";
						}
					});
				}
			});
		}

		// Process UI Schema - ensure it has the correct structure
		let uiSchema = null;
		if (selected.ui_schema) {
			uiSchema = JSON.parse(JSON.stringify(selected.ui_schema));

			// Ensure necessary properties exist
			if (!uiSchema.cssClasses) {
				uiSchema.cssClasses = {
					formContainer: "game-form-container",
					section: "game-form-section",
					field: "game-form-field",
				};
			}

			if (!uiSchema.conditionalDisplay) {
				uiSchema.conditionalDisplay = [];
			}

			if (!uiSchema.layout) {
				uiSchema.layout = "tabs";
			}

			if (!uiSchema.theme) {
				uiSchema.theme = "light";
			}
		}

		// Process validation Schema
		let validationSchema = {};

		// If it's a turtle soup type, add specific validation rules
		if (value === "turtle_soup") {
			validationSchema = {
				soup: [
					{ required: true, message: "Please enter soup content", trigger: "blur" },
					{ min: 10, message: "Soup content must be at least 10 characters", trigger: "blur" },
				],
				answer: [
					{ required: true, message: "Please enter answer content", trigger: "blur" },
					{ min: 10, message: "Answer content must be at least 10 characters", trigger: "blur" },
				],
			};
		} else if (selected.validation_schema && selected.validation_schema.rules) {
			// Extract from original validation rules
			Object.keys(selected.validation_schema.rules).forEach((fieldName) => {
				if (Array.isArray(selected.validation_schema.rules[fieldName])) {
					validationSchema[fieldName] = [...selected.validation_schema.rules[fieldName]];
				}
			});
		}

		console.log("Processed validation Schema:", validationSchema);

		// Set Schema
		gamePlayTypeSchema.value = formSchema;
		gamePlayTypeUiSchema.value = uiSchema;
		gamePlayTypeValidationSchema.value = validationSchema;

		// Confirm final set validation Schema
		console.log("Final validation Schema set:", gamePlayTypeValidationSchema.value);

		// If in edit mode and there is saved rule data, use it to initialize the form
		if (isEdit.value && taskForm.rule_data) {
			ruleFormData.value = JSON.parse(JSON.stringify(taskForm.rule_data));
		} else {
			// Otherwise initialize to empty object
			ruleFormData.value = {};
		}

		console.log("Set game play type Schema:", {
			schema: gamePlayTypeSchema.value,
			uiSchema: gamePlayTypeUiSchema.value,
			validationSchema: gamePlayTypeValidationSchema.value,
		});

		// Force component re-render
		nextTick(() => {
			const timestamp = Date.now();
			console.log(`Trigger component re-render timestamp=${timestamp}`);
		});
	} catch (error) {
		console.error("Failed to handle game play type selection change", error);
		ElMessage.error("Failed to handle game play type selection change");
	}
};

// Auto-fill task fields
const autoFillTaskFields = async (selectedGamePlay) => {
	// Fields mapping to be filled
	const fieldMappings = {
		name: "title",
		description: "description",
		setting: "setting",
		reference_case: "reference_case",
		player_count: "player_count", // This needs special handling
	};

	// Check if there are non-empty fields
	const hasNonEmptyFields = Object.keys(fieldMappings).some((key) => {
		const targetField = fieldMappings[key] === "player_count" ? "game_number_min" : fieldMappings[key];
		return taskForm[targetField] !== undefined && taskForm[targetField] !== null && taskForm[targetField] !== "";
	});

	// If there are non-empty fields, prompt user whether to overwrite
	if (hasNonEmptyFields) {
		try {
			await ElMessageBox.confirm("Existing field content detected, do you want to overwrite relevant fields with the selected game play type?", "Confirm Overwrite", {
				confirmButtonText: "Confirm Overwrite",
				cancelButtonText: "Keep Existing Content",
				type: "warning",
			});
			// User confirmed overwrite, execute fill logic below
		} catch (error) {
			// User canceled overwrite, return directly
			console.log("User canceled field overwrite");
			return;
		}
	}

	// Fill fields
	Object.keys(fieldMappings).forEach((sourceKey) => {
		const targetField = fieldMappings[sourceKey];
		if (selectedGamePlay[sourceKey] !== undefined) {
			// Handle special fields
			if (sourceKey === "player_count" && selectedGamePlay[sourceKey]) {
				// Handle player count format, e.g. "3-4" format
				const playerCount = selectedGamePlay[sourceKey];
				const matches = playerCount.match(/(\d+)-(\d+)/);
				if (matches && matches.length === 3) {
					taskForm.game_number_min = parseInt(matches[1]);
					taskForm.game_number_max = parseInt(matches[2]);
				} else if (!isNaN(parseInt(playerCount))) {
					// If it's a single number
					taskForm.game_number_min = parseInt(playerCount);
					taskForm.game_number_max = parseInt(playerCount);
				}
			} else {
				// Regular fields direct assignment
				taskForm[targetField] = selectedGamePlay[sourceKey];
			}
		}
	});

	// Set difficulty level (if not set)
	if (!taskForm.difficulty) {
		// Can set different default difficulty based on game play type
		switch (selectedGamePlay.game_play_type) {
			case "turtle_soup":
				taskForm.difficulty = "Medium";
				break;
			default:
				taskForm.difficulty = "Easy";
				break;
		}
	}

	// Set user level requirement (if not set)
	if (!taskForm.required_user_level) {
		taskForm.required_user_level = 1;
	}

	// Set task type based on game type (if not set)
	if (!taskForm.task_type) {
		// Set default task type based on game play type
		switch (selectedGamePlay.game_play_type) {
			case "turtle_soup":
				taskForm.task_type = "mystery";
				break;
			case "werewolf":
				taskForm.task_type = "adventure";
				break;
			case "mafia":
				taskForm.task_type = "training";
				break;
			default:
				taskForm.task_type = "adventure";
				break;
		}
	}

	// Set default time period (if not set)
	if (!taskForm.time_period) {
		taskForm.time_period = "19:00-22:00";
		// Update time picker value
		const startDate = new Date();
		startDate.setHours(19, 0, 0);
		const endDate = new Date();
		endDate.setHours(22, 0, 0);
		timeRange.value = [startDate, endDate];
	}

	ElMessage.success("Relevant task fields auto-filled");
};

// Update rule form data
const updateRuleFormData = (data) => {
	ruleFormData.value = data;
	console.log("Rule form data updated:", ruleFormData.value);
	// Synchronize to task form
	taskForm.rule_data = JSON.parse(JSON.stringify(ruleFormData.value));
};

// Handle dynamic form validation
const handleValidation = (result) => {
	console.log("Dynamic form validation result:", result);
	if (!result.valid) {
		// Error messages already handled within the component
		console.warn("Dynamic form validation failed, errors:", result.errors);
	}
};

// Component mount execution
onMounted(() => {
	//loadRoles();
	loadGamePlayTypes(); // Load game play types list
	loadTask();
	loadLLMModels();
	loadVoices();
});
</script>

<style scoped lang="scss">
.task-detail-container {
	min-height: 100vh;
	position: relative;
	overflow: hidden;
	color: #f0f0f0;
	padding-bottom: 50px;
	background-image: linear-gradient(to bottom, rgba(30, 30, 30, 0.9), rgba(10, 10, 10, 0.95)),
		url("https://img.freepik.com/free-photo/abstract-futuristic-background-with-colorful-glowing-neon-lights_181624-34728.jpg");
}

.main-content {
	max-width: 1200px;
	margin: 0 auto;
	padding: 30px;
}

.header {
	text-align: center;
	margin-bottom: 30px;
}

.title {
	font-size: 36px;
	color: #e91e63;
	text-shadow: 0 0 15px rgba(233, 30, 99, 0.5);
	margin-bottom: 10px;
}

.subtitle {
	font-size: 18px;
	color: #aaa;
	margin-bottom: 20px;
}

.nav-actions {
	display: flex;
	justify-content: space-between;
	margin-bottom: 30px;
}

.back-btn,
.save-btn {
	display: flex;
	align-items: center;
	gap: 8px;
	height: 45px;
	padding: 0 25px;
	border-radius: 22.5px;
	font-weight: 500;
	letter-spacing: 1px;
	transition: all 0.3s ease;
}

.back-btn {
	background: rgba(255, 255, 255, 0.1);
	border: 1px solid rgba(255, 255, 255, 0.2);
	color: #fff;
}

.back-btn:hover {
	background: rgba(255, 255, 255, 0.2);
}

.save-btn {
	background: linear-gradient(45deg, #e91e63, #9c27b0);
	border: none;
	box-shadow: 0 5px 15px rgba(233, 30, 99, 0.3);
}

.save-btn:hover {
	transform: translateY(-3px);
	box-shadow: 0 8px 20px rgba(233, 30, 99, 0.5);
}

.task-form {
	background: rgba(35, 35, 45, 0.7);
	border-radius: 20px;
	padding: 30px;
	box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
	backdrop-filter: blur(10px);
	-webkit-backdrop-filter: blur(10px);
	border: 1px solid rgba(255, 255, 255, 0.1);
}

.form-section {
	margin-bottom: 40px;
	position: relative;
	padding: 25px;
	background: rgba(45, 45, 55, 0.4);
	border-radius: 15px;
	border: 1px solid rgba(255, 255, 255, 0.05);
}

.content-section {
	background: rgba(40, 40, 60, 0.4);
}

.role-section {
	background: rgba(60, 40, 60, 0.4);
}

.rule-section {
	background: rgba(40, 60, 60, 0.4);
}

.section-title {
	font-size: 22px;
	color: #fff;
	margin-bottom: 25px;
	position: relative;
	padding-left: 15px;
	font-weight: 600;
}

.section-title::before {
	content: "";
	position: absolute;
	left: 0;
	top: 50%;
	width: 4px;
	height: 25px;
	background: linear-gradient(to bottom, #e91e63, #9c27b0);
	transform: translateY(-50%);
	border-radius: 4px;
}

.section-desc {
	font-size: 14px;
	color: #aaa;
	margin-bottom: 20px;
}

.form-grid {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 20px;
}

.game-settings-container {
	display: flex;
	flex-direction: column;
	gap: 10px;
}

.game-number-setting,
.time-period-setting {
	display: flex;
	align-items: center;
	gap: 5px;
}

.setting-label {
	min-width: 70px;
	font-size: 14px;
	color: #ddd;

	.player-count-hint {
		font-size: 12px;
		color: #e91e63;
		margin-left: 5px;
		font-weight: 500;
	}
}

.range-separator,
.range-unit {
	margin: 0 5px;
	color: #ddd;
}

.type-option {
	display: flex;
	align-items: center;
	gap: 10px;
}

.type-icon {
	width: 20px;
	height: 20px;
	border-radius: 50%;
}

.type-icon.adventure {
	background-color: #67c23a;
}

.type-icon.mystery {
	background-color: #e6a23c;
}

.type-icon.training {
	background-color: #409eff;
}

.type-icon.abyss-crisis {
	background-color: #f56c6c;
}

.type-icon.bureau-mission {
	background-color: #9c27b0;
}

.type-icon.other {
	background-color: #909399;
}

.diff-easy {
	color: #67c23a;
}

.diff-medium {
	color: #e6a23c;
}

.diff-hard {
	color: #f56c6c;
}

.diff-extreme {
	color: #909399;
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

.role-level {
	display: none;
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

:deep(.el-form-item__label) {
	color: #ddd;
}

:deep(.el-input__wrapper) {
	background-color: rgba(60, 60, 70, 0.5);
	border: 1px solid rgba(255, 255, 255, 0.1);
}

:deep(.el-textarea__inner) {
	background-color: rgba(60, 60, 70, 0.5);
	border: 1px solid rgba(255, 255, 255, 0.1);
	color: #fff;
}

:deep(.el-input__inner) {
	color: #fff;
}

:deep(.el-select__popper) {
	background-color: rgba(40, 40, 50, 0.95) !important;
	border: 1px solid rgba(255, 255, 255, 0.1) !important;
	border-radius: 10px !important;
	backdrop-filter: blur(10px);
}

:deep(.el-select-dropdown__item) {
	color: #ddd !important;
}

:deep(.el-select-dropdown__item.selected) {
	color: #e91e63 !important;
}

:deep(.el-select-dropdown__item:hover) {
	background-color: rgba(60, 60, 70, 0.7) !important;
}

.role-avatar-img img {
	width: 100%;
	height: 100%;
	object-fit: cover;
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

.role-model,
.role-voice {
	font-size: 12px;
	color: #bbb;
	margin-top: 2px;
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

.role-settings {
	padding: 10px;
}

/* Add animation effects */
.role-item {
	transition: all 0.3s ease;
}

.role-item:hover {
	transform: translateY(-5px);
	box-shadow: 0 8px 15px rgba(0, 0, 0, 0.3);
}

/* Responsive adjustments */
@media (max-width: 768px) {
	.main-content {
		padding: 20px;
	}

	.form-grid {
		grid-template-columns: 1fr;
	}

	.task-form {
		padding: 20px;
	}

	.title {
		font-size: 28px;
	}

	.nav-actions {
		flex-direction: column;
		gap: 10px;
	}

	.back-btn,
	.save-btn {
		width: 100%;
		justify-content: center;
	}

	.option-with-detail {
		flex-direction: column;
		align-items: flex-start;
	}

	.option-action {
		margin-left: 0;
		margin-top: 5px;
	}
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

/* Modify multi-select dropdown style */
:deep(.el-select-dropdown__item.selected) {
	background-color: rgba(60, 30, 70, 0.3) !important;
}

:deep(.el-select__tags) {
	background-color: transparent;
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

/* Game play type dropdown style */
.game-play-type-option {
	display: flex;
	flex-direction: column;
	gap: 5px;
}

.option-name {
	font-weight: 600;
	font-size: 14px;
}

.option-desc {
	font-size: 12px;
	color: #aaa;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
	max-width: 100%;
}

/* Game rules form style */
.game-rule-section {
	background: rgba(50, 50, 70, 0.4);
	border-radius: 15px;
	border: 1px solid rgba(255, 255, 255, 0.1);
	padding: 20px;
	margin-bottom: 30px;
}

.subsection-title {
	font-size: 18px;
	color: #e91e63;
	margin-bottom: 15px;
	font-weight: 600;
}

.subsection-desc {
	font-size: 14px;
	color: #aaa;
	margin-bottom: 20px;
}
</style>
