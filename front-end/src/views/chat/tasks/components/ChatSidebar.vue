<template>
	<div class="chat-sidebar">
		<div class="user-profile">
			<div class="avatar">{{ userName.charAt(0) }}</div>
			<div class="user-info">
				<div class="name">{{ userName }}</div>
				<div class="role">{{ userRole }}</div>
			</div>
		</div>

		<div class="task-info-panel">
			<div class="panel-title">Task Information</div>
			<!--			<div class="task-progress">-->
			<!--				<div class="progress-item">-->
			<!--					<div class="progress-label">Conversation Progress</div>-->
			<!--					<template v-if="maxRounds === -1">-->
			<!--						<div class="unlimited-progress">-->
			<!--							<div class="progress-bar" :style="{ width: '100%' }"></div>-->
			<!--						</div>-->
			<!--						<div class="progress-text">{{ currentRound }} / Unlimited</div>-->
			<!--					</template>-->
			<!--					<template v-else>-->
			<!--						<el-progress-->
			<!--							:percentage="Math.round((currentRound / maxRounds) * 100)"-->
			<!--							:stroke-width="8"-->
			<!--							:show-text="false"-->
			<!--						/>-->
			<!--						<div class="progress-text">{{ currentRound }}/{{ maxRounds }} Rounds</div>-->
			<!--					</template>-->
			<!--				</div>-->
			<!--			</div>-->

			<!-- Soup Surface Information - Only displayed when soup surface info is available -->
			<div class="soup-info" v-if="soupSurface">
				<div class="panel-title">🐢 Soup Surface</div>
				<div class="soup-content">
					{{ soupSurface }}
				</div>
			</div>
			<!-- Usage Statistics -->
			<div class="usage-stats">
				<div class="panel-title">💡 Token Statistics</div>
				<div class="stats-grid">
					<div class="stat-item">
						<div class="stat-label">Input Tokens</div>
						<div class="stat-value">{{ usageState.totalInputTokens || 0 }}</div>
					</div>
					<div class="stat-item">
						<div class="stat-label">Output Tokens</div>
						<div class="stat-value">{{ usageState.totalOutputTokens || 0 }}</div>
					</div>
					<div class="stat-item">
						<div class="stat-label">Total Tokens</div>
						<div class="stat-value">{{ usageState.totalTokens || 0 }}</div>
					</div>
					<div class="stat-item">
						<div class="stat-label">Total Cost</div>
						<div class="stat-value">¥{{ (usageState.totalPrice || 0).toFixed(4) }}</div>
					</div>
				</div>
			</div>
			<!-- Game Instructions -->
			<div class="game-info">
				<div class="panel-title">{{ soupSurface ? "Game Rules" : "Game Instructions" }}</div>
				<div class="game-tip">
					<template v-if="soupSurface">
						<p>• Ask questions to deduce the truth behind the soup</p>
						<p>• Questions can only be answered with "Yes", "No" or "I don't know"</p>
						<p>• Think carefully about the value of each question</p>
						<p>• When you think you know the answer, you can directly state your complete reasoning</p>
					</template>
					<template v-else>
						<p>You can click on the avatar above to switch conversations with different characters</p>
						<p>Understanding the truth requires continuous questioning and collecting clues</p>
						<p>Enjoy your game!</p>
					</template>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
/**
 * Chat Sidebar Component
 * @description Displays user information and task progress
 */
import { defineProps } from "vue";

