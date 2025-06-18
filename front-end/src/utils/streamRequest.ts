/**
 * @description: 流式请求工具，基于fetch API，复用request配置
 */
import { ajaxHeadersTokenKey } from "@/config/settings";
import { getToken } from "@/utils/localToken";
import { ContentTypeEnum } from "@/enums/utils.request.enum";

/**
 * 处理流式请求的选项
 */
interface StreamOptions {
	/**
	 * 是否启用调试日志
	 */
	debug?: boolean;

	/**
	 * 数据块处理方式
	 * - 'text': 按原始文本处理
	 * - 'json': 尝试解析JSON
	 * - 'sse': 按SSE格式处理 (data: 前缀)
	 * - 'token': 处理逐字符token流
	 */
	dataType?: "text" | "json" | "sse" | "token";

	/**
	 * 分隔符，用于分割响应块
	 * 默认为\n\n（两个换行符）
	 */
	delimiter?: string;

	/**
	 * 空块处理，默认忽略空块
	 */
	ignoreEmptyChunks?: boolean;

	/**
	 * 请求超时时间（毫秒）
	 */
	timeout?: number;

	/**
	 * 接口基础路径，不设置则使用环境变量中的值
	 */
	baseURL?: string;

	/**
	 * 是否需要携带token
	 */
	withToken?: boolean;

	/**
	 * 内容类型
	 */
	contentType?: string;

	/**
	 * 是否实时处理每个收到的数据片段，不等待分隔符
	 * 当需要逐字符显示时设为true
	 */
	realtime?: boolean;
}

/**
 * 流数据处理器回调函数类型
 */
type ChunkHandler = (chunk: string, isRaw?: boolean) => void;
type JsonHandler = (data: any) => void;
type ErrorHandler = (error: Error) => void;
type CompleteHandler = () => void;

/**
 * 流请求基类
 */
export class StreamRequest {
	private url: string;
	private method: string;
	private data: any;
	private options: StreamOptions;
	private headers: Record<string, string>;
	private abortController: AbortController;

	private onChunkHandlers: ChunkHandler[] = [];
	private onJsonHandlers: JsonHandler[] = [];
	private onErrorHandlers: ErrorHandler[] = [];
	private onCompleteHandlers: CompleteHandler[] = [];

	/**
	 * 创建流式请求
	 * @param url 请求URL
	 * @param method 请求方法
	 * @param data 请求数据
	 * @param options 流处理选项
	 */
	constructor(url: string, method: string = "post", data: any = {}, options: StreamOptions = {}) {
		this.url = url;
		this.method = method.toUpperCase();
		this.data = data;
		this.options = {
			debug: false,
			dataType: "sse",
			delimiter: "\n\n",
			ignoreEmptyChunks: true,
			timeout: 30000,
			baseURL: import.meta.env.VITE_APP_API_URL || "",
			withToken: true,
			contentType: ContentTypeEnum.JSON,
			...options,
		};
		this.headers = {
			"Content-Type": this.options.contentType || ContentTypeEnum.JSON,
		};
		this.abortController = new AbortController();

		// 添加token
		if (this.options.withToken) {
			const token = getToken();
			if (token) {
				this.headers[ajaxHeadersTokenKey] = token;
			}
		}
	}

	/**
	 * 构建完整URL
	 */
	private getFullUrl(): string {
		let fullUrl = this.url;
		if (!fullUrl.startsWith("http") && this.options.baseURL) {
			// 移除URL开头的斜杠
			const url = this.url.startsWith("/") ? this.url.substring(1) : this.url;
			// 确保baseURL以斜杠结尾
			const baseURL = this.options.baseURL.endsWith("/") ? this.options.baseURL : this.options.baseURL + "/";

			fullUrl = baseURL + url;
		}
		return fullUrl;
	}

	/**
	 * 添加请求头
	 * @param key 请求头键
	 * @param value 请求头值
	 */
	setHeader(key: string, value: string): this {
		this.headers[key] = value;
		return this;
	}

	/**
	 * 设置请求头
	 * @param headers 请求头对象
	 */
	setHeaders(headers: Record<string, string>): this {
		this.headers = { ...this.headers, ...headers };
		return this;
	}

