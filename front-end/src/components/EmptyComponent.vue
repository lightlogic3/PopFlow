<template>
	<div class="empty-component">
		<el-alert
			title="组件加载失败"
			type="error"
			description="找不到指定的组件，请检查菜单配置是否正确。"
			show-icon
			:closable="false"
		/>
		<div class="error-buttons">
			<el-button type="primary" @click="goToHome">return to the top page</el-button>
			<el-button @click="goBack">back to the previous page</el-button>
		</div>
	</div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";

const router = useRouter();

// 返回首页
const goToHome = () => {
	router.push("/");
};

// 返回上一页
const goBack = () => {
	router.back();
};
</script>

<style scoped>
.empty-component {
	padding: 40px 20px;
	text-align: center;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	height: 100%;
	background-color: rgba(245, 247, 250, 0.9);
}

.error-buttons {
	margin-top: 20px;
	display: flex;
	gap: 10px;
	justify-content: center;
}
</style>
