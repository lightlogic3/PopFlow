<template>
	<div class="setup-container">
		<div class="header">
			<h1 class="title">Ultimate Esper</h1>
			<div class="subtitle">Curse of Description - Interactive Plot</div>
		</div>

		<div class="setup-card">
			<h2 class="setup-title">Begin Your Esper Adventure</h2>

			<div class="setup-section">
				<h3 class="section-title">Personal Information</h3>
				<div class="form-group">
					<label for="playerName">Your Name</label>
					<el-input v-model="playerName" placeholder="Enter your name in the story" />
				</div>
				<div class="form-group">
					<label for="playerBackground">Background Story</label>
					<div class="preset-options">
						<div
							v-for="(option, index) in backgroundOptions"
							:key="index"
							:class="['preset-option', { selected: selectedBackground === option.value }]"
							@click="selectBackground(option.value)"
						>
							{{ option.label }}
						</div>
						<div
							class="preset-option custom-toggle"
							:class="{ selected: isCustomBackground }"
							@click="selectCustomBackground"
						>
							Custom Background
						</div>
					</div>
					<el-input
						v-model="playerBackground"
						type="textarea"
						:rows="4"
						placeholder="Describe your personal background story..."
						@input="handleBackgroundInput"
					/>
				</div>
			</div>

			<div class="setup-section">
				<h3 class="section-title">Character Attributes</h3>
				<p class="attributes-tip">
					Initial attribute points: <span class="remaining-points">{{ remainingPoints }}</span> points to allocate
				</p>

				<div class="attributes-grid">
					<div v-for="(value, key) in attributes" :key="key" class="attribute-item">
						<div class="attribute-header">
							<span class="attribute-name">{{ attributeInfo[key]?.name || key }}</span>
							<span class="attribute-value">{{ value }}</span>
						</div>
						<div class="attribute-description">{{ attributeInfo[key]?.description || "Custom attribute" }}</div>
						<div class="attribute-controls">
							<el-button size="small" @click="decreaseAttribute(key)" :disabled="value <= 5">-</el-button>
							<el-slider
								v-model="attributes[key]"
								:min="5"
								:max="20"
								:disabled="remainingPoints <= 0 && attributes[key] < 20"
								@change="handleAttributeChange"
							></el-slider>
							<el-button size="small" @click="increaseAttribute(key)" :disabled="remainingPoints <= 0">+</el-button>
						</div>
						<el-button
							v-if="!defaultAttributes.includes(key + '')"
							class="remove-attribute-btn"
							size="small"
							type="danger"
							@click="removeAttribute(key)"
						>
							Remove
						</el-button>
					</div>

					<div class="add-attribute-item">
						<el-button class="add-attribute-btn" @click="showAddAttributeDialog = true">
							<i class="el-icon-plus"></i> Add Custom Attribute
						</el-button>
					</div>
				</div>

				<div class="attribute-stats">
					<div class="stat-row">
						<span class="stat-label">Health Maximum:</span>
						<span class="stat-value">{{ calculateStat("health") }}</span>
					</div>
					<div class="stat-row">
						<span class="stat-label">Mental Energy Maximum:</span>
						<span class="stat-value">{{ calculateStat("mana") }}</span>
					</div>
					<div class="stat-row">
						<span class="stat-label">Physical Attack:</span>
						<span class="stat-value">{{ calculateStat("attack") }}</span>
					</div>
					<div class="stat-row">
						<span class="stat-label">Esper Power:</span>
						<span class="stat-value">{{ calculateStat("ability") }}</span>
					</div>
					<div class="stat-row">
						<span class="stat-label">Initial Money:</span>
						<span class="stat-value">{{ initialGold }}</span>
					</div>
				</div>
			</div>

			<div class="setup-section">
				<h3 class="section-title">Select Scenario</h3>
				<div class="scenario-options">
					<div
						v-for="scenario in scenarios"
						:key="scenario.id"
						:class="['scenario-option', { selected: selectedScenario === scenario.id }]"
						@click="selectScenario(scenario.id)"
					>
						<div class="scenario-title">{{ scenario.title }}</div>
						<div class="scenario-desc">{{ scenario.desc }}</div>
					</div>
					<div
						class="scenario-option custom-scenario"
						:class="{ active: isCustomScenario, selected: selectedScenario === 'custom' }"
						@click="toggleCustomScenario"
					>
						<div class="scenario-title">Custom Scenario</div>
						<div class="scenario-desc" v-if="!isCustomScenario">Create your own story scenario...</div>
						<div class="custom-field" v-if="isCustomScenario">
							<el-input v-model="customScenarioTitle" placeholder="Enter scenario title" />
							<el-input v-model="customScenarioDesc" type="textarea" :rows="3" placeholder="Describe your custom scenario..." />
						</div>
					</div>
				</div>
			</div>

			<div class="setup-section">
				<h3 class="section-title">Select Companion NPCs</h3>
				<p class="npc-tip">Select NPCs that will appear in your adventure, multiple selection allowed</p>

				<div class="npc-options">
					<div
						v-for="npc in npcOptions"
						:key="npc.id"
						:class="['npc-option', { selected: selectedNpcs.includes(npc.id) }]"
						@click="toggleNpc(npc.id)"
					>
						<div
							class="npc-avatar"
							:style="{ backgroundImage: `url(${npc.avatar || 'https://placekitten.com/100/100'})` }"
						></div>
						<div class="npc-info">
							<div class="npc-name">{{ npc.name }}</div>
							<div class="npc-role">{{ npc.role }}</div>
							<div class="npc-desc">{{ npc.description }}</div>
						</div>
						<div class="npc-select-mark" v-if="selectedNpcs.includes(npc.id)">
							<i class="el-icon-check"></i>
						</div>
					</div>

					<div class="npc-option custom-npc" @click="showAddNpcDialog = true">
						<div class="npc-avatar custom-avatar">+</div>
						<div class="npc-info">
							<div class="npc-name">Custom NPC</div>
							<div class="npc-role">Create your own NPC character</div>
							<div class="npc-desc">Add a custom character to appear in your adventure</div>
						</div>
					</div>
				</div>

				<div class="selected-npcs-preview" v-if="selectedNpcs.length > 0">
					<div class="preview-title">Selected {{ selectedNpcs.length }} NPCs:</div>
					<div class="preview-list">
						<div v-for="npcId in selectedNpcs" :key="npcId" class="preview-item">
							{{ getNpcName(npcId) }}
							<span class="remove-npc" @click.stop="removeNpc(npcId)">×</span>
						</div>
					</div>
				</div>
			</div>

			<el-button type="primary" class="start-btn" @click="startStory">Start Story</el-button>
		</div>
	</div>

	<!-- Add attribute dialog -->
	<el-dialog title="Add Custom Attribute" v-model="showAddAttributeDialog" width="500px">
		<el-form :model="newAttribute" label-width="80px">
			<FormItem label="Attribute Name" tooltipKey="name">
				<el-input v-model="newAttribute.name" placeholder="Enter attribute name"></el-input>
			</FormItem>
			<FormItem label="Attribute Key" tooltipKey="key">
				<el-input v-model="newAttribute.key" placeholder="Enter attribute key (English)"></el-input>
			</FormItem>
			<FormItem label="Attribute Description" tooltipKey="description">
				<el-input v-model="newAttribute.description" type="textarea" placeholder="Describe the purpose of this attribute"></el-input>
			</FormItem>
		</el-form>
		<template #footer>
			<span class="dialog-footer">
				<el-button @click="showAddAttributeDialog = false">Cancel</el-button>
				<el-button type="primary" @click="addAttribute">Confirm</el-button>
			</span>
		</template>
	</el-dialog>

	<!-- Add NPC dialog -->
	<el-dialog title="Add Custom NPC" v-model="showAddNpcDialog" width="500px">
		<el-form :model="newNpc" label-width="80px">
			<FormItem label="NPC Name" tooltipKey="name">
				<el-input v-model="newNpc.name" placeholder="Enter NPC name"></el-input>
			</FormItem>
			<FormItem label="Identity/Role" tooltipKey="role">
				<el-input v-model="newNpc.role" placeholder="Enter NPC's identity or profession"></el-input>
			</FormItem>
			<FormItem label="Appearance" tooltipKey="appearance">
				<el-input v-model="newNpc.appearance" type="textarea" placeholder="Describe NPC's appearance"></el-input>
			</FormItem>
			<FormItem label="Personality" tooltipKey="personality">
				<el-input v-model="newNpc.personality" type="textarea" placeholder="Describe NPC's personality traits"></el-input>
			</FormItem>
			<FormItem label="Background Story" tooltipKey="background">
				<el-input v-model="newNpc.background" type="textarea" placeholder="Briefly describe NPC's background story"></el-input>
			</FormItem>
		</el-form>
		<template #footer>
			<span class="dialog-footer">
				<el-button @click="showAddNpcDialog = false">Cancel</el-button>
				<el-button type="primary" @click="addCustomNpc">Confirm</el-button>
			</span>
		</template>
	</el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";

