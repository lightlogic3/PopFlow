<template>
	<div class="app-container">
		<div class="filter-container">
			<el-card class="box-card">
				<template #header>
					<div class="clearfix">
						<span>Memory System Plugin Selection</span>
					</div>
				</template>

				<el-form :inline="true" :model="pluginForm" label-width="120px">
					<el-form-item label="Plugin Selection Mode">
						<el-radio-group v-model="pluginSelectMode">
							<el-radio :label="'predefined'">Preset Plugins</el-radio>
							<el-radio :label="'custom'">Custom Plugins</el-radio>
						</el-radio-group>
					</el-form-item>

					<!-- Preset Plugin Selection -->
					<div v-if="pluginSelectMode === 'predefined'">
						<el-form-item label="Select Plugin">
							<el-select
								v-model="pluginForm.selectedPlugin"
								placeholder="Please select memory system plugin"
								style="width: 350px"
								value-key="level"
								@change="handlePluginChange"
							>
								<el-option
									v-for="item in plugins"
									:key="item.level"
									:label="`${item.name} (${item.level_name})`"
									:value="item"
								>
									<div style="display: flex; justify-content: space-between">
										<span>{{ item.name }}</span>
										<span style="color: #8492a6; font-size: 13px">{{ item.level_name }}</span>
									</div>
								</el-option>
							</el-select>
							<el-button type="primary" @click="getPlugins" icon="el-icon-refresh">Refresh</el-button>
						</el-form-item>
						<el-form-item label="Plugin Description" v-if="pluginForm.selectedPlugin">
							<el-tag type="info">{{ pluginForm.selectedPlugin.description }}</el-tag>
						</el-form-item>
					</div>

					<!-- Custom Plugin -->
					<div v-else>
						<el-form-item label="Plugin Level">
							<el-input
								v-model="pluginForm.customPluginLevel"
								placeholder="Enter plugin level number or enum name"
								style="width: 350px"
							/>
						</el-form-item>
						<el-form-item label="Plugin Name">
							<el-input v-model="pluginForm.customPluginName" placeholder="Enter plugin name" style="width: 350px" />
						</el-form-item>
						<el-form-item label="Plugin Path">
							<el-input
								v-model="pluginForm.customPluginPath"
								placeholder="Enter plugin module path, e.g.: plugIns.memory_system.custom_memory.CustomMemory"
								style="width: 350px"
							/>
						</el-form-item>
					</div>
				</el-form>
			</el-card>

			<el-card class="box-card" style="margin-top: 20px">
				<template #header>
					<div class="clearfix">
						<span>User Information</span>
					</div>
				</template>
				<el-form :inline="true" :model="userForm" label-width="120px">
					<el-form-item label="User ID" required>
						<el-input v-model="userForm.userId" placeholder="Please enter user ID" style="width: 350px" />
					</el-form-item>
					<el-form-item label="Role ID" required>
						<el-input v-model="userForm.roleId" placeholder="Please enter role ID" style="width: 350px" />
					</el-form-item>
					<el-form-item label="Session ID">
						<el-input v-model="userForm.sessionId" placeholder="Please enter session ID" style="width: 350px" />
					</el-form-item>
					<el-form-item label="Include History">
						<el-switch v-model="userForm.includeHistory" />
					</el-form-item>
				</el-form>
			</el-card>
		</div>

		<el-tabs v-model="activeTab" type="border-card" style="margin-top: 20px">
			<el-tab-pane label="Store Conversation" name="store">
				<el-form :model="storeForm" label-width="120px">
					<el-form-item label="Content" required>
						<el-input
							v-model="storeForm.content"
							type="textarea"
							:rows="3"
							placeholder="Please enter conversation content"
							style="width: 100%"
						/>
					</el-form-item>
					<el-form-item label="Role">
						<el-radio-group v-model="storeForm.role">
							<el-radio label="user">User</el-radio>
							<el-radio label="assistant">AI Assistant</el-radio>
						</el-radio-group>
					</el-form-item>
					<el-form-item label="Conversation ID">
						<el-input v-model="storeForm.conversation_id" placeholder="(Optional) Please enter conversation ID" style="width: 350px" />
					</el-form-item>
					<el-form-item label="Message ID">
						<el-input v-model="storeForm.message_id" placeholder="(Optional) Please enter message ID" style="width: 350px" />
					</el-form-item>
					<el-form-item label="Parent Message ID">
						<el-input v-model="storeForm.parent_message_id" placeholder="(Optional) Please enter parent message ID" style="width: 350px" />
					</el-form-item>
					<el-form-item>
						<el-button
							type="primary"
							@click="handleStoreConversation"
							:loading="storeLoading"
							:disabled="!userForm.userId || !userForm.roleId || !storeForm.content"
						>
							Store Conversation
						</el-button>
					</el-form-item>
				</el-form>

				<el-alert
					v-if="storeResult"
					:title="storeResult.message"
					:type="storeResult.success ? 'success' : 'error'"
					show-icon
				/>
			</el-tab-pane>

			<el-tab-pane label="Retrieve Conversation" name="retrieve">
				<el-form :model="retrieveForm" label-width="120px">
					<el-form-item label="Query Content" required>
						<el-input
							v-model="retrieveForm.query"
							type="textarea"
							:rows="3"
							placeholder="Please enter query content"
							style="width: 100%"
						/>
					</el-form-item>
					<el-form-item label="Return Count">
						<el-input-number v-model="retrieveForm.top_k" :min="1" :max="50" />
					</el-form-item>
					<el-form-item>
						<el-button
							type="primary"
							@click="handleRetrieveConversations"
							:loading="retrieveLoading"
							:disabled="!userForm.userId || !userForm.roleId || !retrieveForm.query"
						>
							Retrieve Conversations
						</el-button>
					</el-form-item>
				</el-form>

				<div v-if="retrieveResults.length > 0" style="margin-top: 20px">
					<h3>Retrieve Results</h3>
					<el-table :data="retrieveResults" border style="width: 100%">
						<el-table-column prop="content" label="Content" min-width="350" show-overflow-tooltip />
						<el-table-column prop="role" label="Role" width="100" />
						<el-table-column prop="score" label="Relevance" width="100">
							<template #default="scope"> {{ (scope.row.score * 100).toFixed(2) }}% </template>
						</el-table-column>
						<el-table-column prop="timestamp" label="Time" width="180" />
						<el-table-column label="Actions" width="120">
							<template #default="scope">
								<el-button type="text" @click="showDetails(scope.row)">View Details</el-button>
							</template>
						</el-table-column>
					</el-table>
				</div>
			</el-tab-pane>

			<el-tab-pane label="Chat Test" name="chat">
				<el-card>
					<template #header>
						<div class="clearfix">
							<span>Model Selection</span>
						</div>
					</template>

					<el-form :model="chatForm" label-width="120px">
						<el-form-item label="Select Model">
							<model-cascader v-model="chatForm.model_id" :placeholder="'Please select LLM model'" @change="handleModelChange" />
						</el-form-item>

						<el-form-item label="Temperature">
							<el-slider
								v-model="chatForm.temperature"
								:min="0"
								:max="1"
								:step="0.01"
								show-input
								style="width: 350px"
							/>
						</el-form-item>

						<el-form-item label="Max Tokens">
							<el-input-number v-model="chatForm.max_tokens" :min="100" :max="4000" :step="100" />
						</el-form-item>

						<el-form-item>
							<el-checkbox v-model="chatForm.saveToMemory">Save to Memory System</el-checkbox>
						</el-form-item>
					</el-form>
				</el-card>

				<el-card style="margin-top: 20px">
					<template #header>
						<div class="clearfix">
							<span>Chat Test</span>
						</div>
					</template>

					<!-- Chat History -->
					<div class="chat-messages">
						<div v-for="(msg, index) in chatMessages" :key="index" class="message" :class="msg.role">
							<div class="message-content">
								<div class="message-role">{{ msg.role === "user" ? "User" : "AI" }}</div>
								<div class="message-text">{{ msg.content }}</div>
							</div>
						</div>
					</div>

					<!-- Chat Input -->
					<div class="chat-input">
						<el-input
							v-model="chatForm.query"
							type="textarea"
							:rows="3"
							placeholder="Please enter your question"
							style="width: 100%"
							@keyup.enter.ctrl="handleSendMessage"
						/>
						<div class="chat-actions" style="margin-top: 10px">
							<el-button
								type="primary"
								@click="handleSendMessage"
								:loading="chatLoading"
								:disabled="
									!chatForm.model_id ||
									!chatForm.query ||
									(chatForm.saveToMemory && (!userForm.userId || !userForm.roleId))
								"
							>
								Send Message
							</el-button>

							<el-button @click="clearChatMessages"> Clear Chat </el-button>
						</div>

						<!-- Model Response Info -->
						<div v-if="chatResponse" class="response-info" style="margin-top: 10px; font-size: 12px; color: #909399">
							<p>Model: {{ chatResponse.model }}</p>
							<p>
								Tokens: Input {{ chatResponse.tokens?.input || 0 }} / Output {{ chatResponse.tokens?.output || 0 }} / Total
								{{ chatResponse.tokens?.total || 0 }}
							</p>
							<p>Response Time: {{ (chatResponse.elapsed_time * 1000).toFixed(0) }}ms</p>
						</div>
					</div>
				</el-card>
			</el-tab-pane>

			<el-tab-pane label="Sync Management" name="sync">
				<el-form label-width="120px">
					<el-form-item label="Run in Background">
						<el-switch v-model="syncForm.runInBackground" />
					</el-form-item>
					<el-form-item>
						<el-button
							type="primary"
							@click="handleSyncConversations"
							:loading="syncLoading"
							:disabled="!userForm.userId || !userForm.roleId"
						>
							Sync Conversations
						</el-button>
						<el-button
							type="info"
							@click="handleGetSyncStatus"
							:loading="statusLoading"
							:disabled="!userForm.userId || !userForm.roleId"
						>
							Check Status
						</el-button>
					</el-form-item>
				</el-form>

				<el-alert
					v-if="syncResult"
					:title="syncResult.message"
					:type="syncResult.success ? 'success' : 'error'"
					show-icon
				/>

				<div v-if="syncStatus" style="margin-top: 20px">
					<h3>Sync Status</h3>
					<el-card>
						<el-progress
							:percentage="syncStatus.progress"
							:status="syncStatus.is_syncing ? 'warning' : syncStatus.progress >= 100 ? 'success' : 'exception'"
						/>
						<p><strong>Sync Status:</strong> {{ syncStatus.is_syncing ? "Syncing..." : "Not Syncing" }}</p>
						<p><strong>Last Sync Time:</strong> {{ syncStatus.last_sync_time || "None" }}</p>
						<p v-if="syncStatus.error"><strong>Error Message:</strong> {{ syncStatus.error }}</p>
					</el-card>
				</div>
			</el-tab-pane>
		</el-tabs>

		<!-- Result Details Dialog -->
		<el-dialog title="Conversation Details" v-model="detailsVisible" width="50%">
			<div v-if="selectedItem">
				<el-descriptions border :column="1">
					<el-descriptions-item label="Content">{{ selectedItem.content }}</el-descriptions-item>
					<el-descriptions-item label="Role">{{ selectedItem.role }}</el-descriptions-item>
					<el-descriptions-item label="User ID">{{ selectedItem.user_id }}</el-descriptions-item>
					<el-descriptions-item label="Role ID">{{ selectedItem.role_id || "None" }}</el-descriptions-item>
					<el-descriptions-item label="Session ID">{{ selectedItem.session_id || "None" }}</el-descriptions-item>
					<el-descriptions-item label="Conversation ID">{{ selectedItem.conversation_id || "None" }}</el-descriptions-item>
					<el-descriptions-item label="Message ID">{{ selectedItem.message_id || "None" }}</el-descriptions-item>
					<el-descriptions-item label="Parent Message ID">{{ selectedItem.parent_message_id || "None" }}</el-descriptions-item>
					<el-descriptions-item label="Time">{{ selectedItem.timestamp }}</el-descriptions-item>
					<el-descriptions-item label="Relevance">{{ (selectedItem.score * 100).toFixed(2) }}%</el-descriptions-item>
					<el-descriptions-item label="Metadata">{{ JSON.stringify(selectedItem.metadata || {}) }}</el-descriptions-item>
				</el-descriptions>
			</div>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount } from "vue";
