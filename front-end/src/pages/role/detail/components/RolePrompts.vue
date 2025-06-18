<script setup lang="ts">
import { ref, defineProps, defineEmits, onMounted, reactive, computed, nextTick } from "vue";
import { ElMessage, ElMessageBox, FormInstance, type FormRules } from "element-plus";
import { Edit, Delete, Plus, Timer, VideoPlay, InfoFilled } from "@element-plus/icons-vue";
import type { RolePrompt } from "@/types/role";
import {
	updatePrompt,
	getPromptDetail,
	deletePrompt as deleteRolePrompt,
	createPrompt as addRolePrompt,
	getPromptsByRoleId,
} from "@/api/prompt";
import { chatTestStream } from "@/api/llm";
import { listAudioTimbres } from "@/api/audio-timbre";
import { rolePrompt } from "@/utils/editorButton";
import AvatarEditor from "@/components/AvatarEditor/AvatarEditor.vue";

/**
 * Audio timbre type definition
 * @typedef {Object} AudioTimbre
 * @property {number} id - Timbre ID
 * @property {string} alias - Alias
 * @property {string} speaker_id - Voice ID
 * @property {string} version - Training version
 * @property {string} state - Status
 * @property {string} audition - Voice B64
 * @property {string} create_time - Creation time
 * @property {string} update_time - Update time
 */
interface AudioTimbre {
	id: number;
	alias?: string;
	speaker_id?: string;
	version?: string;
	state?: string;
	audition?: string;
	create_time: string;
	update_time: string;
}

/**
 * Component props definition
 * @typedef {Object} Props
 * @property {RolePrompt[]} prompts - Prompt list
 * @property {boolean} loading - Loading state
 * @property {string} roleId - Role ID
 */
const props = defineProps<{
	prompts: RolePrompt[];
	loading: boolean;
	roleId: string;
	relationshipLevels: any[];
}>();

/**
 * Component events definition
 */
const emit = defineEmits<{
	(e: "refresh"): void;
}>();

// Pagination related state
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);
const paginatedPrompts = ref<RolePrompt[]>([]);
const paginationLoading = ref(false);

// Calculate whether to display pagination component
const showPagination = computed(() => total.value > pageSize.value);

// Add prompt related
const ruleFormRef = ref<FormInstance>();
const promptDialogVisible = ref(false);
const promptDialogType = ref("add"); // Dialog type: add or edit
const currentEditPrompt = ref<number>(0); // Current prompt ID being edited
const promptForm = ref({
	role_id: props.roleId,
	level: 1,
	prompt_text: "",
	status: 1,
	prologue: [""], // Modified to store multiple openers in array form
	dialogue: "",
	timbre: undefined,
});

const formRules = reactive<FormRules>({
	prompt_text: [
		{ required: true, message: "Please enter role settings", trigger: "blur" },
		{ min: 3, max: 2000, message: "Length should be between 3 and 2000 characters", trigger: "blur" },
	],
	// timbre: [{ required: true, message: "Please select character voice", trigger: "blur" }],
});

const chatForm = ref({
	username: "User",
	relationship_level: 1,
	long_term_memory: false, // Whether to enable long-term memory
	memory_level: 6, // Memory level, 6 for dialogue memory, 7 for Mem0 memory, 10 for dialogue memory
});

/**
 * Get paginated prompt data
 */
const fetchPrompts = async () => {
	try {
		paginationLoading.value = true;
		// Call API that supports pagination
		const response = await getPromptsByRoleId(props.roleId, {
			page: currentPage.value,
			size: pageSize.value,
		});

		// API return format is { items: [], total: number, page: number, size: number, pages: number }
		if (response && typeof response === "object" && "items" in response) {
			paginatedPrompts.value = response.items;
			total.value = response.total;
		} else {
			// If API call fails, use input props data for client-side pagination
			const startIndex = (currentPage.value - 1) * pageSize.value;
			const endIndex = startIndex + pageSize.value;
			paginatedPrompts.value = props.prompts.slice(startIndex, endIndex);
			total.value = props.prompts.length;
		}
	} catch (error) {
		console.error("Failed to get prompt list", error);
		// Fallback to using props data for client-side pagination
		const startIndex = (currentPage.value - 1) * pageSize.value;
		const endIndex = startIndex + pageSize.value;
		paginatedPrompts.value = props.prompts.slice(startIndex, endIndex);
		total.value = props.prompts.length;
	} finally {
		paginationLoading.value = false;
	}
};

