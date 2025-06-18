<template>
	<div class="blind-box-container">
		<!-- Top toolbar -->
		<div class="header-toolbar">
			<div class="search-section">
				<el-input
					v-model="searchParams.name"
					placeholder="Search blind box name"
					class="search-input"
					@keyup.enter="handleSearch"
				>
					<template #prepend>
						<i class="el-icon-search"></i>
					</template>
				</el-input>
				<el-select v-model="searchParams.status" placeholder="Status" class="select-filter">
					<el-option label="All" :value="null" />
					<el-option label="Enabled" :value="1" />
					<el-option label="Disabled" :value="0" />
				</el-select>
				<el-select v-model="searchParams.guarantee_rarity" placeholder="Guarantee rarity" class="select-filter">
					<el-option label="All" :value="null" />
					<el-option v-for="item in guaranteeRarityChoices" :key="item.value" :label="item.label" :value="item.value" />
				</el-select>
				<el-button type="primary" @click="handleSearch">Search</el-button>
				<el-button @click="handleReset">Reset</el-button>
			</div>
			<div class="action-section">
				<el-button type="primary" @click="handleCreate">
					<i class="el-icon-plus"></i>
					Create Blind Box
				</el-button>
			</div>
		</div>

		<!-- Blind box card grid -->
		<div class="blind-box-gallery-wrapper" v-loading="loading">
			<el-row :gutter="16" class="blind-box-gallery">
				<el-col v-if="blindBoxList.length === 0 && !loading" :span="24">
					<div class="empty-state">
						<el-empty description="No blind box data">
							<el-button type="primary" @click="handleCreate">Create Now</el-button>
						</el-empty>
					</div>
				</el-col>

				<el-col :xs="12" :sm="8" :md="6" :lg="4" :xl="3" v-for="blindBox in blindBoxList" :key="blindBox.id">
					<div class="blind-box-card-wrapper" :class="{ inactive: blindBox.status === 0 }">
						<div class="blind-box-card-inner">
							<div class="box-rarity-badge" :class="`rarity-${blindBox.guarantee_rarity || 1}`">
								{{ getRarityLabel(blindBox.guarantee_rarity) }}
							</div>
							<div class="box-status-badge">
								{{ blindBox.status === 1 ? "Enabled" : "Disabled" }}
							</div>

							<div class="box-image-container">
								<img
									v-if="blindBox.image_url"
									:src="blindBox.image_url"
									:alt="blindBox.name"
									@error="handleImageError"
									class="box-image"
								/>
								<div v-else class="no-image">
									<i class="el-icon-picture"></i>
									<span>No image</span>
								</div>
							</div>

							<div class="box-info">
								<div class="box-name">{{ blindBox.name }}</div>

								<div class="box-stats">
									<div class="stat-item" v-if="blindBox.price">
										<i class="el-icon-coin"></i>
										<span>{{ blindBox.price }} Points</span>
									</div>
									<div class="stat-item" v-if="blindBox.guarantee_count">
										<i class="el-icon-trophy"></i>
										<span>{{ blindBox.guarantee_count }} Draws Guarantee</span>
									</div>
								</div>

								<div class="box-description" v-if="blindBox.description">
									{{ blindBox.description }}
								</div>
							</div>

							<div class="box-actions">
								<el-button
									type="warning"
									size="small"
									circle
									@click.stop="handleEdit(blindBox)"
									class="action-btn edit-btn"
								>
									<el-icon><Edit /></el-icon>
								</el-button>
								<el-button
									type="primary"
									size="small"
									circle
									@click.stop="handleViewCards(blindBox)"
									class="action-btn view-btn"
								>
									<el-icon><Tickets /></el-icon>
								</el-button>
								<el-button
									type="danger"
									size="small"
									circle
									@click.stop="handleDelete(blindBox)"
									class="action-btn delete-btn"
								>
									<el-icon><Delete /></el-icon>
								</el-button>
							</div>

							<div class="select-indicator">View Details</div>
						</div>
					</div>
				</el-col>
			</el-row>
		</div>

		<!-- Pagination -->
		<div class="pagination-container" v-if="total > 0">
			<el-pagination
				v-model:current-page="currentPage"
				v-model:page-size="pageSize"
				:total="total"
				:page-sizes="[10, 20, 50, 100]"
				layout="total, sizes, prev, pager, next, jumper"
				@size-change="handleSizeChange"
				@current-change="handleCurrentChange"
			/>
		</div>

		<!-- Blind box form component -->
		<BlindBoxForm
			v-model:visible="formDialogVisible"
			:is-edit="isEdit"
			:edit-data="currentEditData"
			@saved="handleFormSaved"
		/>

		<!-- Blind box card configuration component -->
		<BlindBoxCardConfig
			v-model:visible="cardConfigDialogVisible"
			:blind-box-id="currentBlindBoxId"
			@saved="handleCardConfigSaved"
		/>
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Edit, Delete, Tickets } from "@element-plus/icons-vue";
import {
	getBlindBoxes,
	deleteBlindBox,
	getGuaranteeRarityChoices,
	type BlindBox,
	type GuaranteeRarityChoice,
} from "@/api/blind-box";
import { BlindBoxForm, BlindBoxCardConfig } from "@/components/blind-box";