	/**
	 * 注册原始数据块处理函数
	 * @param handler 处理函数
	 * @param rawData 是否接收完全未处理的原始数据
	 */
	onChunk(handler: ChunkHandler, rawData: boolean = false): this {
		// 将处理函数和原始数据标志一起存储
		this.onChunkHandlers.push((chunk: string, isRaw: boolean = false) => {
			if (rawData === isRaw) {
				handler(chunk, isRaw);
			}
		});
		return this;
	}

	/**
	 * 注册JSON数据处理函数
	 * @param handler 处理函数
	 */
	onJson(handler: JsonHandler): this {
		this.onJsonHandlers.push(handler);
		return this;
	}

	/**
	 * 注册错误处理函数
	 * @param handler 处理函数
	 */
	onError(handler: ErrorHandler): this {
		this.onErrorHandlers.push(handler);
		return this;
	}

	/**
	 * 注册完成处理函数
	 * @param handler 处理函数
	 */
	onComplete(handler: CompleteHandler): this {
		this.onCompleteHandlers.push(handler);
		return this;
	}

	/**
	 * 取消请求
	 */
	abort(): void {
		this.abortController.abort();
	}

	/**
	 * 执行流式请求
	 * @returns 返回Response对象，可用于获取响应头等信息
	 */
	async execute(): Promise<Response> {
		let response: Response | null = null;

		try {
			const fullUrl = this.getFullUrl();
			this.log("Request URL:", fullUrl);
			this.log("Request headers:", this.headers);

			// 超时处理
			const timeoutId = this.options.timeout
				? setTimeout(() => this.abortController.abort(), this.options.timeout)
				: null;

			// 构建请求配置
			const fetchOptions: RequestInit = {
				method: this.method,
				headers: this.headers,
				signal: this.abortController.signal,
			};

			// 添加请求体
			if (this.method !== "GET" && this.data) {
				fetchOptions.body = JSON.stringify(this.data);
			}

			// 发送请求
			response = await fetch(fullUrl, fetchOptions);

			// 取消超时
			if (timeoutId) {
				clearTimeout(timeoutId);
			}

			// 检查响应
			if (!response.ok) {
				throw new Error(`请求失败: ${response.status} ${response.statusText}`);
			}

			if (!response.body) {
				throw new Error("响应没有包含数据流");
			}

			// 处理流式响应
			await this.processStream(response.body);

			// 处理完成
			this.onCompleteHandlers.forEach((handler) => handler());

			// 返回response对象，让调用者可以获取到响应头等信息
			return response;
		} catch (error) {
			this.log("Stream request error", error);
			this.onErrorHandlers.forEach((handler) => handler(error as Error));

			// 如果已经有response了，即使发生错误也返回它
			if (response) {
				return response;
			}

			// 没有response则抛出异常
			throw error;
		}
	}

	/**
	 * 处理响应流
	 */
	private async processStream(stream: ReadableStream<Uint8Array>): Promise<void> {
		const reader = stream.getReader();
		const decoder = new TextDecoder();
		let buffer = "";

		try {
			while (true) {
				const { done, value } = await reader.read();

				if (done) {
					// 处理缓冲区中剩余的数据
					if (buffer.trim()) {
						await this.processChunk(buffer);
					}
					break;
				}

				// 解码并添加到缓冲区
				const text = decoder.decode(value, { stream: true });

				// 先发送完全未处理的原始数据块
				this.onChunkHandlers.forEach((handler) => handler(text, true));

				buffer += text;

				// 实时模式：立即处理每个到达的文本片段
				if (this.options.realtime && text.trim()) {
					// 对于token模式，直接处理每个文本片段
					if (this.options.dataType === "token") {
						this.processTokenChunk(text);
						// 清空buffer避免重复处理
						buffer = "";
						continue;
					}
				}

				// 标准模式：根据分隔符处理缓冲区
				const delimiter = this.options.delimiter as string;
				if (buffer.includes(delimiter)) {
					const parts = buffer.split(delimiter);
					// 处理除最后一部分外的所有完整部分
					for (let i = 0; i < parts.length - 1; i++) {
						await this.processChunk(parts[i]);
					}
					// 保留最后一部分继续缓冲
					buffer = parts[parts.length - 1];
				}
			}
		} finally {
			reader.releaseLock();
		}
	}

