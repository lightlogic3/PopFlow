<template>
	<div class="task-detail-container">
		<div class="main-content">
			<div class="header">
				<h1 class="title">{{ isEdit ? "Task Modification" : "Create Task" }}</h1>
				<div class="subtitle">{{ isEdit ? "修改现有任务参数" : "创建新的冒险挑战" }}</div>
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
							<FormItem label="Gameplay Type" prop="game_type" tooltipKey="game_play_type">
								<el-select
									v-model="taskForm.game_type"
									placeholder="Select gameplay type"
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

							<FormItem label="Difficulty" prop="difficulty" tooltipKey="difficulty">
								<el-select v-model="taskForm.difficulty" placeholder="Select difficulty level" style="width: 100%">
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

							<FormItem label="Player Count & Time Settings" tooltipKey="game_settings">
								<div class="game-settings-container">
									<div class="game-number-setting">
										<div class="setting-label">
											Player Count:
											<span
												v-if="
													getCurrentGamePlayType() &&
													(getCurrentGamePlayType().game_number_min || getCurrentGamePlayType().game_number_max)
												"
												class="player-count-hint"
											>
												(Allowed range: {{ getCurrentGamePlayType().game_number_min || 1 }}-{{
													getCurrentGamePlayType().game_number_max || 100
												}}players)
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
								placeholder="Describe the task background and objectives..."
							/>
						</FormItem>

						<FormItem label="Task Setting" prop="setting" tooltipKey="setting">
							<el-input
								v-model="taskForm.setting"
								type="textarea"
								:rows="4"
								placeholder="Describe the task setting in detail, including environment, characters, etc..."
							/>
						</FormItem>

						<FormItem label="Reference Case" prop="reference_case" tooltipKey="reference_case">
							<el-input
								v-model="taskForm.reference_case"
								type="textarea"
								:rows="4"
								placeholder="Provide reference examples for this task"
							/>
						</FormItem>
					</div>

					<!-- 游戏规则配置 - 独立卡片 -->
					<div v-if="taskForm.game_type && gamePlayTypeSchema" class="form-section rule-section">
						<h2 class="section-title">Game Rules Configuration</h2>
						<p class="section-desc">Configure gameplay rules according to the selected game type</p>

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
						<p class="section-desc">Associate characters with this task. You may add multiple characters and configure their attributes.</p>

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
									<img :src="role.image_url" alt="character avatar" />
								</div>
								<div class="role-info">
									<div class="role-name">{{ role.role_name || role.role_id }}</div>
									<div class="role-model" v-if="role.llm_model">LLM Model: {{ role.llm_model }}</div>
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

		<!-- 角色选择对话框 -->
		<el-dialog v-model="showRoleSelector" title="Add Character" width="600px" class="role-dialog">
			<div class="role-selector">
				<el-form :model="roleSelectForm" label-position="top">
					<FormItem label="Select Characters" tooltipKey="role_id">
						<el-select
							v-model="selectedRoleIds"
							placeholder="Select characters (multiple)"
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
										<img :src="role.image_url" alt="character avatar" />
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

				<!-- 已选角色列表 -->
				<div class="selected-roles-container" v-if="selectedRoleIds.length > 0">
					<h4 class="selected-roles-title">Selected Characters</h4>
					<div class="selected-roles-list">
						<div v-for="roleId in selectedRoleIds" :key="roleId" class="selected-role-item">
							<template v-if="getRoleById(roleId)">
								<div class="role-avatar" v-if="!getRoleById(roleId).image_url">
									{{ getRoleInitial(getRoleById(roleId).name) }}
								</div>
								<div class="role-avatar-img" v-else>
									<img :src="getRoleById(roleId).image_url" alt="character avatar" />
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
					<el-button class="btn-fix" type="primary" @click="addSelectedRoles" :disabled="selectedRoleIds.length === 0">
						Add Selected ({{ selectedRoleIds.length }})
					</el-button>
				</div>
			</template>
		</el-dialog>

		<!-- 角色设置对话框 -->
		<el-dialog v-model="showRoleSettings" title="角色设置1" width="600px" class="role-dialog" :append-to-body="true">
			<div class="role-settings" v-if="currentRole">
				<div class="role-header">
					<div class="role-avatar-large" v-if="!currentRole.image_url">
						{{ getRoleInitial(currentRole.role_name || currentRole.role_id) }}
					</div>
					<div class="role-avatar-img-large" v-else>
						<img :src="currentRole.image_url" alt="角色头像" />
					</div>
					<div class="role-title">{{ currentRole.role_name || currentRole.role_id }}</div>
				</div>

				<el-form :model="roleSettings" label-position="top">
					<FormItem label="大语言模型" tooltipKey="llm_model">
						<ModelCascader v-model="roleSettings.llm_model" style="width: 100%" class="model-task" />
					</FormItem>

					<FormItem label="音色设置" tooltipKey="voice">
						<el-select v-model="roleSettings.voice" placeholder="选择音色" filterable clearable style="width: 100%">
							<el-option v-for="voice in voices" :key="voice.speaker_id" :label="voice.alias" :value="voice.speaker_id">
								<div class="option-with-detail">
									<div class="option-name">{{ voice.alias }}</div>
									<div class="option-detail">{{ voice.speaker_id }}</div>
									<div class="option-action" v-if="voice.audition">
										<el-button size="small" @click.stop="playVoice(voice.audition)">试听</el-button>
									</div>
								</div>
							</el-option>
						</el-select>
					</FormItem>

					<FormItem label="角色设定" tooltipKey="character_setting">
						<el-input
							v-model="roleSettings.character_setting"
							type="textarea"
							:rows="4"
							placeholder="输入角色的特殊设定..."
						/>
					</FormItem>
				</el-form>
			</div>
			
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

