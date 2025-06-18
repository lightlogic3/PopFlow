<script setup lang="ts">
import { ref, watch, onMounted, nextTick } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Delete, Plus, ChatDotRound, Document, Timer, Trophy } from "@element-plus/icons-vue";
import type { FormItemRule } from "element-plus";
import { chatTask } from "@/api/llm";
import { getTaskList, addTask, deleteTask, updateTask } from "@/api/role-tasks";
import "@/assets/css/knowledge.scss";
import FileUploader from "@/components/FileUploader";
/**
 * Character-Task Chat Component
 * Displays task list, clicking add task will open a dialog
 */

// Receive parameters passed from parent component
const props = defineProps({
	roleId: {
		type: String,
		required: true,
	},
	loading: {
		type: Boolean,
		default: false,
	},
});

// Notify parent component to refresh data
const emit = defineEmits(["refresh"]);

// Task list data
const taskListLoading = ref(false);
const taskList = ref<any[]>([]);
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);

// Add task dialog
const dialogVisible = ref(false);
const dialogLoading = ref(false);

// Chat session ID
const sessionId = ref("");

// Current session status
const currentScore = ref(0); // Current task score
const currentRound = ref(0); // Current dialogue rounds
const taskStatus = ref<"ongoing" | "success" | "failure">("ongoing"); // Task status
const scoreTips = ref<{ change: number; reason: string }[]>([]); // Score change history and reasons

// Form data
const formLoading = ref(false);
const form = ref({
	name: "",
	level: 1,
	description: "",
	goal: "",
	type: 1,
	context: "",
	instruction: "",
	constraints: "",
	roleId: "",
	taskType: "system_task", // Task type field
	maxRounds: 5,
	targetScore: 100,
	scoreRange: "-10~+10",
	taskPersonality: "", // Task character setting field
	hideDesigns: "", // Hidden settings field
	userLevelRequired: 1, // User level requirement
	task_goal_judge: "",
	prologues: "", // Opening lines field, comma separated
	task_cover: "", // Task cover image field
});

// System message
const systemMessage = ref("");

// Form validation rules
const rules = ref<Record<string, FormItemRule[]>>({
	name: [
		{ required: true, message: "Please enter task title", trigger: "blur" },
		{ min: 2, max: 50, message: "Length should be 2 to 50 characters", trigger: "blur" },
	],
	description: [
		{ required: true, message: "Please enter task description", trigger: "blur" },
		{ min: 5, max: 1000, message: "Length should be 5 to 1000 characters", trigger: "blur" },
	],
	goal: [
		{ required: true, message: "Please enter task goal", trigger: "blur" },
		{ min: 5, max: 200, message: "Length should be 5 to 200 characters", trigger: "blur" },
	],
	taskPersonality: [
		{ required: true, message: "Please enter task character setting", trigger: "blur" },
		{ min: 3, max: 1000, message: "Length should be 3 to 1000 characters", trigger: "blur" },
	],
	prologues: [
		{ required: true, message: "Please add at least one opening line", trigger: "blur" },
		{ min: 3, max: 1000, message: "Length should be 3 to 1000 characters", trigger: "blur" },
	],
	maxRounds: [{ required: true, message: "Please enter maximum dialogue rounds", trigger: "blur" }],
	targetScore: [{ required: true, message: "Please enter target score", trigger: "blur" }],
	scoreRange: [{ required: true, message: "Please enter score adjustment range", trigger: "blur" }],
	level: [{ required: true, message: "Please select task difficulty", trigger: "change" }],
	userLevelRequired: [{ required: true, message: "Please set user level requirement", trigger: "change" }],
});

// Chat preview data
const previewLoading = ref(false);
const chatMessages = ref<any[]>([]);
const userMessage = ref("");
const chatActive = ref(false);
const formChanged = ref(false);

// Form reference
const formRef = ref();

// Current session ID
const currentSessionId = ref("");

// Hidden settings list for UI display
const hideDesignsList = ref<string[]>([]);
// New hidden setting input
const newHideDesign = ref("");
function confirmDeleteTask(data:any) {
  console.log("confirmDeleteTask", data);
}

// Opening lines list for UI display
const prologuesList = ref<string[]>([]);
// New opening line input
const newPrologue = ref("");

// Task type options
const taskTypeOptions = [
	{ label: "Standard Task", value: "system_task" },
	{ label: "Game Task", value: "system_game" },
	{ label: "Infinite Flow Task", value: "system_infinite_flow" },
];

// Add edit mode flag and current editing task ID
const isEditMode = ref(false);
const currentTaskId = ref("");

/**
 * Get task list
 */
const fetchTaskList = async () => {
	taskListLoading.value = true;
	try {
		// Call actual API to get task list
		const data = await getTaskList(props.roleId, {
			page: currentPage.value,
			size: 100,
		});

		taskList.value = data.items || [];
		total.value = data?.total || 0;
	} catch (error) {
		console.error("Failed to get task list", error);
		ElMessage.error("Failed to get task list");
	} finally {
		taskListLoading.value = false;
	}
};

/**
 * Handle score change
 */
const handleScoreChange = (data: { scoreChange: number; reason: string; isAchieved: boolean }) => {
	// Update score
	if (isNaN(data.scoreChange)) {
		data.scoreChange = 0;
	}
	currentScore.value += data.scoreChange;

	// Add score change record
	scoreTips.value.push({
		change: data.scoreChange,
		reason: data.reason,
	});

	// Update rounds
	currentRound.value += 1;

	// Check if task is completed or failed
	if (data.isAchieved) {
		taskStatus.value = "success";
		ElMessage.success("Congratulations! You've completed the task goal!");
	} else if (currentRound.value >= form.value.maxRounds) {
		// Maximum rounds reached, check score
		if (currentScore.value >= form.value.targetScore) {
			taskStatus.value = "success";
			ElMessage.success("Congratulations! You've completed the task goal!");
		} else {
			taskStatus.value = "failure";
			ElMessage.error("Unfortunately, you didn't achieve the task goal.");
		}
	}
};

/**
 * Reset task status
 */
const resetTaskStatus = () => {
	currentScore.value = 0;
	currentRound.value = 0;
	taskStatus.value = "ongoing";
	scoreTips.value = [];
};

/**
 * Open add task dialog
 */