/**
 * Handle page change
 */
const handleCurrentChange = (page: number) => {
	currentPage.value = page;
	fetchPrompts();
};

/**
 * Handle page size change
 */
const handleSizeChange = (size: number) => {
	pageSize.value = size;
	currentPage.value = 1; // Reset to first page
	fetchPrompts();
};

/**
 * Refresh prompt list
 */
const refreshPrompts = () => {
	fetchPrompts();
	emit("refresh");
};

/**
 * Add new prompt
 */
const addNewPrompt = () => {
	promptDialogType.value = "add";
	chatMessages.value = [];
	promptForm.value = {
		role_id: props.roleId,
		level: 1,
		prompt_text: "",
		status: 1,
		prologue: [""], // Initialize with one empty opener
		dialogue: "",
		timbre: undefined,
	};
	promptDialogVisible.value = true;
};

/**
 * Edit prompt
 * @param {RolePrompt} prompt - Prompt object to edit
 */
async function editPrompt(prompt: RolePrompt) {
	promptDialogType.value = "edit";
	currentEditPrompt.value = prompt.id;
	const data = await getPromptDetail(prompt.id);
	chatMessages.value = [];
	// Handle prologue field compatibility
	let prologue = [];
	if (data.prologue.length) {
		prologue = data.prologue.map((item) => item.prologue);
	}

	if (prologue.length === 0) {
		prologue = [""];
	}

	promptForm.value = {
		role_id: data.role_id,
		level: data.level,
		prompt_text: data.prompt_text,
		status: data.status,
		prologue: prologue,
		dialogue: data.dialogue || "",
		timbre: data.timbre,
	};
	promptDialogVisible.value = true;

	// Reset chat messages and add opener
	chatMessages.value = [];
	if (promptForm.value.prologue.length > 0 && promptForm.value.prologue[0]) {
		// Randomly select an opener
		const randomIndex = Math.floor(Math.random() * promptForm.value.prologue.length);
		const selectedPrologue = promptForm.value.prologue[randomIndex] || "";

		if (selectedPrologue.trim()) {
			chatMessages.value.push({
				type: "role",
				content: selectedPrologue,
				timestamp: new Date().toLocaleTimeString(),
				audio: "",
				sources: [],
			});
			// Scroll to bottom
			scrollToBottom();
		}
	}
}

/**
 * Delete prompt
 * @param {RolePrompt} prompt - Prompt object to delete
 */
const deletePrompt = (prompt: RolePrompt) => {
	ElMessageBox.confirm("Are you sure you want to delete this prompt?", "Confirmation", {
		confirmButtonText: "Confirm",
		cancelButtonText: "Cancel",
		type: "warning",
	})
		.then(async () => {
			try {
				await deleteRolePrompt(prompt.id);
				ElMessage.success("Delete successful");
				refreshPrompts(); // Use the new refresh method
			} catch (error) {
				console.error("Failed to delete prompt", error);
				ElMessage.error("Failed to delete prompt");
			}
		})
		.catch(() => {
			// Operation canceled
		});
};

/**
 * Submit prompt form
 */
const submitPrompt = async (formEl: FormInstance | undefined) => {
	if (!promptForm.value.prompt_text) {
		ElMessage.warning("Please enter role settings");
		return;
	}

	if (!formEl) return;
	await formEl.validate(async (valid, fields) => {
		if (valid) {
			try {
				// Filter out empty openers
				const nonEmptyprologue = promptForm.value.prologue.filter((p) => p.trim() !== "");
				// Prepare data for submission, ensuring all required fields are included
				const submitData = {
					role_id: promptForm.value.role_id,
					level: promptForm.value.level,
					prompt_text: promptForm.value.prompt_text,
					status: promptForm.value.status,
					prologue: nonEmptyprologue.length > 0 ? nonEmptyprologue : [""], // Ensure at least one opener
					dialogue: promptForm.value.dialogue || "",
					timbre: promptForm.value.timbre,
				};

				if (promptDialogType.value === "add") {
					await addRolePrompt(submitData);
					ElMessage.success("Prompt added successfully");
				} else {
					await updatePrompt(currentEditPrompt.value, submitData);
					ElMessage.success("Prompt updated successfully");
				}
				promptDialogVisible.value = false;
				refreshPrompts(); // Use the new refresh method
			} catch (error: any) {
				console.error(promptDialogType.value === "add" ? "Failed to add prompt" : "Failed to update prompt", error);
				const message = error.response?.data?.message;
				ElMessage.error(message || (promptDialogType.value === "add" ? "Failed to add prompt" : "Failed to update prompt"));
			}
		} else {
			console.log("error submit!", fields);
		}
	});
};