import { ElMessage } from "element-plus";
import {
	getMemoryPlugins,
	storeConversation,
	retrieveConversations,
	syncConversations,
	getSyncStatus,
	testChat,
	PluginRequest,
	ConversationRequest,
	ChatTestRequest,
} from "@/api/memory";
import ModelCascader from "@/components/ModelCascader.vue";

// 类型定义
interface Plugin {
	level: number;
	level_name: string;
	name: string;
	description: string;
}

interface ChatMessage {
	role: string;
	content: string;
}

interface ResultItem {
	content: string;
	role: string;
	user_id: string;
	role_id?: string;
	session_id?: string;
	conversation_id?: string;
	message_id?: string;
	parent_message_id?: string;
	timestamp: string;
	score: number;
	metadata?: Record<string, any>;
}

interface ChatResponse {
	response: string;
	model: string;
	tokens: {
		input: number;
		output: number;
		total: number;
	};
	elapsed_time: number;
}

interface SyncStatus {
	is_syncing: any;
	progress: number;
	last_sync_time: string | null;
	error: string | null;
}

interface ResponseResult {
	success: boolean;
	message: string;
	data: any;
}

// 响应式状态
const pluginSelectMode = ref<string>("predefined");
const plugins = ref<Plugin[]>([]);
const activeTab = ref<string>("store");
const statusTimer = ref(null);