const router = useRouter();
const playerName = ref("");
const playerBackground = ref("");
const selectedBackground = ref("");
const isCustomBackground = ref(false);
const selectedScenario = ref("deep-abyss");
const isCustomScenario = ref(false);
const customScenarioTitle = ref("");
const customScenarioDesc = ref("");

// Background story options
const backgroundOptions = [
	{ label: "College Student", value: "I am an ordinary college student who discovered that I have special abilities and was recruited by the Seventh Bureau as a trainee ability user." },
	{ label: "Veteran", value: "As a military veteran with extensive combat experience, I awakened my ability during an accident, attracting the attention of the Seventh Bureau." },
	{ label: "Investigative Journalist", value: "I was originally an investigative journalist who accidentally gained descriptive abilities while investigating a supernatural event." },
	{
		label: "Doctor",
		value: "As a doctor, I developed ability mutations while rescuing patients infected with Abyss contamination, enabling me to alter material properties through descriptions.",
	},
	{ label: "Police Officer", value: "I was once a police officer who was involved in an anomalous phenomenon while pursuing supernatural criminals, and since then gained the ability to manipulate descriptions." },
];

// Scenario options
const scenarios = [
	{
		id: "deep-abyss",
		title: "Abyss Crisis",
		desc: "Multiple Abyss creatures have appeared in the Northern Industrial Zone, causing chaos. Regular teams cannot control the situation, and the Seventh Bureau needs your special abilities to deal with this crisis.",
	},
	{
		id: "seventh-bureau",
		title: "Seventh Bureau Newcomer",
		desc: "As a new member of the Seventh Bureau, you will assist in guiding another description-type ability user, Wang Ming, to master his ability while better understanding your own power.",
	},
	{
		id: "mysterious-relic",
		title: "Ancient Relic",
		desc: "An ancient relic suspected to be related to ability users has been discovered in S City, and the Seventh Bureau has sealed off the site. Director Lin specifically requests you to investigate because there are texts and symbols that only you can interpret.",
	},
	{
		id: "ability-awakening",
		title: "Ability Awakening",
		desc: "You've just awakened your descriptive ability and are learning how to control it. The Seventh Bureau has sent someone to contact you, hoping to help you understand and master this rare ability.",
	},
];