/**
 * Add new opener input field
 */
const addPrologue = () => {
	promptForm.value.prologue.push("");
};

/**
 * Delete opener at specified index
 * @param {number} index - Index of the opener to delete
 */
const removePrologue = (index: number) => {
	if (promptForm.value.prologue.length > 1) {
		promptForm.value.prologue.splice(index, 1);
	} else {
		// If there's only one opener, clear its content
		promptForm.value.prologue = [""];
	}
};

// Chat preview related
/**
 * Chat message array
 * @type {Array<{type: string, content: string, timestamp: string, audio: string, sources?: Array<{id: string, text: string, title: string, source: string, score: number}>}>}
 */
const chatMessages = ref<Array<{ type: string; content: string; timestamp: string; audio: string; sources?: any }>>([]);

/**
 * Chat container reference
 */
const chatContainer = ref<HTMLElement | null>(null);

/**
 * User input message
 */
const userMessage = ref("");

/**
 * Whether role is currently typing
 */
const isRoleTyping = ref(false);

/**
 * Current session ID
 */
const sessionId = ref(Date.now().toString());

/**
 * Role's current reply content
 */
const currentResponse = ref("");

/**
 * Scroll chat messages to bottom
 */
const scrollToBottom = async () => {
	await nextTick();
	const container = chatContainer.value;
	if (container) {
		container.scrollTop = container.scrollHeight;
	}
};

/**
 * Send chat message
 */
const sendMessage = () => {
	if (!userMessage.value.trim()) return;
	if (!promptForm.value.prompt_text) {
		ElMessage.warning("Please complete the role settings first");
		return;
	}
	// Add user message
	chatMessages.value.push({
		type: "user",
		content: userMessage.value,
		timestamp: new Date().toLocaleTimeString(),
		audio: "",
		sources: [],
	});

	// Scroll to bottom
	scrollToBottom();

	// Clear input field
	const message = userMessage.value;
	userMessage.value = "";

	// Set role typing status
	isRoleTyping.value = true;
	currentResponse.value = "";
	function getRandomElement(arr: Array<any>): any {
		if (!arr.length) return "";
		const randomIndex = Math.floor(Math.random() * arr.length); // Get random index
		return arr[randomIndex]; // Return random array element
	}
	chatTestStream(
		{
			message: message,
			role_id: props.roleId,
			level: promptForm.value.level.toString(),
			user_level: promptForm.value.level.toString(),
			session_id: sessionId.value,
			role_prompt: promptForm.value.prompt_text,
			role_prologue: getRandomElement(promptForm.value.prologue),
			role_dialogue: promptForm.value.dialogue,
			user_name: chatForm.value.username,
			relationship_level: chatForm.value.relationship_level,
			long_term_memory: chatForm.value.long_term_memory,
			memory_level: chatForm.value.memory_level,
		},
		() => {},
		(rawChunk) => {
			// Process each received token
			if (isRoleTyping.value) {
				// Accumulate current response content
				currentResponse.value += rawChunk;
				// Real-time scroll to bottom
				scrollToBottom();
			}
		},
		(error) => {
			// Handle errors
			isRoleTyping.value = false;
			ElMessage.error("Failed to get character response");
			console.error("Chat stream request failed", error);

			// Add error message
			chatMessages.value.push({
				type: "role",
				content: "Sorry, I can't respond right now. Please try again later.",
				timestamp: new Date().toLocaleTimeString(),
				audio: "",
				sources: [],
			});
			// Scroll to bottom
			scrollToBottom();
		},
	).finally(() => {
		// When request completes, turn off typing status
		isRoleTyping.value = false;

		// Add complete response to message list
		if (currentResponse.value) {
			const audio_text = currentResponse.value.split("<div>");
			let audio = "";
			if (audio_text.length > 1 && audio_text[1].length > 1) {
				audio = "data:audio/mpeg;base64," + audio_text[1].replaceAll("\"", "").trim();
				playAudio(audio);
			}
			let sources = {};
			if (audio_text.length > 2 && audio_text[2].length > 1) {
				try {
					sources = JSON.parse(audio_text[2].trim());
				} catch (e) {}
			} else {
				audio = "";
			}
			const data = {
				type: "role",
				content: audio_text[0],
				audio: audio,
				timestamp: new Date().toLocaleTimeString(),
				sources: sources,
			};
			chatMessages.value.push(data);
			// Scroll to bottom
			scrollToBottom();
		}
	});
};