defineProps({
	/** User name */
	userName: {
		type: String,
		required: true,
	},
	/** User role */
	userRole: {
		type: String,
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
</script>

<style lang="scss" scoped>
.chat-sidebar {
	width: 300px;
	background: linear-gradient(to bottom, #1a1a2e, #16213e);
	border-right: 1px solid rgba(100, 100, 255, 0.2);
	display: flex;
	flex-direction: column;

	.user-profile {
		padding: 1.5rem;
		display: flex;
		align-items: center;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);

		.avatar {
			width: 50px;
			height: 50px;
			border-radius: 50%;
			background: linear-gradient(135deg, #4da6ff, #5e72e4);
			color: #fff;
			display: flex;
			align-items: center;
			justify-content: center;
			font-size: 1.5rem;
			font-weight: bold;
			margin-right: 1rem;
			box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
		}

		.user-info {
			.name {
				font-weight: 600;
				font-size: 1.1rem;
				color: #e0e0e0;
			}

			.role {
				color: #a0a0a0;
				font-size: 0.9rem;
			}
		}
	}

	.task-info-panel {
		flex: 1;
		padding: 1.5rem;
		overflow-y: auto;

		.panel-title {
			font-size: 0.9rem;
			color: #a0a0a0;
			text-transform: uppercase;
			margin-bottom: 1rem;
			letter-spacing: 1px;
		}

		.task-progress {
			margin-bottom: 2rem;

			.progress-item {
				margin-bottom: 1rem;

				.progress-label {
					display: flex;
					justify-content: space-between;
					margin-bottom: 0.5rem;
					color: #e0e0e0;
					font-size: 0.9rem;
				}

				.progress-text {
					margin-top: 0.5rem;
					font-size: 0.9rem;
					color: #a0a0a0;
					text-align: right;
				}
			}
		}

		.usage-stats {
			margin-bottom: 2rem;

			.stats-grid {
				display: grid;
				grid-template-columns: 1fr 1fr;
				gap: 0.75rem;
			}

			.stat-item {
				padding: 0.75rem;
				background: rgba(30, 30, 50, 0.6);
				border: 1px solid rgba(100, 100, 255, 0.2);
				border-radius: 6px;
				text-align: center;

				.stat-label {
					font-size: 0.75rem;
					color: #a0a0a0;
					margin-bottom: 0.25rem;
				}

				.stat-value {
					font-size: 0.9rem;
					color: #4da6ff;
					font-weight: 600;
				}
			}
		}

		.soup-info {
			margin-bottom: 2rem;

			.soup-content {
				padding: 1rem;
				background: linear-gradient(135deg, rgba(37, 99, 235, 0.1), rgba(30, 64, 175, 0.1));
				border: 1px solid rgba(37, 99, 235, 0.3);
				border-radius: 8px;
				color: #f0f9ff;
				font-size: 0.9rem;
				line-height: 1.6;
				white-space: pre-wrap;
				word-break: break-word;
				box-shadow: 0 2px 8px rgba(37, 99, 235, 0.1);
			}
		}

		.game-info {
			.game-tip {
				padding: 1rem;
				background-color: rgba(30, 30, 50, 0.6);
				border-radius: 6px;
				border: 1px solid rgba(100, 100, 255, 0.2);

				p {
					margin: 0.7rem 0;
					color: #e0e0e0;
					font-size: 0.9rem;
					line-height: 1.4;

					&:first-child {
						margin-top: 0;
					}

					&:last-child {
						margin-bottom: 0;
					}
				}
			}
		}
	}
}

.unlimited-progress {
	height: 8px;
	background-color: rgba(77, 166, 255, 0.2);
	border-radius: 4px;
	overflow: hidden;
	position: relative;

	.progress-bar {
		height: 100%;
		background: linear-gradient(90deg, rgba(77, 166, 255, 0.5), rgba(77, 166, 255, 0.8));
		background-size: 200% 100%;
		animation: gradient-move 2s infinite linear;
		border-radius: 4px;
	}
}

@keyframes gradient-move {
	0% {
		background-position: 0% 50%;
	}
	50% {
		background-position: 100% 50%;
	}
	100% {
		background-position: 0% 50%;
	}
}

// 媒体查询 - 移动适配
@media (max-width: 768px) {
	.chat-sidebar {
		width: 100%;
		height: auto;
		border-right: none;
		border-bottom: 1px solid rgba(100, 100, 255, 0.2);

		.task-info-panel {
			display: none; // 移动端隐藏任务信息面板
		}
	}
}
</style>
