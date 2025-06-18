<!-- WorldInfo.vue - Component to display world basic information -->
<script setup lang="ts">
import { ArrowLeft, Document } from "@element-plus/icons-vue";
import { useRouter } from "vue-router";
import type { World } from "@/types/world";

defineProps<{
	world: World;
	loading: boolean;
}>();

const router = useRouter();

/**
 * Return to world list page
 */
const goBack = () => {
	router.push("/world/list");
};
</script>

<template>
	<div>
		<div class="header">
			<el-button type="text" @click="goBack" class="back-button">
				<el-icon><ArrowLeft /></el-icon>
				Back to List
			</el-button>
			<h1 class="title">World Details</h1>
		</div>

		<!-- World information -->
		<el-card class="world-info-card">
			<div class="world-info">
				<img :src="world.image_url" :alt="world.title" class="world-image" />
				<div class="world-details">
					<el-tag size="small" class="world-type" effect="dark">{{ world.type }}</el-tag>
					<h2 class="world-title">{{ world.title }}</h2>
					<p class="world-description">{{ world.description }}</p>
					<div class="world-stats">
						<div class="stat-item">
							<el-icon><Document /></el-icon>
							<span>Knowledge Entries: {{ world.knowledge_count }}</span>
						</div>
					</div>
					<div class="tag-list" v-if="world.type">
						<el-tag v-for="tag in ['World View', world.type]" :key="tag" size="small" effect="plain">
							{{ tag }}
						</el-tag>
					</div>
				</div>
			</div>
		</el-card>
	</div>
</template>

<style scoped>
.header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 24px;
}

.back-button {
	display: flex;
	align-items: center;
	gap: 5px;
	color: var(--el-color-primary);
}

.title {
	font-size: 24px;
	margin: 0;
	color: var(--el-text-color-primary);
}

.world-info-card {
	margin-bottom: 24px;
}

.world-info {
	display: flex;
	gap: 24px;
}

.world-image {
	width: 300px;
	height: 200px;
	object-fit: cover;
	border-radius: 8px;
}

.world-details {
	flex: 1;
}

.world-type {
	margin-bottom: 12px;
}

.world-title {
	font-size: 24px;
	margin: 0 0 12px 0;
	color: var(--el-text-color-primary);
}

.world-description {
	margin: 0 0 16px 0;
	font-size: 16px;
	color: var(--el-text-color-secondary);
	line-height: 1.6;
}

.world-stats {
	display: flex;
	gap: 24px;
	margin-bottom: 16px;
}

.stat-item {
	display: flex;
	align-items: center;
	gap: 5px;
	color: var(--el-text-color-secondary);
	font-size: 14px;
}
</style>
