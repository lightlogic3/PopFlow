import request from "@/utils/request";

/**
 * 上传文件到OSS
 */
export function uploadFile(data: FormData) {
	return request({
		url: "oss/upload-file",
		method: "post",
		data,
		headers: {
			"Content-Type": "multipart/form-data",
		},
		transformRequest: [(data) => data],
	});
}

/**
 * 上传Base64编码的数据到OSS
 */
export function uploadBase64(data: { base64_data: string; file_ext?: string; folder?: string }) {
	return request({
		url: "oss/upload-base64",
		method: "post",
		data,
	});
}

/**
 * 获取对象的URL
 */
export function getObjectUrl(key: string) {
	return request({
		url: `oss/get-url/${key}`,
		method: "get",
	});
}

/**
 * 创建上传文件表单数据
 */
export function createUploadFormData(file: File, folder: string = "upload"): FormData {
	const formData = new FormData();
	formData.append("file", file);
	formData.append("folder", folder);
	return formData;
}

/**
 * 获取文件扩展名
 */
export function getFileExtension(filename: string): string {
	return filename.slice(((filename.lastIndexOf(".") - 1) >>> 0) + 1);
}

/**
 * 从文件URL中提取文件名
 */
export function getFileNameFromUrl(url: string): string {
	if (!url) return "";
	const parts = url.split("/");
	return parts[parts.length - 1];
}

/**
 * 判断是否是图片文件
 */
export function isImageFile(filename: string): boolean {
	const ext = getFileExtension(filename).toLowerCase();
	return ["jpg", "jpeg", "png", "gif", "bmp", "webp"].includes(ext);
}

/**
 * 判断是否是音频文件
 */
export function isAudioFile(filename: string): boolean {
	const ext = getFileExtension(filename).toLowerCase();
	return ["mp3", "wav", "ogg", "m4a", "flac"].includes(ext);
}

/**
 * 判断是否是视频文件
 */
export function isVideoFile(filename: string): boolean {
	const ext = getFileExtension(filename).toLowerCase();
	return ["mp4", "webm", "mov", "avi", "mkv"].includes(ext);
}
