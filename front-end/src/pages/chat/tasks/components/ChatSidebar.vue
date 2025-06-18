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
			<div class="panel-title">任务信息</div>
			<!--			<div class="task-progress">-->
			<!--				<div class="progress-item">-->
			<!--					<div class="progress-label">对话进度</div>-->
			<!--					<template v-if="maxRounds === -1">-->
			<!--						<div class="unlimited-progress">-->
			<!--							<div class="progress-bar" :style="{ width: '100%' }"></div>-->
			<!--						</div>-->
			<!--						<div class="progress-text">{{ currentRound }} / 无限制</div>-->
			<!--					</template>-->
			<!--					<template v-else>-->
			<!--						<el-progress-->
			<!--							:percentage="Math.round((currentRound / maxRounds) * 100)"-->
			<!--							:stroke-width="8"-->
			<!--							:show-text="false"-->
			<!--						/>-->
			<!--						<div class="progress-text">{{ currentRound }}/{{ maxRounds }}轮</div>-->
			<!--					</template>-->
			<!--				</div>-->
			<!--			</div>-->

			<!-- 汤面信息 - 仅当有汤面信息时显示 -->
			<div class="soup-info" v-if="soupSurface">
				<div class="panel-title">🐢 汤面</div>
				<div class="soup-content">
					{{ soupSurface }}
				</div>
			</div>
			<!-- 使用统计 -->
			<div class="usage-stats">
				<div class="panel-title">💡 Token统计</div>
				<div class="stats-grid">
					<div class="stat-item">
						<div class="stat-label">输入Token</div>
						<div class="stat-value">{{ usageState.totalInputTokens || 0 }}</div>
					</div>
					<div class="stat-item">
						<div class="stat-label">输出Token</div>
						<div class="stat-value">{{ usageState.totalOutputTokens || 0 }}</div>
					</div>
					<div class="stat-item">
						<div class="stat-label">总Token</div>
						<div class="stat-value">{{ usageState.totalTokens || 0 }}</div>
					</div>
					<div class="stat-item">
						<div class="stat-label">总费用</div>
						<div class="stat-value">¥{{ (usageState.totalPrice || 0).toFixed(4) }}</div>
					</div>
				</div>
			</div>
			<!-- 游戏说明 -->
			<div class="game-info">
				<div class="panel-title">{{ soupSurface ? "游戏规则" : "游戏说明" }}</div>
				<div class="game-tip">
					<template v-if="soupSurface">
						<p>• 通过提问来推理出汤底真相</p>
						<p>• 问题只能用"是"、"否"或"不知道"回答</p>
						<p>• 仔细思考每个问题的价值</p>
						<p>• 当你觉得知道答案时，可以直接说出完整推理</p>
					</template>
					<template v-else>
						<p>您可以通过点击上方的头像切换与不同角色对话</p>
						<p>了解真相需要不断提问，收集线索</p>
						<p>祝您游戏愉快！</p>
					</template>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
/**
 * 聊天侧边栏组件
 * @description 显示用户信息和任务进度
 */
import { defineProps } from "vue";

defineProps({
	/** 用户名称 */
	userName: {
		type: String,
		required: true,
	},
	/** 用户角色 */
	userRole: {
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
