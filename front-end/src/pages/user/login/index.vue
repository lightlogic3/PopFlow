<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, FormInstance, FormRules } from "element-plus";
import IconSvg from "@/components/IconSvg/index.vue";
import { setToken } from "@/utils/localToken";
import { IResponseData } from "@/@types/utils.request";
import { LoginParamsType } from "./data";
import { accountLogin } from "./server";
const router = useRouter();

const formRef = ref<FormInstance>();
const formData = reactive<LoginParamsType>({
	username: "",
	password: "",
});
const rules = reactive<FormRules>({
	username: [{ required: true, message: "Please enter username", trigger: "blur" }],
	password: [{ required: true, message: "Please enter password", trigger: "blur" }],
});

const loading = ref(false);
const onSubmit = async () => {
	if (loading.value === true) {
		return;
	}
	loading.value = true;
	try {
		const valid: boolean | undefined = await formRef.value?.validate();
		if (valid === true) {
			const response: IResponseData<any> = await accountLogin(formData);
			const data: any = response || {};
			setToken(data.token || "");

			// Ensure writer role marker is cleared
			localStorage.removeItem("user_role");

			ElMessage.success("Login successful");
			const { redirect, ...query } = router.currentRoute.value.query;

			// Handle redirect parameters to avoid nested redirects
			let redirectPath = "/";
			if (redirect) {
				const redirectStr = redirect as string;

				// If nested redirects exist, use only the innermost target path
				if (redirectStr.includes("redirect=")) {
					try {
						const url = new URL(redirectStr, window.location.origin);
						// Remove redirect parameter from URL
						url.searchParams.delete("redirect");
						redirectPath = url.pathname + url.search;
					} catch {
						// Extract path part when parsing fails
						redirectPath = redirectStr.split("?")[0];
					}
				} else {
					redirectPath = redirectStr;
				}

				// Ensure no redirect to login page
				if (redirectPath.includes("/user/login")) {
					redirectPath = "/";
				}
			}

			router.replace({
				path: redirectPath,
				query: {
					...query,
				},
			});
		}
	} catch (error: any) {
		console.log(error);
		const message = error.message;
		if (message === "CustomError") {
			const response = error.response || {};
			const data = response.data || {};
			const msg = data.msg || "";
			ElMessage.error(msg);
		} else {
			// alert(message);
			ElMessage.warning("Validation failed, please check your input");
		}
	}
	loading.value = false;
};
</script>

<template>
	<div class="user-login">
		<el-form ref="formRef" :model="formData" :rules="rules">
			<div class="title">
				<div>Login to</div>
				<div>AI Agent Management Platform</div>
			</div>
			<div class="item">
				<el-form-item prop="username" tooltipKey="username">
					<el-input
						placeholder="Username: admin or test or user"
						v-model="formData.username"
						clearable
						@keydown.enter="onSubmit"
					>
						<template #prefix>
							<IconSvg name="user" />
						</template>
					</el-input>
				</el-form-item>
			</div>
			<div class="item">
				<el-form-item prop="password" tooltipKey="password">
					<el-input
						placeholder="Password: 123456"
						type="password"
						v-model="formData.password"
						clearable
						@keydown.enter="onSubmit"
					>
						<template #prefix>
							<IconSvg name="pwd" />
						</template>
					</el-input>
				</el-form-item>
			</div>
			<div class="item">
				<el-button @click="onSubmit" :loading="loading" class="width100" type="primary">Submit</el-button>
			</div>
		</el-form>
		<div class="item2">
			<a href="#/user/login/writer" class="switch-link">Switch to Writer Login</a>
		</div>
	</div>
</template>

<style scoped lang="scss">
.user-login {
	width: 380px;
	padding-bottom: 40px;
	.title {
		padding: 0 20px 20px;
		font-size: 30px;
		line-height: 50px;
	}
	.item {
		padding: 5px 20px;
		.width100 {
			box-sizing: border-box;
			width: 100%;
		}
	}
	.item2 {
		padding: 10px 20px;
		font-size: 14px;
		text-align: center;
	}

	.switch-link {
		color: #409eff;
		text-decoration: none;
		&:hover {
			text-decoration: underline;
		}
	}
}
</style>
