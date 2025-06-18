<template>
	<div class="model-selector-container">
		<el-dialog
			v-model="dialogVisible"
			:title="title"
			width="1000px"
			:close-on-click-modal="false"
			:before-close="handleCancel"
		>
			<div class="model-selector-content">
				<div class="model-list-container">
					<div class="model-list-header">
						<span>list of models</span>
					</div>
					<div class="model-list" ref="modelListRef" @scroll="handleModelListScroll">
						<div v-if="modelList.length > 0">
							<div
								v-for="(item, index) in modelList"
								:key="index"
								class="model-card"
								:class="{ active: currentModel?.Name === item.Name }"
								@click="handleSelectModel(item)"
							>
								<div class="model-card-header">
									<img
										:src="
											item.FeaturedImage?.Url ||
											'https://p11-ark-imagex.byteimg.com/tos-cn-i-51fv3nh8ci/6f1ac63ee5f5495caa265f3025734113~tplv-51fv3nh8ci-avif-cp:q95.avif'
										"
										alt="modelPicture"
										class="model-card-image"
									/>
									<div class="model-card-title">
										<div class="model-name">{{ item.DisplayName || item.Name }}</div>
										<div class="model-vendor">{{ item.VendorName }}</div>
									</div>
								</div>
								<div class="model-card-desc" v-if="item.Description">
									{{ truncateText(item.Description, 100) }}
								</div>
								<div class="model-card-tags">
									<el-tag v-for="tag in getModelTags(item)" :key="tag" size="small">{{ tag }}</el-tag>
								</div>
							</div>
						</div>

						<!-- 初始加载骨架屏 -->
						<div v-if="modelList.length === 0 && loading">
							<el-skeleton :rows="10" animated v-for="i in 3" :key="i" style="margin-bottom: 12px" />
						</div>

						<!-- 加载更多提示 -->
						<div v-if="loading && modelList.length > 0" class="loading-more">
							<el-icon class="loading-icon"><Loading /></el-icon>
							<span>加载更多...</span>
						</div>

						<!-- 无数据提示 -->
						<el-empty v-if="modelList.length === 0 && !loading" description="no model data is available" />

						<!-- 数据已全部加载提示 -->
						<div v-if="!hasMore && modelList.length > 0 && !loading" class="no-more">there is no more data</div>
					</div>
				</div>
				<div class="model-version-container">
					<div class="model-version-header">
						<span>{{ currentModel ? `${currentModel.DisplayName || currentModel.Name} version` : "modelVersion" }}</span>
					</div>
					<div class="model-version-content">
						<div v-if="currentModel && !versionLoading">
							<div class="model-detail">
								<div class="model-detail-header">
									<img
										:src="
											currentModel.FeaturedImage?.Url ||
											'https://p11-ark-imagex.byteimg.com/tos-cn-i-51fv3nh8ci/6f1ac63ee5f5495caa265f3025734113~tplv-51fv3nh8ci-avif-cp:q95.avif'
										"
										alt="模型图片"
										class="model-detail-image"
									/>
									<div class="model-detail-info">
										<h2>{{ currentModel.DisplayName || currentModel.Name }}</h2>
										<p>{{ currentModel.Description }}</p>
										<div class="model-detail-tags">
											<el-tag v-for="tag in getModelTags(currentModel)" :key="tag" size="small">{{ tag }}</el-tag>
										</div>
									</div>
								</div>
								<div class="model-versions">
									<div
										v-for="(version, index) in versionList"
										:key="index"
										class="version-card"
										:class="{ active: selectedVersion?.ModelVersion === version.ModelVersion }"
										@click="handleSelectVersion(version)"
									>
										<div class="version-card-title">
											<span class="version-name">版本: {{ version.ModelVersion }}</span>
											<span v-if="version.Status === 'Published'" class="version-status online">published</span>
											<span v-else class="version-status">{{ version.Status }}</span>
										</div>
										<div class="version-card-desc" v-if="version.Description">
											{{ version.Description }}
										</div>
										<div class="version-card-time">released: {{ formatDate(version.PublishTime) }}</div>
									</div>
								</div>
							</div>
						</div>

						<!-- 版本加载骨架屏 -->
						<el-skeleton v-if="versionLoading" :rows="5" animated />

						<!-- 未选择模型提示 -->
						<div v-if="!currentModel && !versionLoading" class="empty-version">
							<el-empty description="start by selecting the model on the left" />
						</div>
					</div>
				</div>
			</div>
			<template #footer>
				<span class="dialog-footer">
					<el-button @click="handleCancel">cancel</el-button>
					<el-button type="primary" :disabled="!selectedVersion" @click="handleConfirm">confirm your selection</el-button>
				</span>
			</template>
		</el-dialog>
	</div>
