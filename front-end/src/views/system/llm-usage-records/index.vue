<template>
	<div class="llm-usage-records">
		<div class="header fade-in">
			<h1 class="title">LLM Usage Records</h1>
			<div class="date-selector">
				<el-date-picker
					v-model="dateRange"
					type="daterange"
					range-separator="to"
					start-placeholder="Start Date"
					end-placeholder="End Date"
					:shortcuts="dateShortcuts"
					@change="handleDateChange"
				/>
			</div>
		</div>

		<!-- Statistics Cards -->
		<div class="statistics-cards fade-in-up">
			<el-row :gutter="20">
				<el-col :span="6" :class="{ 'animated-card': true }" style="animation-delay: 0ms">
					<el-card class="stat-card">
						<template #header>
							<div class="card-header">
								<span>Total Token Consumption</span>
								<el-tooltip content="Includes all input and output tokens" placement="top">
									<el-icon><InfoFilled /></el-icon>
								</el-tooltip>
							</div>
						</template>
						<div class="card-content">
							<div class="card-value">{{ formatNumber(animatedStats.total_tokens) }}</div>
							<div class="card-unit">tokens</div>
						</div>
					</el-card>
				</el-col>
				<el-col :span="6" :class="{ 'animated-card': true }" style="animation-delay: 100ms">
					<el-card class="stat-card">
						<template #header>
							<div class="card-header">
								<span>Total Cost</span>
								<el-tooltip content="Total cost of all requests" placement="top">
									<el-icon><InfoFilled /></el-icon>
								</el-tooltip>
							</div>
						</template>
						<div class="card-content">
							<div class="card-value">¥ {{ formatCurrency(animatedStats.total_price) }}</div>
							<div class="card-unit">CNY</div>
						</div>
					</el-card>
				</el-col>
				<el-col :span="6" :class="{ 'animated-card': true }" style="animation-delay: 200ms">
					<el-card class="stat-card">
						<template #header>
							<div class="card-header">
								<span>Request Count</span>
								<el-tooltip content="Total API call count" placement="top">
									<el-icon><InfoFilled /></el-icon>
								</el-tooltip>
							</div>
						</template>
						<div class="card-content">
							<div class="card-value">{{ formatNumber(animatedStats.total_requests) }}</div>
							<div class="card-unit">times</div>
						</div>
					</el-card>
				</el-col>
				<el-col :span="6" :class="{ 'animated-card': true }" style="animation-delay: 300ms">
					<el-card class="stat-card">
						<template #header>
							<div class="card-header">
								<span>Average Response Time</span>
								<el-tooltip content="Average API response time" placement="top">
									<el-icon><InfoFilled /></el-icon>
								</el-tooltip>
							</div>
						</template>
						<div class="card-content">
							<div class="card-value">{{ formatResponseTime(animatedStats.avg_response_time) }}</div>
							<div class="card-unit">seconds</div>
						</div>
					</el-card>
				</el-col>
			</el-row>
		</div>

		<!-- Search Bar -->
		<div class="search-box fade-in-up" style="animation-delay: 400ms">
			<el-row :gutter="20">
				<el-col :span="6">
					<el-select
						v-model="filters.vendor_type"
						placeholder="Provider Type"
						clearable
						@change="handleSearch"
						class="filter-select"
					>
						<el-option label="All" value="" />
						<el-option v-for="item in vendorOptions" :key="item.value" :label="item.label" :value="item.value" />
					</el-select>
				</el-col>
				<el-col :span="6">
					<el-select
						v-model="filters.model_id"
						placeholder="Model Selection"
						clearable
						@change="handleSearch"
						class="filter-select"
					>
						<el-option label="All" value="" />
						<el-option v-for="item in modelOptions" :key="item.value" :label="item.label" :value="item.value" />
					</el-select>
				</el-col>
				<el-col :span="6">
					<el-select
						v-model="filters.application_scenario"
						placeholder="Application Scenario"
						clearable
						@change="handleSearch"
						class="filter-select"
					>
						<el-option label="All" value="" />
						<el-option v-for="item in scenarioOptions" :key="item.value" :label="item.label" :value="item.value" />
					</el-select>
				</el-col>
				<el-col :span="6">
					<el-button type="primary" @click="handleSearch">Search</el-button>
					<el-button @click="resetFilters">Reset</el-button>
				</el-col>
			</el-row>
		</div>

		<!-- Data Table -->
		<div class="table-container fade-in-up" style="animation-delay: 500ms">
			<el-table
				v-loading="loading"
				:data="tableData"
				style="width: 100%"
				border
				stripe
				:highlight-current-row="true"
				@row-click="handleRowClick"
				:row-class-name="tableRowClassName"
			>
				<el-table-column prop="id" label="ID" width="80" />
				<el-table-column prop="vendor_type" label="Provider" width="120" />
				<el-table-column prop="model_id" label="Model" />
				<el-table-column prop="application_scenario" label="Application Scenario" width="220">
					<template #default="scope">
						{{ formatTokenUse(scope.row.application_scenario || "-") }}
					</template>
				</el-table-column>
				<el-table-column prop="input_tokens" label="Input Tokens" width="120">
					<template #default="scope">
						{{ formatNumber(scope.row.input_tokens) }}
					</template>
				</el-table-column>
				<el-table-column prop="completion_tokens" label="Output Tokens" width="120">
					<template #default="scope">
						{{ formatNumber(scope.row.output_tokens) }}
					</template>
				</el-table-column>
				<el-table-column prop="total_tokens" label="Total Tokens" width="120">
					<template #default="scope">
						{{ formatNumber(scope.row.total_tokens) }}
					</template>
				</el-table-column>
				<el-table-column prop="total_price" label="Cost" width="120">
					<template #default="scope"> ¥ {{ scope.row.total_price }} </template>
				</el-table-column>
				<el-table-column prop="response_time" label="Response Time (s)" width="120">
					<template #default="scope">
						{{ scope.row.response_time || 0 }}
					</template>
				</el-table-column>
				<el-table-column
					prop="created_at"
					label="Creation Time"
					width="180"
					:formatter="(row: any) => formatDate(row.created_at)"
				/>
				<el-table-column label="Actions" width="150" fixed="right">
					<template #default="{ row }">
						<el-button-group>
							<el-button type="primary" link @click="handleView(row)">
								<el-icon><View /></el-icon>
								Details
							</el-button>
							<el-button type="danger" link @click="handleDelete(row)">
								<el-icon><Delete /></el-icon>
								Delete
							</el-button>
						</el-button-group>
					</template>
				</el-table-column>
			</el-table>
		</div>

		<!-- Pagination -->
		<div class="pagination">
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

		<!-- Details Dialog -->
		<el-dialog v-model="detailDialogVisible" title="Usage Record Details" width="800px">
			<el-descriptions :column="2" border>
				<el-descriptions-item label="Request ID">{{ currentRecord.request_id }}</el-descriptions-item>
				<el-descriptions-item label="Provider">{{ currentRecord.vendor_type }}</el-descriptions-item>
				<el-descriptions-item label="Model">{{ currentRecord.model_id }}</el-descriptions-item>
				<el-descriptions-item label="Application Scenario">{{ currentRecord.application_scenario || "-" }}</el-descriptions-item>
				<el-descriptions-item label="Input Tokens">{{ formatNumber(currentRecord.input_tokens) }}</el-descriptions-item>
				<el-descriptions-item label="Output Tokens">{{
					formatNumber(currentRecord.completion_tokens)
				}}</el-descriptions-item>
				<el-descriptions-item label="Total Tokens">{{ formatNumber(currentRecord.total_tokens) }}</el-descriptions-item>
				<el-descriptions-item label="Cost">¥ {{ currentRecord.total_price }}</el-descriptions-item>
				<el-descriptions-item label="Response Time"
					>{{ formatResponseTime(currentRecord.response_time) }}seconds</el-descriptions-item
				>
				<el-descriptions-item label="Creation Time" :span="2">{{
					formatDate(currentRecord.created_at)
				}}</el-descriptions-item>
				<el-descriptions-item label="Related Record ID" :span="2">
					{{ currentRecord.related_record_id || "-" }}
				</el-descriptions-item>
			</el-descriptions>

			<template v-if="currentRecord.prompt_text || currentRecord.completion_text">
				<div class="message-content">
					<h3>Conversation Content</h3>
					<div class="message prompt">
						<div class="message-header">
							<el-icon><ChatDotRound /></el-icon>
							<span>Input Content</span>
						</div>
						<div class="message-body">{{ currentRecord.prompt_text || "No content" }}</div>
					</div>
					<div class="message completion">
						<div class="message-header">
							<el-icon><Service /></el-icon>
							<span>Output Content</span>
						</div>
						<div class="message-body">{{ currentRecord.completion_text || "No content" }}</div>
					</div>
				</div>
			</template>
		</el-dialog>
	</div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { InfoFilled, Delete, View, ChatDotRound, Service } from "@element-plus/icons-vue";
