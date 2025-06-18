import request from "@/utils/request";

export async function queryUserInfo(): Promise<any> {
	return request({
		url: "/auth/api/user/info",
		method: "get",
	});
}
