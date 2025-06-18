import request from "@/utils/request";

/**
 * 文本转语音
 */
export function textToSpeech(params: {
	text: string;
	speaker_id: string;
	speed_ratio?: number;
	volume_ratio?: number;
	pitch_ratio?: number;
	save_file?: boolean;
}) {
	return request({
		url: "tts/text-to-speech",
		method: "post",
		data: params,
	});
}

/**
 * 获取音色列表
 */
export function getVoiceList(params: { sync_to_db?: boolean } = {}) {
	return request({
		url: "tts/voices",
		method: "get",
		params,
	});
}

/**
 * 激活音色
 */
export function activateVoices(data: { speaker_ids: string[] }) {
	return request({
		url: "tts/voices/activate",
		method: "post",
		data,
	});
}

/**
 * 同步音色数据
 */
export function syncVoices() {
	return request({
		url: "tts/voices/sync",
		method: "post",
	});
}

/**
 * 获取应用ID
 */
export function getAppId() {
	return request({
		url: "tts/app-id",
		method: "get",
	});
}

/**
 * 播放音频
 * @param base64 音频base64数据
 */
export function playAudio(base64: string): HTMLAudioElement | null {
	if (!base64) return null;

	try {
		// 判断是否已经是data URL格式
		const audioSrc = base64.startsWith("data:audio") ? base64 : `data:audio/mp3;base64,${base64}`;

		// 创建音频元素
		const audio = new Audio(audioSrc);
		audio.play();
		return audio;
	} catch (error) {
		console.error("播放音频失败:", error);
		return null;
	}
}

/**
 * 下载音频
 * @param base64 音频base64数据
 * @param fileName 文件名
 */
export function downloadAudio(base64: string, fileName: string = "audio.mp3"): boolean {
	if (!base64) return false;

	try {
		// 判断是否已经是data URL格式
		const audioSrc = base64.startsWith("data:audio") ? base64 : `data:audio/mp3;base64,${base64}`;

		// 创建下载链接
		const link = document.createElement("a");
		link.href = audioSrc;
		link.download = fileName;
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
		return true;
	} catch (error) {
		console.error("下载音频失败:", error);
		return false;
	}
}
