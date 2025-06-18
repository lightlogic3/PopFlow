<template>
	<div class="settings-container">
		<el-card class="settings-card">
			<template #header>
				<div class="card-header">
					<span>用户设置</span>
					<el-button type="primary" @click="handleStartChat" :disabled="!isFormValid"> 开始聊天</el-button>
				</div>
			</template>

			<div class="settings-form">
				<!-- 用户设置 -->
				<div class="setting-section">
					<div class="section-title">基本信息</div>
					<div class="form-group">
						<label for="userName">用户名称</label>
						<el-input v-model="userInfo.name" placeholder="输入你的名称" />
					</div>
					<div class="form-group">
						<label for="userBackground">背景设定</label>
						<el-input
							type="textarea"
							v-model="userInfo.background"
							:rows="3"
							placeholder="描述你的身份背景，例如职业、经历等"
						/>
					</div>
				</div>

				<!-- 角色选择 -->
				<div class="setting-section">
					<div class="section-title">角色选择</div>
					<div class="role-selection">
						<p class="selection-hint">选择想要对话的角色（可多选）</p>
						<p v-if="minPlayers > 0 || maxPlayers > 0" class="player-limit-hint">
							游戏人数限制: {{ minPlayers === maxPlayers ? `${minPlayers}人` : `${minPlayers}-${maxPlayers}人` }}
						</p>

						<div v-if="loading" class="loading-roles">
							<el-skeleton :rows="3" animated />
						</div>

						<div v-else-if="taskRoles.length === 0" class="no-roles">
							<el-empty description="暂无可选角色" />
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
									<img v-if="role.image_url" :src="role.image_url" :alt="role.role_name || '角色'" />
									<span v-else>{{ (role.role_name || "?").charAt(0) }}</span>
								</div>
								<div class="role-info">
									<div class="role-name">{{ role.role_name || "未命名角色" }}</div>
									<div class="role-description">{{ role.description || "暂无描述" }}</div>
								</div>
								<div class="selection-indicator">
									<el-icon v-if="selectedRoleIds.includes(role.role_id)">
										<Check />
									</el-icon>
								</div>
							</div>
						</div>

						<div v-if="taskRoles.length > 0" class="selected-roles-summary">
							已选择: {{ selectedRoleIds.length }} 个角色
						</div>
					</div>
				</div>

				<!-- 游戏题目类型配置 - 仅在游戏类型存在时显示 -->
				<div class="setting-section" v-if="gameType">
					<div class="section-title">生成题目配置</div>
					<div class="game-config">
						<div class="form-group">
							<label for="questionType">生成题目类型</label>
							<el-select
								v-model="questionType"
								placeholder="请选择题目类型"
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

				<!-- 任务信息 -->
				<div class="setting-section">
					<div class="section-title">任务说明</div>
					<div class="task-description">
						<p>{{ taskInfo.description }}</p>
						<p class="task-note">连接后将根据服务器返回的信息开始对话，您可以随时切换与不同角色的对话。</p>
					</div>
					<div class="task-meta-info">
						<div class="meta-item">
							<label>任务难度</label>
							<span :class="['difficulty-tag', `difficulty-${taskInfo.difficulty.toLowerCase()}`]">
								{{ taskInfo.difficulty }}
							</span>
						</div>
						<div class="meta-item">
							<label>最大对话轮数</label>
							<div class="dialogue-rounds">
								{{ taskInfo.maxRounds === -1 ? "无限制" : `${taskInfo.maxRounds} 轮` }}
							</div>
						</div>
						<div class="meta-item" v-if="gameType">
							<label>游戏类型</label>
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
 * 任务设置面板组件
 * @description 用于设置任务相关参数
 */
