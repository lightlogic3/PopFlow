/**
 * @description: 登录用户信息 store
 * @author LiQingSong
 */
import { defineStore } from "pinia";
import { queryUserInfo } from "@/services/user";

// state ts类型
export interface IUserState {
	// 用户id
	id: number;
	// 用户名
	name: string;
	// 用户权限角色
	roles: string[];
	permissions: string[];
	token: string;
	userId: number | null;
	username: string;
	nickname: string;
	avatar: string;
}

export const useUserStore = defineStore("useUserStore", {
	state: (): IUserState => {
		return {
			id: 0,
			name: "",
			roles: [],
			permissions: [],
			token: localStorage.getItem("token") || "",
			userId: null,
			username: "",
			nickname: "",
			avatar: "",
		};
	},
	getters: {
		// 是否登录
		isLogin({ id }) {
			return id > 0;
		},
		isLoggedIn: (state) => !!state.token,
		isAdmin: (state) => state.roles.includes("admin"),
	},
	actions: {
		/**
		 * @description: 获取用户信息
		 * @returns result code 0 已登录并且获取用户信息成功,1 未登录, 2 后端返回的其他错误，999 服务器错误
		 */
		async getInfo() {
			const result = { code: 0, msg: "" };
			if (this.id > 0) {
				// 如果用户已经登录了，就不要请求了
				return result;
			}

			try {
				const response: any = await queryUserInfo();
				const data = response.user || {};
				this.id = data.id || 0;
				this.name = data.nickname || "";
				this.roles = response.roles || [];
				this.permissions = response.permissions || [];

				// 检查角色并正确设置user_role
				const hasWriterRole = this.roles.some((role: any) =>
					typeof role === "string" ? role === "writer" : role.code === "writer",
				);

				if (hasWriterRole) {
					// 设置writer角色标记
					localStorage.setItem("user_role", "writer");
					console.log("用户具有writer角色，已设置角色标记");
				} else {
					// 清除writer角色标记，确保不会使用writer布局
					localStorage.removeItem("user_role");
					console.log("用户不具有writer角色，已清除角色标记");
				}
			} catch (error: any) {
				console.log("error", error);
				// if (error.message && error.message === "CustomError") {
				// 	const response = error.response || { data: { code: ResultCodeEnum.LOGININVALID, msg: "" } };
				// const { code, msg } = response.data;
				// 	if (code === ResultCodeEnum.LOGININVALID) {
				// 		result.code = 1;
				// 	} else {
				// 		result.code = 2;
				// 	}
				// 	result.msg = msg;
				// } else {
				// 	result.code = 999;
				// 	result.msg = error;
				// }
			}
			return result;
		},
		/**
		 * @description: 重置用户信息
		 */
		reset() {
			this.id = 0;
			this.name = "";
			this.roles = [];
		},
		setToken(token: string) {
			this.token = token;
			localStorage.setItem("token", token);
		},
		clearToken() {
			this.token = "";
			localStorage.removeItem("token");
		},
		clearUserInfo() {
			this.userId = null;
			this.username = "";
			this.nickname = "";
			this.avatar = "";
			this.roles = [];
			this.permissions = [];
		},
		logout() {
			this.clearToken();
			this.clearUserInfo();
			// 清除用户角色信息
			localStorage.removeItem("user_role");
		},
	},
});