// Attribute info interface definition
interface AttributeInfo {
	name: string;
	description: string;
}

// Attribute dictionary interface
interface AttributeDict {
	[key: string]: number;
}

// Attribute info dictionary interface
interface AttributeInfoDict {
	[key: string]: AttributeInfo;
}

// Add attribute-related variables beneath existing variable definitions
const initialPoints = 50;
const baseAttributeValue = 5;
// Default attribute list
const defaultAttributes = ["strength", "spirit", "agility", "intelligence", "charm"];
// Custom attribute key list
const attributeKeys = ref<string[]>([...defaultAttributes]);
// Attribute detailed information
const attributeInfo = ref<AttributeInfoDict>({
	strength: { name: "Constitution", description: "Determines your health limit and physical resistance" },
	spirit: { name: "Spirit", description: "Determines your mental energy and ability effects" },
	agility: { name: "Agility", description: "Determines your movement speed and evasion ability" },
	intelligence: { name: "Intelligence", description: "Affects your choice effects and dialogue responses" },
	charm: { name: "Charm", description: "Affects NPC attitudes and special dialogue options" },
});

// Dynamic attribute related
const showAddAttributeDialog = ref(false);
const newAttribute = ref({
	name: "",
	key: "",
	description: "",
});

// Player attributes
const attributes = ref<AttributeDict>({
	strength: baseAttributeValue,
	spirit: baseAttributeValue,
	agility: baseAttributeValue,
	intelligence: baseAttributeValue,
	charm: baseAttributeValue,
});

