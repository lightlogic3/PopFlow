<template>
	<div class="scenarios-container">
		<div class="header">
			<h1 class="title">Story Scenario Management</h1>
			<el-button type="primary" @click="createNewScenario" class="create-btn">
				<el-icon><Plus /></el-icon>
				Create New Scenario
			</el-button>
		</div>

		<div class="scenarios-grid" v-loading="loading">
			<el-empty v-if="scenarios.length === 0" description="No custom scenarios available" />

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
						<span>Created: {{ formatDateTime(scenario.createdAt) }}</span>
					</div>
					<div class="meta-item">
						<el-icon><User /></el-icon>
						<span>Character Setup: {{ scenario.characterCount || "Not specified" }}</span>
					</div>
				</div>

				<div class="scenario-actions">
					<el-button class="action-button play-button" @click="playScenario(scenario)">
						<el-icon><VideoPlay /></el-icon>
						Play
					</el-button>
					<el-button class="action-button edit-button" @click="editScenario(scenario)">
						<el-icon><Edit /></el-icon>
						Edit
					</el-button>
					<el-button class="action-button delete-button" @click="deleteScenario(scenario)">
						<el-icon><Delete /></el-icon>
						Delete
					</el-button>
				</div>
			</div>
		</div>

		<!-- New/Edit Scenario Dialog -->
		<el-dialog v-model="dialogVisible" :title="isEditMode ? 'Edit Scenario' : 'Create New Scenario'" width="600px" destroy-on-close>
			<el-form :model="scenarioForm" label-position="top" :rules="formRules" ref="scenarioFormRef">
				<FormItem label="Scenario Name" prop="title" tooltipKey="title">
					<el-input v-model="scenarioForm.title" placeholder="Enter scenario name" />
				</FormItem>

				<FormItem label="Scenario Type" prop="type" tooltipKey="type">
					<el-select v-model="scenarioForm.type" placeholder="Select scenario type" style="width: 100%">
						<el-option label="Adventure Exploration" value="adventure" />
						<el-option label="Mystery Investigation" value="mystery" />
						<el-option label="Ability Training" value="training" />
						<el-option label="Abyss Crisis" value="abyss-crisis" />
						<el-option label="Bureau Mission" value="bureau-mission" />
						<el-option label="Other Type" value="other" />
					</el-select>
				</FormItem>

				<FormItem label="Scenario Description" prop="description" tooltipKey="description">
					<el-input v-model="scenarioForm.description" type="textarea" :rows="5" placeholder="Describe your scenario content..." />
				</FormItem>

				<FormItem label="Character Setup" prop="characterCount" tooltipKey="characterCount">
					<el-input v-model="scenarioForm.characterCount" placeholder="Describe characters in the scenario (optional)" />
				</FormItem>
			</el-form>

			<template #footer>
				<div class="dialog-footer">
					<el-button @click="dialogVisible = false">Cancel</el-button>
					<el-button type="primary" @click="saveScenario">Save</el-button>
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

// Form rules
const formRules = reactive<FormRules>({
	title: [
		{ required: true, message: "Please enter scenario name", trigger: "blur" },
		{ min: 2, max: 30, message: "Length should be between 2 and 30 characters", trigger: "blur" },
	],
	type: [{ required: true, message: "Please select scenario type", trigger: "change" }],
	description: [
		{ required: true, message: "Please enter scenario description", trigger: "blur" },
		{ min: 10, max: 500, message: "Length should be between 10 and 500 characters", trigger: "blur" },
	],
});

// Scenario data
interface Scenario {
	id: string;
	title: string;
	type: string;
	description: string;
	characterCount?: string;
	createdAt: number;
	updatedAt?: number;
}

// Scenario data list
const scenarios = ref<Scenario[]>([]);

// Form data
const scenarioForm = reactive({
	title: "",
	type: "",
	description: "",
	characterCount: "",
});

// Generate unique ID
const generateId = () => {
	return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
};

