<template>
	<div class="user-blind-box-stats">
		<el-card shadow="never" header="用户盲盒统计" v-loading="loading">
			<template v-if="statsData && statsData.length > 0">
				<!-- 盲盒统计列表 -->
				<el-table :data="statsData" stripe style="width: 100%">
					<el-table-column prop="blindBoxName" label="盲盒名称" min-width="180" />
					<el-table-column prop="totalCount" label="总抽取次数" width="100" align="center" />
					<el-table-column prop="currentCount" label="当前保底计数" width="100" align="center" />
					<el-table-column label="上次保底时间" width="180" align="center">
						<template #default="scope">
							{{ formatDateTime(scope.row.lastGuaranteedTime) }}
						</template>
					</el-table-column>
					<el-table-column label="保底状态" min-width="250">
						<template #default="scope">
							<el-tag v-if="scope.row.nextGuarantee" :type="getGuaranteeTagType(scope.row.nextGuarantee.remaining)">
								距离触发保底还需 {{ scope.row.nextGuarantee.remaining }} 次抽卡， 将获得{{
									getRarityText(scope.row.nextGuarantee.rarity)
								}}及以上卡牌
							</el-tag>
							<span v-else>无保底规则</span>
						</template>
					</el-table-column>
					<el-table-column label="操作" width="180" align="center">
						<template #default="scope">
							<el-button type="primary" link size="small" @click="showStatsDetail(scope.row)"> 详细信息 </el-button>
							<el-button type="danger" link size="small" @click="showEditPityModal(scope.row)"> 修改计数 </el-button>
						</template>
					</el-table-column>
				</el-table>
			</template>
			<el-empty v-else description="该用户暂无盲盒统计数据" />
		</el-card>

		<!-- 盲盒详情弹窗 -->
		<el-dialog v-model="detailModalVisible" :title="`盲盒详情 - ${selectedStats?.blindBoxName}`" width="700px">
			<div v-if="selectedStats">
				<el-descriptions :column="2" border>
					<el-descriptions-item label="盲盒ID">{{ selectedStats.blindBoxId }}</el-descriptions-item>
					<el-descriptions-item label="盲盒名称">{{ selectedStats.blindBoxName }}</el-descriptions-item>
					<el-descriptions-item label="总抽取次数">{{ selectedStats.totalCount }}</el-descriptions-item>
					<el-descriptions-item label="当前保底计数">{{ selectedStats.currentCount }}</el-descriptions-item>
					<el-descriptions-item label="上次保底时间" :span="2">
						{{ formatDateTime(selectedStats.lastGuaranteedTime) }}
					</el-descriptions-item>
				</el-descriptions>

				<!-- 保底规则 -->
				<div v-if="selectedStats.guaranteeRules && selectedStats.guaranteeRules.length > 0" class="mt-20">
					<h3>保底规则</h3>
					<el-table :data="selectedStats.guaranteeRules" stripe style="width: 100%">
						<el-table-column prop="count" label="抽卡次数" width="100" />
						<el-table-column label="保底稀有度" width="120">
							<template #default="scope">
								{{ getRarityText(scope.row.guarantee_rarity) }}
							</template>
						</el-table-column>
						<el-table-column prop="description" label="描述" />
					</el-table>
				</div>

				<!-- 下一次保底信息 -->
				<el-alert v-if="selectedStats.nextGuarantee" type="success" :closable="false" show-icon class="mt-20">
					<template #title>
						<div class="next-guarantee-info">
							<span>
								距离触发下一次保底还需
								<b style="font-size: 16px; color: #cf1322">{{ selectedStats.nextGuarantee.remaining }}</b>
								次抽卡
							</span>
							<span>
								将获得稀有度
								<b style="font-size: 16px; color: #1677ff">
									{{ getRarityText(selectedStats.nextGuarantee.rarity) }}
								</b>
								及以上的卡牌
							</span>
							<span v-if="selectedStats.nextGuarantee.description">
								{{ selectedStats.nextGuarantee.description }}
							</span>
						</div>
					</template>
				</el-alert>

				<div class="action-buttons mt-20">
					<el-button @click="simulateDrawIncrease(selectedStats)" type="primary">模拟抽取（增加计数）</el-button>
					<el-button @click="simulateGuaranteedTrigger(selectedStats)" type="danger">模拟触发保底</el-button>
				</div>
			</div>
		</el-dialog>

		<!-- 修改保底计数弹窗 -->
		<el-dialog v-model="editPityModalVisible" :title="`修改保底计数 - ${selectedStats?.blindBoxName}`">
			<el-form :model="editForm" label-position="top">
				<el-form-item label="当前保底计数" prop="currentPityCount">
					<el-input-number v-model="editForm.currentPityCount" :min="0" style="width: 100%" />
				</el-form-item>
				<el-alert type="info" show-icon :closable="false" title="调整保底计数将直接影响用户抽取到稀有卡牌的概率。" />
			</el-form>
			<template #footer>
				<span class="dialog-footer">
					<el-button @click="editPityModalVisible = false">取消</el-button>
					<el-button type="primary" @click="handleEditPity" :loading="editPityLoading">确定</el-button>
				</span>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, PropType } from "vue";