const openAddDialog = () => {
	dialogVisible.value = true;
	resetForm();
	resetTaskStatus();
	chatActive.value = false;
	updateSystemMessage();
	// Reset to add mode
	isEditMode.value = false;
	currentTaskId.value = "";
	// Generate new session ID
	sessionId.value = `task_session_${Date.now()}`;
};

/**
 * Submit form, generate preview
 */
const submitForm = async () => {
	if (!formRef.value) return;

	await formRef.value.validate(async (valid: boolean) => {
		if (valid) {
			await generateChatPreview();
			chatActive.value = true;
			formChanged.value = false;
		} else {
			ElMessage.warning("Please complete the form information");
			return false;
		}
	});
};

/**
 * Reset form
 */
const resetForm = () => {
	if (!formRef.value) return;
	formRef.value.resetFields();
	chatMessages.value = [];
	chatActive.value = false;
	formChanged.value = false;
	resetTaskStatus();
	updateSystemMessage();

	// Clear hidden settings list
	hideDesignsList.value = [];
	newHideDesign.value = "";

	// Clear opening lines list
	prologuesList.value = [];
	newPrologue.value = "";
};

/**
 * Update system message
 */
const updateSystemMessage = () => {
	// Build system message
	let message = "Now you will play a role, and I will give you a task. Please follow the task requirements I give you.\n\n";

	// Add task information
	message += `Task name: ${form.value.name}\n`;
	message += `Task level: ${getTaskLevelText(form.value.level)}（${getTaskLevelDescription(form.value.level)}）\n`;
	message += `Task type: ${taskTypeOptions.find((item) => item.value === form.value.taskType)?.label || "Standard Task"}\n`;
	message += `Task description: ${form.value.description}\n`;
	message += `Task goal: ${form.value.goal}\n\n`;

	// Add additional information
	if (form.value.context) {
		message += `Background information: ${form.value.context}\n\n`;
	}

	if (form.value.instruction) {
		message += `Task instructions: ${form.value.instruction}\n\n`;
	}

	if (form.value.constraints) {
		message += `Task constraints: ${form.value.constraints}\n\n`;
	}

	// Update
	systemMessage.value = message;
};

/**
 * Get task type display text
 */
const getTaskTypeLabel = (type: string) => {
	const option = taskTypeOptions.find((opt) => opt.value === type);
	return option ? option.label : "Standard Task";
};

// Modify chatTask call method to avoid type errors
const callChatTaskAPI = (params: any) => {
	// Allow passing any parameters when calling API
	return chatTask(params);
};

/**
 * Function to ensure messages scroll to bottom
 */
const scrollToBottom = () => {
	nextTick(() => {
		const messagesContainer = document.querySelector(".chat-messages");
		if (messagesContainer) {
			messagesContainer.scrollTop = messagesContainer.scrollHeight;
		}
	});
};

/**
 * Generate chat preview
 */
const generateChatPreview = async () => {
	// Create a new session ID
	currentSessionId.value = Date.now().toString();

	// If there are opening lines, randomly select one
	if (prologuesList.value.length > 0) {
		const randomIndex = Math.floor(Math.random() * prologuesList.value.length);
		chatMessages.value.push({
			id: Date.now(),
			role: "assistant",
			content: prologuesList.value[randomIndex],
			timestamp: new Date().toLocaleTimeString(),
			scoreChange: 0,
			scoreReason: "",
		});
	} else {
		chatMessages.value.push({
			id: Date.now(),
			role: "assistant",
			content: "I'm so sad, I can't produce gold coins anymore, can you help me (hanging head)?",
			timestamp: new Date().toLocaleTimeString(),
			scoreChange: 0,
			scoreReason: "",
		});
	}

	setTimeout(() => {
		formChanged.value = false;
	}, 100);
	return;

	previewLoading.value = true;
	updateSystemMessage(); // Update system message
	resetTaskStatus(); // Reset task status

	// Create a new session ID
	const sessionId = Date.now().toString();
	currentSessionId.value = sessionId;

	try {
		// Use chatTask API to send initial message
		const { data } = await callChatTaskAPI({
			message: "How can I help you",
			role_id: props.roleId,
			level: "1", // Default value, can be adjusted according to actual situation
			user_level: form.value.userLevelRequired.toString(),
			session_id: sessionId,
			taskDescription: form.value.description,
			taskGoal: form.value.goal,
			scoreRange: form.value.scoreRange,
			maxRounds: form.value.maxRounds,
			targetScore: form.value.targetScore,
			taskLevel: form.value.level,
			taskPersonality: form.value.taskPersonality,
			hideDesigns: form.value.hideDesigns, // Add hidden settings field
			taskType: form.value.taskType, // Add task type field
			task_goal_judge: form.value.task_goal_judge || "", // Add task goal judge field
		});

		// Handle API response
		if (data && data.message) {
			const assistantMessage = {
				id: Date.now() + 1,
				role: "assistant",
				content: data.message,
				timestamp: new Date().toLocaleTimeString(),
				scoreChange: 0, // Default no score change
				scoreReason: data.score_reason, // Add score change reason
			};

			// Handle tool call results
			if (data.tool_results && data.tool_results.length > 0) {
				for (const toolResult of data.tool_results) {
					if (toolResult.content) {
						try {
							const resultData = JSON.parse(toolResult.content);
							if (resultData.name === "score_change") {
								// Update message score change
								assistantMessage.scoreChange = resultData.scoreChange;
								assistantMessage.scoreReason = resultData.reason;
								// Handle score change
								handleScoreChange({
									scoreChange: parseInt(resultData.scoreChange),
									reason: resultData.reason,
									isAchieved: resultData.isAchieved,
								});
							}
						} catch (e) {
							console.error("Failed to parse tool result", e);
						}
					}
				}
			}

			// Add message to chat history
			chatMessages.value.push(assistantMessage);
		} else {
			// If API response has no content, use backup response
			chatMessages.value.push({
				id: Date.now() + 1,
				role: "assistant",
				content: mockGreeting(),
				timestamp: new Date().toLocaleTimeString(),
				scoreChange: 0,
				scoreReason: "",
			});
		}
	} catch (error) {
		console.error("Failed to generate chat preview", error);
		// If API call fails, use backup response
		chatMessages.value.push({
			id: Date.now() + 1,
			role: "assistant",
			content: mockGreeting(),
			timestamp: new Date().toLocaleTimeString(),
			scoreChange: 0,
			scoreReason: "",
		});
	} finally {
		previewLoading.value = false;
		chatActive.value = true;
		formChanged.value = false;

		// Scroll to bottom
		scrollToBottom();
	}
};

