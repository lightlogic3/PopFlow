<template>
	<div class="task-chat-container">
		<!-- 任务头部 -->
		<task-header
			:title="taskSettings.taskInfo.title"
			:description="taskSettings.taskInfo.description"
			:is-started="chatState.isStarted"
			@go-back="goBack"
		>
			<!-- 添加结束游戏按钮 -->
			<el-button v-if="chatState.isStarted" type="danger" size="small" class="end-game-btn" @click="endGame">
				End Game
			</el-button>
		</task-header>

		<!-- 设置和聊天区域 -->
		<div class="main-content">
			<!-- 设置面板 - 未开始聊天时显示 -->
			<task-settings-panel
				v-if="!chatState.isStarted"
				:task-info="taskSettings.taskInfo"
				:user-info="taskSettings.userInfo"
				:ai-info="taskSettings.aiInfo"
				:data="taskSettings.data"
				:task-id="taskId"
				:game-type="(sourceType === 'gamePlayType' ? gamePlayType : '') + ''"
				:min-players="taskSettings.minPlayers"
				:max-players="taskSettings.maxPlayers"
				@start-chat="startChat"
				@select-roles="handleSelectRoles"
				@update:question-type="questionType = $event"
			/>

			<!-- 聊天面板 - 开始聊天后显示 -->
			<chat-container
				v-else
				:user-info="taskSettings.userInfo"
				:ai-info="taskSettings.aiInfo"
				:current-round="chatState.currentRound"
				:max-rounds="chatState.maxRounds"
				:messages="chatState.messages"
				:is-loading="chatState.isLoading"
				:is-ai-typing="chatState.isAiTyping"
				:user-input="chatState.userInput"
				:characters="taskRoles"
				:current-role-id="currentRoleId"
				:soup-surface="gameState.soupSurface"
				:usage-state="usageState"
				@update:user-input="chatState.userInput = $event"
				@send-message="sendMessage"
				@select-character="switchRole"
			/>
		</div>

		<!-- 连接状态指示器 -->
		<div class="status-indicator" :class="{ active: wsClient && wsClient.isConnected() }">
			{{ getConnectionStatus() }}
		</div>
	</div>
</template>

<script setup lang="ts">
/**
 * 任务聊天页面
 * @description 任务对话页面，包含任务信息、用户设置和聊天界面
 */
import { ref, reactive, onMounted, computed, onBeforeUnmount } from "vue";
import { useRouter, useRoute } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";

import { getTaskDetail } from "@/api/task";
import { getGamePlayType } from "@/api/gamePlayType";
import { WebSocketClient } from "@/utils/websocket";
import wsAPI from "@/api/websocket";

// 导入子组件
import TaskHeader from "./components/TaskHeader.vue";
import TaskSettingsPanel from "./components/TaskSettingsPanel.vue";
import ChatContainer from "./components/ChatContainer.vue";

const router = useRouter();
const route = useRoute();
const taskId = computed(() => Number(route.params.id));
const loading = ref(false);
const wsClient = ref<WebSocketClient | null>(null);
const sessionId = ref("");

// 来源类型：'task' 或 'gamePlayType'
const sourceType = ref(route.query.source || "task");
// 游戏玩法类型（仅当来源是gamePlayType时有效）
const gamePlayType = ref(route.query.gameType || "");
// 题目类型配置
const questionType = ref("standard");

// 任务设置（整合所有数据）
const taskSettings = reactive({
	taskInfo: {
		title: "",
		description: "",
		maxRounds: -1,
		difficulty: "中等",
	},
	userInfo: {
		name: localStorage.getItem("playerName") || "",
		background: "",
	},
	data: {
		question_type: "",
	},
	aiInfo: {
		name: "AI Assistant",
		role: "Task Helper",
		background: "",
		image: "",
	},
	minPlayers: 0,
	maxPlayers: 0,
});

// 聊天状态
const chatState = reactive({
	isStarted: false,
	isLoading: false,
	isAiTyping: false,
	userInput: "",
	currentRound: 0,
	maxRounds: -1,
	messages: [],
});

// 游戏状态（海龟汤特有）
const gameState = reactive({
	soupSurface: "", // 汤面信息
	hasGameStarted: false, // 游戏是否已开始（接收到汤面）
});