import { ref, computed, defineProps, defineEmits, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { Check } from "@element-plus/icons-vue";
import { getTaskRelations } from "@/api/task";
import { getGameRelations } from "@/api/gamePlayType";
import { getConfig_value } from "@/api/system";

// 定义任务信息类型
interface TaskInfo {
	title: string;
	description: string;
	difficulty: string;
	maxRounds: number;
}

// 定义用户信息类型
interface UserInfo {
	name: string;
	background: string;
}

// 定义AI信息类型
interface AiInfo {
	name: string;
	role: string;
	background: string;
}

// 定义角色类型
interface TaskRole {
	role_id: string;
	role_name?: string;
	image_url?: string;
	description?: string;
	character_level?: string;
}

const props = defineProps({
	/** 任务信息 */
	taskInfo: {
		type: Object as () => TaskInfo,
		required: true,
	},
	/** 用户信息 */
	userInfo: {
		type: Object as () => UserInfo,
		required: true,
	},
	/** AI信息 */
	aiInfo: {
		type: Object as () => AiInfo,
		required: true,
	},
	/** 任务ID */
	taskId: {
		type: [Number, String],
		required: true,
	},
	/** 游戏类型 - 仅对游戏玩法有效 */
	gameType: {
		type: String,
		default: "",
	},
	/** 游戏最小人数 */
	minPlayers: {
		type: Number,
		default: 0,
	},
	/** 游戏最大人数 */
	maxPlayers: {
		type: Number,
		default: 0,
	},
});

const emit = defineEmits(["start-chat", "select-roles", "update:question-type"]);

// 角色相关
const taskRoles = ref<TaskRole[]>([]);
const selectedRoleIds = ref<string[]>([]);
const loading = ref(false);
// 生成题目类型
const questionType = ref("简单");

// 加载任务关联的角色
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

			// 默认选择第一个角色
			if (taskRoles.value.length > 0 && selectedRoleIds.value.length === 0) {
				toggleRoleSelection(taskRoles.value[0]);
			}
		} else {
			taskRoles.value = [];
		}
	} catch (error) {
		console.error("加载任务角色失败", error);
		ElMessage.error("加载任务角色失败");
	} finally {
		loading.value = false;
	}
};

// 切换角色选择状态
const toggleRoleSelection = (role: TaskRole) => {
	const index = selectedRoleIds.value.indexOf(role.role_id);
	if (index === -1) {
		// 添加到选择列表
		selectedRoleIds.value.push(role.role_id);
	} else {
		// 从选择列表中移除
		selectedRoleIds.value.splice(index, 1);
	}

	// 通知父组件选择变化
	emit("select-roles", getSelectedRoles());
};

// 获取已选择的角色完整信息
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
 * 表单验证
 */
const isFormValid = computed(() => {
	// 基本验证：用户名和选择了角色
	const basicValid = props.userInfo.name.trim() !== "" && selectedRoleIds.value.length > 0;

	// 人数验证：检查是否满足最小人数要求
	const playersValid = props.minPlayers === 0 || selectedRoleIds.value.length >= props.minPlayers;

	return basicValid && playersValid;
});

/**
 * 处理开始聊天按钮点击
 */
const handleStartChat = () => {
	if (!props.userInfo.name.trim()) {
		ElMessage.warning("请输入您的名称");
		return;
	}

	if (selectedRoleIds.value.length === 0) {
		ElMessage.warning("请至少选择一个角色");
		return;
	}

	// 检查最小人数要求
	if (props.minPlayers > 0 && selectedRoleIds.value.length < props.minPlayers) {
		ElMessage.warning(`游戏要求至少选择 ${props.minPlayers} 个角色参与`);
		return;
	}

	// 检查最大人数限制
	if (props.maxPlayers > 0 && selectedRoleIds.value.length > props.maxPlayers) {
		ElMessage.warning(`游戏最多允许 ${props.maxPlayers} 个角色参与`);
		return;
	}

	if (isFormValid.value) {
		emit("start-chat");
	}
};
const createQuestionType = ref([]);
function getConfig() {
	getConfig_value("WEB_CREATE_QUESTION").then((res) => {
		createQuestionType.value = JSON.parse(res.config_value);
	});
}
// 组件挂载时加载角色
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

					&.difficulty-简单 {
						background-color: rgba(76, 175, 80, 0.2);
						color: #66bb6a;
					}

					&.difficulty-中等 {
						background-color: rgba(255, 152, 0, 0.2);
						color: #ffa726;
					}

					&.difficulty-困难 {
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
