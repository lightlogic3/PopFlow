<template>
	<div class="task-header">
		<div class="header-row">
			<div class="back-button" @click="handleGoBack"><i class="el-icon-arrow-left"></i> 返回</div>
			<div class="action-buttons">
				<slot></slot>
			</div>
		</div>
		<div class="task-title">{{ title }}</div>
		<div class="task-description">{{ description }}</div>
	</div>
</template>

<script setup lang="ts">
/**
 * 任务头部组件
 * @description 显示任务标题、描述和返回按钮
 */
import { defineProps, defineEmits } from "vue";

const props = defineProps({
	/** 任务标题 */
	title: {
		type: String,
		required: true,
	},
	/** 任务描述 */
	description: {
		type: String,
		required: true,
	},
	/** 是否已开始聊天 */
	isStarted: {
		type: Boolean,
		default: false,
	},
});
console.log(props);
const emit = defineEmits(["go-back"]);

/**
 * 处理返回按钮点击
 */
const handleGoBack = () => {
	emit("go-back");
};
</script>

<style lang="scss" scoped>
.task-header {
	padding: 1rem 2rem;
	background: linear-gradient(to right, #1a1a2e, #16213e);
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
	position: relative;
	z-index: 1;

	.header-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
	}

	.back-button {
		display: inline-flex;
		align-items: center;
		cursor: pointer;
		color: #4da6ff;
		transition: color 0.2s;

		&:hover {
			color: #66b3ff;
		}

		i {
			margin-right: 0.5rem;
		}
	}

	.action-buttons {
		display: flex;
		gap: 10px;
	}

	.task-title {
		font-size: 1.8rem;
		font-weight: 600;
		margin-bottom: 0.5rem;
		background: linear-gradient(90deg, #5e72e4, #00c6ff);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
	}

	.task-description {
		font-size: 1rem;
		color: #a0a0a0;
		max-width: 800px;
	}
}

@media (max-width: 768px) {
	.task-header {
		padding: 1rem;

		.task-title {
			font-size: 1.5rem;
		}

		.task-description {
			font-size: 0.9rem;
		}
	}
}
</style>
