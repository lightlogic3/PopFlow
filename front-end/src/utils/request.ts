/**
 * @description: 自定义 request 网络请求工具,基于axios
 * @author LiQingSong
 */
import { message as ElMessage } from "@/utils/reset-message";
import qs from "qs";
import axios, { AxiosInstance, AxiosResponse, Canceler, RawAxiosRequestHeaders } from "axios";
import { ContentTypeEnum, ResultCodeEnum } from "@/enums/utils.request.enum";
import { ajaxHeadersTokenKey, ajaxResponseNoVerifyUrl } from "@/config/settings";
import { getToken, removeToken } from "@/utils/localToken";
import { isFunction } from "@/utils/is";
import router from "@/config/router";
import { IResponseData, ICodeMessage, IAxiosRequestConfig } from "@/@types/utils.request";

// 判断是否是writer角色
const isWriterRole = () => {
	// 优先从localStorage读取用户角色
	const storedRole = localStorage.getItem("user_role");
	if (storedRole === "writer") {
		return true;
	}

	// 检查URL参数（仅作为备选方案）
	const urlParams = new URLSearchParams(window.location.search);
	if (urlParams.get("role") === "writer") {
		// 保存用户角色到localStorage
		localStorage.setItem("user_role", "writer");
		return true;
	}

	return false;
};

/* ================ 自定义请求消除器 相关 S ======================= */
/**
 * @description: 声明一个 Map 用于存储每个请求的标识 和 取消函数
 */
// let requestPendingMap = new Map<string, Canceler>();

/**
 * @description: 序列化配置参数，生成唯一请求标识url
 * @param config 请求配置参数
 * @returns string
 */
// export const getRequestPendingUrl = (config: IAxiosRequestConfig) => {
// 	let configData: any = config.data;
// 	try {
// 		configData = JSON.parse(config.data);
// 	} catch (error) {
// 		configData = config.data;
// 	}
// 	return [config.method, config.url, qs.stringify(configData), qs.stringify(config.params)].join("&");
// };
/**
 * @description: 自定义请求消除器类
 */
// export class RequestCanceler {
// 	/**
// 	 * @description: 添加请求
// 	 * @param config 请求配置参数
// 	 * @returns void
// 	 */
// 	addPending(config: IAxiosRequestConfig) {
// 		// 在请求开始前，对之前的请求做检查取消操作
// 		this.removePending(config);
// 		const url = getRequestPendingUrl(config);
// 		config.cancelToken =
// 			config.cancelToken ||
// 			new axios.CancelToken((cancel) => {
// 				if (!requestPendingMap.has(url)) {
// 					// 如果 pending 中不存在当前请求，则添加进去
// 					requestPendingMap.set(url, cancel);
// 				}
// 			});
// 	}

// 	/**
// 	 * @description: 移除请求
// 	 * @param config 请求配置参数
// 	 * @returns void
// 	 */
// 	removePending(config: IAxiosRequestConfig, isCancel = true) {
// 		const url = getRequestPendingUrl(config);
// 		if (requestPendingMap.has(url)) {
// 			// 如果在 pending 中存在当前请求标识
// 			if (isCancel) {
// 				//  isCancel = true，需要取消当前请求
// 				const cancel = requestPendingMap.get(url);
// 				cancel && cancel();
// 			}
// 			// 移除
// 			requestPendingMap.delete(url);
// 		}
// 	}

// 	/**
// 	 * @description: 清空所有pending
// 	 * @returns void
// 	 */
// 	removeAllPending() {
// 		requestPendingMap.forEach((cancel) => {
// 			cancel && isFunction(cancel) && cancel();
// 		});
// 		requestPendingMap.clear();
// 	}

// 	/**
// 	 * @description: 重置
// 	 * @returns void
// 	 */
// 	reset(): void {
// 		requestPendingMap = new Map<string, Canceler>();
// 	}
// }

/**
 * @description: 生成请求消除器
 */
// export const requestCanceler = new RequestCanceler();

/* ================ 自定义请求类 相关 S ======================= */
/**
 * @description: 自定义状态码对应内容信息
 */
const customCodeMessage: ICodeMessage = {
	[ResultCodeEnum.LOGININVALID]: "当前用户登入信息已失效，请重新登入再操作", // 未登陆,自己可以调整状态码
};

/**
 * @description: 定义服务端状态码对应内容信息
 */