// 插件表单
const pluginForm = reactive({
	selectedPlugin: null as Plugin | null,
	customPluginLevel: "",
	customPluginName: "",
	customPluginPath: "",
});

// 用户表单
const userForm = reactive({
	userId: "test_user_001", // 默认用户ID - 用于识别不同用户
	roleId: "assistant", // 默认角色ID - 系统角色标识
	sessionId: "session_001", // 默认会话ID - 用于会话隔离
	includeHistory: true,
});

// 存储表单
const storeForm = reactive({
	content: "这是一条测试对话内容", // 默认值方便测试
	role: "user",
	conversation_id: "",
	message_id: "",
	parent_message_id: "",
});

// 检索表单
const retrieveForm = reactive({
	query: "测试查询", // 默认值方便测试
	top_k: 5,
});

// 同步表单
const syncForm = reactive({
	runInBackground: true,
});

// 聊天测试表单
const chatForm = reactive({
	model_id: "",
	query: "你好，请介绍一下自己", // 默认值方便测试
	temperature: 0.7,
	max_tokens: 1000,
	saveToMemory: true,
});

// 聊天历史记录和状态
const chatMessages = ref<ChatMessage[]>([]);
const chatLoading = ref<boolean>(false);
const chatResponse = ref<ChatResponse | null>(null);
const selectedModel = ref<any>(null);

