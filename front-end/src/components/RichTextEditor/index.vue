<template>
	<div class="rich-text-editor">
		<div class="editor-wrapper">
			<!-- 工具栏 -->
			<div class="editor-toolbar" v-if="showToolbar">
				<div class="toolbar-group">
					<button
						type="button"
						class="toolbar-btn"
						:class="{ active: editor?.isActive('bold') }"
						@click="editor?.chain().focus().toggleBold().run()"
						title="粗体"
					>
						<strong>B</strong>
					</button>
					<button
						type="button"
						class="toolbar-btn"
						:class="{ active: editor?.isActive('italic') }"
						@click="editor?.chain().focus().toggleItalic().run()"
						title="斜体"
					>
						<em>I</em>
					</button>
					<button
						type="button"
						class="toolbar-btn"
						:class="{ active: editor?.isActive('strike') }"
						@click="editor?.chain().focus().toggleStrike().run()"
						title="删除线"
					>
						<s>S</s>
					</button>
				</div>

				<div class="toolbar-group">
					<button
						type="button"
						class="toolbar-btn"
						:class="{ active: editor?.isActive('heading', { level: 1 }) }"
						@click="editor?.chain().focus().toggleHeading({ level: 1 }).run()"
						title="标题1"
					>
						H1
					</button>
					<button
						type="button"
						class="toolbar-btn"
						:class="{ active: editor?.isActive('heading', { level: 2 }) }"
						@click="editor?.chain().focus().toggleHeading({ level: 2 }).run()"
						title="标题2"
					>
						H2
					</button>
					<button
						type="button"
						class="toolbar-btn"
						:class="{ active: editor?.isActive('heading', { level: 3 }) }"
						@click="editor?.chain().focus().toggleHeading({ level: 3 }).run()"
						title="标题3"
					>
						H3
					</button>
				</div>

				<div class="toolbar-group">
					<button
						type="button"
						class="toolbar-btn"
						:class="{ active: editor?.isActive('bulletList') }"
						@click="editor?.chain().focus().toggleBulletList().run()"
						title="无序列表"
					>
						•
					</button>
					<button
						type="button"
						class="toolbar-btn"
						:class="{ active: editor?.isActive('orderedList') }"
						@click="editor?.chain().focus().toggleOrderedList().run()"
						title="有序列表"
					>
						1.
					</button>
				</div>

				<div class="toolbar-group">
					<button type="button" class="toolbar-btn" @click="insertImage" title="插入图片">📷</button>
					<button
						type="button"
						class="toolbar-btn"
						@click="adjustImageSize"
						title="调整图片大小"
						:disabled="!hasSelectedImage"
					>
						📏
					</button>
				</div>
			</div>

			<!-- 编辑器内容区 -->
			<div class="editor-content" :style="{ minHeight: minHeight }">
				<EditorContent :editor="editor" />
			</div>

			<!-- 字符计数 -->
			<div class="editor-footer" v-if="showCharCount">
				<div class="char-counter" :class="{ warning: charCount > maxLength * 0.9, error: charCount > maxLength }">
					{{ charCount }}{{ maxLength ? ` / ${maxLength}` : "" }}
				</div>
			</div>
		</div>

		<!-- 图片上传对话框 -->
		<el-dialog v-model="imageDialogVisible" title="插入图片" width="500px">
			<div class="image-upload-section">
				<FileUploader
					v-model="imageUrl"
					folder="rich-text-images"
					accept="image/*"
					:max-size="5"
					@upload-success="onImageUploadSuccess"
				/>
			</div>
			<template #footer>
				<div class="dialog-footer">
					<el-button @click="imageDialogVisible = false">取消</el-button>
					<el-button type="primary" @click="confirmInsertImage" :disabled="!imageUrl"> 插入图片 </el-button>
				</div>
			</template>
		</el-dialog>

		<!-- 图片尺寸调整对话框 -->
		<el-dialog v-model="imageSizeDialogVisible" title="调整图片大小" width="400px">
			<div class="image-size-section">
				<el-radio-group v-model="currentImageSize" @change="previewImageSize">
					<el-radio v-for="option in imageSizeOptions" :key="option.value" :label="option.value" class="size-option">
						{{ option.label }}
					</el-radio>
				</el-radio-group>
			</div>
			<template #footer>
				<div class="dialog-footer">
					<el-button @click="imageSizeDialogVisible = false">取消</el-button>
					<el-button type="primary" @click="confirmImageSize">确认</el-button>
				</div>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, computed } from "vue";
import { Editor, EditorContent } from "@tiptap/vue-3";
import StarterKit from "@tiptap/starter-kit";
import Placeholder from "@tiptap/extension-placeholder";
import { Node, mergeAttributes } from "@tiptap/core";
import FileUploader from "@/components/FileUploader";

