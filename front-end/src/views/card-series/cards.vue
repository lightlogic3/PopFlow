<template>
	<div class="cards-container">
		<!-- 页面头部 -->
		<div class="header fade-in">
			<div class="header-left">
				<el-button @click="goBack" class="back-button">
					<el-icon><ArrowLeft /></el-icon>
					Back to Series
				</el-button>
				<div class="series-info">
					<h1 class="title">{{ seriesInfo?.name || "Card Management" }}</h1>
					<p class="series-code">{{ seriesInfo?.code }}</p>
				</div>
			</div>
			<div class="header-actions">
				<el-button type="primary" @click="handleCreate" class="create-btn">
					<el-icon><Plus /></el-icon>
					Add Card
				</el-button>
			</div>
		</div>

		<!-- 搜索栏 -->
		<div class="search-box fade-in-up" style="animation-delay: 200ms">
			<el-row :gutter="20">
				<el-col :span="4">
					<el-input v-model="filters.name" placeholder="Card Name" clearable @change="handleSearch" />
				</el-col>
				<el-col :span="4">
					<el-select v-model="filters.rarity" placeholder="Rarity" clearable @change="handleSearch">
						<el-option label="All" value="" />
						<el-option v-for="(label, value) in rarityChoices" :key="value" :label="label" :value="parseInt(value)" />
					</el-select>
				</el-col>
				<el-col :span="4">
					<el-select v-model="filters.status" placeholder="Status" clearable @change="handleSearch">
						<el-option label="全部" value="" />
						<el-option label="Enabled" :value="1" />
						<el-option label="Disabled" :value="0" />
					</el-select>
				</el-col>
				<el-col :span="4">
					<el-select v-model="filters.is_limited" placeholder="Limited Type" clearable @change="handleSearch">
						<el-option label="全部" value="" />
						<el-option label="Limited" :value="1" />
						<el-option label="Permanent" :value="0" />
					</el-select>
				</el-col>
				<el-col :span="4">
					<el-button type="primary" @click="handleSearch">Search</el-button>
					<el-button @click="resetFilters">Reset</el-button>
				</el-col>
			</el-row>
		</div>

		<!-- 数据表格 -->
		<div class="table-container fade-in-up" style="animation-delay: 400ms">
			<el-row v-loading="loading" :gutter="16">
				<el-col :xs="24" :sm="12" :md="8" :lg="6" :xl="4" v-for="card in cardsList" :key="card.id" class="card-col">
					<el-card
						:class="['card-item', { 'disabled-card': card.status === 0, 'limited-card': card.is_limited === 1 }]"
						shadow="hover"
					>
						<div class="card-header">
							<div class="card-id">#{{ card.id }}</div>
							<el-tag :type="getRarityType(card.rarity)" size="small" class="rarity-tag">
								{{ getRarityLabel(card.rarity) }}
							</el-tag>
						</div>

						<div class="card-image">
							<img v-if="card.image_url" :src="card.image_url" @error="handleImageError($event)" />
							<div v-else class="no-image">
								<el-icon><Picture /></el-icon>
							</div>
						</div>

						<div class="card-content">
							<h3 class="card-name" :title="card.name">{{ card.name }}</h3>

							<div class="card-info">
								<div class="info-row">
									<span class="info-label">Unlock Type:</span>
									<el-tag :type="card.unlock_type === 'both' ? 'success' : 'warning'" size="small">
										{{ card.unlock_type === "both" ? "Points & Blind Box" : "Blind Box Only" }}
									</el-tag>
								</div>

								<div class="info-row" v-if="card.unlock_type !== 'box_only'">
									<span class="info-label">Purchase Price:</span>
									<span>{{ card.points_required || 0 }} Points</span>
								</div>

								<div class="info-row">
									<span class="info-label">Drop Rate:</span>
									<span>{{ card.box_drop_rate || 0 }}%</span>
								</div>

								<div class="info-row" v-if="card.blind_box_id">
									<span class="info-label">Bound Blind Box:</span>
									<div class="mini-box-tag">
										<img
											v-if="getBlindBoxImage(card.blind_box_id)"
											:src="getBlindBoxImage(card.blind_box_id)"
											class="mini-box-icon"
										/>
										<span class="mini-box-name">{{ getBlindBoxName(card.blind_box_id) }}</span>
									</div>
								</div>

								<div class="info-row">
									<span class="info-label">Duplicate Points:</span>
									<span>{{ card.duplicate_points }}</span>
								</div>

								<div class="info-row">
									<span class="info-label">Victory Reward:</span>
									<span>{{ card.victory_points || 0 }} Points</span>
								</div>

								<div class="info-row">
									<span class="info-label">Game Cost:</span>
									<span>{{ card.game_cost_points || 0 }} Points</span>
								</div>

								<div class="info-row" v-if="card.is_limited === 1">
									<span class="info-label">Limited Count:</span>
									<span>{{ card.limited_count || "Unlimited" }}</span>
								</div>
							</div>
						</div>

						<div class="card-footer">
							<el-button-group>
							<el-button type="primary" link @click="handleEdit(card)">
								<el-icon><Edit /></el-icon>
								Edit
							</el-button>
							<el-button type="info" link @click="handleView(card)">
								<el-icon><View /></el-icon>
								View
							</el-button>
							<el-button type="danger" link @click="handleDelete(card)">
								<el-icon><Delete /></el-icon>
								Delete
							</el-button>
						</el-button-group>
						</div>

						<div class="card-status">
					<el-tag v-if="card.status === 0" type="danger" size="small">Disabled</el-tag>
					<el-tag v-if="card.is_limited === 1" type="danger" size="small">Limited</el-tag>
						</div>
					</el-card>
				</el-col>
			</el-row>

			<!-- No data prompt -->
			<el-empty v-if="cardsList.length === 0" description="No card data available" />
		</div>

		<!-- 分页 -->
		<div class="pagination" v-if="total > 10">
			<el-pagination
				v-model:current-page="currentPage"
				v-model:page-size="pageSize"
				:total="total"
				:page-sizes="[10, 20, 50, 100]"
				layout="total, sizes, prev, pager, next"
				@size-change="handleSizeChange"
				@current-change="handleCurrentChange"
			/>
		</div>

		<!-- Create/Edit Dialog -->
		<el-dialog
			v-model="dialogVisible"
			:title="editingId ? 'Edit Card' : 'Add Card'"
			width="800px"
			:before-close="handleDialogClose"
		>
			<el-form ref="formRef" :model="formData" :rules="formRules" label-width="120px" class="card-form">
				<el-row :gutter="20">
					<el-col :span="12">
						<el-form-item label="Card Image" prop="image_url" required>
							<FileUploader v-model="formData.image_url" folder="cards" accept="image/*" :max-size="5" />
						</el-form-item>
					</el-col>
					<el-col :span="12">
						<el-form-item label="Card Name" prop="name">
							<el-input v-model="formData.name" placeholder="Please enter card name" />
						</el-form-item>
					</el-col>
				</el-row>
				<el-row :gutter="20">
					<el-col :span="12">
						<el-form-item label="Rarity" prop="rarity">
							<el-select v-model="formData.rarity" placeholder="Please select rarity" style="width: 100%">
								<el-option
									v-for="(label, value) in rarityChoices"
									:key="value"
									:label="label"
									:value="parseInt(value)"
								/>
							</el-select>
						</el-form-item>
					</el-col>
					<el-col :span="12">
						<el-form-item label="Unlock Type" prop="unlock_type">
							<el-select v-model="formData.unlock_type" placeholder="Please select unlock type" style="width: 100%">
								<el-option label="Points & Blind Box" value="both" />
								<el-option label="Blind Box Only" value="box_only" />
							</el-select>
						</el-form-item>
					</el-col>
				</el-row>
				<el-row :gutter="20">
					<el-col :span="12">
						<el-form-item
							label="Bind Blind Box"
							prop="blind_box_id"
							:rules="[{ required: true, message: 'Please select bind blind box', trigger: 'change' }]"
						>
							<el-select
								v-model="formData.blind_box_id"
								filterable
								placeholder="Please select bind blind box"
								style="width: 100%"
								:loading="loadingBlindBoxes"
							>
								<el-option v-for="box in blindBoxList" :key="box.id" :label="box.name" :value="box.id">
									<div style="display: flex; align-items: center">
										<img
											v-if="box.image_url"
											:src="box.image_url"
											style="width: 20px; height: 20px; margin-right: 8px"
										/>
										<span>{{ box.name }}</span>
									</div>
								</el-option>
							</el-select>
						</el-form-item>
					</el-col>
					<el-col :span="12" v-if="formData.unlock_type !== 'box_only'">
						<el-form-item label="Points Purchase Price" prop="points_required">
							<el-input-number v-model="formData.points_required" :min="0" style="width: 100%" />
						</el-form-item>
					</el-col>
				</el-row>
				<el-row :gutter="20">
					<el-col :span="12">
						<el-form-item
							label="Blind Box Drop Rate(%)"
							prop="box_drop_rate"
							:rules="[{ required: true, message: 'Please enter blind box drop rate', trigger: 'blur' }]"
						>
							<el-input-number
								v-model="formData.box_drop_rate"
								:min="0"
								:max="100"
								:precision="2"
								style="width: 100%"
							/>
						</el-form-item>
					</el-col>
					<el-col :span="12">
						<el-form-item label="Victory Points" prop="victory_points">
							<el-input-number v-model="formData.victory_points" :min="0" style="width: 100%" />
						</el-form-item>
					</el-col>
				</el-row>
				<el-row :gutter="20">
					<el-col :span="12">
						<el-form-item label="Game Cost Points" prop="game_cost_points">
							<el-input-number v-model="formData.game_cost_points" :min="0" style="width: 100%" />
						</el-form-item>
					</el-col>
					<el-col :span="12">
						<el-form-item label="Duplicate Points" prop="duplicate_points">
							<el-input-number v-model="formData.duplicate_points" :min="0" style="width: 100%" />
						</el-form-item>
					</el-col>
				</el-row>
				<el-row :gutter="20">
					<el-col :span="12">
						<el-form-item label="Is Limited" prop="is_limited">
							<el-radio-group v-model="formData.is_limited">
								<el-radio :label="0">Permanent</el-radio>
								<el-radio :label="1">Limited</el-radio>
							</el-radio-group>
						</el-form-item>
					</el-col>
					<el-col :span="12" v-if="formData.is_limited === 1">
						<el-form-item label="Limited Count" prop="limited_count">
							<el-input-number v-model="formData.limited_count" :min="1" style="width: 100%" />
						</el-form-item>
					</el-col>
				</el-row>
				<el-row :gutter="20">
					<el-col :span="12">
						<el-form-item label="Status" prop="status">
							<el-radio-group v-model="formData.status">
								<el-radio :label="1">Enabled</el-radio>
								<el-radio :label="0">Disabled</el-radio>
							</el-radio-group>
						</el-form-item>
					</el-col>
					<el-col :span="12">
						<el-form-item label="Associated Role" prop="role_id">
							<el-select
								v-model="formData.role_id"
								filterable
								clearable
								placeholder="Please select associated role (optional)"
								style="width: 100%"
								:loading="loadingRoles"
							>
								<el-option v-for="role in rolesList" :key="role.id" :label="role.name" :value="role.id">
									<div style="display: flex; align-items: center">
										<img
											v-if="role.avatar"
											:src="role.avatar"
											style="width: 20px; height: 20px; border-radius: 50%; margin-right: 8px"
										/>
										<span>{{ role.name }}</span>
									</div>
								</el-option>
							</el-select>
						</el-form-item>
					</el-col>
				</el-row>
				<el-form-item label="card description" prop="description">
					<RichTextEditor
						v-model="formData.description"
						placeholder="please enter a description of the card optional"
						:min-height="'200px'"
						:max-length="2000"
					/>
				</el-form-item>
			</el-form>
			<template #footer>
				<span class="dialog-footer">
					<el-button @click="dialogVisible = false">Cancel</el-button>
					<el-button type="primary" @click="handleSubmit" :loading="submitLoading">
						{{ editingId ? "Update" : "Create" }}
					</el-button>
				</span>
			</template>
		</el-dialog>
	</div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted, computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { ArrowLeft, Plus, Edit, Delete, View, Picture } from "@element-plus/icons-vue";
