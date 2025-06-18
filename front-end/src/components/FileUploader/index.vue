<template>
	<div class="file-uploader" :class="{ 'is-disabled': disabled }">
		<div
			class="file-uploader-input"
			:class="{
				'is-dragover': isDragOver,
				'has-file': !!modelValue,
				'is-image': isImage && !imageLoadError,
			}"
			@dragover.prevent="onDragOver"
			@dragleave.prevent="onDragLeave"
			@drop.prevent="onDrop"
			@click="triggerUpload"
		>
			<div v-if="!modelValue" class="upload-placeholder">
				<i class="el-icon-upload"></i>
				<div class="el-upload__text">
					<span>click upload file or drag and drop the file here</span>
				</div>
			</div>
			<div v-else class="file-preview">
				<div v-if="isImage" class="image-preview">
					<img :src="modelValue" :alt="fileName" @load="onImageLoad" @error="onImageError" v-loading="imageLoading" />
				</div>
				<div v-else class="file-info">
					<i class="el-icon-document"></i>
					<span>{{ fileName }}</span>
				</div>
			</div>
			<el-progress
				v-if="uploading"
				class="upload-progress"
				:percentage="uploadProgress"
				:stroke-width="3"
				status="success"
			></el-progress>
		</div>

		<div v-if="modelValue" class="file-actions">
			<a :href="modelValue" target="_blank" class="action-btn">
				<i class="el-icon-view"></i>
			</a>
			<a v-if="allowCopy" @click.prevent="copyUrl" class="action-btn">
				<i class="el-icon-document-copy"></i>
			</a>
			<a @click.prevent="removeFile" class="action-btn">
				<i class="el-icon-delete"></i>
			</a>
		</div>

		<input ref="fileInput" type="file" class="file-input" :accept="accept" @change="handleFileChange" />
	</div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { uploadFile, getFileNameFromUrl, isImageFile } from "@/api/oss";

const props = defineProps({
	modelValue: {
		type: String,
		default: "",
	},
	accept: {
		type: String,
		default: "*",
	},
	disabled: {
		type: Boolean,
		default: false,
	},
	folder: {
		type: String,
		default: "upload",
	},
	allowCopy: {
		type: Boolean,
		default: true,
	},
	maxSize: {
		type: Number,
		default: 10, // 默认最大10MB
	},
});

const emit = defineEmits(["update:modelValue", "upload-success", "upload-error"]);

// 引用和状态
const fileInput = ref<HTMLInputElement | null>(null);
const isDragOver = ref(false);
const uploading = ref(false);
const uploadProgress = ref(0);
const imageLoading = ref(false);
const imageLoadError = ref(false);

// 计算属性
const fileName = computed(() => {
	if (!props.modelValue) return "";
	return getFileNameFromUrl(props.modelValue);
});

const isImage = computed(() => {
	if (!props.modelValue) return false;

	// 检查URL是否是图片
	const url = props.modelValue.toLowerCase();
	if (url.match(/\.(jpg|jpeg|png|gif|bmp|webp)(\?.*)?$/)) {
		return true;
	}

	// 也检查文件名
	return isImageFile(fileName.value);
});

// 方法
const triggerUpload = () => {
	if (props.disabled) return;
	if (fileInput.value) {
		fileInput.value.click();
	}
};

const onDragOver = (e: DragEvent) => {
	if (props.disabled) return;
	isDragOver.value = true;
	e.dataTransfer;
};

const onDragLeave = () => {
	isDragOver.value = false;
};

const onDrop = (e: DragEvent) => {
	if (props.disabled) return;
	isDragOver.value = false;

	if (e.dataTransfer && e.dataTransfer.files.length > 0) {
		handleFile(e.dataTransfer.files[0]);
	}
};

const handleFileChange = (e: Event) => {
	const target = e.target as HTMLInputElement;
	if (target.files && target.files.length > 0) {
		handleFile(target.files[0]);
		// 重置input以便可以上传相同的文件
		target.value = "";
	}
};

