<template>
	<div class="chat-detail">
		<div class="header fade-in">
			<div class="left">
				<el-button @click="goBack" icon="ArrowLeft">Back to List</el-button>
				<h1 class="title">
					Session Details <span class="session-id">{{ sessionId }}</span>
				</h1>
			</div>
			<div class="right">
				<el-button type="warning" @click="handleCopySessionId" icon="CopyDocument">Copy Session ID</el-button>
				<el-button type="danger" @click="handleDeleteSession" icon="Delete">Delete Session Record</el-button>
			</div>
		</div>

		<!-- Session information card -->
		<el-card class="info-card fade-in-up" style="animation-delay: 100ms">
			<template #header>
				<div class="card-header">
					<span
						><el-icon><InfoFilled /></el-icon> Session Information</span
					>
					<div class="header-actions">
						<el-tag type="success" v-if="sessionInfo.messages_count">{{ sessionInfo.messages_count }} messages</el-tag>
						<el-tag type="warning" v-if="sessionInfo.rounds_count">{{ sessionInfo.rounds_count }} rounds</el-tag>
						<el-tag type="info" v-if="sessionInfo.total_score_change !== undefined"
							>Total Score Change: {{ sessionInfo.total_score_change }}</el-tag
						>
					</div>
				</div>
			</template>
			<el-descriptions :column="3" border>
				<el-descriptions-item label="Created Time">
					{{ sessionInfo.first_message_time ? formatDate(sessionInfo.first_message_time) : "No data" }}
				</el-descriptions-item>
				<el-descriptions-item label="Last Activity">
					{{ sessionInfo.last_message_time ? formatDate(sessionInfo.last_message_time) : "No data" }}
				</el-descriptions-item>
				<el-descriptions-item label="Duration">
					{{ sessionInfo.duration || "No data" }}
				</el-descriptions-item>
				<el-descriptions-item label="User ID">
					{{ sessionInfo.user_id || "No data" }}
				</el-descriptions-item>
				<el-descriptions-item label="Role ID">
					{{ sessionInfo.role_id || "No data" }}
				</el-descriptions-item>
				<el-descriptions-item label="Max Rounds">
					{{ sessionInfo.max_round || "0" }}
				</el-descriptions-item>
				<el-descriptions-item label="Total Messages">
					{{ sessionInfo.messages_count || "0" }}
				</el-descriptions-item>
			</el-descriptions>
		</el-card>

		<!-- Round filter -->
		<div class="round-filter fade-in-up" style="animation-delay: 200ms">
			<el-radio-group v-model="currentRound" @change="handleRoundChange">
				<el-radio-button :label="-1">All Rounds</el-radio-button>
				<el-radio-button v-for="round in availableRounds" :key="round" :label="round">Round {{ round }}</el-radio-button>
			</el-radio-group>
		</div>

		<!-- Chat message list -->
		<div class="chat-messages fade-in-up" style="animation-delay: 300ms" v-loading="loading">
			<div v-if="!loading && messages.length === 0" class="empty-messages">
				<el-empty description="No chat records" />
			</div>
			<div v-else class="message-list">
				<div
					v-for="(message, index) in messages"
					:key="message.id"
					:class="[
						'message-item',
						message.role === 'user'
							? 'user-message'
							: message.role === 'system'
							? 'system-message'
							: message.role === 'function'
							? 'function-message'
							: 'assistant-message',
						{ 'round-start': isRoundStart(message, index) },
					]"
				>
					<div v-if="isRoundStart(message, index)" class="round-divider">
						<span class="round-tag">Round {{ message.round }}</span>
					</div>
					<div class="message-header">
						<span class="message-type">
							<el-tag :type="getRoleTypeTag(message.role)" size="small">
								{{ formatRoleType(message.role) }}
							</el-tag>
							<el-tag
								v-if="message.score_change !== 0 && message.score_change !== null"
								:type="message.score_change > 0 ? 'success' : 'danger'"
								size="small"
								class="score-tag"
							>
								Points {{ message.score_change > 0 ? "+" : "" }}{{ message.score_change }}
							</el-tag>
						</span>
						<span class="message-time">{{ formatDate(message.create_time) }}</span>
					</div>
					<div class="message-content">
						<!-- Render different content based on role type -->
						<template v-if="message.role === 'function'">
							<div class="function-content">
								<el-collapse>
									<el-collapse-item>
										<template #title>
											<span class="function-title">
												{{ getFunctionTitle(message.content) }}
											</span>
										</template>
										<div class="function-details">
											<div v-if="parsedFunctionContent(message.content)">
												<el-descriptions border :column="1">
													<el-descriptions-item
														v-if="parsedFunctionContent(message.content).scoreChange !== undefined"
														label="Score Change"
													>
														<span
															:class="{
																'score-positive': parsedFunctionContent(message.content).scoreChange > 0,
																'score-negative': parsedFunctionContent(message.content).scoreChange < 0,
																'score-neutral': parsedFunctionContent(message.content).scoreChange === 0,
															}"
														>
															{{ parsedFunctionContent(message.content).scoreChange > 0 ? "+" : ""
															}}{{ parsedFunctionContent(message.content).scoreChange }}
														</span>
													</el-descriptions-item>
													<el-descriptions-item v-if="parsedFunctionContent(message.content).reason" label="Reason">
														{{ parsedFunctionContent(message.content).reason }}
													</el-descriptions-item>
													<el-descriptions-item
														v-if="parsedFunctionContent(message.content).isAchieved !== undefined"
														label="Goal Achieved"
													>
														<el-tag :type="parsedFunctionContent(message.content).isAchieved ? 'success' : 'info'">
															{{ parsedFunctionContent(message.content).isAchieved ? "Yes" : "No" }}
														</el-tag>
													</el-descriptions-item>
												</el-descriptions>
											</div>
											<pre v-else>{{ formatJson(message.content) }}</pre>
										</div>
									</el-collapse-item>
								</el-collapse>
							</div>
						</template>
						<!-- AI assistant or system message -->
						<template v-else-if="message.role === 'assistant' || message.role === 'system'">
							<div class="ai-content">
								<div class="message-text">{{ message.content }}</div>
								<div v-if="message.score_reason" class="score-reason">
									<el-tag type="info" size="small">Score Reason: {{ message.score_reason }}</el-tag>
								</div>
								<div v-if="message.model_id" class="model-info">
									<el-tag type="info" size="small">Model: {{ message.model_id }}</el-tag>
									<el-tag type="info" size="small" v-if="message.input_tokens"
										>Input: {{ message.input_tokens }} tokens</el-tag
									>
									<el-tag type="info" size="small" v-if="message.output_tokens"
										>Output: {{ message.output_tokens }} tokens</el-tag
									>
								</div>
							</div>
						</template>
						<!-- User message -->
						<template v-else>
							<div class="text-content">
								{{ message.content }}
							</div>
						</template>
					</div>
					<div class="message-actions">
						<el-button type="info" link size="small" @click="handleCopyMessage(message.content)">
							<el-icon><CopyDocument /></el-icon> Copy
						</el-button>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { InfoFilled, CopyDocument } from "@element-plus/icons-vue";