</template>

<script lang="ts">
import { defineComponent, ref, reactive, toRefs, onMounted, computed, watch } from "vue";
import { getModelList, getModelVersions } from "@/api/llm_model_config_api";
import { Loading } from "@element-plus/icons-vue";

export default defineComponent({
	name: "ModelSelector",
	components: {
		Loading,
	},
	props: {
		visible: {
			type: Boolean,
			default: false,
		},
		title: {
			type: String,
			default: "select a model",
		},
	},
	emits: ["update:visible", "cancel", "confirm"],
	setup(props, { emit }) {
		const state = reactive({
			loading: false,
			versionLoading: false,
			modelList: [] as any[],
			versionList: [] as any[],
			currentModel: null as any,
			selectedVersion: null as any,
			pageNumber: 1,
			pageSize: 10,
			hasMore: true,
			modelListRef: ref<HTMLElement | null>(null),
			scrollThreshold: 100, // 滚动阈值，提前触发加载
		});

		// 计算属性 - 控制对话框显示状态
		const dialogVisible = computed({
			get: () => props.visible,
			set: (val) => emit("update:visible", val),
		});

		// 加载模型列表
		const loadModelList = async (isLoadMore = false) => {
			if (state.loading || (!isLoadMore && !state.hasMore)) return;

			state.loading = true;

			try {
				// 记录当前滚动位置和内容高度
				const modelListElement = state.modelListRef;
				const scrollTop = modelListElement ? modelListElement.scrollTop : 0;

				const res = await getModelList({
					page: state.pageNumber,
					size: state.pageSize,
				});

				if (res?.Result) {
					const { Items = [], TotalCount = 0 } = res.Result;

					if (isLoadMore) {
						state.modelList = [...state.modelList, ...Items];
					} else {
						state.modelList = Items;
					}

					state.hasMore = state.modelList.length < TotalCount;
					if (state.hasMore) {
						state.pageNumber += 1;
					}

					// 在DOM更新后恢复滚动位置
					if (isLoadMore) {
						setTimeout(() => {
							if (modelListElement) {
								// 针对Element UI的特殊处理
								modelListElement.scrollTop = scrollTop;
							}
						}, 10);
					}
				}
			} catch (error) {
				console.error("加载模型列表失败:", error);
			} finally {
				state.loading = false;
			}
		};

		// 加载模型版本列表
		const loadModelVersions = async (modelName: string) => {
			state.versionLoading = true;
			state.versionList = [];

			try {
				const res = await getModelVersions(modelName);
				if (res?.Result) {
					state.versionList = res.Result.Items || [];
				}
			} catch (error) {
				console.error("加载模型版本失败:", error);
			} finally {
				state.versionLoading = false;
			}
		};

		// 选择模型
		const handleSelectModel = (model: any) => {
			state.currentModel = model;
			state.selectedVersion = null;
			loadModelVersions(model.Name);
		};

		// 选择版本
		const handleSelectVersion = (version: any) => {
			state.selectedVersion = version;
		};

		// 滚动加载更多
		const handleModelListScroll = async (e: Event) => {
			const target = e.target as HTMLElement;
			const { scrollTop, scrollHeight, clientHeight } = target;

			// 滚动到底部前预加载，提高用户体验
			if (scrollHeight - scrollTop - clientHeight <= state.scrollThreshold && state.hasMore && !state.loading) {
				await loadModelList(true);
			}
		};

		// 获取模型类型
		const getModelType = (model: any): string => {
			const tag = model.FoundationModelTag || {};
			const taskTypes = tag.TaskTypes || [];

			if (taskTypes.includes("VisualQuestionAnswering")) {
				return "multimodal";
			} else if (taskTypes.includes("Chat")) {
				return "chat";
			}

			return "chat"; // 默认为对话型
		};

		// 获取模型能力
		const getModelCapabilities = (model: any): string => {
			const capabilities: string[] = [];
			const tag = model.FoundationModelTag || {};

			if (tag.CustomizedTags?.length > 0) {
				capabilities.push(...tag.CustomizedTags);
			}

			if (tag.ContextLength) {
				capabilities.push(tag.ContextLength);
			}

			return capabilities.join(",");
		};

		// 取消选择
		const handleCancel = () => {
			dialogVisible.value = false;
			emit("cancel");
		};

		// 确认选择
		const handleConfirm = () => {
			if (state.currentModel && state.selectedVersion) {
				emit("confirm", {
					model_name: state.currentModel.Name,
					model_id: state.selectedVersion.ModelId,
					model_version: state.selectedVersion.ModelVersion,
					display_name: state.currentModel.DisplayName || state.currentModel.Name,
					introduction: state.currentModel.Introduction || state.currentModel.Description,
					description: state.currentModel.Description,
					icon_url: state.currentModel.FeaturedImage?.Url || "",
					vendor: state.currentModel.VendorName,
					model_type: getModelType(state.currentModel),
					capabilities: getModelCapabilities(state.currentModel),
					publish_time: state.selectedVersion.PublishTime,
					status: state.selectedVersion.Status,
					// 原始数据，以防需要
					model: state.currentModel,
					version: state.selectedVersion,
				});
				dialogVisible.value = false;
			}
		};

		// 获取模型标签
		const getModelTags = (model: any) => {
			const tags: string[] = [];

			if (model.FoundationModelTag) {
				const { Domains = [], TaskTypes = [], CustomizedTags = [], ContextLength } = model.FoundationModelTag;

				if (Domains.length > 0) {
					tags.push(...Domains);
				}

				if (TaskTypes.length > 0) {
					tags.push(...TaskTypes);
				}

				if (CustomizedTags.length > 0) {
					tags.push(...CustomizedTags);
				}

				if (ContextLength) {
					tags.push(ContextLength);
				}
			}

			return tags.slice(0, 3); // 最多显示3个标签
		};

		// 格式化日期
		const formatDate = (dateString: string) => {
			if (!dateString) return "";

			const date = new Date(dateString);
			return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(
				2,
				"0",
			)}`;
		};

		// 截断文本
		const truncateText = (text: string, maxLength: number) => {
			if (!text) return "";
			return text.length > maxLength ? text.substring(0, maxLength) + "..." : text;
		};

		// 监听visible属性变化，重置选中状态
		watch(
			() => props.visible,
			(newVal) => {
				if (newVal) {
					// 弹窗打开时加载模型列表
					state.pageNumber = 1;
					state.hasMore = true;
					loadModelList();
				} else {
					// 弹窗关闭时重置状态
					state.currentModel = null;
					state.selectedVersion = null;
					state.versionList = [];
				}
			},
		);

		onMounted(() => {
			if (props.visible) {
				loadModelList();
			}
		});

		return {
			...toRefs(state),
			dialogVisible,
			handleSelectModel,
			handleSelectVersion,
			handleModelListScroll,
			handleCancel,
			handleConfirm,
			getModelTags,
			formatDate,
			truncateText,
		};
	},
});
</script>

<style scoped>
.model-selector-container {
	width: 100%;
}

.model-selector-content {
	display: flex;
	height: 600px;
}

.model-list-container {
	width: 45%;
	border-right: 1px solid #f0f0f0;
	padding-right: 16px;
}

.model-version-container {
	width: 55%;
	padding-left: 16px;
}

.model-list-header,
.model-version-header {
	font-size: 16px;
	font-weight: 500;
	margin-bottom: 16px;
	padding-bottom: 8px;
	border-bottom: 1px solid #f0f0f0;
}

.model-list {
	height: calc(100% - 40px);
	overflow-y: auto;
	padding-right: 4px;
}

.model-card {
	padding: 12px;
	border: 1px solid #f0f0f0;
	border-radius: 8px;
	margin-bottom: 12px;
	cursor: pointer;
	transition: all 0.3s;
}

.model-card:hover {
	box-shadow: 0 3px 6px rgba(0, 0, 0, 0.1);
	border-color: #e6f7ff;
}

.model-card.active {
	border-color: #409eff;
	background-color: #ecf5ff;
}

.model-card-header {
	display: flex;
	align-items: center;
	margin-bottom: 8px;
}

.model-card-image {
	width: 40px;
	height: 40px;
	border-radius: 4px;
	object-fit: cover;
	margin-right: 12px;
}

.model-card-title {
	flex: 1;
}

.model-name {
	font-weight: 500;
	font-size: 14px;
}

.model-vendor {
	font-size: 12px;
	color: #999;
}

.model-card-desc {
	font-size: 12px;
	color: #666;
	margin-bottom: 8px;
	line-height: 1.5;
	display: -webkit-box;
	-webkit-box-orient: vertical;
	-webkit-line-clamp: 2;
	overflow: hidden;
}

.model-card-tags {
	display: flex;
	flex-wrap: wrap;
	gap: 4px;
}

.model-version-content {
	height: calc(100% - 40px);
	overflow-y: auto;
}

.model-detail-header {
	display: flex;
	margin-bottom: 16px;
}

.model-detail-image {
	width: 80px;
	height: 80px;
	border-radius: 8px;
	object-fit: cover;
	margin-right: 16px;
}

.model-detail-info {
	flex: 1;
}

.model-detail-info h2 {
	margin-top: 0;
	margin-bottom: 8px;
}

.model-detail-info p {
	margin-bottom: 8px;
	color: #666;
	line-height: 1.5;
}

.model-detail-tags {
	display: flex;
	flex-wrap: wrap;
	gap: 4px;
}

.model-versions {
	margin-top: 16px;
}

.version-card {
	padding: 12px;
	border: 1px solid #f0f0f0;
	border-radius: 8px;
	margin-bottom: 12px;
	cursor: pointer;
	transition: all 0.3s;
}

.version-card:hover {
	box-shadow: 0 3px 6px rgba(0, 0, 0, 0.1);
	border-color: #e6f7ff;
}

.version-card.active {
	border-color: #409eff;
	background-color: #ecf5ff;
}

.version-card-title {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 8px;
}

.version-name {
	font-weight: 500;
}

.version-status {
	font-size: 12px;
	padding: 2px 6px;
	border-radius: 4px;
	background-color: #f5f5f5;
}

.version-status.online {
	color: #67c23a;
	background-color: #f0f9eb;
}

.version-card-desc {
	font-size: 13px;
	color: #666;
	margin-bottom: 8px;
	line-height: 1.5;
}

.version-card-time {
	font-size: 12px;
	color: #999;
}

.empty-version {
	height: 100%;
	display: flex;
	align-items: center;
	justify-content: center;
}

.dialog-footer {
	display: flex;
	justify-content: flex-end;
}

.dialog-footer .el-button {
	margin-left: 8px;
}

.loading-more {
	text-align: center;
	padding: 10px 0;
	color: #909399;
	font-size: 14px;
	display: flex;
	align-items: center;
	justify-content: center;
}

.loading-icon {
	margin-right: 4px;
	animation: rotating 2s linear infinite;
}

.no-more {
	text-align: center;
	padding: 10px 0;
	color: #909399;
	font-size: 14px;
}

@keyframes rotating {
	0% {
		transform: rotate(0deg);
	}
	100% {
		transform: rotate(360deg);
	}
}
</style>
