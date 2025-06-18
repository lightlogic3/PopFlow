<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import type { ChatSession } from "@/types/chat";
import { getChatSessions, deleteChatSession, clearChatSession, updateChatSession } from "@/api/chat";
import { formatDate } from "@/utils";
import {
	Edit,
	Delete,
	Timer,
	RemoveFilled,
	Refresh,
	View,
	Calendar,
	Trophy,
	Box,
	ChatDotRound,
	User,
} from "@element-plus/icons-vue";
const router = useRouter();
const loading = ref(false);
const chatSessions = ref<ChatSession[]>([]);
const editingSession = ref<string | null>(null);
const sessionNameInput = ref("");
const sessionSummaryInput = ref("");

/**
 * Get chat session list
 */
const fetchChatSessions = async () => {
	loading.value = true;
	try {
		const response = await getChatSessions();
		chatSessions.value = Array.isArray(response) && response.length > 0 ? response : [];
	} catch (error) {
		console.error("Failed to get chat session list", error);
		ElMessage.error("Failed to get chat session list");
		chatSessions.value = [];
	} finally {
		loading.value = false;
	}
};

/**
 * View chat session details
 */
const handleView = (id: string) => {
	router.push(`/chat/detail/${id}`);
};

/**
 * Clear chat session
 */
const handleClear = (id: string) => {
	ElMessageBox.confirm("Are you sure you want to clear all messages in this chat session?", "Notice", {
		confirmButtonText: "Confirm",
		cancelButtonText: "Cancel",
		type: "warning",
	})
		.then(async () => {
			try {
				await clearChatSession(id);
				ElMessage.success("Cleared successfully");
				fetchChatSessions();
			} catch (error) {
				console.error("Clear failed", error);
				ElMessage.error("Clear failed");
			}
		})
		.catch(() => {
			// User canceled operation
		});
};

/**
 * Delete chat session
 */
const handleDelete = (id: string) => {
	ElMessageBox.confirm("Are you sure you want to delete this chat session?", "Notice", {
		confirmButtonText: "Confirm",
		cancelButtonText: "Cancel",
		type: "warning",
	})
		.then(async () => {
			try {
				await deleteChatSession(id);
				ElMessage.success("Deleted successfully");
				fetchChatSessions();
			} catch (error) {
				console.error("Delete failed", error);
				ElMessage.error("Delete failed");
			}
		})
		.catch(() => {
			// User canceled operation
		});
};

/**
 * Edit session name and summary
 */
const startEdit = (session: ChatSession) => {
	editingSession.value = session.session_id;
	sessionNameInput.value = session.session_name || "";
	sessionSummaryInput.value = session.session_summary || "";
};

/**
 * Save edited session information
 */
const saveEdit = async (sessionId: string) => {
	try {
		await updateChatSession(sessionId, {
			title: sessionNameInput.value,
			summary: sessionSummaryInput.value,
		});
		ElMessage.success("Updated successfully");
		fetchChatSessions();
	} catch (error) {
		console.error("Update failed", error);
		ElMessage.error("Update failed");
	} finally {
		editingSession.value = null;
	}
};

/**
 * Cancel editing
 */
const cancelEdit = () => {
	editingSession.value = null;
};

/**
 * Get session name (use default name if empty)
 */
const getSessionName = (session: ChatSession) => {
	return session.session_name || `Session ${formatDate(session.created_at).split(" ")[0]}`;
};

/**
 * Format session status
 */
const formatStatus = (status: string) => {
	const statusMap: Record<string, string> = {
		active: "Active",
		archived: "Archived",
		deleted: "Deleted",
	};
	return statusMap[status] || status;
};

/**
 * Get tag type based on session status
 */
const getStatusType = (status: string): "success" | "warning" | "info" | "primary" | "danger" => {
	const typeMap: Record<string, "success" | "warning" | "info" | "primary" | "danger"> = {
		active: "success",
		archived: "info",
		deleted: "danger",
	};
	return typeMap[status] || "primary";
};

