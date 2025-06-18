<template>
	<div class="conversation-form">
		<el-form ref="formRef" :model="form" :rules="rules" label-width="100px" @submit.prevent>
			<el-form-item label="系统提示" prop="systemPrompt">
				<el-input
					v-model="form.systemPrompt"
					type="textarea"
					:rows="3"
					placeholder="请输入系统提示内容（可选）"
					maxlength="2000"
					show-word-limit
				/>
				<template #tip>
					<div class="form-tip">可选字段，设置对话开始时的系统指令或角色定位</div>
				</template>
			</el-form-item>

			<div class="messages-container">
				<div class="messages-header">
					<div class="title">对话消息</div>
					<el-button type="primary" size="small" @click="addMessage">添加消息</el-button>
				</div>

				<div v-if="!form.messages.length" class="empty-messages">请添加对话消息，至少需要一条消息</div>

				<div v-else class="messages-list">
					<transition-group name="message-item">
						<div v-for="(message, index) in form.messages" :key="message.id" class="message-item">
							<div class="message-header">
								<div class="message-index">消息 #{{ index + 1 }}</div>
								<div class="message-actions">
									<el-button v-if="index > 0" type="text" @click="moveMessage(index, index - 1)">
										<el-icon><ArrowUp /></el-icon>
									</el-button>
									<el-button v-if="index < form.messages.length - 1" type="text" @click="moveMessage(index, index + 1)">
										<el-icon><ArrowDown /></el-icon>
									</el-button>
									<el-button type="text" @click="removeMessage(index)">
										<el-icon><Delete /></el-icon>
									</el-button>
								</div>
							</div>

							<el-form-item :prop="`messages.${index}.role`" :rules="rules.messageRole" label="角色">
								<el-select v-model="message.role" placeholder="选择消息角色">
									<el-option label="用户" value="user" />
									<el-option label="助手" value="assistant" />
								</el-select>
							</el-form-item>

							<el-form-item :prop="`messages.${index}.content`" :rules="rules.messageContent" label="内容">
								<el-input
									v-model="message.content"
									type="textarea"
									:rows="3"
									:placeholder="message.role === 'user' ? '请输入用户消息内容' : '请输入助手回复内容'"
									maxlength="15000"
									show-word-limit
								/>
							</el-form-item>

							<div class="message-divider"></div>
						</div>
					</transition-group>
				</div>
			</div>

			<el-form-item>
				<el-switch v-model="showMetadata" class="block" active-text="添加元数据" />
			</el-form-item>

			<el-form-item v-if="showMetadata" label="元数据" prop="metadata">
				<el-input
					v-model="form.metadata"
					type="textarea"
					:rows="3"
					placeholder="请输入JSON格式的元数据（可选）"
					maxlength="2000"
					show-word-limit
				/>
				<template #tip>
					<div class="form-tip">可选字段，以JSON格式添加额外信息，如对话类别、来源等</div>
				</template>
			</el-form-item>
		</el-form>
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, defineProps, defineExpose } from "vue";
import { ElMessage } from "element-plus";
import { ArrowUp, ArrowDown, Delete } from "@element-plus/icons-vue";
import type { FormInstance, FormRules } from "element-plus";

/**
 * 消息类型定义
 */
interface Message {
	id: string;
	role: "user" | "assistant";
	content: string;
}

/**
 * 多轮对话表单数据类型定义
 */
interface ConversationFormData {
	id?: string | number;
	systemPrompt?: string;
	messages: Message[];
	metadata?: string;
}

/**
 * 多轮对话数据表单组件
 * @description 用于添加或编辑多轮对话类型的数据集条目，用于对话训练
 */

// 定义props
const props = defineProps<{
	formData: ConversationFormData;
	editMode: boolean;
}>();

// 表单引用
const formRef = ref<FormInstance>();

// 是否显示元数据
const showMetadata = ref(!!props.formData.metadata);

// 生成唯一ID
const generateId = (): string => {
	return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
};

// 表单数据
const form = reactive<ConversationFormData>({
	id: props.formData.id,
	systemPrompt: props.formData.systemPrompt || "",
	messages: props.formData.messages?.length
		? props.formData.messages.map((msg) => ({
				id: msg.id || generateId(),
				role: msg.role,
				content: msg.content,
		  }))
		: [],
	metadata: props.formData.metadata || "",
});

