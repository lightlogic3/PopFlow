/**
 * @description: WebSocket连接管理工具
 * @description WebSocket连接管理器，用于创建、管理和监听WebSocket连接
 */

export interface WebSocketOptions {
	/** WebSocket连接URL */
	url: string;
	/** 连接成功回调 */
	onOpen?: (event: Event) => void;
	/** 接收消息回调 */
	onMessage?: (event: MessageEvent) => void;
	/** 连接关闭回调 */
	onClose?: (event: CloseEvent) => void;
	/** 连接错误回调 */
	onError?: (event: Event) => void;
	/** 是否自动重连 */
	autoReconnect?: boolean;
	/** 最大重连次数, 0表示无限重连 */
	maxReconnectAttempts?: number;
	/** 重连间隔(毫秒) */
	reconnectInterval?: number;
}

export interface WebSocketMessage {
	/** 消息类型 */
	type: string;
	/** 消息内容 */
	[key: string]: any;
}

/**
 * WebSocket连接管理类
 */
export class WebSocketClient {
	private socket: WebSocket | null = null;
	private options: WebSocketOptions;
	private reconnectAttempts = 0;
	private reconnectTimer: number | null = null;
	private manualClosed = false;

	/**
	 * 构造函数
	 * @param options WebSocket连接选项
	 */
	constructor(options: WebSocketOptions) {
		// 默认选项
		const defaultOptions: Partial<WebSocketOptions> = {
			autoReconnect: true,
			maxReconnectAttempts: 5,
			reconnectInterval: 3000,
		};

		this.options = { ...defaultOptions, ...options };
	}

	/**
	 * 连接WebSocket
	 * @returns Promise<boolean> 连接结果
	 */
	public connect(): Promise<boolean> {
		return new Promise((resolve, reject) => {
			try {
				this.manualClosed = false;
				this.socket = new WebSocket(this.options.url);

				// 连接成功
				this.socket.onopen = (event) => {
					this.reconnectAttempts = 0;
					if (this.options.onOpen) {
						this.options.onOpen(event);
					}
					resolve(true);
				};

				// 接收消息
				this.socket.onmessage = (event) => {
					if (this.options.onMessage) {
						this.options.onMessage(event);
					}
				};

				// 连接关闭
				this.socket.onclose = (event) => {
					if (this.options.onClose) {
						this.options.onClose(event);
					}

					// 自动重连
					if (
						this.options.autoReconnect &&
						!this.manualClosed &&
						(this.options.maxReconnectAttempts === 0 || this.reconnectAttempts < this.options.maxReconnectAttempts)
					) {
						this.reconnect();
					}

					if (event.code !== 1000 && event.code !== 1001) {
						// 非正常关闭
						reject(new Error(`WebSocket连接关闭: ${event.code}, ${event.reason}`));
					} else if (this.socket && this.socket.readyState === WebSocket.CONNECTING) {
						// 连接中但失败
						reject(new Error("WebSocket连接失败"));
					}
				};

				// 连接错误
				this.socket.onerror = (event) => {
					if (this.options.onError) {
						this.options.onError(event);
					}
					reject(new Error("WebSocket连接错误"));
				};
			} catch (error) {
				reject(error);
			}
		});
	}

	/**
	 * 发送消息
	 * @param message 消息内容
	 * @returns boolean 发送结果
	 */
	public send(message: string | WebSocketMessage): boolean {
		if (!this.isConnected()) {
			console.error("WebSocket未连接，无法发送消息");
			return false;
		}

		try {
			// 如果message不是字符串，则转换为JSON字符串
			const data = typeof message === "string" ? message : JSON.stringify(message);
			this.socket?.send(data);
			return true;
		} catch (error) {
			console.error("发送消息失败:", error);
			return false;
		}
	}

	/**
	 * 关闭连接
	 * @param code 关闭代码
	 * @param reason 关闭原因
	 */
	public close(code?: number, reason?: string): void {
		this.manualClosed = true;
		if (this.reconnectTimer) {
			window.clearTimeout(this.reconnectTimer);
			this.reconnectTimer = null;
		}

		if (this.socket) {
			this.socket.close(code, reason);
			this.socket = null;
		}
	}

	/**
	 * 检查是否已连接
	 * @returns boolean
	 */
	public isConnected(): boolean {
		return this.socket !== null && this.socket.readyState === WebSocket.OPEN;
	}

	/**
	 * 重新连接
	 */
	private reconnect(): void {
		this.reconnectAttempts++;
		this.reconnectTimer = window.setTimeout(() => {
			console.log(
				`尝试重新连接 WebSocket (${this.reconnectAttempts}/${this.options.maxReconnectAttempts || "unlimited"})`,
			);
			this.connect().catch(() => {
				// 连接失败，不做处理，会自动触发重连
			});
		}, this.options.reconnectInterval);
	}
}

/**
 * WebSocket连接实例Map
 */
const wsInstances = new Map<string, WebSocketClient>();

/**
 * 创建WebSocket连接
 * @param key 连接标识
 * @param options 连接选项
 * @returns WebSocketClient
 */
export function createWebSocket(key: string, options: WebSocketOptions): WebSocketClient {
	// 如果已存在相同key的连接，先关闭
	if (wsInstances.has(key)) {
		wsInstances.get(key)?.close();
		wsInstances.delete(key);
	}

	// 创建新连接
	const client = new WebSocketClient(options);
	wsInstances.set(key, client);
	return client;
}

/**
 * 获取WebSocket连接
 * @param key 连接标识
 * @returns WebSocketClient | undefined
 */
export function getWebSocket(key: string): WebSocketClient | undefined {
	return wsInstances.get(key);
}

/**
 * 关闭WebSocket连接
 * @param key 连接标识
 * @returns boolean
 */
export function closeWebSocket(key: string): boolean {
	if (wsInstances.has(key)) {
		wsInstances.get(key)?.close();
		wsInstances.delete(key);
		return true;
	}
	return false;
}

/**
 * 关闭所有WebSocket连接
 */
export function closeAllWebSockets(): void {
	wsInstances.forEach((client) => {
		client.close();
	});
	wsInstances.clear();
}

// 页面刷新或关闭时，关闭所有连接
window.addEventListener("beforeunload", () => {
	closeAllWebSockets();
});

export default {
	createWebSocket,
	getWebSocket,
	closeWebSocket,
	closeAllWebSockets,
};
