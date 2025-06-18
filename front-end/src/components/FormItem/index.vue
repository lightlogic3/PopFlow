<template>
	<el-form-item :label="label" v-bind="$attrs">
		<template #label>
			{{ label }}
			<Tooltip
				v-if="shouldShowTooltip"
				:tooltipKey="tooltipKey"
				:content="tooltipContent"
				:placement="tooltipPlacement"
				:effect="tooltipEffect"
				:usePopover="usePopover"
				:popoverTitle="popoverTitle"
				:popoverWidth="popoverWidth"
				:popoverTrigger="popoverTrigger"
				:closeButtonText="closeButtonText"
				:closeButtonType="closeButtonType"
			/>
		</template>
		<slot></slot>
	</el-form-item>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { ElFormItem } from "element-plus";
import Tooltip from "../Tooltip/index.vue";
import { useTooltipStore } from "@/store/tooltip";
import type { Placement } from "element-plus";

const tooltipStore = useTooltipStore();
const props = defineProps({
	// 表单项标签
	label: {
		type: String,
		default: "",
	},
	// 提示信息的key
	tooltipKey: {
		type: String,
		default: "",
	},
	// 直接提供的提示内容，优先级高于tooltipKey
	tooltipContent: {
		type: String,
		default: "",
	},
	// 提示的位置
	tooltipPlacement: {
		type: String as () => Placement,
		default: "top",
	},
	// 提示的主题
	tooltipEffect: {
		type: String,
		default: "dark",
	},
	// 是否使用弹出层模式
	usePopover: {
		type: Boolean,
		default: true,
	},
	// 弹出层标题
	popoverTitle: {
		type: String,
		default: "prompt information",
	},
	// 弹出层宽度
	popoverWidth: {
		type: [String, Number],
		default: 260,
	},
	// 弹出层触发方式
	popoverTrigger: {
		type: String,
		default: "click",
	},
	// 关闭按钮文本
	closeButtonText: {
		type: String,
		default: "shut down",
	},
	// 关闭按钮类型
	closeButtonType: {
		type: String,
		default: "primary",
	},
});

// 判断是否应该显示Tooltip
const shouldShowTooltip = computed(() => {
	try {
		// 有直接提供的内容
		if (props.tooltipContent) {
			return true;
		}

		// 有tooltipKey且能获取到内容
		if (props.tooltipKey && tooltipStore.isLoaded && tooltipStore.getTooltip(props.tooltipKey)) {
			return true;
		}

		return false;
	} catch (error) {
		console.error("An error occurred while calculating whether a prompt was displayed:", error);
		return false;
	}
});

// 组件挂载时，确保提示数据已加载
onMounted(async () => {
	try {
		await tooltipStore.ensureLoaded();
	} catch (error) {
		console.error("an error occurred while loading the prompt data:", error);
	}
});
</script>

<style scoped>
/* 确保组件样式与el-form-item保持一致 */
</style>