// 创建一个自定义的图片Node扩展
const CustomImage = Node.create({
	name: "customImage",
	group: "block",
	atom: true,

	addAttributes() {
		return {
			src: {
				default: null,
			},
			alt: {
				default: null,
			},
			title: {
				default: null,
			},
			width: {
				default: "100%",
			},
			size: {
				default: "large", // small, medium, large, original
			},
		};
	},

	parseHTML() {
		return [
			{
				tag: "img[src]",
				getAttrs: (element) => {
					const width = element.style.width || element.getAttribute("width") || "100%";
					let size = "large";

					// 根据宽度推断尺寸
					if (width.includes("25%") || width.includes("200px")) size = "small";
					else if (width.includes("50%") || width.includes("400px")) size = "medium";
					else if (width.includes("75%") || width.includes("600px")) size = "large";
					else if (width.includes("100%") || width === "auto") size = "original";

					return {
						src: element.getAttribute("src"),
						alt: element.getAttribute("alt") || "",
						title: element.getAttribute("title") || "",
						width: width,
						size: size,
					};
				},
			},
		];
	},

	renderHTML({ HTMLAttributes, node }) {
		const { size, width } = node.attrs;
		let imageWidth = "100%";

		// 根据尺寸设置宽度
		switch (size) {
			case "small":
				imageWidth = "25%";
				break;
			case "medium":
				imageWidth = "50%";
				break;
			case "large":
				imageWidth = "75%";
				break;
			case "original":
				imageWidth = width || "100%";
				break;
			default:
				imageWidth = width || "100%";
		}

		return [
			"img",
			mergeAttributes(HTMLAttributes, {
				class: "rich-text-image",
				style: `width: ${imageWidth}; max-width: 100%; height: auto; margin: 12px 0; border-radius: 4px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); display: block;`,
			}),
		];
	},
  addCommands() {
		return {
			setCustomImage:
				(options: any) =>
				({ commands }: { commands: any }) => {
					return commands.insertContent({
						type: this.name,
						attrs: {
							...options,
							size: options.size || "large",
							width: options.width || "75%",
						},
					}) as boolean;
				},
			updateImageSize:
				(options: any) =>
				({ commands }: { commands: any }) => {
					return commands.updateAttributes(this.name, {
						size: options.size,
						width: options.width,
					}) as boolean;
				},
		} as any;
	},
});

const props = defineProps({
	modelValue: {
		type: String,
		default: "",
	},
	placeholder: {
		type: String,
		default: "请输入内容...",
	},
	minHeight: {
		type: String,
		default: "200px",
	},
	maxLength: {
		type: Number,
		default: 0, // 0表示无限制
	},
	showToolbar: {
		type: Boolean,
		default: true,
	},
	showCharCount: {
		type: Boolean,
		default: true,
	},
});

const emit = defineEmits(["update:modelValue"]);

// 编辑器实例
const editor = ref<any>(null);

// 图片上传相关
const imageDialogVisible = ref(false);
const imageUrl = ref("");

// 图片尺寸调整相关
const imageSizeDialogVisible = ref(false);
const selectedImagePos = ref(null);
const currentImageSize = ref("large");

// 图片尺寸选项
const imageSizeOptions = [
	{ label: "小图 (25%)", value: "small", width: "25%" },
	{ label: "中图 (50%)", value: "medium", width: "50%" },
	{ label: "大图 (75%)", value: "large", width: "75%" },
	{ label: "原始大小", value: "original", width: "100%" },
];

// 字符计数
const charCount = computed(() => {
	if (!editor.value) return 0;
	return editor.value.getText().length;
});

// 检查是否选中了图片
const hasSelectedImage = computed(() => {
	if (!editor.value) return false;
	const { selection } = editor.value.state;
	const node = editor.value.state.doc.nodeAt(selection.from);
	return node && node.type.name === "customImage";
});

// 初始化编辑器
onMounted(() => {
	editor.value = new Editor({
		extensions: [
			StarterKit,
			CustomImage,
			Placeholder.configure({
				placeholder: props.placeholder,
			}),
		],
		content: props.modelValue || "",
		parseOptions: {
			preserveWhitespace: "full",
		},
		onUpdate: ({ editor }) => {
			const html = editor.getHTML();

			// 检查字符数限制
			if (props.maxLength > 0 && editor.getText().length > props.maxLength) {
				return; // 阻止更新
			}

			emit("update:modelValue", html);
		},
	});
});

// 清理编辑器
onBeforeUnmount(() => {
	if (editor.value) {
		editor.value.destroy();
	}
});

// 监听外部值变化
watch(
	() => props.modelValue,
	(newValue) => {
		if (editor.value && editor.value.getHTML() !== newValue) {
			// 使用 setContent 来设置 HTML 内容，确保能正确解析图片等元素
			editor.value.commands.setContent(newValue || "");
		}
	},
);

// 插入图片
function insertImage() {
	imageUrl.value = "";
	imageDialogVisible.value = true;
}

// 图片上传成功回调
function onImageUploadSuccess() {
	// 图片上传成功后不自动插入，等用户点击确认
}