/**
 * 发送用户消息
 */
const sendUserMessage = async () => {
	if (!userMessage.value.trim()) return;

	// 添加用户消息到聊天记录
	const message = userMessage.value;
	chatMessages.value.push({
		id: Date.now(),
		role: "user",
		content: message,
		timestamp: new Date().toLocaleTimeString(),
	});

	// 清空输入框
	userMessage.value = "";

	// 设置加载状态
	previewLoading.value = true;

	// 滚动到底部
	scrollToBottom();

	try {
		// 使用chatTask API发送用户消息
		const { data } = await callChatTaskAPI({
			message: message,
			role_id: props.roleId,
			level: "1", // 默认值，可以根据实际情况调整
			user_level: form.value.userLevelRequired.toString(),
			session_id: currentSessionId.value,
			taskDescription: form.value.description,
			taskGoal: form.value.goal,
			scoreRange: form.value.scoreRange,
			maxRounds: form.value.maxRounds,
			targetScore: form.value.targetScore,
			taskLevel: form.value.level,
			taskPersonality: form.value.taskPersonality,
			hideDesigns: form.value.hideDesigns, // 添加隐藏设定字段
			taskType: form.value.taskType, // 添加任务类型字段
			task_goal_judge: form.value.task_goal_judge || "",
		});

		// 处理API响应
		if (data && data.message) {
			const assistantMessage = {
				id: Date.now(),
				role: "assistant",
				content: data.message,
				timestamp: new Date().toLocaleTimeString(),
				scoreChange: 0, // 默认无分数变化
				scoreReason: data.score_reason, // 添加分数变化原因
			};

			// 处理工具调用结果
			if (data.tool_results && data.tool_results.length > 0) {
				for (const toolResult of data.tool_results) {
					if (toolResult.content) {
						try {
							const resultData = JSON.parse(toolResult.content);
							if (resultData.name === "score_change") {
								// 更新消息的分数变化
								assistantMessage.scoreChange = resultData.scoreChange;
								assistantMessage.scoreReason = resultData.reason;
								// 处理分数变化
								handleScoreChange({
									scoreChange: parseInt(resultData.scoreChange),
									reason: resultData.reason,
									isAchieved: resultData.isAchieved,
								});
							}
						} catch (e) {
							console.error("解析工具结果失败", e);
						}
					}
				}
			}

			// 添加消息到聊天记录
			chatMessages.value.push(assistantMessage);
		} else {
			// 如果API响应没有内容，使用备用响应
			chatMessages.value.push({
				id: Date.now(),
				role: "assistant",
				content: mockResponse(),
				timestamp: new Date().toLocaleTimeString(),
				scoreChange: 0,
				scoreReason: "",
			});
		}
	} catch (error) {
		console.error("发送消息失败", error);

		// 如果API调用失败，使用备用响应
		chatMessages.value.push({
			id: Date.now(),
			role: "assistant",
			content: mockResponse(),
			timestamp: new Date().toLocaleTimeString(),
			scoreChange: 0,
			scoreReason: "",
		});
	} finally {
		previewLoading.value = false;

		// 滚动到底部
		scrollToBottom();
	}
};

/**
 * 查看任务对话
 */
const viewTaskDialog = (task: any) => {
	resetForm();
	dialogVisible.value = true;
	// 设置为编辑模式
	isEditMode.value = true;
	currentTaskId.value = task.id;

	// 填充表单数据
	form.value = {
		name: task.title || "",
		type: 1,
		context: "",
		instruction: "",
		constraints: "",
		roleId: task.role_id || props.roleId,
		description: task.description,
		goal: task.task_goal,
		maxRounds: task.max_rounds,
		targetScore: task.target_score,
		scoreRange: task.score_range,
		level: task.task_level,
		taskPersonality: task.task_personality || "",
		hideDesigns: task.hide_designs || "",
		taskType: task.task_type || "system_task",
		userLevelRequired: task.user_level_required || 1,
		task_goal_judge: task.task_goal_judge || "",
		prologues: task.prologues || "",
		task_cover: task.task_cover || "", // 任务封面字段
	};

	// 更新隐藏设定列表
	updateHideDesignsList();
	// 更新开场白列表
	updateProloguesList();

	// 重置任务状态
	resetTaskStatus();

	// 生成新的会话ID
	sessionId.value = `task_session_${Date.now()}`;

	// 生成预览
	generateChatPreview();
	chatActive.value = true;
	formChanged.value = false;
};

/**
 * 获取任务等级对应的文本
 */
const getTaskLevelText = (level: number) => {
	const levelTexts = ["", "入门", "初级", "中级", "高级", "专家"];
	return levelTexts[level] || `${level}级`;
};

/**
 * 获取任务等级对应的描述
 */
const getTaskLevelDescription = (level: number) => {
	const levelDescriptions = [
		"",
		"适合完全没有经验的新手",
		"需要基础知识和少量经验",
		"需要一定的专业知识和经验",
		"需要专业技能和丰富经验",
		"需要精通相关领域和创新能力",
	];
	return levelDescriptions[level] || "需要相应等级的知识与技能";
};

/**
 * 监听页码变化
 */
watch(currentPage, () => {
	fetchTaskList();
});

/**
 * 监听表单变化，实时更新聊天预览
 */
watch(
	() => form.value.description,
	(newVal, oldVal) => {
		if (newVal !== oldVal) {
			formChanged.value = true;
			updateSystemMessage();
		}
	},
	{ deep: true },
);

watch(
	() => form.value.goal,
	(newVal, oldVal) => {
		if (newVal !== oldVal) {
			formChanged.value = true;
			updateSystemMessage();
		}
	},
	{ deep: true },
);

watch(
	() => form.value.maxRounds,
	(newVal, oldVal) => {
		if (newVal !== oldVal) {
			formChanged.value = true;
			updateSystemMessage();
		}
	},
	{ deep: true },
);

watch(
	() => form.value.targetScore,
	(newVal, oldVal) => {
		if (newVal !== oldVal) {
			formChanged.value = true;
			updateSystemMessage();
		}
	},
	{ deep: true },
);