// 使用统计状态
const usageState = reactive({
	totalInputTokens: 0, // 累计输入token
	totalOutputTokens: 0, // 累计输出token
	totalTokens: 0, // 累计总token
	totalPrice: 0, // 累计价格
});

// 角色列表
const taskRoles = ref([]);
// 当前选中的角色
const currentRoleId = ref("");

// 修改为支持多选的角色ID数组
const selectedRoleIds = ref<string[]>([]);
const selectedRoles = ref<any[]>([]);

/**
 * 生成随机会话ID
 */
const generateSessionId = () => {
	// 检查localStorage中是否已有会话ID
	const storedSessionId = localStorage.getItem(`game_session_${taskId.value}`);

	if (storedSessionId) {
		// 使用已存储的会话ID
		sessionId.value = storedSessionId;
	} else {
		// 生成新的会话ID
		const uuid = "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
			const r = (Math.random() * 16) | 0,
				v = c === "x" ? r : (r & 0x3) | 0x8;
			return v.toString(16);
		});
		sessionId.value = uuid;

		// 存储会话ID到localStorage
		localStorage.setItem(`game_session_${taskId.value}`, uuid);
	}
};

/**
 * 保存汤面信息到缓存
 */
const saveSoupToCache = (soupContent: string) => {
	localStorage.setItem(`soup_surface_${taskId.value}`, soupContent);
	console.log(`已缓存汤面信息到: soup_surface_${taskId.value}`);
};

/**
 * 从缓存加载汤面信息
 */
const loadSoupFromCache = () => {
	const cachedSoup = localStorage.getItem(`soup_surface_${taskId.value}`);
	if (cachedSoup) {
		gameState.soupSurface = cachedSoup;
		gameState.hasGameStarted = true;
		console.log("从缓存加载汤面信息:", cachedSoup);
		return true;
	}
	return false;
};

/**
 * 保存usage统计到缓存
 */
const saveUsageToCache = () => {
	const usageData = {
		totalInputTokens: usageState.totalInputTokens,
		totalOutputTokens: usageState.totalOutputTokens,
		totalTokens: usageState.totalTokens,
		totalPrice: usageState.totalPrice,
	};
	localStorage.setItem(`usage_stats_${taskId.value}`, JSON.stringify(usageData));
	console.log("已缓存usage统计:", usageData);
};

/**
 * 从缓存加载usage统计
 */
const loadUsageFromCache = () => {
	const cachedUsage = localStorage.getItem(`usage_stats_${taskId.value}`);
	if (cachedUsage) {
		try {
			const usageData = JSON.parse(cachedUsage);
			usageState.totalInputTokens = usageData.totalInputTokens || 0;
			usageState.totalOutputTokens = usageData.totalOutputTokens || 0;
			usageState.totalTokens = usageData.totalTokens || 0;
			usageState.totalPrice = usageData.totalPrice || 0;
			console.log("从缓存加载usage统计:", usageData);
			return true;
		} catch (error) {
			console.error("解析usage缓存失败:", error);
		}
	}
	return false;
};

/**
 * 累加usage统计
 */
const addUsage = (usage: any) => {
	if (!usage) return;

	const inputTokens = usage.input_tokens || 0;
	const outputTokens = usage.output_tokens || 0;
	const totalTokens = usage.total_tokens || 0;
	const price = usage.price || 0;

	usageState.totalInputTokens += inputTokens;
	usageState.totalOutputTokens += outputTokens;
	usageState.totalTokens += totalTokens;
	usageState.totalPrice += price;

	// 立即保存到缓存
	saveUsageToCache();

	console.log(`累加usage - 输入:${inputTokens}, 输出:${outputTokens}, 总计:${totalTokens}, 价格:${price}`);
};

/**
 * 清理会话缓存
 */
const clearSessionCache = () => {
	localStorage.removeItem(`game_session_${taskId.value}`);
	localStorage.removeItem(`soup_surface_${taskId.value}`); // 同时清理汤面缓存
	localStorage.removeItem(`usage_stats_${taskId.value}`); // 清理usage统计缓存
	sessionId.value = "";

	// 同时清理游戏状态
	gameState.soupSurface = "";
	gameState.hasGameStarted = false;

	// 清理usage统计状态
	usageState.totalInputTokens = 0;
	usageState.totalOutputTokens = 0;
	usageState.totalTokens = 0;
	usageState.totalPrice = 0;

	console.log(`已清理任务 ${taskId.value} 的会话、汤面和usage统计缓存`);
};

