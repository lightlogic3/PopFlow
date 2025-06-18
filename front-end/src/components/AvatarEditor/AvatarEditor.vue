<script setup>
import { ref, onMounted, onBeforeUnmount, watch, computed } from "vue";
import { Editor, EditorContent } from "@tiptap/vue-3";
import StarterKit from "@tiptap/starter-kit";
import { Node, mergeAttributes } from "@tiptap/core";
import Placeholder from "@tiptap/extension-placeholder";

// 定义用户列表数据
const props = defineProps({
	users: {
		type: Array,
		default: () => [],
	},
	modelValue: {
		type: String,
		default: "",
	},
	maxLength: {
		type: Number,
		default: Infinity,
	},
	minLength: {
		type: Number,
		default: 0,
	},
	placeholder: {
		type: String,
		default: "请输入内容...",
	},
	minHeight: {
		type: String,
		default: "250px",
	},
});

// 定义事件
const emit = defineEmits(["update:content", "update:modelValue"]);

// 编辑器状态
const editor = ref(null);
const editorRef = ref(null);

// 创建一个自定义的角色头像Node扩展
const UserAvatar = Node.create({
	name: "userAvatar",

	addOptions() {
		return {
			HTMLAttributes: {},
		};
	},

	group: "inline",

	inline: true,

	atom: true,

	addAttributes() {
		return {
			value: {
				default: null,
			},
			name: {
				default: null,
			},
			avatar: {
				default: null,
			},
		};
	},

	parseHTML() {
		return [
			{
				tag: "span[data-type=\"user-avatar\"]",
			},
		];
	},

	renderHTML({ node }) {
		return [
			"span",
			mergeAttributes({ "data-type": "user-avatar", class: "user-mention", "data-data": node.attrs.value }),
			[
				"img",
				{
					src: node.attrs.avatar,
					alt: node.attrs.name,
					class: "user-avatar",
				},
			],
			["span", { class: "user-name" }, node.attrs.name],
		];
	},
});

// 监听编辑器内容变化，实现最大长度限制
let isUpdating = false;

// 初始化编辑器
onMounted(() => {
	// 创建编辑器实例
	editor.value = new Editor({
		extensions: [
			StarterKit,
			UserAvatar,
			Placeholder.configure({
				placeholder: props.placeholder,
			}),
		],
		content: "",
		autofocus: true,
		editable: true,
		onUpdate: ({ editor }) => {
			if (isUpdating) return;

			// 获取纯文本内容
			const plainText = getPlainText();

			// 检查是否超出最大长度限制
			if (plainText.length > props.maxLength) {
				// 如果超出，回滚到前一个有效状态
				isUpdating = true;
				const transaction = editor.state.tr.setMeta("preventUpdate", true);
				editor.view.dispatch(transaction);

				// 恢复之前的内容
				const validContent = props.modelValue.substring(0, props.maxLength);
				setContentFromText(validContent);

				isUpdating = false;
				return;
			}

			// 当编辑器内容更新时发出事件
			emit("update:content", editor.getHTML());

			// 同时更新modelValue
			emit("update:modelValue", plainText);
		},
	});

	// 初始化时发出一次内容更新事件
	emit("update:content", editor.value.getHTML());

	// 如果有初始modelValue，设置内容
	if (props.modelValue) {
		setContentFromText(props.modelValue);
	}
});

// 清理资源
onBeforeUnmount(() => {
	if (editor.value) {
		editor.value.destroy();
	}
});

// 插入用户提及
function insertMention(user) {
	if (!editor.value) return;

	// 先获取焦点
	editor.value.chain().focus();

	// 插入角色头像
	editor.value
		.chain()
		.insertContent({
			type: "userAvatar",
			attrs: {
				value: user.value,
				name: user.name,
				avatar: user.avatar,
			},
		})
		.run();
}