/**
 * Reset chat with random opener
 */
const resetChat = () => {
	chatMessages.value = [];

	// If there are openers, randomly select one
	if (promptForm.value.prologue.length > 0) {
		const validprologue = promptForm.value.prologue.filter((p) => p.trim() !== "");
		if (validprologue.length > 0) {
			const randomIndex = Math.floor(Math.random() * validprologue.length);
			chatMessages.value.push({
				type: "role",
				content: validprologue[randomIndex],
				timestamp: new Date().toLocaleTimeString(),
				audio: "",
				sources: [],
			});
			// Scroll to bottom
			scrollToBottom();
		}
	}
};

// Voice related
const audioTimbres = ref<AudioTimbre[]>([]);
const audioPlayer = ref<HTMLAudioElement | null>(null);

/**
 * Get voice list
 */
const fetchAudioTimbres = async () => {
	try {
		const response = await listAudioTimbres();
		audioTimbres.value = response;
	} catch (error) {
		console.error("Failed to get voice list", error);
		ElMessage.error("Failed to get voice list");
	}
};

/**
 * Play voice
 * @param {string} base64Audio - base64 encoded audio data
 */
const playAudio = (base64Audio: string) => {
	if (!base64Audio) {
		ElMessage.warning("No audio data available");
		return;
	}

	if (audioPlayer.value) {
		audioPlayer.value.pause();
	}

	try {
		// Check if base64 data contains audio format information
		let audioUrl = base64Audio;
		if (!base64Audio.startsWith("data:audio/")) {
			// If no audio format information, add default wav format
			audioUrl = `data:audio/wav;base64,${base64Audio}`;
		}

		audioPlayer.value = new Audio(audioUrl);

		// Add error handling
		audioPlayer.value.onerror = (error) => {
			console.error("Audio playback error:", error);
			ElMessage.error("Audio playback failed, please check audio format");
		};

		// Add load error handling
		audioPlayer.value.oncanplaythrough = () => {
			audioPlayer.value?.play().catch((error) => {
				console.error("Audio playback failed:", error);
				ElMessage.error("Audio playback failed, please check audio format");
			});
		};
	} catch (error) {
		console.error("Audio processing error:", error);
		ElMessage.error("Audio processing failed, please check audio data");
	}
};

// Initialize pagination data when component mounts
onMounted(() => {
	fetchAudioTimbres();
	fetchPrompts();
});
</script>

