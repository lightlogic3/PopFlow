<template>
	<el-dialog
		v-model="dialogVisible"
		title="配置盲盒卡牌"
		width="90%"
		:close-on-click-modal="true"
		:close-on-press-escape="true"
		:before-close="handleDialogBeforeClose"
	>
		<div class="card-config-container">
			<!-- 搜索栏 -->
			<div class="card-search-bar">
				<el-input v-model="cardSearchQuery" placeholder="search for the name of the card" style="width: 300px" @input="handleCardSearch">
					<template #prepend>
						<el-icon><Search /></el-icon>
					</template>
				</el-input>
				<el-select v-model="cardRarityFilter" placeholder="rarity filtering" style="width: 150px" @change="handleCardSearch">
					<el-option label="全部" :value="null" />
					<el-option label="普通" :value="1" />
					<el-option label="稀有" :value="2" />
					<el-option label="史诗" :value="3" />
					<el-option label="传说" :value="4" />
				</el-select>
			</div>

			<!-- 已选卡牌统计 -->
			<div class="selected-cards-info" v-if="boundCards.length > 0">
				<el-alert
					:title="`bind ${boundCards.length} 张卡牌，总概率: ${totalProbability.toFixed(2)}%`"
					:type="totalProbability > 100 ? 'error' : totalProbability === 100 ? 'success' : 'warning'"
					:description="
						totalProbability > 100
							? '总概率超过100%，请调整'
							: totalProbability < 100
							? '总概率低于100%，建议调整'
							: '概率配置完美！'
					"
					show-icon
					:closable="false"
				/>
			</div>

			<!-- 卡牌区域 -->
			<div class="card-panels-container">
				<!-- 已绑定卡牌区域 -->
				<div class="bound-cards-panel">
					<div class="panel-header">
						<h3>已绑定卡牌 ({{ boundCards.length }})</h3>
					</div>
					<div class="card-selection-grid" v-loading="loading">
						<div
							v-for="card in boundCards"
							:key="card.card_id"
							class="card-selection-item bound"
							:class="{ expanded: expandedCardId === card.card_id }"
							@click="toggleCardConfig(card.card_id)"
						>
							<div class="card-rarity-badge" :class="`rarity-${card.rarity || 1}`">
								{{ getCardRarityLabel(card.rarity) }}
							</div>
							<div class="card-info-badge">
								<span class="probability-badge">{{ card.probability }}%</span>
								<span v-if="card.is_special_reward" class="special-badge">特殊</span>
							</div>
							<div class="card-image-small">
								<img v-if="card.image_url" :src="card.image_url" :alt="card.name" />
								<div v-else class="no-image-small">
									<i class="el-icon-picture"></i>
								</div>
							</div>
							<div class="card-info">
								<h4>{{ card.name }}</h4>
								<p v-if="card.description">{{ card.description }}</p>
							</div>
							<div class="card-actions">
								<el-button type="danger" size="small" circle @click.stop="unbindCard(card)">
									<el-icon><Delete /></el-icon>
								</el-button>
							</div>

							<!-- 内联卡牌配置 -->
							<div v-if="expandedCardId === card.card_id" class="card-config-inputs" @click.stop>
								<div class="config-label">概率设置 (%)</div>
								<el-input-number
									v-model="card.probability"
									:min="0"
									:max="100"
									:precision="2"
									placeholder="概率%"
									size="small"
									style="width: 100%; margin-bottom: 8px"
									@change="updateCardConfig(card)"
								/>
								<div class="config-label">权重设置</div>
								<el-input-number
									v-model="card.weight"
									:min="1"
									placeholder="权重"
									size="small"
									style="width: 100%; margin-bottom: 8px"
									@change="updateCardConfig(card)"
								/>
								<el-checkbox v-model="card.is_special_reward" size="small" @change="updateCardConfig(card)">
									特殊奖励
								</el-checkbox>
							</div>
						</div>

						<div v-if="boundCards.length === 0" class="empty-state">
							<el-empty description="暂无绑定卡牌" />
						</div>
					</div>
				</div>

				<!-- 未绑定卡牌区域 -->
				<div class="unbound-cards-panel">
					<div class="panel-header">
						<h3>可选卡牌 ({{ unboundTotal }})</h3>
					</div>
					<div class="card-selection-grid" v-loading="loading">
						<div
							v-for="card in unboundCards"
							:key="card.id"
							class="card-selection-item unbound"
							@click="bindCard(card)"
						>
							<div class="card-rarity-badge" :class="`rarity-${card.rarity || 1}`">
								{{ getCardRarityLabel(card.rarity) }}
							</div>
							<div class="card-image-small">
								<img v-if="card.image_url" :src="card.image_url" :alt="card.name" />
								<div v-else class="no-image-small">
									<i class="el-icon-picture"></i>
								</div>
							</div>
							<div class="card-info">
								<h4>{{ card.name }}</h4>
								<p v-if="card.description">{{ card.description }}</p>
							</div>
							<div class="card-actions">
								<el-button type="primary" size="small" circle @click.stop="bindCard(card)">
									<el-icon><Plus /></el-icon>
								</el-button>
							</div>
						</div>

						<div v-if="unboundCards.length === 0" class="empty-state">
							<el-empty description="暂无未绑定卡牌" />
						</div>
					</div>

					<!-- 分页 -->
					<div class="card-pagination" v-if="unboundTotal > 0">
						<el-pagination
							v-model:current-page="unboundCurrentPage"
							v-model:page-size="unboundPageSize"
							:total="unboundTotal"
							:page-sizes="[12, 24, 48]"
							layout="total, sizes, prev, pager, next"
							@size-change="handleUnboundSizeChange"
							@current-change="handleUnboundCurrentChange"
						/>
					</div>
				</div>
			</div>
		</div>

		<template #footer>
			<div class="dialog-footer">
				<el-button @click="handleCancel">关闭</el-button>
				<el-button @click="handleClearAll" type="warning">清空所有</el-button>
			</div>
		</template>
	</el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Delete, Plus, Search } from "@element-plus/icons-vue";