// 获取纯文本内容，用户头像转为{用户名}格式，并处理换行
function getPlainText() {
	if (!editor.value) return "";

	// 获取HTML内容
	const html = editor.value.getHTML();

	// 创建临时DOM元素解析HTML
	const tempDiv = document.createElement("div");
	tempDiv.innerHTML = html;

	// 处理所有用户头像节点
	const avatarNodes = tempDiv.querySelectorAll("span[data-type=\"user-avatar\"]");
	avatarNodes.forEach((node) => {
		// 获取用户名并创建替换文本
		const userName = node.getAttribute("data-data") || "";
		const replacement = document.createTextNode(`{${userName}}`);

		// 替换节点
		node.parentNode.replaceChild(replacement, node);
	});

	// 处理换行标签 <br>
	const brNodes = tempDiv.querySelectorAll("br");
	brNodes.forEach((br) => {
		const newLine = document.createTextNode("\n");
		br.parentNode.replaceChild(newLine, br);
	});

	// 处理段落标签 <p>，确保每个段落后有换行
	const paragraphs = tempDiv.querySelectorAll("p");
	paragraphs.forEach((p, index) => {
		// 只有当这不是最后一个段落时，才在末尾添加换行符
		if (index < paragraphs.length - 1 && !p.textContent.endsWith("\n")) {
			p.appendChild(document.createTextNode("\n"));
		}
	});

	// 获取处理后的纯文本
	const plainText = tempDiv.textContent || "";

	// 返回处理后的文本
	return plainText;
}

// 从纯文本设置内容，将{用户名}转换为用户头像
function setContentFromText(text) {
	if (!editor.value) return;

	// 清空当前内容
	editor.value.commands.setContent("");

	// 如果文本为空，直接返回（此时编辑器已被清空）
	if (!text) {
		emit("update:content", editor.value.getHTML());
		emit("update:modelValue", text);
		return;
	}

	// 正则表达式匹配{用户名}格式
	const regex = /{([^}]+)}/g;
	let lastIndex = 0;
	let match;

	// 遍历所有匹配项
	while ((match = regex.exec(text)) !== null) {
		// 添加匹配前的文本，处理文本中的换行符
		if (match.index > lastIndex) {
			const textBefore = text.substring(lastIndex, match.index);
			// 将文本按换行符分割，然后用 <br> 连接
			const lines = textBefore.split("\n");
			for (let i = 0; i < lines.length; i++) {
				if (i > 0) {
					// 插入换行
					editor.value.commands.insertContent("<br>");
				}
				if (lines[i].length > 0) {
					editor.value.commands.insertContent(lines[i]);
				}
			}
		}

		// 获取用户名
		const userName = match[1];

		// 查找对应的用户
		const user = props.users.find((u) => u.value === userName);

		if (user) {
			// 插入用户头像
			editor.value.commands.insertContent({
				type: "userAvatar",
				attrs: {
					value: user.value,
					name: user.name,
					avatar: user.avatar,
				},
			});
		} else {
			// 如果没找到用户，保留原文本
			editor.value.commands.insertContent(`{${userName}}`);
		}

		// 更新处理位置
		lastIndex = regex.lastIndex;
	}

	// 添加剩余文本，处理文本中的换行符
	if (lastIndex < text.length) {
		const textAfter = text.substring(lastIndex);
		// 将文本按换行符分割，然后用 <br> 连接
		const lines = textAfter.split("\n");
		for (let i = 0; i < lines.length; i++) {
			if (i > 0) {
				// 插入换行
				editor.value.commands.insertContent("<br>");
			}
			if (lines[i].length > 0) {
				editor.value.commands.insertContent(lines[i]);
			}
		}
	}

	// 发出内容更新事件
	emit("update:content", editor.value.getHTML());
	emit("update:modelValue", text);
}

// 监听modelValue变化
watch(
	() => props.modelValue,
	(newValue, oldValue) => {
		// 只有当值发生变化且编辑器实例存在时才更新
		if (newValue !== oldValue && editor.value && newValue !== getPlainText()) {
			setContentFromText(newValue);
		}
	},
);

// 创建计算属性来获取当前文本长度，供模板使用
const currentLength = computed(() => {
	return getPlainText().length;
});

// 创建计算属性检查是否有效
const isValidLength = computed(() => {
	const length = currentLength.value;
	return length >= props.minLength;
});

// 提供编辑器内容给父组件
defineExpose({
	getContent: () => editor.value?.getHTML(),
	getPlainText,
	setContentFromText,

	// 验证是否满足最小长度要求
	isValid: () => isValidLength.value,

	// 提供当前文本长度
	getCurrentLength: () => currentLength.value,
});
</script>

