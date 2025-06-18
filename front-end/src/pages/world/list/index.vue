<script setup lang="ts">
	import { ref, onMounted, computed } from "vue";
	import { useRouter } from "vue-router";
	import { ElMessage, ElMessageBox } from "element-plus";
	import type { World, WorldCreate, WorldUpdate } from "@/types/world";
	import type { Page } from "@/types/api";
	import { getWorldList, createWorld, updateWorld, deleteWorld } from "@/api/world";
	import { Delete, Edit, Plus, Document, View, Timer } from "@element-plus/icons-vue";
	import { getConfig_value } from "@/api/system";
	import FileUploader from "@/components/FileUploader/index.vue";

	const router = useRouter();
	const loading = ref(false);
	const worlds = ref<World[]>([]);
	const worldFormRef = ref();

	// Pagination related
	const currentPage = ref(1);
	const pageSize = ref(12);
	const total = ref(0);

	// Dialog related
	const dialogVisible = ref(false);
	const dialogTitle = ref("Create New World");
	const formLoading = ref(false);
	const isEdit = ref(false);
	const form = ref({
		id: "",
		title: "",
		type: "",
		description: "",
		image_url: "",
		sort: 1,
	});

	// World type options
	const worldTypeOptions = ref([]);

	// Computed property: whether to show pagination component
	const showPagination = computed(() => total.value > pageSize.value);

	// Form validation rules
	const rules = {
		title: [{ required: true, message: "Please enter world title", trigger: "blur" }],
		type: [{ required: true, message: "Please select world type", trigger: "change" }],
		description: [{ required: true, message: "Please enter world description", trigger: "blur" }],
	};

	const fetchWorlds = async () => {
		loading.value = true;
		try {
			const params = {
				page: currentPage.value,
				size: pageSize.value,
			};

			const response : Page<World> = await getWorldList(params);
			if (response && response.items) {
				worlds.value = response.items.map((item : World) => ({
					...item,
					imageUrl: item.image_url,
					knowledgeCount: item.knowledge_count || 0,
					grade: item.sort || 1,
					tags: item.tags || [],
				}));
				total.value = response.total;
			} else {
				ElMessage.warning("No world data retrieved");
				worlds.value = [];
				total.value = 0;
			}
		} catch (error) {
			console.error("Failed to get world list", error);
			ElMessage.error("Failed to get world list");
			worlds.value = [];
			total.value = 0;
		} finally {
			loading.value = false;
		}
	};

	// Pagination handling functions
	const handleSizeChange = (size : number) => {
		pageSize.value = size;
		currentPage.value = 1;
		fetchWorlds();
	};

	const handleCurrentChange = (page : number) => {
		currentPage.value = page;
		fetchWorlds();
	};

	const goToDetail = (worldId : string) => {
		router.push(`/world/detail/${worldId}`);
	};

	// Open add world dialog
	const addWorld = () => {
		isEdit.value = false;
		dialogTitle.value = "Create New World";
		form.value = {
			id: "",
			title: "",
			type: "Worldview",
			description: "",
			image_url: "",
			sort: 1,
		};
		dialogVisible.value = true;
	};

	// Open edit world dialog
	const handleEdit = (world : World) => {
		dialogTitle.value = "Edit World";
		isEdit.value = true;
		form.value = {
			id: world.id,
			title: world.title,
			type: world.type,
			description: world.description,
			image_url: world.image_url || world.imageUrl || "",
			sort: world.sort || world.grade || 1,
		};
		dialogVisible.value = true;
	};

	// Submit form
	const submitForm = async (formEl : any) => {
		if (!formEl) return;
		await formEl.validate(async (valid : boolean) => {
			if (valid) {
				formLoading.value = true;
				try {
					if (isEdit.value && form.value.id) {
						const data : WorldUpdate = {
							title: form.value.title,
							type: form.value.type,
							description: form.value.description,
							image_url: form.value.image_url,
							sort: form.value.sort,
						};
						await updateWorld(form.value.id, data);
						ElMessage.success("World updated successfully");
					} else {
						const data : WorldCreate = {
							title: form.value.title,
							type: form.value.type,
							description: form.value.description,
							image_url: form.value.image_url,
							sort: form.value.sort,
						};
						await createWorld(data);
						ElMessage.success("World created successfully");
					}
					dialogVisible.value = false;
					fetchWorlds();
				} catch (error) {
					console.error("Failed to submit world data", error);
					ElMessage.error(isEdit.value ? "Failed to update world" : "Failed to create world");
				} finally {
					formLoading.value = false;
				}
			}
		});
	};

	// Delete world
	const handleDelete = (worldId : string) => {
		ElMessageBox.confirm("Are you sure you want to delete this world? This operation cannot be undone", "Delete Confirmation", {
			confirmButtonText: "Confirm Delete",
			cancelButtonText: "Cancel",
			type: "warning",
		})
			.then(async () => {
				try {
					await deleteWorld(worldId);
					ElMessage.success("Deleted successfully");
					fetchWorlds();
				} catch (error) {
					console.error("Failed to delete world", error);
					ElMessage.error("Failed to delete world");
				}
			})
			.catch(() => { });
	};

	// 格式化时间
	const formatDate = (dateStr : string) => {
		return new Date(dateStr).toLocaleDateString("zh-CN");
	};

	function getConfig() {
		getConfig_value("WEB_WORLD_TYPE_OPTIONS").then((res) => {
			worldTypeOptions.value = JSON.parse(res.config_value);
		});
	}

	onMounted(() => {
		fetchWorlds();
		getConfig();
	});
