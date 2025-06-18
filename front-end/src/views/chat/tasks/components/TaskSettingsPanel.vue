<template>
	<div class="settings-container">
		<el-card class="settings-card">
			<template #header>
				<div class="card-header">
					<span>User Settings</span>
					<el-button type="primary" @click="handleStartChat"> Start Chat</el-button>
				</div>
			</template>

			<div class="settings-form">
				<!-- User Settings -->
				<div class="setting-section">
					<div class="section-title">Basic Information</div>
					<div class="form-group">
						<label for="userName">Username</label>
						<el-input v-model="userInfo.name" placeholder="Enter your name" />
					</div>
					<div class="form-group">
						<label for="userBackground">Background Setting</label>
						<el-input
							type="textarea"
							v-model="userInfo.background"
							:rows="3"
							placeholder="Describe your identity background, such as profession, experience, etc."
						/>
					</div>
				</div>

				<!-- Character Selection -->
				<div class="setting-section">
					<div class="section-title">Character Selection</div>
					<div class="role-selection">
						<p class="selection-hint">Select characters you want to chat with (multiple selection allowed)</p>
						<p v-if="minPlayers > 0 || maxPlayers > 0" class="player-limit-hint">
							Player limit: {{ minPlayers === maxPlayers ? `${minPlayers} player` : `${minPlayers}-${maxPlayers} players` }}
						</p>

						<div v-if="loading" class="loading-roles">
							<el-skeleton :rows="3" animated />
						</div>

						<div v-else-if="taskRoles.length === 0" class="no-roles">
							<el-empty description="No available characters" />
						</div>

						<div v-else class="role-cards">
							<div
								v-for="role in taskRoles"
								:key="role.role_id"
								class="role-card"
								:class="{ active: selectedRoleIds.includes(role.role_id) }"
								@click="toggleRoleSelection(role)"
							>
								<div class="role-avatar">
									<img v-if="role.image_url" :src="role.image_url" :alt="role.role_name || 'Character'" />
									<span v-else>{{ (role.role_name || "?").charAt(0) }}</span>
								</div>
								<div class="role-info">
									<div class="role-name">{{ role.role_name || "Unnamed Character" }}</div>
									<div class="role-description">{{ role.description || "No description" }}</div>
								</div>
								<div class="selection-indicator">
									<el-icon v-if="selectedRoleIds.includes(role.role_id)">
										<Check />
									</el-icon>
								</div>
							</div>
						</div>

						<div v-if="taskRoles.length > 0" class="selected-roles-summary">
							Selected: {{ selectedRoleIds.length }} character(s)
						</div>
					</div>
				</div>

				<!-- Game Question Type Configuration - Only displayed when game type exists -->
				<div class="setting-section" v-if="gameType">
					<div class="section-title">Question Generation Configuration</div>
					<div class="game-config">
						<div class="form-group">
							<label for="questionType">Question Type</label>
							<el-select
								v-model="questionType"
								placeholder="Please select question type"
								@change="$emit('update:question-type', questionType)"
							>
								<el-option
									v-for="item in createQuestionType"
									:key="item.value"
									:label="item.lable"
									:value="item.value"
								/>
							</el-select>
						</div>
					</div>
				</div>

				<!-- Task Information -->
				<div class="setting-section">
					<div class="section-title">Task Description</div>
					<div class="task-description">
						<p>{{ taskInfo.description }}</p>
						<p class="task-note">After connecting, the conversation will start based on the information returned by the server. You can switch between different characters at any time.</p>
					</div>
					<div class="task-meta-info">
						<div class="meta-item">
							<label>Task Difficulty</label>
							<span :class="['difficulty-tag', `difficulty-${taskInfo.difficulty.toLowerCase()}`]">
								{{ taskInfo.difficulty }}
							</span>
						</div>
						<div class="meta-item">
							<label>Maximum Conversation Rounds</label>
							<div class="dialogue-rounds">
								{{ taskInfo.maxRounds === -1 ? "Unlimited" : `${taskInfo.maxRounds} Rounds` }}
							</div>
						</div>
						<div class="meta-item" v-if="gameType">
							<label>Game Type</label>
							<div class="game-type">
								{{ gameType }}
							</div>
						</div>
					</div>
				</div>
			</div>
		</el-card>
	</div>