<template>
	<div class="prompt-section">
		<div class="section-toolbar">
			<el-button class="btn-class" type="primary" size="small" @click="addNewPrompt">
				<el-icon>
					<Plus />
				</el-icon>
				Add Prompt
			</el-button>
		</div>
		<div class="prompt-list" v-loading="paginationLoading || loading">
			<el-empty v-if="paginatedPrompts.length === 0 && !paginationLoading" description="No prompts available" />
			<div class="prompt-grid" v-else>
				<el-card v-for="prompt in paginatedPrompts" :key="prompt.id" class="prompt-card" shadow="hover">
					<div class="prompt-header">
						<div class="prompt-level">Level: {{ prompt.level }}</div>
						<el-tag :type="prompt.status === 1 ? 'success' : 'danger'">
							{{ prompt.status === 1 ? "Enabled" : "Disabled" }}
						</el-tag>
					</div>
					<div class="prompt-preview">
						{{ prompt.prompt_text }}
					</div>
					<div class="prompt-card-footer">
						<div class="prompt-update-time">
							<el-icon>
								<Timer />
							</el-icon>
							<span>Updated: {{ new Date(prompt.updated_at).toLocaleString() }}</span>
						</div>
						<div class="prompt-actions">
							<el-button class="btn-class" type="primary" link @click="editPrompt(prompt)">
								<el-icon>
									<Edit />
								</el-icon>
								Try out
							</el-button>
							<el-button type="danger" link @click="deletePrompt(prompt)">
								<el-icon>
									<Delete />
								</el-icon>
								Delete
							</el-button>
						</div>
					</div>
				</el-card>
			</div>

			<!-- Pagination component -->
			<div v-if="showPagination" class="pagination-container">
				<el-pagination
					v-model:current-page="currentPage"
					v-model:page-size="pageSize"
					:page-sizes="[5, 10, 20, 50]"
					:total="total"
					layout="total, sizes, prev, pager, next, jumper"
					@size-change="handleSizeChange"
					@current-change="handleCurrentChange"
				/>
			</div>
		</div>

		<!-- Add/edit prompt drawer -->
		<el-drawer
			v-model="promptDialogVisible"
			:title="promptDialogType === 'add' ? 'Add Role Description' : 'Edit Role Description'"
			direction="rtl"
			size="85%"
			class="prompt-drawer"
		>
			<template #header>
				<div class="drawer-header">
					<h3>{{ promptDialogType === "add" ? "Add Role Description" : "Edit Role Description" }}</h3>
				</div>
			</template>

			<div class="prompt-drawer-content">
				<el-row :gutter="16" style="height: 100%">
					<el-col :span="12" class="form-section">
						<div class="form-container">
							<el-form :model="promptForm" label-width="80px" :rules="formRules" ref="ruleFormRef">
								<FormItem label="Role Configuration" label-position="top" style="width: 100%">
									<el-row style="width: 100%">
										<el-col :span="12">
											<FormItem label="Level" tooltipKey="level">
												<el-input-number v-model="promptForm.level" :precision="1" :min="0" :max="100" :step="0.1" />
											</FormItem>
										</el-col>
										<el-col :span="12">
											<FormItem label="Status" tooltipKey="status">
												<el-switch v-model="promptForm.status" :active-value="1" :inactive-value="0" />
											</FormItem>
										</el-col>
									</el-row>
								</FormItem>
								<FormItem label="Role Settings" label-position="top" prop="prompt_text" tooltipKey="rolePrompt">
									<AvatarEditor
										:users="rolePrompt"
										:max-length="3000"
										:min-length="10"
										placeholder="Please enter role description content..."
										v-model="promptForm.prompt_text"
									/>
								</FormItem>

								<!-- Multiple openers settings -->
								<FormItem label-position="top" prop="prologue" tooltipKey="prologue">
									<div class="prologue-section">
										<div class="prologue-header">
											<span>Role Opener List</span>
											<el-button type="primary" size="small" @click="addPrologue">
												<el-icon><Plus /></el-icon>
											</el-button>
										</div>

										<div v-for="(prologue, index) in promptForm.prologue" :key="index" class="prologue-item">
											<el-input
												v-model="promptForm.prologue[index]"
												type="textarea"
												:rows="2"
												show-word-limit
												maxlength="200"
												:placeholder="'Opener #' + (index + 1) + ' (Use () to describe actions or scenes)'"
											/>
											<el-button
												type="danger"
												circle
												size="small"
												class="prologue-delete-btn"
												@click="removePrologue(index)"
												:disabled="promptForm.prologue.length === 1 && !promptForm.prologue[0]"
											>
												<el-icon><Delete /></el-icon>
											</el-button>
										</div>
									</div>
								</FormItem>

								<FormItem label="Dialogue Examples" label-position="top" tooltipKey="dialogue">
									<el-input
										v-model="promptForm.dialogue"
										type="textarea"
										:rows="2"
										maxlength="200"
										show-word-limit
										placeholder="Dialogue that the character might say according to their personality style"
									/>
								</FormItem>
								<FormItem label="Character Voice" label-position="top" prop="timbre" tooltipKey="timbre">
									<el-select v-model="promptForm.timbre" placeholder="Please select character voice" size="large">
										<el-option
											v-for="item in audioTimbres"
											:key="item.id"
											:label="item.alias || item.speaker_id || 'Unnamed Voice'"
											:value="item.speaker_id"
										>
											<div class="timbre-option">
												<span>{{ item.alias || item.speaker_id || "Unnamed Voice" }}</span>
												<el-button type="primary" link @click.stop="playAudio(item.audition)">
													<el-icon><VideoPlay /></el-icon>
												</el-button>
											</div>
										</el-option>
									</el-select>
								</FormItem>
							</el-form>
						</div>
					</el-col>

					<el-col :span="12" class="chat-section">
						<div class="chat-container">
							<div class="preview-header">
								<h4 class="preview-title">Chat Preview Effect</h4>
								<el-button type="primary" size="small" @click="resetChat"> Reset Conversation </el-button>
							</div>
							<el-divider />
							<div class="chat-preview">
								<div class="chat-messages" ref="chatContainer">
									<!-- If no messages and has opener, show opener -->
									<div
										v-if="chatMessages.length === 0 && promptForm.prologue.length > 0 && promptForm.prologue[0]"
										class="message role-message"
									>
										<div class="message-content">{{ promptForm.prologue[0] }}</div>
										<div class="message-time">{{ new Date().toLocaleTimeString() }}</div>
									</div>

									<!-- Chat message list -->
									<div
										v-for="(message, index) in chatMessages"
										:key="index"
										:class="['message', message.type === 'user' ? 'user-message' : 'role-message']"
									>
										<!-- User message -->
										<template v-if="message.type === 'user'">
											<div class="message-content">
												{{ message.content }}
											</div>
											<div class="message-time">{{ message.timestamp }}</div>
										</template>

										<!-- AI character message -->
										<template v-else>
											<el-popover
												v-if="message.sources && message.sources.length > 0"
												placement="top"
												width="600"
												trigger="hover"
											>
												<template #reference>
													<div class="message-content">
														{{ message.content }}
														<el-button v-if="message.audio" type="primary" link @click.stop="playAudio(message.audio)">
															<el-icon><VideoPlay /></el-icon>
														</el-button>
														<el-icon class="sources-indicator" title="Contains reference information">
															<InfoFilled />
														</el-icon>
													</div>
												</template>
												<template #default>
													<div class="sources-popup">
														<h4 class="sources-title">Reference Information Sources</h4>
														<el-table :data="message.sources" size="small" style="width: 100%">
															<el-table-column prop="title" label="Title" width="120" show-overflow-tooltip />
															<el-table-column prop="text" label="Content" min-width="200" show-overflow-tooltip />
															<el-table-column prop="source" label="Source" width="100" show-overflow-tooltip />
															<el-table-column prop="score" label="Similarity" width="80">
																<template #default="scope">
																	<el-tag
																		size="small"
																		:type="
																			scope.row.score < 0.5 ? 'success' : scope.row.score < 0.8 ? 'warning' : 'info'
																		"
																	>
																		{{ (scope.row.score * 100).toFixed(1) }}%
																	</el-tag>
																</template>
															</el-table-column>
														</el-table>
													</div>
												</template>
											</el-popover>
											<!-- AI message without sources -->
											<div v-else class="message-content">
												{{ message.content }}
												<el-button v-if="message.audio" type="primary" link @click.stop="playAudio(message.audio)">
													<el-icon><VideoPlay /></el-icon>
												</el-button>
											</div>
											<div class="message-time">{{ message.timestamp }}</div>
										</template>
									</div>

									<!-- Typing indicator -->
									<div v-if="isRoleTyping" class="message role-message typing">
										<div class="message-content">
											<template v-if="currentResponse">
												{{ currentResponse }}<span class="cursor-blink">|</span>
											</template>
											<span v-else class="typing-indicator">
												<span class="dot"></span>
												<span class="dot"></span>
												<span class="dot"></span>
											</span>
										</div>
									</div>
								</div>

								<div class="chat-input">
									<el-form>
										<div class="chat-input-item">
											<FormItem label="Name" tooltipKey="username">
												<el-input v-model="chatForm.username" placeholder="Please enter your name"></el-input>
											</FormItem>
											<FormItem label="Relationship Level" style="width: 300px" tooltipKey="relationship_level">
												<el-select v-model="chatForm.relationship_level">
													<el-option
														v-for="item in relationshipLevels"
														:value="item.relationship_level"
														:label="item.relationship_name"
														:key="item.id"
													></el-option>
												</el-select>
											</FormItem>
										</div>
										<div class="chat-input-item">
											<FormItem label="Enable Long-term Memory" tooltipKey="long_term_memory">
												<el-switch v-model="chatForm.long_term_memory" />
											</FormItem>
											<FormItem label="Memory Level" style="width: 300px" tooltipKey="memory_level">
												<el-select v-model="chatForm.memory_level">
													<el-option :value="6" label="RAG Conversation Memory"></el-option>
													<el-option :value="7" label="Mem0 Memory"></el-option>
													<el-option :value="10" label="Knowledge Graph Memory" disabled></el-option>
												</el-select>
											</FormItem>
										</div>
									</el-form>
									<el-input v-model="userMessage" placeholder="Enter message..." @keyup.enter="sendMessage">
										<template #append>
											<el-button @click="sendMessage">Send</el-button>
										</template>
									</el-input>
								</div>
							</div>
						</div>
					</el-col>
				</el-row>
			</div>

			<template #footer>
				<div class="drawer-footer">
					<el-button @click="promptDialogVisible = false">Cancel</el-button>
					<el-button type="primary" @click="submitPrompt(ruleFormRef)">Confirm</el-button>
				</div>
			</template>
		</el-drawer>
	</div>
