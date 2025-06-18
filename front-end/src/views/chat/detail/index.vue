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

// Actual API returned chat message interface
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

// Dataset types
type DatasetType = "dpo" | "sft" | "conversation";

// Dataset options
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
const sessionInfo = ref<any>(null); // Session information
const selectedMessageIds = ref<string[]>([]); // Selected message IDs

// Dataset related state
const showDatasetDialog = ref(false);
const datasetType = ref<DatasetType>("conversation");
const datasetOptions = ref<DatasetOption[]>([
	{ id: 1, name: "Conversation Dataset Example", type: "conversation", description: "Dataset for conversation training" },
	{ id: 2, name: "DPO Preference Dataset Example", type: "dpo", description: "Dataset for DPO preference training" },
	{ id: 3, name: "SFT Fine-tuning Dataset Example", type: "sft", description: "Dataset for SFT fine-tuning" },
]);
const selectedDataset = ref<number | null>(null);
const processingDataset = ref(false);

// Initialize page
const initPage = async () => {
	const id = route.params.id as string;
	sessionId.value = id;
	await Promise.all([fetchSessionDetail(id), fetchMessages(id)]);
};

// Get session details
const fetchSessionDetail = async (id: string) => {
	loading.value = true;
	try {
		// extractResponseData in request.ts has processed the response, returning the data object directly instead of AxiosResponse
		const response: any = await getChatSessionById(id);

		if (response) {
			chatSession.value = response;
			selectedMemoryType.value = response.memory_type;
		} else {
			// Use mock data
			// const mockSession: any = mockChatSessions.find((s: any) => s.id === id);
			// if (mockSession) {
			// 	chatSession.value = mockSession;
			// 	selectedMemoryType.value = mockSession.memory_type;
			// } else {
			// 	ElMessage.error("Session does not exist");
			// 	router.push("/chat/list");
			// }
		}
	} catch (error) {
		console.error("Failed to get chat session details", error);
		ElMessage.error("Failed to get chat session details");

		// Use mock data
		// const mockSession: any = mockChatSessions.find((s: any) => s.id === id);
		// if (mockSession) {
		// 	chatSession.value = mockSession;
		// 	selectedMemoryType.value = mockSession.memory_type;
		// }
	} finally {
		loading.value = false;
	}
};

// Get session messages
const fetchMessages = async (id: string) => {
	messagesLoading.value = true;
	try {
		// extractResponseData in request.ts has processed the response, returning the data array directly instead of AxiosResponse
		const response: any = await getChatMessages(id);

		if (response && Array.isArray(response)) {
			chatMessages.value = response as ChatMessageRaw[];
		} else {
			// Use mock data
			// chatMessages.value = mockChatMessages.filter((m) => m.session_id === id) as ChatMessageRaw[];
		}

		// Extract session basic information
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
		console.error("Failed to get chat messages", error);
		ElMessage.error("Failed to get chat messages");
	} finally {
		messagesLoading.value = false;
	}
};

// Back to list page
const goBack = () => {
	router.push("/chat/list");
};

// Calculate statistics
const statistics = computed(() => {
	if (!chatMessages.value.length) return { total: 0, user: 0, assistant: 0, totalTokens: 0 };

	const total = chatMessages.value.length;
	const user = chatMessages.value.filter((msg) => msg.role === "user").length;
	const assistant = chatMessages.value.filter((msg) => msg.role === "assistant").length;
	const totalTokens = chatMessages.value.reduce((sum, msg) => sum + (msg.total_tokens || 0), 0);

	return { total, user, assistant, totalTokens };
});

// Get chat date groups
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

// Format chat date display
const formatChatDay = (dateStr: string) => {
	const date = new Date(dateStr);
	const today = new Date();
	const yesterday = new Date(today);
	yesterday.setDate(yesterday.getDate() - 1);

	if (dateStr === formatDate(today, "YYYY-MM-DD")) {
		return "Today";
	} else if (dateStr === formatDate(yesterday, "YYYY-MM-DD")) {
		return "Yesterday";
	} else {
		return formatDate(date, "YYYY/MM/DD");
	}
};

// Toggle message selection status
const toggleMessageSelection = (messageId: string) => {
	const index = selectedMessageIds.value.indexOf(messageId);
	if (index !== -1) {
		selectedMessageIds.value.splice(index, 1);
	} else {
		selectedMessageIds.value.push(messageId);
	}
};

// Check if message is selected
const isMessageSelected = (messageId: string) => {
	return selectedMessageIds.value.includes(messageId);
};

// Get selected message objects
const getSelectedMessages = () => {
	return chatMessages.value.filter((msg) => selectedMessageIds.value.includes(msg.message_id));
};