// Calculate remaining distributable points
const remainingPoints = computed(() => {
	let usedPoints = 0;
	for (const key in attributes.value) {
		usedPoints += attributes.value[key] - baseAttributeValue;
	}
	return initialPoints - usedPoints;
});

// Add initial gold value
const initialGold = ref(100);

// Function to calculate derived attributes
function calculateStat(statType: "health" | "mana" | "attack" | "ability"): number {
	switch (statType) {
		case "health":
			return 100 + (attributes.value.strength || 0) * 10;
		case "mana":
			return 50 + (attributes.value.spirit || 0) * 10;
		case "attack":
			return 5 + (attributes.value.strength || 0) * 2 + (attributes.value.agility || 0);
		case "ability":
			return 5 + (attributes.value.intelligence || 0) * 2 + (attributes.value.spirit || 0);
		default:
			return 0;
	}
}

// Handle attribute changes
const handleAttributeChange = () => {
	// If remaining points are negative, revert the last change
	if (remainingPoints.value < 0) {
		ElMessage.warning("Attribute points have been exhausted");
		// Set upper limit for all attributes
		for (const key in attributes.value) {
			if (attributes.value[key] > 20) {
				attributes.value[key] = 20;
			}
		}
	}
};

// Increase attribute value
const increaseAttribute = (attr: any) => {
	if (remainingPoints.value > 0 && attributes.value[attr] < 20) {
		attributes.value[attr]++;
	}
};

// Decrease attribute value
const decreaseAttribute = (attr: any) => {
	if (attributes.value[attr] > baseAttributeValue) {
		attributes.value[attr]--;
	}
};

// Add new attribute
const addAttribute = () => {
	if (!newAttribute.value.name || !newAttribute.value.key || !newAttribute.value.description) {
		ElMessage.warning("Please complete all attribute information");
		return;
	}

	// Check if attribute key already exists
	if (attributes.value.hasOwnProperty(newAttribute.value.key)) {
		ElMessage.warning("Attribute key already exists, please change it");
		return;
	}

	// Add to attribute key list
	attributeKeys.value.push(newAttribute.value.key);

	// Add to attribute information
	attributeInfo.value[newAttribute.value.key] = {
		name: newAttribute.value.name,
		description: newAttribute.value.description,
	};

	// Add to player attributes
	attributes.value[newAttribute.value.key] = baseAttributeValue;

	// Reset new attribute form
	newAttribute.value = { name: "", key: "", description: "" };
	showAddAttributeDialog.value = false;

	ElMessage.success("Custom attribute added successfully");
};

// Remove attribute
const removeAttribute = (key: any) => {
	if (defaultAttributes.includes(key)) {
		ElMessage.warning("Default attributes cannot be removed");
		return;
	}

	// Remove from attribute key list
	const index = attributeKeys.value.indexOf(key);
	if (index !== -1) {
		attributeKeys.value.splice(index, 1);
	}

	// Remove attribute
	delete attributes.value[key];
	delete attributeInfo.value[key];

	ElMessage.success("Attribute has been removed");
};

// Select preset background
const selectBackground = (value: string) => {
	selectedBackground.value = value;
	playerBackground.value = value;
	isCustomBackground.value = false;
};

// Select custom background
const selectCustomBackground = () => {
	isCustomBackground.value = true;
	selectedBackground.value = "";
	playerBackground.value = "";
};

// Handle background input
const handleBackgroundInput = () => {
	// Check if it matches a preset background
	const matchedOption = backgroundOptions.find((option) => option.value === playerBackground.value);
	if (matchedOption) {
		selectedBackground.value = matchedOption.value;
		isCustomBackground.value = false;
	} else if (playerBackground.value) {
		isCustomBackground.value = true;
		selectedBackground.value = "";
	} else {
		isCustomBackground.value = false;
		selectedBackground.value = "";
	}
};

// Select preset scenario
const selectScenario = (id: string) => {
	selectedScenario.value = id;
	isCustomScenario.value = false;
};

