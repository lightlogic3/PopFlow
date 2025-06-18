<template>
	<div class="user-info-container" v-loading="loading">
		<el-card class="user-info-card">
			<div class="user-header">
				<!-- 左侧：头像和基本信息 -->
				<div class="user-basic">
					<div class="user-avatar">
						<el-avatar :size="64" :src="user?.avatar_url" class="avatar-image">
							{{ user?.user_id?.toString().charAt(0).toUpperCase() || "U" }}
						</el-avatar>
					</div>
					<div class="user-info">
						<h2 class="user-name">用户 {{ user?.user_id || "未知" }}</h2>
						<p class="user-id">ID: {{ user?.id || "N/A" }}</p>
						<div class="user-badges">
							<el-tag size="small" type="success" v-if="user?.total_points > 1000">高积分用户</el-tag>
							<el-tag size="small" type="primary" v-if="user?.total_login_count > 30">活跃用户</el-tag>
							<el-tag size="small" type="warning" v-if="user?.challenge_success_rate > 70">挑战达人</el-tag>
							<el-tag size="small" type="info" v-if="user?.total_card_count > 20">收藏家</el-tag>
						</div>
					</div>
				</div>

				<!-- 右侧：统计信息 -->
				<div class="user-stats">
					<div class="stat-card">
						<div class="stat-icon points-icon">
							<el-icon><CreditCard /></el-icon>
						</div>
						<div class="stat-content">
							<div class="stat-value">{{ formatNumber(user?.total_points) || 0 }}</div>
							<div class="stat-label">总积分</div>
						</div>
					</div>
					<div class="stat-card">
						<div class="stat-icon activity-icon">
							<el-icon><Reading /></el-icon>
						</div>
						<div class="stat-content">
							<div class="stat-value">{{ activityLevel }}%</div>
							<div class="stat-label">活跃度</div>
						</div>
					</div>
				</div>
			</div>

			<!-- 详细信息区域 -->
			<div class="user-detail-grid">
				<!-- 积分信息 -->
				<div class="detail-item">
					<div class="detail-icon">
						<el-icon><CreditCard /></el-icon>
					</div>
					<div class="detail-content">
						<div class="detail-label">可用积分</div>
						<div class="detail-value">{{ formatNumber(user?.available_points) || 0 }}</div>
					</div>
				</div>

				<!-- 卡牌信息 -->
				<div class="detail-item">
					<div class="detail-icon">
						<el-icon><Collection /></el-icon>
					</div>
					<div class="detail-content">
						<div class="detail-label">卡牌数量</div>
						<div class="detail-value">{{ formatNumber(user?.total_card_count) || 0 }}</div>
					</div>
				</div>

				<!-- 挑战信息 -->
				<div class="detail-item">
					<div class="detail-icon">
						<el-icon><Aim /></el-icon>
					</div>
					<div class="detail-content">
						<div class="detail-label">挑战成功率</div>
						<div class="detail-value">{{ user?.challenge_success_rate || 0 }}%</div>
					</div>
				</div>

				<!-- 盲盒信息 -->
				<div class="detail-item">
					<div class="detail-icon">
						<el-icon><Box /></el-icon>
					</div>
					<div class="detail-content">
						<div class="detail-label">盲盒开启数</div>
						<div class="detail-value">{{ formatNumber(user?.total_blind_box_opened) || 0 }}</div>
					</div>
				</div>

				<!-- 登录次数 -->
				<div class="detail-item">
					<div class="detail-icon">
						<el-icon><User /></el-icon>
					</div>
					<div class="detail-content">
						<div class="detail-label">登录次数</div>
						<div class="detail-value">{{ formatNumber(user?.total_login_count) || 0 }}</div>
					</div>
				</div>

				<!-- 最后活跃时间 -->
				<div class="detail-item">
					<div class="detail-icon">
						<el-icon><Clock /></el-icon>
					</div>
					<div class="detail-content">
						<div class="detail-label">最后活跃</div>
						<div class="detail-value">{{ formatDate(user?.last_active_time) || "未知" }}</div>
					</div>
				</div>
			</div>
		</el-card>
	</div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { User, Reading, Clock, CreditCard, Box, Collection, Aim } from "@element-plus/icons-vue";