const handleFile = async (file: File) => {
	// check the file size
	const fileSizeMB = file.size / (1024 * 1024);
	if (fileSizeMB > props.maxSize) {
		ElMessage.error(`the file size cannot be exceeded ${props.maxSize}MB`);
		return;
	}

	try {
		uploading.value = true;
		uploadProgress.value = 0;

		// 创建表单数据
		const formData = new FormData();
		// 确保文件作为文件对象传递，而不是对象字面量
		formData.append("file", file, file.name);
		formData.append("folder", props.folder);

		// log output for easy debugging
		console.log("Uploading file:", file.name, file.type, file.size);

		// simulate the progress of the upload
		const progressInterval = setInterval(() => {
			if (uploadProgress.value < 90) {
				uploadProgress.value += 10;
			}
		}, 300);

		// 上传文件
		const response = await uploadFile(formData);

		clearInterval(progressInterval);
		uploadProgress.value = 100;

		if (response.success) {
			// 如果是图片，预加载一下
			if (file.type.startsWith("image/")) {
				preloadImage(response.file_url);
			}

			// 更新模型值
			emit("update:modelValue", response.file_url);
			emit("upload-success", response);
			ElMessage.success("文件上传成功");
		} else {
			emit("upload-error", response);
			ElMessage.error(response.message || "upload failed");
		}
	} catch (error: any) {
		emit("upload-error", error);
		ElMessage.error("upload failed: " + (error.message || "unknown error"));
	} finally {
		setTimeout(() => {
			uploading.value = false;
		}, 500);
	}
};

const removeFile = () => {
	emit("update:modelValue", "");
	imageLoadError.value = false;
};

const copyUrl = () => {
	if (!props.modelValue) return;

	navigator.clipboard
		.writeText(props.modelValue)
		.then(() => {
			ElMessage.success("the url has been copied to the clipboard");
		})
		.catch(() => {
			ElMessage.error("replication-failed");
		});
};

// picture loading related
const onImageLoad = () => {
	imageLoading.value = false;
	imageLoadError.value = false;
};

const onImageError = () => {
	imageLoading.value = false;
	imageLoadError.value = true;
	ElMessage.warning("the image failed to load");
};

const preloadImage = (url: string) => {
	imageLoading.value = true;
	imageLoadError.value = false;

	const img = new Image();
	img.onload = () => {
		imageLoading.value = false;
	};
	img.onerror = () => {
		imageLoading.value = false;
		imageLoadError.value = true;
	};
	img.src = url;
};

// Listens for changes in model value and preloads when the URL is an image
watch(
	() => props.modelValue,
	(newValue) => {
		if (newValue && isImage.value) {
			preloadImage(newValue);
		}
	},
);

// When the component is loaded, if the model value is the image URL, the image is preloaded
onMounted(() => {
	if (props.modelValue && isImage.value) {
		preloadImage(props.modelValue);
	}
});
</script>

<style scoped>
.file-uploader {
	display: flex;
	flex-direction: column;
	width: 100%;
}

.file-uploader-input {
	position: relative;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	border: 1px dashed #d9d9d9;
	border-radius: 6px;
	background-color: #fafafa;
	min-height: 120px;
	padding: 16px;
	cursor: pointer;
	transition: all 0.3s;
}

.file-uploader-input:hover {
	border-color: #409eff;
}

.file-uploader-input.is-dragover {
	border-color: #409eff;
	background-color: rgba(64, 158, 255, 0.1);
}

.file-uploader-input.has-file {
	border-style: solid;
}

.file-uploader-input.is-image {
	border-color: #67c23a;
	background-color: #f0f9eb;
}

.upload-placeholder {
	display: flex;
	flex-direction: column;
	align-items: center;
	color: #8c939d;
}

.upload-placeholder i {
	font-size: 28px;
	margin-bottom: 8px;
}

.file-preview {
	width: 100%;
	display: flex;
	justify-content: center;
}

.image-preview {
	max-width: 100%;
	position: relative;
}

.image-preview img {
	max-width: 100%;
	max-height: 200px;
	object-fit: contain;
	border-radius: 4px;
	box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
	transition: all 0.3s;
}

.image-preview img:hover {
	transform: scale(1.05);
	box-shadow: 0 2px 16px 0 rgba(0, 0, 0, 0.2);
}

.file-info {
	display: flex;
	align-items: center;
	color: #606266;
}

.file-info i {
	margin-right: 8px;
	font-size: 20px;
}

.file-actions {
	display: flex;
	justify-content: flex-end;
	margin-top: 8px;
}

.action-btn {
	color: #606266;
	margin-left: 10px;
	cursor: pointer;
}

.action-btn:hover {
	color: #409eff;
}

.file-input {
	display: none;
}

.upload-progress {
	position: absolute;
	bottom: 10px;
	left: 10px;
	right: 10px;
}

.is-disabled .file-uploader-input {
	cursor: not-allowed;
	background-color: #f5f7fa;
	border-color: #e4e7ed;
}

.is-disabled .upload-placeholder,
.is-disabled .file-info,
.is-disabled .action-btn {
	color: #c0c4cc;
}
</style>