/**
 * 加载任务数据
 */
const loadTaskData = async () => {
	loading.value = true;
	try {
		let taskData;

		// 根据来源类型选择不同的API调用
		if (sourceType.value === "gamePlayType") {
			// 加载游戏玩法详情
			const gamePlayTypeResponse = await getGamePlayType(taskId.value);
			taskData = gamePlayTypeResponse;

			// 确保gamePlayType字段已设置
			if (!gamePlayType.value && taskData.name) {
				gamePlayType.value = taskData.name;
			}
		} else {
			// 加载任务基本信息
			const taskResponse = await getTaskDetail(taskId.value);
			taskData = taskResponse;
		}

		// 更新taskSettings
		taskSettings.taskInfo.title = taskData.title || taskData.name || "未命名";
		taskSettings.taskInfo.description = taskData.description || "";
		taskSettings.taskInfo.maxRounds = taskData.max_dialogue_rounds || -1;
		taskSettings.taskInfo.difficulty = taskData.difficulty || "中等";

		// 更新玩家人数限制
		taskSettings.minPlayers = taskData.game_number_min || 0;
		taskSettings.maxPlayers = taskData.game_number_max || 0;

		// 更新聊天状态
		chatState.maxRounds = taskData.max_dialogue_rounds || -1;

		// 生成随机会话ID
		generateSessionId();
	} catch (error) {
		console.error("加载数据失败", error);
		ElMessage.error("加载数据失败");
		router.push(sourceType.value === "gamePlayType" ? "/game/play/list" : "/chat/tasks");
	} finally {
		loading.value = false;
	}
};

/**
 * 处理WebSocket消息
 * @param data 消息数据
 */
const handleWebSocketMessage = (data) => {
	// 处理角色信息
	if (data.roles_info) {
		// 更新角色列表
		taskRoles.value = data.roles_info.map((role) => ({
			role_id: role.role_id,
			role_name: role.name,
			image_url: role.image_url || "https://via.placeholder.com/100?text=" + role.name,
			description: role.description || "",
			character_level: role.level || "",
		}));

		// 设置默认选中的角色ID
		if (taskRoles.value.length > 0 && !currentRoleId.value) {
			currentRoleId.value = taskRoles.value[0].role_id;

			// 设置AI信息
			const mainRole = taskRoles.value[0];
			taskSettings.aiInfo.name = mainRole.role_name || "AI助手";
			taskSettings.aiInfo.role = mainRole.character_level ? `${mainRole.character_level}级角色` : "任务辅助者";
			taskSettings.aiInfo.background = mainRole.description || "";
			taskSettings.aiInfo.image = mainRole.image_url || "";
		}
	}

	// 处理状态消息
	if (data.status) {
		if (data.status === "session_updated" || data.status === "session_resumed") {
			if (data.session_id) {
				sessionId.value = data.session_id;
			}

			// 添加系统消息
			addSystemMessage(data.message || `状态: ${data.status}`);

			// 更新状态，禁用输入框
			chatState.isLoading = true;
			chatState.isAiTyping = true;
		} else if (data.status === "waiting_for_human") {
			// 添加系统消息
			addSystemMessage(data.message || "轮到你提问了");

			// 启用输入框
			chatState.isLoading = false;
			chatState.isAiTyping = false;

			// 确保UI更新完成后聚焦输入框
			setTimeout(() => {
				const textarea = document.querySelector(".chat-input-area textarea");
				if (textarea) {
					(textarea as HTMLTextAreaElement).focus();
				}
			}, 100);
		} else if (data.status === "game_over") {
			// 添加系统消息
			addSystemMessage(data.message || "游戏结束");

			// 禁用输入框
			chatState.isLoading = true;
			chatState.isAiTyping = false;

			// 清理会话缓存
			clearSessionCache();

			// 显示结束提示
			setTimeout(() => {
				ElMessageBox.alert("游戏已结束", "提示", {
					confirmButtonText: "返回列表",
					callback: () => {
						router.push(sourceType.value === "gamePlayType" ? "/game/play/list" : "/chat/tasks");
					},
				});
			}, 1000);
		} else {
			// 添加其他状态消息
			addSystemMessage(`状态: ${data.status}, 消息: ${data.message || "无"}`);
		}
	}

	// 处理游戏消息
	if (data.role) {
		// 特殊处理task_setter消息，直接使用完整content作为汤面信息
		if (data.role === "task_setter" && data.content) {
			gameState.soupSurface = data.content;
			gameState.hasGameStarted = true;

			// 将汤面信息缓存到localStorage
			saveSoupToCache(data.content);

			console.log("收到汤面信息:", gameState.soupSurface);
		}

		// 显示游戏消息
		addMessage(data.role, data.content, data.role_name, data);
	}

	// 如果消息包含usage信息，累加统计
	if (data.usage) {
		addUsage(data.usage);
	}
};