watch(
	() => form.value.scoreRange,
	(newVal, oldVal) => {
		if (newVal !== oldVal) {
			formChanged.value = true;
			updateSystemMessage();
		}
	},
	{ deep: true },
);

watch(
	() => form.value.level,
	(newVal, oldVal) => {
		if (newVal !== oldVal) {
			formChanged.value = true;
			updateSystemMessage();
		}
	},
	{ deep: true },
);

watch(
	() => form.value.taskPersonality,
	(newVal, oldVal) => {
		if (newVal !== oldVal) {
			formChanged.value = true;
			updateSystemMessage();
		}
	},
	{ deep: true },
);

// 添加watch监听hideDesigns变化
watch(
	() => form.value.hideDesigns,
	(newVal, oldVal) => {
		if (newVal !== oldVal) {
			formChanged.value = true;
			updateSystemMessage();
		}
	},
);

// 添加watch监听prologues变化
watch(
	() => form.value.prologues,
	(newVal, oldVal) => {
		if (newVal !== oldVal) {
			formChanged.value = true;
		}
	},
);

// 添加watch监听taskType变化
watch(
	() => form.value.taskType,
	(newVal, oldVal) => {
		if (newVal !== oldVal) {
			formChanged.value = true;
			updateSystemMessage();
		}
	},
);

/**
 * 组件加载时执行
 */
onMounted(() => {
	fetchTaskList();
});

/**
 * 模拟欢迎语
 */
const mockGreeting = () => {
	const greetings = [
		`你好！我是${form.value.taskPersonality || "任务引导者"}。欢迎开始关于"${
			form.value.description
		}"的任务。你的目标是${form.value.goal}。我们总共有${form.value.maxRounds}轮对话，目标分数是${
			form.value.targetScore
		}分。你有什么问题吗？`,
		`欢迎参与这个任务！我是${form.value.taskPersonality || "任务助手"}。这个任务要求你${
			form.value.description
		}，目标是${form.value.goal}。让我们开始吧！`,
		`你好！很高兴能协助你完成这个任务。作为${form.value.taskPersonality || "任务指导员"}，我将帮助你${
			form.value.description
		}。记住，你的目标是${form.value.goal}。准备好了吗？`,
	];
	return greetings[Math.floor(Math.random() * greetings.length)];
};

/**
 * 模拟回复
 */
const mockResponse = () => {
	const responses = ["现在网络遇到了问题，请稍后再试。"];
	return responses[Math.floor(Math.random() * responses.length)];
};

// 添加隐藏设定
const addHideDesign = () => {
	if (!newHideDesign.value.trim()) return;
	hideDesignsList.value.push(newHideDesign.value.trim());
	newHideDesign.value = "";
	// 更新表单中的隐藏设定字段
	form.value.hideDesigns = hideDesignsList.value.join(",");
};

// 删除隐藏设定
const removeHideDesign = (index: number) => {
	hideDesignsList.value.splice(index, 1);
	// 更新表单中的隐藏设定字段
	form.value.hideDesigns = hideDesignsList.value.join(",");
};

// 更新隐藏设定列表（从字符串解析）
const updateHideDesignsList = () => {
	if (!form.value.hideDesigns) {
		hideDesignsList.value = [];
		return;
	}
	hideDesignsList.value = form.value.hideDesigns.split(",").filter((item) => item.trim() !== "");
};

// 添加开场白
const addPrologue = () => {
	if (!newPrologue.value.trim()) return;
	if (prologuesList.value.length >= 3) {
		ElMessage.warning("最多只能添加3条开场白");
		return;
	}
	prologuesList.value.push(newPrologue.value.trim());
	newPrologue.value = "";
	// 更新表单中的开场白字段
	form.value.prologues = prologuesList.value.join(",");
};

// 删除开场白
const removePrologue = (index: number) => {
	prologuesList.value.splice(index, 1);
	// 更新表单中的开场白字段
	form.value.prologues = prologuesList.value.join(",");
};

// 更新开场白列表（从字符串解析）
const updateProloguesList = () => {
	if (!form.value.prologues) {
		prologuesList.value = [];
		return;
	}
	prologuesList.value = form.value.prologues.split(",").filter((item) => item.trim() !== "");
};

/**
 * 复制文本到剪贴板
 */
const copyToClipboard = (text: string) => {
	navigator.clipboard
		.writeText(text)
		.then(() => {
			ElMessage.success("已复制到剪贴板");
		})
		.catch(() => {
			ElMessage.error("复制失败");
		});
};

/**
 * 保存任务
 */
const saveTask = async () => {
	if (!formRef.value) return;

	await formRef.value.validate(async (valid: boolean) => {
		if (valid) {
			formLoading.value = true;
			try {
				// 转换隐藏设定列表为字符串
				form.value.hideDesigns = hideDesignsList.value.join(",");
				// 转换开场白列表为字符串
				form.value.prologues = prologuesList.value.join(",");

				// 准备保存的数据
				const taskData: any = {
					title: form.value.name,
					description: form.value.description,
					task_goal: form.value.goal,
					max_rounds: form.value.maxRounds,
					target_score: form.value.targetScore,
					score_range: form.value.scoreRange,
					task_level: form.value.level,
					task_personality: form.value.taskPersonality,
					hide_designs: form.value.hideDesigns,
					task_type: form.value.taskType,
					user_level_required: form.value.userLevelRequired,
					role_id: props.roleId,
					update_at: "admin", // 默认更新者
					task_goal_judge: form.value.task_goal_judge || "",
					prologues: form.value.prologues, // 添加开场白字段
					task_cover: form.value.task_cover, // 添加任务封面字段
				};

				// 根据是否是编辑模式决定调用创建还是更新API
				if (isEditMode.value && currentTaskId.value) {
					// 编辑模式 - 调用更新API
					await updateTask(currentTaskId.value, taskData);
					ElMessage.success("任务更新成功");
				} else {
					// 新增模式 - 调用创建API
					taskData.create_at = "admin"; // 只在创建时设置创建者
					await addTask(taskData);
					ElMessage.success("任务创建成功");
				}

				dialogVisible.value = false;
				emit("refresh");
				fetchTaskList();
			} catch (error) {
				console.error("保存任务失败", error);
				ElMessage.error("保存任务失败");
			} finally {
				formLoading.value = false;
			}
		} else {
			ElMessage.warning("请完善表单信息");
			return false;
		}
	});
};

