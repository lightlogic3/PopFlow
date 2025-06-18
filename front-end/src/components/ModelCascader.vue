<template>
	<div class="model-cascader-container">
		<el-cascader
			v-model="selectedValue"
			:options="cascaderOptions"
			:props="cascaderProps"
			:placeholder="placeholder"
			:disabled="disabled || loading"
			:clearable="clearable"
			:filterable="filterable"
			:show-all-levels="showAllLevels"
			class="model-cascader"
			popper-class="model-cascader-dropdown"
			@change="handleChange"
		>
			<template #default="{ data }">
				<div class="cascader-node">
					<div class="cascader-label">
						<span>{{ data.label }}</span>
						<span v-if="data.remark" class="cascader-remark">({{ data.remark }})</span>
					</div>
					<div v-if="data.capabilities" class="cascader-capabilities">
						<el-tag v-for="cap in data.capabilities.split(',')" :key="cap" size="small" class="capability-tag">
							{{ cap }}
						</el-tag>
					</div>
				</div>
			</template>
		</el-cascader>
	</div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed, defineProps, defineEmits } from "vue";
import { ElMessage } from "element-plus";
import { useGlobalStore } from "@/store/global";
const props = defineProps({
	modelValue: {
		type: String,
		default: "",
	},
	placeholder: {
		type: String,
		default: "please select a large model",
	},
	disabled: {
		type: Boolean,
		default: false,
	},
	clearable: {
		type: Boolean,
		default: true,
	},
	filterable: {
		type: Boolean,
		default: true,
	},
	showAllLevels: {
		type: Boolean,
		default: false,
	},
	filterCapability: {
		type: String,
		default: "",
	},
	// 是否强制刷新数据
	forceRefresh: {
		type: Boolean,
		default: false,
	},
});

const emit = defineEmits(["update:modelValue", "change"]);

const globalStore = useGlobalStore();
const selectedValue = ref("");
const loading = ref(false);

// 计算获取LLM供应商和模型数据
const providerModels = computed(() => globalStore.llmProviderModels);

// 级联选择器配置
const cascaderProps = {
	value: "value",
	label: "label",
	children: "children",
	checkStrictly: false,
	emitPath: false,
	expandTrigger: "hover" as const,
};

// 转换为级联选择器需要的格式，并根据capabilities过滤
const cascaderOptions = computed(() => {
	return providerModels.value
		.map((provider) => {
			// 如果存在过滤条件，则过滤模型
			const filteredModels = provider.models.filter((model) => {
				// 如果没有过滤条件，显示所有模型
				if (!props.filterCapability) return true;
				// 如果模型没有capabilities字段，则不显示
				if (!model.capabilities) return false;
				// 检查模型的capabilities是否包含过滤条件（不区分大小写）
				return model.capabilities.toLowerCase().includes(props.filterCapability.toLowerCase());
			});

			// 如果该提供商下没有符合条件的模型，则不显示该提供商
			if (filteredModels.length === 0) {
				return null;
			}

			return {
				value: `provider_${provider.id}`,
				label: provider.provider_name,
				remark: provider.remark,
				disabled: false,
				children: filteredModels.map((model) => ({
					value: model.model_id,
					label: model.model_name,
					capabilities: model.capabilities,
					modelInfo: model,
				})),
			};
		})
		.filter((provider) => provider !== null); // 过滤掉没有符合条件模型的提供商
});

/**
 * @description 获取模型数据
 */
const fetchModels = async () => {
	loading.value = true;
	try {
		// 如果强制刷新，则重置加载状态
		if (props.forceRefresh) {
			globalStore.resetLLMProviderModelsLoadedState();
		}

		// 从全局store中获取数据
		await globalStore.fetchLLMProviderModels();
	} catch (error) {
		console.error("获取模型层级数据失败", error);
		ElMessage.error("failed to get model data");
	} finally {
		loading.value = false;
	}
};

// 处理选择变化
const handleChange = (value: string) => {
	console.log(value);
	emit("update:modelValue", value);

	// 查找选中模型的完整信息
	let selectedModel = null;
	for (const provider of providerModels.value) {
		for (const model of provider.models) {
			if (model.model_id === value) {
				selectedModel = {
					...model,
					provider_name: provider.provider_name,
					provider_id: provider.id,
				};
				break;
			}
		}
		if (selectedModel) break;
	}

	emit("change", selectedModel);
};

// 监听外部传入的值变化
watch(
	() => props.modelValue,
	(newVal) => {
		if (newVal !== selectedValue.value) {
			selectedValue.value = newVal;
		}
	},
	{ immediate: true },
);

// 监听filterCapability的变化，当过滤条件变化时，重置选择的值
watch(
	() => props.filterCapability,
	() => {
		// 当过滤条件变化时，清空选择
		selectedValue.value = "";
		emit("update:modelValue", "");
	},
);

// 监听forceRefresh的变化
watch(
	() => props.forceRefresh,
	(newVal) => {
		if (newVal) {
			fetchModels();
		}
	},
);

onMounted(() => {
	fetchModels();
});
</script>

<style scoped lang="scss">
.model-cascader-container {
	width: 100%;
}

.cascader-node {
	display: flex;
	flex-direction: column;
}

.cascader-label {
	display: flex;
	align-items: center;
}

.cascader-remark {
	font-size: 12px;
	color: #909399;
	margin-left: 4px;
}

.cascader-capabilities {
	margin-top: 4px;
	display: flex;
	flex-wrap: wrap;
	gap: 4px;
}

.capability-tag {
	font-size: 10px;
	padding: 0 4px;
	height: 20px;
	line-height: 18px;
}
:deep(.el-cascader) {
	width: 100%;
}
</style>

<style lang="scss">
/* 非scoped全局样式，用于控制级联选择器弹出层的样式 */
.model-cascader-dropdown {
	.el-cascader-menu {
		height: auto;
		max-height: 550px;
		width: 100%;
	}

	.el-cascader-node {
		height: 50px;
		padding: 8px 20px;
		line-height: normal;
	}
}
</style>
