<script lang="ts">
export default {
	name: "Home",
};
</script>
<script setup lang="ts">
// import { defineAsyncComponent } from "vue";
// import PageLoading from "@/components/PageLoading/index.vue";
// const ArticleChartCard = defineAsyncComponent({
// 	loader: () => import("./components/ArticleChartCard/index.vue"),
// 	loadingComponent: PageLoading,
// });
// const WorksChartCard = defineAsyncComponent({
// 	loader: () => import("./components/WorksChartCard/index.vue"),
// 	loadingComponent: PageLoading,
// });
// const TopicsChartCard = defineAsyncComponent({
// 	loader: () => import("./components/TopicsChartCard/index.vue"),
// 	loadingComponent: PageLoading,
// });
// const LinksChartCard = defineAsyncComponent({
// 	loader: () => import("./components/LinksChartCard/index.vue"),
// 	loadingComponent: PageLoading,
// });
//
// const HotSearchCard = defineAsyncComponent({
// 	loader: () => import("./components/HotSearchCard/index.vue"),
// 	loadingComponent: PageLoading,
// });
// const HotTagsCard = defineAsyncComponent({
// 	loader: () => import("./components/HotTagsCard/index.vue"),
// 	loadingComponent: PageLoading,
// });
//
// const ArticleHitCard = defineAsyncComponent({
// 	loader: () => import("./components/ArticleHitCard/index.vue"),
// 	loadingComponent: PageLoading,
// });
// const WorksHitCard = defineAsyncComponent({
// 	loader: () => import("./components/WorksHitCard/index.vue"),
// 	loadingComponent: PageLoading,
// });
// 编辑器引用
</script>

<template>
	<div>
		<el-empty description="Hello World ~(´•ω•̥` )" />
	</div>
</template>

<style scoped lang="scss">
body {
	margin: 0;
	padding: 0;
	font-family: "Microsoft YaHei", sans-serif;
	background-color: #f9f9f9;
	color: #333;
}

.container {
	max-width: 900px;
	margin: 40px auto;
	padding: 30px;
	background-color: white;
	border-radius: 10px;
	box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

h1 {
	color: #222;
	text-align: center;
	margin-bottom: 30px;
	font-size: 28px;
}

.editor-actions {
	margin-bottom: 15px;
	text-align: right;
}

.default-btn {
	background-color: #1890ff;
	color: white;
	border: none;
	padding: 8px 16px;
	border-radius: 4px;
	cursor: pointer;
	font-size: 14px;
	transition: background-color 0.3s;
}

.default-btn:hover {
	background-color: #40a9ff;
}

.editor-container {
	height: 400px;
	border-radius: 8px;
	overflow: hidden;
	margin-bottom: 20px;
}

.content-preview {
	margin-top: 30px;
	border-top: 1px solid #eee;
	padding-top: 20px;
}

.preview-section {
	margin-bottom: 20px;
}

.content-preview h3 {
	margin-bottom: 15px;
	color: #333;
}

.preview-code {
	background-color: #f5f5f5;
	border-radius: 4px;
	padding: 15px;
	overflow: auto;
	max-height: 200px;
}

.preview-code.plain-text {
	background-color: #f0f7ff;
}

.preview-code pre {
	margin: 0;
	white-space: pre-wrap;
	word-break: break-word;
	color: #444;
	font-family: monospace;
	font-size: 14px;
}
</style>
