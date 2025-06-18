<template>
	<div class="chat-main">
		<div class="chat-header">
			<div class="chat-title">
				<span class="ai-name">{{ aiName }}</span>
				<span class="ai-role">{{ aiRole }}</span>
			</div>
			<div class="chat-rounds">对话轮数: {{ maxRounds === -1 ? "无限制" : `${currentRound}/${maxRounds}` }}</div>
		</div>

		<div class="chat-content" ref="chatContentRef">
			<div v-for="message in messages" :key="message.id" :class="['message-item', `message-${message.sender}`]">
				<div class="message-avatar">
					<img v-if="message.imageUrl" :src="message.imageUrl" alt="角色头像" />
					<img v-else-if="message.sender === 'assistant' && aiImage" :src="aiImage" alt="AI" />
					<span v-else>{{ message.senderName.charAt(0) }}</span>
				</div>
				<div class="message-bubble">
					<div class="message-sender">{{ message.senderName }}</div>
					<div class="message-content">{{ message.content }}</div>
					<div class="message-time">{{ formatTimestamp(message.timestamp) }}</div>
				</div>
			</div>

			<div v-if="isAiTyping" class="typing-indicator">
				<div class="typing-dot"></div>
				<div class="typing-dot"></div>
				<div class="typing-dot"></div>
			</div>
		</div>

		<div
			class="chat-input-area"
			:class="{ 'input-disabled': isLoading || isAiTyping || (maxRounds !== -1 && currentRound >= maxRounds) }"
		>
			<div v-if="isAiTyping" class="waiting-overlay">AI正在思考...</div>
			<el-input
				ref="inputRef"
				v-model="userInput"
				type="textarea"
				:rows="3"
				placeholder="输入你的消息..."
				:disabled="isLoading || isAiTyping || (maxRounds !== -1 && currentRound >= maxRounds)"
				@keydown.enter.ctrl="handleSendMessage"
				@keydown.enter.exact.prevent="handleSendMessage"
			/>
			<el-button
				type="primary"
				@click="handleSendMessage"
				:disabled="
					isLoading || isAiTyping || userInput.trim() === '' || (maxRounds !== -1 && currentRound >= maxRounds)
				"
				:loading="isLoading"
			>
				发送
			</el-button>
		</div>
	</div>
</template>

<script setup lang="ts">
/**
 * 聊天主区域组件
 * @description 显示消息列表和输入框
 */
import { ref, defineProps, defineEmits, watch, nextTick, onMounted, onUpdated } from "vue";

// 消息类型定义
interface ChatMessage {
	id: string | number;
	sender: string;
	senderName: string;
	content: string;
	timestamp: number;
	imageUrl?: string; // 添加可选的头像URL字段
}

const chatContentRef = ref(null);
const inputRef = ref(null);

const props = defineProps({
	/** AI名称 */
	aiName: {
		type: String,
		required: true,
	},
	/** AI角色 */
	aiRole: {
		type: String,
		required: true,
	},
	/** 当前回合 */
	currentRound: {
		type: Number,
		required: true,
	},
	/** 最大回合数 */
	maxRounds: {
		type: Number,
		required: true,
	},
	/** 消息列表 */
	messages: {
		type: Array as () => ChatMessage[],
		required: true,
	},
	/** 是否加载中 */
	isLoading: {
		type: Boolean,
		default: false,
	},
	/** AI是否正在输入 */
	isAiTyping: {
		type: Boolean,
		default: false,
	},
	/** 用户输入 */
	modelValue: {
		type: String,
		default: "",
	},
	/** AI头像 */
	aiImage: {
		type: String,
		default: "",
	},
});
// 滚动到底部
const scrollToBottom = async () => {
	if (chatContentRef.value) {
		await nextTick();
		// 确保一定滚动到底部
		const chatContent = chatContentRef.value;
		chatContent.scrollTop = chatContent.scrollHeight;

		// 双重保险：添加延时再次滚动到底部，防止动态内容导致高度计算不准确
		setTimeout(() => {
			chatContent.scrollTop = chatContent.scrollHeight;
		}, 50);
	}
};
// 双向绑定用户输入
const emit = defineEmits(["update:modelValue", "send-message"]);

