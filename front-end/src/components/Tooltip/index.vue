<template>
	<div class="custom-tooltip">
		<!-- 悬停提示模式 -->
		<el-tooltip
			v-if="!usePopover && hasContent"
			:content="tooltipContent"
			:effect="effect"
			:placement="placement"
			:visible="visible"
			:raw-content="rawContent"
			:disabled="disabled"
			:offset="offset"
			:show-after="showAfter"
			:hide-after="hideAfter"
			:auto-close="autoClose"
			:show-arrow="showArrow"
			:teleported="teleported"
			:transition="transition"
			:trigger="trigger"
			:virtual-triggering="virtualTriggering"
			:popper-class="popperClass"
			:popper-style="popperStyle"
			:popper-options="popperOptions"
			:append-to-body="appendToBody"
			:enterable="enterable"
			:persistent="persistent"
			:z-index="zIndex"
			@before-show="onBeforeShow"
			@before-hide="onBeforeHide"
			@show="onShow"
			@hide="onHide"
		>
			<template #content v-if="$slots.content">
				<slot name="content"></slot>
			</template>
			<div class="tooltip-trigger" v-bind="$attrs">
				<slot></slot>
				<el-icon v-if="showIcon" :size="iconSize" :color="iconColor" class="tooltip-icon">
					<QuestionFilled />
				</el-icon>
			</div>
		</el-tooltip>

		<!-- 点击弹出层模式 -->
		<el-popover
			v-else-if="usePopover && hasContent"
			:placement="placement"
			:width="popoverWidth"
			:trigger="popoverTrigger"
			:title="popoverTitle"
			:teleported="teleported"
			:append-to-body="appendToBody"
			:popper-class="popperClass"
			:show-arrow="showArrow"
			:transition="transition"
			:persistent="persistent"
			:offset="offset"
		>
			<template #reference>
				<div class="tooltip-trigger" v-bind="$attrs">
					<slot></slot>
					<el-icon v-if="showIcon" :size="iconSize" :color="iconColor" class="tooltip-icon">
						<QuestionFilled />
					</el-icon>
				</div>
			</template>

			<div class="popover-content">
				<div v-if="$slots.content" class="popover-custom-content">
					<slot name="content"></slot>
				</div>
				<div v-else class="popover-text-content" v-html="formattedContent"></div>
			</div>
		</el-popover>

		<!-- 无提示内容时只显示插槽内容 -->
		<div v-else class="tooltip-trigger no-tooltip" v-bind="$attrs">
			<slot></slot>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { ElTooltip, ElIcon, ElPopover } from "element-plus";
import { QuestionFilled } from "@element-plus/icons-vue";
import { useTooltipStore } from "@/store/tooltip";
import type { Placement, TooltipTriggerType } from "element-plus";

const tooltipStore = useTooltipStore();

// 定义组件属性
const props = defineProps({
	// 提示 key
	tooltipKey: {
		type: String,
		default: "",
	},
	// 提示内容，优先级高于 tooltipKey
	content: {
		type: String,
		default: "",
	},
	// 是否使用弹出层模式
	usePopover: {
		type: Boolean,
		default: true,
	},
	// 弹出层标题
	popoverTitle: {
		type: String,
		default: "提示信息",
	},
	// 弹出层宽度
	popoverWidth: {
		type: [String, Number],
		default: 260,
	},
	// 弹出层触发方式
	popoverTrigger: {
		type: String as unknown as () => string,
		default: "click",
	},
	// 关闭按钮文本
	closeButtonText: {
		type: String,
		default: "关闭",
	},
	// 关闭按钮类型
	closeButtonType: {
		type: String,
		default: "primary",
	},
	// 是否显示图标
	showIcon: {
		type: Boolean,
		default: true,
	},
	// 图标大小
	iconSize: {
		type: [Number, String],
		default: 16,
	},
	// 图标颜色
	iconColor: {
		type: String,
		default: "#909399",
	},
	// el-tooltip 原有属性
	effect: {
		type: String,
		default: "dark",
	},
	placement: {
		type: String as () => Placement,
		default: "top",
	},
	visible: {
		type: Boolean,
		default: undefined,
	},
	rawContent: {
		type: Boolean,
		default: false,
	},
	disabled: {
		type: Boolean,
		default: false,
	},
	offset: {
		type: Number,
		default: 8,
	},
	showAfter: {
		type: Number,
		default: 0,
	},
	hideAfter: {
		type: Number,
		default: 200,
	},
	autoClose: {
		type: Number,
		default: 0,
	},
	showArrow: {
		type: Boolean,
		default: true,
	},
	teleported: {
		type: Boolean,
		default: true,
	},
	transition: {
		type: String,
		default: "el-fade-in-linear",
	},
	trigger: {
		type: [String, Array] as unknown as () => TooltipTriggerType | TooltipTriggerType[],
		default: "hover",
	},
	virtualTriggering: {
		type: Boolean,
		default: false,
	},
	popperClass: {
		type: String,
		default: "",
	},
	popperStyle: {
		type: Object,
		default: () => ({}),
	},
	popperOptions: {
		type: Object,
		default: () => ({}),
	},
	appendToBody: {
		type: Boolean,
		default: true,
	},
	enterable: {
		type: Boolean,
		default: true,
	},
	persistent: {
		type: Boolean,
		default: true,
	},
	zIndex: {
		type: Number,
		default: undefined,
	},
});

// 定义事件
const emit = defineEmits(["before-show", "before-hide", "show", "hide", "popover-open", "popover-close"]);

// 事件处理函数
const onBeforeShow = () => {
	emit("before-show");
};
const onBeforeHide = () => {
	emit("before-hide");
};
const onShow = () => {
	emit("show");
};
const onHide = () => {
	emit("hide");
};

// 获取提示内容
const tooltipContent = computed(() => {
	if (props.content) {
		return props.content;
	}

	if (props.tooltipKey) {
		return tooltipStore.getTooltip(props.tooltipKey);
	}

	return "";
});

// 判断是否有内容可显示
const hasContent = computed(() => {
	// 如果有直接提供的内容，则显示提示
	if (props.content) {
		return true;
	}

	// 如果有tooltipKey且能获取到内容，则显示提示
	if (props.tooltipKey && tooltipStore.isLoaded && tooltipStore.getTooltip(props.tooltipKey)) {
		return true;
	}

	return false;
});

// 格式化内容，将换行转换为<br>
const formattedContent = computed(() => {
	return tooltipContent.value.replace(/\n/g, "<br>");
});

// 弹出层触发方式的计算属性
const popoverTrigger = computed(() => {
	return props.popoverTrigger as any;
});

// 组件挂载时，确保提示数据已加载
onMounted(async () => {
	try {
		await tooltipStore.ensureLoaded();
	} catch (error) {
		console.error("加载提示数据时出错:", error);
	}
});
</script>

<style scoped>
.custom-tooltip {
	display: inline-flex;
	align-items: center;
}

.tooltip-trigger,
.tooltip-dialog-trigger {
	display: inline-flex;
	align-items: center;
	cursor: help;
}

.tooltip-dialog-trigger {
	cursor: pointer;
}

.no-tooltip {
	cursor: auto;
}

.tooltip-icon {
	margin-left: 4px;
	display: inline-flex;
	align-items: center;
	justify-content: center;
}

.popover-content {
	padding: 5px 0;
}

.popover-text-content {
	line-height: 1.6;
	margin-bottom: 12px;
}

.popover-footer {
	text-align: right;
	margin-top: 10px;
}

:deep(.el-popover__title) {
	margin-bottom: 8px;
	font-weight: 500;
}
</style>