import { getMessagesBySession, getMessagesByRound, deleteSessionMessages } from "@/api/task_game_messages";
import { formatDate } from "@/utils";

// Type definitions
interface TaskGameMessage {
	id: number;
	session_id: string;
	role: string;
	role_id: string;
	user_id: string;
	content: string;
	round: number;
	score_change: number | null;
	score_reason: string | null;
	input_tokens: number | null;
	output_tokens: number | null;
	model_id: string | null;
	create_time: string;
}

interface SessionInfo {
	user_id: string;
	role_id: string;
	first_message_time: string;
	last_message_time: string;
	duration: string;
	messages_count: number;
	max_round: number;
	rounds_count: number;
	total_score_change: number;
}

interface FunctionContent {
	scoreChange?: number;
	reason?: string;
	isAchieved?: boolean;
	name?: string;
	[key: string]: any;
}

// Route related
const route = useRoute();
const router = useRouter();
const sessionId = ref(route.params.id as string);

// Data definitions
const loading = ref(false);
const messages = ref<TaskGameMessage[]>([]);
const currentRound = ref(-1); // -1 means all rounds
const availableRounds = ref<number[]>([]);
const sessionInfo = reactive<SessionInfo>({
	user_id: "",
	role_id: "",
	first_message_time: "",
	last_message_time: "",
	duration: "",
	messages_count: 0,
	max_round: 0,
	rounds_count: 0,
	total_score_change: 0,
});

// Calculate if a message is the start of a round
function isRoundStart(message: TaskGameMessage, index: number): boolean {
	if (index === 0) return true;
	return message.round !== messages.value[index - 1].round;
}

// Format role type
function formatRoleType(role: string) {
	switch (role) {
		case "user":
			return "User";
		case "system":
			return "System";
		case "assistant":
			return "AI Assistant";
		case "function":
			return "Function Score";
		default:
			return role;
	}
}