/**
 * 删除任务
 */
const handleDelete = async (id: string) => {
	try {
		await ElMessageBox.confirm("确定要删除这个任务吗？", "提示", {
			confirmButtonText: "确定",
			cancelButtonText: "取消",
			type: "warning",
		});

		// 调用API删除任务
		await deleteTask(id);

		ElMessage.success("删除成功");
		emit("refresh");
		fetchTaskList();
	} catch (error) {
		console.error("删除任务失败", error);
		if (error !== "cancel") {
			ElMessage.error("删除任务失败");
		}
	}
};
</script>

<template>
	<div class="task-list-section">
		<div class="section-toolbar">
			<el-button type="primary" size="small" @click="openAddDialog">
				<el-icon>
					<Plus />
				</el-icon>
				Add Task
			</el-button>
		</div>

		<!-- Task list card view -->
		<div class="task-list-container" v-loading="taskListLoading">
			<el-empty v-if="taskList.length === 0" description="No tasks yet" />
			<div class="task-grid" v-else>
				<el-card v-for="task in taskList" :key="task.id" class="task-card" shadow="hover" @click="viewTaskDialog(task)">
					<div class="task-header">
						<div class="task-title">{{ task.title || "Unnamed Task" }}</div>
						<el-tag type="info">{{ getTaskLevelText(task.task_level) }}</el-tag>
					</div>

					<div class="task-cover" v-if="task.task_cover">
						<el-image :src="task.task_cover" fit="cover" class="task-cover-image">
							<template #error>
								<div class="image-error">
									<el-icon><Picture /></el-icon>
								</div>
							</template>
						</el-image>
					</div>

					<div class="task-description">{{ task.description || "No description" }}</div>
					<div class="task-goal">
						<strong>Goal:</strong> {{ task.task_goal || "No goal defined" }}
					</div>

					<template #footer>
						<div class="task-meta">
							<div class="task-type">
								<el-tag size="small">{{ getTaskTypeLabel(task.task_type) }}</el-tag>
							</div>
							<div class="task-actions">
								<el-button type="danger" link @click.stop="confirmDeleteTask(task.id)">
									<el-icon>
										<Delete />
									</el-icon>
									Delete
								</el-button>
							</div>
						</div>
					</template>
				</el-card>
			</div>

			<!-- Pagination -->
			<div class="pagination-container">
				<el-pagination
					v-model:current-page="currentPage"
					:page-size="pageSize"
					layout="total, prev, pager, next"
					:total="total"
					background
				/>
			</div>
		</div>

		<!-- Add/Edit task drawer -->
		<el-drawer
			v-model="dialogVisible"
			:title="isEditMode ? 'Edit Task' : 'Add Task'"
			direction="rtl"
			size="85%"
			:close-on-click-modal="false"
			class="task-drawer"
		>
			<div v-loading="dialogLoading" class="drawer-content">
				<el-row :gutter="16" class="drawer-row">
					<!-- Left form area -->
					<el-col :span="12" class="form-section">
						<el-form ref="formRef" :model="form" :rules="rules" label-position="top">
							<FormItem label="Task Title" prop="name" tooltipKey="name">
								<el-input v-model="form.name" placeholder="Please enter task title"></el-input>
							</FormItem>

							<FormItem label="Upload Task Cover" tooltipKey="task_cover">
								<FileUploader v-model="form.task_cover" accept="image/*" folder="images" :max-size="10" />
							</FormItem>

							<FormItem label="Task Description" prop="description" tooltipKey="description">
								<el-input v-model="form.description" type="textarea" :rows="3" placeholder="Please enter task description"></el-input>
							</FormItem>

							<FormItem label="Task Character Setting" prop="taskPersonality" tooltipKey="taskPersonality">
								<el-input
									v-model="form.taskPersonality"
									type="textarea"
									:rows="3"
									placeholder="Please enter task character setting"
								></el-input>
							</FormItem>

							<FormItem label="Task Goal" prop="goal" tooltipKey="goal">
								<el-input v-model="form.goal" placeholder="Please enter task goal"></el-input>
							</FormItem>
							<FormItem label="Judgment Criteria (not shown to users)" tooltipKey="task_goal_judge">
								<el-input v-model="form.task_goal_judge" placeholder="Define what level of user achievement constitutes success or failure"></el-input>
							</FormItem>
							<FormItem label="Hidden Settings (not shown to users)" prop="hideDesigns" tooltipKey="hideDesigns">
								<div class="hide-designs-container" style="width: 100%">
									<div class="hide-designs-input">
										<el-input v-model="newHideDesign" placeholder="Enter hidden setting content" @keyup.enter="addHideDesign">
											<template #append>
												<el-button @click="addHideDesign">Add</el-button>
											</template>
										</el-input>
									</div>
									<div class="hide-designs-tags" v-if="hideDesignsList.length > 0">
										<el-tooltip v-for="(item, index) in hideDesignsList" :key="index" :content="item" placement="top">
											<el-tag
												closable
												@close="removeHideDesign(index)"
												class="hide-design-tag"
												@click="copyToClipboard(item)"
											>
												{{ item.length > 20 ? item.substring(0, 20) + "..." : item }}
											</el-tag>
										</el-tooltip>
									</div>
									<div class="hide-designs-empty" v-else>
										<el-empty description="No hidden settings yet" :image-size="60"></el-empty>
									</div>
								</div>
							</FormItem>

							<FormItem label="Opening Lines (max 3)" prop="prologues" tooltipKey="prologues">
								<div class="prologues-container" style="width: 100%">
									<div class="prologues-input">
										<el-input v-model="newPrologue" placeholder="Enter opening line content" @keyup.enter="addPrologue">
											<template #append>
												<el-button @click="addPrologue">Add</el-button>
											</template>
										</el-input>
									</div>
									<div class="prologues-count" v-if="prologuesList.length > 0">
										Added {{ prologuesList.length }}/3 opening lines
									</div>
									<div class="prologues-tags" v-if="prologuesList.length > 0">
										<el-tooltip v-for="(item, index) in prologuesList" :key="index" :content="item" placement="top">
											<el-tag
												closable
												@close="removePrologue(index)"
												class="prologue-tag"
												@click="copyToClipboard(item)"
											>
												{{ item.length > 20 ? item.substring(0, 20) + "..." : item }}
											</el-tag>
										</el-tooltip>
									</div>
									<div class="prologues-empty" v-else>
										<el-empty description="No opening lines yet" :image-size="60"></el-empty>
									</div>
								</div>
							</FormItem>

							<!-- Numerical attributes in same row -->
							<el-row :gutter="10">
								<el-col :span="8">
									<FormItem label="Max Dialogue Rounds" prop="maxRounds" tooltipKey="maxRounds">
										<el-input-number
											v-model="form.maxRounds"
											:min="1"
											:max="50"
											:step="1"
											style="width: 100%"
										></el-input-number>
									</FormItem>
								</el-col>
								<el-col :span="8">
									<FormItem label="Target Score" prop="targetScore" tooltipKey="targetScore">
										<el-input-number
											v-model="form.targetScore"
											:min="1"
											:step="10"
											style="width: 100%"
										></el-input-number>
									</FormItem>
								</el-col>
								<el-col :span="8">
									<FormItem label="Score Adjustment Range" prop="scoreRange" tooltipKey="scoreRange">
										<el-input v-model="form.scoreRange" placeholder="E.g.: -10~+10"></el-input>
									</FormItem>
								</el-col>
							</el-row>

							<!-- Task type, difficulty and level requirements in same row -->
							<el-row :gutter="10">
								<el-col :span="8">
									<FormItem label="Task Type" prop="taskType" tooltipKey="taskType">
										<el-select v-model="form.taskType" placeholder="Please select task type" style="width: 100%">
											<el-option
												v-for="item in taskTypeOptions"
												:key="item.value"
												:label="item.label"
												:value="item.value"
											>
												<div class="task-type-option">
													<span class="task-type-label">{{ item.label }}</span>
												</div>
											</el-option>
										</el-select>
									</FormItem>
								</el-col>
								<el-col :span="8">
									<FormItem label="Task Difficulty" prop="level" tooltipKey="level">
										<el-rate v-model="form.level" :max="5" show-score show-text score-template="{value} Level"></el-rate>
									</FormItem>
								</el-col>
								<el-col :span="8">
									<FormItem label="User Level Requirement" prop="userLevelRequired" tooltipKey="userLevelRequired">
										<el-input-number
											v-model="form.userLevelRequired"
											:min="1"
											:max="10"
											:step="1"
											style="width: 100%"
										></el-input-number>
									</FormItem>
								</el-col>
							</el-row>

							<el-form-item>
								<el-button @click="resetForm">Reset</el-button>
							</el-form-item>
						</el-form>
					</el-col>

					<!-- Right chat preview area -->
					<el-col :span="12" class="preview-section">
						<div class="chat-preview-container">
							<h4 class="preview-title">Chat Preview</h4>

							<!-- Task floating card -->
							<div class="task-floating-card" v-if="form.description || form.goal">
								<div class="task-floating-header">
									<h5 class="task-floating-title">
										{{
											form.description
												? form.description.slice(0, 30) + (form.description.length > 30 ? "..." : "")
												: "New Task"
										}}
										<el-tag size="small" type="success" class="task-floating-level">{{
											getTaskLevelText(form.level)
										}}</el-tag>
										<el-tag size="small" type="info" class="task-type-tag">{{
											getTaskTypeLabel(form.taskType)
										}}</el-tag>
									</h5>
									<div class="task-floating-info">
										<el-tooltip content="Maximum dialogue rounds">
											<div class="task-info-item">
												<el-icon><Timer /></el-icon> {{ currentRound }}/{{ form.maxRounds }} rounds
											</div>
										</el-tooltip>
										<el-tooltip content="Target score">
											<div class="task-info-item" :class="{ 'score-success': currentScore >= form.targetScore }">
												<el-icon><Trophy /></el-icon> {{ currentScore }}/{{ form.targetScore }} points
											</div>
										</el-tooltip>
										<el-tooltip content="Score adjustment range per round">
											<div class="task-info-item">
												<el-icon><Document /></el-icon> {{ form.scoreRange }}
											</div>
										</el-tooltip>
										<div class="task-status-badge" v-if="taskStatus !== 'ongoing'">
											<el-tag type="success" v-if="taskStatus === 'success'">Task Successful</el-tag>
											<el-tag type="danger" v-else>Task Failed</el-tag>
										</div>
									</div>
								</div>
								<div class="task-floating-goal" v-if="form.goal">
									Goal: {{ form.goal.slice(0, 40) + (form.goal.length > 40 ? "..." : "") }}
								</div>
								<div class="task-floating-personality" v-if="form.taskPersonality">
									Character: {{ form.taskPersonality }}
								</div>
							</div>

							<div class="chat-messages" v-loading="previewLoading">
								<div v-if="chatMessages.length === 0" class="empty-chat">
									<el-empty description="Click Generate Preview to see chat effect"></el-empty>
								</div>

								<div v-else class="messages-container">
									<div v-for="message in chatMessages" :key="message.id" :class="['message-bubble', message.role]">
										<div v-if="message.role === 'system'" class="system-message">
											<div class="system-message-content">{{ message.content }}</div>
											<div class="message-time">{{ message.timestamp }}</div>
										</div>
										<div v-else-if="message.role === 'user'" class="user-message">
											<div class="user-message-content">{{ message.content }}</div>
											<div class="message-time">{{ message.timestamp }}</div>
										</div>
										<div v-else-if="message.role === 'assistant'" class="assistant-message">
											<div class="assistant-message-content">{{ message.content }}</div>
											<div class="message-time">{{ message.timestamp }}</div>
											<div class="score-badge" v-if="message.scoreChange && message.role === 'assistant'">
												<el-tooltip :content="message.scoreReason || 'Score change'" placement="top">
													<span :class="{ positive: message.scoreChange > 0, negative: message.scoreChange < 0 }">
														{{ message.scoreChange > 0 ? "+" + message.scoreChange : message.scoreChange }} pts
													</span>
												</el-tooltip>
											</div>
										</div>
									</div>
								</div>
							</div>

							<!-- Chat input area -->
							<div class="chat-input-container" v-if="chatActive && taskStatus === 'ongoing'">
								<el-input
									v-model="userMessage"
									:placeholder="formChanged ? 'Please generate preview first' : 'Enter your message...'"
									:disabled="formChanged || previewLoading"
									@keyup.enter="sendUserMessage"
								>
									<template #append>
										<el-button @click="sendUserMessage" :disabled="formChanged || previewLoading">Send</el-button>
									</template>
								</el-input>
							</div>

							<!-- Actions area -->
							<div class="actions-container">
								<el-button
									type="primary"
									@click="submitForm"
									:loading="previewLoading"
									:disabled="formChanged === false && chatActive"
								>
									{{ chatActive ? "Regenerate Preview" : "Generate Preview" }}
								</el-button>
								<el-button
									type="success"
									@click="saveTask"
									:loading="formLoading"
									:disabled="formChanged || !chatActive"
								>
									{{ isEditMode ? "Update Task" : "Save Task" }}
								</el-button>
							</div>

							<!-- Score tips -->
							<div class="score-tips" v-if="scoreTips.length > 0">
								<h5 class="score-tips-title">Score Changes:</h5>
								<ul class="score-tips-list">
									<li v-for="(tip, index) in scoreTips" :key="index" class="score-tip-item">
										<span :class="{ positive: tip.change > 0, negative: tip.change < 0 }">
											{{ tip.change > 0 ? "+" + tip.change : tip.change }}
										</span>
										<span class="score-reason">{{ tip.reason }}</span>
									</li>
								</ul>
							</div>
						</div>
					</el-col>
				</el-row>
			</div>
		</el-drawer>
	</div>
