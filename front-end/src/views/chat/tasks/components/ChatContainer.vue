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
			<!-- Character Selection Area -->
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
 * Chat Container Component
 * @description Integrates chat sidebar and main area
 */
import { defineProps, defineEmits } from "vue";
import ChatSidebar from "./ChatSidebar.vue";
import ChatMainPanel from "./ChatMainPanel.vue";

// Character type definition
interface Character {
	role_id: string | number;
	role_name: string;
	image_url: string;
	character_level: string;
	description?: string;
}

// Message type definition
interface ChatMessage {
	id: string | number;
	sender: string;
	senderName: string;
	content: string;
	timestamp: number;
	role?: string;
}

// User info type
interface UserInfo {
	name: string;
	background?: string;
}

// AI info type
interface AiInfo {
	name: string;
	role: string;
	background?: string;
	image?: string;
}

defineProps({
	/** User information */
	userInfo: {
		type: Object as () => UserInfo,
		required: true,
	},
	/** AI information */
	aiInfo: {
		type: Object as () => AiInfo,
		required: true,
	},
	/** Current round */
	currentRound: {
		type: Number,
		required: true,
	},
	/** Maximum rounds */
	maxRounds: {
		type: Number,
		required: true,
	},
	/** Message list */
	messages: {
		type: Array as () => ChatMessage[],
		required: true,
	},
	/** Is loading */
	isLoading: {
		type: Boolean,
		default: false,
	},
	/** Is AI typing */
	isAiTyping: {
		type: Boolean,
		default: false,
	},
	/** User input */
	userInput: {
		type: String,
		default: "",
	},
	/** Character list */
	characters: {
		type: Array as () => Character[],
		default: () => [],
	},
	/** Currently selected character ID */
	currentRoleId: {
		type: [String, Number],
		default: "",
	},
	/** Soup surface information */
	soupSurface: {
		type: String,
		default: "",
	},
	/** Usage statistics */
	usageState: {
		type: Object,
		default: () => ({}),
	},
});

const emit = defineEmits(["update:userInput", "send-message", "select-character"]);

// Handle sending message
const handleSendMessage = (message: string) => {
	emit("send-message", message);
};

// Handle character selection
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