// 确认插入图片
function confirmInsertImage() {
	if (imageUrl.value && editor.value) {
		editor.value.chain().focus().setCustomImage({ src: imageUrl.value }).run();
		imageDialogVisible.value = false;
		imageUrl.value = "";
	}
}

// 调整图片大小
function adjustImageSize() {
	if (!editor.value || !hasSelectedImage.value) return;

	const { selection } = editor.value.state;
	const node = editor.value.state.doc.nodeAt(selection.from);

	if (node && node.type.name === "customImage") {
		currentImageSize.value = node.attrs.size || "large";
		selectedImagePos.value = selection.from;
		imageSizeDialogVisible.value = true;
	}
}

// 预览图片尺寸（实时更新）
function previewImageSize() {
	if (editor.value && selectedImagePos.value !== null) {
		const sizeOption = imageSizeOptions.find((opt) => opt.value === currentImageSize.value);
		if (sizeOption) {
			editor.value
				.chain()
				.focus()
				.updateImageSize({
					size: currentImageSize.value,
					width: sizeOption.width,
				})
				.run();
		}
	}
}

// 确认图片尺寸
function confirmImageSize() {
	imageSizeDialogVisible.value = false;
	selectedImagePos.value = null;
}

// 导出方法供父组件使用
defineExpose({
	getHTML: () => editor.value?.getHTML() || "",
	getText: () => editor.value?.getText() || "",
	setContent: (content: string) => editor.value?.commands.setContent(content),
	focus: () => editor.value?.commands.focus(),
});
</script>

<style lang="scss" scoped>
.rich-text-editor {
	border: 1px solid #dcdfe6;
	border-radius: 4px;
	background-color: #fff;

	&:hover {
		border-color: #c0c4cc;
	}

	&:focus-within {
		border-color: #409eff;
	}
}

.editor-wrapper {
	display: flex;
	flex-direction: column;
}

.editor-toolbar {
	display: flex;
	align-items: center;
	gap: 8px;
	padding: 8px 12px;
	border-bottom: 1px solid #e4e7ed;
	background-color: #fafafa;
	border-radius: 4px 4px 0 0;

	.toolbar-group {
		display: flex;
		align-items: center;
		gap: 4px;

		&:not(:last-child)::after {
			content: "";
			width: 1px;
			height: 20px;
			background-color: #e4e7ed;
			margin-left: 8px;
		}
	}

	.toolbar-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 28px;
		height: 28px;
		border: none;
		background: transparent;
		border-radius: 4px;
		cursor: pointer;
		transition: all 0.2s;
		font-size: 12px;
		font-weight: 600;

		&:hover {
			background-color: #f0f0f0;
		}

		&.active {
			background-color: #409eff;
			color: #fff;
		}

		&:disabled {
			opacity: 0.5;
			cursor: not-allowed;
		}
	}
}

.editor-content {
	flex: 1;
	overflow-y: auto;

	:deep(.ProseMirror) {
		padding: 12px;
		outline: none;
		font-size: 14px;
		line-height: 1.6;
		color: #303133;

		p {
			margin: 0 0 12px 0;

			&:last-child {
				margin-bottom: 0;
			}
		}

		h1,
		h2,
		h3,
		h4,
		h5,
		h6 {
			margin: 16px 0 8px 0;
			font-weight: 600;

			&:first-child {
				margin-top: 0;
			}
		}

		h1 {
			font-size: 24px;
		}
		h2 {
			font-size: 20px;
		}
		h3 {
			font-size: 18px;
		}

		ul,
		ol {
			padding-left: 20px;
			margin: 12px 0;

			li {
				margin: 4px 0;
			}
		}

		strong {
			font-weight: 600;
		}

		em {
			font-style: italic;
		}

		s {
			text-decoration: line-through;
		}

		.rich-text-image {
			max-width: 100%;
			height: auto;
			margin: 12px 0;
			border-radius: 4px;
			box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
			display: block;
		}

		img {
			max-width: 100%;
			height: auto;
		}

		// 占位符样式
		p.is-editor-empty:first-child::before {
			content: attr(data-placeholder);
			float: left;
			color: #c0c4cc;
			pointer-events: none;
			height: 0;
		}
	}
}

.editor-footer {
	padding: 8px 12px;
	border-top: 1px solid #e4e7ed;
	background-color: #fafafa;
	border-radius: 0 0 4px 4px;

	.char-counter {
		font-size: 12px;
		color: #909399;
		text-align: right;

		&.warning {
			color: #e6a23c;
		}

		&.error {
			color: #f56c6c;
		}
	}
}

.image-upload-section {
	padding: 20px 0;
}

.image-size-section {
	padding: 20px 0;

	.size-option {
		display: block;
		margin-bottom: 12px;

		&:last-child {
			margin-bottom: 0;
		}
	}
}

.dialog-footer {
	text-align: right;
}
</style>
