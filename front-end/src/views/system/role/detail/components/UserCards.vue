<template>
	<div class="user-cards-container">
		<div class="filter-row">
			<el-input
				v-model="searchQuery"
				placeholder="搜索卡牌"
				clearable
				prefix-icon="Search"
				@input="handleSearch"
				class="search-input"
			/>
			<div class="filter-group">
				<el-select
					v-model="filterRarity"
					placeholder="按稀有度筛选"
					clearable
					@change="handleFilter"
					style="width: 400px"
				>
					<el-option label="全部稀有度" value="" />
					<el-option v-for="item in rarityOptions" :key="item.value" :label="item.label" :value="item.value" />
				</el-select>
				<el-select v-model="filterSeries" placeholder="按系列筛选" clearable @change="handleFilter">
					<el-option label="全部系列" value="" />
					<el-option v-for="item in seriesOptions" :key="item.value" :label="item.label" :value="item.value" />
				</el-select>
				<el-select v-model="sortOrder" placeholder="排序方式" @change="handleSort">
					<el-option label="获取时间 (新→旧)" value="obtain_time_desc" />
					<el-option label="获取时间 (旧→新)" value="obtain_time_asc" />
					<el-option label="使用次数 (多→少)" value="use_count_desc" />
					<el-option label="使用次数 (少→多)" value="use_count_asc" />
				</el-select>
			</div>
		</div>
		<el-empty v-if="loading" description="加载中..." />
		<el-empty v-else-if="filteredCards.length === 0" description="暂无卡牌" />
		<div v-else class="cards-grid">
			<div
				v-for="userCard in filteredCards"
				:key="`${userCard.user_id}-${userCard.card_id}-${userCard.id}`"
				class="card-item"
			>
				<el-card :body-style="{ padding: '0px' }" shadow="hover">
					<div class="card-image-container">
						<el-image :src="userCard.card_detail.image_url" fit="cover" :lazy="true" class="card-image">
							<template #error>
								<div class="image-placeholder">
									<el-icon><Picture /></el-icon>
								</div>
							</template>
						</el-image>
						<div class="card-rarity" :class="`rarity-${userCard.card_detail.rarity}`">
							{{ getRarityLabel(userCard.card_detail.rarity) }}
						</div>
						<div v-if="userCard.is_duplicate" class="card-duplicate">重复</div>
					</div>

					<div class="card-content">
						<div class="card-name">{{ userCard.card_detail.name }}</div>
						<div class="card-meta">
							<span class="obtain-type" :class="userCard.source_type">
								{{ getObtainTypeLabel(userCard.source_type) }}
							</span>
							<span class="obtain-time">{{ formatDate(userCard.create_time) }}</span>
						</div>

						<div v-if="userCard.points_gained" class="points-gained">
							<el-icon><Money /></el-icon> +{{ userCard.points_gained }}
						</div>

						<div class="card-actions">
							<el-tooltip content="使用次数">
								<span class="use-count">
									<el-icon><VideoPlay /></el-icon> {{ userCard.use_count || 0 }}
								</span>
							</el-tooltip>
							<!--							<el-tooltip :content="userCard.is_favorite ? '取消收藏' : '收藏'">-->
							<!--								<el-button-->
							<!--									:type="userCard.is_favorite ? 'danger' : 'default'"-->
							<!--									:icon="userCard.is_favorite ? 'Star' : 'StarFilled'"-->
							<!--									circle-->
							<!--									size="small"-->
							<!--									@click="toggleFavorite(userCard)"-->
							<!--								/>-->
							<!--							</el-tooltip>-->
						</div>
					</div>
				</el-card>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from "vue";
import { getUserCardsByUserId } from "@/api/user-card";
import { ElMessage } from "element-plus";
import { Picture, VideoPlay, Money } from "@element-plus/icons-vue";
import { formatDate } from "@/utils";
const props = defineProps({
	userId: {
		type: Number,
		required: true,
	},
});

// 数据状态
const loading = ref(true);
const userCards = ref<any[]>([]);

// 筛选和排序状态
const searchQuery = ref("");
const filterRarity = ref("");
const filterSeries = ref("");
const sortOrder = ref("obtain_time_desc");

// 选项数据
const rarityOptions = ref([
	{ value: "1", label: "普通" },
	{ value: "2", label: "稀有" },
	{ value: "3", label: "史诗" },
	{ value: "4", label: "传说" },
	{ value: "5", label: "SSR" },
]);
const seriesOptions = ref([
	// 系列选项将从卡牌数据中动态获取
]);