import { ElMessage } from "element-plus";
import {
	getUserAllBlindBoxStats,
	resetPityCounter,
	incrementDrawCount,
	triggerGuaranteed,
} from "@/api/user-blind-box-stats";

// Props
const props = defineProps({
	userId: {
		type: Number as PropType<number>,
		required: true,
	},
});

// 稀有度映射
const rarityMap = {
	1: "普通",
	2: "稀有",
	3: "史诗",
	4: "传说",
};

// 保底规则
interface GuaranteeRule {
	count: number;
	guarantee_rarity: number;
	description: string;
}

// 下一次保底信息
interface NextGuarantee {
	remaining: number;
	rarity: number;
	description: string;
}

// 盲盒统计数据
interface BlindBoxStats {
	id: number;
	blindBoxId: number;
	blindBoxName: string;
	totalCount: number;
	currentCount: number;
	lastGuaranteedTime: string | null;
	guaranteeRules: GuaranteeRule[] | null;
	nextGuarantee: NextGuarantee | null;
}

// 状态
const loading = ref(false);
const statsData = ref<BlindBoxStats[]>([]);
const selectedStats = ref<BlindBoxStats | null>(null);

// 弹窗
const detailModalVisible = ref(false);
const editPityModalVisible = ref(false);
const editPityLoading = ref(false);
const editForm = reactive({
	currentPityCount: 0,
});

// 格式化日期时间
const formatDateTime = (dateStr: string | null) => {
	if (!dateStr) return "无";
	try {
		const date = new Date(dateStr);
		return date.toLocaleString();
	} catch (e) {
		return dateStr;
	}
};

// 获取稀有度文本
const getRarityText = (rarity: number) => {
	return rarityMap[rarity as keyof typeof rarityMap] || `未知(${rarity})`;
};

// 获取保底标签类型
const getGuaranteeTagType = (remaining: number) => {
	if (remaining <= 5) return "danger";
	if (remaining <= 15) return "warning";
	return "info";
};

// 加载用户盲盒统计数据
const loadUserStats = async () => {
	loading.value = true;

	try {
		const res = await getUserAllBlindBoxStats(props.userId);
		statsData.value = res.data.map((item: any) => ({
			id: item.stats.id,
			blindBoxId: item.stats.blind_box_id,
			blindBoxName: item.blind_box_name || `盲盒 #${item.stats.blind_box_id}`,
			totalCount: item.stats.total_count,
			currentCount: item.stats.current_count,
			lastGuaranteedTime: item.stats.last_guaranteed_time,
			guaranteeRules: item.probability_info?.guarantee_rules || null,
			nextGuarantee: item.probability_info?.next_guarantee || null,
		}));
	} catch (error) {
		ElMessage.error("获取用户盲盒统计数据失败");
		console.error(error);
	} finally {
		loading.value = false;
	}
};

// 显示盲盒详情
const showStatsDetail = (stats: BlindBoxStats) => {
	selectedStats.value = stats;
	detailModalVisible.value = true;
};

// 显示编辑保底弹窗
const showEditPityModal = (stats: BlindBoxStats) => {
	selectedStats.value = stats;
	editForm.currentPityCount = stats.currentCount;
	editPityModalVisible.value = true;
};

// 处理编辑保底
const handleEditPity = async () => {
	if (!selectedStats.value) return;

	editPityLoading.value = true;
	try {
		await resetPityCounter(props.userId, selectedStats.value.blindBoxId, editForm.currentPityCount);
		ElMessage.success("保底计数修改成功");
		editPityModalVisible.value = false;

		// 重新加载数据
		await loadUserStats();
	} catch (error) {
		ElMessage.error("保底计数修改失败");
		console.error(error);
	} finally {
		editPityLoading.value = false;
	}
};

// 模拟抽取（增加计数）
const simulateDrawIncrease = async (stats: BlindBoxStats) => {
	try {
		await incrementDrawCount(props.userId, stats.blindBoxId);
		ElMessage.success("模拟抽取成功");
		await loadUserStats();

		// 如果弹窗打开，更新选中的数据
		if (detailModalVisible.value && selectedStats.value) {
			selectedStats.value = statsData.value.find((s) => s.id === stats.id) || null;
		}
	} catch (error) {
		ElMessage.error("操作失败");
		console.error(error);
	}
};

// 模拟触发保底
const simulateGuaranteedTrigger = async (stats: BlindBoxStats) => {
	try {
		await triggerGuaranteed(props.userId, stats.blindBoxId);
		ElMessage.success("模拟触发保底成功");
		await loadUserStats();

		// 如果弹窗打开，更新选中的数据
		if (detailModalVisible.value && selectedStats.value) {
			selectedStats.value = statsData.value.find((s) => s.id === stats.id) || null;
		}
	} catch (error) {
		ElMessage.error("操作失败");
		console.error(error);
	}
};

onMounted(() => {
	loadUserStats();
});
</script>

<style scoped>
.user-blind-box-stats {
	padding: 16px;
}

.action-buttons {
	display: flex;
	gap: 12px;
	justify-content: center;
}

.statistic-value {
	font-size: 24px;
	font-weight: 600;
}

.next-guarantee-info {
	display: flex;
	flex-wrap: wrap;
	gap: 12px;
}

.mt-20 {
	margin-top: 20px;
}

.guarantee-rules {
	margin-top: 10px;
}
</style>