// Get role type tag style
function getRoleTypeTag(role: string): any {
	switch (role) {
		case "user":
			return "success";
		case "system":
			return "info";
		case "assistant":
			return "warning";
		case "function":
			return "danger";
		default:
			return "default";
	}
}

// Get function message title
function getFunctionTitle(content: string): string {
	const parsedContent = parsedFunctionContent(content);
	if (parsedContent) {
		if (parsedContent.name === "score_change") {
			return `Score Assessment: ${parsedContent.scoreChange > 0 ? "Added Points" : parsedContent.scoreChange < 0 ? "Reduced Points" : "No Change"}`;
		}
		return parsedContent.name || "Function Call";
	}
	return "Function Content";
}

// Parse function content
function parsedFunctionContent(content: string): FunctionContent | null {
	try {
		if (!content) return null;
		const parsed = JSON.parse(content);

		// Handle nested structure
		if (parsed.content && typeof parsed.content === "object") {
			return parsed.content;
		}

		return parsed;
	} catch (e) {
		return null;
	}
}

// Format JSON
function formatJson(json: string) {
	try {
		if (!json) return "{}";
		const obj = typeof json === "string" ? JSON.parse(json) : json;
		return JSON.stringify(obj, null, 2);
	} catch (e) {
		return json;
	}
}

// Calculate session duration
function calculateDuration(start: string, end: string): string {
	if (!start || !end) return "Unknown";

	const startDate = new Date(start);
	const endDate = new Date(end);
	const diffMs = endDate.getTime() - startDate.getTime();

	// Calculate days, hours, minutes, and seconds
	const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
	const hours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
	const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
	const seconds = Math.floor((diffMs % (1000 * 60)) / 1000);

	// Format output
	let result = "";
	if (days > 0) result += `${days} days `;
	if (hours > 0 || days > 0) result += `${hours} hours `;
	if (minutes > 0 || hours > 0 || days > 0) result += `${minutes} minutes `;
	result += `${seconds} seconds`;

	return result;
}

// Load messages
async function loadMessages() {
	loading.value = true;
	try {
		let result;

		if (currentRound.value === -1) {
			// Load all rounds
			result = await getMessagesBySession(sessionId.value);
		} else {
			// Load specific round
			result = await getMessagesByRound(sessionId.value, currentRound.value);
		}

		if (result && result.items) {
			messages.value = result.items;

			// Update session info
			if (messages.value.length > 0) {
				// Extract user ID and role ID
				const firstMessage = messages.value[0];
				sessionInfo.user_id = firstMessage.user_id;
				sessionInfo.role_id = firstMessage.role_id;

				// Calculate statistics
				sessionInfo.messages_count = result.total || messages.value.length;

				// Find max round
				const rounds = messages.value.map((m) => m.round);
				sessionInfo.max_round = Math.max(...rounds);

				// Calculate unique round count
				const uniqueRounds = [...new Set(rounds)];
				sessionInfo.rounds_count = uniqueRounds.length;
				availableRounds.value = uniqueRounds.sort((a, b) => a - b);

				// Calculate total score change
				sessionInfo.total_score_change = messages.value.reduce((total, msg) => {
					return total + (msg.score_change || 0);
				}, 0);

				// Calculate time
				const sortedMessages = [...messages.value].sort(
					(a, b) => new Date(a.create_time).getTime() - new Date(b.create_time).getTime(),
				);

				sessionInfo.first_message_time = sortedMessages[0].create_time;
				sessionInfo.last_message_time = sortedMessages[sortedMessages.length - 1].create_time;

				// Calculate duration
				sessionInfo.duration = calculateDuration(sessionInfo.first_message_time, sessionInfo.last_message_time);
			}
		} else {
			messages.value = [];
		}
	} catch (err: any) {
		ElMessage.error(`Failed to load messages: ${err.message}`);
	} finally {
		loading.value = false;
	}
}

// Handle round change
function handleRoundChange() {
	loadMessages();
}

// Handle copy session ID
function handleCopySessionId() {
	navigator.clipboard
		.writeText(sessionId.value)
		.then(() => {
			ElMessage.success("Session ID copied to clipboard");
		})
		.catch(() => {
			ElMessage.error("Copy failed, please copy manually");
		});
}

// Handle copy message content
function handleCopyMessage(content: string) {
	navigator.clipboard
		.writeText(content)
		.then(() => {
			ElMessage.success("Message content copied to clipboard");
		})
		.catch(() => {
			ElMessage.error("Copy failed, please copy manually");
		});
}