onMounted(() => {
	fetchChatSessions();
});
</script>

<template>
	<div class="chat-container">
		<div class="header">
			<h1 class="title">Chat Session Management</h1>
			<el-button type="primary" @click="fetchChatSessions">
				<el-icon><Refresh /></el-icon>
				Refresh
			</el-button>
		</div>

		<div class="chat-grid" v-loading="loading">
			<el-empty v-if="chatSessions.length === 0" description="No chat records" />

			<el-card
				v-for="session in chatSessions"
				:key="session.session_id"
				class="chat-card"
				:body-style="{ padding: '0' }"
				shadow="hover"
			>
				<div class="card-header">
					<div class="header-content">
						<template v-if="editingSession === session.session_id">
							<el-input v-model="sessionNameInput" placeholder="Please enter session name" maxlength="50" class="edit-input" />
						</template>
						<template v-else>
							<h3 class="card-title">{{ getSessionName(session) }}</h3>
							<el-tag :type="getStatusType(session.session_status)" size="small">{{
								formatStatus(session.session_status)
							}}</el-tag>
						</template>
					</div>
					<div class="header-actions" v-if="editingSession !== session.session_id">
						<el-button type="primary" size="small" circle @click="startEdit(session)" title="Edit session info">
							<el-icon><Edit /></el-icon>
						</el-button>
					</div>
				</div>

				<div class="card-body">
					<div class="info-grid">
						<div class="info-item">
							<el-icon><User /></el-icon>
							<span class="info-label">Role:</span>
							<el-tooltip :content="session.role_id" placement="top" :disabled="!session.role_id">
								<span class="info-value ellipsis">{{ session.role_id }}</span>
							</el-tooltip>
						</div>
						<div class="info-item">
							<el-icon><ChatDotRound /></el-icon>
							<span class="info-label">Messages:</span>
							<span class="info-value">{{ session.message_count }}</span>
						</div>
						<div class="info-item">
							<el-icon><Trophy /></el-icon>
							<span class="info-label">Token:</span>
							<span class="info-value">{{ session.total_tokens }}</span>
						</div>
						<div class="info-item">
							<el-icon><Box /></el-icon>
							<span class="info-label">Model:</span>
							<el-tooltip :content="session.model_name" placement="top" :disabled="!session.model_name">
								<span class="info-value ellipsis">{{ session.model_name }}</span>
							</el-tooltip>
						</div>
						<div class="info-item">
							<el-icon><Calendar /></el-icon>
							<span class="info-label">Created:</span>
							<el-tooltip :content="formatDate(session.created_at)" placement="top" :disabled="!session.created_at">
								<span class="info-value">{{ formatDate(session.created_at, "YYYY/MM/DD") }}</span>
							</el-tooltip>
						</div>
						<div class="info-item">
							<el-icon><Timer /></el-icon>
							<span class="info-label">Last interaction:</span>
							<el-tooltip
								:content="formatDate(session.last_message_time)"
								placement="top"
								:disabled="!session.last_message_time"
							>
								<span class="info-value">{{ formatDate(session.last_message_time, "YYYY/MM/DD") }}</span>
							</el-tooltip>
						</div>
					</div>

					<div class="summary-section">
						<div class="summary-header">
							<span>Session Summary</span>
							<el-button v-if="editingSession !== session.session_id" type="text" @click="startEdit(session)">
								<el-icon><Edit /></el-icon>
							</el-button>
						</div>
						<template v-if="editingSession === session.session_id">
							<el-input
								v-model="sessionSummaryInput"
								type="textarea"
								:rows="2"
								placeholder="Please enter session summary"
								maxlength="200"
								class="edit-textarea"
							/>
							<div class="edit-actions">
								<el-button type="success" size="small" @click="saveEdit(session.session_id)">Save</el-button>
								<el-button size="small" @click="cancelEdit">Cancel</el-button>
							</div>
						</template>
						<el-tooltip
							v-else
							:content="session.session_summary || 'No summary information'"
							placement="top"
							:disabled="!session.session_summary"
						>
							<div class="summary-content">
								{{ session.session_summary || "No summary information" }}
							</div>
						</el-tooltip>
					</div>
				</div>

				<div class="card-footer">
					<el-button type="primary" size="small" @click="handleView(session.session_id)">
						<el-icon><View /></el-icon>
						View
					</el-button>
					<el-button type="warning" size="small" @click="handleClear(session.session_id)">
						<el-icon><Delete /></el-icon>
						Clear
					</el-button>
					<el-button type="danger" size="small" @click="handleDelete(session.session_id)">
						<el-icon><RemoveFilled /></el-icon>
						Delete
					</el-button>
				</div>
			</el-card>
		</div>
	</div>
