<template>
	<div class="chat-container">
		<chat-sidebar
			:user-name="userInfo.name"
			:user-role="userInfo.background"
			:current-round="currentRound"
			:max-rounds="maxRounds"
			:soup-surface="soupSurface"
			:usage-state="usageState"
		/>

		<div class="chat-main-container">
			<!-- 角色选择区域 -->
			<div class="character-selector" v-if="characters.length > 0">
				<div
					v-for="character in characters"
					:key="character.role_id"
					:class="['character-avatar', { active: character.role_id === currentRoleId }]"
					@click="handleCharacterSelect(character.role_id)"
				>
					<img :src="character.image_url" :alt="character.role_name" class="avatar-image" />
					<div class="character-info">
						<span class="character-name">{{ character.role_name }}</span>
						<span class="character-level">{{ character.character_level }}</span>
					</div>
				</div>
			</div>

			<chat-main-panel
				:ai-name="aiInfo.name"
				:ai-role="aiInfo.role"
				:ai-image="aiInfo.image"
				:current-round="currentRound"
				:max-rounds="maxRounds"
				:messages="messages"
				:is-loading="isLoading"
				:is-ai-typing="isAiTyping"
				:model-value="userInput"
				@update:model-value="(newValue) => emit('update:userInput', newValue)"
				@send-message="handleSendMessage"
			/>
		</div>
	</div>
</template>

<script setup lang="ts">
/**
 * 聊天容器组件
 * @description 整合聊天侧边栏和主区域
 */
import { defineProps, defineEmits } from "vue";
import ChatSidebar from "./ChatSidebar.vue";
import ChatMainPanel from "./ChatMainPanel.vue";

// 角色类型定义
interface Character {
	role_id: string | number;
	role_name: string;
	image_url: string;
	character_level: string;
	description?: string;
}

// 消息类型定义
interface ChatMessage {
	id: string | number;
	sender: string;
	senderName: string;
	content: string;
	timestamp: number;
	role?: string;
}

// 用户信息类型
interface UserInfo {
	name: string;
	background?: string;
}

// AI信息类型
interface AiInfo {
	name: string;
	role: string;
	background?: string;
	image?: string;
}

defineProps({
	/** 用户信息 */
	userInfo: {
		type: Object as () => UserInfo,
		required: true,
	},
	/** AI信息 */
	aiInfo: {
		type: Object as () => AiInfo,
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
	userInput: {
		type: String,
		default: "",
	},
	/** 角色列表 */
	characters: {
		type: Array as () => Character[],
		default: () => [],
	},
	/** 当前选中的角色ID */
	currentRoleId: {
		type: [String, Number],
		default: "",
	},
	/** 汤面信息 */
	soupSurface: {
		type: String,
		default: "",
	},
	/** 使用统计 */
	usageState: {
		type: Object,
		default: () => ({}),
	},
});

const emit = defineEmits(["update:userInput", "send-message", "select-character"]);

// 处理发送消息
const handleSendMessage = (message: string) => {
	emit("send-message", message);
};

// 处理角色选择
const handleCharacterSelect = (roleId: string | number) => {
	emit("select-character", roleId);
};
</script>

<style lang="scss" scoped>
.chat-container {
	display: flex;
	flex: 1;
	background-color: rgba(18, 18, 24, 0.7);
}

.chat-main-container {
	display: flex;
	flex-direction: column;
	flex: 1;
}

.character-selector {
	display: flex;
	padding: 10px;
	background-color: rgba(16, 16, 24, 0.9);
	border-bottom: 1px solid rgba(100, 100, 255, 0.2);
	overflow-x: auto;
	scrollbar-width: thin;

	&::-webkit-scrollbar {
		height: 4px;
	}

	&::-webkit-scrollbar-track {
		background: rgba(0, 0, 0, 0.2);
	}

	&::-webkit-scrollbar-thumb {
		background-color: rgba(100, 100, 255, 0.3);
		border-radius: 2px;
	}
}

.character-avatar {
	display: flex;
	flex-direction: column;
	align-items: center;
	margin-right: 15px;
	padding: 5px;
	border-radius: 8px;
	cursor: pointer;
	transition: all 0.2s ease;
	min-width: 80px;

	&:hover {
		background-color: rgba(100, 100, 255, 0.1);
	}

	&.active {
		background-color: rgba(100, 100, 255, 0.2);
		box-shadow: 0 0 10px rgba(100, 100, 255, 0.2);
	}

	.avatar-image {
		width: 50px;
		height: 50px;
		border-radius: 50%;
		object-fit: cover;
		border: 2px solid transparent;
		transition: all 0.2s ease;
	}

	&.active .avatar-image {
		border-color: #4da6ff;
	}

	.character-info {
		display: flex;
		flex-direction: column;
		align-items: center;
		margin-top: 5px;

		.character-name {
			font-size: 0.85rem;
			color: #e0e0e0;
			font-weight: 500;
		}

		.character-level {
			font-size: 0.7rem;
			color: #4da6ff;
			margin-top: 2px;
		}
	}
}

@media (max-width: 768px) {
	.chat-container {
		flex-direction: column;
	}

	.character-avatar {
		min-width: 60px;

		.avatar-image {
			width: 40px;
			height: 40px;
		}
	}
}
</style>
