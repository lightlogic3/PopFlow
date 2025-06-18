<template>
	<div class="scenarios-container">
		<div class="header">
			<h1 class="title">剧情场景管理</h1>
			<el-button type="primary" @click="createNewScenario" class="create-btn">
				<el-icon><Plus /></el-icon>
				创建新场景
			</el-button>
		</div>

		<div class="scenarios-grid" v-loading="loading">
			<el-empty v-if="scenarios.length === 0" description="暂无自定义场景" />

			<div v-for="(scenario, index) in scenarios" :key="index" class="scenario-card">
				<div class="scenario-header">
					<h3 class="scenario-title">{{ scenario.title }}</h3>
					<el-tag size="small" :type="getScenarioTypeTag(scenario.type)">{{
						getScenarioTypeName(scenario.type)
					}}</el-tag>
				</div>

				<div class="scenario-description">
					{{ scenario.description }}
				</div>

				<div class="scenario-meta">
					<div class="meta-item">
						<el-icon><Calendar /></el-icon>
						<span>创建时间: {{ formatDateTime(scenario.createdAt) }}</span>
					</div>
					<div class="meta-item">
						<el-icon><User /></el-icon>
						<span>主角设定: {{ scenario.characterCount || "未指定" }}</span>
					</div>
				</div>

				<div class="scenario-actions">
					<el-button class="action-button play-button" @click="playScenario(scenario)">
						<el-icon><VideoPlay /></el-icon>
						体验
					</el-button>
					<el-button class="action-button edit-button" @click="editScenario(scenario)">
						<el-icon><Edit /></el-icon>
						编辑
					</el-button>
					<el-button class="action-button delete-button" @click="deleteScenario(scenario)">
						<el-icon><Delete /></el-icon>
						删除
					</el-button>
				</div>
			</div>
		</div>

		<!-- 新建/编辑场景对话框 -->
		<el-dialog v-model="dialogVisible" :title="isEditMode ? '编辑场景' : '创建新场景'" width="600px" destroy-on-close>
			<el-form :model="scenarioForm" label-position="top" :rules="formRules" ref="scenarioFormRef">
				<FormItem label="场景名称" prop="title" tooltipKey="title">
					<el-input v-model="scenarioForm.title" placeholder="输入场景名称" />
				</FormItem>

				<FormItem label="场景类型" prop="type" tooltipKey="type">
					<el-select v-model="scenarioForm.type" placeholder="选择场景类型" style="width: 100%">
						<el-option label="冒险探索" value="adventure" />
						<el-option label="悬疑调查" value="mystery" />
						<el-option label="能力训练" value="training" />
						<el-option label="深渊危机" value="abyss-crisis" />
						<el-option label="组织任务" value="bureau-mission" />
						<el-option label="其他类型" value="other" />
					</el-select>
				</FormItem>

				<FormItem label="场景描述" prop="description" tooltipKey="description">
					<el-input v-model="scenarioForm.description" type="textarea" :rows="5" placeholder="描述你的场景内容..." />
				</FormItem>

				<FormItem label="角色设定" prop="characterCount" tooltipKey="characterCount">
					<el-input v-model="scenarioForm.characterCount" placeholder="描述场景中的角色 (可选)" />
				</FormItem>
			</el-form>

			<template #footer>
				<div class="dialog-footer">
					<el-button @click="dialogVisible = false">取消</el-button>
					<el-button type="primary" @click="saveScenario">保存</el-button>
				</div>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";

const router = useRouter();
const loading = ref(false);
const dialogVisible = ref(false);
const isEditMode = ref(false);
const currentScenarioIndex = ref(-1);
const scenarioFormRef = ref<FormInstance>();

// 表单规则
const formRules = reactive<FormRules>({
	title: [
		{ required: true, message: "请输入场景名称", trigger: "blur" },
		{ min: 2, max: 30, message: "长度应在 2 到 30 个字符之间", trigger: "blur" },
	],
	type: [{ required: true, message: "请选择场景类型", trigger: "change" }],
	description: [
		{ required: true, message: "请输入场景描述", trigger: "blur" },
		{ min: 10, max: 500, message: "长度应在 10 到 500 个字符之间", trigger: "blur" },
	],
});

// 场景数据
interface Scenario {
	id: string;
	title: string;
	type: string;
	description: string;
	characterCount?: string;
	createdAt: number;
	updatedAt?: number;
}