</template>

<style scoped>
.chat-container {
	padding: 16px;
	background-color: var(--el-bg-color-page, #f5f7fa);
	min-height: calc(100vh - 60px);
}

.header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 20px;
}

.title {
	font-size: 22px;
	color: var(--el-text-color-primary);
	margin: 0;
	font-weight: 600;
}

.chat-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
	gap: 16px;
}

.chat-card {
	border-radius: 8px;
	overflow: hidden;
	transition: all 0.3s ease;
	height: 100%;
	display: flex;
	flex-direction: column;
}

.chat-card:hover {
	transform: translateY(-3px);
}

.card-header {
	background-color: var(--el-color-primary-light-9);
	padding: 10px 12px;
	display: flex;
	justify-content: space-between;
	align-items: center;
	border-bottom: 1px solid var(--el-border-color-light);
}

.header-content {
	flex: 1;
	display: flex;
	align-items: center;
	gap: 8px;
}

.card-title {
	font-size: 16px;
	color: var(--el-text-color-primary);
	margin: 0;
	font-weight: 600;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
	max-width: 200px;
}

.card-body {
	padding: 12px;
	flex: 1;
	display: flex;
	flex-direction: column;
	gap: 12px;
}

.info-grid {
	display: grid;
	grid-template-columns: repeat(2, 1fr);
	gap: 8px;
	background-color: var(--el-fill-color-light);
	border-radius: 6px;
	padding: 8px;
}

.info-item {
	display: flex;
	align-items: center;
	gap: 4px;
	font-size: 13px;
	overflow: hidden;
}

.info-label {
	color: var(--el-text-color-secondary);
	font-weight: 500;
	white-space: nowrap;
}

.info-value {
	color: var(--el-text-color-primary);
	flex: 1;
}

.ellipsis {
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

.summary-section {
	background-color: var(--el-fill-color-light);
	border-radius: 6px;
	padding: 8px;
	flex: 1;
	display: flex;
	flex-direction: column;
	min-height: 80px;
}

.summary-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	font-size: 14px;
	font-weight: 600;
	margin-bottom: 6px;
	color: var(--el-text-color-primary);
}

.summary-content {
	font-size: 13px;
	color: var(--el-text-color-regular);
	line-height: 1.4;
	white-space: pre-line;
	overflow: hidden;
	position: relative;
	max-height: 70px;
	text-overflow: ellipsis;
	display: -webkit-box;
	-webkit-line-clamp: 3;
	-webkit-box-orient: vertical;
}

.card-footer {
	padding: 10px 12px;
	border-top: 1px solid var(--el-border-color-light);
	display: flex;
	justify-content: space-between;
	gap: 8px;
	background-color: var(--el-bg-color);
}

.edit-input {
	margin-bottom: 8px;
}

.edit-textarea {
	margin-bottom: 8px;
}

.edit-actions {
	display: flex;
	justify-content: flex-end;
	gap: 8px;
	margin-top: 8px;
}
</style>