// Handle delete session
function handleDeleteSession() {
	ElMessageBox.confirm(`Are you sure you want to delete all messages for session ${sessionId.value}? This action cannot be undone.`, "Warning", {
		confirmButtonText: "Confirm Delete",
		cancelButtonText: "Cancel",
		type: "warning",
	})
		.then(() => {
			deleteSessionMessages(sessionId.value)
				.then((res) => {
					ElMessage.success(`Successfully deleted ${res.data} message records`);
					goBack();
				})
				.catch((err) => {
					ElMessage.error(`Delete failed: ${err.message}`);
				});
		})
		.catch(() => {
			// User canceled deletion
		});
}

// Go back to list page
function goBack() {
	router.push("/bink/task-game-messages");
}

// Watch route changes, update session ID
watch(
	() => route.params.id,
	(newId) => {
		if (newId) {
			sessionId.value = newId as string;
			loadMessages();
		}
	},
);

// Initialize
onMounted(() => {
	if (sessionId.value) {
		loadMessages();
	}
});
</script>

<style lang="scss" scoped>
.chat-detail {
	padding: 20px;
	min-height: 100vh;

	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 20px;

		.left {
			display: flex;
			align-items: center;
			gap: 15px;

			.title {
				font-size: 22px;
				font-weight: 600;
				margin: 0;

				.session-id {
					color: #409eff;
					font-size: 16px;
					margin-left: 10px;
				}
			}
		}

		.right {
			display: flex;
			gap: 10px;
		}
	}

	.info-card {
		margin-bottom: 20px;

		.card-header {
			display: flex;
			justify-content: space-between;
			align-items: center;

			.header-actions {
				display: flex;
				gap: 10px;
			}
		}
	}

	.round-filter {
		margin-bottom: 20px;
		padding: 15px;
		background-color: #f5f7fa;
		border-radius: 4px;
		text-align: center;
	}

	.chat-messages {
		background-color: #fff;
		border-radius: 8px;
		box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
		padding: 20px;

		.empty-messages {
			padding: 40px 0;
		}

		.message-list {
			display: flex;
			flex-direction: column;
			gap: 15px;

			.message-item {
				position: relative;
				padding: 15px;
				border-radius: 8px;
				max-width: 100%;

				&.user-message {
					background-color: #ecf5ff;
					border-left: 4px solid #409eff;
				}

				&.system-message {
					background-color: #f5f7fa;
					border-left: 4px solid #909399;
				}

				&.assistant-message {
					background-color: #fdf6ec;
					border-left: 4px solid #e6a23c;
				}

				&.function-message {
					background-color: #f0f9eb;
					border-left: 4px solid #67c23a;
				}

				&.round-start {
					margin-top: 25px;
				}

				.round-divider {
					position: absolute;
					top: -20px;
					left: 0;
					width: 100%;
					display: flex;
					justify-content: center;

					.round-tag {
						background-color: #409eff;
						color: white;
						padding: 2px 10px;
						border-radius: 12px;
						font-size: 12px;
					}
				}

				.message-header {
					display: flex;
					justify-content: space-between;
					margin-bottom: 8px;

					.message-type {
						display: flex;
						align-items: center;
						gap: 8px;

						.score-tag {
							margin-left: 5px;
						}
					}

					.message-time {
						font-size: 12px;
						color: #909399;
					}
				}

				.message-content {
					font-size: 14px;
					line-height: 1.6;
					word-break: break-word;
					white-space: pre-wrap;

					.ai-content {
						.message-text {
							margin-bottom: 10px;
						}

						.score-reason {
							margin-top: 8px;
						}

						.model-info {
							margin-top: 8px;
							display: flex;
							gap: 8px;
							flex-wrap: wrap;
						}
					}

					.function-content {
						.function-title {
							font-size: 13px;
							color: #606266;
						}

						.function-details {
							padding: 10px;
							background-color: #f8f8f8;
							border-radius: 4px;

							pre {
								overflow-x: auto;
								font-family: monospace;
							}

							.score-positive {
								color: #67c23a;
								font-weight: bold;
							}

							.score-negative {
								color: #f56c6c;
								font-weight: bold;
							}

							.score-neutral {
								color: #909399;
							}
						}
					}
				}

				.message-actions {
					display: flex;
					justify-content: flex-end;
					margin-top: 8px;
				}
			}
		}
	}
}

// Animation effects
.fade-in {
	animation: fadeIn 0.5s ease-out forwards;
}

.fade-in-up {
	animation: fadeInUp 0.5s ease-out forwards;
	opacity: 0;
}

@keyframes fadeIn {
	from {
		opacity: 0;
	}
	to {
		opacity: 1;
	}
}

@keyframes fadeInUp {
	from {
		opacity: 0;
		transform: translateY(20px);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}
</style>