// 使用计算属性实现双向绑定
const userInput = ref(props.modelValue);

watch(
	() => props.modelValue,
	(val) => {
		userInput.value = val;
	},
);

watch(userInput, (val) => {
	emit("update:modelValue", val);
});

// 处理发送消息
const handleSendMessage = () => {
	// 判断是否满足发送条件：
	// 1. 有内容且不为空白
	// 2. 不在加载状态
	// 3. AI不在输入状态
	// 4. 轮次未达到上限(如果不是无限轮次模式)
	if (
		userInput.value.trim() &&
		!props.isLoading &&
		!props.isAiTyping &&
		(props.maxRounds === -1 || props.currentRound < props.maxRounds)
	) {
		emit("send-message", userInput.value);
	}
};

// 格式化时间戳
const formatTimestamp = (timestamp: number) => {
	const date = new Date(timestamp);
	return `${date.getHours().toString().padStart(2, "0")}:${date.getMinutes().toString().padStart(2, "0")}`;
};

// 监听消息变化，自动滚动到底部
watch(
	() => props.messages.length,
	() => {
		scrollToBottom();
	},
);

// 监听AI输入状态变化
watch(
	() => props.isAiTyping,
	(newValue) => {
		if (!newValue) {
			// AI停止输入，用户可以输入了
			focusInput();
		}
		scrollToBottom();
	},
	{ immediate: true },
);

// 聚焦输入框
const focusInput = async () => {
	if (inputRef.value && !props.isLoading && !props.isAiTyping) {
		await nextTick();
		setTimeout(() => {
			// 获取实际的input元素并聚焦
			const inputEl = inputRef.value?.$el?.querySelector("textarea");
			if (inputEl && !props.isLoading && !props.isAiTyping) {
				inputEl.focus();
			}
		}, 100);
	}
};

// 组件挂载时滚动到底部
onMounted(() => {
	scrollToBottom();
});

// 组件更新时滚动到底部
onUpdated(() => {
	scrollToBottom();
});
</script>