// 任务类型映射
const taskTypes = {
    adventure: "Adventure Exploration",
    mystery: "Mystery Investigation", 
    training: "Skill Training",
    "abyss-crisis": "Abyss Crisis",
    "bureau-mission": "Agency Mission",
    other: "Other Types"
};

// 难度等级
const difficulties = ["Easy", "Mid", "Hard", "Extreme"];

// 游戏玩法相关
const gamePlayTypes = ref([]); // 游戏玩法列表
const selectedGamePlayType = ref(null); // 选中的游戏玩法
const gamePlayTypeSchema = ref(null); // 游戏玩法Schema
const gamePlayTypeUiSchema = ref(null); // 游戏玩法UI Schema
const gamePlayTypeValidationSchema = ref(null); // 游戏玩法验证Schema
const ruleFormData = ref({}); // 规则表单数据

// 监视验证规则变化
watchEffect(() => {
	if (gamePlayTypeValidationSchema.value) {
		console.log("验证规则已更新:", gamePlayTypeValidationSchema.value);
	}
});

// 表单规则
const formRules = reactive<FormRules>({
	title: [
		{ required: true, message: "请输入任务标题", trigger: "blur" },
		{ min: 2, max: 100, message: "长度应在 2 到 100 个字符之间", trigger: "blur" },
	],
	task_type: [{ required: true, message: "请选择任务类型", trigger: "change" }],
	game_type: [{ required: true, message: "请选择游戏玩法", trigger: "change" }],
	difficulty: [{ required: true, message: "请选择任务难度", trigger: "change" }],
	description: [
		{ required: true, message: "请输入任务描述", trigger: "blur" },
		{ min: 10, max: 500, message: "长度应在 10 到 500 个字符之间", trigger: "blur" },
	],
	game_number_min: [{ required: true, message: "请输入最少人数", trigger: "blur" }],
	game_number_max: [{ required: true, message: "请输入最多人数", trigger: "blur" }],
});