</template>

<style scoped lang="scss">
.prompt-section {
	padding: 0;
}

.section-toolbar {
	display: flex;
	justify-content: flex-end;
	align-items: center;
	margin-bottom: 20px;
	padding: 0 4px;
}

/* New prompt card styles */
.prompt-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
	gap: 16px;
	margin-bottom: 20px;
}

.prompt-card {
	position: relative;
	background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
	border: 1px solid #e2e8f0;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	transition: all 0.3s ease;
	height: 280px;
	overflow: hidden;
}

.prompt-card:hover {
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
	border-color: #2563eb;
}

.prompt-header {
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
	margin-bottom: 15px;
}

.prompt-level {
	font-size: 16px;
	color: #1e293b;
	margin: 0;
	font-weight: 600;
	line-height: 1.4;
}

.prompt-meta {
	display: flex;
	gap: 12px;
	margin-bottom: 12px;
	font-size: 12px;
	color: #64748b;
}

.prompt-preview {
	background: #f8fafc;
	border-radius: 6px;
	padding: 12px;
	margin-bottom: 12px;
	font-size: 14px;
	line-height: 1.5;
	color: #64748b;
	height: 90px;
	overflow: hidden;
	position: relative;
	border: 1px solid #e2e8f0;
}

.prompt-preview::after {
	content: "";
	position: absolute;
	bottom: 0;
	left: 0;
	right: 0;
	height: 30px;
	background: linear-gradient(transparent, #f8fafc);
}

.prompt-card-footer {
	position: absolute;
	bottom: 12px;
	left: 20px;
	right: 20px;
	display: flex;
	justify-content: space-between;
	align-items: center;
	background: rgba(255, 255, 255, 0.9);
	padding: 8px 0;
}

.prompt-update-time {
	display: flex;
	align-items: center;
	gap: 5px;
	font-size: 12px;
	color: #64748b;
}

.prompt-actions {
	display: flex;
	gap: 10px;
}

/* Prompt drawer styles */
:deep(.prompt-drawer .el-drawer__header) {
	background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
	color: white;
	margin-bottom: 0;
}

.drawer-header h3 {
	margin: 0;
	color: white;
	font-size: 18px;
	font-weight: 600;
}

.prompt-drawer-content {
	height: calc(100vh - 200px);
	padding: 24px;
}

.form-section {
	height: 100%;
}

.form-container {
	height: 100%;
	overflow-y: auto;
	padding-right: 12px;
}

.chat-section {
	height: 100%;
	border-left: 1px solid var(--el-border-color-lighter);
	padding-left: 16px;
}

.chat-container {
	height: 100%;
	display: flex;
	flex-direction: column;
}

.preview-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 10px;
}