// Load scenario data
const loadScenarios = () => {
	loading.value = true;
	try {
		const savedScenarios = localStorage.getItem("userScenarios");
		if (savedScenarios) {
			scenarios.value = JSON.parse(savedScenarios);
		} else {
			// Initialize some example scenarios
			scenarios.value = [
				{
					id: generateId(),
					title: "Ancient Relic Exploration",
					type: "adventure",
					description:
						"A thousand-year-old ability user relic has been discovered on the outskirts of S City. You and Su Yu have been dispatched to investigate. The relic contains mysterious symbols that only you can interpret, potentially revealing the secret origin of abilities.",
					characterCount: "Su Yu, Director Lin, Investigation Team",
					createdAt: Date.now() - 7 * 24 * 60 * 60 * 1000,
				},
				{
					id: generateId(),
					title: "Abyss Rift Sealing",
					type: "abyss-crisis",
					description:
						"A large-scale Abyss creature invasion has suddenly appeared in the city center, causing multiple casualties. The Seventh Bureau has sent you and Su Yu to handle the situation. There seems to be evidence of human manipulation behind this invasion.",
					characterCount: "Su Yu, Li Yang, Cheng An",
					createdAt: Date.now() - 3 * 24 * 60 * 60 * 1000,
				},
				{
					id: generateId(),
					title: "Ability Awakening Guidance",
					type: "training",
					description:
						"You have just awakened your description-type ability, and the Seventh Bureau has sent Su Yu to help you understand and master this rare ability. During training, you gradually discover that your ability has unusual characteristics.",
					characterCount: "Su Yu, New Trainee",
					createdAt: Date.now() - 1 * 24 * 60 * 60 * 1000,
				},
			];
			saveToLocalStorage();
		}
	} catch (error) {
		console.error("Failed to load scenario data", error);
		ElMessage.error("Failed to load scenario data");
	} finally {
		loading.value = false;
	}
};

// Save to local storage
const saveToLocalStorage = () => {
	localStorage.setItem("userScenarios", JSON.stringify(scenarios.value));
};

// Create new scenario
const createNewScenario = () => {
	resetForm();
	isEditMode.value = false;
	dialogVisible.value = true;
};

// Edit scenario
const editScenario = (scenario: Scenario) => {
	isEditMode.value = true;
	currentScenarioIndex.value = scenarios.value.findIndex((s) => s.id === scenario.id);

	// Fill the form
	scenarioForm.title = scenario.title;
	scenarioForm.type = scenario.type;
	scenarioForm.description = scenario.description;
	scenarioForm.characterCount = scenario.characterCount || "";

	dialogVisible.value = true;
};

// Delete scenario
const deleteScenario = (scenario: Scenario) => {
	ElMessageBox.confirm(`Are you sure you want to delete the scenario "${scenario.title}"? This action cannot be undone.`, "Delete Confirmation", {
		confirmButtonText: "Confirm",
		cancelButtonText: "Cancel",
		type: "warning",
	})
		.then(() => {
			scenarios.value = scenarios.value.filter((s) => s.id !== scenario.id);
			saveToLocalStorage();
			ElMessage.success("Scenario has been deleted");
		})
		.catch(() => {
			// User canceled operation
		});
};

// Play scenario
const playScenario = (scenario: Scenario) => {
	// Save scenario to localStorage for the story page
	const playerData = {
		name: localStorage.getItem("playerName") || "Visitor",
		background: localStorage.getItem("playerBackground") || "",
		scenario: {
			id: "custom-scene",
			title: scenario.title,
			description: scenario.description,
		},
	};

	localStorage.setItem("playerData", JSON.stringify(playerData));

	// Navigate to the story experience page
	router.push("/chat/story");
};

// Save scenario
const saveScenario = async () => {
	if (!scenarioFormRef.value) return;

	await scenarioFormRef.value.validate((valid) => {
		if (valid) {
			if (isEditMode.value && currentScenarioIndex.value >= 0) {
				// Update existing scenario
				const updatedScenario = {
					...scenarios.value[currentScenarioIndex.value],
					title: scenarioForm.title,
					type: scenarioForm.type,
					description: scenarioForm.description,
					characterCount: scenarioForm.characterCount,
					updatedAt: Date.now(),
				};

				scenarios.value[currentScenarioIndex.value] = updatedScenario;
				ElMessage.success("Scenario updated successfully");
			} else {
				// Create new scenario
				const newScenario: Scenario = {
					id: generateId(),
					title: scenarioForm.title,
					type: scenarioForm.type,
					description: scenarioForm.description,
					characterCount: scenarioForm.characterCount,
					createdAt: Date.now(),
				};

				scenarios.value.unshift(newScenario);
				ElMessage.success("New scenario created successfully");
			}

			saveToLocalStorage();
			dialogVisible.value = false;
		}
	});
};

// Reset form
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

// Format date time
const formatDateTime = (timestamp: number) => {
	const date = new Date(timestamp);
	const year = date.getFullYear();
	const month = String(date.getMonth() + 1).padStart(2, "0");
	const day = String(date.getDate()).padStart(2, "0");
	const hours = String(date.getHours()).padStart(2, "0");
	const minutes = String(date.getMinutes()).padStart(2, "0");

	return `${year}-${month}-${day} ${hours}:${minutes}`;
};

// Get scenario type tag
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

// Get scenario type name
const getScenarioTypeName = (type: string): string => {
	const typeMap: Record<string, string> = {
		adventure: "Adventure Exploration",
		mystery: "Mystery Investigation",
		training: "Ability Training",
		"abyss-crisis": "Abyss Crisis",
		"bureau-mission": "Bureau Mission",
		other: "Other Type",
	};

	return typeMap[type] || "Unknown Type";
};

// Load data when component is mounted
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