import {
	clearBlindBoxCards,
	getCardBindingStatus,
	deleteBlindBoxCardRelation,
	createBlindBoxCard,
	updateBlindBoxCard,
	type BoundCardItem,
	type UnboundCardItem,
	type BlindBoxCardCreate,
	type BlindBoxCardUpdate,
} from "@/api/blind-box-card";

const props = defineProps({
	blindBoxId: {
		type: Number,
		required: true,
	},
	visible: {
		type: Boolean,
		default: false,
	},
});

const emit = defineEmits(["update:visible", "saved"]);

// 响应式数据
const dialogVisible = ref(false);
const loading = ref(false);
const cardSearchQuery = ref("");
const cardRarityFilter = ref<number | null>(null);

// 已绑定和未绑定卡牌
const boundCards = ref<BoundCardItem[]>([]);
const unboundCards = ref<UnboundCardItem[]>([]);
const unboundTotal = ref(0);
const unboundCurrentPage = ref(1);
const unboundPageSize = ref(12);

// 展开卡片配置的ID
const expandedCardId = ref<number | null>(null);

// 同步props.visible到本地
watch(
	() => props.visible,
	(newVal) => {
		dialogVisible.value = newVal;
		if (newVal && props.blindBoxId) {
			fetchCardBindingStatus();
		}
	},
);

// 同步本地状态到父组件
watch(
	() => dialogVisible.value,
	(newVal) => {
		emit("update:visible", newVal);
	},
);

// 计算属性
const totalProbability = computed(() => {
	try {
		return boundCards.value.reduce((sum, card) => sum + (card.probability || 0), 0);
	} catch (error) {
		console.error("Error calculating total probability:", error);
		return 0;
	}
});

// 获取卡牌绑定状态
const fetchCardBindingStatus = async () => {
	try {
		loading.value = true;
		const params = {
			name: cardSearchQuery.value || undefined,
			rarity: cardRarityFilter.value || undefined,
			page: unboundCurrentPage.value,
			size: unboundPageSize.value,
		};

		const response = await getCardBindingStatus(props.blindBoxId, params);
		boundCards.value = response.bound_cards || [];
		unboundCards.value = response.unbound_cards?.items || [];
		unboundTotal.value = response.unbound_cards?.total || 0;
	} catch (error) {
		ElMessage.error("获取卡牌绑定状态失败");
		console.error("Error fetching card binding status:", error);
	} finally {
		loading.value = false;
	}
};