.preview-title {
	font-size: 18px;
	margin: 0;
	color: var(--el-text-color-primary);
}

.drawer-footer {
	display: flex;
	justify-content: flex-end;
	gap: 12px;
	padding: 16px 24px;
	border-top: 1px solid var(--el-border-color-lighter);
	background: #f8fafc;
}

/* Opener styles */
.prologue-section {
	display: flex;
	flex-direction: column;
	gap: 10px;
	width: 100%;
}

.prologue-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 10px;
}

.prologue-item {
	display: flex;
	gap: 10px;
	align-items: flex-start;
	margin-bottom: 10px;
}

.prologue-delete-btn {
	margin-top: 8px;
}

/* Chat preview styles */
.chat-preview {
	display: flex;
	flex-direction: column;
	height: calc(100% - 60px);
	background: #f5f6fa;
	border-radius: 8px;
	overflow: hidden;
	flex: 1;
}

.chat-messages {
	flex: 1;
	padding: 15px;
	overflow-y: auto;
	display: flex;
	flex-direction: column;
	gap: 10px;
}

.message {
	max-width: 70%;
	padding: 10px 15px;
	border-radius: 12px;
	position: relative;
	margin-bottom: 10px;
}

.user-message {
	align-self: flex-end;
	background-color: #95ec69;
	color: #000;
	border-bottom-right-radius: 4px;
}