<style lang="scss" scoped>
.chat-main {
	flex: 1;
	display: flex;
	flex-direction: column;
	background-color: rgba(18, 18, 24, 0.5);
	position: relative;
	height: 100%;
	overflow: hidden;

	.chat-header {
		padding: 1rem 1.5rem;
		display: flex;
		justify-content: space-between;
		align-items: center;
		border-bottom: 1px solid rgba(100, 100, 255, 0.2);
		background-color: rgba(26, 26, 46, 0.8);

		.chat-title {
			display: flex;
			flex-direction: column;

			.ai-name {
				font-weight: 600;
				font-size: 1.1rem;
				color: #e0e0e0;
			}

			.ai-role {
				font-size: 0.85rem;
				color: #a0a0a0;
			}
		}

		.chat-rounds {
			font-size: 0.9rem;
			padding: 0.3rem 0.8rem;
			background-color: rgba(77, 166, 255, 0.2);
			border-radius: 4px;
			color: #4da6ff;
		}
	}

	.chat-content {
		padding: 1rem;
		overflow-y: auto;
		overflow-x: hidden;
		scrollbar-width: thin;
		scrollbar-color: rgba(100, 100, 255, 0.3) rgba(0, 0, 0, 0.1);
		display: flex;
		flex-direction: column;
		gap: 1rem;
		height: calc(100vh - 220px);
		min-height: 200px;
		max-height: calc(100vh - 180px);
		box-sizing: border-box;
		position: relative;
		scroll-behavior: smooth;

		&::-webkit-scrollbar {
			width: 6px;
		}

		&::-webkit-scrollbar-track {
			background: rgba(0, 0, 0, 0.1);
		}

		&::-webkit-scrollbar-thumb {
			background-color: rgba(100, 100, 255, 0.3);
			border-radius: 3px;
		}

		.message-item {
			display: flex;
			margin-bottom: 1rem;
			animation: fadeIn 0.3s ease;

			&.message-human {
				flex-direction: row-reverse;

				.message-bubble {
					background-color: rgba(77, 166, 255, 0.2);
					border-radius: 15px 15px 0 15px;
					margin-right: 10px;
				}

				.message-sender {
					text-align: right;
				}

				.message-time {
					text-align: left;
				}
			}

			&.message-assistant {
				.message-bubble {
					background-color: rgba(30, 30, 50, 0.6);
					border-radius: 15px 15px 15px 0;
					margin-left: 10px;
				}
			}

			&.message-setter {
				.message-bubble {
					background-color: rgba(90, 60, 120, 0.6);
					border-radius: 15px 15px 15px 0;
					margin-left: 10px;
					border-left: 3px solid #9370db;
				}

				.message-sender {
					color: #b388ff;
					font-weight: 600;
				}
			}

			&.message-system {
				justify-content: center;

				.message-bubble {
					background-color: rgba(255, 153, 0, 0.1);
					border: 1px dashed rgba(255, 153, 0, 0.3);
					border-radius: 10px;
					padding: 5px 15px;
					max-width: 80%;
				}

				.message-avatar {
					display: none;
				}

				.message-sender {
					color: #ff9900;
				}
			}

			.message-avatar {
				width: 40px;
				height: 40px;
				border-radius: 50%;
				background: linear-gradient(135deg, #4da6ff, #5e72e4);
				color: #fff;
				display: flex;
				align-items: center;
				justify-content: center;
				font-weight: bold;
				flex-shrink: 0;

				img {
					width: 100%;
					height: 100%;
					border-radius: 50%;
					object-fit: cover;
				}
			}

			.message-bubble {
				padding: 10px 15px;
				max-width: 70%;

				.message-sender {
					font-size: 0.85rem;
					margin-bottom: 5px;
					color: #a0a0a0;
				}

				.message-content {
					font-size: 0.95rem;
					color: #e0e0e0;
					line-height: 1.4;
					white-space: pre-wrap;
				}

				.message-time {
					font-size: 0.75rem;
					color: rgba(160, 160, 160, 0.7);
					margin-top: 5px;
					text-align: right;
				}
			}
		}

		.typing-indicator {
			display: flex;
			align-items: center;
			justify-content: center;
			margin: 10px 0;
			padding: 10px;

			.typing-dot {
				width: 8px;
				height: 8px;
				background-color: #4da6ff;
				border-radius: 50%;
				margin: 0 3px;
				animation: blink 1.4s infinite both;

				&:nth-child(2) {
					animation-delay: 0.2s;
				}

				&:nth-child(3) {
					animation-delay: 0.4s;
				}
			}
		}
	}

	.chat-input-area {
		padding: 1rem;
		background-color: rgba(26, 26, 46, 0.8);
		border-top: 1px solid rgba(100, 100, 255, 0.2);
		display: flex;
		gap: 10px;
		position: relative;

		.el-input {
			flex: 1;

			:deep(.el-textarea__inner) {
				background-color: rgba(30, 30, 50, 0.6);
				border: 1px solid rgba(100, 100, 255, 0.2);
				color: #e0e0e0;
				resize: none;
				border-radius: 6px;
				padding: 10px 15px;

				&:focus {
					border-color: #4da6ff;
					box-shadow: 0 0 0 2px rgba(77, 166, 255, 0.2);
				}

				&::placeholder {
					color: rgba(160, 160, 160, 0.6);
				}
			}
		}

		.el-button {
			align-self: flex-end;
			height: 40px;
			min-width: 80px;
		}

		&.input-disabled {
			opacity: 0.8;
		}

		.waiting-overlay {
			position: absolute;
			top: 0;
			left: 0;
			right: 0;
			bottom: 0;
			background-color: rgba(0, 0, 0, 0.4);
			display: flex;
			align-items: center;
			justify-content: center;
			z-index: 10;
			backdrop-filter: blur(2px);
			color: #e0e0e0;
			font-style: italic;
		}
	}
}

@keyframes fadeIn {
	from {
		opacity: 0;
		transform: translateY(5px);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}

@keyframes blink {
	0%,
	100% {
		opacity: 0.5;
		transform: scale(1);
	}
	50% {
		opacity: 1;
		transform: scale(1.2);
	}
}

@media (max-width: 768px) {
	.chat-main {
		.message-item {
			.message-bubble {
				max-width: 85%;
			}
		}
	}
}
</style>