/**
 * 连接WebSocket
 */
const connectWebSocket = () => {
	if (!sessionId.value) {
		generateSessionId();
	}

	// 使用API连接WebSocket
	wsClient.value = wsAPI.connectGameWebSocket(
		"turtle_soup",
		taskId.value,
		sourceType.value === "gamePlayType" ? "game" : "task",
		{
			onOpen: () => {
				// 连接成功后发送初始化消息
				if (wsClient.value) {
					const initParams = {
						name: taskSettings.userInfo.name,
						background: taskSettings.userInfo.background,
					};

					// 如果是游戏玩法来源，添加生成题目类型参数
					if (sourceType.value === "gamePlayType" && gamePlayType.value) {
						initParams["game_type"] = gamePlayType.value;
						initParams["question_type"] = questionType.value;
					}

					wsAPI.initGameSession(
						wsClient.value,
						sessionId.value,
						initParams,
						selectedRoleIds.value, // 使用多选的角色ID数组
					);
				}
			},
			onMessage: handleWebSocketMessage,
			onClose: () => {
				addSystemMessage("连接已关闭");
				wsClient.value = null;

				// 如果聊天已开始但连接异常关闭，可能需要清理缓存
				if (chatState.isStarted) {
					console.log("WebSocket连接异常关闭，保留会话缓存以便恢复");
				}
			},
			onError: (error) => {
				addSystemMessage(`连接错误: ${error?.message || "未知错误"}`);
				wsClient.value = null;

				// 连接错误时，考虑清理缓存（严重错误情况）
				if (error?.message?.includes("服务器错误") || error?.message?.includes("认证失败")) {
					console.log("检测到严重错误，清理会话缓存");
					clearSessionCache();
				}
			},
		},
	);

	// 禁用输入，等待服务器通知
	chatState.isLoading = true;
	chatState.isAiTyping = true;
};

/**
 * 添加系统消息
 */
const addSystemMessage = (content) => {
	chatState.messages.push({
		id: Date.now(),
		role: "system",
		sender: "system",
		senderName: "系统",
		content: content,
		timestamp: Date.now(),
		imageUrl: "",
	});
};

/**
 * 添加消息
 */
const addMessage = (role, content, roleName = null, data: any = {}) => {
	// 设置角色标签
	let senderName = roleName || "";
	let imageUrl = "";

	// 尝试解析role_info
	if (data.role_info) {
		try {
			const roleInfo = JSON.parse(data.role_info);
			if (roleInfo.name) {
				senderName = roleInfo.name;
			}
			if (roleInfo.image_url) {
				imageUrl = roleInfo.image_url;
			}
		} catch (e) {
			console.error("解析role_info失败", e);
		}
	}

	// 如果没有从role_info获取，则使用默认设置
	if (!senderName) {
		switch (role) {
			case "human":
				senderName = taskSettings.userInfo.name || "You";
				break;
			case "setter":
				senderName = "Question Master";
				break;
			case "player":
				senderName = "AI Player";
				break;
			case "system":
				senderName = "System";
				break;
			default:
				senderName = role;
		}
	}

	// 为setter角色添加特殊标记
	if (role === "setter") {
		senderName = `${senderName} (Question Master)`;
	}

	chatState.messages.push({
		id: Date.now(),
		role: role,
		sender: role,
		senderName: senderName,
		content: content,
		timestamp: Date.now(),
		imageUrl: imageUrl || (role === "assistant" ? taskSettings.aiInfo.image : ""),
	});
};

/**
 * 开始聊天
 */