.role-message {
	align-self: flex-start;
	background-color: #fff;
	color: #333;
	border-bottom-left-radius: 4px;
}

.message-content {
	font-size: 14px;
	line-height: 1.5;
	word-break: break-word;
}

.message-time {
	font-size: 11px;
	color: rgba(0, 0, 0, 0.45);
	margin-top: 4px;
	text-align: right;
}

.chat-input {
	padding: 10px;
	background: #fff;
	border-top: 1px solid #eee;
}

/* Typing indicator styles */
.typing-indicator {
	display: flex;
	align-items: center;
	column-gap: 4px;
}

.dot {
	height: 8px;
	width: 8px;
	border-radius: 50%;
	background-color: #bbb;
	display: inline-block;
	animation: bounce 1.3s linear infinite;
}

.dot:nth-child(2) {
	animation-delay: 0.15s;
}

.dot:nth-child(3) {
	animation-delay: 0.3s;
}

@keyframes bounce {
	0%,
	60%,
	100% {
		transform: translateY(0);
	}
	30% {
		transform: translateY(-4px);
	}
}

.cursor-blink {
	animation: cursor-blink 0.8s infinite;
}

@keyframes cursor-blink {
	0%,
	49% {
		opacity: 1;
	}
	50%,
	100% {
		opacity: 0;
	}
}

.timbre-option {
	display: flex;
	justify-content: space-between;
	align-items: center;
	width: 100%;
	padding: 0 10px;
}

.timbre-option .el-button {
	padding: 0;
}

.chat-input-item {
	display: flex;
	justify-content: space-between;
}

/* Pagination styles */
.pagination-container {
	display: flex;
	justify-content: center;
	align-items: center;
	margin-top: 20px;
	padding: 20px 0;
}

.pagination-container .el-pagination {
	justify-content: center;
}

/* Responsive pagination */
@media (max-width: 768px) {
	.pagination-container .el-pagination {
		justify-content: center;
	}
}

/* Sources related styles */
.sources-indicator {
	margin-left: 5px;
	color: #409eff;
	cursor: pointer;
	vertical-align: middle;
}

.sources-popup {
	max-height: 400px;
	overflow-y: auto;
}

.sources-title {
	margin: 0 0 10px 0;
	font-size: 14px;
	color: #303133;
	font-weight: 600;
}

.sources-popup .el-table {
	margin-top: 5px;
}

.sources-popup .el-table .el-table__cell {
	padding: 8px 0;
}

.sources-popup .el-tag {
	font-size: 12px;
}

/* Responsive design */
@media (max-width: 1200px) {
	.prompt-drawer-content {
		height: calc(100vh - 180px);
	}

	:deep(.prompt-drawer) {
		width: 95% !important;
	}
}

@media (max-width: 768px) {
	.prompt-drawer-content {
		height: calc(100vh - 160px);
		padding: 16px;
	}

	.prompt-drawer-content .el-row {
		flex-direction: column;
	}

	.form-section,
	.chat-section {
		height: auto;
		min-height: 50vh;
	}

	.chat-section {
		border-left: none;
		border-top: 1px solid var(--el-border-color-lighter);
		padding-left: 0;
		padding-top: 16px;
		margin-top: 16px;
	}

	.chat-preview {
		height: 400px;
	}

	:deep(.prompt-drawer) {
		width: 100% !important;
	}
}
@import '@/layouts/WriterLayout/css/extra.scss';

.btn-class {
	color: #fff;
	background-color: $btn-bg-color0;
	border-color: $btn-bg-color0;
}
</style>
