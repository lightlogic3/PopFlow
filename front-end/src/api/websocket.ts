/**
 * @description: WebSocket API封装
 * @description WebSocket相关业务逻辑封装，包括游戏连接等
 */
import { ElMessage } from "element-plus";
import wsClient, { WebSocketClient, WebSocketOptions } from "@/utils/websocket";

/**
 * 游戏消息类型
 */
export interface GameMessage {
	/** 消息角色 */
	role?: string;
	/** 角色名称 */
	role_name?: string;
	/** 消息内容 */
	content?: string;
	/** 消息状态 */
	status?: string;
	/** 会话ID */
	session_id?: string;
	/** 消息 */
	message?: string;
	/** 角色信息 */
	roles_info?: Array<{
		role_id: string | number;
		name: string;
		description?: string;
		level?: string;
		image_url?: string;
	}>;
	/** 错误信息 */
	error?: string;
}

/**
 * 连接游戏WebSocket
 * @param gameType 游戏类型
 * @param taskId 任务ID
 * @param play_type 玩法类型
 * @param callbacks 回调函数
 * @returns WebSocketClient 连接对象
 */
export function connectGameWebSocket(
	gameType: string,
	taskId: string | number,
	play_type: string,
	callbacks: {
		onMessage?: (data: GameMessage) => void;
		onOpen?: () => void;
		onClose?: () => void;
		onError?: (error: any) => void;
	},
): WebSocketClient {
	// 构建WebSocket URL
	const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
	// 使用与API相同的环境变量配置，从API_URL提取主机部分
	const apiUrl = import.meta.env.VITE_APP_API_URL || "";
	// 从API URL中提取主机部分，或者使用当前域名
	let wsBaseUrl = "";

	if (apiUrl) {
		// 尝试从API URL提取主机部分
		try {
			// 移除协议前缀 (http:// 或 https://)
			const apiUrlNoProtocol = apiUrl.replace(/^https?:\/\//, "");
			// 提取主机部分 (排除路径)
			wsBaseUrl = apiUrlNoProtocol.split("/")[0];
		} catch (e) {
			console.warn("无法从API URL提取主机部分:", e);
			wsBaseUrl = window.location.host;
		}
	} else {
		// 回退到当前域名
		wsBaseUrl = window.location.host;
	}

	// 使用专用的WebSocket环境变量（如果有）
	wsBaseUrl = import.meta.env.VITE_APP_WS_BASE_URL || wsBaseUrl;

	const wsUrl = `${wsProtocol}//${wsBaseUrl}/ws/game/${gameType}/${taskId}/${play_type}`;
	console.log("使用WebSocket URL:", wsUrl);

	// WebSocket连接配置
	const options: WebSocketOptions = {
		url: wsUrl,
		autoReconnect: true, // 自动重连
		maxReconnectAttempts: 3, // 最大重连次数
		reconnectInterval: 3000, // 重连间隔时间(ms)
		onOpen: () => {
			console.log("游戏WebSocket连接已建立");
			if (callbacks.onOpen) {
				callbacks.onOpen();
			}
		},
		onMessage: (event) => {
			try {
				// 解析消息数据
				const data: GameMessage = JSON.parse(event.data);
				console.log("游戏WebSocket收到消息:", data);

				// 调用回调函数
				if (callbacks.onMessage) {
					callbacks.onMessage(data);
				}
			} catch (error) {
				console.error("解析WebSocket消息失败:", error);
				ElMessage.error("解析游戏消息失败");
			}
		},
		onClose: (event) => {
			console.log("游戏WebSocket连接已关闭", event);
			if (callbacks.onClose) {
				callbacks.onClose();
			}
		},
		onError: (event) => {
			console.error("游戏WebSocket连接错误:", event);
			ElMessage.error("游戏连接失败，请稍后重试");
			if (callbacks.onError) {
				callbacks.onError(event);
			}
		},
	};

	// 生成连接key (避免相同游戏建立多个连接)
	const connectionKey = `game_${gameType}_${taskId}`;

	// 创建连接
	const client = wsClient.createWebSocket(connectionKey, options);

	// 启动连接
	client.connect().catch((error) => {
		console.error("WebSocket连接失败:", error);
		if (callbacks.onError) {
			callbacks.onError(error);
		}
		ElMessage.error("无法连接到游戏服务器，请检查网络后重试");
	});

	return client;
}

/**
 * 初始化游戏会话
 * @param client WebSocket客户端
 * @param sessionId 会话ID
 * @param userData 用户数据
 * @param roleIds 角色ID列表
 * @returns boolean 是否发送成功
 */
export function initGameSession(
	client: any,
	sessionId: string,
	userData: { name: string; background?: string },
	roleIds: string[] = ["123"], // 默认角色ID
): boolean {
	// 构建初始化消息
	const initMessage = {
		type: "init_session",
		session_id: sessionId,
		user_data: userData,
		roles: roleIds,
	};

	// 发送初始化消息
	return client.send(initMessage);
}

/**
 * 发送用户消息
 * @param client WebSocket客户端
 * @param message 消息内容
 * @returns boolean 是否发送成功
 */
export function sendUserMessage(client: any, message: string): boolean {
	// 构建用户消息
	const userMessage = {
		type: "human_message",
		message: message,
	};

	// 发送用户消息
	return client.send(userMessage);
}

/**
 * 结束游戏
 * @param client WebSocket客户端
 * @returns boolean 是否发送成功
 */
export function endGame(client: any): boolean {
	// 构建结束游戏消息
	const endGameMessage = {
		type: "end_game",
	};

	// 发送结束游戏消息
	const result = client.send(endGameMessage);

	// 关闭WebSocket连接
	if (result) {
		setTimeout(() => {
			client.close(1000, "游戏结束");
		}, 2000); // 延迟关闭，等待服务器响应
	}

	return result;
}

/**
 * 检查WebSocket连接状态
 * @param gameType 游戏类型
 * @param taskId 任务ID
 * @returns boolean 是否已连接
 */
export function isGameConnected(gameType: string, taskId: string | number): boolean {
	const connectionKey = `game_${gameType}_${taskId}`;
	const client = wsClient.getWebSocket(connectionKey);
	return client?.isConnected() || false;
}

/**
 * 断开游戏WebSocket连接
 * @param gameType 游戏类型
 * @param taskId 任务ID
 * @returns boolean 是否成功关闭
 */
export function disconnectGameWebSocket(gameType: string, taskId: string | number): boolean {
	const connectionKey = `game_${gameType}_${taskId}`;
	return wsClient.closeWebSocket(connectionKey);
}

export default {
	connectGameWebSocket,
	initGameSession,
	sendUserMessage,
	endGame,
	isGameConnected,
	disconnectGameWebSocket,
};