import {
	getCardList,
	createCard,
	updateCard,
	deleteCard,
	getRarityChoices,
	getUnlockTypeChoices,
	type Card,
	type CardCreate,
	type CardUpdate,
} from "@/api/card";
import { getAllRoles, type Role } from "@/api/role";
import { getActiveBlindBoxes } from "@/api/blind-box";
import { getCardSeriesDetail, type CardSeries } from "@/api/card-series";
import FileUploader from "@/components/FileUploader";
import RichTextEditor from "@/components/RichTextEditor/index.vue";

// 路由信息
const router = useRouter();
const route = useRoute();
const seriesId = computed(() => parseInt(route.params.seriesId as string));

// 响应式数据
const loading = ref(false);
const submitLoading = ref(false);
const cardsList = ref<Card[]>([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(20);
const seriesInfo = ref<CardSeries | null>(null);

// 枚举选项
const rarityChoices = ref<Record<string, string>>({});
const unlockTypeChoices = ref<Record<string, string>>({});

// 搜索过滤条件
const filters = reactive({
	name: "",
	rarity: "",
	status: "",
	is_limited: "",
});

// 对话框相关
const dialogVisible = ref(false);
const editingId = ref<number | null>(null);
const formRef = ref();

// 表单数据
const formData = reactive<CardCreate & { status: number; is_limited: number }>({
	name: "",
	series_id: seriesId.value,
	rarity: 1,
	description: "",
	image_url: "",
	sort_order: 0,
	unlock_type: "both",
	points_required: 0,
	duplicate_points: 1000,
	blind_box_id: undefined,
	box_drop_rate: 5,
	victory_points: 100,
	game_cost_points: 10,
	status: 1,
	role_id: "",
	limited_count: undefined,
	is_limited: 0,
});

// 表单验证规则
const formRules = {
	name: [{ required: true, message: "Please enter card name", trigger: "blur" }],
	image_url: [{ required: true, message: "Please upload card image", trigger: "change" }],
};

// 角色列表
const rolesList = ref<Role[]>([]);
const loadingRoles = ref(false);

// 盲盒列表
const blindBoxList = ref<any[]>([]);
const loadingBlindBoxes = ref(false);

// 获取盲盒名称
function getBlindBoxName(blindBoxId?: number): string {
	if (!blindBoxId) return "未绑定";
	const box = blindBoxList.value.find((box) => box.id === blindBoxId);
	return box ? box.name : "未知盲盒";
}

// 获取盲盒图片
function getBlindBoxImage(blindBoxId?: number): string | null {
	if (!blindBoxId) return null;
	const box = blindBoxList.value.find((box) => box.id === blindBoxId);
	return box?.image_url || null;
}

// 工具函数
function getRarityLabel(rarity: number): string {
	return rarityChoices.value[rarity.toString()] || "未知";
}

function getRarityType(rarity: number): any {
	const types = { 1: "", 2: "warning", 3: "danger", 4: "success" };
	return types[rarity as keyof typeof types] || "";
}

// 数据加载
async function loadEnumChoices() {
	try {
		const [rarityRes, unlockTypeRes] = await Promise.all([getRarityChoices(), getUnlockTypeChoices()]);
		rarityChoices.value = rarityRes;
		unlockTypeChoices.value = unlockTypeRes;
	} catch (err) {
		console.error("加载枚举选项失败:", err);
	}
}

async function loadSeriesInfo() {
	try {
		const res = await getCardSeriesDetail(seriesId.value);
		seriesInfo.value = res;
	} catch (err) {
		ElMessage.error("加载系列信息失败");
	}
}

async function loadRolesList() {
	try {
		loadingRoles.value = true;
		const response = await getAllRoles();
		rolesList.value = response || [];
	} catch (error) {
		console.error("Failed to load role list:", error);
		ElMessage.error("Failed to load role list");
	} finally {
		loadingRoles.value = false;
	}
}

async function loadBlindBoxesList() {
	try {
		loadingBlindBoxes.value = true;
		const response = await getActiveBlindBoxes();
		blindBoxList.value = response || [];
	} catch (error) {
		console.error("Failed to load blind box list:", error);
		ElMessage.error("Failed to load blind box list");
	} finally {
		loadingBlindBoxes.value = false;
	}
}

function loadCardsList() {
	loading.value = true;
	const params = {
		...filters,
		series_id: seriesId.value,
		page: currentPage.value,
		size: pageSize.value,
	};

	getCardList(params)
		.then((res) => {
			cardsList.value = res.items || [];
			total.value = res.total || 0;
		})
		.catch((err) => {
			ElMessage.error(`Failed to load card list: ${err.message}`);
		})
		.finally(() => {
			loading.value = false;
		});
}

// 搜索处理
function handleSearch() {
	currentPage.value = 1;
	loadCardsList();
}

function resetFilters() {
	filters.name = "";
	filters.rarity = "";
	filters.status = "";
	filters.is_limited = "";
	handleSearch();
}

// 分页处理
function handleSizeChange(val: number) {
	pageSize.value = val;
	loadCardsList();
}

function handleCurrentChange(val: number) {
	currentPage.value = val;
	loadCardsList();
}

// 操作处理
function goBack() {
	router.push("/bink/card-series");
}

function handleCreate() {
	editingId.value = null;
	resetForm();
	dialogVisible.value = true;
}

function handleEdit(card: Card) {
	editingId.value = card.id;
	formData.name = card.name;
	formData.series_id = card.series_id;
	formData.rarity = card.rarity;
	formData.description = card.description || "";
	formData.image_url = card.image_url || "";
	formData.sort_order = card.sort_order;
	formData.unlock_type = card.unlock_type || "both";
	formData.points_required = card.points_required || 0;
	formData.duplicate_points = card.duplicate_points;
	formData.status = card.status;
	formData.role_id = card.role_id || "";
	formData.blind_box_id = card.blind_box_id;
	formData.box_drop_rate = card.box_drop_rate || 5;
	formData.victory_points = card.victory_points || 100;
	formData.game_cost_points = card.game_cost_points || 10;
	formData.limited_count = card.limited_count;
	formData.is_limited = card.is_limited;
	dialogVisible.value = true;
}

function handleView(card: Card) {
	// Can implement card detail view functionality
	ElMessage.info("View function to be implemented: " + card.name);
}

function handleDelete(card: Card) {
	ElMessageBox.confirm(`Are you sure you want to delete card "${card.name}"? This operation cannot be undone.`, "Warning", {
		confirmButtonText: "Confirm",
		cancelButtonText: "Cancel",
		type: "warning",
	})
		.then(() => {
			deleteCard(card.id)
				.then(() => {
					ElMessage.success("Delete successful");
					loadCardsList();
				})
				.catch((err) => {
					ElMessage.error(`Delete failed: ${err.message}`);
				});
		})
		.catch(() => {
			// Cancel delete
		});
}

// 表单处理
function resetForm() {
	formData.name = "";
	formData.series_id = seriesId.value;
	formData.rarity = 1;
	formData.description = "";
	formData.image_url = "";
	formData.sort_order = 0;
	formData.unlock_type = "both";
	formData.points_required = 0;
	formData.duplicate_points = 1000;
	formData.status = 1;
	formData.role_id = "";
	formData.blind_box_id = undefined;
	formData.box_drop_rate = 5;
	formData.victory_points = 100;
	formData.game_cost_points = 10;
	formData.limited_count = undefined;
	formData.is_limited = 0;
	if (formRef.value) {
		formRef.value.clearValidate();
	}
}

function handleDialogClose() {
	resetForm();
	dialogVisible.value = false;
}

function handleSubmit() {
	if (!formRef.value) return;

	formRef.value.validate((valid: boolean) => {
		if (!valid) return;

		submitLoading.value = true;
		const request = editingId.value ? updateCard(editingId.value, formData as CardUpdate) : createCard(formData);

		request
			.then(() => {
				ElMessage.success(editingId.value ? "Update successful" : "Create successful");
				dialogVisible.value = false;
				loadCardsList();
			})
			.catch((err) => {
				ElMessage.error(`Operation failed: ${err.message}`);
			})
			.finally(() => {
				submitLoading.value = false;
			});
	});
}

// 处理图片错误
function handleImageError(event: Event) {
	const img = event.target as HTMLImageElement;
	img.src = "/placeholder.png"; // 设置默认占位图
}

// 初始化
onMounted(async () => {
	await Promise.all([loadEnumChoices(), loadSeriesInfo(), loadRolesList(), loadBlindBoxesList()]);
	loadCardsList();
});
</script>

<style lang="scss" scoped>
.cards-container {
	padding: 20px;
	min-height: 100vh;

	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 20px;

		.header-left {
			display: flex;
			align-items: center;
			gap: 16px;

			.back-button {
				display: flex;
				align-items: center;
				gap: 5px;
				color: var(--el-color-primary);
			}

			.series-info {
				.title {
					font-size: 24px;
					font-weight: 600;
					margin: 0;
				}

				.series-code {
					font-size: 14px;
					color: #666;
					margin: 4px 0 0 0;
					font-family: "Monaco", "Courier New", monospace;
				}
			}
		}

		.create-btn {
			background: var(--el-color-primary);
			border: none;
			border-radius: 6px;
			padding: 10px 20px;
		}
	}

	.search-box {
		margin-bottom: 20px;
		padding: 15px;
		background-color: #f5f7fa;
		border-radius: 4px;
	}

	.table-container {
		margin-bottom: 20px;

		.card-col {
			margin-bottom: 20px;
		}

		.card-item {
			position: relative;
			height: 100%;
			border-radius: 8px;
			transition: all 0.3s ease;
			overflow: hidden;

			&:hover {
				transform: translateY(-5px);
				box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
			}

			&.disabled-card {
				opacity: 0.7;
				border: 1px solid #f0f0f0;
			}

			&.limited-card {
				border: 1px solid var(--el-color-danger-light-3);
				background-color: #fff8f8;
			}

			.card-header {
				display: flex;
				justify-content: space-between;
				align-items: center;
				margin-bottom: 10px;

				.card-id {
					font-size: 12px;
					color: #999;
					font-weight: 500;
				}

				.rarity-tag {
					font-weight: 600;
				}
			}

			.card-image {
				height: 160px;
				overflow: hidden;
				border-radius: 6px;
				margin-bottom: 12px;
				box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
				background-color: #f7f7f7;

				img {
					width: 100%;
					height: 100%;
					object-fit: cover;
					transition: transform 0.3s ease;

					&:hover {
						transform: scale(1.05);
					}
				}

				.no-image {
					width: 100%;
					height: 100%;
					display: flex;
					align-items: center;
					justify-content: center;
					background-color: #f5f7fa;
					border-radius: 4px;
					color: #909399;
					font-size: 32px;
				}
			}

			.card-content {
				.card-name {
					font-size: 16px;
					font-weight: 600;
					margin: 0 0 12px 0;
					overflow: hidden;
					text-overflow: ellipsis;
					white-space: nowrap;
				}

				.card-info {
					font-size: 13px;

					.info-row {
						display: flex;
						justify-content: space-between;
						margin-bottom: 6px;
						padding-bottom: 6px;
						border-bottom: 1px dashed #eee;

						&:last-child {
							border-bottom: none;
						}

						.info-label {
							color: #666;
							flex-shrink: 0;
						}

						.mini-box-tag {
							display: flex;
							align-items: center;
							background-color: #f0f9eb;
							border-radius: 3px;
							padding: 2px 5px;
							max-width: 120px;

							.mini-box-icon {
								width: 14px;
								height: 14px;
								border-radius: 2px;
								margin-right: 4px;
							}

							.mini-box-name {
								font-size: 12px;
								color: #67c23a;
								white-space: nowrap;
								overflow: hidden;
								text-overflow: ellipsis;
							}
						}
					}
				}
			}

			.card-footer {
				margin-top: 15px;
				display: flex;
				justify-content: center;
				padding-top: 10px;
				border-top: 1px solid #eee;
			}

			.card-status {
				position: absolute;
				top: 8px;
				right: 8px;
				display: flex;
				flex-direction: column;
				gap: 5px;
			}
		}

		.text-muted {
			color: #c0c4cc;
		}
	}

	.pagination {
		display: flex;
		justify-content: center;
		margin-top: 20px;
		padding: 20px 0;

		:deep(.el-pagination) {
			background: #ffffff;
			padding: 15px 20px;
			border-radius: 8px;
			border: 1px solid #e2e8f0;
			box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
		}

		:deep(.el-pager li) {
			background: transparent;
			color: #64748b;
			border: 1px solid #e2e8f0;
			margin: 0 2px;
			border-radius: 4px;
		}

		:deep(.el-pager li:hover),
		:deep(.el-pager li.is-active) {
			background: #2563eb;
			color: #ffffff;
			border-color: #2563eb;
		}
	}
}

// 表单样式
.card-form {
	.el-form-item {
		margin-bottom: 20px;
	}
}

// 动画效果
.fade-in {
	animation: fadeIn 0.5s ease-out forwards;
}

.fade-in-up {
	animation: fadeInUp 0.5s ease-out forwards;
	opacity: 0;
}

@keyframes fadeIn {
	from {
		opacity: 0;
	}
	to {
		opacity: 1;
	}
}

@keyframes fadeInUp {
	from {
		opacity: 0;
		transform: translateY(20px);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}
</style>
