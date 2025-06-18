<script lang="ts" setup>
import { onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { useUserStore } from "@/store/user";
import PageLoading from "@/components/PageLoading/index.vue";
import { useTooltipStore } from "@/store/tooltip";

const router = useRouter();
const userStore = useUserStore();
// 在应用挂载后预加载提示数据，避免在路由导航期间被取消
const tooltipStore = useTooltipStore();
// 读取当前用户信息
const getUser = async () => {
	const { code, msg } = await userStore.getInfo();
	if (code === 1) {
		// 未登录或登入信息失效
		router.replace({
			path: "/auth/login",
			query: {
				redirect: router.currentRoute.value.path,
				...router.currentRoute.value.query,
			},
		});
	} else {
		if (code !== 0) {
			// 没有获取用户信息成功
			console.log("error msg", msg);
			// alert(msg);
			ElMessage.warning(msg);
			router.replace({
				path: "/user/login",
				query: {
					redirect: router.currentRoute.value.path,
					...router.currentRoute.value.query,
				},
			});
		}
	}

	tooltipStore.fetchTooltipData().catch((error) => {
		// 忽略已取消的请求错误
		if (error?.name !== "CanceledError" && error?.code !== "ERR_CANCELED") {
			console.error("预加载提示数据失败:", error);
		}
	});
};

onMounted(() => {
	getUser();
});
</script>
<template>
	<router-view v-if="userStore.isLogin" />
	<PageLoading v-else />
</template>