import { formatDate } from "@/utils";

/**
 * 组件属性定义
 */
const props = defineProps({
	user: {
		type: Object,
		default: () => null,
	},
	loading: {
		type: Boolean,
		default: false,
	},
});

/**
 * 用户活跃度计算
 */
const activityLevel = computed(() => {
	if (!props.user) return 0;

	const loginWeight = Math.min(props.user.total_login_count / 100, 1) * 30;
	const challengeWeight = Math.min(props.user.total_ai_challenge_count / 50, 1) * 30;
	const cardWeight = Math.min(props.user.total_card_count / 20, 1) * 20;
	const boxWeight = Math.min(props.user.total_blind_box_opened / 10, 1) * 20;

	return Math.round(loginWeight + challengeWeight + cardWeight + boxWeight);
});

/**
 * 格式化数字
 */
const formatNumber = (num) => {
	if (num === undefined || num === null) return "0";
	return num.toLocaleString();
};
</script>

<style scoped>
.user-info-container {
	margin-bottom: 20px;
}

.user-info-card {
	background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
	border: 1px solid #e2e8f0;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	transition: all 0.3s ease;
}

.user-header {
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
	margin-bottom: 16px;
	padding-bottom: 16px;
	border-bottom: 1px solid #e2e8f0;
}

/* 基本信息区域 */
.user-basic {
	display: flex;
	gap: 16px;
	align-items: center;
}

.avatar-image {
	border: 2px solid #e2e8f0;
	background-color: #3b82f6;
	color: white;
	font-weight: bold;
	font-size: 24px;
}

.user-name {
	font-size: 20px;
	margin: 0 0 4px 0;
	font-weight: 600;
	color: #1e293b;
}

.user-id {
	font-size: 13px;
	color: #64748b;
	margin: 0 0 8px 0;
}

.user-badges {
	display: flex;
	flex-wrap: wrap;
	gap: 6px;
}

/* 统计卡片 */
.user-stats {
	display: flex;
	gap: 12px;
}

.stat-card {
	display: flex;
	align-items: center;
	gap: 10px;
	background: #f8fafc;
	border: 1px solid #e2e8f0;
	border-radius: 8px;
	padding: 10px;
	min-width: 100px;
}

.stat-icon {
	width: 32px;
	height: 32px;
	border-radius: 8px;
	background: linear-gradient(135deg, #3b82f6, #2563eb);
	color: white;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 16px;
}

.points-icon {
	background: linear-gradient(135deg, #f59e0b, #d97706);
}

.activity-icon {
	background: linear-gradient(135deg, #10b981, #059669);
}

.stat-content {
	text-align: left;
}

.stat-value {
	font-size: 18px;
	font-weight: 600;
	color: #1e293b;
	line-height: 1.2;
}

.stat-label {
	font-size: 12px;
	color: #64748b;
}

/* 详细信息网格 */
.user-detail-grid {
	display: grid;
	grid-template-columns: repeat(3, 1fr);
	gap: 12px;
}

.detail-item {
	display: flex;
	align-items: center;
	gap: 10px;
	background: #f8fafc;
	border: 1px solid #e2e8f0;
	border-radius: 6px;
	padding: 10px;
}

.detail-icon {
	width: 28px;
	height: 28px;
	border-radius: 6px;
	background: rgba(59, 130, 246, 0.1);
	color: #3b82f6;
	display: flex;
	align-items: center;
	justify-content: center;
}

.detail-content {
	flex: 1;
}

.detail-label {
	font-size: 12px;
	color: #64748b;
	margin-bottom: 2px;
}

.detail-value {
	font-size: 14px;
	font-weight: 600;
	color: #1e293b;
}

/* 响应式设计 */
@media (max-width: 768px) {
	.user-header {
		flex-direction: column;
		gap: 16px;
	}

	.user-stats {
		width: 100%;
		justify-content: space-between;
	}

	.user-detail-grid {
		grid-template-columns: repeat(2, 1fr);
	}
}

@media (max-width: 480px) {
	.user-detail-grid {
		grid-template-columns: 1fr;
	}
}
</style>
