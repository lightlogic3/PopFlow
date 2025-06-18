<script setup lang="ts">
import { computed } from "vue";
import { User, Setting } from "@element-plus/icons-vue";
import type { Role } from "@/types/role";

/**
 * Component properties definition
 * @typedef {Object} Props
 * @property {Role} role - Role information object
 * @property {boolean} loading - Loading status
 */
const props = defineProps<{
	role: Role;
	loading: boolean;
}>();

/**
 * Role type tag mapping
 */
const roleTypeMap = {
	main: { label: "Main Character", type: "primary" },
	supporting: { label: "Supporting Character", type: "success" },
	npc: { label: "NPC", type: "info" },
	system: { label: "System Role", type: "warning" },
};

/**
 * Worldview control method mapping
 */
const worldviewControlMap = {
	system_prompt: "System Prompt",
	knowledge_base: "Knowledge Base Driven",
	hybrid: "Hybrid Mode",
};

/**
 * Calculate role completeness
 */
const completeness = computed(() => {
	if (!props.role) return 0;
	let score = 0;
	if (props.role.name) score += 20;
	if (props.role.image_url) score += 20;
	if (props.role.knowledge_count > 0) score += 30;
	if (props.role.llm_choose) score += 20;
	if (props.role.tags) score += 10;
	return score;
});
</script>

<template>
	<div class="role-info-container" v-loading="loading">
		<el-card class="role-info-card">
			<div class="role-header">
				<!-- Left side: Avatar and basic information -->
				<div class="role-basic">
					<div class="role-avatar">
						<el-avatar :size="80" :src="role?.image_url" class="avatar-image">
							<el-icon><User /></el-icon>
						</el-avatar>
						<div class="avatar-overlay">
							<el-tag :type="roleTypeMap[role?.role_type]?.type || 'info'" class="role-type-tag">
								{{ roleTypeMap[role?.role_type]?.label || role?.role_type || "Unknown Type" }}
							</el-tag>
						</div>
					</div>
					<div class="role-info">
						<h2 class="role-name">{{ role?.name || "Unnamed Character" }}</h2>
						<p class="role-id">ID: {{ role?.role_id || "N/A" }}</p>
						<div class="role-tags" v-if="role?.tags">
							<el-tag
								v-for="tag in (role.tags || '').split(',').filter((t) => t.trim())"
								:key="tag"
								size="small"
								class="tag-item"
							>
								{{ tag.trim() }}
							</el-tag>
						</div>
					</div>
				</div>

				<!-- Right side: Statistics -->
				<div class="role-stats">
					<div class="stat-card">
						<div class="stat-icon">
							<el-icon><Database /></el-icon>
						</div>
						<div class="stat-content">
							<div class="stat-value">{{ role?.knowledge_count || 0 }}</div>
							<div class="stat-label">Knowledge Items</div>
						</div>
					</div>
					<div class="stat-card">
						<div class="stat-icon completeness-icon">
							<el-icon><Setting /></el-icon>
						</div>
						<div class="stat-content">
							<div class="stat-value">{{ completeness }}%</div>
							<div class="stat-label">Completeness</div>
						</div>
					</div>
				</div>
			</div>

			<!-- Technical information area -->
			<div class="role-tech-info">
				<div class="tech-item">
					<div class="tech-label">
						<el-icon><Bot /></el-icon>
						<span>LLM Model</span>
					</div>
					<div class="tech-value">{{ role?.llm_choose || "Not Set" }}</div>
				</div>
				<div class="tech-item">
					<div class="tech-label">
						<el-icon><Setting /></el-icon>
						<span>Worldview Control</span>
					</div>
					<div class="tech-value">
						{{ worldviewControlMap[role?.worldview_control] || role?.worldview_control || "Not Set" }}
					</div>
				</div>
			</div>
		</el-card>
	</div>
</template>

<style scoped>
.role-info-container {
	margin: 20px;
}

.role-info-card {
	background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
	border: 1px solid #e2e8f0;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	transition: all 0.3s ease;
}

.role-info-card:hover {
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
	border-color: #2563eb;
}

/* Header area */
.role-header {
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
	margin-bottom: 24px;
	padding-bottom: 20px;
	border-bottom: 1px solid #e2e8f0;
}