// 操作结果状态
const storeResult = ref<ResponseResult | null>(null);
const retrieveResults = ref<ResultItem[]>([]);
const syncResult = ref<ResponseResult | null>(null);
const syncStatus: any = ref<SyncStatus | null>(null);

// 详情弹窗状态
const selectedItem = ref<ResultItem | null>(null);
const detailsVisible = ref<boolean>(false);

// 加载状态
const storeLoading = ref<boolean>(false);
const retrieveLoading = ref<boolean>(false);
const syncLoading = ref<boolean>(false);
const statusLoading = ref<boolean>(false);

// 生命周期钩子
onMounted(() => {
	getPlugins();
});

onBeforeUnmount(() => {
	// 组件销毁前清除计时器
	if (statusTimer.value) {
		clearInterval(statusTimer.value);
	}
});

// Get available plugins
const getPlugins = async () => {
	try {
		const response = await getMemoryPlugins();
		if (response.success) {
			plugins.value = response.data || [];
			// Default select the last plugin
			if (plugins.value.length > 0 && !pluginForm.selectedPlugin) {
				pluginForm.selectedPlugin = plugins.value[plugins.value.length - 1];
			}
		} else {
			ElMessage.error(response.message || "Failed to get plugin list");
		}
	} catch (error: any) {
		console.error("Failed to get plugin list:", error);
		ElMessage.error("Failed to get plugin list: " + (error.message || error));
	}
};

// 处理插件选择变化
const handlePluginChange = (value: Plugin | null) => {
	console.log("插件选择变化:", value);
	pluginForm.selectedPlugin = value;
};

// 获取当前插件配置
const getCurrentPlugin = (): PluginRequest | null => {
	if (pluginSelectMode.value === "predefined" && pluginForm.selectedPlugin) {
		return {
			plugin_level: pluginForm.selectedPlugin.level,
		};
	} else if (pluginSelectMode.value === "custom") {
		const plugin: PluginRequest = {};

		if (pluginForm.customPluginLevel) {
			// 尝试转换为数字，如果不是数字则保持原样
			const level = Number(pluginForm.customPluginLevel);
			plugin.plugin_level = isNaN(level) ? pluginForm.customPluginLevel : level;
		}

		if (pluginForm.customPluginName) {
			plugin.plugin_name = pluginForm.customPluginName;
		}

		if (pluginForm.customPluginPath) {
			plugin.custom_plugin_path = pluginForm.customPluginPath;
		}

		return Object.keys(plugin).length > 0 ? plugin : null;
	}

	return null;
};