// 卡牌搜索
const handleCardSearch = () => {
	unboundCurrentPage.value = 1;
	fetchCardBindingStatus();
};

// 未绑定卡牌分页
const handleUnboundSizeChange = (size: number) => {
	unboundPageSize.value = size;
	unboundCurrentPage.value = 1;
	fetchCardBindingStatus();
};

const handleUnboundCurrentChange = (page: number) => {
	unboundCurrentPage.value = page;
	fetchCardBindingStatus();
};

// 稀有度标签
const getCardRarityLabel = (rarity?: number) => {
	const labels: Record<number, string> = {
		1: "普通",
		2: "稀有",
		3: "史诗",
		4: "传说",
	};
	return labels[rarity || 1] || "普通";
};

// 绑定卡牌
const bindCard = async (card: UnboundCardItem) => {
	try {
		if (!props.blindBoxId) {
			ElMessage.error("盲盒ID不能为空");
			return;
		}

		// 创建绑定数据
		const bindData: BlindBoxCardCreate = {
			blind_box_id: props.blindBoxId,
			card_id: card.id,
			probability: 10, // 默认概率
			weight: 1,
			is_special_reward: 0,
		};

		// 调用接口创建绑定关系
		await createBlindBoxCard(bindData);

		// 添加到已绑定列表
		boundCards.value.push({
			blind_box_card_id: 0, // 临时ID，后续刷新会更新
			card_id: card.id,
			name: card.name,
			description: card.description,
			image_url: card.image_url,
			rarity: card.rarity,
			probability: 10, // 默认概率
			weight: 1,
			is_special_reward: false,
		});

		// 从未绑定列表中移除
		unboundCards.value = unboundCards.value.filter((c) => c.id !== card.id);
		unboundTotal.value--;

		// 刷新数据
		fetchCardBindingStatus();

		ElMessage.success("卡牌绑定成功");
	} catch (error) {
		console.error("Error binding card:", error);
		ElMessage.error("卡牌绑定失败");
	}
};

// 解绑卡牌
const unbindCard = async (card: BoundCardItem) => {
	try {
		if (props.blindBoxId && card.blind_box_card_id) {
			// 调用接口删除绑定关系
			await deleteBlindBoxCardRelation(props.blindBoxId, card.card_id);
		}

		// 从已绑定列表中移除
		boundCards.value = boundCards.value.filter((c) => c.card_id !== card.card_id);

		// 如果是展开的卡牌被删除，重置展开状态
		if (expandedCardId.value === card.card_id) {
			expandedCardId.value = null;
		}

		// 重新加载未绑定卡牌列表
		fetchCardBindingStatus();

		ElMessage.success("卡牌解绑成功");
	} catch (error) {
		console.error("Error unbinding card:", error);
		ElMessage.error("卡牌解绑失败");
	}
};

// 切换卡牌配置区域的展开/折叠
const toggleCardConfig = (cardId: number) => {
	if (expandedCardId.value === cardId) {
		expandedCardId.value = null;
	} else {
		expandedCardId.value = cardId;
	}
};

// 清空所有卡牌配置
const handleClearAll = async () => {
	try {
		await ElMessageBox.confirm("确定要清空所有卡牌配置吗？", "提示", {
			confirmButtonText: "确定",
			cancelButtonText: "取消",
			type: "warning",
		});

		if (props.blindBoxId) {
			await clearBlindBoxCards(props.blindBoxId);
			fetchCardBindingStatus();
			ElMessage.success("清空成功");
		}
	} catch (error) {
		if (error !== "cancel") {
			ElMessage.error("清空失败");
		}
	}
};