/* Basic information area */
.role-basic {
	display: flex;
	gap: 20px;
	align-items: flex-start;
}

.role-avatar {
	position: relative;
}

.avatar-image {
	border: 3px solid #e2e8f0;
	box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.avatar-overlay {
	position: absolute;
	bottom: -8px;
	left: 50%;
	transform: translateX(-50%);
}

.role-type-tag {
	font-size: 12px;
	border-radius: 12px;
	padding: 4px 8px;
}

.role-info {
	flex: 1;
}

.role-name {
	font-size: 28px;
	margin: 0 0 8px 0;
	color: #1e293b;
	font-weight: 700;
	background: linear-gradient(135deg, #2563eb, #1e40af);
	background-clip: text;
	-webkit-background-clip: text;
	-webkit-text-fill-color: transparent;
}

.role-id {
	font-size: 14px;
	color: #64748b;
	margin: 0 0 12px 0;
	font-family: "Courier New", monospace;
}

.role-tags {
	display: flex;
	flex-wrap: wrap;
	gap: 6px;
}

.tag-item {
	border-radius: 12px;
	font-size: 12px;
}

/* Statistic cards */
.role-stats {
	display: flex;
	gap: 16px;
}

.stat-card {
	display: flex;
	align-items: center;
	gap: 12px;
	background: #f8fafc;
	border: 1px solid #e2e8f0;
	border-radius: 12px;
	padding: 16px;
	min-width: 120px;
	transition: all 0.3s ease;
}

.stat-card:hover {
	background: #f1f5f9;
	border-color: #2563eb;
	transform: translateY(-2px);
}

.stat-icon {
	width: 40px;
	height: 40px;
	border-radius: 10px;
	background: linear-gradient(135deg, #2563eb, #3b82f6);
	color: white;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 18px;
}

.completeness-icon {
	background: linear-gradient(135deg, #10b981, #059669);
}

.stat-content {
	text-align: center;
}

.stat-value {
	font-size: 24px;
	font-weight: 700;
	color: #1e293b;
	line-height: 1;
}

.stat-label {
	font-size: 12px;
	color: #64748b;
	margin-top: 4px;
}

/* Technical information area */
.role-tech-info {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 16px;
	margin-bottom: 20px;
	padding-bottom: 20px;
	border-bottom: 1px solid #e2e8f0;
}

.tech-item {
	background: #f8fafc;
	border-radius: 8px;
	padding: 14px;
	border: 1px solid #e2e8f0;
}

.tech-label {
	display: flex;
	align-items: center;
	gap: 8px;
	font-size: 13px;
	color: #64748b;
	margin-bottom: 6px;
	font-weight: 500;
}

.tech-value {
	font-size: 14px;
	color: #1e293b;
	font-weight: 600;
	font-family: "Courier New", monospace;
}

/* Time information area */
.role-time-info {
	display: flex;
	justify-content: space-between;
	margin-bottom: 20px;
	padding: 12px;
	background: #f8fafc;
	border-radius: 8px;
	border: 1px solid #e2e8f0;
}

.time-item {
	display: flex;
	align-items: center;
	gap: 6px;
	font-size: 13px;
	color: #64748b;
}

.time-label {
	font-weight: 500;
}

.time-value {
	color: #1e293b;
	font-weight: 600;
}

/* Completeness progress bar */
.completeness-bar {
	background: #f8fafc;
	border-radius: 8px;
	padding: 16px;
	border: 1px solid #e2e8f0;
}

.completeness-label {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 12px;
	font-size: 14px;
	font-weight: 600;
	color: #1e293b;
}

.completeness-percentage {
	font-size: 16px;
	font-weight: 700;
	color: #2563eb;
}

.progress-bar {
	margin-top: 8px;
}

/* Responsive design */
@media (max-width: 768px) {
	.role-header {
		flex-direction: column;
		gap: 20px;
	}

	.role-basic {
		flex-direction: column;
		align-items: center;
		text-align: center;
	}

	.role-stats {
		justify-content: center;
	}

	.role-tech-info {
		grid-template-columns: 1fr;
	}

	.role-time-info {
		flex-direction: column;
		gap: 8px;
	}
}
</style>
