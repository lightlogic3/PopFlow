<script setup lang="ts">
import { ref, onMounted, watch, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import type { RagMessage, ChatSettings, SessionResponse } from "@/types/chat";
import { MEMORY_TYPES } from "@/types/chat";
import { Delete, UserFilled, Service } from "@element-plus/icons-vue";
import { ragChatTokenStream, clearRagSession, deleteRagSession, changeMemoryType, getChatMessages } from "@/api/chat";
const router = useRouter();
const route = useRoute();
const messagesLoading = ref(false);
const sending = ref(false);
const sessionId = ref<string>("");
const userMessage = ref("");
const chatMessages = ref<RagMessage[]>([]);
const sessionInfo = ref<SessionResponse | null>(null);
const selectedMemoryType = ref("");

// 聊天设置
const chatSettings = ref<ChatSettings>({
	roleId: "",
	level: 1,
	userLevel: 1,
	topK: 3,
	temperature: 0.7,
	templateType: "chat",
	includeSources: true,
});

// 获取URL中的会话ID参数
onMounted(() => {
	const sid = route.query.sessionId as string;
	if (sid) {
		sessionId.value = sid;
		fetchSessionInfo(sid);
	}

	// 从本地存储加载之前的设置
	const savedSettings = localStorage.getItem("ragChatSettings");
	if (savedSettings) {
		try {
			const settings = JSON.parse(savedSettings);
			chatSettings.value = { ...chatSettings.value, ...settings };

			// 如果会话ID存在，不需要回填到输入框
			// 如果会话ID不存在，且有缓存的上一次消息，则回填到输入框
			if (!sid && settings.lastMessage) {
				userMessage.value = settings.lastMessage;
			}
		} catch (error) {
			console.error("解析缓存的聊天设置失败", error);
		}
	}
});

// 监听会话ID变化
watch(
	() => sessionId.value,
	(newSessionId) => {
		if (newSessionId) {
			fetchSessionInfo(newSessionId);
		} else {
			sessionInfo.value = null;
			chatMessages.value = [];
		}
	},
);

// 获取会话信息
const fetchSessionInfo = async (sid: string) => {
	const response = await getChatMessages(sid);
	// messagesLoading.value = true;
	// try {
	// 	const response = await getSessionInfo(sid);
	// 	if (response && response.data) {
	// 		sessionInfo.value = response.data;
	// 		selectedMemoryType.value = response.data.memory_type;
	//
	if (response) {
		chatMessages.value = response;
	}
	// 	}
	// } catch (error) {
	// 	console.error("获取会话信息失败", error);
	// 	ElMessage.error("获取会话信息失败");
	// } finally {
	// 	messagesLoading.value = false;
	// }
};

// 发送消息
const sendMessage = async () => {
	if (!userMessage.value.trim()) {
		ElMessage.warning("请输入消息内容");
		return;
	}

	// 保存聊天设置到本地存储
	const settingsToSave = {
		...chatSettings.value,
		lastMessage: userMessage.value,
	};
	localStorage.setItem("ragChatSettings", JSON.stringify(settingsToSave));

	sending.value = true;

	// 添加用户消息到列表
	const userMsg: RagMessage = {
		role: "user",
		content: userMessage.value,
	};
	chatMessages.value.push(userMsg);

	// 创建一个空的AI响应消息
	const aiResponseMsg: RagMessage = {
		role: "assistant",
		content: "",
	};
	chatMessages.value.push(aiResponseMsg);

	// 构建请求数据
	const requestData = {
		message: userMessage.value,
		role_id: chatSettings.value.roleId,
		level: chatSettings.value.level,
		user_level: chatSettings.value.userLevel,
		session_id: sessionId.value || undefined,
		stream: true,
		top_k: chatSettings.value.topK,
		temperature: chatSettings.value.temperature,
		template_type: chatSettings.value.templateType,
		include_sources: chatSettings.value.includeSources,
		user_id: "admin",
		way: "all",
	};

	// 清空输入框
	userMessage.value = "";

	// 收集原始数据块，用于调试
	const rawChunks: string[] = [];

	try {
		// 使用逐字符流式API
		const response = await ragChatTokenStream(
			requestData,
			// 处理标准处理后的token
			(token) => {
				console.log("处理后的token:", token);
				// 直接将每个token添加到响应消息中
				aiResponseMsg.content += token;
			},
			// 处理原始数据块
			(rawChunk) => {
				console.log("原始数据块:", rawChunk);
				rawChunks.push(rawChunk);
			},
			// 处理错误
			(error) => {
				console.error("流式响应处理错误", error);
				ElMessage.error("接收消息失败");
			},
		);

		// 记录所有收到的原始数据，用于调试
		console.log("所有原始数据块:", rawChunks);

		// 处理响应头中的会话ID
		if (!sessionId.value && response.headers) {
			const sessionIdFromHeader = response.headers.get("session-id");
			if (sessionIdFromHeader) {
				sessionId.value = sessionIdFromHeader;
				// 更新URL
				router.replace({
					query: { ...route.query, sessionId: sessionId.value },
				});
			}
		}
	} catch (error) {
		console.error("发送消息失败", error);
		ElMessage.error("发送消息失败");
		// 移除空的AI响应消息
		chatMessages.value.pop();
	} finally {
		sending.value = false;
	}
};

// 清空会话
const handleClear = () => {
	if (!sessionId.value) return;

	ElMessageBox.confirm("确定要清空该聊天会话的所有消息吗？", "提示", {
		confirmButtonText: "确定",
		cancelButtonText: "取消",
		type: "warning",
	})
		.then(async () => {
			try {
				await clearRagSession(sessionId.value);
				ElMessage.success("清空成功");
				chatMessages.value = [];
			} catch (error) {
				console.error("清空失败", error);
				ElMessage.error("清空失败");
			}
		})
		.catch(() => {
			// 用户取消操作
		});
};

// 删除会话
const handleDelete = () => {
	if (!sessionId.value) return;

	ElMessageBox.confirm("确定要删除该聊天会话吗？", "提示", {
		confirmButtonText: "确定",
		cancelButtonText: "取消",
		type: "warning",
	})
		.then(async () => {
			try {
				await deleteRagSession(sessionId.value);
				ElMessage.success("删除成功");
				router.push("/rag-chat/list");
			} catch (error) {
				console.error("删除失败", error);
				ElMessage.error("删除失败");
			}
		})
		.catch(() => {
			// 用户取消操作
		});
};

// 更新记忆类型
const handleMemoryTypeChange = async () => {
	if (!sessionId.value) return;

	try {
		await changeMemoryType(sessionId.value, selectedMemoryType.value);
		ElMessage.success("记忆类型更新成功");

		// 更新本地状态
		if (sessionInfo.value) {
			sessionInfo.value.memory_type = selectedMemoryType.value;
		}
	} catch (error) {
		console.error("更新记忆类型失败", error);
		ElMessage.error("更新记忆类型失败");
	}
};

// 返回列表页
const goBack = () => {
	router.push("/rag-chat/list");
};

// 是否为新会话
const isNewChat = computed(() => !sessionId.value);

// 生成会话标题
const chatTitle = computed(() => {
	if (sessionInfo.value?.session_id) {
		return sessionInfo.value.session_id;
	}
	return "新的聊天会话";
});
</script>

<template>
	<div class="rag-chat-container">
		<div class="chat-header">
			<a class="back-button" @click="goBack">
				<el-icon>
					<ArrowLeft />
				</el-icon>
				返回列表
			</a>

			<h1 class="chat-title">{{ chatTitle }}</h1>

			<div class="header-actions" v-if="!isNewChat">
				<el-button type="danger" size="small" @click="handleDelete">
					<el-icon>
						<Delete />
					</el-icon>
					删除会话
				</el-button>
				<el-button type="warning" size="small" @click="handleClear">
					<el-icon>
						<RemoveFilled />
					</el-icon>
					清空消息
				</el-button>
			</div>
		</div>

		<div class="chat-main">
			<div class="chat-messages" v-loading="messagesLoading">
				<el-empty v-if="chatMessages.length === 0" description="开始一个新的对话吧" />

				<div v-for="(message, index) in chatMessages" :key="index" :class="['message', message.role]">
					<div class="message-avatar">
						<el-avatar :icon="message.role === 'user' ? UserFilled : Service" />
					</div>
					<div class="message-content">
						<div class="message-text">{{ message.content }}</div>
					</div>
				</div>
			</div>

			<div class="chat-input-area">
				<el-input
					v-model="userMessage"
					type="textarea"
					:rows="3"
					placeholder="请输入消息..."
					:disabled="sending"
					@keyup.ctrl.enter="sendMessage"
				/>
				<div class="input-actions">
					<el-button type="primary" :loading="sending" @click="sendMessage"> 发送 </el-button>
				</div>
			</div>
		</div>

		<div class="chat-sidebar">
			<div class="sidebar-section">
				<h3 class="section-title">聊天设置</h3>

				<div class="setting-item">
					<div class="setting-label">角色ID</div>
					<el-input v-model="chatSettings.roleId" placeholder="请输入角色ID" />
				</div>

				<div class="setting-item">
					<div class="setting-label">角色等级</div>
					<el-input-number v-model="chatSettings.level" :min="1" :max="100" />
				</div>

				<div class="setting-item">
					<div class="setting-label">用户等级</div>
					<el-input-number v-model="chatSettings.userLevel" :min="1" :max="100" />
				</div>

				<div class="setting-item">
					<div class="setting-label">Top K</div>
					<el-input-number v-model="chatSettings.topK" :min="1" :max="10" />
				</div>

				<div class="setting-item">
					<div class="setting-label">温度</div>
					<el-slider v-model="chatSettings.temperature" :min="0" :max="1" :step="0.05" />
				</div>

				<div class="setting-item">
					<div class="setting-label">模板类型</div>
					<el-input v-model="chatSettings.templateType" placeholder="模板类型" />
				</div>

				<div class="setting-item">
					<div class="setting-label">包含引用来源</div>
					<el-switch v-model="chatSettings.includeSources" />
				</div>
			</div>

			<div class="sidebar-section" v-if="!isNewChat">
				<h3 class="section-title">记忆类型</h3>
				<el-select v-model="selectedMemoryType" class="memory-type-select" @change="handleMemoryTypeChange">
					<el-option v-for="type in MEMORY_TYPES" :key="type.value" :label="type.label" :value="type.value" />
				</el-select>
			</div>

			<div class="sidebar-section" v-if="!isNewChat">
				<h3 class="section-title">会话信息</h3>
				<div class="info-item">
					<span class="info-label">会话ID</span>
					<span class="info-value">{{ sessionId }}</span>
				</div>
				<div class="info-item" v-if="sessionInfo">
					<span class="info-label">创建时间</span>
					<span class="info-value">{{ sessionInfo.created_at }}</span>
				</div>
				<div class="info-item" v-if="sessionInfo">
					<span class="info-label">消息数量</span>
					<span class="info-value">{{ sessionInfo.message_count }}</span>
				</div>
			</div>
		</div>
	</div>
</template>

<style scoped>
.rag-chat-container {
	height: 100%;
	display: grid;
	grid-template-rows: auto 1fr;
	grid-template-columns: 1fr 300px;
	grid-template-areas:
		"header header"
		"main sidebar";
	gap: 20px;
	padding: 20px;
}

.chat-header {
	grid-area: header;
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding-bottom: 15px;
	border-bottom: 1px solid var(--el-border-color-light);
}

.back-button {
	display: flex;
	align-items: center;
	color: var(--el-color-primary);
	cursor: pointer;
	font-size: 14px;
}

.back-button .el-icon {
	margin-right: 5px;
}

.chat-title {
	font-size: 18px;
	font-weight: 600;
	margin: 0;
	flex: 1;
	text-align: center;
}

.header-actions {
	display: flex;
	gap: 10px;
}

.chat-main {
	grid-area: main;
	display: flex;
	flex-direction: column;
}

.chat-messages {
	flex: 1;
	overflow-y: auto;
	padding: 15px;
	background-color: var(--el-bg-color-page);
	border-radius: 8px;
	margin-bottom: 20px;
}

.message {
	display: flex;
	margin-bottom: 20px;
}

.message.user {
	flex-direction: row-reverse;
}

.message-avatar {
	flex-shrink: 0;
	margin: 0 10px;
}

.message-content {
	max-width: 70%;
}

.message.user .message-content {
	background-color: var(--el-color-primary-light-9);
	border-radius: 10px 0 10px 10px;
}

.message.assistant .message-content {
	background-color: var(--el-fill-color-light);
	border-radius: 0 10px 10px 10px;
}

.message-text {
	padding: 10px 15px;
	white-space: pre-wrap;
	word-break: break-word;
}

.chat-input-area {
	display: flex;
	flex-direction: column;
	gap: 10px;
}

.input-actions {
	display: flex;
	justify-content: flex-end;
}

.chat-sidebar {
	grid-area: sidebar;
	background-color: var(--el-bg-color);
	border-radius: 8px;
	padding: 15px;
	border: 1px solid var(--el-border-color-light);
	overflow-y: auto;
}

.sidebar-section {
	margin-bottom: 20px;
}

.section-title {
	font-size: 16px;
	font-weight: 600;
	margin-bottom: 15px;
	padding-bottom: 10px;
	border-bottom: 1px solid var(--el-border-color-light);
}

.setting-item {
	margin-bottom: 15px;
}

.setting-label {
	margin-bottom: 5px;
	font-size: 14px;
	color: var(--el-text-color-regular);
}

.memory-type-select {
	width: 100%;
}

.info-item {
	display: flex;
	justify-content: space-between;
	margin-bottom: 10px;
}

.info-label {
	color: var(--el-text-color-secondary);
}

.info-value {
	color: var(--el-text-color-primary);
	word-break: break-all;
}
</style>