// Clear all selections
const clearAllSelections = () => {
	selectedMessageIds.value = [];
};

// Open add to dataset dialog
const openDatasetDialog = () => {
	if (selectedMessageIds.value.length === 0) {
		ElMessage.warning("Please select at least one message");
		return;
	}

	// Automatically select appropriate dataset type based on selected message count
	const selectedMessages = getSelectedMessages();
	const hasUserMessage = selectedMessages.some((msg) => msg.role === "user");
	const hasAiMessage = selectedMessages.some((msg) => msg.role === "assistant");

	if (selectedMessages.length === 1) {
		if (hasUserMessage) {
			datasetType.value = "sft";
		} else {
			ElMessage.warning("Selecting only AI messages cannot be added to dataset, please select user messages or conversation pairs");
			return;
		}
	} else if (selectedMessages.length === 2 && hasUserMessage && hasAiMessage) {
		datasetType.value = "dpo";
	} else {
		datasetType.value = "conversation";
	}

	// Automatically select first matching dataset
	const matchingDataset = datasetOptions.value.find((dataset) => dataset.type === datasetType.value);
	selectedDataset.value = matchingDataset ? matchingDataset.id : null;

	showDatasetDialog.value = true;
};

// Confirm add to dataset
const confirmAddToDataset = async () => {
	if (!selectedDataset.value) {
		ElMessage.warning("Please select a dataset");
		return;
	}

	processingDataset.value = true;

	try {
		const selectedMessages = getSelectedMessages();
		const selectedDatasetInfo = datasetOptions.value.find((d) => d.id === selectedDataset.value);

		if (!selectedDatasetInfo) {
			throw new Error("Selected dataset not found");
		}

		// Process data based on different dataset types
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
				throw new Error("Unsupported dataset type");
		}
		console.log(result);
		ElNotification({
			title: "Success",
			message: `Successfully added to "${selectedDatasetInfo.name}" dataset`,
			type: "success",
		});

		// Close dialog and clear selections
		showDatasetDialog.value = false;
		clearAllSelections();
	} catch (error) {
		console.error("Failed to add to dataset", error);
		ElMessage.error("Failed to add to dataset: " + (error as Error).message);
	} finally {
		processingDataset.value = false;
	}
};

// DPO preference dataset processing
const processDpoDataset = async (messages: ChatMessageRaw[], dataset: DatasetOption) => {
	// Validate if data meets DPO format requirements (question + 2 answers)
	const userMsg = messages.find((m) => m.role === "user");
	const aiMsgs = messages.filter((m) => m.role === "assistant");

	if (!userMsg || aiMsgs.length !== 1) {
		throw new Error("DPO dataset requires 1 user question and 1 AI response");
	}

	// Build DPO data
	const dpoData = {
		dataset_id: dataset.id,
		query: userMsg.content,
		chosen_response: aiMsgs[0].content,
		rejected_response: "", // In actual application, may need user specification or from other sources
		raw_data: JSON.stringify(messages),
	};

	// Call API to add data to DPO dataset
	console.log("Add to DPO dataset:", dpoData);

	// Reserved for API call
	// return await addToDpoDataset(dpoData);
	return true;
};

// SFT fine-tuning dataset processing
const processSftDataset = async (messages: ChatMessageRaw[], dataset: DatasetOption) => {
	// Validate if data meets SFT format requirements (typically instruction + output)
	if (messages.length < 1) {
		throw new Error("SFT dataset requires at least 1 message");
	}

	// Find user message as instruction
	const userMsg = messages.find((m) => m.role === "user");
	if (!userMsg) {
		throw new Error("SFT dataset requires at least one user message as instruction");
	}

	// Find AI reply as output
	const aiMsg = messages.find((m) => m.role === "assistant");

	// Build SFT data
	const sftData = {
		dataset_id: dataset.id,
		instruction: userMsg.content,
		input: "", // Optional input, may be needed in some scenarios
		output: aiMsg ? aiMsg.content : "",
		raw_data: JSON.stringify(messages),
	};

	// Call API to add data to SFT dataset
	console.log("Add to SFT dataset:", sftData);

	// Reserved for API call
	// return await addToSftDataset(sftData);
	return true;
};

