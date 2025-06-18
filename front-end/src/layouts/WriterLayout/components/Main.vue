<script lang="ts" setup>
import { defineProps, ref, onMounted } from "vue";

defineProps({
	routeItem: {
		type: Object,
		default: () => ({}),
	},
});

// 用于控制内容显示状态，防止闪烁
const contentReady = ref(false);

onMounted(() => {
	// 使用短暂延迟确保DOM已完全渲染
	setTimeout(() => {
		contentReady.value = true;
	}, 50);
});
</script>

<template>
	<main class="writer-main">
		<div class="content-wrapper" :class="{ 'content-loaded': contentReady }">
			<router-view v-slot="{ Component }">
				<transition name="fade" mode="out-in">
					<keep-alive>
						<component :is="Component" />
					</keep-alive>
				</transition>
			</router-view>
		</div>
	</main>
</template>

<style lang="scss" scoped></style>