// 场景数据列表
const scenarios = ref<Scenario[]>([]);

// 表单数据
const scenarioForm = reactive({
	title: "",
	type: "",
	description: "",
	characterCount: "",
});

// 生成唯一ID
const generateId = () => {
	return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
};

// 加载场景数据
const loadScenarios = () => {
	loading.value = true;
	try {
		const savedScenarios = localStorage.getItem("userScenarios");
		if (savedScenarios) {
			scenarios.value = JSON.parse(savedScenarios);
		} else {
			// 初始化一些示例场景
			scenarios.value = [
				{
					id: generateId(),
					title: "古老遗迹探索",
					type: "adventure",
					description:
						"S市郊外发现了一处据信有千年历史的超能者遗迹，你和苏御被派往调查。遗迹中有只有你能解读的神秘符文，可能揭示异能起源的秘密。",
					characterCount: "苏御、林局长、调查小组",
					createdAt: Date.now() - 7 * 24 * 60 * 60 * 1000,
				},
				{
					id: generateId(),
					title: "深渊裂缝封印",
					type: "abyss-crisis",
					description:
						"城市中心突然出现大规模深渊生物入侵，已造成多人伤亡。第七局派遣你与苏御前往处理。这次入侵背后似乎有人为操控的痕迹。",
					characterCount: "苏御、李阳、成安",
					createdAt: Date.now() - 3 * 24 * 60 * 60 * 1000,
				},
				{
					id: generateId(),
					title: "能力觉醒指导",
					type: "training",
					description:
						"你刚刚觉醒了描述系能力，第七局派遣苏御协助你理解并掌握这种罕见的异能。在训练过程中，你逐渐发现自己的能力有着不同寻常的特性。",
					characterCount: "苏御、新人训练员",
					createdAt: Date.now() - 1 * 24 * 60 * 60 * 1000,
				},
			];
			saveToLocalStorage();
		}
	} catch (error) {
		console.error("加载场景数据失败", error);
		ElMessage.error("加载场景数据失败");
	} finally {
		loading.value = false;
	}
};

// 保存到本地存储
const saveToLocalStorage = () => {
	localStorage.setItem("userScenarios", JSON.stringify(scenarios.value));
};

// 创建新场景
const createNewScenario = () => {
	resetForm();
	isEditMode.value = false;
	dialogVisible.value = true;
};

// 编辑场景
const editScenario = (scenario: Scenario) => {
	isEditMode.value = true;
	currentScenarioIndex.value = scenarios.value.findIndex((s) => s.id === scenario.id);

	// 填充表单
	scenarioForm.title = scenario.title;
	scenarioForm.type = scenario.type;
	scenarioForm.description = scenario.description;
	scenarioForm.characterCount = scenario.characterCount || "";

	dialogVisible.value = true;
};

// 删除场景
const deleteScenario = (scenario: Scenario) => {
	ElMessageBox.confirm(`确定要删除场景 "${scenario.title}" 吗？此操作不可恢复。`, "删除确认", {
		confirmButtonText: "确定",
		cancelButtonText: "取消",
		type: "warning",
	})
		.then(() => {
			scenarios.value = scenarios.value.filter((s) => s.id !== scenario.id);
			saveToLocalStorage();
			ElMessage.success("场景已删除");
		})
		.catch(() => {
			// 用户取消操作
		});
};

// 体验场景
const playScenario = (scenario: Scenario) => {
	// 保存场景到 localStorage 供故事页面使用
	const playerData = {
		name: localStorage.getItem("playerName") || "游客",
		background: localStorage.getItem("playerBackground") || "",
		scenario: {
			id: "custom-scene",
			title: scenario.title,
			description: scenario.description,
		},
	};

	localStorage.setItem("playerData", JSON.stringify(playerData));

	// 跳转到故事体验页面
	router.push("/chat/story");
};