// 表单验证规则
const rules = reactive<FormRules>({
	messageRole: [{ required: true, message: "请选择消息角色", trigger: "change" }],
	messageContent: [
		{ required: true, message: "请输入消息内容", trigger: "blur" },
		{ min: 1, message: "消息内容不能为空", trigger: "blur" },
	],
	metadata: [
		{
			validator: (rule, value, callback) => {
				if (!value || value.trim() === "") {
					callback();
					return;
				}
				try {
					JSON.parse(value);
					callback();
				} catch (error) {
					callback(new Error("请输入有效的JSON格式"));
				}
			},
			trigger: "blur",
		},
	],
});

/**
 * 添加一条消息
 */
const addMessage = () => {
	form.messages.push({
		id: generateId(),
		role: form.messages.length % 2 === 0 ? "user" : "assistant",
		content: "",
	});
};

/**
 * 移除指定索引的消息
 */
const removeMessage = (index: number) => {
	form.messages.splice(index, 1);
};

/**
 * 移动消息位置
 */
const moveMessage = (fromIndex: number, toIndex: number) => {
	if (toIndex < 0 || toIndex >= form.messages.length) return;

	const item = form.messages[fromIndex];
	form.messages.splice(fromIndex, 1);
	form.messages.splice(toIndex, 0, item);
};

/**
 * 表单验证
 */
const validate = async (): Promise<boolean> => {
	if (!formRef.value) return false;

	// 检查是否有消息
	if (form.messages.length === 0) {
		ElMessage.error("请至少添加一条消息");
		return false;
	}

	try {
		await formRef.value.validate();

		// 检查每条消息的内容
		for (let i = 0; i < form.messages.length; i++) {
			const msg = form.messages[i];
			if (!msg.content.trim()) {
				ElMessage.error(`第 ${i + 1} 条消息内容不能为空`);
				return false;
			}
		}

		return true;
	} catch (error) {
		return false;
	}
};

/**
 * 获取表单数据
 */
const getFormData = (): ConversationFormData => {
	return {
		id: form.id,
		systemPrompt: form.systemPrompt.trim() !== "" ? form.systemPrompt.trim() : undefined,
		messages: form.messages.map((msg) => ({
			id: msg.id,
			role: msg.role,
			content: msg.content.trim(),
		})),
		metadata: showMetadata.value && form.metadata.trim() !== "" ? form.metadata.trim() : undefined,
	};
};

// 暴露方法
defineExpose({
	validate,
	getFormData,
});
</script>

<style lang="scss" scoped>
.conversation-form {
	.form-tip {
		color: var(--el-text-color-secondary);
		font-size: 12px;
		line-height: 1.5;
		margin-top: 2px;
	}

	.messages-container {
		margin-bottom: 20px;
		border: 1px solid var(--el-border-color);
		border-radius: 4px;
		padding: 16px;

		.messages-header {
			display: flex;
			justify-content: space-between;
			align-items: center;
			margin-bottom: 16px;

			.title {
				font-weight: bold;
				font-size: 16px;
			}
		}

		.empty-messages {
			color: var(--el-text-color-secondary);
			text-align: center;
			padding: 40px 0;
			font-size: 14px;
			background-color: var(--el-fill-color-lighter);
			border-radius: 4px;
		}

		.messages-list {
			.message-item {
				margin-bottom: 16px;
				padding-bottom: 16px;

				.message-header {
					display: flex;
					justify-content: space-between;
					align-items: center;
					margin-bottom: 12px;

					.message-index {
						font-weight: bold;
						color: var(--el-text-color-regular);
					}

					.message-actions {
						display: flex;
						gap: 8px;
					}
				}

				.message-divider {
					height: 1px;
					background-color: var(--el-border-color-lighter);
					margin-top: 16px;
				}

				&:last-child {
					margin-bottom: 0;

					.message-divider {
						display: none;
					}
				}
			}
		}
	}

	// 动画效果
	.message-item-enter-active,
	.message-item-leave-active {
		transition: all 0.3s ease;
	}

	.message-item-enter-from,
	.message-item-leave-to {
		opacity: 0;
		transform: translateY(30px);
	}
}
</style>