// Toggle custom scenario
const toggleCustomScenario = () => {
	isCustomScenario.value = !isCustomScenario.value;
	if (isCustomScenario.value) {
		selectedScenario.value = "custom";
	} else {
		selectedScenario.value = "deep-abyss";
	}
};

// NPC-related data interface
interface NpcOption {
	id: string;
	name: string;
	role: string;
	description: string;
	avatar?: string;
	appearance?: string;
	personality?: string;
	background?: string;
}

// Custom NPC form
const newNpc = ref({
	name: "",
	role: "",
	appearance: "",
	personality: "",
	background: "",
});

// NPC selection related variables
const showAddNpcDialog = ref(false);
const selectedNpcs = ref<string[]>([]);
const customNpcs = ref<NpcOption[]>([]);

// Preset NPC options
const npcOptions = computed(() => {
	const presetNpcs: NpcOption[] = [
		{
			id: "li-yang",
			name: "Li Yang",
			role: "Seventh Bureau - Sensory Ability User",
			description: "An ability user who can sense danger, very sensitive to surroundings, but has average combat abilities.",
			avatar: "",
		},
		{
			id: "ji-xiang",
			name: "Ji Xiang",
			role: "Seventh Bureau - Combat Ability User",
			description: "A powerful combat ability user, battle-hardened, capable of protecting teammates in danger, with a steady personality.",
			avatar: "",
		},
		{
			id: "lin-director",
			name: "Director Lin",
			role: "Seventh Bureau Director",
			description: "Leader of the Seventh Bureau, politically adept, with extensive experience in ability management and immeasurable powers.",
			avatar: "",
		},
		{
			id: "cheng-an",
			name: "Cheng An",
			role: "Seventh Bureau Deputy Director",
			description: "Deputy director with a radical approach to ability incidents, powerful but decisive, sometimes appearing cold.",
			avatar: "",
		},
		{
			id: "gu-qiu",
			name: "Gu Qiu",
			role: "Mysterious Figure",
			description: "A mysterious figure with an enigmatic identity, seems to have unique understanding of the Abyss, with ambiguous attitudes.",
			avatar: "",
		},
	];

	// Combine preset and custom NPCs
	return [...presetNpcs, ...customNpcs.value];
});

// Toggle NPC selection status
const toggleNpc = (npcId: string) => {
	const index = selectedNpcs.value.indexOf(npcId);
	if (index === -1) {
		selectedNpcs.value.push(npcId);
	} else {
		selectedNpcs.value.splice(index, 1);
	}
};

// Remove selected NPC
const removeNpc = (npcId: string) => {
	const index = selectedNpcs.value.indexOf(npcId);
	if (index !== -1) {
		selectedNpcs.value.splice(index, 1);
	}
};

// Get NPC name
const getNpcName = (npcId: string) => {
	const npc = npcOptions.value.find((n) => n.id === npcId);
	return npc ? npc.name : "Unknown NPC";
};

// Add custom NPC
const addCustomNpc = () => {
	if (!newNpc.value.name || !newNpc.value.role) {
		ElMessage.warning("Please fill in at least the NPC name and identity/role");
		return;
	}

	// Generate unique ID
	const customId = `custom-npc-${Date.now()}`;

	// Create new NPC object
	const customNpc: NpcOption = {
		id: customId,
		name: newNpc.value.name,
		role: newNpc.value.role,
		description: `${newNpc.value.appearance ? "Appearance: " + newNpc.value.appearance.substring(0, 20) + "... " : ""}${
			newNpc.value.personality ? "Personality: " + newNpc.value.personality.substring(0, 20) + "..." : ""
		}`,
		appearance: newNpc.value.appearance,
		personality: newNpc.value.personality,
		background: newNpc.value.background,
	};

	// Add to custom NPC list
	customNpcs.value.push(customNpc);

	// Automatically select newly added NPC
	selectedNpcs.value.push(customId);

	// Reset form
	newNpc.value = {
		name: "",
		role: "",
		appearance: "",
		personality: "",
		background: "",
	};

	showAddNpcDialog.value = false;
	ElMessage.success("Custom NPC added successfully");
};