// 更新卡牌配置
const updateCardConfig = async (card: BoundCardItem) => {
	try {
		if (!card.blind_box_card_id) {
			ElMessage.warning("卡牌信息不完整，无法更新");
			return;
		}

		// 准备更新数据
		const updateData: BlindBoxCardUpdate = {
			probability: card.probability,
			weight: card.weight,
			is_special_reward: card.is_special_reward ? 1 : 0,
		};

		// 调用API更新卡牌配置
		await updateBlindBoxCard(card.blind_box_card_id, updateData);

		// 提示更新成功
		ElMessage.success({
			message: "配置已更新",
			duration: 1000,
		});
	} catch (error) {
		console.error("Error updating card config:", error);
		ElMessage.error("更新卡牌配置失败");
	}
};

// 取消
const handleCancel = () => {
	clearCardConfigData();
	dialogVisible.value = false;
};

// 处理对话框关闭前的逻辑
const handleDialogBeforeClose = (done: () => void) => {
	clearCardConfigData();
	done();
};

// 清理卡牌配置数据
const clearCardConfigData = () => {
	boundCards.value = [];
	unboundCards.value = [];
	unboundTotal.value = 0;
	cardSearchQuery.value = "";
	cardRarityFilter.value = null;
	unboundCurrentPage.value = 1;
	expandedCardId.value = null;
};
</script>

<style lang="scss" scoped>
// 卡牌配置对话框样式
.card-config-container {
	.card-search-bar {
		display: flex;
		gap: 15px;
		margin-bottom: 20px;
		align-items: center;
	}

	.selected-cards-info {
		margin-bottom: 20px;
	}

	.card-panels-container {
		display: flex;
		gap: 20px;
		margin-bottom: 20px;

		.bound-cards-panel,
		.unbound-cards-panel {
			flex: 1;
			background: #f8f9fa;
			border-radius: 12px;
			padding: 15px;
			box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
			min-height: 500px;
			display: flex;
			flex-direction: column;

			.panel-header {
				margin-bottom: 15px;
				border-bottom: 1px solid #e0e0e0;
				padding-bottom: 10px;

				h3 {
					margin: 0;
					color: #333;
					font-size: 16px;
					font-weight: bold;
				}
			}
		}

		.bound-cards-panel {
			border-left: 4px solid #409eff;
		}

		.unbound-cards-panel {
			border-left: 4px solid #67c23a;
		}
	}

	.card-selection-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
		grid-auto-rows: min-content;
		gap: 15px;
		overflow-y: auto;
		flex: 1;
		padding: 10px;

		.card-selection-item {
			position: relative;
			background: #fff;
			border: 2px solid transparent;
			border-radius: 12px;
			padding: 15px;
			cursor: pointer;
			transition: all 0.3s ease;
			align-self: start;
			width: 100%;
			min-height: 160px; /* 设置最小高度，确保按钮等元素有足够空间 */
			box-sizing: border-box;

			/* 清除浮动，确保内容正确包含 */
			&::after {
				content: "";
				display: table;
				clear: both;
			}

			&:hover {
				transform: translateY(-2px);
				box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
			}

			&.bound {
				border-color: #409eff;
				background: #ecf5ff;

				&:hover {
					background: #dbedff;
				}

				&.expanded {
					grid-column: span 2;
					transition: all 0.3s ease;
				}
			}

			&.unbound {
				&:hover {
					border-color: #67c23a;
					background: #f0f9eb;
				}
			}

			.card-rarity-badge {
				position: absolute;
				top: 10px;
				right: 10px;
				padding: 2px 8px;
				border-radius: 12px;
				font-size: 11px;
				font-weight: bold;
				color: white;

				&.rarity-1 {
					background: #95a5a6;
				}
				&.rarity-2 {
					background: #3498db;
				}
				&.rarity-3 {
					background: #9b59b6;
				}
				&.rarity-4 {
					background: #f1c40f;
				}
			}

			.card-info-badge {
				position: absolute;
				top: 10px;
				left: 10px;
				display: flex;
				gap: 5px;

				.probability-badge {
					background: #e6a23c;
					color: white;
					padding: 2px 6px;
					border-radius: 12px;
					font-size: 11px;
					font-weight: bold;
				}

				.special-badge {
					background: #f56c6c;
					color: white;
					padding: 2px 6px;
					border-radius: 12px;
					font-size: 11px;
					font-weight: bold;
				}
			}

			.card-image-small {
				width: 60px;
				height: 60px;
				border-radius: 8px;
				overflow: hidden;
				margin-bottom: 10px;
				background: #f0f2f5;
				display: flex;
				align-items: center;
				justify-content: center;

				img {
					width: 100%;
					height: 100%;
					object-fit: cover;
				}

				.no-image-small {
					color: #bbb;
					i {
						font-size: 24px;
					}
				}
			}

			.card-info {
				h4 {
					margin: 0 0 5px 0;
					font-size: 14px;
					font-weight: bold;
					color: #333;
				}

				p {
					margin: 0;
					font-size: 12px;
					color: #666;
					display: -webkit-box;
					-webkit-line-clamp: 2;
					-webkit-box-orient: vertical;
					overflow: hidden;
				}

				margin-bottom: 25px; /* 为底部按钮留出空间 */
			}

			.card-actions {
				position: absolute;
				bottom: 10px;
				right: 10px;
				opacity: 0;
				transition: opacity 0.3s;
			}

			&:hover .card-actions {
				opacity: 1;
			}

			.card-config-inputs {
				margin-top: 15px;
				padding-top: 15px;
				border-top: 1px solid #e0e0e0;
				background: rgba(64, 158, 255, 0.05);
				border-radius: 8px;
				padding: 15px;

				.config-label {
					font-size: 12px;
					color: #606266;
					margin-bottom: 5px;
					margin-top: 8px;
					font-weight: 500;

					&:first-child {
						margin-top: 0;
					}
				}

				.el-checkbox {
					margin-top: 8px;
				}
			}
		}

		.empty-state {
			grid-column: 1 / -1;
			padding: 40px 20px;
			text-align: center;
		}
	}

	.card-pagination {
		display: flex;
		justify-content: center;
		padding: 15px 0;
		margin-top: auto;
	}
}