// Store conversation
const handleStoreConversation = async () => {
	if (!userForm.userId) {
		ElMessage.warning("Please enter user ID");
		return;
	}

	if (!userForm.roleId) {
		ElMessage.warning("Please enter role ID");
		return;
	}

	if (!storeForm.content) {
		ElMessage.warning("Please enter conversation content");
		return;
	}

	storeLoading.value = true;
	try {
		const response = await storeConversation(
			storeForm as ConversationRequest,
			userForm.userId,
			userForm.roleId, // Must pass roleId
			userForm.sessionId || undefined,
			getCurrentPlugin() || undefined,
		);
		storeResult.value = response;
		if (response.success) {
			ElMessage.success(response.message || "Stored successfully");
		} else {
			ElMessage.error(response.message || "Store failed");
		}
	} catch (error: any) {
		console.error("Store conversation failed:", error);
		ElMessage.error("Store conversation failed: " + (error.message || error));
		storeResult.value = { success: false, message: "Store conversation failed: " + (error.message || error), data: null };
	} finally {
		storeLoading.value = false;
	}
};

// Retrieve conversations
const handleRetrieveConversations = async () => {
	if (!userForm.userId) {
		ElMessage.warning("Please enter user ID");
		return;
	}

	if (!userForm.roleId) {
		ElMessage.warning("Please enter role ID");
		return;
	}

	if (!retrieveForm.query) {
		ElMessage.warning("Please enter query content");
		return;
	}

	retrieveLoading.value = true;
	try {
		const response = await retrieveConversations(
			{
				query: retrieveForm.query,
				top_k: retrieveForm.top_k,
				include_history: userForm.includeHistory,
			},
			userForm.userId,
			userForm.roleId, // Must pass roleId
			userForm.sessionId || undefined,
			getCurrentPlugin() || undefined,
		);
		if (response.success) {
			retrieveResults.value = response.data || [];
			ElMessage.success(response.message || "Retrieved successfully");
		} else {
			ElMessage.error(response.message || "Retrieve failed");
			retrieveResults.value = [];
		}
	} catch (error: any) {
		console.error("Retrieve conversations failed:", error);
		ElMessage.error("Retrieve conversations failed: " + (error.message || error));
		retrieveResults.value = [];
	} finally {
		retrieveLoading.value = false;
	}
};

// 模型选择变更
const handleModelChange = (model: any) => {
	console.log("选择的模型信息: ", model);
	selectedModel.value = model;
};

// Send chat message
const handleSendMessage = async () => {
	if (!chatForm.model_id) {
		ElMessage.warning("Please select a model");
		return;
	}

	if (!chatForm.query.trim()) {
		ElMessage.warning("Please enter chat content");
		return;
	}

	// If need to save to memory system, check user ID and role ID
	if (chatForm.saveToMemory) {
		if (!userForm.userId) {
			ElMessage.warning("Please enter user ID");
			return;
		}

		if (!userForm.roleId) {
			ElMessage.warning("Please enter role ID");
			return;
		}
	}

	// 添加用户消息到聊天记录
	chatMessages.value.push({
		role: "user",
		content: chatForm.query,
	});

	const requestData: ChatTestRequest = {
		model_id: chatForm.model_id,
		query: chatForm.query,
		temperature: chatForm.temperature,
		max_tokens: chatForm.max_tokens,
		conversation_history: chatMessages.value.slice(0, -1), // 不包括刚添加的消息
	};

	// 如果需要保存到记忆系统，则添加用户ID等信息
	if (chatForm.saveToMemory) {
		requestData.user_id = userForm.userId;
		requestData.role_id = userForm.roleId; // 必须传递roleId
		requestData.session_id = userForm.sessionId;
		requestData.plugin_request = getCurrentPlugin() || undefined; // 添加插件选择
	}

	chatLoading.value = true;

	// 发送请求
	try {
		const response = await testChat(requestData);
		if (response.success) {
			// 添加AI回复到聊天记录
			chatMessages.value.push({
				role: "assistant",
				content: response.data.response,
			});
			chatResponse.value = response.data;
		} else {
			ElMessage.error(response.message || "聊天失败");
		}
	} catch (error: any) {
		console.error("聊天失败:", error);
		ElMessage.error("聊天失败: " + (error.message || error));
	} finally {
		// 清空输入框
		chatForm.query = "";
		chatLoading.value = false;
	}
};