// 筛选后的卡牌列表
const filteredCards = computed(() => {
	let filtered = [...userCards.value];

	// 根据搜索关键字过滤
	if (searchQuery.value) {
		const query = searchQuery.value.toLowerCase();
		filtered = filtered.filter((card) => {
			const cardName = card.card_detail?.name?.toLowerCase() || "";
			return cardName.includes(query);
		});
	}

	// 根据稀有度过滤
	if (filterRarity.value) {
		filtered = filtered.filter((card) => {
			const rarity = card.card_detail?.rarity;
			return rarity === parseInt(filterRarity.value);
		});
	}

	// 根据系列过滤
	if (filterSeries.value) {
		filtered = filtered.filter((card) => {
			const seriesId = card.card_detail?.series_id;
			return seriesId === parseInt(filterSeries.value);
		});
	}

	// 根据排序方式排序
	filtered.sort((a, b) => {
		switch (sortOrder.value) {
			case "obtain_time_desc":
				return new Date(b.create_time).getTime() - new Date(a.create_time).getTime();
			case "obtain_time_asc":
				return new Date(a.create_time).getTime() - new Date(b.create_time).getTime();
			case "use_count_desc":
				return (b.use_count || 0) - (a.use_count || 0);
			case "use_count_asc":
				return (a.use_count || 0) - (b.use_count || 0);
			default:
				return 0;
		}
	});

	return filtered;
});

// 监听用户ID变化，重新加载数据
watch(
	() => props.userId,
	(newVal) => {
		if (newVal) {
			loadUserCards();
		}
	},
);

// 方法
const loadUserCards = async () => {
	if (!props.userId) return;

	loading.value = true;
	try {
		const response = await getUserCardsByUserId(props.userId);
		userCards.value = response;
		// 从卡牌数据中提取系列选项
		const seriesMap = new Map();
		userCards.value.forEach((card) => {
			if (card.card_detail?.series_id) {
				seriesMap.set(card.card_detail.series_id, true);
			}
		});
		seriesOptions.value = Array.from(seriesMap.keys()).map((id) => ({
			value: id.toString(),
			label: `系列 ${id}`,
		}));
	} catch (error) {
		console.error("加载用户卡牌失败", error);
		ElMessage.error("加载用户卡牌失败");
	} finally {
		loading.value = false;
	}
};

const getRarityLabel = (rarity: number): string => {
	switch (rarity) {
		case 1:
			return "普通";
		case 2:
			return "稀有";
		case 3:
			return "史诗";
		case 4:
			return "传说";
		case 5:
			return "SSR";
		default:
			return "未知";
	}
};

const getObtainTypeLabel = (obtainType: string): string => {
	switch (obtainType) {
		case "points":
			return "积分解锁";
		case "blind_box":
			return "盲盒抽取";
		case "reward":
			return "奖励获得";
		default:
			return obtainType;
	}
};

const handleSearch = () => {
	// 搜索操作已由 computed 属性处理
};

const handleFilter = () => {
	// 筛选操作已由 computed 属性处理
};

const handleSort = () => {
	// 排序操作已由 computed 属性处理
};

// 生命周期钩子
onMounted(() => {
	loadUserCards();
});
</script>

<style scoped>
.user-cards-container {
	padding: 20px 0;
}

.filter-row {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 20px;
}

.search-input {
	width: 200px;
}

.filter-group {
	display: flex;
	gap: 10px;
}

.cards-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
	gap: 20px;
}

.card-item {
	transition: all 0.3s;
}

.card-item:hover {
	transform: translateY(-5px);
}

.card-image-container {
	position: relative;
	height: 160px;
	overflow: hidden;
}

.card-image {
	width: 100%;
	height: 100%;
	object-fit: cover;
}

.image-placeholder {
	display: flex;
	align-items: center;
	justify-content: center;
	height: 100%;
	background-color: #f5f7fa;
	font-size: 48px;
	color: #909399;
}

.card-rarity {
	position: absolute;
	top: 10px;
	right: 10px;
	padding: 2px 8px;
	border-radius: 4px;
	font-size: 12px;
	font-weight: bold;
	color: white;
	background-color: #909399;
}

.card-duplicate {
	position: absolute;
	top: 10px;
	left: 10px;
	padding: 2px 8px;
	border-radius: 4px;
	font-size: 12px;
	font-weight: bold;
	color: white;
	background-color: #f56c6c;
}

.rarity-1 {
	background-color: #909399;
} /* 普通 */
.rarity-2 {
	background-color: #409eff;
} /* 稀有 */
.rarity-3 {
	background-color: #67c23a;
} /* 史诗 */
.rarity-4 {
	background-color: #e6a23c;
} /* 传说 */
.rarity-5 {
	background-color: #f56c6c;
} /* SSR */

.card-content {
	padding: 12px;
}

.card-name {
	font-size: 16px;
	font-weight: bold;
	margin-bottom: 8px;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

.card-meta {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 10px;
	font-size: 12px;
	color: #606266;
}

.obtain-type {
	padding: 2px 6px;
	border-radius: 3px;
	font-size: 10px;
}

.obtain-type.points {
	background-color: #ecf5ff;
	color: #409eff;
}

.obtain-type.blind_box {
	background-color: #f0f9eb;
	color: #67c23a;
}

.obtain-type.reward {
	background-color: #fdf6ec;
	color: #e6a23c;
}

.points-gained {
	display: flex;
	align-items: center;
	gap: 4px;
	font-size: 14px;
	font-weight: bold;
	color: #67c23a;
	margin-bottom: 8px;
}

.card-actions {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.use-count {
	display: flex;
	align-items: center;
	gap: 4px;
	font-size: 12px;
	color: #606266;
}
</style>