const serverCodeMessage: ICodeMessage = {
	200: "服务器成功返回请求的数据",
	400: "Bad Request",
	401: "Unauthorized",
	403: "Forbidden",
	404: "Not Found",
	500: "服务器发生错误，请检查服务器(Internal Server Error)",
	502: "网关错误(Bad Gateway)",
	503: "服务不可用，服务器暂时过载或维护(Service Unavailable)",
	504: "网关超时(Gateway Timeout)",
};

/**
 * @description: 处理后端新的响应结构，提取data字段
 * @param response 后端响应数据
 * @returns 提取后的data数据
 */
export function extractResponseData<T = any>(response: any): T {
	// 如果响应包含code和message字段，说明是新的响应结构
	if (response && typeof response === "object" && "code" in response && "message" in response) {
		// 如果code不是成功码，抛出错误
		if (response.code !== 200) {
			throw new Error(response.message || "请求失败");
		}
		// 返回data字段
		return response.data;
	}

	// 如果不是新结构，直接返回原始响应
	return response;
}

/**
 * @description: 异常处理程序
 * @returns Promise
 */
const errorHandler = (error: any) => {
	const { response, message } = error;
	if (message === "CustomError") {
		// 自定义错误
		const { config, data } = response;
		const { url, baseURL } = config;
		const { code, msg } = data;
		const reqUrl = url.split("?")[0].replace(baseURL, "");
		const noVerifyBool = ajaxResponseNoVerifyUrl.includes(reqUrl);
		if (!noVerifyBool) {
			// alert(customCodeMessage[code] || msg || "Error");
			ElMessage.warning(customCodeMessage[code] || msg || "Error");

			if (code === ResultCodeEnum.LOGININVALID) {
				// 如果未登录或失效，这里可以跳转到登录页面
				// 根据角色确定登录页面
				const loginPath = isWriterRole() ? "/user/login/writer" : "/user/login";
				router.push(loginPath);
			}
		}
	} else if (message === "canceled") {
		console.log("canceled", error);
	} else if (response && response.status) {
		const errorText = serverCodeMessage[response.status] || response.statusText;
		const { status, request } = response;

		// 处理401状态码（未授权/令牌问题）
		if (status === 401) {
			// 检查响应数据是否包含特定错误码
			try {
				const errorData = response.data;
				// 显示更友好的提示消息
				if (errorData && errorData.detail) {
					const detail = typeof errorData.detail === "object" ? errorData.detail : { message: errorData.detail };
					ElMessage.error(detail.message || "登录已过期，请重新登录");
				} else if (errorData && errorData.message) {
					// 处理API返回的错误消息
					ElMessage.error(errorData.message);
				} else {
					ElMessage.error("登录已过期，请重新登录");
				}
			} catch (e) {
				ElMessage.error("登录状态异常，请重新登录");
			}

			// 获取当前路径和查询参数
			const currentRoute = router.currentRoute.value;
			const currentPath = currentRoute.fullPath;

			// 检查是否已经在登录页面
			const isOnLoginPage = currentPath.includes("/user/login");

			// 如果已经在登录页面，不需要跳转
			if (isOnLoginPage) {
				// 如果是在登录页面发生的401错误（登录失败），不做路由跳转
				// 只清除token，让用户重新输入
				removeToken();
				return Promise.reject(new Error("登录失败"));
			}

			// 不在登录页面，需要跳转到对应的登录页

			// 清除本地token
			removeToken();

			// 延迟跳转，让用户看到提示信息
			setTimeout(() => {
				// 提取清理后的路径，避免重定向参数叠加
				let cleanPath = currentPath;

				// 处理现有的URL中可能包含的redirect参数
				if (cleanPath.includes("redirect=")) {
					try {
						// 尝试从URL中提取最内层的目标路径
						const url = new URL(cleanPath, window.location.origin);
						// 提取值并删除redirect参数
						if (url.searchParams.has("redirect")) {
							const redirectValue = url.searchParams.get("redirect");
							url.searchParams.delete("redirect");

							// 如果redirect值不是登录页面，则使用它作为最终redirect
							if (redirectValue && !redirectValue.includes("/user/login")) {
								cleanPath = redirectValue;
							} else {
								// 否则使用当前路径(不含redirect参数)
								cleanPath = url.pathname + url.search;
							}
						}
					} catch {
						// 解析失败时简化处理
						cleanPath = cleanPath.split("?")[0];
					}
				}

				// 根据角色确定登录页面
				const loginPath = isWriterRole() ? "/user/login/writer" : "/user/login";
				router.push({
					path: loginPath,
					query: {
						redirect: cleanPath !== loginPath ? cleanPath : undefined,
					},
				});
			}, 1500);

			return Promise.reject(new Error("登录已过期"));
		}

		// 其他状态码错误
		ElMessage.warning(`请求错误 ${status}: ${request.responseURL}\n${errorText}`);
	} else if (!response) {
		// alert("网络异常：您的网络发生异常，无法连接服务器");
		ElMessage.warning("网络异常：您的网络发生异常，无法连接服务器");
	}

	return Promise.reject(error);
};