// Start story
const startStory = () => {
	if (!playerName.value) {
		ElMessage.warning("Please enter your name");
		return;
	}

	if (!playerBackground.value) {
		ElMessage.warning("Please select or enter your background story");
		return;
	}

	// Create character data
	const playerData = {
		name: playerName.value,
		background: playerBackground.value,
		scenario:
			selectedScenario.value === "custom"
				? {
						id: "custom-scene",
						title: customScenarioTitle.value || "Custom Scenario",
						description: customScenarioDesc.value || "Player-created custom scenario",
				  }
				: scenarios.find((s) => s.id === selectedScenario.value),
		attributes: {
			...attributes.value,
			attributeInfo: attributeInfo.value,
			level: 1,
			experience: 0,
			health: calculateStat("health"),
			maxHealth: calculateStat("health"),
			mana: calculateStat("mana"),
			maxMana: calculateStat("mana"),
			attack: calculateStat("attack"),
			ability: calculateStat("ability"),
			gold: initialGold.value,
			items: [],
		},
		npcs: selectedNpcs.value
			.map((npcId) => {
				const npc = npcOptions.value.find((n) => n.id === npcId);
				if (!npc) return null;

				return {
					id: npc.id,
					name: npc.name,
					role: npc.role,
					description: npc.description,
					appearance: npc.appearance || "",
					personality: npc.personality || "",
					background: npc.background || "",
					relationship: 50, // Initial relationship level
					trust: 50, // Initial trust level
				};
			})
			.filter(Boolean),
	};

	// Save to local storage
	localStorage.setItem("playerData", JSON.stringify(playerData));

	// Navigate to story page
	router.push("/chat/story");
};

// Check for saved data when page loads
onMounted(() => {
	const savedData = localStorage.getItem("playerData");
	if (savedData) {
		try {
			const data = JSON.parse(savedData);
			playerName.value = data.name || "";
			selectedBackground.value = data.background || "civilian";
			selectedScenario.value = data.scenario || "investigation";
			customScenarioTitle.value = data.scenario?.title || "";
			customScenarioDesc.value = data.scenario?.description || "";

			// Restore attributes
			if (data.attributes) {
				// Restore custom attributes
				const customAttrs = Object.keys(data.attributes).filter(
					(key) =>
						![
							"health",
							"maxHealth",
							"mana",
							"maxMana",
							"attack",
							"ability",
							"gold",
							"level",
							"experience",
							"items",
							"attributeInfo",
						].includes(key) && !defaultAttributes.includes(key),
				);

				// Add custom attributes to key list
				for (const key of customAttrs) {
					if (!attributeKeys.value.includes(key)) {
						attributeKeys.value.push(key);
						attributes.value[key] = data.attributes[key];
					}
				}

				// Restore default attribute values
				for (const key of defaultAttributes) {
					if (data.attributes[key]) {
						attributes.value[key] = data.attributes[key];
					}
				}

				// Restore attribute information
				if (data.attributes.attributeInfo) {
					for (const key in data.attributes.attributeInfo) {
						attributeInfo.value[key] = data.attributes.attributeInfo[key];
					}
				}
			}
		} catch (error) {
			console.error("Error parsing saved data:", error);
		}
	}
});
</script>

<style scoped>
.setup-container {
	padding: 20px;
	min-height: 100vh;
	background-color: #121212;
	color: #f0f0f0;
	background-image: url("https://picsum.photos/1920/1080?blur=5");
	background-size: cover;
	background-position: center;
	background-attachment: fixed;
	position: relative;
}

.setup-container::before {
	content: "";
	position: absolute;
	top: 0;
	left: 0;
	width: 100%;
	height: 100%;
	background-color: rgba(0, 0, 0, 0.7);
	z-index: 0;
}

.header {
	text-align: center;
	margin-bottom: 30px;
	position: relative;
	z-index: 1;
}

.title {
	font-size: 42px;
	color: #e91e63;
	text-shadow: 0 0 15px rgba(233, 30, 99, 0.5);
	letter-spacing: 3px;
	margin-bottom: 15px;
}

.subtitle {
	font-size: 20px;
	color: #aaa;
	font-style: italic;
}