// 卡牌配置抽屉样式
.card-config-drawer {
	padding: 20px;

	.card-detail {
		display: flex;
		flex-direction: column;
		align-items: center;
		margin-bottom: 30px;

		.card-image-med {
			width: 120px;
			height: 120px;
			border-radius: 10px;
			overflow: hidden;
			box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
			margin-bottom: 15px;

			img {
				width: 100%;
				height: 100%;
				object-fit: cover;
			}

			.no-image-med {
				width: 100%;
				height: 100%;
				display: flex;
				align-items: center;
				justify-content: center;
				background: #f0f2f5;
				color: #bbb;

				i {
					font-size: 40px;
				}
			}
		}

		.card-name {
			font-size: 18px;
			font-weight: bold;
			margin: 10px 0;
			text-align: center;
		}

		.card-rarity {
			margin-bottom: 10px;

			.rarity-badge {
				padding: 3px 10px;
				border-radius: 15px;
				font-size: 12px;
				color: white;
				font-weight: bold;

				&.rarity-1 {
					background: #95a5a6;
				}
				&.rarity-2 {
					background: #3498db;
				}
				&.rarity-3 {
					background: #9b59b6;
				}
				&.rarity-4 {
					background: #f1c40f;
				}
			}
		}
	}

	.card-config-form {
		.config-item {
			margin-bottom: 20px;

			.config-label {
				font-size: 14px;
				color: #606266;
				margin-bottom: 8px;
				font-weight: 500;
			}

			.config-hint {
				font-size: 12px;
				color: #909399;
				margin-top: 5px;
			}
		}

		.config-actions {
			display: flex;
			justify-content: flex-end;
			gap: 10px;
			margin-top: 30px;
		}
	}
}

:deep(.el-dialog) {
	.el-dialog__header {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		padding: 20px;
		margin: 0;
		border-radius: 8px 8px 0 0;
	}

	.el-dialog__title {
		color: white;
		font-weight: bold;
	}

	.el-dialog__headerbtn .el-dialog__close {
		color: white;
	}
}

@media (max-width: 768px) {
	.card-panels-container {
		flex-direction: column;
	}

	.card-selection-grid .card-selection-item.bound.expanded {
		grid-column: span 1;
	}

	.card-selection-grid {
		grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));

		.card-selection-item {
			min-height: 180px;
		}
	}
}

@media (min-width: 1200px) {
	.card-selection-grid {
		grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
	}
}
</style>