	/**
	 * 处理单个数据块
	 */
	private async processChunk(chunk: string): Promise<void> {
		// 跳过空块
		if (this.options.ignoreEmptyChunks && !chunk.trim()) {
			return;
		}

		// 处理标准块（非原始数据）
		this.onChunkHandlers.forEach((handler) => handler(chunk, false));

		// 根据数据类型处理
		switch (this.options.dataType) {
			case "text":
				// 原始文本，已在onChunk中处理
				break;

			case "json":
				try {
					const jsonData = JSON.parse(chunk);
					this.onJsonHandlers.forEach((handler) => handler(jsonData));
				} catch (error) {
					this.log("JSON parse error", error);
					// 非JSON数据，忽略
				}
				break;

			case "sse":
				// 处理Server-Sent Events格式
				await this.processSSEChunk(chunk);
				break;
		}
	}

	/**
	 * 处理SSE格式的数据块
	 */
	private async processSSEChunk(chunk: string): Promise<void> {
		const lines = chunk.split("\n").filter((line) => line.trim());

		for (const line of lines) {
			if (line.startsWith("data: ")) {
				const dataStr = line.slice(6);

				// 特殊标记处理
				if (dataStr === "[DONE]") {
					continue;
				}

				// 尝试解析JSON
				try {
					const jsonData = JSON.parse(dataStr);
					this.onJsonHandlers.forEach((handler) => handler(jsonData));
				} catch (error) {
					// 不是JSON，当作普通文本处理
					this.log("SSE data is not JSON", dataStr);
					this.onJsonHandlers.forEach((handler) => handler({ content: dataStr }));
				}
			}
		}
	}

	/**
	 * 处理token模式的文本片段（逐字符）
	 */
	private processTokenChunk(text: string): void {
		// 移除可能存在的SSE前缀
		let processedText = text;
		if (processedText.startsWith("data: ")) {
			processedText = processedText.slice(6);
		}

		// 去除多余的换行符
		processedText = processedText.replace(/\n\n$/, "");

		// 如果是[DONE]特殊标记，跳过
		if (processedText === "[DONE]") {
			return;
		}

		// 处理标准块（非原始数据）
		this.onChunkHandlers.forEach((handler) => handler(processedText, false));

		// 尝试解析JSON，否则作为普通文本处理
		try {
			const data = JSON.parse(processedText);
			this.onJsonHandlers.forEach((handler) => handler(data));
		} catch (e) {
			// 不是JSON，当作普通文本，但不重复发送给onChunkHandlers
			// 因为已经在上面发送过了
			this.onJsonHandlers.forEach((handler) => handler({ content: processedText }));
		}
	}

	/**
	 * 调试日志输出
	 */
	private log(...args: any[]): void {
		if (this.options.debug) {
			console.log("[StreamRequest]", ...args);
		}
	}
}

/**
 * 创建流式请求
 * @param url 请求URL
 * @param method 请求方法
 * @param data 请求数据
 * @param options 流处理选项
 */
export function createStreamRequest(
	url: string,
	method: string = "post",
	data: any = {},
	options: StreamOptions = {},
): StreamRequest {
	return new StreamRequest(url, method, data, options);
}

/**
 * 快速执行流式请求
 * @param url 请求URL
 * @param data 请求数据
 * @param onChunk 数据块处理函数
 * @param onError 错误处理函数
 * @returns 返回Response对象的Promise
 */
export function executeStreamRequest(
	url: string,
	data: any,
	onChunk: (data: any) => void,
	onError?: (error: Error) => void,
): Promise<Response> {
	const streamRequest = new StreamRequest(url, "post", data, { dataType: "sse" });

	streamRequest.onJson(onChunk);

	if (onError) {
		streamRequest.onError(onError);
	}

	return streamRequest.execute();
}
