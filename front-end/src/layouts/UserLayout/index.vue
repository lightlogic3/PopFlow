<script lang="ts" setup>
import { watch } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();

// 简单设置页面标题
watch(
	() => route.meta.title,
	(title) => {
		document.title = (title as string) || "登录";
	},
	{ immediate: true },
);
</script>

<template>
	<div class="user-layout">
		<router-view />
	</div>
</template>

<style scoped lang="scss">
.user-layout {
	position: relative;
	display: flex;
	align-items: center;
	justify-content: center;
	height: 100vh;
	background-image: url("../../assets/images/bg.svg");
	// background-image: url("../../assets/images/bg.jpg");
	background-repeat: no-repeat;
	background-attachment: fixed;
	background-position: 50%;
	background-size: cover;
}
</style>