</template>

<style scoped>
.task-list-section {
	padding: 0;
}

.section-toolbar {
	display: flex;
	justify-content: flex-end;
	align-items: center;
	margin-bottom: 20px;
	padding: 0 4px;
}

/* Task card styles */
.task-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
	gap: 20px;
	margin-bottom: 20px;
}

.task-card {
	margin-bottom: 16px;
	position: relative;
}

.task-header {
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
	margin-bottom: 15px;
}

.task-level {
	font-size: 12px;
	color: #e4bb5c;
	display: inline;
	margin-left: 5px;
}

.task-title {
	font-size: 16px;
	font-weight: bold;
	margin: 0 0 10px 0;
	color: var(--el-text-color-primary);
}

.task-cover {
	margin-bottom: 10px;
}

.task-cover-image {
	width: 100%;
	height: 200px;
	object-fit: cover;
	border-radius: 4px;
}

.task-description {
	margin-bottom: 10px;
	color: var(--el-text-color-regular);
	height: 100px;
	overflow: hidden;
}

.task-goal {
	border-radius: 4px;
	padding: 8px;
	margin-bottom: 10px;
	font-size: 14px;
	color: rgba(96, 98, 102, 0.8);
	height: 50px;
	overflow: hidden;
}

.task-meta {
	display: flex;
	flex-wrap: wrap;
	font-size: 14px;
	color: #7f8c8d;
	justify-content: space-between;
}