import {
	listUsageRecords,
	filterUsageRecords,
	getStatistics,
	deleteUsageRecord,
	getUsageRecord,
} from "@/api/llm_usage_records";
import { getConfig_value } from "@/api/system";

// Type definitions
interface LLMUsageRecord {
	id: number;
	request_id: string;
	vendor_type: string;
	model_id: string;
	application_scenario?: string;
	input_tokens: number;
	completion_tokens: number;
	total_tokens: number;
	total_price: string;
	response_time: number;
	created_at: string;
	related_record_id?: string;
	prompt_text?: string;
	completion_text?: string;
}

interface Statistics {
	total_tokens: number;
	total_price: number;
	total_requests: number;
	avg_response_time: number;
}

interface FilterOptions {
	vendor_type: string;
	model_id: string;
	application_scenario: string;
}

// Data definitions
const loading = ref(false);
const tableData = ref<LLMUsageRecord[]>([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(10);

// Animated statistics
const animatedStats = reactive({
	total_tokens: 0,
	total_price: 0,
	total_requests: 0,
	avg_response_time: 0,
});

const statistics = reactive<Statistics>({
	total_tokens: 0,
	total_price: 0,
	total_requests: 0,
	avg_response_time: 0,
});

// Number animation
function animateValue(obj: any, prop: string, start: number, end: number, duration: number) {
	const startTime = performance.now();

	function updateValue(currentTime: number) {
		const elapsedTime = currentTime - startTime;
		const progress = Math.min(elapsedTime / duration, 1);
		const easeProgress = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
		const currentValue = Math.floor(start + (end - start) * easeProgress);

		obj[prop] = currentValue;

		if (progress < 1) {
			requestAnimationFrame(updateValue);
		}
	}

	requestAnimationFrame(updateValue);
}

// Filter conditions
const filters = reactive<FilterOptions>({
	vendor_type: "",
	model_id: "",
	application_scenario: "",
});

// Date range selection
const dateRange = ref<[Date, Date] | null>(null);
const dateShortcuts = [
	{
		text: "Last Week",
		value: (() => {
			const end = new Date();
			const start = new Date();
			start.setTime(start.getTime() - 3600 * 1000 * 24 * 7);
			return [start, end];
		})(),
	},
	{
		text: "Last Month",
		value: (() => {
			const end = new Date();
			const start = new Date();
			start.setTime(start.getTime() - 3600 * 1000 * 24 * 30);
			return [start, end];
		})(),
	},
	{
		text: "Last Three Months",
		value: (() => {
			const end = new Date();
			const start = new Date();
			start.setTime(start.getTime() - 3600 * 1000 * 24 * 90);
			return [start, end];
		})(),
	},
];

// Details dialog
const detailDialogVisible = ref(false);
const currentRecord = reactive<LLMUsageRecord>({
	id: 0,
	request_id: "",
	vendor_type: "",
	model_id: "",
	input_tokens: 0,
	completion_tokens: 0,
	total_tokens: 0,
	total_price: "0",
	response_time: 0,
	created_at: "",
});

// Option data
const vendorOptions = [
	{ label: "OpenAI", value: "openai" },
	{ label: "Anthropic", value: "anthropic" },
	{ label: "Baidu Wenxin", value: "baidu" },
	{ label: "Xunfei Spark", value: "xunfei" },
	{ label: "Zhipu AI", value: "zhipu" },
];

const modelOptions = [
	{ label: "GPT-3.5", value: "gpt-3.5-turbo" },
	{ label: "GPT-4", value: "gpt-4" },
	{ label: "Claude-3", value: "claude-3" },
	{ label: "ERNIE Bot", value: "ernie-bot" },
	{ label: "Spark Model", value: "spark" },
	{ label: "ChatGLM", value: "chatglm" },
];

const scenarioOptions = [
	{ label: "Chat Conversation", value: "chat" },
	{ label: "Role Playing", value: "roleplay" },
	{ label: "World Building", value: "worldbuilding" },
	{ label: "Task Execution", value: "task" },
	{ label: "Text Generation", value: "text_generation" },
];

// Formatting functions
/**
 * Format number, add thousands separator
 * @param num Number to format
 */
const formatNumber = (num: number): string => {
	if (!num) {
		num = 0;
	}
	return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
};

/**
 * Format currency amount
 * @param amount Amount
 */
const formatCurrency = (amount: number): string => {
	// Keep 8 decimal places to ensure no precision loss
	if (typeof amount !== "number") {
		amount = 0;
	}
	return amount.toFixed(8);
};

/**
 * Format response time
 * @param seconds Seconds
 */
const formatResponseTime = (seconds: number): string => {
	return (seconds / 100).toFixed(2);
};

/**
 * Format date
 * @param dateString Date string
 */
const formatDate = (dateString: string): string => {
	if (!dateString) return "-";
	const date = new Date(dateString);
	return date.toLocaleString("zh-CN", {
		year: "numeric",
		month: "2-digit",
		day: "2-digit",
		hour: "2-digit",
		minute: "2-digit",
		second: "2-digit",
	});
};

// Get list data
const getList = async (): Promise<void> => {
	loading.value = true;
	try {
		let params: any = {
			page: currentPage.value,
			size: pageSize.value,
		};

		// If there are filter conditions, use filter interface
		if (filters.vendor_type || filters.model_id || filters.application_scenario || dateRange.value) {
			const filterData: any = {};

			if (filters.vendor_type) filterData.vendor_type = filters.vendor_type;
			if (filters.model_id) filterData.model_id = filters.model_id;
			if (filters.application_scenario) filterData.application_scenario = filters.application_scenario;

			// Process date range
			if (dateRange.value) {
				filterData.start_date = dateRange.value[0].toISOString();
				filterData.end_date = dateRange.value[1].toISOString();
			}

			const res = await filterUsageRecords(filterData, params);
			tableData.value = res.items;
			total.value = res.total; // Backend should return total
		} else {
			// Use list interface when no filter conditions
			const res = await listUsageRecords(params);
			tableData.value = res.items;
			total.value = res.total; // Backend should return total
		}
	} catch (error) {
		console.error("Failed to get LLM usage records:", error);
		ElMessage.error("Failed to get LLM usage records");
	} finally {
		loading.value = false;
	}
};

// Get statistics data
const getStatsData = async (): Promise<void> => {
	try {
		const params: any = {};

		// Process date range
		if (dateRange.value) {
			params.start_date = dateRange.value[0].toISOString();
			params.end_date = dateRange.value[1].toISOString();
		}

		// Add other filter conditions
		if (filters.vendor_type) params.vendor_type = filters.vendor_type;
		if (filters.model_id) params.model_id = filters.model_id;
		if (filters.application_scenario) params.application_scenario = filters.application_scenario;

		const res = await getStatistics(params);
		// Update statistics data
		const oldStats = { ...statistics };
		statistics.total_tokens = res.total_tokens || 0;
		statistics.total_price = res.total_price || 0;
		statistics.total_requests = res.total_records || 0;
		statistics.avg_response_time = res.average_elapsed_time || 0;

		// Trigger animation directly
		animateValue(animatedStats, "total_tokens", oldStats.total_tokens, statistics.total_tokens, 1500);
		// For price, set directly instead of animating to avoid precision issues
		animatedStats.total_price = statistics.total_price;
		animateValue(animatedStats, "total_requests", oldStats.total_requests, statistics.total_requests, 1500);
		animateValue(
			animatedStats,
			"avg_response_time",
			oldStats.avg_response_time * 100,
			statistics.avg_response_time * 100,
			1500,
		);
	} catch (error) {
		console.error("Failed to get statistics data:", error);
		ElMessage.error("Failed to get statistics data");
	}
};

// Search
const handleSearch = (): void => {
	currentPage.value = 1;
	getList();
	getStatsData();
};

// Reset filter conditions
const resetFilters = (): void => {
	filters.vendor_type = "";
	filters.model_id = "";
	filters.application_scenario = "";
	dateRange.value = null;
	handleSearch();
};

// Date change
const handleDateChange = (): void => {
	handleSearch();
};

// Pagination
const handleSizeChange = (val: number): void => {
	pageSize.value = val;
	getList();
};

const handleCurrentChange = (val: number): void => {
	currentPage.value = val;
	getList();
};

// View details
const handleView = async (row: LLMUsageRecord): Promise<void> => {
	try {
		// Get complete record details
		const record = await getUsageRecord(row.id);
		Object.assign(currentRecord, record);
		detailDialogVisible.value = true;
	} catch (error) {
		console.error("Failed to get record details:", error);
		ElMessage.error("Failed to get record details");
	}
};

// Delete
const handleDelete = (row: LLMUsageRecord): void => {
	ElMessageBox.confirm("Are you sure you want to delete this usage record?", "Prompt", {
		confirmButtonText: "Confirm",
		cancelButtonText: "Cancel",
		type: "warning",
	})
		.then(async () => {
			try {
				await deleteUsageRecord(row.id);
				ElMessage.success("Delete successful");
				getList();
				getStatsData();
			} catch (error) {
				console.error("Failed to delete usage record:", error);
				ElMessage.error("Failed to delete usage record");
			}
		})
		.catch(() => {
			// User canceled deletion
		});
};

// Table row click effect
const handleRowClick = (row: LLMUsageRecord) => {
	// Optional: Highlight row or perform other operations
	console.log(row);
};

// Table row class name
const tableRowClassName = ({ rowIndex }: { row: LLMUsageRecord; rowIndex: number }) => {
	// Add alternating row colors, can customize more styles
	return rowIndex % 2 === 0 ? "highlighted-row" : "";
};

const tokenUse = ref({});
function getConfig() {
	getConfig_value("TOKEN_STATISTICAL").then((res) => {
		tokenUse.value = JSON.parse(res.config_value);
		getList();
	});
}

function formatTokenUse(scenario: string) {
	for (const key in tokenUse.value) {
		if (scenario.includes(key)) {
			return tokenUse.value[key];
		}
	}
	return scenario;
}

onMounted(() => {
	// Set default query to last month
	dateRange.value = dateShortcuts[1].value as [Date, Date];
	getStatsData();
	getConfig();
});
</script>

<style lang="scss" scoped>
.llm-usage-records {
	padding: 20px;
	background-color: #f5f6fa;
	min-height: 100%;

	// Top fade in
	.fade-in {
		animation: fadeIn 0.6s ease-in-out;
	}

	// Bottom up fade in
	.fade-in-up {
		animation: fadeInUp 0.8s ease-in-out;
	}

	// Card animation
	.animated-card {
		opacity: 0;
		animation: fadeInUp 0.8s ease-in-out forwards;
	}

	// Table container
	.table-container {
		transition: all 0.3s ease;
		border-radius: 8px;
		overflow: hidden;
		box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
		background-color: #fff;
		margin-bottom: 20px;
	}

	// Row hover effect
	:deep(.highlighted-row) {
		background-color: rgba(64, 158, 255, 0.05) !important;
		transition: background-color 0.3s ease;
	}

	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 20px;

		.title {
			font-size: 24px;
			color: #2c3e50;
			margin: 0;
			position: relative;

			&:after {
				content: "";
				position: absolute;
				left: 0;
				bottom: -8px;
				width: 40px;
				height: 3px;
				background: linear-gradient(90deg, #1890ff, #36cfc9);
				border-radius: 2px;
			}
		}

		.date-selector {
			width: 400px;
			transition: all 0.3s ease;

			&:hover {
				transform: translateY(-2px);
			}
		}
	}

	.statistics-cards {
		margin-bottom: 20px;

		.stat-card {
			transition: all 0.3s ease;
			border-radius: 8px;
			overflow: hidden;
			box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);

			&:hover {
				transform: translateY(-5px);
				box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
			}

			.card-header {
				display: flex;
				align-items: center;
				gap: 8px;
				font-size: 16px;
				font-weight: 500;
				background: linear-gradient(135deg, #f6f8fa, #edf2f7);
				padding: 12px 15px;
			}

			.card-content {
				text-align: center;
				padding: 20px 0;
				background: linear-gradient(180deg, #fcfcfc, #f9f9f9);

				.card-value {
					font-size: 28px;
					font-weight: bold;
					color: transparent;
					background: linear-gradient(90deg, #1890ff, #36cfc9);
					background-clip: text;
					-webkit-background-clip: text;
					margin-bottom: 8px;
					line-height: 1.2;
					letter-spacing: 0.5px;
					transition: all 0.3s ease;
				}

				.card-unit {
					font-size: 14px;
					color: #909399;
					font-weight: 500;
				}
			}

			&:nth-child(1) .card-value {
				background: linear-gradient(90deg, #1890ff, #36cfc9);
				background-clip: text;
				-webkit-background-clip: text;
			}

			&:nth-child(2) .card-value {
				background: linear-gradient(90deg, #722ed1, #eb2f96);
				background-clip: text;
				-webkit-background-clip: text;
			}

			&:nth-child(3) .card-value {
				background: linear-gradient(90deg, #52c41a, #13c2c2);
				background-clip: text;
				-webkit-background-clip: text;
			}

			&:nth-child(4) .card-value {
				background: linear-gradient(90deg, #fa8c16, #fa541c);
				background-clip: text;
				-webkit-background-clip: text;
			}
		}
	}

	.search-box {
		margin-bottom: 20px;

		.filter-select {
			width: 100%;
		}
	}

	.pagination {
		margin-top: 20px;
		display: flex;
		justify-content: flex-end;
	}

	.message-content {
		margin-top: 20px;
		border-top: 1px solid #ebeef5;
		padding-top: 20px;

		h3 {
			margin-bottom: 15px;
			font-size: 18px;
			color: #2c3e50;
		}

		.message {
			margin-bottom: 15px;
			padding: 15px;
			border-radius: 8px;

			&.prompt {
				background-color: #f2f6fc;
			}

			&.completion {
				background-color: #f0f9eb;
			}

			.message-header {
				display: flex;
				align-items: center;
				gap: 8px;
				margin-bottom: 10px;
				font-weight: 500;
			}

			.message-body {
				white-space: pre-wrap;
				line-height: 1.5;
				color: #606266;
			}
		}
	}
}

// Animation keyframes
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