const startChat = async () => {
	// 检查是否有缓存的会话ID
	const cachedSessionId = localStorage.getItem(`game_session_${taskId.value}`);

	if (cachedSessionId) {
		// 每次都开启新任务，清除之前的缓存
		localStorage.removeItem(`game_session_${taskId.value}`);
		sessionId.value = ""; // 清空当前会话ID，将在连接时重新生成

		// // 有缓存会话，询问用户是否开启新任务
		// try {
		// 	await ElMessageBox.confirm("检测到之前未完成的任务会话，是否要开启新的任务？", {
		// 		confirmButtonText: "开启新任务",
		// 		cancelButtonText: "继续之前任务",
		// 	});

		// 	// 用户选择开启新任务，清除缓存的会话ID
		// 	localStorage.removeItem(`game_session_${taskId.value}`);
		// 	sessionId.value = ""; // 清空当前会话ID，将在连接时重新生成
		// } catch (error) {
		// 	// 用户选择取消（继续之前任务），不做任何操作，使用缓存的会话ID
		// 	console.log("用户选择继续之前的任务");
		// }
	}

	// 将用户信息保存到localStorage
	localStorage.setItem("playerName", taskSettings.userInfo.name);

	// 切换到聊天界面
	chatState.isStarted = true;

	// 初始化欢迎消息
	chatState.messages = [
		{
			id: Date.now(),
			role: "system",
			sender: "system",
			senderName: "系统",
			content: `Welcome to ${sourceType.value === 'gamePlayType' ? 'the game' : 'the mission'}: ${taskSettings.taskInfo.title}\n\n${taskSettings.taskInfo.description}\n\nConnecting to server...`,
			timestamp: Date.now(),
		},
	];

	// 连接WebSocket
	connectWebSocket();
};

/**
 * 发送消息
 * @param userInput 用户输入的消息
 */
const sendMessage = async (userInput) => {
	if (!userInput.trim() || chatState.isLoading) return;

	// 检查WebSocket连接
	if (!wsClient.value || !wsClient.value.isConnected()) {
		ElMessage.error("WebSocket未连接");
		return;
	}

	// 添加用户消息
	addMessage("human", userInput);
	chatState.currentRound++;

	// 清空输入框
	chatState.userInput = "";

	// 禁用输入，等待AI回应
	chatState.isLoading = true;
	chatState.isAiTyping = true;

	try {
		// 发送用户消息
		const result = wsAPI.sendUserMessage(wsClient.value, userInput);

		if (!result) {
			// 发送失败，显示错误
			addSystemMessage("Message sending failed, please try again.");
			chatState.isLoading = false;
			chatState.isAiTyping = false;
		} else {
			// 确保界面显示"AI正在思考"状态
			console.log("消息已发送，等待AI回应");
		}
	} catch (error) {
		console.error("发送消息失败:", error);
		addSystemMessage("Message sending failed, please try again.");
		chatState.isLoading = false;
		chatState.isAiTyping = false;
	}
};

/**
 * 切换当前对话角色
 * @param roleId 角色ID
 */
const switchRole = (roleId) => {
	if (currentRoleId.value === roleId) return;

	currentRoleId.value = roleId;

	// 更新AI信息
	const selectedRole = taskRoles.value.find((role) => role.role_id === roleId);
	if (selectedRole) {
		taskSettings.aiInfo.name = selectedRole.role_name || "AI Assistant";
		taskSettings.aiInfo.role = selectedRole.character_level ? `${selectedRole.character_level}-level character` : "Task Helper";
		taskSettings.aiInfo.background = selectedRole.description || "";
		taskSettings.aiInfo.image = selectedRole.image_url || "";
	}

	// 添加系统消息提示角色切换
	if (chatState.isStarted) {
		chatState.messages.push({
			id: Date.now(),
			role: "system",
			sender: "system",
			senderName: "System",
			content: `You are now chatting with ${taskSettings.aiInfo.name}`,
			timestamp: Date.now(),
		});
	}
};

/**
 * 返回上一页
 */
const goBack = () => {
	if (chatState.isStarted) {
		ElMessageBox.confirm("Are you sure you want to quit the current task? Progress will not be saved.", "Warning", {
			confirmButtonText: "Confirm",
			cancelButtonText: "Cancel",
			type: "warning",
		})
			.then(() => {
				// 断开WebSocket连接
				disconnectWebSocket();

				// 用户主动退出时清理缓存
				clearSessionCache();

				router.push(sourceType.value === "gamePlayType" ? "/game/play/list" : "/chat/tasks");
			})
			.catch(() => {});
	} else {
		router.push(sourceType.value === "gamePlayType" ? "/game/play/list" : "/chat/tasks");
	}
};