// 任务表单数据
const taskForm = reactive({
	title: "",
	description: "",
	setting: "",
	max_dialogue_rounds: -1,
	status: 1, // 默认启用
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

// 角色关联数据
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

// 角色设置
const roleSettings = reactive({
	relation_id: null,
	llm_model: null,
	voice: null,
	character_setting: null,
});

// 获取角色首字母作为头像
const getRoleInitial = (name) => {
	if (!name) return "?";
	return name.charAt(0).toUpperCase();
};

// 获取当前选择的游戏玩法对象
const getCurrentGamePlayType = () => {
	if (taskForm.game_type) {
		return gamePlayTypes.value.find((item) => item.game_play_type === taskForm.game_type);
	}
	return null;
};

// 获取当前游戏玩法允许的最小人数
const getMinPlayerCount = () => {
	if (taskForm.game_type) {
		const currentGamePlayType = gamePlayTypes.value.find((item) => item.game_play_type === taskForm.game_type);
		if (currentGamePlayType && currentGamePlayType.game_number_min) {
			return currentGamePlayType.game_number_min;
		}
	}
	return 1; // 默认最少1人
};

// 获取当前游戏玩法允许的最大人数
const getMaxPlayerCount = () => {
	if (taskForm.game_type) {
		const currentGamePlayType = gamePlayTypes.value.find((item) => item.game_play_type === taskForm.game_type);
		if (currentGamePlayType && currentGamePlayType.game_number_max) {
			return currentGamePlayType.game_number_max;
		}
	}
	return 100; // 默认最多100人
};

// 验证人数范围是否符合游戏玩法要求
const validatePlayerCountRange = () => {
	// 检查是否必须填写人数
	if (!taskForm.game_number_min || !taskForm.game_number_max) {
		throw new Error("游戏人数设置不能为空");
	}

	// 基本逻辑验证
	if (taskForm.game_number_min > taskForm.game_number_max) {
		throw new Error("最少人数不能大于最多人数");
	}

	if (taskForm.game_number_min < 1) {
		throw new Error("最少人数不能小于1");
	}

	// 如果选择了特定游戏玩法，验证人数范围
	if (taskForm.game_type) {
		// 通过game_type找到对应的游戏玩法
		const currentGamePlayType = gamePlayTypes.value.find((item) => item.game_play_type === taskForm.game_type);

		console.log("当前游戏玩法类型:", taskForm.game_type);
		console.log("找到的游戏玩法:", currentGamePlayType);

		if (currentGamePlayType && (currentGamePlayType.game_number_min || currentGamePlayType.game_number_max)) {
			const minAllowed = currentGamePlayType.game_number_min || 1;
			const maxAllowed = currentGamePlayType.game_number_max || 100;

			console.log(`游戏玩法 ${currentGamePlayType.name} 要求人数范围：${minAllowed}-${maxAllowed}`);
			console.log(`用户设置人数范围：${taskForm.game_number_min}-${taskForm.game_number_max}`);

			// 验证最少人数
			if (taskForm.game_number_min < minAllowed) {
				throw new Error(`最少人数不能小于 ${minAllowed} 人（游戏玩法"${currentGamePlayType.name}"要求）`);
			}

			if (taskForm.game_number_min > maxAllowed) {
				throw new Error(`最少人数不能大于 ${maxAllowed} 人（游戏玩法"${currentGamePlayType.name}"要求）`);
			}

			// 验证最多人数
			if (taskForm.game_number_max < minAllowed) {
				throw new Error(`最多人数不能小于 ${minAllowed} 人（游戏玩法"${currentGamePlayType.name}"要求）`);
			}

			if (taskForm.game_number_max > maxAllowed) {
				throw new Error(`最多人数不能大于 ${maxAllowed} 人（游戏玩法"${currentGamePlayType.name}"要求）`);
			}
		}
	}

	return true;
};

// 验证人数输入
const validatePlayerCount = () => {
	if (taskFormRef.value) {
		// 验证人数字段
		setTimeout(() => {
			taskFormRef.value.validateField(["game_number_min", "game_number_max"], () => {});
		}, 100);
	}
};

// 加载角色数据
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
		console.error("加载角色数据失败", error);
		ElMessage.error("加载角色数据失败");
		availableRoles.value = [];
		availableRolesTotal.value = 0;
	}
};

// 加载任务数据
const loadTask = async () => {
	if (!isEdit.value) return;

	loading.value = true;
	try {
		// 加载任务基本信息
		const taskResponse = await getTaskDetail(Number(taskId.value));
		const taskData = taskResponse;

		// 填充表单
		Object.keys(taskForm).forEach((key) => {
			if (key in taskData) {
				taskForm[key] = taskData[key];
			}
		});

		// 解析时间段
		parseTimePeriod();

		// 如果有游戏玩法ID，则加载相应的游戏玩法Schema
		if (taskData.game_type) {
			// 直接修改游戏玩法Schema，不通过handleGamePlayTypeChange方法触发自动填充
			loadGamePlayTypeSchema(taskData.game_type);

			// 如果有规则数据，设置到表单
			if (taskData.rule_data) {
				ruleFormData.value = JSON.parse(JSON.stringify(taskData.rule_data));
				console.log("已加载规则数据:", ruleFormData.value);
			}
		}

		// 加载任务角色关联
		const relationsResponse = await getTaskRelations(Number(taskId.value));
		roleRelations.value = relationsResponse || [];
	} catch (error) {
		console.error("加载任务数据失败", error);
		ElMessage.error("加载任务数据失败");
	} finally {
		loading.value = false;
	}
};