.setup-card {
	background-color: rgba(20, 20, 20, 0.8);
	border-radius: 15px;
	padding: 40px;
	box-shadow: 0 0 30px rgba(0, 0, 0, 0.7);
	animation: fadeIn 0.8s ease;
	position: relative;
	z-index: 1;
	max-width: 1000px;
	margin: 0 auto;
}

@keyframes fadeIn {
	from {
		opacity: 0;
		transform: translateY(20px);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}

.setup-title {
	font-size: 24px;
	color: #e91e63;
	margin-bottom: 30px;
	text-align: center;
}

.setup-section {
	margin-bottom: 30px;
}

.section-title {
	font-size: 18px;
	color: #fff;
	margin-bottom: 15px;
	display: flex;
	align-items: center;
}

.section-title::before {
	content: "";
	display: inline-block;
	width: 8px;
	height: 20px;
	background-color: #e91e63;
	margin-right: 10px;
	border-radius: 4px;
}

.form-group {
	margin-bottom: 20px;
}

label {
	display: block;
	margin-bottom: 8px;
	color: #ccc;
}

.preset-options {
	display: flex;
	flex-wrap: wrap;
	gap: 10px;
	margin-bottom: 15px;
}

.preset-option {
	background-color: rgba(40, 40, 40, 0.9);
	border: 1px solid #555;
	border-radius: 8px;
	padding: 8px 15px;
	font-size: 14px;
	color: #ccc;
	cursor: pointer;
	transition: all 0.3s;
}

.preset-option:hover {
	background-color: rgba(60, 60, 60, 0.9);
	border-color: #e91e63;
}

.preset-option.selected {
	background-color: rgba(233, 30, 99, 0.3);
	border-color: #e91e63;
	color: white;
}

.scenario-options {
	display: grid;
	grid-template-columns: repeat(2, 1fr);
	gap: 15px;
}

.scenario-option {
	background-color: rgba(40, 40, 40, 0.9);
	border: 1px solid #555;
	border-radius: 10px;
	padding: 15px;
	cursor: pointer;
	transition: all 0.3s;
}

.scenario-option:hover {
	background-color: rgba(60, 60, 60, 0.9);
	border-color: #e91e63;
}

.scenario-option.selected {
	background-color: rgba(233, 30, 99, 0.3);
	border-color: #e91e63;
	box-shadow: 0 0 15px rgba(233, 30, 99, 0.3);
}

.scenario-title {
	font-size: 18px;
	color: #fff;
	margin-bottom: 8px;
}

.scenario-desc {
	font-size: 14px;
	color: #aaa;
}

.start-btn {
	background-color: #e91e63;
	color: white;
	border: none;
	border-radius: 30px;
	padding: 15px 30px;
	font-size: 18px;
	cursor: pointer;
	transition: all 0.3s;
	display: block;
	width: 200px;
	margin: 40px auto 0;
	text-align: center;
}

.start-btn:hover {
	background-color: #c2185b;
	box-shadow: 0 0 20px rgba(233, 30, 99, 0.5);
	transform: translateY(-3px);
}

/* Custom scenario related styles */
.custom-scenario .custom-field {
	display: flex;
	flex-direction: column;
	gap: 10px;
}

.custom-scenario.active {
	height: auto;
}

.attributes-grid {
	display: grid;
	grid-template-columns: repeat(2, 1fr);
	gap: 20px;
	margin-bottom: 20px;
}

.attributes-tip {
	margin-bottom: 15px;
	color: #e91e63;
	font-weight: 600;
}

.remaining-points {
	font-weight: bold;
	font-size: 18px;
}

.attribute-item {
	background-color: rgba(40, 40, 40, 0.9);
	border-radius: 10px;
	padding: 15px;
	transition: all 0.3s;
	position: relative;
}

.attribute-header {
	display: flex;
	justify-content: space-between;
	margin-bottom: 8px;
}

.attribute-name {
	color: #e91e63;
	font-weight: bold;
	font-size: 16px;
}

.attribute-value {
	color: #fff;
	font-weight: bold;
	font-size: 18px;
}

.attribute-description {
	color: #aaa;
	font-size: 12px;
	margin-bottom: 10px;
}

.attribute-controls {
	display: flex;
	align-items: center;
	gap: 10px;
}

.attribute-controls .el-slider {
	flex: 1;
}

.add-attribute-item {
	background-color: rgba(40, 40, 40, 0.5);
	border-radius: 10px;
	padding: 15px;
	display: flex;
	align-items: center;
	justify-content: center;
	cursor: pointer;
	transition: all 0.3s;
	border: 1px dashed #555;
}

.add-attribute-item:hover {
	background-color: rgba(60, 60, 60, 0.5);
	border-color: #e91e63;
}

.add-attribute-btn {
	width: 100%;
	height: 100%;
	background: transparent;
	border: none;
	color: #e91e63;
	font-weight: bold;
}

.remove-attribute-btn {
	position: absolute;
	top: 10px;
	right: 10px;
	padding: 3px 8px;
	font-size: 12px;
}

.attribute-stats {
	background-color: rgba(20, 20, 20, 0.8);
	border-radius: 10px;
	padding: 15px;
	margin-top: 20px;
}

.stat-row {
	display: flex;
	justify-content: space-between;
	margin-bottom: 10px;
	padding-bottom: 10px;
	border-bottom: 1px solid rgba(100, 100, 100, 0.3);
}

.stat-row:last-child {
	margin-bottom: 0;
	padding-bottom: 0;
	border-bottom: none;
}

.stat-label {
	color: #ccc;
}

.stat-value {
	color: #e91e63;
	font-weight: bold;
}

@media (max-width: 768px) {
	.scenario-options {
		grid-template-columns: 1fr;
	}

	.setup-card {
		padding: 20px;
	}

	.title {
		font-size: 32px;
	}

	.attributes-grid {
		grid-template-columns: 1fr;
	}
}

/* NPC selection part styles */
.npc-tip {
	font-size: 14px;
	color: #888;
	margin-bottom: 15px;
}

.npc-options {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
	gap: 15px;
	margin-bottom: 20px;
}

.npc-option {
	background-color: rgba(30, 30, 40, 0.7);
	border-radius: 8px;
	padding: 15px;
	display: flex;
	position: relative;
	cursor: pointer;
	transition: all 0.3s ease;
	border: 1px solid transparent;
	overflow: hidden;
}

.npc-option:hover {
	background-color: rgba(40, 40, 50, 0.8);
	transform: translateY(-3px);
	box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
}

.npc-option.selected {
	border-color: #e91e63;
	background-color: rgba(50, 30, 40, 0.8);
}

.npc-avatar {
	width: 60px;
	height: 60px;
	border-radius: 50%;
	background-color: #333;
	margin-right: 15px;
	flex-shrink: 0;
	background-size: cover;
	background-position: center;
}

.custom-avatar {
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 30px;
	color: #aaa;
	background-color: rgba(60, 60, 70, 0.5);
}

.npc-info {
	flex: 1;
}

.npc-name {
	font-size: 18px;
	font-weight: bold;
	color: #e91e63;
	margin-bottom: 5px;
}

.npc-role {
	font-size: 14px;
	color: #ccc;
	margin-bottom: 8px;
}

.npc-desc {
	font-size: 13px;
	color: #aaa;
	line-height: 1.4;
}

.npc-select-mark {
	position: absolute;
	top: 10px;
	right: 10px;
	width: 24px;
	height: 24px;
	border-radius: 50%;
	background-color: #e91e63;
	display: flex;
	align-items: center;
	justify-content: center;
	color: white;
}

.custom-npc {
	border-style: dashed;
	border-color: #666;
}

.selected-npcs-preview {
	background-color: rgba(30, 30, 40, 0.7);
	border-radius: 8px;
	padding: 12px 15px;
	margin-bottom: 20px;
}

.preview-title {
	font-size: 15px;
	color: #ccc;
	margin-bottom: 10px;
}

.preview-list {
	display: flex;
	flex-wrap: wrap;
	gap: 10px;
}

.preview-item {
	background-color: rgba(60, 60, 70, 0.7);
	border-radius: 20px;
	padding: 5px 12px;
	font-size: 14px;
	color: #e0e0e0;
	display: flex;
	align-items: center;
}

.remove-npc {
	margin-left: 6px;
	font-size: 16px;
	color: #999;
	cursor: pointer;
}

.remove-npc:hover {
	color: #e91e63;
}
</style>