// 保存场景
const saveScenario = async () => {
	if (!scenarioFormRef.value) return;

	await scenarioFormRef.value.validate((valid) => {
		if (valid) {
			if (isEditMode.value && currentScenarioIndex.value >= 0) {
				// 更新现有场景
				const updatedScenario = {
					...scenarios.value[currentScenarioIndex.value],
					title: scenarioForm.title,
					type: scenarioForm.type,
					description: scenarioForm.description,
					characterCount: scenarioForm.characterCount,
					updatedAt: Date.now(),
				};

				scenarios.value[currentScenarioIndex.value] = updatedScenario;
				ElMessage.success("场景更新成功");
			} else {
				// 创建新场景
				const newScenario: Scenario = {
					id: generateId(),
					title: scenarioForm.title,
					type: scenarioForm.type,
					description: scenarioForm.description,
					characterCount: scenarioForm.characterCount,
					createdAt: Date.now(),
				};

				scenarios.value.unshift(newScenario);
				ElMessage.success("新场景创建成功");
			}

			saveToLocalStorage();
			dialogVisible.value = false;
		}
	});
};

// 重置表单
const resetForm = () => {
	if (scenarioFormRef.value) {
		scenarioFormRef.value.resetFields();
	}

	scenarioForm.title = "";
	scenarioForm.type = "";
	scenarioForm.description = "";
	scenarioForm.characterCount = "";
	currentScenarioIndex.value = -1;
};

// 格式化日期时间
const formatDateTime = (timestamp: number) => {
	const date = new Date(timestamp);
	const year = date.getFullYear();
	const month = String(date.getMonth() + 1).padStart(2, "0");
	const day = String(date.getDate()).padStart(2, "0");
	const hours = String(date.getHours()).padStart(2, "0");
	const minutes = String(date.getMinutes()).padStart(2, "0");

	return `${year}-${month}-${day} ${hours}:${minutes}`;
};

// 获取场景类型标签
const getScenarioTypeTag = (type: string): any => {
	const typeMap: Record<string, "" | "success" | "warning" | "info" | "primary" | "danger"> = {
		adventure: "success",
		mystery: "warning",
		training: "info",
		"abyss-crisis": "danger",
		"bureau-mission": "primary",
		other: "",
	};

	return typeMap[type] || "";
};

// 获取场景类型名称
const getScenarioTypeName = (type: string): string => {
	const typeMap: Record<string, string> = {
		adventure: "冒险探索",
		mystery: "悬疑调查",
		training: "能力训练",
		"abyss-crisis": "深渊危机",
		"bureau-mission": "组织任务",
		other: "其他类型",
	};

	return typeMap[type] || "未知类型";
};

// 组件挂载时加载数据
onMounted(() => {
	loadScenarios();
});
</script>

<style scoped>
.scenarios-container {
	padding: 20px;
}

.header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 30px;
}

.title {
	font-size: 24px;
	color: var(--el-text-color-primary);
	margin: 0;
}

.create-btn {
	background-color: var(--el-color-primary);
}

.scenarios-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
	gap: 20px;
}

.scenario-card {
	background: var(--el-bg-color);
	border-radius: 10px;
	padding: 20px;
	position: relative;
	transition: all 0.3s ease;
	box-shadow: var(--el-box-shadow-light);
	display: flex;
	flex-direction: column;
}

.scenario-card:hover {
	transform: translateY(-2px);
	box-shadow: var(--el-box-shadow);
}

.scenario-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 15px;
}

.scenario-title {
	font-size: 18px;
	margin: 0;
	color: var(--el-text-color-primary);
}

.scenario-description {
	color: var(--el-text-color-regular);
	font-size: 14px;
	line-height: 1.5;
	margin-bottom: 15px;
	flex-grow: 1;
	overflow: hidden;
	display: -webkit-box;
	-webkit-line-clamp: 3;
	-webkit-box-orient: vertical;
}

.scenario-meta {
	margin-bottom: 15px;
}

.meta-item {
	display: flex;
	align-items: center;
	gap: 6px;
	font-size: 13px;
	color: var(--el-text-color-secondary);
	margin-bottom: 5px;
}

.scenario-actions {
	display: flex;
	justify-content: space-between;
	margin-top: auto;
}

.action-button {
	flex: 1;
	padding: 8px 0;
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 5px;
	font-size: 14px;
}

.play-button {
	background-color: var(--el-color-primary);
	color: white;
	border: none;
}

.edit-button {
	background-color: var(--el-color-info);
	color: white;
	border: none;
}

.delete-button {
	background-color: var(--el-color-danger);
	color: white;
	border: none;
}

@media (max-width: 768px) {
	.scenarios-grid {
		grid-template-columns: 1fr;
	}

	.header {
		flex-direction: column;
		align-items: flex-start;
		gap: 15px;
	}

	.create-btn {
		width: 100%;
	}
}
</style>