// 清空聊天记录
const clearChatMessages = () => {
	chatMessages.value = [];
	chatResponse.value = null;
};

// Sync conversations
const handleSyncConversations = async () => {
	if (!userForm.userId) {
		ElMessage.warning("Please enter user ID");
		return;
	}

	if (!userForm.roleId) {
		ElMessage.warning("Please enter role ID");
		return;
	}

	syncLoading.value = true;
	try {
		const response = await syncConversations(
			userForm.userId,
			userForm.roleId, // Must pass roleId
			syncForm.runInBackground,
			getCurrentPlugin() || undefined,
		);
		syncResult.value = response;
		if (response.success) {
			ElMessage.success(response.message || "Sync task started");
			// Start status polling
			startStatusPolling();
		} else {
			ElMessage.error(response.message || "Failed to start sync task");
		}
	} catch (error: any) {
		console.error("Sync conversations failed:", error);
		ElMessage.error("Sync conversations failed: " + (error.message || error));
		syncResult.value = { success: false, message: "Sync conversations failed: " + (error.message || error), data: null };
	} finally {
		syncLoading.value = false;
	}
};

// Get sync status
const handleGetSyncStatus = async () => {
	if (!userForm.userId) {
		ElMessage.warning("Please enter user ID");
		return;
	}

	if (!userForm.roleId) {
		ElMessage.warning("Please enter role ID");
		return;
	}

	statusLoading.value = true;
	try {
		const response = await getSyncStatus(userForm.userId, userForm.roleId, getCurrentPlugin() || undefined);
		if (response.success) {
			syncStatus.value = response.data;
			// If syncing, start status polling
			if (syncStatus.value && syncStatus.value.is_syncing) {
				startStatusPolling();
			}
		} else {
			ElMessage.error(response.message || "Failed to get sync status");
		}
	} catch (error: any) {
		console.error("Get sync status failed:", error);
		ElMessage.error("Get sync status failed: " + (error.message || error));
	} finally {
		statusLoading.value = false;
	}
};

// 启动状态轮询
const startStatusPolling = () => {
	// 清除现有的计时器
	if (statusTimer.value) {
		clearInterval(statusTimer.value);
	}

	// 设置新的计时器，每2秒查询一次状态
	statusTimer.value = setInterval(() => {
		// 只有在同步中才继续查询
		if (syncStatus.value && syncStatus.value.is_syncing) {
			// 确保每次查询状态都包含必要的参数
			handleGetSyncStatus();
		} else {
			// 已完成同步，清除计时器
			if (statusTimer.value) {
				clearInterval(statusTimer.value);
				statusTimer.value = null;
			}
		}
	}, 2000);
};

// 查看详情
const showDetails = (item: ResultItem) => {
	selectedItem.value = item;
	detailsVisible.value = true;
};
</script>

<style lang="scss" scoped>
.filter-container {
	margin-bottom: 20px;
}

.box-card {
	margin-bottom: 20px;
}

.clearfix {
	&::before,
	&::after {
		display: table;
		content: "";
	}

	&::after {
		clear: both;
	}
}

/* 聊天消息样式 */
.chat-messages {
	max-height: 400px;
	overflow-y: auto;
	margin-bottom: 20px;
	padding: 10px;
	border: 1px solid #e6e6e6;
	border-radius: 4px;

	.message {
		margin-bottom: 10px;
		display: flex;

		&.user {
			justify-content: flex-end;

			.message-content {
				background-color: #e6f7ff;
				border: 1px solid #91d5ff;
			}
		}

		&.assistant .message-content {
			background-color: #f6ffed;
			border: 1px solid #b7eb8f;
		}

		.message-content {
			max-width: 70%;
			padding: 10px;
			border-radius: 8px;

			.message-role {
				font-weight: bold;
				margin-bottom: 5px;
			}

			.message-text {
				white-space: pre-wrap;
				word-break: break-word;
			}
		}
	}
}
</style>