.task-time {
	display: flex;
	align-items: center;
	gap: 5px;
	font-size: 14px;
	color: #7f8c8d;
}

.task-actions {
	display: flex;
	gap: 10px;
}

.pagination-container {
	margin-top: 20px;
	display: flex;
	justify-content: center;
}

/* Drawer styles */
.task-drawer {
	--el-drawer-padding-primary: 20px;
}

.task-drawer :deep(.el-drawer__header) {
	background: linear-gradient(135deg, #2563eb, #1e40af);
	color: white;
	margin-bottom: 0;
	padding: 20px;
	border-bottom: 3px solid #1d4ed8;
}

.task-drawer :deep(.el-drawer__title) {
	color: white;
	font-weight: 600;
	font-size: 18px;
}

.task-drawer :deep(.el-drawer__close-btn) {
	color: white;
	font-size: 18px;
}

.task-drawer :deep(.el-drawer__close-btn):hover {
	color: #cbd5e1;
}

.task-drawer :deep(.el-drawer__body) {
	padding: 0;
	background: #f8fafc;
	overflow: hidden;
	height: 100%;
}

.drawer-footer {
	display: flex;
	justify-content: flex-end;
	gap: 12px;
	padding: 16px 20px;
	border-top: 1px solid #e2e8f0;
	background: white;
	margin: 0 -20px -20px -20px;
}

.drawer-content {
	height: 100%;
	padding: 20px;
	overflow: hidden;
	display: flex;
	flex-direction: column;
}

.drawer-row {
	flex: 1;
	margin: 0 !important;
	height: calc(100vh - 200px);
	overflow: hidden;
}

.form-section {
	height: 100%;
	overflow-y: auto;
	background: white;
	border-radius: 8px;
	padding: 20px;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.preview-section {
	height: 100%;
}

/* Chat preview container styles */
.chat-preview-container {
	height: 100%;
	border: 1px solid #e6e6e6;
	border-radius: 8px;
	display: flex;
	flex-direction: column;
	position: relative;
	min-height: 600px; /* Ensure minimum height */
	background: white;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.preview-title {
	padding: 10px;
	margin: 0;
	border-bottom: 1px solid #e6e6e6;
	background-color: #f5f7fa;
}

/* Floating task card styles */
.task-floating-card {
	background-color: #fff;
	border-bottom: 1px solid #e6e6e6;
	padding: 10px;
	margin-bottom: 0;
	box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
	position: sticky;
	top: 0;
	z-index: 10;
}

.task-floating-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 5px;
}

.task-floating-title {
	margin: 0;
	font-size: 14px;
	font-weight: bold;
	color: var(--el-text-color-primary);
	display: flex;
	align-items: center;
	gap: 8px;
}

.task-floating-level {
	font-weight: normal;
}

.task-floating-info {
	display: flex;
	gap: 15px;
}

.task-info-item {
	display: flex;
	align-items: center;
	gap: 4px;
	font-size: 12px;
	color: var(--el-text-color-secondary);
}

.task-floating-goal,
.task-floating-personality {
	font-size: 13px;
	color: var(--el-text-color-secondary);
	line-height: 1.4;
	border-top: 1px dashed #eee;
	margin-top: 5px;
	padding: 5px 0;
}

.chat-messages {
	flex: 1;
	padding: 10px;
	overflow-y: auto;
	background-color: #f9f9f9;
	height: 400px; /* Increase height to fit drawer */
	max-height: 400px; /* Maximum height */
	position: relative;
}

.chat-input-container {
	padding: 10px;
	border-top: 1px solid #e6e6e6;
	background-color: #fff;
}

.empty-chat {
	height: 100%;
	display: flex;
	justify-content: center;
	align-items: center;
}

.messages-container {
	display: flex;
	flex-direction: column;
	gap: 10px;
}

.message-bubble {
	max-width: 80%;
	padding: 10px;
	border-radius: 12px;
	margin: 5px 0;
}

.message-bubble.system {
	width: 100%;
	max-width: 100%;
	background-color: #f2f6fc;
}

.message-bubble.user {
	align-self: flex-end;
	background-color: #ecf5ff;
	border: 1px solid #d9ecff;
}

.message-bubble.assistant {
	position: relative;
	align-self: flex-start;
	background-color: #fff;
	border: 1px solid #ebeef5;
}

.system-message {
	text-align: center;
}

.system-message-content {
	white-space: pre-wrap;
	font-size: 13px;
	color: #606266;
}

.user-message-content,
.assistant-message-content {
	white-space: pre-wrap;
	word-break: break-word;
}

.message-time {
	font-size: 12px;
	color: #909399;
	margin-top: 5px;
	text-align: right;
}

/* Chat preview mask styles */
.preview-mask {
	position: absolute;
	top: 44px; /* Start from title below */
	left: 0;
	right: 0;
	bottom: 0;
	background-color: rgba(0, 0, 0, 0.5);
	display: flex;
	justify-content: center;
	align-items: center;
	z-index: 100;
	backdrop-filter: blur(2px);
}

.preview-mask-content {
	background-color: white;
	padding: 24px;
	border-radius: 8px;
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
	text-align: center;
	max-width: 90%;
}

.mask-hint {
	margin-top: 12px;
	color: var(--el-text-color-secondary);
	font-size: 14px;
}

.mask-warning {
	font-size: 18px;
	font-weight: bold;
	color: #e6a23c;
	margin-bottom: 16px;
}

.mask-buttons {
	display: flex;
	flex-direction: column;
	gap: 10px;
}

.mask-task-summary {
	margin-top: 16px;
	text-align: left;
	border-top: 1px dashed #eee;
	padding-top: 12px;
}

.summary-item {
	margin-bottom: 6px;
	color: var(--el-text-color-secondary);
}

.summary-item span {
	font-weight: bold;
	color: var(--el-text-color-primary);
}

/* Score and status styles */
.score-success {
	color: #67c23a;
	font-weight: bold;
}

.task-status-badge {
	margin-left: 10px;
}

.score-tips {
	border-top: 1px dashed #eee;
	margin-top: 5px;
	padding: 5px 0;
	display: flex;
	flex-wrap: wrap;
	gap: 8px;
}

.score-tip-item {
	cursor: pointer;
}

.score-change {
	display: inline-flex;
	align-items: center;
	gap: 2px;
	padding: 2px 6px;
	border-radius: 10px;
	font-size: 12px;
	background-color: #f5f7fa;
}

.score-positive {
	color: #67c23a;
	background-color: rgba(103, 194, 58, 0.1);
}

.score-negative {
	color: #f56c6c;
	background-color: rgba(245, 108, 108, 0.1);
}

/* Hidden settings styles */
.hide-designs-container {
	display: flex;
	flex-direction: column;
	gap: 10px;
}

.hide-designs-input {
	width: 100%;
}

.hide-designs-tags {
	display: flex;
	flex-wrap: wrap;
	gap: 8px;
	padding: 8px;
	border: 1px solid #ebeef5;
	border-radius: 4px;
	min-height: 80px;
	background-color: #f9f9f9;
}

.hide-design-tag {
	margin-bottom: 4px;
	cursor: pointer;
	max-width: 100%;
	overflow: hidden;
	text-overflow: ellipsis;
}

.hide-designs-empty {
	padding: 10px;
	border: 1px solid #ebeef5;
	border-radius: 4px;
	min-height: 80px;
	display: flex;
	justify-content: center;
	align-items: center;
	background-color: #f9f9f9;
}

/* Opening lines styles */
.prologues-container {
	display: flex;
	flex-direction: column;
	gap: 10px;
}

.prologues-input {
	width: 100%;
}

.prologues-count {
	font-size: 12px;
	color: #909399;
	margin-top: -5px;
	text-align: right;
}

.prologues-tags {
	display: flex;
	flex-wrap: wrap;
	gap: 8px;
	padding: 8px;
	border: 1px solid #ebeef5;
	border-radius: 4px;
	min-height: 80px;
	background-color: #f9f9f9;
}

.prologue-tag {
	margin-bottom: 4px;
	cursor: pointer;
	max-width: 100%;
	overflow: hidden;
	text-overflow: ellipsis;
}

.prologues-empty {
	padding: 10px;
	border: 1px solid #ebeef5;
	border-radius: 4px;
	min-height: 80px;
	display: flex;
	justify-content: center;
	align-items: center;
	background-color: #f9f9f9;
}

/* Task type styles */
.task-type-option {
	display: flex;
	justify-content: space-between;
	align-items: center;
	width: 100%;
}

.task-type-label {
	font-weight: bold;
}

.task-type-desc {
	color: #909399;
	font-size: 12px;
}

.task-type-tag {
	margin-left: 5px;
}

.assistant-message {
	position: relative;
}

.score-badge {
	position: absolute;
	top: -31px;
	right: -8px;
	background-color: #f5f7fa;
	border-radius: 10px;
	padding: 2px 6px;
	font-size: 12px;
	display: inline-flex;
	align-items: center;
	gap: 2px;
	box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.score-badge.positive {
	color: #67c23a;
	background-color: rgba(103, 194, 58, 0.1);
}

.score-badge.negative {
	color: #f56c6c;
	background-color: rgba(245, 108, 108, 0.1);
}

/* Drawer responsive design */
@media (max-width: 1200px) {
	.task-drawer {
		size: 95%;
	}

	.drawer-row .form-section,
	.drawer-row .preview-section {
		padding: 16px;
	}
}

@media (max-width: 768px) {
	.task-drawer {
		size: 100%;
	}

	.drawer-content {
		height: calc(100vh - 120px);
	}

	.drawer-row {
		flex-direction: column;
	}

	.form-section {
		height: auto;
		margin-bottom: 20px;
		padding: 16px;
	}

	.preview-section {
		padding-left: 0;
		height: 500px;
	}

	.chat-messages {
		height: 300px;
		max-height: 300px;
	}
}
</style>