/**
 * 断开WebSocket连接
 */
const disconnectWebSocket = () => {
	if (wsClient.value) {
		wsAPI.disconnectGameWebSocket("turtle_soup", taskId.value);
		wsClient.value = null;
	}
};

/**
 * 获取连接状态文本
 */
const getConnectionStatus = () => {
	if (!chatState.isStarted) {
		return "Not connected";
	}

	if (!wsClient.value) {
		return "Connection lost";
	}

	if (wsClient.value.isConnected()) {
		if (chatState.isAiTyping) {
			return "AI is thinking...";
		} else if (chatState.isLoading) {
			return "Waiting for server response...";
		} else {
			// 根据轮次显示不同消息
			return chatState.maxRounds === -1
				? `Your turn (Round ${chatState.currentRound})`
				: `Your turn (${chatState.currentRound}/${chatState.maxRounds})`;
		}
	} else {
		return "Connecting to server...";
	}
};

/**
 * 结束游戏
 */
const endGame = () => {
	if (!wsClient.value || !wsClient.value.isConnected()) {
		ElMessage.error("WebSocket disconnected");
		return;
	}

	ElMessageBox.confirm("Are you sure you want to end the current game?", "Warning", {
		confirmButtonText: "Confirm",
		cancelButtonText: "Cancel",
		type: "warning",
	})
		.then(() => {
			if (wsClient.value) {
				wsAPI.endGame(wsClient.value);
				chatState.isLoading = true;

				// 手动结束游戏时清理缓存
				clearSessionCache();
			}
		})
		.catch(() => {});
};

/**
 * 处理角色选择
 * @param roles 选择的角色列表
 */
const handleSelectRoles = (roles: any[]) => {
	selectedRoles.value = roles;
	selectedRoleIds.value = roles.map((role) => role.role_id);
	console.log("已选择角色:", roles);

	// 如果有角色被选中，将第一个角色设为当前活动角色
	if (roles.length > 0 && !currentRoleId.value) {
		currentRoleId.value = roles[0].role_id;
	}
};

// 组件挂载时执行
onMounted(() => {
	loadTaskData();
	// 尝试从缓存加载汤面信息
	loadSoupFromCache();
	// 尝试从缓存加载usage统计
	loadUsageFromCache();
});

// 组件卸载前断开连接
onBeforeUnmount(() => {
	disconnectWebSocket();

	// 如果游戏状态异常，考虑清理缓存
	if (chatState.isStarted && !wsClient.value) {
		console.log("组件卸载时检测到异常状态，保留会话缓存以便恢复");
	}
});
</script>

<style lang="scss" scoped>
.task-chat-container {
	display: flex;
	flex-direction: column;
	height: 100vh;
	background-color: #121212;
	color: #e0e0e0;
	font-family: "Roboto", sans-serif;
	position: relative;
	overflow: hidden;

	&::before {
		content: "";
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-size: cover;
		opacity: 0.1;
		z-index: 0;
	}
}

.main-content {
	display: flex;
	flex: 1;
	position: relative;
	z-index: 1;
	overflow: hidden;
}

@keyframes fadeIn {
	from {
		opacity: 0;
		transform: translateY(10px);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}

@keyframes blink {
	0%,
	100% {
		transform: scale(1);
		opacity: 0.6;
	}
	50% {
		transform: scale(1.2);
		opacity: 1;
	}
}

// 媒体查询
@media (max-width: 992px) {
	.settings-container {
		grid-template-columns: 1fr;
	}

	.start-chat-button {
		width: 80%;
	}
}

.status-indicator {
	position: fixed;
	bottom: 0;
	left: 0;
	right: 0;
	padding: 8px;
	background-color: rgba(26, 26, 46, 0.8);
	color: #a0a0a0;
	font-style: italic;
	text-align: center;
	border-top: 1px solid rgba(100, 100, 255, 0.2);
	font-size: 0.9rem;
	z-index: 10;
	transition: all 0.3s ease;
	transform: translateY(100%);

	&.active {
		transform: translateY(0);
	}
}

.end-game-btn {
	margin-left: 10px;
}

// 媒体查询
@media (max-width: 992px) {
	.status-indicator {
		font-size: 0.8rem;
		padding: 5px;
	}
}
</style>