<template>
	<div class="avatar-editor">
		<div class="editor-wrapper" ref="editorRef" :style="{ minHeight: props.minHeight }">
			<!-- Tiptap编辑器 -->
			<EditorContent :editor="editor" class="content-editable" :style="{ minHeight: props.minHeight }" />

			<!-- 工具栏 -->
			<div class="editor-toolbar">
				<div class="characters-list">
					<!-- 显示所有角色 -->
					<div
						v-for="user in users"
						:key="user.id"
						class="character-item"
						@click="insertMention(user)"
						:title="`插入${user.name}`"
					>
						<img :src="user.avatar" :alt="user.name" class="character-avatar" />
						<span class="character-name">{{ user.name }}</span>
					</div>
				</div>

				<!-- 字符计数显示 -->
				<div
					class="char-counter"
					:class="{
						warning: currentLength > props.maxLength * 0.9,
						error: currentLength > props.maxLength,
						'too-short': currentLength < props.minLength && currentLength > 0,
					}"
				>
					<span>the current number of characters: {{ currentLength }}</span>
					<template v-if="props.maxLength !== Infinity">
						<span> / maximum: {{ props.maxLength }}</span>
					</template>
					<template v-if="props.minLength > 0">
						<span> (minimum requirements: {{ props.minLength }})</span>
					</template>
				</div>
			</div>
		</div>
	</div>
</template>

<style scoped>
.avatar-editor {
	display: flex;
	flex-direction: column;
	border: 1px solid #e8e8e8;
	border-radius: 6px;
	background-color: #fff;
	width: 100%;
	height: 100%;
}

.editor-wrapper {
	position: relative;
	display: flex;
	flex-direction: column;
	flex-grow: 1;
}

.content-editable {
	padding: 16px;
	outline: none;
	font-size: 16px;
	line-height: 1.8;
	overflow-y: auto;
	flex-grow: 1;
}

:deep(.ProseMirror) {
	outline: none;
	word-break: break-word;
	color: #000;
	font-size: 14px;
	min-height: calc(100% - 32px); /* 减去padding */
}

:deep(.ProseMirror p) {
	margin: 0 0 12px 0;
	color: #000;
}

.editor-toolbar {
	display: flex;
	flex-direction: column;
	padding: 12px 16px;
	border-top: 1px solid #f0f0f0;
	margin-top: auto;
}

.characters-list {
	display: flex;
	flex-wrap: wrap;
	gap: 10px;
	margin-bottom: 8px;
}

.character-item {
	display: flex;
	align-items: center;
	padding: 6px 10px;
	border-radius: 20px;
	background-color: #f5f5f5;
	cursor: pointer;
	transition: all 0.2s;
}

.character-item:hover {
	background-color: #e8f4ff;
}

.character-avatar {
	width: 16px;
	height: 16px;
	margin-right: 6px;
}

.character-name {
	font-size: 14px;
	color: #333;
}

.toolbar-hint {
	font-size: 14px;
	color: #666;
	margin-top: 8px;
}

/* 用户提及样式 */
:deep(.user-mention) {
	display: inline-flex;
	align-items: center;
	background-color: rgba(8, 115, 236, 0.45);
	border-radius: 4px;
	padding: 2px 6px;
	margin: 2px 2px;
	white-space: nowrap;
	user-select: none;
	vertical-align: middle;
}

:deep(.user-avatar) {
	width: 16px;
	height: 16px;
	margin-right: 6px;
	vertical-align: middle;
	position: relative;
	top: -2px;
	display: inline-block;
	margin-top: 2px;
}

:deep(.user-name) {
	font-size: 14px;
	color: #333;
	vertical-align: middle;
	display: inline-block;
}

.char-counter {
	font-size: 13px;
	color: #666;
	margin-top: 12px;
	padding: 6px 0;
	display: flex;
	align-items: center;
	justify-content: flex-start;
}

.char-counter.warning {
	color: #e6a23c;
}

.char-counter.error {
	color: #f56c6c;
}

.char-counter.too-short {
	color: #f56c6c;
}

/* 添加占位符文本的样式 */
:deep(.ProseMirror p.is-editor-empty:first-of-type::before) {
	content: attr(data-placeholder);
	float: left;
	color: #adb5bd;
	pointer-events: none;
	height: 0;
}

:deep(.ProseMirror .is-empty::before) {
	content: attr(data-placeholder);
	float: left;
	color: #adb5bd;
	pointer-events: none;
	height: 0;
}
</style>
