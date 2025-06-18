<template>
	<el-dialog
		v-model="dialogVisible"
		:title="dialogTitle"
		width="1000px"
		:before-close="handleClose"
		class="chat-dialog"
	>
		<el-row :gutter="20" class="chat-container">
			<!-- Left side user information input -->
			<el-col :span="6" class="user-info-panel">
				<div class="user-info-header">User Information</div>
				<el-form label-position="top" size="small">
					<el-form-item label="User Name">
						<el-input v-model="userInfo.user_name" placeholder="Player" :disabled="sessionInitialized"></el-input>
					</el-form-item>
					<el-form-item label="User ID">
						<el-input v-model="userInfo.user_id" placeholder="Optional" :disabled="sessionInitialized"></el-input>
					</el-form-item>
					<el-form-item>
						<el-button type="primary" @click="initSession" :disabled="sessionInitialized || isLoading">
							{{ sessionInitialized ? "Initialized" : "Initialize Session" }}
						</el-button>
					</el-form-item>
				</el-form>
			</el-col>

			<!-- Right side chat area -->
			<el-col :span="18" class="chat-right-panel">
				<!-- Task information area -->
				<div class="task-info">
					<div class="task-header">
						<div class="task-title">{{ taskInfo.title || "Random Task" }}</div>
						<div class="task-stats">
							<span>Rounds: {{ currentRound }}/{{ taskInfo.max_rounds || 10 }}</span>
							<span>Score: {{ currentScore }}/{{ taskInfo.target_score || 10 }}</span>
							<el-button
								v-if="sessionInitialized && !isSkipping"
								size="small"
								type="warning"
								@click="skipCurrentTask"
								:disabled="isLoading"
							>
								Skip Task
							</el-button>
						</div>
					</div>
					<div class="task-description-container">
						<div class="task-description">{{ taskInfo.description || "" }}</div>
						<div class="task-goal">Goal: {{ taskInfo.task_goal || "" }}</div>
					</div>
				</div>

				<!-- Chat messages area -->
				<div class="chat-messages" ref="chatMessagesRef">
					<div
						v-for="(message, index) in chatMessages"
						:key="index"
						:class="['message-item', message.fromUser ? 'user-message' : 'ai-message']"
					>
						<div class="message-avatar">
							<img :src="message.fromUser ? userAvatar : aiAvatar" alt="Avatar" />
						</div>
						<div class="message-content">
							<div class="message-name">
								{{ message.fromUser ? userInfo.user_name : taskInfo.task_personality || "Character" }}
							</div>
							<div class="message-text" v-html="formatMessage(message.content)"></div>
							<div v-if="message.scoreChange !== undefined" class="score-indicator">
								{{ message.scoreChange > 0 ? "+" : "" }}{{ message.scoreChange }} points
								<el-tooltip placement="top" v-if="message.scoreReason">
									<template #content>{{ message.scoreReason }}</template>
									<i class="el-icon-question"></i>
								</el-tooltip>
							</div>
						</div>
					</div>
				</div>

				<!-- Input area -->
				<div class="chat-input">
					<el-input
						v-model="userInput"
						type="textarea"
						:rows="3"
						:placeholder="isLoading ? 'Waiting for reply...' : sessionInitialized ? 'Please enter message' : 'Please initialize session first'"
						:disabled="isLoading || isTaskCompleted || !sessionInitialized"
						@keydown.enter.prevent="handleEnterKey"
					></el-input>
					<el-button
						type="primary"
						@click="sendMessage"
						:loading="isLoading"
						:disabled="!userInput.trim() || isTaskCompleted || !sessionInitialized"
					>
						Send
					</el-button>
				</div>
			</el-col>
		</el-row>
	</el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed, nextTick } from "vue";
import { chatSubTask, initRandomTaskSession, skipSubTask } from "@/api/llm";
import { ElMessage, ElMessageBox } from "element-plus";

// Dialog properties
const props = defineProps({
	visible: {
		type: Boolean,
		default: false,
	},
	roleSelectMode: {
		type: Boolean,
		default: false,
	},
});

// Dialog events
const emit = defineEmits(["update:visible", "close", "task-completed", "task-skipped"]);

// Data definitions
const dialogVisible = ref(props.visible);
const userInput = ref("");
const isLoading = ref(false);
const chatMessages = ref<any[]>([]);
const currentRound = ref(0);
const currentScore = ref(0);
const sessionId = ref("");
const subTaskId = ref("");
const chatMessagesRef = ref<HTMLElement | null>(null);
const userAvatar = ref("https://picsum.photos/400/300?random=1"); // User avatar
const aiAvatar = ref("https://picsum.photos/400/300?random=2"); // AI avatar
const sessionInitialized = ref(false);
const taskInfo = ref<any>({});
const isSkipping = ref(false);

// User information
const userInfo = ref({
	user_name: "Player",
	user_level: 1,
	level: 1,
	relationship_level: 1,
	role_id: "",
	user_id: "test1",
	temperature: 0.7,
	top_k: 3,
});

