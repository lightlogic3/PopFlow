import request from "@/utils/request";

/**
 * 音色类型定义
 * @typedef {Object} AudioTimbre
 * @property {number} id - 音色ID
 * @property {string} alias - 别名
 * @property {string} speaker_id - 声音ID
 * @property {string} version - 训练版本
 * @property {string} state - 状态
 * @property {string} audition - 声音B64
 * @property {string} create_time - 创建时间
 * @property {string} update_time - 更新时间
 */
export interface AudioTimbre {
	id: number;
	alias?: string;
	speaker_id?: string;
	version?: string;
	state?: string;
	audition?: string;
	create_time: string;
	update_time: string;
}

/**
 * 获取音色列表
 * @returns {Promise<AudioTimbre[]>}
 */
export function listAudioTimbres() {
	return request<any[]>({
		url: "/audio-timbre",
		method: "get",
	});
}

/**
 * 获取单个音色详情
 * @param {number} id - 音色ID
 * @returns {Promise<AudioTimbre>}
 */
export function getAudioTimbre(id: number) {
	return request<AudioTimbre>({
		url: `/audio-timbre/${id}`,
		method: "get",
	});
}

/**
 * 根据说话人ID获取音色
 * @param {string} speakerId - 说话人ID
 * @returns {Promise<AudioTimbre>}
 */
export function getAudioTimbreBySpeakerId(speakerId: string) {
	return request<AudioTimbre>({
		url: `/audio-timbre/speaker/${speakerId}`,
		method: "get",
	});
}

/**
 * 创建音色
 */
export function createAudioTimbre(data: {
	alias?: string;
	speaker_id?: string;
	version?: string;
	expire_time?: string;
	state?: string;
	audition?: string;
	craete_at?: string;
}) {
	return request({
		url: "audio-timbre/",
		method: "post",
		data,
	});
}

/**
 * 更新音色
 */
export function updateAudioTimbre(
	timbreId: number,
	data: {
		alias?: string;
		speaker_id?: string;
		version?: string;
		expire_time?: string;
		state?: string;
		audition?: string;
		update_at?: string;
	},
) {
	return request({
		url: `audio-timbre/${timbreId}`,
		method: "put",
		data,
	});
}

/**
 * 删除音色
 */
export function deleteAudioTimbre(timbreId: number) {
	return request({
		url: `audio-timbre/${timbreId}`,
		method: "delete",
	});
}