// Reactive data
const loading = ref(false);
const formDialogVisible = ref(false);
const cardConfigDialogVisible = ref(false);
const isEdit = ref(false);
const currentEditData = ref<BlindBox | null>(null);

// Search parameters
const searchParams = reactive({
	name: "",
	status: null as number | null,
	guarantee_rarity: null as number | null,
});

// Pagination parameters
const currentPage = ref(1);
const pageSize = ref(20);
const total = ref(0);

// Blind box list data
const blindBoxList = ref<BlindBox[]>([]);
const guaranteeRarityChoices = ref<GuaranteeRarityChoice[]>([]);
const currentBlindBoxId = ref<number | null>(null);

// Computed properties
const getRarityLabel = (rarity?: number) => {
	const choice = guaranteeRarityChoices.value.find((item) => item.value === rarity);
	return choice ? choice.label : "Common";
};

// Methods
const fetchBlindBoxes = async () => {
	try {
		loading.value = true;
		const params = {
			...searchParams,
			page: currentPage.value,
			size: pageSize.value,
		};

		const response = await getBlindBoxes(params);
		blindBoxList.value = response.items || [];
		total.value = response.total || 0;
	} catch (error) {
		ElMessage.error("Failed to get blind box list");
		console.error("Error fetching blind boxes:", error);
	} finally {
		loading.value = false;
	}
};

const fetchGuaranteeRarityChoices = async () => {
	try {
		const response = await getGuaranteeRarityChoices();
		guaranteeRarityChoices.value = response || [];
	} catch (error) {
		console.error("Error fetching guarantee rarity choices:", error);
	}
};

const handleSearch = () => {
	currentPage.value = 1;
	fetchBlindBoxes();
};

const handleReset = () => {
	searchParams.name = "";
	searchParams.status = null;
	searchParams.guarantee_rarity = null;
	currentPage.value = 1;
	fetchBlindBoxes();
};

const handleCreate = () => {
	isEdit.value = false;
	currentEditData.value = null;
	formDialogVisible.value = true;
};

const handleEdit = (blindBox: BlindBox) => {
	isEdit.value = true;
	currentEditData.value = blindBox;
	formDialogVisible.value = true;
};

const handleDelete = async (blindBox: BlindBox) => {
	try {
		await ElMessageBox.confirm("Are you sure you want to delete this blind box?", "Confirm", {
			confirmButtonText: "Confirm",
			cancelButtonText: "Cancel",
			type: "warning",
		});

		await deleteBlindBox(blindBox.id);
		ElMessage.success("Deleted successfully");
		fetchBlindBoxes();
	} catch (error) {
		if (error !== "cancel") {
			ElMessage.error("Delete failed");
		}
	}
};

const handleViewCards = (blindBox: BlindBox) => {
	currentBlindBoxId.value = blindBox.id;
	cardConfigDialogVisible.value = true;
};

const handleImageError = (event: Event) => {
	const img = event.target as HTMLImageElement;
	img.src = "/placeholder.png"; // Set default image
};

const handleSizeChange = (size: number) => {
	pageSize.value = size;
	currentPage.value = 1;
	fetchBlindBoxes();
};

const handleCurrentChange = (page: number) => {
	currentPage.value = page;
	fetchBlindBoxes();
};

const handleFormSaved = () => {
	fetchBlindBoxes();
};

const handleCardConfigSaved = () => {
	fetchBlindBoxes();
};

// Lifecycle
onMounted(() => {
	fetchBlindBoxes();
	fetchGuaranteeRarityChoices();
});
</script>