// Compute dialog title
const dialogTitle = computed(() => `Random Task Chat: ${taskInfo.value.title || "Start New Task"}`);

// Whether task is completed
const isTaskCompleted = computed(() => {
	return (
		currentRound.value >= (taskInfo.value.max_rounds || 10) || currentScore.value >= (taskInfo.value.target_score || 10)
	);
});

// Watch dialog visibility state
watch(
	() => props.visible,
	(newVal) => {
		dialogVisible.value = newVal;
		if (!newVal) {
			// Reset state when closing dialog
			resetChatState();
		}
	},
);

// Watch dialog state changes and feedback to parent component
watch(dialogVisible, (newVal) => {
	emit("update:visible", newVal);
	if (!newVal) {
		emit("close");
	}
});

// Watch message changes for auto-scroll
watch(
	chatMessages,
	() => {
		nextTick(() => {
			scrollToBottom();
		});
	},
	{ deep: true },
);

// Watch task completion status
watch(isTaskCompleted, (newVal) => {
	if (newVal) {
		emit("task-completed", {
			score: currentScore.value,
			rounds: currentRound.value,
			achieved: currentScore.value >= (taskInfo.value.target_score || 10),
		});
	}
});

// Method definitions
function handleClose() {
	dialogVisible.value = false;
	resetChatState();
}

function resetChatState() {
	sessionInitialized.value = false;
	chatMessages.value = [];
	currentRound.value = 0;
	currentScore.value = 0;
	taskInfo.value = {};
	sessionId.value = "";
	subTaskId.value = "";
	userInput.value = "";
}

// Initialize session
async function initSession() {
	if (sessionInitialized.value) return;

	isLoading.value = true;
	try {
		const response = await initRandomTaskSession({
			user_name: userInfo.value.user_name,
			user_level: userInfo.value.user_level,
			level: userInfo.value.level,
			relationship_level: userInfo.value.relationship_level,
			role_id: userInfo.value.role_id,
			user_id: userInfo.value.user_id,
		});

		// Save session ID, subtask ID and task information
		sessionId.value = response.session_id;
		subTaskId.value = response.sup_task_id;
		taskInfo.value = response.task;
		sessionInitialized.value = true;

		// Add system welcome message
		addSystemMessage();

		ElMessage.success("Session initialized successfully");
	} catch (error) {
		console.error("Failed to initialize session", error);
		ElMessage.error("Failed to initialize session, please try again");
	} finally {
		isLoading.value = false;
	}
}

function addSystemMessage() {
	// Add prologue or task description
	const intro = taskInfo.value.prologues || `Welcome to "${taskInfo.value.title}" task. Goal: ${taskInfo.value.task_goal}`;
	chatMessages.value.push({
		fromUser: false,
		content: intro,
		time: new Date().toLocaleTimeString(),
	});
}

function formatMessage(text: string) {
	// Handle message line breaks
	return text?.replace(/\n/g, "<br>") || "";
}

async function sendMessage() {
	if (!userInput.value.trim() || isLoading.value || !sessionInitialized.value) return;

	const userMessage = userInput.value.trim();

	// Add user message to chat history
	chatMessages.value.push({
		fromUser: true,
		content: userMessage,
		time: new Date().toLocaleTimeString(),
	});

	userInput.value = "";
	isLoading.value = true;

	try {
		// Prepare request parameters
		const requestData = {
			message: userMessage,
			role_id: userInfo.value.role_id,
			level: userInfo.value.level.toString(),
			user_level: userInfo.value.user_level.toString(),
			session_id: sessionId.value,
			user_name: userInfo.value.user_name,
			relationship_level: userInfo.value.relationship_level,
			user_id: userInfo.value.user_id,
			temperature: userInfo.value.temperature,
			top_k: userInfo.value.top_k,
			// The following parameters are retained according to interface requirements, but are no longer used
			taskDescription: "",
			taskGoal: "",
			scoreRange: "",
			maxRounds: 10,
			targetScore: 10,
			taskLevel: 1,
			taskPersonality: "",
			sub_task_id: "",
		};

		// Call API
		const response = await chatSubTask(requestData);

		// Update round count
		currentRound.value += 1;

		// Handle score changes
		let scoreChange = 0;
		let scoreReason = "";

		// Check and handle tool_results
		if (response.data.tool_results) {
			let toolResults = response.data.tool_results;

			// If tool_results is a string, parse it into an object first
			if (typeof toolResults === "string") {
				try {
					toolResults = JSON.parse(toolResults);
				} catch (e) {
					console.error("Failed to parse tool_results", e);
				}
			}

			// Find score_change tool call result
			if (Array.isArray(toolResults)) {
				const scoreResult = toolResults.find(
					(tool) =>
						tool.content &&
						((typeof tool.content === "string" && tool.content.includes("score_change")) ||
							(typeof tool.content === "object" && tool.content.name === "score_change")),
				);

				if (scoreResult) {
					let scoreData;
					if (typeof scoreResult.content === "string") {
						try {
							scoreData = JSON.parse(scoreResult.content);
						} catch (e) {
							console.error("Failed to parse score data", e);
						}
					} else {
						scoreData = scoreResult.content;
					}

					if (scoreData) {
						scoreChange = scoreData.scoreChange || 0;
						scoreReason = scoreData.reason || "";
					}
				}
			}
		}

		// Update total score
		currentScore.value += scoreChange;

		// Add AI reply to chat history
		chatMessages.value.push({
			fromUser: false,
			content: response.data.message || "Sorry, I didn't receive a reply.",
			time: new Date().toLocaleTimeString(),
			scoreChange,
			scoreReason,
		});
	} catch (error) {
		console.error("Failed to send message", error);
		chatMessages.value.push({
			fromUser: false,
			content: "Failed to send message, please try again later.",
			time: new Date().toLocaleTimeString(),
		});
	} finally {
		isLoading.value = false;
		scrollToBottom();
	}
}