// 直接加载游戏玩法Schema，不触发自动填充
const loadGamePlayTypeSchema = (gamePlayType) => {
	try {
		// 找到选中的游戏玩法
		const selected = gamePlayTypes.value.find((item) => item.game_play_type === gamePlayType);
		if (!selected) return;

		selectedGamePlayType.value = selected;
		console.log("选中的游戏玩法:", selected);

		// 克隆schema以避免修改原始数据
		const formSchema = selected.form_schema ? JSON.parse(JSON.stringify(selected.form_schema)) : null;

		// 处理schema转换 - 将input类型转换为text类型
		if (formSchema && formSchema.components) {
			formSchema.components.forEach((section) => {
				if (section.fields) {
					section.fields.forEach((field) => {
						// 将"input"类型映射为"text"类型
						if (field.type === "input") {
							field.type = "text";
						}
					});
				}
			});
		}

		// 处理UI Schema - 确保它有正确的结构
		let uiSchema = null;
		if (selected.ui_schema) {
			uiSchema = JSON.parse(JSON.stringify(selected.ui_schema));

			// 确保必要的属性存在
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

		// 处理验证Schema
		let validationSchema = {};

		// 如果是海龟汤类型，添加特定的验证规则
		if (gamePlayType === "turtle_soup") {
			validationSchema = {
				soup: [
					{ required: true, message: "请输入汤面内容", trigger: "blur" },
					{ min: 10, message: "汤面内容至少10个字符", trigger: "blur" },
				],
				answer: [
					{ required: true, message: "请输入汤底内容", trigger: "blur" },
					{ min: 10, message: "汤底内容至少10个字符", trigger: "blur" },
				],
			};
		} else if (selected.validation_schema && selected.validation_schema.rules) {
			// 从原始验证规则中提取
			Object.keys(selected.validation_schema.rules).forEach((fieldName) => {
				if (Array.isArray(selected.validation_schema.rules[fieldName])) {
					validationSchema[fieldName] = [...selected.validation_schema.rules[fieldName]];
				}
			});
		}

		// 设置Schema
		gamePlayTypeSchema.value = formSchema;
		gamePlayTypeUiSchema.value = uiSchema;
		gamePlayTypeValidationSchema.value = validationSchema;
	} catch (error) {
		console.error("加载游戏玩法Schema失败", error);
	}
};

// 返回列表
const goBack = () => {
	if (isFormDirty()) {
		ElMessageBox.confirm("有未保存的修改，确定要离开吗？", "确认", {
			confirmButtonText: "确定",
			cancelButtonText: "取消",
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

// 判断表单是否有修改
const isFormDirty = () => {
	// 简单判断，实际应用可能需要更复杂的比较
	return true;
};

// 保存任务
const saveTask = async () => {
	if (!taskFormRef.value) return;

	await taskFormRef.value.validate(async (valid) => {
		if (!valid) {
			ElMessage.error("请检查表单内容");
			return;
		}

		// 强制验证人数范围
		try {
			validatePlayerCountRange();
		} catch (error: any) {
			ElMessage.error(error.message);
			return;
		}

		// 判断是否需要验证动态表单
		if (taskForm.game_type && gamePlayTypeSchema.value && dynamicFormRef.value) {
			try {
				// 验证动态表单
				const dynamicFormValid = await dynamicFormRef.value.validate();

				if (!dynamicFormValid) {
					ElMessage.error("请检查游戏规则配置表单");
					return;
				}
			} catch (error) {
				console.error("动态表单验证错误", error);
				ElMessage.error("游戏规则配置验证失败");
				return;
			}
		}

		saving.value = true;
		try {
			// 准备提交数据
			const taskData = { ...taskForm } as any; // 使用类型断言允许添加额外属性
			taskData.role_relations = roleRelations.value;

			if (isEdit.value) {
				// 更新任务
				await updateTask(Number(taskId.value), taskData);
				ElMessage.success("任务更新成功");
			} else {
				// 创建任务
				await createTask(taskData);
				ElMessage.success("任务创建成功");
			}

			// 返回列表页
			router.push("/chat/tasks");
		} catch (error) {
			console.error("保存任务失败", error);
			ElMessage.error("保存任务失败");
		} finally {
			saving.value = false;
		}
	});
};

// 加载LLM模型
const loadLLMModels = async () => {
	try {
		const response = await getActiveLLMProviders();
		llmModels.value = response || [];
	} catch (error) {
		console.error("加载LLM模型失败", error);
		ElMessage.error("加载LLM模型失败");
	}
};

// 加载音色数据
const loadVoices = async () => {
	try {
		const response = await listAudioTimbres();
		voices.value = response || [];
	} catch (error) {
		console.error("加载音色数据失败", error);
		ElMessage.error("加载音色数据失败");
	}
};

// 播放音色示例
const playVoice = (base64Audio) => {
	if (!base64Audio) {
		ElMessage.warning("无音频示例");
		return;
	}

	try {
		const audio = new Audio("data:audio/wav;base64," + base64Audio);
		audio.play();
	} catch (error) {
		console.error("播放音频失败", error);
		ElMessage.error("播放音频失败");
	}
};

// 编辑角色设置
const editRoleSettings = (role) => {
	currentRole.value = role;
	roleSettings.relation_id = role.relation_id;
	roleSettings.llm_model = role.llm_model;
	roleSettings.voice = role.voice;
	roleSettings.character_setting = role.character_setting;
	showRoleSettings.value = true;
};

// 保存角色设置
const saveRoleSettings = async () => {
	if (!currentRole.value || !roleSettings.relation_id) return;

	savingRoleSettings.value = true;
	try {
		// 发送请求保存设置
		const data = await updateTaskRelation(roleSettings.relation_id, {
			llm_model: roleSettings.llm_model,
			voice: roleSettings.voice,
			character_setting: roleSettings.character_setting,
		});

		// 更新本地数据
		const index = roleRelations.value.findIndex((r) => r.relation_id === roleSettings.relation_id);
		if (index !== -1) {
			roleRelations.value[index] = {
				...roleRelations.value[index],
				llm_model: data.llm_model,
				voice: data.voice,
				character_setting: data.character_setting,
			};
		}

		ElMessage.success("角色设置保存成功");
		showRoleSettings.value = false;
	} catch (error) {
		console.error("保存角色设置失败", error);
		ElMessage.error("保存角色设置失败");
	} finally {
		savingRoleSettings.value = false;
	}
};

// 角色相关计算属性
const filteredAvailableRoles = computed(() => {
	// 过滤掉已经在roleRelations中的角色
	const existingRoleIds = roleRelations.value.map((r) => r.role_id);
	return availableRoles.value.filter((r) => !existingRoleIds.includes(r.role_id));
});

// 添加选择的角色
const addSelectedRoles = () => {
	if (selectedRoleIds.value.length === 0) {
		ElMessage.warning("请选择角色");
		return;
	}

	// 获取角色详情
	for (const roleId of selectedRoleIds.value) {
		const selectedRole = availableRoles.value.find((r) => r.role_id === roleId);
		if (!selectedRole) continue;

		// 检查是否已经添加
		if (roleRelations.value.some((r) => r.role_id === roleId)) {
			continue; // 跳过已添加的角色
		}

		// 添加角色
		roleRelations.value.push({
			role_id: roleId,
			role_name: selectedRole.name,
			image_url: selectedRole.image_url || null,
			llm_model: selectedRole.llm_choose || null,
			voice: null,
			character_setting: null,
		});
	}

	ElMessage.success(`已添加 ${selectedRoleIds.value.length} 个角色`);

	// 重置表单
	selectedRoleIds.value = [];
	showRoleSelector.value = false;
};

// 从已选择列表中移除角色
const removeSelectedRole = (roleId) => {
	selectedRoleIds.value = selectedRoleIds.value.filter((id) => id !== roleId);
};

// 根据角色ID获取角色详情
const getRoleById = (roleId) => {
	return availableRoles.value.find((r) => r.role_id === roleId);
};

// 移除角色
const removeRole = (index) => {
	roleRelations.value.splice(index, 1);
};

// 更新时间段
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

// 解析时间段
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

// 加载游戏玩法列表
const loadGamePlayTypes = async () => {
	try {
		const response = await getGamePlayTypes({
			skip: 0,
			limit: 100,
		});
		gamePlayTypes.value = response;
		console.log("游戏玩法列表加载成功:", gamePlayTypes.value);
	} catch (error) {
		console.error("加载游戏玩法列表失败", error);
		ElMessage.error("加载游戏玩法列表失败");
	}
};

// 处理游戏玩法选择变化
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
		// 找到选中的游戏玩法
		const selected = gamePlayTypes.value.find((item) => item.game_play_type === value);
		if (!selected) return;

		selectedGamePlayType.value = selected;
		console.log("选中的游戏玩法:", selected);
		console.log("原始验证Schema:", selected.validation_schema);

		// 自动填充相关任务字段
		await autoFillTaskFields(selected);

		// 克隆schema以避免修改原始数据
		const formSchema = selected.form_schema ? JSON.parse(JSON.stringify(selected.form_schema)) : null;

		// 处理schema转换 - 将input类型转换为text类型
		if (formSchema && formSchema.components) {
			formSchema.components.forEach((section) => {
				if (section.fields) {
					section.fields.forEach((field) => {
						// 将"input"类型映射为"text"类型
						if (field.type === "input") {
							field.type = "text";
						}
					});
				}
			});
		}

		// 处理UI Schema - 确保它有正确的结构
		let uiSchema = null;
		if (selected.ui_schema) {
			uiSchema = JSON.parse(JSON.stringify(selected.ui_schema));

			// 确保必要的属性存在
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

		// 处理验证Schema
		let validationSchema = {};

		// 如果是海龟汤类型，添加特定的验证规则
		if (value === "turtle_soup") {
			validationSchema = {
				soup: [
					{ required: true, message: "请输入汤面内容", trigger: "blur" },
					{ min: 10, message: "汤面内容至少10个字符", trigger: "blur" },
				],
				answer: [
					{ required: true, message: "请输入汤底内容", trigger: "blur" },
					{ min: 10, message: "汤底内容至少10个字符", trigger: "blur" },
				],
			};
		} else if (selected.validation_schema && selected.validation_schema.rules) {
			// 从原始验证规则中提取
			Object.keys(selected.validation_schema.rules).forEach((fieldName) => {
				if (Array.isArray(selected.validation_schema.rules[fieldName])) {
					validationSchema[fieldName] = [...selected.validation_schema.rules[fieldName]];
				}
			});
		}

		console.log("处理后的验证Schema:", validationSchema);

		// 设置Schema
		gamePlayTypeSchema.value = formSchema;
		gamePlayTypeUiSchema.value = uiSchema;
		gamePlayTypeValidationSchema.value = validationSchema;

		// 确认最终设置的验证Schema
		console.log("最终设置的验证Schema:", gamePlayTypeValidationSchema.value);

		// 如果是编辑模式且有已保存的规则数据，则使用它初始化表单
		if (isEdit.value && taskForm.rule_data) {
			ruleFormData.value = JSON.parse(JSON.stringify(taskForm.rule_data));
		} else {
			// 否则初始化为空对象
			ruleFormData.value = {};
		}

		console.log("设置游戏玩法Schema:", {
			schema: gamePlayTypeSchema.value,
			uiSchema: gamePlayTypeUiSchema.value,
			validationSchema: gamePlayTypeValidationSchema.value,
		});

		// 强制组件重新渲染
		nextTick(() => {
			const timestamp = Date.now();
			console.log(`触发组件重新渲染 timestamp=${timestamp}`);
		});
	} catch (error) {
		console.error("处理游戏玩法选择变化失败", error);
		ElMessage.error("处理游戏玩法选择变化失败");
	}
};

// 自动填充任务字段
const autoFillTaskFields = async (selectedGamePlay) => {
	// 需要填充的字段映射
	const fieldMappings = {
		name: "title",
		description: "description",
		setting: "setting",
		reference_case: "reference_case",
		player_count: "player_count", // 这个需要特殊处理
	};

	// 检查是否有非空字段
	const hasNonEmptyFields = Object.keys(fieldMappings).some((key) => {
		const targetField = fieldMappings[key] === "player_count" ? "game_number_min" : fieldMappings[key];
		return taskForm[targetField] !== undefined && taskForm[targetField] !== null && taskForm[targetField] !== "";
	});

	// 如果有非空字段，提示用户是否覆盖
	if (hasNonEmptyFields) {
		try {
			await ElMessageBox.confirm("检测到已有字段内容，是否用所选游戏玩法覆盖相关字段？", "确认覆盖", {
				confirmButtonText: "确定覆盖",
				cancelButtonText: "保留现有内容",
				type: "warning",
			});
			// 用户确认覆盖，执行下面的填充逻辑
		} catch (error) {
			// 用户取消覆盖，直接返回
			console.log("用户取消字段覆盖");
			return;
		}
	}

	// 填充字段
	Object.keys(fieldMappings).forEach((sourceKey) => {
		const targetField = fieldMappings[sourceKey];
		if (selectedGamePlay[sourceKey] !== undefined) {
			// 处理特殊字段
			if (sourceKey === "player_count" && selectedGamePlay[sourceKey]) {
				// 处理玩家数量格式，例如 "3-4" 格式
				const playerCount = selectedGamePlay[sourceKey];
				const matches = playerCount.match(/(\d+)-(\d+)/);
				if (matches && matches.length === 3) {
					taskForm.game_number_min = parseInt(matches[1]);
					taskForm.game_number_max = parseInt(matches[2]);
				} else if (!isNaN(parseInt(playerCount))) {
					// 如果是单个数字
					taskForm.game_number_min = parseInt(playerCount);
					taskForm.game_number_max = parseInt(playerCount);
				}
			} else {
				// 常规字段直接赋值
				taskForm[targetField] = selectedGamePlay[sourceKey];
			}
		}
	});

	// 设置难度等级（如果没有）
	if (!taskForm.difficulty) {
		// 可以根据游戏玩法类型为不同游戏设置不同的默认难度
		switch (selectedGamePlay.game_play_type) {
			case "turtle_soup":
				taskForm.difficulty = "中等";
				break;
			default:
				taskForm.difficulty = "简单";
				break;
		}
	}

	// 设置用户等级要求（如果没有）
	if (!taskForm.required_user_level) {
		taskForm.required_user_level = 1;
	}

	// 根据游戏类型设置任务类型（如果没有）
	if (!taskForm.task_type) {
		// 根据游戏玩法类型来设置默认的任务类型
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

	// 设置默认时间段（如果没有）
	if (!taskForm.time_period) {
		taskForm.time_period = "19:00-22:00";
		// 更新时间选择器的值
		const startDate = new Date();
		startDate.setHours(19, 0, 0);
		const endDate = new Date();
		endDate.setHours(22, 0, 0);
		timeRange.value = [startDate, endDate];
	}

	ElMessage.success("已自动填充相关任务字段");
};

// 更新规则表单数据
const updateRuleFormData = (data) => {
	ruleFormData.value = data;
	console.log("规则表单数据更新:", ruleFormData.value);
	// 同步更新到任务表单
	taskForm.rule_data = JSON.parse(JSON.stringify(ruleFormData.value));
};

// 处理动态表单验证
const handleValidation = (result) => {
	console.log("动态表单验证结果:", result);
	if (!result.valid) {
		// 错误信息已经在组件内部处理
		console.warn("动态表单验证失败，错误:", result.errors);
	}
};

// 组件挂载时执行
onMounted(() => {
	loadRoles();
	loadGamePlayTypes(); // 加载游戏玩法列表
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

/* 添加动画效果 */
.role-item {
	transition: all 0.3s ease;
}

.role-item:hover {
	transform: translateY(-5px);
	box-shadow: 0 8px 15px rgba(0, 0, 0, 0.3);
}

/* 响应式调整 */
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

/* 修改多选下拉框样式 */
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

/* 游戏玩法下拉框样式 */
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

/* 游戏规则表单样式 */
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

@import '@/layouts/WriterLayout/css/extra.scss';

.btn-fix {
	color: #fff;
	background-color: $btn-bg-color0;
	border-color: $btn-bg-color0;
	
	&:hover {
		background-color: $btn-bg-hover-color0;
		border-color: $btn-bg-hover-color0;
	}
}
</style>