<style scoped lang="scss">
.blind-box-container {
	padding: 20px;
	background: #f3f3f3;
	min-height: calc(100vh - 140px);

	.header-toolbar {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 20px;
		padding: 20px;
		background: rgba(5, 36, 73, 0.91);
		border-bottom: 3px solid #2563eb;
		border-radius: 8px;
		box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);

		.search-section {
			display: flex;
			gap: 15px;
			align-items: center;

			.search-input {
				width: 250px;
			}

			.select-filter {
				width: 150px;
			}
		}
	}

	.blind-box-gallery-wrapper {
		padding: 20px;
		background: transparent;

		.blind-box-gallery {
			display: flex;
			flex-wrap: wrap;
			gap: 20px;
		}

		.empty-state {
			padding: 60px 20px;
			background: #ffffff;
			border-radius: 8px;
			box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
			margin: 20px 0;
			text-align: center;
			width: 100%;
		}

		.blind-box-card-wrapper {
			margin-bottom: 20px;
			position: relative;
			border-radius: 8px;
			transition: all 0.3s ease;
			box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
			overflow: hidden;
			background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
			border: 2px solid #e2e8f0;
			height: 210px;

			&:hover {
				transform: translateY(-3px);
				box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
				border-color: #2563eb;
				z-index: 10;
			}

			&.inactive {
				opacity: 0.7;
				border-color: #e74c3c;
			}

			.blind-box-card-inner {
				position: relative;
				height: 100%;
				display: flex;
				flex-direction: column;
				align-items: center;
				padding: 15px 10px;
				cursor: pointer;
				text-align: center;
			}

			.box-rarity-badge {
				position: absolute;
				top: 5px;
				left: 5px;
				background: linear-gradient(135deg, #031528, #1e293b);
				color: #fff;
				padding: 2px 6px;
				border-radius: 12px;
				font-size: 10px;
				font-weight: bold;
				z-index: 5;
				box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
				border: 1px solid #2563eb;

				&.rarity-1 {
					background: linear-gradient(45deg, #95a5a6, #bdc3c7);
					border-color: #95a5a6;
				}
				&.rarity-2 {
					background: linear-gradient(45deg, #3498db, #5dade2);
					border-color: #3498db;
				}
				&.rarity-3 {
					background: linear-gradient(45deg, #9b59b6, #bb8fce);
					border-color: #9b59b6;
				}
				&.rarity-4 {
					background: linear-gradient(45deg, #f1c40f, #f7dc6f);
					border-color: #f1c40f;
				}
			}

			.box-status-badge {
				position: absolute;
				top: 5px;
				right: 5px;
				padding: 2px 6px;
				border-radius: 12px;
				font-size: 10px;
				font-weight: bold;
				color: white;
				background: #27ae60;
				z-index: 5;
				box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
				border: 1px solid rgba(255, 255, 255, 0.2);
			}

			.box-image-container {
				margin-top: 15px;
				margin-bottom: 10px;
				width: 80px;
				height: 80px;
				border-radius: 50%;
				overflow: hidden;
				border: 3px solid #fff;
				box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
				transition: transform 0.3s;
				background: #f0f2f5;
				display: flex;
				align-items: center;
				justify-content: center;

				.box-image {
					width: 100%;
					height: 100%;
					object-fit: cover;
				}

				.no-image {
					display: flex;
					flex-direction: column;
					align-items: center;
					color: #bbb;

					i {
						font-size: 24px;
					}

					span {
						font-size: 10px;
					}
				}
			}

			&:hover .box-image-container {
				transform: scale(1.05);
			}

			.box-info {
				flex: 1;
				width: 100%;
				display: flex;
				flex-direction: column;
				align-items: center;

				.box-name {
					font-size: 16px;
					margin: 5px 0 2px 0;
					color: var(--el-text-color-primary);
					font-weight: 600;
					white-space: nowrap;
					overflow: hidden;
					text-overflow: ellipsis;
					width: 100%;
				}

				.box-stats {
					display: flex;
					justify-content: center;
					gap: 10px;
					margin: 8px 0;

					.stat-item {
						display: flex;
						align-items: center;
						gap: 3px;
						color: var(--el-text-color-secondary);
						font-size: 10px;

						i {
							color: #f39c12;
						}
					}
				}

				.box-description {
					font-size: 12px;
					color: #8492a6;
					margin-bottom: 8px;
					max-height: 36px;
					overflow: hidden;
					display: -webkit-box;
					-webkit-line-clamp: 2;
					-webkit-box-orient: vertical;
				}
			}

			.box-actions {
				position: absolute;
				top: 5px;
				right: 5px;
				display: flex;
				gap: 5px;
				z-index: 5;
				opacity: 0;
				transition: opacity 0.3s;
			}

			&:hover .box-actions {
				opacity: 1;
			}

			.action-btn {
				box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.2);
				transform: scale(0.85);
			}

			.select-indicator {
				position: absolute;
				bottom: 0;
				left: 0;
				width: 100%;
				text-align: center;
				background: #2563eb;
				color: white;
				padding: 4px 0;
				font-size: 12px;
				font-weight: 600;
				opacity: 0;
				transform: translateY(100%);
				transition: all 0.3s;
			}

			&:hover .select-indicator {
				opacity: 1;
				transform: translateY(0);
			}
		}
	}

	.pagination-container {
		display: flex;
		justify-content: center;
		padding: 20px 0;
	}
}
</style>