/**
 * @description: 自定义请求类
 */
export class Request {
	ajax: AxiosInstance;
	public constructor(config: IAxiosRequestConfig) {
		// 初始化传参，所以目前 headers 是 RawAxiosRequestHeaders | undefined 类型。
		const { contentType, headers = {}, ...otherCofing } = config || {};
		// console.log("headers constructor", headers);

		// 实例化axios，配置请求时的默认参数
		this.ajax = axios.create({
			...otherCofing,
			headers: {
				...(headers as RawAxiosRequestHeaders),
				"content-type": contentType || ContentTypeEnum.JSON,
			},
		});

		/**
		 * @description: 请求前, 请求拦截器
		 */
		this.ajax.interceptors.request.use(
			(axiosConfig) => {
				// 将当前请求添加到请求消除器 pending 中
				// requestCanceler.addPending(axiosConfig);

				// 自定义添加token header
				const headerToken = getToken();
				if (headerToken) {
					// axios 已经运行起来了，所以 headers 现在已经是 AxiosHeaders 类型了，所以不能当做json类型
					if (typeof axiosConfig.headers?.set === "function") {
						axiosConfig.headers?.set(ajaxHeadersTokenKey, headerToken);
					}
					// axiosConfig.headers[ajaxHeadersTokenKey] = headerToken;
				}

				// 添加用户角色到请求头
				if (isWriterRole() && typeof axiosConfig.headers?.set === "function") {
					axiosConfig.headers?.set("X-User-Role", "writer");
				}

				return axiosConfig;
			},
			/* ,error=> {} */ // 已在 export default catch
		);

		/**
		 * @description: 请求后, 响应拦截器
		 */
		this.ajax.interceptors.response.use(
			(response: AxiosResponse<IResponseData>) => {
				// 在请求结束后，移除本次请求
				// requestCanceler.removePending(response.config, false);

				// const res = response.data;
				// const { code } = res;

				// 自定义状态码验证
				// if (code !== ResultCodeEnum.SUCCESS) {
				// 	return Promise.reject({
				// 		response,
				// 		message: "CustomError",
				// 	});
				// }

				return response;
			},
			/* , error => {} */ // 已在 export default catch
		);
	}

	/**
	 * @description: 请求方法
	 * @param config 请求参数
	 * @returns Promise of extracted data
	 */
	all<T = any>(config: IAxiosRequestConfig): Promise<T> {
		// 初始化传参，所以目前 headers 是 RawAxiosRequestHeaders | undefined 类型。
		const { contentType, headers = {}, ...otherCofing } = config || {};
		// console.log("headers all", headers);

		// 对于流式响应，直接返回响应对象
		if (config.responseType === "stream") {
			return this.ajax({
				...otherCofing,
				headers: {
					...(headers as RawAxiosRequestHeaders),
					"content-type": contentType || ContentTypeEnum.JSON,
				},
				responseType: "blob",
			}).catch((error: any) => errorHandler(error)) as Promise<T>;
		}

		return this.ajax({
			...otherCofing,
			headers: {
				...(headers as RawAxiosRequestHeaders),
				"content-type": contentType || ContentTypeEnum.JSON,
			},
		})
			.then((response: AxiosResponse) => {
				// 提取响应中的data字段
				const resData = response.data;
				// 处理新的响应结构，提取data字段
				return extractResponseData(resData) as T;
			})
			.catch((error: any) => errorHandler(error));
	}
}

/**
 * @description: 生成统一公共请求
 */
const ask = new Request({
	baseURL: import.meta.env.VITE_APP_API_URL || "", // url = api url + request url
	withCredentials: false, // 当跨域请求时发送cookie
	timeout: 300000, // 请求超时时间,5000(单位毫秒) / 0 不做限制
});

/**
 * @description: 导出 ajax 方法
 * @param config IAxiosRequestConfig 请求参数
 * @returns Promise of extracted data
 */
export default function ajax<T = any>(config: IAxiosRequestConfig): Promise<T> {
	return ask.all<T>(config);
}