// Multi-turn conversation dataset processing
const processConversationDataset = async (messages: ChatMessageRaw[], dataset: DatasetOption) => {
	// Validate if there are enough messages
	if (messages.length < 2) {
		throw new Error("Conversation dataset requires at least 2 messages");
	}

	// Sort messages by creation time
	const sortedMessages = [...messages].sort(
		(a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
	);

	// Build conversation format data
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

	// Call API to add data to conversation dataset
	console.log("Add to conversation dataset:", conversationEntries);

	// Reserved for API call
	// return await addToConversationDataset(conversationEntries);
	return true;
};

// Get filtered dataset options for current dataset type
const filteredDatasetOptions = computed(() => {
	return datasetOptions.value.filter((d) => d.type === datasetType.value);
});

/**
 * Truncate text, adding ellipsis when exceeding maximum length
 */
const truncateText = (text: string, maxLength: number): string => {
	if (!text) return "";
	return text.length > maxLength ? text.substring(0, maxLength) + "..." : text;
};

/**
 * DPO preview data
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
 * SFT preview data
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
 * Conversation preview data
 */
const conversationPreviewData = computed(() => {
	const selectedMessages = getSelectedMessages();
	if (selectedMessages.length < 2) return [];

	// Sort by creation time
	return [...selectedMessages]
		.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
		.map((msg) => ({
			role: msg.role,
			content: msg.content,
		}));
});

// Watch dataset type changes, adapt preview content
watch(datasetType, (newType) => {
	// Automatically select first matching dataset
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
					Back to List
				</a>
			</div>
			<div class="header-title">
				<el-icon><ChatLineRound /></el-icon>
				<span>Chat History Details</span>
			</div>
			<div class="header-right">
				<!-- Show number of selected messages -->
				<span v-if="selectedMessageIds.length > 0" class="selection-count">
					{{ selectedMessageIds.length }} messages selected
				</span>

				<!-- Add to dataset button -->
				<el-button type="primary" size="small" :disabled="selectedMessageIds.length === 0" @click="openDatasetDialog">
					<el-icon><Plus /></el-icon>
					Add to Dataset
				</el-button>

				<!-- Clear selection button -->
				<el-button type="info" size="small" :disabled="selectedMessageIds.length === 0" @click="clearAllSelections">
					<el-icon><Select /></el-icon>
					Clear Selection
				</el-button>
			</div>
		</div>

		<div class="chat-container" v-loading="messagesLoading">
			<div class="chat-main">
				<!-- Chat content -->
				<div class="chat-messages">
					<el-empty v-if="chatMessages.length === 0" description="No chat messages" />

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
										<span class="sender-name">{{ message.role === "user" ? "Me" : "AI Assistant" }}</span>
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
						<span>Session Information</span>
					</div>

					<div class="card-content">
						<div class="info-item">
							<span class="info-label">Session ID</span>
							<el-tooltip :content="sessionInfo?.session_id" placement="top" :disabled="!sessionInfo?.session_id">
								<span class="info-value ellipsis">{{ sessionInfo?.session_id || sessionId }}</span>
							</el-tooltip>
						</div>

						<div class="info-item">
							<span class="info-label">Role ID</span>
							<el-tooltip :content="sessionInfo?.chat_role_id" placement="top" :disabled="!sessionInfo?.chat_role_id">
								<span class="info-value ellipsis">{{ sessionInfo?.chat_role_id || "-" }}</span>
							</el-tooltip>
						</div>

						<div class="info-item">
							<span class="info-label">Model</span>
							<el-tooltip :content="sessionInfo?.model_name" placement="top" :disabled="!sessionInfo?.model_name">
								<span class="info-value ellipsis">{{ sessionInfo?.model_name || "-" }}</span>
							</el-tooltip>
						</div>

						<div class="info-item">
							<span class="info-label">Created At</span>
							<span class="info-value">{{ sessionInfo?.created_at ? formatDate(sessionInfo.created_at) : "-" }}</span>
						</div>

						<el-divider />

						<div class="info-item">
							<span class="info-label">Total Messages</span>
							<span class="info-value highlight">{{ statistics.total }}</span>
						</div>

						<div class="info-item">
							<span class="info-label">User Messages</span>
							<span class="info-value">{{ statistics.user }}</span>
						</div>

						<div class="info-item">
							<span class="info-label">AI Replies</span>
							<span class="info-value">{{ statistics.assistant }}</span>
						</div>

						<div class="info-item">
							<span class="info-label">Total Tokens</span>
							<span class="info-value">{{ statistics.totalTokens }}</span>
						</div>

						<el-divider />

						<div class="dataset-help">
							<h4>
								<el-icon><DataAnalysis /></el-icon> Dataset Building Help
							</h4>
							<div class="dataset-type">
								<div class="type-title">
									<el-icon><DocumentAdd /></el-icon> DPO Preference Training
								</div>
								<div class="type-desc">Select one user question and one AI reply</div>
							</div>
							<div class="dataset-type">
								<div class="type-title">
									<el-icon><DocumentAdd /></el-icon> SFT Fine-tuning
								</div>
								<div class="type-desc">Select one user instruction and one AI reply</div>
							</div>
							<div class="dataset-type">
								<div class="type-title">
									<el-icon><Connection /></el-icon> Multi-turn Conversation
								</div>
								<div class="type-desc">Select multiple messages ordered sequentially</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- Add to dataset dialog -->
		<el-dialog
			v-model="showDatasetDialog"
			title="Add to Dataset"
			width="560px"
			:close-on-click-modal="false"
			:close-on-press-escape="!processingDataset"
			:show-close="!processingDataset"
		>
			<div class="dataset-dialog-content">
				<el-form label-position="top">
					<el-form-item label="Dataset Type">
						<el-radio-group v-model="datasetType">
							<el-radio-button label="conversation">Multi-turn Conversation</el-radio-button>
							<el-radio-button label="dpo">DPO Preference</el-radio-button>
							<el-radio-button label="sft">SFT Fine-tuning</el-radio-button>
						</el-radio-group>
					</el-form-item>

					<el-form-item label="Select Dataset">
						<el-select v-model="selectedDataset" placeholder="Please select a dataset" style="width: 100%">
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
								<span class="summary-label">Selected Messages:</span>
								<span class="summary-value">{{ selectedMessageIds.length }} items</span>
							</div>
							<div class="summary-item">
								<span class="summary-label">User Messages:</span>
								<span class="summary-value">{{ getSelectedMessages().filter((m) => m.role === "user").length }} items</span>
							</div>
							<div class="summary-item">
								<span class="summary-label">AI Replies:</span>
								<span class="summary-value"
									>{{ getSelectedMessages().filter((m) => m.role === "assistant").length }} items</span
								>
							</div>
						</div>
					</el-form-item>

					<!-- Preview area -->
					<el-form-item label="Data Preview">
						<div class="preview-container">
							<!-- DPO preference data preview -->
							<template v-if="datasetType === 'dpo'">
								<div class="preview-dpo" v-if="dpoPreviewData.query">
									<div class="preview-section">
										<div class="preview-title">Question:</div>
										<div class="preview-content">{{ truncateText(dpoPreviewData.query, 100) }}</div>
									</div>
									<div class="preview-section">
										<div class="preview-title">Chosen Response:</div>
										<div class="preview-content">{{ truncateText(dpoPreviewData.chosen_response, 100) }}</div>
									</div>
									<div class="preview-section">
										<div class="preview-title">Rejected Response:</div>
										<div class="preview-content preview-empty">Need to add and maintain this rejected response on the specified page after completion</div>
									</div>
								</div>
								<div class="preview-empty" v-else>Invalid DPO data, please select one user question and one AI reply</div>
							</template>

							<!-- SFT fine-tuning data preview -->
							<template v-if="datasetType === 'sft'">
								<div class="preview-sft" v-if="sftPreviewData.instruction">
									<div class="preview-section">
										<div class="preview-title">Instruction:</div>
										<div class="preview-content">{{ truncateText(sftPreviewData.instruction, 100) }}</div>
									</div>
									<div class="preview-section" v-if="sftPreviewData.output">
										<div class="preview-title">Output:</div>
										<div class="preview-content">{{ truncateText(sftPreviewData.output, 100) }}</div>
									</div>
								</div>
								<div class="preview-empty" v-else>Invalid SFT data, please select at least one user instruction</div>
							</template>

							<!-- Multi-turn conversation data preview -->
							<template v-if="datasetType === 'conversation'">
								<div class="preview-conversation" v-if="conversationPreviewData.length > 0">
									<div v-for="(msg, idx) in conversationPreviewData" :key="idx" :class="['preview-message', msg.role]">
										<span class="preview-role">{{ msg.role === "user" ? "User" : "AI" }}</span>
										<span class="preview-content">{{ truncateText(msg.content, 60) }}</span>
									</div>
								</div>
								<div class="preview-empty" v-else>Invalid conversation data, please select at least two messages</div>
							</template>
						</div>
					</el-form-item>
				</el-form>
			</div>

			<template #footer>
				<span class="dialog-footer">
					<el-button @click="showDatasetDialog = false" :disabled="processingDataset">Cancel</el-button>
					<el-button
						type="primary"
						@click="confirmAddToDataset"
						:loading="processingDataset"
						:disabled="!selectedDataset"
					>
						Confirm Add
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

/* Dataset help area styles */
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

/* Dataset dialog styles */
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

/* Preview area styles */
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
