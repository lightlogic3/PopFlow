<script setup lang="ts">
import { ref, onMounted, computed, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import { ElMessage, ElNotification } from "element-plus";
import { formatDate } from "@/utils";
import {
	ArrowLeft,
	ChatLineRound,
	InfoFilled,
	UserFilled,
	Plus,
	DataAnalysis,
	DocumentAdd,
	Select,
	Connection,
} from "@element-plus/icons-vue";
import type { ChatSession } from "@/types/chat";
import { getChatSessionById, getChatMessages } from "@/api/chat";

// 实际API返回的聊天消息接口
interface ChatMessageRaw {
	user_id: string;
	session_id: string;
	chat_role_id: string;
	conversation_id: string;
	message_id: string;
	parent_message_id: string | null;
	role: "user" | "assistant";
	content: string;
	prompt_tokens: number;
	completion_tokens: number;
	total_tokens: number;
	model_name: string;
	id: number;
	created_at: string;
}

// 数据集类型
type DatasetType = "dpo" | "sft" | "conversation";

// 数据集选项
interface DatasetOption {
	id: number;
	name: string;
	type: DatasetType;
	description?: string;
}

const router = useRouter();
const route = useRoute();
const loading = ref(false);
const messagesLoading = ref(false);
const sessionId = ref<string>("");
const chatSession = ref<ChatSession | null>(null);
const chatMessages = ref<ChatMessageRaw[]>([]);
const selectedMemoryType = ref("");
const sessionInfo = ref<any>(null); // 会话信息
const selectedMessageIds = ref<string[]>([]); // 已选中的消息ID

// 数据集相关状态
const showDatasetDialog = ref(false);
const datasetType = ref<DatasetType>("conversation");
const datasetOptions = ref<DatasetOption[]>([
	{ id: 1, name: "对话数据集示例", type: "conversation", description: "用于对话训练的数据集" },
	{ id: 2, name: "DPO偏好数据集示例", type: "dpo", description: "用于DPO偏好训练的数据集" },
	{ id: 3, name: "SFT微调数据集示例", type: "sft", description: "用于SFT微调的数据集" },
]);
const selectedDataset = ref<number | null>(null);
const processingDataset = ref(false);

// 初始化页面
const initPage = async () => {
	const id = route.params.id as string;
	sessionId.value = id;
	await Promise.all([fetchSessionDetail(id), fetchMessages(id)]);
};

// 获取会话详情
const fetchSessionDetail = async (id: string) => {
	loading.value = true;
	try {
		// request.ts的extractResponseData已处理响应，返回的直接是数据对象而非AxiosResponse
		const response: any = await getChatSessionById(id);

		if (response) {
			chatSession.value = response;
			selectedMemoryType.value = response.memory_type;
		} else {
			// 使用模拟数据
			// const mockSession: any = mockChatSessions.find((s: any) => s.id === id);
			// if (mockSession) {
			// 	chatSession.value = mockSession;
			// 	selectedMemoryType.value = mockSession.memory_type;
			// } else {
			// 	ElMessage.error("会话不存在");
			// 	router.push("/chat/list");
			// }
		}
	} catch (error) {
		console.error("获取聊天会话详情失败", error);
		ElMessage.error("获取聊天会话详情失败");

		// 使用模拟数据
		// const mockSession: any = mockChatSessions.find((s: any) => s.id === id);
		// if (mockSession) {
		// 	chatSession.value = mockSession;
		// 	selectedMemoryType.value = mockSession.memory_type;
		// }
	} finally {
		loading.value = false;
	}
};

// 获取会话消息
const fetchMessages = async (id: string) => {
	messagesLoading.value = true;
	try {
		// request.ts的extractResponseData已处理响应，返回的直接是数据数组而非AxiosResponse
		const response: any = await getChatMessages(id);

		if (response && Array.isArray(response)) {
			chatMessages.value = response as ChatMessageRaw[];
		} else {
			// 使用模拟数据
			// chatMessages.value = mockChatMessages.filter((m) => m.session_id === id) as ChatMessageRaw[];
		}

		// 提取会话基本信息
		if (chatMessages.value.length > 0) {
			const firstMsg = chatMessages.value[0];
			sessionInfo.value = {
				user_id: firstMsg.user_id,
				session_id: firstMsg.session_id,
				chat_role_id: firstMsg.chat_role_id,
				model_name: firstMsg.model_name,
				created_at: firstMsg.created_at,
			};
		}
	} catch (error) {
		console.error("获取聊天消息失败", error);
		ElMessage.error("获取聊天消息失败");
	} finally {
		messagesLoading.value = false;
	}
};

// 返回列表页
const goBack = () => {
	router.push("/chat/list");
};

// 计算统计信息
const statistics = computed(() => {
	if (!chatMessages.value.length) return { total: 0, user: 0, assistant: 0, totalTokens: 0 };

	const total = chatMessages.value.length;
	const user = chatMessages.value.filter((msg) => msg.role === "user").length;
	const assistant = chatMessages.value.filter((msg) => msg.role === "assistant").length;
	const totalTokens = chatMessages.value.reduce((sum, msg) => sum + (msg.total_tokens || 0), 0);

	return { total, user, assistant, totalTokens };
});

// 获取聊天日期分组
const chatDays = computed(() => {
	const days = new Map();

	chatMessages.value.forEach((msg) => {
		const date = new Date(msg.created_at);
		const dayKey = formatDate(date, "YYYY-MM-DD");

		if (!days.has(dayKey)) {
			days.set(dayKey, []);
		}
		days.get(dayKey).push(msg);
	});

	return Array.from(days.entries()).map(([day, messages]) => ({
		day,
		messages,
		formattedDay: formatChatDay(day),
	}));
});

// 格式化聊天日期显示
const formatChatDay = (dateStr: string) => {
	const date = new Date(dateStr);
	const today = new Date();
	const yesterday = new Date(today);
	yesterday.setDate(yesterday.getDate() - 1);

	if (dateStr === formatDate(today, "YYYY-MM-DD")) {
		return "今天";
	} else if (dateStr === formatDate(yesterday, "YYYY-MM-DD")) {
		return "昨天";
	} else {
		return formatDate(date, "YYYY年MM月DD日");
	}
};

// 切换消息选中状态
const toggleMessageSelection = (messageId: string) => {
	const index = selectedMessageIds.value.indexOf(messageId);
	if (index !== -1) {
		selectedMessageIds.value.splice(index, 1);
	} else {
		selectedMessageIds.value.push(messageId);
	}
};

// 检查消息是否已选中
const isMessageSelected = (messageId: string) => {
	return selectedMessageIds.value.includes(messageId);
};

// 获取已选中的消息对象
const getSelectedMessages = () => {
	return chatMessages.value.filter((msg) => selectedMessageIds.value.includes(msg.message_id));
};

// 清除所有选中
const clearAllSelections = () => {
	selectedMessageIds.value = [];
};

// 打开添加到数据集对话框
const openDatasetDialog = () => {
	if (selectedMessageIds.value.length === 0) {
		ElMessage.warning("请先选择至少一条消息");
		return;
	}

	// 根据选中的消息数量自动选择合适的数据集类型
	const selectedMessages = getSelectedMessages();
	const hasUserMessage = selectedMessages.some((msg) => msg.role === "user");
	const hasAiMessage = selectedMessages.some((msg) => msg.role === "assistant");

	if (selectedMessages.length === 1) {
		if (hasUserMessage) {
			datasetType.value = "sft";
		} else {
			ElMessage.warning("单独选择AI消息无法添加到数据集，请选择用户消息或成对的对话");
			return;
		}
	} else if (selectedMessages.length === 2 && hasUserMessage && hasAiMessage) {
		datasetType.value = "dpo";
	} else {
		datasetType.value = "conversation";
	}

	// 根据类型自动选择第一个匹配的数据集
	const matchingDataset = datasetOptions.value.find((dataset) => dataset.type === datasetType.value);
	selectedDataset.value = matchingDataset ? matchingDataset.id : null;

	showDatasetDialog.value = true;
};

// 确认添加到数据集
const confirmAddToDataset = async () => {
	if (!selectedDataset.value) {
		ElMessage.warning("请选择一个数据集");
		return;
	}

	processingDataset.value = true;

	try {
		const selectedMessages = getSelectedMessages();
		const selectedDatasetInfo = datasetOptions.value.find((d) => d.id === selectedDataset.value);

		if (!selectedDatasetInfo) {
			throw new Error("找不到所选数据集");
		}

		// 根据不同的数据集类型处理数据
		let result;
		switch (selectedDatasetInfo.type) {
			case "dpo":
				result = await processDpoDataset(selectedMessages, selectedDatasetInfo);
				break;
			case "sft":
				result = await processSftDataset(selectedMessages, selectedDatasetInfo);
				break;
			case "conversation":
				result = await processConversationDataset(selectedMessages, selectedDatasetInfo);
				break;
			default:
				throw new Error("不支持的数据集类型");
		}
		console.log(result);
		ElNotification({
			title: "成功",
			message: `成功添加到"${selectedDatasetInfo.name}"数据集`,
			type: "success",
		});

		// 关闭对话框并清除选择
		showDatasetDialog.value = false;
		clearAllSelections();
	} catch (error) {
		console.error("添加到数据集失败", error);
		ElMessage.error("添加到数据集失败: " + (error as Error).message);
	} finally {
		processingDataset.value = false;
	}
};

// DPO偏好数据集处理
const processDpoDataset = async (messages: ChatMessageRaw[], dataset: DatasetOption) => {
	// 验证数据是否符合DPO格式要求（问题+2个回答）
	const userMsg = messages.find((m) => m.role === "user");
	const aiMsgs = messages.filter((m) => m.role === "assistant");

	if (!userMsg || aiMsgs.length !== 1) {
		throw new Error("DPO数据集需要1个用户问题和1个AI回答");
	}

	// 构建DPO数据
	const dpoData = {
		dataset_id: dataset.id,
		query: userMsg.content,
		chosen_response: aiMsgs[0].content,
		rejected_response: "", // 在实际应用中，可能需要用户指定或从其他来源获取
		raw_data: JSON.stringify(messages),
	};

	// 此处调用API将数据添加到DPO数据集
	console.log("添加到DPO数据集:", dpoData);

	// 预留给API调用
	// return await addToDpoDataset(dpoData);
	return true;
};

// SFT微调数据集处理
const processSftDataset = async (messages: ChatMessageRaw[], dataset: DatasetOption) => {
	// 验证数据是否符合SFT格式要求（通常是指令+输出）
	if (messages.length < 1) {
		throw new Error("SFT数据集至少需要1条消息");
	}

	// 找出用户消息作为指令
	const userMsg = messages.find((m) => m.role === "user");
	if (!userMsg) {
		throw new Error("SFT数据集需要至少一条用户消息作为指令");
	}

	// 找出AI回复作为输出
	const aiMsg = messages.find((m) => m.role === "assistant");

	// 构建SFT数据
	const sftData = {
		dataset_id: dataset.id,
		instruction: userMsg.content,
		input: "", // 可选输入，在某些场景可能需要
		output: aiMsg ? aiMsg.content : "",
		raw_data: JSON.stringify(messages),
	};

	// 此处调用API将数据添加到SFT数据集
	console.log("添加到SFT数据集:", sftData);

	// 预留给API调用
	// return await addToSftDataset(sftData);
	return true;
};

// 多轮对话数据集处理
const processConversationDataset = async (messages: ChatMessageRaw[], dataset: DatasetOption) => {
	// 验证是否有足够的消息
	if (messages.length < 2) {
		throw new Error("对话数据集至少需要2条消息");
	}

	// 按创建时间排序消息
	const sortedMessages = [...messages].sort(
		(a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
	);

	// 构建对话格式数据
	const conversationId = `conv_${Date.now()}`;
	const conversationEntries = sortedMessages.map((msg, index) => ({
		dataset_id: dataset.id,
		conversation_id: conversationId,
		sequence_order: index + 1,
		role: msg.role,
		content: msg.content,
		has_tool_calls: 0,
		tool_calls: null,
		tool_name: null,
		loss_weight: 1.0,
		raw_message: JSON.stringify(msg),
	}));

	// 此处调用API将数据添加到会话数据集
	console.log("添加到对话数据集:", conversationEntries);

	// 预留给API调用
	// return await addToConversationDataset(conversationEntries);
	return true;
};

// 获取当前数据集类型的过滤选项
const filteredDatasetOptions = computed(() => {
	return datasetOptions.value.filter((d) => d.type === datasetType.value);
});

/**
 * 截断文本，超过最大长度时添加省略号
 */
const truncateText = (text: string, maxLength: number): string => {
	if (!text) return "";
	return text.length > maxLength ? text.substring(0, maxLength) + "..." : text;
};

/**
 * DPO预览数据
 */
const dpoPreviewData = computed(() => {
	const selectedMessages = getSelectedMessages();
	const userMsg = selectedMessages.find((m) => m.role === "user");
	const aiMsg = selectedMessages.find((m) => m.role === "assistant");

	return {
		query: userMsg?.content || "",
		chosen_response: aiMsg?.content || "",
	};
});

/**
 * SFT预览数据
 */
const sftPreviewData = computed(() => {
	const selectedMessages = getSelectedMessages();
	const userMsg = selectedMessages.find((m) => m.role === "user");
	const aiMsg = selectedMessages.find((m) => m.role === "assistant");

	return {
		instruction: userMsg?.content || "",
		output: aiMsg?.content || "",
	};
});

/**
 * 对话预览数据
 */
const conversationPreviewData = computed(() => {
	const selectedMessages = getSelectedMessages();
	if (selectedMessages.length < 2) return [];

	// 按创建时间排序
	return [...selectedMessages]
		.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
		.map((msg) => ({
			role: msg.role,
			content: msg.content,
		}));
});

// 监听数据集类型变化，适配预览内容
watch(datasetType, (newType) => {
	// 根据类型自动选择第一个匹配的数据集
	const matchingDataset = datasetOptions.value.find((dataset) => dataset.type === newType);
	selectedDataset.value = matchingDataset ? matchingDataset.id : null;
});

onMounted(() => {
	initPage();
});
</script>

<template>
	<div class="chat-detail-container" v-loading="loading">
		<div class="header">
			<div class="header-left">
				<a class="back-button" @click="goBack">
					<el-icon><ArrowLeft /></el-icon>
					返回列表
				</a>
			</div>
			<div class="header-title">
				<el-icon><ChatLineRound /></el-icon>
				<span>聊天记录详情</span>
			</div>
			<div class="header-right">
				<!-- 显示已选择的消息数量 -->
				<span v-if="selectedMessageIds.length > 0" class="selection-count">
					已选择 {{ selectedMessageIds.length }} 条消息
				</span>

				<!-- 添加到数据集按钮 -->
				<el-button type="primary" size="small" :disabled="selectedMessageIds.length === 0" @click="openDatasetDialog">
					<el-icon><Plus /></el-icon>
					添加到数据集
				</el-button>

				<!-- 清除选择按钮 -->
				<el-button type="info" size="small" :disabled="selectedMessageIds.length === 0" @click="clearAllSelections">
					<el-icon><Select /></el-icon>
					清除选择
				</el-button>
			</div>
		</div>

		<div class="chat-container" v-loading="messagesLoading">
			<div class="chat-main">
				<!-- 聊天内容 -->
				<div class="chat-messages">
					<el-empty v-if="chatMessages.length === 0" description="暂无聊天消息" />

					<template v-else>
						<div v-for="(group, groupIndex) in chatDays" :key="groupIndex" class="message-group">
							<div class="date-divider">
								<span class="date-text">{{ group.formattedDay }}</span>
							</div>

							<div
								v-for="message in group.messages"
								:key="message.message_id"
								:class="[
									'message-wrapper',
									message.role,
									{ 'message-selected': isMessageSelected(message.message_id) },
								]"
								@click="toggleMessageSelection(message.message_id)"
							>
								<div class="selection-indicator" v-if="isMessageSelected(message.message_id)">
									<el-icon><Select /></el-icon>
								</div>

								<div class="message-avatar">
									<el-avatar v-if="message.role === 'user'" :icon="UserFilled" />
									<el-avatar v-else :icon="ChatLineRound" />
								</div>

								<div class="message-content-wrapper">
									<div class="message-header">
										<span class="sender-name">{{ message.role === "user" ? "我" : "AI助手" }}</span>
										<span class="message-time">{{ formatDate(message.created_at, "HH:mm:ss") }}</span>
									</div>

									<div class="message-bubble">
										<div class="message-text">{{ message.content }}</div>
									</div>
								</div>
							</div>
						</div>
					</template>
				</div>
			</div>

			<div class="chat-sidebar">
				<div class="sidebar-card">
					<div class="card-header">
						<el-icon><InfoFilled /></el-icon>
						<span>会话信息</span>
					</div>

					<div class="card-content">
						<div class="info-item">
							<span class="info-label">会话ID</span>
							<el-tooltip :content="sessionInfo?.session_id" placement="top" :disabled="!sessionInfo?.session_id">
								<span class="info-value ellipsis">{{ sessionInfo?.session_id || sessionId }}</span>
							</el-tooltip>
						</div>

						<div class="info-item">
							<span class="info-label">角色ID</span>
							<el-tooltip :content="sessionInfo?.chat_role_id" placement="top" :disabled="!sessionInfo?.chat_role_id">
								<span class="info-value ellipsis">{{ sessionInfo?.chat_role_id || "-" }}</span>
							</el-tooltip>
						</div>

						<div class="info-item">
							<span class="info-label">模型</span>
							<el-tooltip :content="sessionInfo?.model_name" placement="top" :disabled="!sessionInfo?.model_name">
								<span class="info-value ellipsis">{{ sessionInfo?.model_name || "-" }}</span>
							</el-tooltip>
						</div>

						<div class="info-item">
							<span class="info-label">创建时间</span>
							<span class="info-value">{{ sessionInfo?.created_at ? formatDate(sessionInfo.created_at) : "-" }}</span>
						</div>

						<el-divider />

						<div class="info-item">
							<span class="info-label">总消息数</span>
							<span class="info-value highlight">{{ statistics.total }}</span>
						</div>

						<div class="info-item">
							<span class="info-label">用户消息</span>
							<span class="info-value">{{ statistics.user }}</span>
						</div>

						<div class="info-item">
							<span class="info-label">AI回复</span>
							<span class="info-value">{{ statistics.assistant }}</span>
						</div>

						<div class="info-item">
							<span class="info-label">总Token</span>
							<span class="info-value">{{ statistics.totalTokens }}</span>
						</div>

						<el-divider />

						<div class="dataset-help">
							<h4>
								<el-icon><DataAnalysis /></el-icon> 数据集构建帮助
							</h4>
							<div class="dataset-type">
								<div class="type-title">
									<el-icon><DocumentAdd /></el-icon> DPO偏好训练
								</div>
								<div class="type-desc">选择一个用户问题和一个AI回答</div>
							</div>
							<div class="dataset-type">
								<div class="type-title">
									<el-icon><DocumentAdd /></el-icon> SFT微调
								</div>
								<div class="type-desc">选择一个用户指令和一个AI回复</div>
							</div>
							<div class="dataset-type">
								<div class="type-title">
									<el-icon><Connection /></el-icon> 多轮对话
								</div>
								<div class="type-desc">选择多条按顺序排列的消息</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- 添加到数据集的对话框 -->
		<el-dialog
			v-model="showDatasetDialog"
			title="添加到数据集"
			width="560px"
			:close-on-click-modal="false"
			:close-on-press-escape="!processingDataset"
			:show-close="!processingDataset"
		>
			<div class="dataset-dialog-content">
				<el-form label-position="top">
					<el-form-item label="数据集类型">
						<el-radio-group v-model="datasetType">
							<el-radio-button label="conversation">多轮对话</el-radio-button>
							<el-radio-button label="dpo">DPO偏好</el-radio-button>
							<el-radio-button label="sft">SFT微调</el-radio-button>
						</el-radio-group>
					</el-form-item>

					<el-form-item label="选择数据集">
						<el-select v-model="selectedDataset" placeholder="请选择数据集" style="width: 100%">
							<el-option
								v-for="option in filteredDatasetOptions"
								:key="option.id"
								:label="option.name"
								:value="option.id"
							>
								<div class="dataset-option">
									<span>{{ option.name }}</span>
									<span class="dataset-desc">{{ option.description }}</span>
								</div>
							</el-option>
						</el-select>
					</el-form-item>

					<el-form-item>
						<div class="dataset-summary">
							<div class="summary-item">
								<span class="summary-label">已选消息:</span>
								<span class="summary-value">{{ selectedMessageIds.length }}条</span>
							</div>
							<div class="summary-item">
								<span class="summary-label">用户消息:</span>
								<span class="summary-value">{{ getSelectedMessages().filter((m) => m.role === "user").length }}条</span>
							</div>
							<div class="summary-item">
								<span class="summary-label">AI回复:</span>
								<span class="summary-value"
									>{{ getSelectedMessages().filter((m) => m.role === "assistant").length }}条</span
								>
							</div>
						</div>
					</el-form-item>

					<!-- 添加预览区域 -->
					<el-form-item label="数据预览">
						<div class="preview-container">
							<!-- DPO偏好数据预览 -->
							<template v-if="datasetType === 'dpo'">
								<div class="preview-dpo" v-if="dpoPreviewData.query">
									<div class="preview-section">
										<div class="preview-title">问题:</div>
										<div class="preview-content">{{ truncateText(dpoPreviewData.query, 100) }}</div>
									</div>
									<div class="preview-section">
										<div class="preview-title">首选回答:</div>
										<div class="preview-content">{{ truncateText(dpoPreviewData.chosen_response, 100) }}</div>
									</div>
									<div class="preview-section">
										<div class="preview-title">负面回答:</div>
										<div class="preview-content preview-empty">需要添加完成后，去指定页面维护这个负面回答</div>
									</div>
								</div>
								<div class="preview-empty" v-else>无效的DPO数据，请选择一个用户问题和一个AI回答</div>
							</template>

							<!-- SFT微调数据预览 -->
							<template v-if="datasetType === 'sft'">
								<div class="preview-sft" v-if="sftPreviewData.instruction">
									<div class="preview-section">
										<div class="preview-title">指令:</div>
										<div class="preview-content">{{ truncateText(sftPreviewData.instruction, 100) }}</div>
									</div>
									<div class="preview-section" v-if="sftPreviewData.output">
										<div class="preview-title">输出:</div>
										<div class="preview-content">{{ truncateText(sftPreviewData.output, 100) }}</div>
									</div>
								</div>
								<div class="preview-empty" v-else>无效的SFT数据，请至少选择一个用户指令</div>
							</template>

							<!-- 多轮对话数据预览 -->
							<template v-if="datasetType === 'conversation'">
								<div class="preview-conversation" v-if="conversationPreviewData.length > 0">
									<div v-for="(msg, idx) in conversationPreviewData" :key="idx" :class="['preview-message', msg.role]">
										<span class="preview-role">{{ msg.role === "user" ? "用户" : "AI" }}</span>
										<span class="preview-content">{{ truncateText(msg.content, 60) }}</span>
									</div>
								</div>
								<div class="preview-empty" v-else>无效的对话数据，请选择至少两条消息</div>
							</template>
						</div>
					</el-form-item>
				</el-form>
			</div>

			<template #footer>
				<span class="dialog-footer">
					<el-button @click="showDatasetDialog = false" :disabled="processingDataset">取消</el-button>
					<el-button
						type="primary"
						@click="confirmAddToDataset"
						:loading="processingDataset"
						:disabled="!selectedDataset"
					>
						确认添加
					</el-button>
				</span>
			</template>
		</el-dialog>
	</div>
</template>

<style scoped>
.chat-detail-container {
	padding: 16px;
	height: calc(100vh - 60px);
	display: flex;
	flex-direction: column;
	background-color: var(--el-bg-color-page, #f5f7fa);
}

.header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 12px 16px;
	background-color: var(--el-bg-color);
	border-radius: 8px;
	box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
	margin-bottom: 16px;
}

.header-left {
	flex: 1;
}

.header-title {
	flex: 2;
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 8px;
	font-size: 18px;
	font-weight: 600;
	color: var(--el-text-color-primary);
}

.header-right {
	flex: 1;
	display: flex;
	justify-content: flex-end;
	align-items: center;
	gap: 8px;
}

.selection-count {
	font-size: 14px;
	color: var(--el-color-primary);
	font-weight: 500;
}

.back-button {
	display: flex;
	align-items: center;
	gap: 4px;
	color: var(--el-color-primary);
	cursor: pointer;
	font-size: 14px;
}

.chat-container {
	display: flex;
	flex: 1;
	gap: 16px;
	overflow: hidden;
}

.chat-main {
	flex: 1;
	display: flex;
	flex-direction: column;
	background-color: var(--el-bg-color);
	border-radius: 8px;
	box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
	overflow: hidden;
}

.chat-sidebar {
	width: 280px;
}

.sidebar-card {
	background-color: var(--el-bg-color);
	border-radius: 8px;
	box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
	overflow: hidden;
}

.card-header {
	display: flex;
	align-items: center;
	gap: 8px;
	padding: 12px 16px;
	font-size: 16px;
	font-weight: 600;
	color: var(--el-text-color-primary);
	border-bottom: 1px solid var(--el-border-color-light);
}

.card-content {
	padding: 16px;
}

.info-item {
	display: flex;
	justify-content: space-between;
	margin-bottom: 12px;
	font-size: 14px;
}

.info-label {
	color: var(--el-text-color-secondary);
	font-weight: 500;
}

.info-value {
	color: var(--el-text-color-primary);
	max-width: 60%;
}

.info-value.highlight {
	color: var(--el-color-primary);
	font-weight: 600;
}

.ellipsis {
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

.chat-messages {
	flex: 1;
	padding: 16px;
	overflow-y: auto;
}

.date-divider {
	display: flex;
	align-items: center;
	justify-content: center;
	margin: 16px 0;
	position: relative;
}

.date-divider:before,
.date-divider:after {
	content: "";
	flex: 1;
	height: 1px;
	background: var(--el-border-color-light);
	margin: 0 16px;
}

.date-text {
	font-size: 13px;
	color: var(--el-text-color-secondary);
	background-color: var(--el-bg-color);
	padding: 0 10px;
}

.message-wrapper {
	display: flex;
	margin-bottom: 20px;
	position: relative;
	cursor: pointer;
	transition: all 0.2s ease;
	padding: 4px;
	border-radius: 12px;
}

.message-wrapper:hover {
	background-color: var(--el-fill-color-light, #f5f7fa);
}

.message-wrapper.message-selected {
	background-color: var(--el-color-primary-light-9);
	box-shadow: 0 0 0 1px var(--el-color-primary-light-5);
}

.message-wrapper.user {
	flex-direction: row-reverse;
}

.selection-indicator {
	position: absolute;
	top: 8px;
	left: 8px;
	background-color: var(--el-color-primary);
	color: white;
	border-radius: 50%;
	width: 20px;
	height: 20px;
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 2;
}

.message-wrapper.user .selection-indicator {
	left: auto;
	right: 8px;
}

.message-avatar {
	margin: 0 12px;
}

.message-content-wrapper {
	max-width: 70%;
	display: flex;
	flex-direction: column;
}

.user .message-content-wrapper {
	align-items: flex-end;
}

.message-header {
	display: flex;
	align-items: center;
	margin-bottom: 4px;
	gap: 8px;
}

.user .message-header {
	flex-direction: row-reverse;
}

.sender-name {
	font-size: 13px;
	font-weight: 500;
	color: var(--el-text-color-secondary);
}

.message-time {
	font-size: 12px;
	color: var(--el-text-color-secondary);
	opacity: 0.7;
}

.message-bubble {
	padding: 12px 16px;
	border-radius: 12px;
	position: relative;
}

.user .message-bubble {
	background-color: var(--el-color-primary-light-9);
	border-top-right-radius: 2px;
}

.assistant .message-bubble {
	background-color: var(--el-fill-color-light);
	border-top-left-radius: 2px;
}

.message-text {
	font-size: 14px;
	line-height: 1.5;
	color: var(--el-text-color-primary);
	word-break: break-word;
	white-space: pre-wrap;
}

/* 数据集帮助区域样式 */
.dataset-help {
	margin-top: 16px;
}

.dataset-help h4 {
	display: flex;
	align-items: center;
	gap: 4px;
	font-size: 15px;
	margin: 0 0 12px 0;
	color: var(--el-text-color-primary);
}

.dataset-type {
	margin-bottom: 10px;
	padding: 8px;
	border-radius: 6px;
	background-color: var(--el-fill-color-light);
}

.type-title {
	display: flex;
	align-items: center;
	gap: 4px;
	font-size: 14px;
	font-weight: 500;
	color: var(--el-text-color-primary);
	margin-bottom: 4px;
}

.type-desc {
	font-size: 12px;
	color: var(--el-text-color-secondary);
}

/* 数据集对话框样式 */
.dataset-dialog-content {
	padding: 0 20px;
}

.dataset-option {
	display: flex;
	flex-direction: column;
}

.dataset-desc {
	font-size: 12px;
	color: var(--el-text-color-secondary);
}

.dataset-summary {
	background-color: var(--el-fill-color-light);
	border-radius: 6px;
	padding: 12px;
	margin-top: 12px;
}

.summary-item {
	display: flex;
	justify-content: space-between;
	margin-bottom: 8px;
}

.summary-label {
	color: var(--el-text-color-secondary);
}

.summary-value {
	font-weight: 500;
	color: var(--el-text-color-primary);
}

/* 数据预览区域样式 */
.preview-container {
	background-color: var(--el-fill-color-light);
	border-radius: 6px;
	padding: 12px;
	max-height: 200px;
	overflow-y: auto;
}

.preview-empty {
	text-align: center;
	color: var(--el-text-color-secondary);
	padding: 12px 0;
	font-size: 13px;
	font-style: italic;
}

.preview-section {
	margin-bottom: 10px;
}

.preview-title {
	font-size: 13px;
	font-weight: 500;
	color: var(--el-text-color-secondary);
	margin-bottom: 4px;
}

.preview-content {
	font-size: 13px;
	color: var(--el-text-color-primary);
	background-color: var(--el-bg-color);
	padding: 8px;
	border-radius: 4px;
	border-left: 3px solid var(--el-color-primary-light-5);
	word-break: break-word;
}

.preview-message {
	display: flex;
	margin-bottom: 8px;
	padding: 6px;
	border-radius: 4px;
	background-color: var(--el-bg-color);
}

.preview-message.user {
	background-color: var(--el-color-primary-light-9);
}

.preview-message.assistant {
	background-color: var(--el-fill-color);
}

.preview-role {
	font-size: 12px;
	font-weight: 500;
	color: var(--el-text-color-primary);
	margin-right: 8px;
	min-width: 32px;
}
</style>