</template>

<script setup lang="ts">
/**
 * Task Settings Panel Component
 * @description Used to set task-related parameters
 */
import { ref, computed, defineProps, defineEmits, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { Check } from "@element-plus/icons-vue";
import { getTaskRelations } from "@/api/task";
import { getGameRelations } from "@/api/gamePlayType";
import { getConfig_value } from "@/api/system";

// Define task information type
interface TaskInfo {
	title: string;
	description: string;
	difficulty: string;
	maxRounds: number;
}

// Define user information type
interface UserInfo {
	name: string;
	background: string;
}

// Define AI information type
interface AiInfo {
	name: string;
	role: string;
	background: string;
}

// Define character type
interface TaskRole {
	role_id: string;
	role_name?: string;
	image_url?: string;
	description?: string;
	character_level?: string;
}

const props = defineProps({
	/** Task information */
	taskInfo: {
		type: Object as () => TaskInfo,
		required: true,
	},
	/** User information */
	userInfo: {
		type: Object as () => UserInfo,
		required: true,
	},
	/** AI information */
	aiInfo: {
		type: Object as () => AiInfo,
		required: true,
	},
	/** Task ID */
	taskId: {
		type: [Number, String],
		required: true,
	},
	/** Game type - Only valid for gameplay types */
	gameType: {
		type: String,
		default: "",
	},
	/** Minimum number of players */
	minPlayers: {
		type: Number,
		default: 0,
	},
	/** Maximum number of players */
	maxPlayers: {
		type: Number,
		default: 0,
	},
});

const emit = defineEmits(["start-chat", "select-roles", "update:question-type"]);

// Character related
const taskRoles = ref<TaskRole[]>([]);
const selectedRoleIds = ref<string[]>([]);
const loading = ref(false);
// Question generation type
const questionType = ref("Simple");

// Load characters associated with the task
const loadTaskRoles = async () => {
	loading.value = true;
	try {
		let relations = [];
		if (props.gameType) {
			relations = await getGameRelations(Number(props.taskId));
		} else {
			relations = await getTaskRelations(Number(props.taskId));
		}
		if (relations && relations.length > 0) {
			taskRoles.value = relations.map((role) => ({
				role_id: role.role_id,
				role_name: role.role_name,
				image_url: role.image_url,
				description: role.character_setting,
				character_level: role.character_level,
			}));

			// Default select the first character
			if (taskRoles.value.length > 0 && selectedRoleIds.value.length === 0) {
				toggleRoleSelection(taskRoles.value[0]);
			}
		} else {
			taskRoles.value = [];
		}
	} catch (error) {
		console.error("Failed to load task characters", error);
		ElMessage.error("Failed to load task characters");
	} finally {
		loading.value = false;
	}
};

// Toggle character selection status
const toggleRoleSelection = (role: TaskRole) => {
	const index = selectedRoleIds.value.indexOf(role.role_id);
	if (index === -1) {
		// Add to selection list
		selectedRoleIds.value.push(role.role_id);
	} else {
		// Remove from selection list
		selectedRoleIds.value.splice(index, 1);
	}

	// Notify parent component of selection change
	emit("select-roles", getSelectedRoles());
};

// Get complete information of selected characters
const getSelectedRoles = () => {
	return selectedRoleIds.value.map((roleId) => {
		const roleInfo = taskRoles.value.find((r) => r.role_id === roleId);
		return {
			role_id: roleId,
			role_name: roleInfo?.role_name || "",
			image_url: roleInfo?.image_url || "",
			description: roleInfo?.description || "",
			character_level: roleInfo?.character_level || "",
		};
	});
};

/**
 * Form validation
 */
const isFormValid = computed(() => {
	// Basic validation: username and character selection
	const basicValid = props.userInfo.name.trim() !== "" && selectedRoleIds.value.length > 0;

	// Player count validation: check if minimum and maximum player requirements are met
	const minPlayersValid = props.minPlayers === 0 || selectedRoleIds.value.length >= props.minPlayers;
	const maxPlayersValid = props.maxPlayers === 0 || selectedRoleIds.value.length <= props.maxPlayers;
	const playersValid = minPlayersValid && maxPlayersValid;

	return basicValid && playersValid;
});

/**
 * Handle start chat button click
 */
const handleStartChat = () => {
	// Check username
	if (!props.userInfo.name.trim()) {
		ElMessage.warning("Please enter your name");
		return;
	}

	// Check character selection
	if (selectedRoleIds.value.length === 0) {
		ElMessage.warning("Please select at least one character");
		return;
	}

	// Check minimum player requirement
	if (props.minPlayers > 0 && selectedRoleIds.value.length < props.minPlayers) {
		ElMessage.warning(`Game requires at least ${props.minPlayers} characters to participate`);
		return;
	}

	// Check maximum player limit
	if (props.maxPlayers > 0 && selectedRoleIds.value.length > props.maxPlayers) {
		ElMessage.warning(`Game allows maximum ${props.maxPlayers} characters to participate`);
		return;
	}

	// All validations passed, emit start-chat event
	emit("start-chat");
};
const createQuestionType = ref([]);
function getConfig() {
	getConfig_value("WEB_CREATE_QUESTION").then((res) => {
		createQuestionType.value = JSON.parse(res.config_value);
	});
}
// Load characters when component is mounted
onMounted(() => {
	loadTaskRoles();
	getConfig();
});
</script>

<style lang="scss" scoped>
.el-input,
.el-textarea {
	color: white;
}
.settings-container {
	flex: 1;
	padding: 2rem;
	overflow-y: auto;
	background-color: rgba(18, 18, 24, 0.7);

	.settings-card {
		max-width: 900px;
		margin: 0 auto;
		background-color: #1a1a2e;
		border-radius: 8px;
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
		border: 1px solid rgba(78, 143, 255, 0.15);
		overflow: hidden;

		.card-header {
			display: flex;
			justify-content: space-between;
			align-items: center;
			padding: 1rem;
			background: linear-gradient(to right, #0d253f, #16213e);
			font-size: 1.2rem;
			color: #fff;
		}
	}

	.settings-form {
		padding: 1.5rem;

		.setting-section {
			margin-bottom: 2rem;
			padding-bottom: 1.5rem;
			border-bottom: 1px solid rgba(255, 255, 255, 0.1);

			&:last-child {
				border-bottom: none;
				margin-bottom: 0;
			}

			.section-title {
				font-size: 1.1rem;
				color: #4da6ff;
				margin-bottom: 1.2rem;
				position: relative;

				&::after {
					content: "";
					position: absolute;
					bottom: -5px;
					left: 0;
					width: 50px;
					height: 2px;
					background: linear-gradient(to right, #5e72e4, #00c6ff);
				}
			}
		}

		.form-group {
			margin-bottom: 1.2rem;

			label {
				display: block;
				margin-bottom: 0.5rem;
				color: #b0b0b0;
				font-size: 0.9rem;
			}

			:deep(.el-input__inner),
			:deep(.el-textarea__inner) {
				background-color: rgba(30, 30, 50, 0.7);
				border: 1px solid rgba(100, 100, 255, 0.2);
				color: #e0e0e0;
			}
		}

		.task-description {
			background-color: rgba(30, 30, 50, 0.5);
			padding: 1rem;
			border-radius: 6px;
			margin-bottom: 1rem;
			color: #d0d0d0;
			line-height: 1.5;

			.task-note {
				margin-top: 1rem;
				font-style: italic;
				color: #4da6ff;
				font-size: 0.9rem;
			}
		}

		.task-meta-info {
			display: flex;
			gap: 1.5rem;
			margin-top: 1rem;

			.meta-item {
				display: flex;
				flex-direction: column;
				gap: 0.5rem;

				label {
					color: #b0b0b0;
					font-size: 0.8rem;
				}

				.difficulty-tag {
					display: inline-block;
					padding: 2px 8px;
					border-radius: 4px;
					font-size: 0.8rem;
					text-align: center;

					&.difficulty-Simple {
						background-color: rgba(76, 175, 80, 0.2);
						color: #66bb6a;
					}

					&.difficulty-Medium {
						background-color: rgba(255, 152, 0, 0.2);
						color: #ffa726;
					}

					&.difficulty-Hard {
						background-color: rgba(244, 67, 54, 0.2);
						color: #ef5350;
					}
				}

				.dialogue-rounds {
					font-size: 0.9rem;
					color: #e0e0e0;
				}
			}
		}
	}

	// 角色选择样式
	.role-selection {
		margin-top: 0.5rem;

		.selection-hint {
			color: #a0a0a0;
			font-size: 0.9rem;
			margin-bottom: 1rem;
		}

		.player-limit-hint {
			color: #ff9800;
			font-size: 0.9rem;
			margin-bottom: 1rem;
			padding: 5px 10px;
			background-color: rgba(255, 152, 0, 0.1);
			border-left: 3px solid #ff9800;
			border-radius: 3px;
		}

		.role-cards {
			display: grid;
			grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
			gap: 1rem;
			margin-bottom: 1rem;

			.role-card {
				display: flex;
				padding: 1rem;
				background-color: rgba(30, 30, 50, 0.5);
				border: 1px solid rgba(100, 100, 255, 0.1);
				border-radius: 8px;
				cursor: pointer;
				transition: all 0.2s ease;
				position: relative;

				&:hover {
					background-color: rgba(40, 40, 70, 0.5);
					border-color: rgba(100, 100, 255, 0.3);
				}

				&.active {
					background-color: rgba(50, 50, 100, 0.5);
					border-color: rgba(100, 100, 255, 0.5);
					box-shadow: 0 0 10px rgba(100, 100, 255, 0.2);
				}

				.role-avatar {
					width: 60px;
					height: 60px;
					border-radius: 50%;
					background: linear-gradient(135deg, #4da6ff, #5e72e4);
					color: #fff;
					display: flex;
					align-items: center;
					justify-content: center;
					font-size: 1.5rem;
					font-weight: bold;
					margin-right: 1rem;
					flex-shrink: 0;

					img {
						width: 100%;
						height: 100%;
						border-radius: 50%;
						object-fit: cover;
					}
				}

				.role-info {
					flex: 1;

					.role-name {
						font-weight: 600;
						font-size: 1rem;
						color: #e0e0e0;
						margin-bottom: 0.5rem;
					}

					.role-description {
						font-size: 0.85rem;
						color: #a0a0a0;
						display: -webkit-box;
						-webkit-line-clamp: 2;
						-webkit-box-orient: vertical;
						overflow: hidden;
					}
				}

				.selection-indicator {
					position: absolute;
					top: 10px;
					right: 10px;
					color: #4da6ff;
					font-size: 1.2rem;
				}
			}
		}

		.selected-roles-summary {
			font-size: 0.9rem;
			color: #4da6ff;
			text-align: right;
			padding: 0.5rem 0;
		}

		.loading-roles,
		.no-roles {
			padding: 1rem;
			background-color: rgba(30, 30, 50, 0.5);
			border-radius: 8px;
			margin-bottom: 1rem;
		}
	}

	// 游戏配置区域样式
	.game-config {
		background-color: rgba(30, 30, 50, 0.5);
		padding: 1rem;
		border-radius: 8px;
		margin-bottom: 1rem;

		.el-select {
			width: 100%;
		}

		:deep(.el-select .el-input__inner) {
			background-color: rgba(40, 40, 70, 0.7);
			border-color: rgba(100, 100, 255, 0.3);
		}

		:deep(.el-select .el-input__inner:hover) {
			border-color: rgba(100, 100, 255, 0.5);
		}

		:deep(.el-select .el-input__inner:focus) {
			border-color: #4da6ff;
		}
	}
}
</style>