</script>

<template>
	<div class="world-library">
		<!-- Simple page header -->
		<div class="page-header theme-0">
			<div class="header-content">
				<div class="title-area">
					<h1 class="page-title">World Book Management</h1>
					<span class="page-subtitle sub-text-small">Total {{ total }} worlds,
						{{ worlds.reduce((sum, w) => sum + w.knowledgeCount, 0) }} knowledge entries</span>
				</div>
				<el-button class="btn-fix" type="primary" @click="addWorld" size="large">
					<el-icon>
						<Plus />
					</el-icon>
					Create New World
				</el-button>
			</div>
		</div>

		<!-- 世界书架 -->
		<div class="world-bookshelf" v-loading="loading">
			<div class="shelf-background"></div>

			<div class="books-container">
				<div v-for="(world, index) in worlds" :key="world.id" class="world-tome"
					:class="`tome-${(index % 4) + 1}`" @click="goToDetail(world.id)">
					<!-- 书脊装饰 -->
					<div class="tome-spine">
						<div class="spine-decoration"></div>
					</div>

					<!-- 书本封面 -->
					<div class="tome-cover">
						<div class="cover-image">
							<img :src="world.image_url" :alt="world.title" />
							<div class="image-overlay"></div>
						</div>

						<div class="cover-content">
							<div class="world-type-badge">{{ world.type }}</div>
							<h3 class="world-title">{{ world.title }}</h3>
							<p class="world-description">{{ world.description }}</p>

							<div class="world-meta">
								<div class="meta-item">
									<el-icon>
										<Document />
									</el-icon>
									<span>{{ world.knowledgeCount }} entries</span>
								</div>
								<div class="meta-item">
									<el-icon>
										<Timer />
									</el-icon>
									<span>{{ formatDate(world.updated_at) }}</span>
								</div>
							</div>
						</div>

						<!-- 悬浮操作按钮 -->
						<div class="tome-actions">
							<el-button size="small" circle @click.stop="goToDetail(world.id)"
								class="action-btn view-btn theme-2" title="read">
								<el-icon>
									<View />
								</el-icon>
							</el-button>
							<el-button size="small" circle @click.stop="handleEdit(world)" class="action-btn edit-btn theme-1"
								title="Edit">
								<el-icon>
									<Edit />
								</el-icon>
							</el-button>
							<el-button size="small" circle @click.stop="handleDelete(world.id)"
								class="action-btn delete-btn theme-0" title="Delete">
								<el-icon>
									<Delete />
								</el-icon>
							</el-button>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- 分页组件 -->
		<div v-if="showPagination" class="library-pagination">
			<el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize" :total="total"
				:page-sizes="[12, 24, 36, 48]" layout="total, sizes, prev, pager, next" @size-change="handleSizeChange"
				@current-change="handleCurrentChange" />
		</div>

		<!-- Create/Edit world dialog -->
		<el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px" class="world-dialog">
			<el-form ref="worldFormRef" :model="form" :rules="rules" label-width="120px" label-position="right"
				v-loading="formLoading">
				<el-form-item label="World Title" prop="title">
					<el-input v-model="form.title" placeholder="Give your world a resounding name" />
				</el-form-item>
				<el-form-item label="World Type" prop="type">
					<el-select v-model="form.type" placeholder="Select world type">
						<el-option v-for="item in worldTypeOptions" :key="item.value" :label="item.label"
							:value="item.value" />
					</el-select>
				</el-form-item>
				<el-form-item label="Importance Level" prop="sort">
					<el-select v-model="form.sort" placeholder="Set world importance level">
						<el-option v-for="i in 5" :key="i" :label="`Level ${i} ${'★'.repeat(i)}`" :value="i" />
					</el-select>
				</el-form-item>
				<el-form-item label="World Description" prop="description">
					<el-input v-model="form.description" type="textarea" :rows="4"
						placeholder="Describe the background, features and main content of this world..." />
				</el-form-item>
				<el-form-item label="Cover Image" prop="image_url">
					<FileUploader v-model="form.image_url" accept="image/*" folder="images" :max-size="10" />
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="dialogVisible = false" size="large">Cancel</el-button>
				<el-button class="btn-fix" type="primary" @click="submitForm(worldFormRef)" :loading="formLoading"
					size="large">
					{{ isEdit ? "Save Changes" : "Create World" }}
				</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<style scoped lang="scss">
	.world-library {
		min-height: 100vh;
		background: #f3f3f3;
		padding: 0;
		position: relative;
	}

	.world-library::before {
		content: "";
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-image: radial-gradient(circle at 25% 25%, rgba(3, 21, 40, 0.05) 0%, transparent 50%),
			radial-gradient(circle at 75% 75%, rgba(3, 21, 40, 0.03) 0%, transparent 50%);
		pointer-events: none;
		z-index: 0;
	}

	.page-header {
		background: rgba(5, 36, 73, 0.91);
		border-bottom: 3px solid #2563eb;
		padding: 20px;
		position: relative;
		z-index: 1;
	}

	.header-content {
		display: flex;
		justify-content: space-between;
		align-items: center;
		max-width: 1400px;
		margin: 0 auto;
	}

	.title-area {
		display: flex;
		flex-direction: column;
		gap: 5px;
	}

	.page-title {
		font-size: 24px;
		font-weight: bold;
		color: #ffffff;
		margin: 0;
		text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
	}

	.page-subtitle {
		font-size: 14px;
		color: #94a3b8;
		opacity: 0.9;
	}

	.world-bookshelf {
		position: relative;
		padding: 40px 20px;
		min-height: 400px;
		z-index: 1;
	}

	.shelf-background {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-image: repeating-linear-gradient(90deg,
				rgba(139, 69, 19, 0.1) 0px,
				rgba(139, 69, 19, 0.1) 2px,
				transparent 2px,
				transparent 40px);
		pointer-events: none;
	}

	.books-container {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
		gap: 20px;
		max-width: 1400px;
		margin: 0 auto;
	}

	.world-tome {
		position: relative;
		cursor: pointer;
		transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
		transform-style: preserve-3d;
	}

	.world-tome:hover {
		transform: translateY(-10px) rotateY(5deg);
	}

	.tome-spine {
		position: absolute;
		left: -8px;
		top: 0;
		bottom: 0;
		width: 16px;
		background: linear-gradient(135deg, #031528, #1e293b);
		border-radius: 8px 0 0 8px;
		box-shadow: -2px 0 8px rgba(0, 0, 0, 0.3);
	}

	.spine-decoration {
		position: absolute;
		top: 20px;
		bottom: 20px;
		left: 2px;
		right: 2px;
		background: repeating-linear-gradient(0deg, #2563eb 0px, #2563eb 2px, transparent 2px, transparent 12px);
		border-radius: 2px;
	}

	.tome-cover {
		background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
		border: 2px solid #031528;
		border-radius: 0 8px 8px 0;
		box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.8);
		overflow: hidden;
		position: relative;
		height: 280px;
	}

	.tome-cover::before {
		content: "";
		position: absolute;
		top: 12px;
		left: 12px;
		right: 12px;
		bottom: 12px;
		border: 1px solid #e2e8f0;
		border-radius: 8px;
		pointer-events: none;
	}

	.cover-image {
		position: relative;
		height: 140px;
		overflow: hidden;
		margin: 15px;
		border-radius: 6px;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
	}

	.cover-image img {
		width: 100%;
		height: 100%;
		object-fit: cover;
		transition: transform 0.3s ease;
	}

	.world-tome:hover .cover-image img {
		transform: scale(1.05);
	}

	.image-overlay {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: linear-gradient(135deg, rgba(139, 69, 19, 0.1) 0%, transparent 50%, rgba(218, 165, 32, 0.1) 100%);
	}

	.cover-content {
		padding: 0 15px 15px;
	}

	.world-type-badge {
		display: inline-block;
		background: linear-gradient(135deg, #031528, #1e293b);
		color: #ffffff;
		padding: 4px 12px;
		border-radius: 20px;
		font-size: 12px;
		font-weight: 500;
		margin-bottom: 8px;
		border: 1px solid #2563eb;
	}

	.world-title {
		font-size: 16px;
		font-weight: bold;
		color: #1e293b;
		margin: 0 0 6px 0;
		text-shadow: none;
		line-height: 1.2;
	}

	.world-description {
		color: #64748b;
		font-size: 14px;
		line-height: 1.4;
		margin: 0 0 12px 0;
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.world-meta {
		display: flex;
		justify-content: space-between;
		font-size: 12px;
		color: #475569;
	}

	.meta-item {
		display: flex;
		align-items: center;
		gap: 4px;
	}

	.tome-actions {
		position: absolute;
		top: 15px;
		right: 15px;
		display: flex;
		gap: 8px;
		opacity: 0;
		transition: opacity 0.3s ease;
	}

	.world-tome:hover .tome-actions {
		opacity: 1;
	}

	.action-btn {
		width: 32px;
		height: 32px;
		border-radius: 50%;
		border: none;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
		transition: all 0.2s ease;
	}

	.view-btn {
		background: linear-gradient(135deg, #4caf50, #45a049);
		color: white;
	}

	.edit-btn {
		background: linear-gradient(135deg, #ff9800, #f57c00);
		color: white;
	}

	.delete-btn {
		background: linear-gradient(135deg, #f44336, #d32f2f);
		color: white;
	}

	.action-btn:hover {
		transform: scale(1.1);
	}

	/* 不同书本的样式变化 */
	.tome-1 {
		transform: rotate(-1deg);
	}

	.tome-2 {
		transform: rotate(0.5deg);
	}

	.tome-3 {
		transform: rotate(-0.3deg);
	}

	.tome-4 {
		transform: rotate(0.8deg);
	}

	.tome-1:hover {
		transform: translateY(-10px) rotateY(5deg) rotate(-1deg);
	}

	.tome-2:hover {
		transform: translateY(-10px) rotateY(5deg) rotate(0.5deg);
	}

	.tome-3:hover {
		transform: translateY(-10px) rotateY(5deg) rotate(-0.3deg);
	}

	.tome-4:hover {
		transform: translateY(-10px) rotateY(5deg) rotate(0.8deg);
	}

	.library-pagination {
		padding: 40px 20px;
		display: flex;
		justify-content: center;
		position: relative;
		z-index: 1;
	}

	.library-pagination :deep(.el-pagination) {
		background: #ffffff;
		padding: 15px 20px;
		border-radius: 8px;
		border: 1px solid #e2e8f0;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	}

	.library-pagination :deep(.el-pager li) {
		background: transparent;
		color: #64748b;
		border: 1px solid #e2e8f0;
		margin: 0 2px;
		border-radius: 4px;
	}

	.library-pagination :deep(.el-pager li:hover),
	.library-pagination :deep(.el-pager li.is-active) {
		background: #2563eb;
		color: #ffffff;
		border-color: #2563eb;
	}

	.world-dialog :deep(.el-dialog) {
		background: linear-gradient(135deg, #f4e4bc 0%, #ddd5b8 100%);
		border: 3px solid #8b4513;
		border-radius: 12px;
	}

	.world-dialog :deep(.el-dialog__header) {
		background: linear-gradient(135deg, #8b4513, #a0522d);
		color: #f4e4bc;
		border-radius: 8px 8px 0 0;
		padding: 20px;
		border-bottom: 2px solid #daa520;
	}

	.world-dialog :deep(.el-dialog__title) {
		font-size: 20px;
		font-weight: bold;
	}

	/* 响应式设计 */
	@media (max-width: 768px) {
		.page-header {
			padding: 15px;
		}

		.header-content {
			flex-direction: column;
			gap: 15px;
			align-items: flex-start;
		}

		.page-title {
			font-size: 20px;
		}

		.books-container {
			grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
			gap: 15px;
		}

		.tome-cover {
			height: 260px;
		}
	}

	@media (max-width: 480px) {
		.books-container {
			grid-template-columns: 1fr;
			padding: 0 10px;
		}

		.world-tome {
			max-width: 300px;
			margin: 0 auto;
		}
	}
	

	@import '@/layouts/WriterLayout/css/extra.scss';

	.btn-fix {
		color: #fff;
		background-color: $btn-bg-color0;
		border-color: $btn-bg-color0;

		&:hover {
			background-color: $btn-bg-hover-color0;
			border-color: $btn-bg-hover-color0;
		}
	}


	.theme-0 {
		color: #fff;
		background: $theme-0;
		border-color: $btn-bg-color0;

		&:hover {
			background: $theme-hover-0;
			border-color: $theme-hover-0;
		}

		.sub-text-small {
			color: #333;
		}
	}


	.theme-1 {
		background: $theme-1;
		border-color: $theme-1;

		&:hover {
			background: $theme-hover-1;
			border-color: $theme-hover-1;
		}
	}

	.theme-2 {
		background: $theme-2;
		border-color: $theme-2;

		&:hover {
			background: $theme-hover-2;
			border-color: $theme-hover-2;
		}
	}
</style>