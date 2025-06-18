<template>
	<div class="user-detail-container">
		<div class="header">
			<el-button type="text" @click="goBack" class="back-button">
				<el-icon>
					<ArrowLeft />
				</el-icon>
				返回列表
			</el-button>
			<h1 class="title">用户详情</h1>
		</div>

		<!-- 用户基本信息 -->
		<UserInfo :user="user" :loading="loading" />

		<!-- Tabs容器 -->
		<el-card class="tabs-container">
			<el-tabs v-model="activeTab" @tab-change="handleTabChange" type="border-card">
				<!-- 卡牌列表 -->
				<el-tab-pane label="卡牌列表" name="cards">
					<UserCards :userId="userId" :loading="cardsLoading" />
				</el-tab-pane>

				<!-- 挑战记录 -->
				<el-tab-pane label="挑战记录" name="challenges">
					<UserChallenges :userId="userId" :loading="challengesLoading" />
				</el-tab-pane>

				<!-- 盲盒记录 -->
				<el-tab-pane label="盲盒记录" name="blindBoxes">
					<UserBlindBoxes :userId="userId" :loading="blindBoxesLoading" />
				</el-tab-pane>

				<!-- 盲盒概率统计 -->
				<el-tab-pane label="盲盒概率统计" name="blindBoxStats">
					<UserBlindBoxStats :userId="userId" :loading="blindBoxStatsLoading" />
				</el-tab-pane>

				<!-- 积分变动记录 -->
				<el-tab-pane label="积分变动记录" name="pointRecords">
					<UserPointRecords :userId="userId" :loading="pointRecordsLoading" />
				</el-tab-pane>
			</el-tabs>
		</el-card>
	</div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ArrowLeft } from "@element-plus/icons-vue";
import { getUserDetail } from "@/api/userDetail";

// 引入子组件
import UserInfo from "./components/UserInfo.vue";
import UserCards from "./components/UserCards.vue";
import UserChallenges from "./components/UserChallenges.vue";
import UserBlindBoxes from "./components/UserBlindBoxes.vue";
import UserBlindBoxStats from "./components/UserBlindBoxStats.vue";
import UserPointRecords from "./components/UserPointRecords.vue";

const route = useRoute();
const router = useRouter();
const userId = ref(route.params.id as any);
const loading = ref(false);
const user = ref(null);

// Tab相关
const activeTab = ref(localStorage.getItem("userDetailActiveTab") || "cards");

// 各Tab加载状态
const cardsLoading = ref(false);
const challengesLoading = ref(false);
const blindBoxesLoading = ref(false);
const blindBoxStatsLoading = ref(false);
const pointRecordsLoading = ref(false);

/**
 * 获取用户详情
 */
const fetchUserDetail = async () => {
	loading.value = true;
	try {
		const response = await getUserDetail(userId.value);
		user.value = response;
	} catch (error) {
		console.error("获取用户详情失败", error);
	} finally {
		loading.value = false;
	}
};

/**
 * 返回用户列表页
 */
const goBack = () => {
	router.push("/user-detail");
};

/**
 * 处理tab切换
 */
const handleTabChange = (tabName: string) => {
	activeTab.value = tabName;
	localStorage.setItem("userDetailActiveTab", tabName);
};

/**
 * 组件挂载时加载数据
 */
onMounted(() => {
	fetchUserDetail();
});
</script>

<style scoped lang="scss">
.user-detail-container {
	padding: 20px;

	.header {
		display: flex;
		align-items: center;
		margin-bottom: 20px;

		.back-button {
			display: flex;
			align-items: center;
			gap: 5px;
			margin-right: 20px;
		}

		.title {
			font-size: 24px;
			font-weight: 500;
			margin: 0;
		}
	}

	.tabs-container {
		margin-bottom: 20px;

		:deep(.el-tabs__content) {
			padding: 20px;
			min-height: 500px;
		}
	}
}
</style>