function scrollToBottom() {
	if (chatMessagesRef.value) {
		chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight;
	}
}

// Skip current task
async function skipCurrentTask() {
	if (!sessionInitialized.value || !userInfo.value.user_id || !subTaskId.value) {
		ElMessage.warning("Unable to skip task, please ensure session is initialized and user ID is provided");
		return;
	}

	// Confirm whether to skip
	try {
		await ElMessageBox.confirm("Are you sure you want to skip the current task?", "Warning", {
			confirmButtonText: "Confirm",
			cancelButtonText: "Cancel",
			type: "warning",
		});

		isSkipping.value = true;

		// Call skip interface, using subtask ID
		await skipSubTask({
			user_id: userInfo.value.user_id,
			subtask_id: subTaskId.value,
		});

		ElMessage.success("Successfully skipped current task");

		// Reset task or close dialog
		resetChatState();
		dialogVisible.value = false;
		emit("task-skipped");
	} catch (error) {
		if (error !== "cancel") {
			// User cancellation is not considered an error
			console.error("Failed to skip task", error);
			ElMessage.error("Failed to skip task, please try again");
		}
	} finally {
		isSkipping.value = false;
	}
}

// Handle Enter key to send message
function handleEnterKey(event: KeyboardEvent) {
	// If Shift key is held, don't send message, allow line break
	if (event.shiftKey) {
		return;
	}

	// Otherwise send message
	sendMessage();
}
</script>

<style scoped>
.chat-dialog :deep(.el-dialog__body) {
	padding: 0;
}

.chat-container {
	height: 600px;
	margin: 0;
}

.user-info-panel {
	padding: 15px;
	background-color: #f8f9fa;
	border-right: 1px solid #e6e6e6;
	height: 100%;
	overflow-y: auto;
}

.chat-right-panel {
	display: flex;
	flex-direction: column;
	height: 100%;
	overflow: hidden;
}

.user-info-header {
	font-size: 16px;
	font-weight: bold;
	margin-bottom: 15px;
	text-align: center;
}

.task-info {
	padding: 15px;
	background-color: #f5f7fa;
	border-bottom: 1px solid #e6e6e6;
	overflow-y: auto;
	max-height: 150px;
}

.task-description-container {
	overflow-y: auto;
	max-height: 80px;
}

.task-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 10px;
}

.task-title {
	font-size: 18px;
	font-weight: bold;
}

.task-stats {
	font-size: 14px;
}

.task-stats span {
	margin-left: 15px;
}

.task-description {
	margin-bottom: 8px;
	color: #606266;
}

.task-goal {
	font-weight: bold;
	color: #409eff;
}

.chat-messages {
	flex: 1;
	overflow-y: auto;
	padding: 15px;
	background-color: #f9f9f9;
	min-height: 300px;
}

.message-item {
	display: flex;
	margin-bottom: 15px;
	align-items: flex-start;
}

.user-message {
	flex-direction: row-reverse;
}

.message-avatar {
	width: 40px;
	height: 40px;
	border-radius: 50%;
	overflow: hidden;
	margin: 0 10px;
}

.message-avatar img {
	width: 100%;
	height: 100%;
	object-fit: cover;
}

.message-content {
	max-width: 70%;
	padding: 10px;
	border-radius: 8px;
	position: relative;
}

.user-message .message-content {
	background-color: #ecf5ff;
	text-align: right;
}

.ai-message .message-content {
	background-color: #ffffff;
	text-align: left;
	border: 1px solid #e6e6e6;
}

.message-name {
	font-size: 12px;
	color: #909399;
	margin-bottom: 5px;
}

.message-text {
	word-break: break-word;
	line-height: 1.5;
}

.score-indicator {
	font-size: 12px;
	margin-top: 5px;
	color: #67c23a;
}

.score-indicator i {
	margin-left: 4px;
	cursor: pointer;
}

.chat-input {
	padding: 15px;
	border-top: 1px solid #e6e6e6;
	display: flex;
	align-items: flex-end;
}

.chat-input .el-input {
	margin-right: 10px;
	flex: 1;
}
</style>
