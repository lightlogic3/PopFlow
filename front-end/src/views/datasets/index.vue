<template>
	<div class="app-container">
		<router-view />
	</div>
</template>

<script setup lang="ts">
/**
 * 数据集管理模块入口组件
 * @description 基于Vue 3 Composition API和TypeScript的数据集管理模块
 */
defineOptions({
	name: "DatasetsManagement",
});
</script>

<style lang="scss" scoped>
.app-container {
	height: 100%;
	width: 100%;
	padding: 20px;
	box-sizing: border-box;
}
</style>
