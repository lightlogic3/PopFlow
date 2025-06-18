<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import { ElMessage, FormInstance, FormRules } from "element-plus";
import IconSvg from "@/components/IconSvg/index.vue";
import { setToken } from "@/utils/localToken";
import { IResponseData } from "@/@types/utils.request";
import { LoginParamsType } from "./data";
import { accountLogin } from "./server";

const router = useRouter();
const route = useRoute();

const formRef = ref<FormInstance>();
const formData = reactive<LoginParamsType>({
	username: "popflow",
	password: "123456",
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

			// Store user role as writer
			localStorage.setItem("user_role", "writer");

			ElMessage.success("Login successful");
			const { redirect, ...query } = route.query;

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
			ElMessage.warning("Validation failed, please check your input");
		}
	}
	loading.value = false;
};
</script>

<template>
	<div class="writer-login-container">
		<div class="writer-login-box">
			<div class="login-header">
				<div class="login-logo">
					<img src="../../../assets/images/logo.png" alt="Logo" class="logo-image" />
					<div class="logo-text">
						<!-- <h2>Content Creator Platform</h2> -->
						<h2>PopFlow-Second Life AI Engine</h2>
						<p>Make creation smoother, inspiration freer</p>
					</div>
				</div>
			</div>

			<div class="login-form-container">
				<h3 class="form-title">Login</h3>
				<el-form ref="formRef" :model="formData" :rules="rules" class="login-form">
					<el-form-item prop="username">
						<el-input
							placeholder="Username"
							v-model="formData.username"
							clearable
							@keydown.enter="onSubmit"
							class="login-input"
						>
							<template #prefix>
								<IconSvg name="user" />
							</template>
						</el-input>
					</el-form-item>

					<el-form-item prop="password">
						<el-input
							placeholder="Password"
							type="password"
							v-model="formData.password"
							clearable
							@keydown.enter="onSubmit"
							class="login-input"
						>
							<template #prefix>
								<IconSvg name="pwd" />
							</template>
						</el-input>
					</el-form-item>

					<div class="form-actions">
						<el-button @click="onSubmit" :loading="loading" class="login-button" type="primary"> Login </el-button>
					</div>
				</el-form>

				<div class="switch-container">
					<a href="#/user/login?forceLogin=admin" class="switch-link">Switch to Admin Login</a>
				</div>
			</div>
		</div>
	</div>
</template>

<style scoped lang="scss">
.writer-login-container {
	display: flex;
	align-items: center;
	justify-content: center;
	height: 100vh;
	width: 100vw;
	background-image: url("../../../assets/images/bg.jpg");
	background-repeat: no-repeat;
	background-size: cover;
	// background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
	position: relative;
	overflow: hidden;

	&::before {
		content: "";
		position: absolute;
		top: -50%;
		left: -50%;
		width: 200%;
		height: 200%;
		background: radial-gradient(circle, rgba(0, 160, 209, 0.1) 0%, rgba(0, 160, 209, 0) 60%);
		animation: pulse 15s infinite;
	}

	&::after {
		content: "";
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background-image: url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M11 18c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm48 25c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm-43-7c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm63 31c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM34 90c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm56-76c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM12 86c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm28-65c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm23-11c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-6 60c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm29 22c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zM32 63c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm57-13c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-9-21c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM60 91c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM35 41c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM12 60c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2z' fill='%231a3f6f' fill-opacity='0.05' fill-rule='evenodd'/%3E%3C/svg%3E");
		opacity: 0.2;
	}
}

.writer-login-box {
	width: 480px;
	background: rgba(26, 32, 44, 0.7);
	backdrop-filter: blur(10px);
	border-radius: 20px;
	box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
	z-index: 10;
	overflow: hidden;
	color: #fff;
}

.login-header {
	padding: 30px;
	border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.login-logo {
	display: flex;
	align-items: center;

	.logo-image {
		height: 50px;
		width: 50px;
		object-fit: contain;
		margin-right: 15px;
	}

	.logo-text {
		h2 {
			margin: 0;
			color: #ffffff;
			font-size: 20px;
			font-weight: 600;
		}

		p {
			margin: 5px 0 0;
			color: rgba(255, 255, 255, 0.7);
			font-size: 14px;
		}
	}
}

.login-form-container {
	padding: 30px;
}

.form-title {
	color: #ffffff;
	font-size: 24px;
	font-weight: 600;
	margin: 0 0 30px;
	text-align: center;
}

.login-form {
	.login-input {
		:deep(.el-input__inner) {
			background-color: rgba(255, 255, 255, 0.05);
			border: 1px solid rgba(255, 255, 255, 0.1);
			border-radius: 10px;
			color: #ffffff;
			height: 50px;
			padding-left: 15px;
			font-size: 16px;

			&::placeholder {
				color: rgba(255, 255, 255, 0.3);
			}
		}

		:deep(.el-input__prefix) {
			color: rgba(255, 255, 255, 0.5);
			font-size: 18px;
			margin-right: 10px;
		}
	}
}

.form-actions {
	margin-top: 30px;
}

.switch-container {
	margin-top: 20px;
	text-align: center;
}

.switch-link {
	color: rgba(255, 255, 255, 0.7);
	font-size: 14px;
	text-decoration: none;
	transition: color 0.3s;

	&:hover {
		color: #ffffff;
		text-decoration: underline;
	}
}

.login-button {
	width: 100%;
	height: 50px;
	border-radius: 10px;
	font-size: 16px;
	font-weight: 600;
	background: linear-gradient(90deg, #00a0d1 0%, #0077b6 100%);
	border: none;
	transition: all 0.3s;

	&:hover {
		transform: translateY(-2px);
		box-shadow: 0 8px 15px rgba(0, 160, 209, 0.3);
		background: linear-gradient(90deg, #00b4d8 0%, #0096c7 100%);
	}

	&:active {
		transform: translateY(0);
	}
}

@keyframes pulse {
	0% {
		transform: rotate(0deg);
	}
	100% {
		transform: rotate(360deg);
	}
}

/* 响应式处理 */
@media (max-width: 520px) {
	.writer-login-box {
		width: 90%;
		max-width: 480px;
	}

	.login-logo {
		flex-direction: column;
		text-align: center;

		.logo-image {
			margin: 0 0 10px;
		}
	}
}
</style>
