<template>
	<div class="setup-container">
		<div class="header">
			<h1 class="title">史上最强异能者</h1>
			<div class="subtitle">描述之厄 - 互动剧情</div>
		</div>

		<div class="setup-card">
			<h2 class="setup-title">开始你的异能冒险</h2>

			<div class="setup-section">
				<h3 class="section-title">个人信息</h3>
				<div class="form-group">
					<label for="playerName">你的名字</label>
					<el-input v-model="playerName" placeholder="输入你在故事中的名字" />
				</div>
				<div class="form-group">
					<label for="playerBackground">背景故事</label>
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
							自定义背景
						</div>
					</div>
					<el-input
						v-model="playerBackground"
						type="textarea"
						:rows="4"
						placeholder="描述你的个人背景故事..."
						@input="handleBackgroundInput"
					/>
				</div>
			</div>

			<div class="setup-section">
				<h3 class="section-title">角色属性</h3>
				<p class="attributes-tip">
					初始属性点数：<span class="remaining-points">{{ remainingPoints }}</span> 点可分配
				</p>

				<div class="attributes-grid">
					<div v-for="(value, key) in attributes" :key="key" class="attribute-item">
						<div class="attribute-header">
							<span class="attribute-name">{{ attributeInfo[key]?.name || key }}</span>
							<span class="attribute-value">{{ value }}</span>
						</div>
						<div class="attribute-description">{{ attributeInfo[key]?.description || "自定义属性" }}</div>
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
							移除
						</el-button>
					</div>

					<div class="add-attribute-item">
						<el-button class="add-attribute-btn" @click="showAddAttributeDialog = true">
							<i class="el-icon-plus"></i> 添加自定义属性
						</el-button>
					</div>
				</div>

				<div class="attribute-stats">
					<div class="stat-row">
						<span class="stat-label">生命值上限:</span>
						<span class="stat-value">{{ calculateStat("health") }}</span>
					</div>
					<div class="stat-row">
						<span class="stat-label">精神力上限:</span>
						<span class="stat-value">{{ calculateStat("mana") }}</span>
					</div>
					<div class="stat-row">
						<span class="stat-label">物理攻击:</span>
						<span class="stat-value">{{ calculateStat("attack") }}</span>
					</div>
					<div class="stat-row">
						<span class="stat-label">异能强度:</span>
						<span class="stat-value">{{ calculateStat("ability") }}</span>
					</div>
					<div class="stat-row">
						<span class="stat-label">初始金钱:</span>
						<span class="stat-value">{{ initialGold }}</span>
					</div>
				</div>
			</div>

			<div class="setup-section">
				<h3 class="section-title">选择剧情场景</h3>
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
						<div class="scenario-title">自定义场景</div>
						<div class="scenario-desc" v-if="!isCustomScenario">创建你自己的故事场景...</div>
						<div class="custom-field" v-if="isCustomScenario">
							<el-input v-model="customScenarioTitle" placeholder="输入场景标题" />
							<el-input v-model="customScenarioDesc" type="textarea" :rows="3" placeholder="描述你的自定义场景..." />
						</div>
					</div>
				</div>
			</div>

			<div class="setup-section">
				<h3 class="section-title">选择同伴NPC</h3>
				<p class="npc-tip">选择将在冒险中遇到的NPC角色，可多选</p>

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
							<div class="npc-name">自定义NPC</div>
							<div class="npc-role">创建你自己的NPC角色</div>
							<div class="npc-desc">添加一个自定义的角色以在冒险中出现</div>
						</div>
					</div>
				</div>

				<div class="selected-npcs-preview" v-if="selectedNpcs.length > 0">
					<div class="preview-title">已选择 {{ selectedNpcs.length }} 个NPC:</div>
					<div class="preview-list">
						<div v-for="npcId in selectedNpcs" :key="npcId" class="preview-item">
							{{ getNpcName(npcId) }}
							<span class="remove-npc" @click.stop="removeNpc(npcId)">×</span>
						</div>
					</div>
				</div>
			</div>

			<el-button type="primary" class="start-btn" @click="startStory">开始故事</el-button>
		</div>
	</div>

	<!-- 添加属性对话框 -->
	<el-dialog title="添加自定义属性" v-model="showAddAttributeDialog" width="500px">
		<el-form :model="newAttribute" label-width="80px">
			<FormItem label="属性名称" tooltipKey="name">
				<el-input v-model="newAttribute.name" placeholder="输入属性名称"></el-input>
			</FormItem>
			<FormItem label="属性键名" tooltipKey="key">
				<el-input v-model="newAttribute.key" placeholder="输入属性键名(英文)"></el-input>
			</FormItem>
			<FormItem label="属性描述" tooltipKey="description">
				<el-input v-model="newAttribute.description" type="textarea" placeholder="描述此属性的作用"></el-input>
			</FormItem>
		</el-form>
		<template #footer>
			<span class="dialog-footer">
				<el-button @click="showAddAttributeDialog = false">取消</el-button>
				<el-button type="primary" @click="addAttribute">确定</el-button>
			</span>
		</template>
	</el-dialog>

	<!-- 添加NPC对话框 -->
	<el-dialog title="添加自定义NPC" v-model="showAddNpcDialog" width="500px">
		<el-form :model="newNpc" label-width="80px">
			<FormItem label="NPC名称" tooltipKey="name">
				<el-input v-model="newNpc.name" placeholder="输入NPC名称"></el-input>
			</FormItem>
			<FormItem label="身份/职业" tooltipKey="role">
				<el-input v-model="newNpc.role" placeholder="输入NPC的身份或职业"></el-input>
			</FormItem>
			<FormItem label="外观描述" tooltipKey="appearance">
				<el-input v-model="newNpc.appearance" type="textarea" placeholder="描述NPC的外观特征"></el-input>
			</FormItem>
			<FormItem label="性格特点" tooltipKey="personality">
				<el-input v-model="newNpc.personality" type="textarea" placeholder="描述NPC的性格特点"></el-input>
			</FormItem>
			<FormItem label="背景故事" tooltipKey="background">
				<el-input v-model="newNpc.background" type="textarea" placeholder="简要描述NPC的背景故事"></el-input>
			</FormItem>
		</el-form>
		<template #footer>
			<span class="dialog-footer">
				<el-button @click="showAddNpcDialog = false">取消</el-button>
				<el-button type="primary" @click="addCustomNpc">确定</el-button>
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

// 背景故事选项
const backgroundOptions = [
	{ label: "普通大学生", value: "我是一名普通大学生，偶然发现自己拥有特殊能力，被第七局招募成为见习能力者。" },
	{ label: "退役军人", value: "作为一名退役军人，我具备丰富的作战经验，在一次意外中觉醒了能力，引起了第七局的注意。" },
	{ label: "调查记者", value: "我原本是一名调查记者，在追查一起超能力相关事件时，意外获得了描述类能力。" },
	{
		label: "医生",
		value: "身为医生的我在一次抢救深渊污染患者的过程中，自身产生了能力变异，能够通过描述改变物质特性。",
	},
	{ label: "警察", value: "我曾是一名警察，在一次追捕超能力犯罪分子时被卷入异常现象，从此获得了操控描述的能力。" },
];

// 场景选项
const scenarios = [
	{
		id: "deep-abyss",
		title: "深渊危机",
		desc: "多个深渊生物在北部工业区出现，引发混乱。常规小队无法控制局面，第七局需要你的特殊能力来应对这一危机。",
	},
	{
		id: "seventh-bureau",
		title: "第七局新人",
		desc: "作为第七局的新成员，你将协助指导另一位描述系能力者王铭掌握他的能力，同时更好地了解自己的力量。",
	},
	{
		id: "mysterious-relic",
		title: "远古遗迹",
		desc: "S市发现了疑似超能力者的远古遗迹，第七局封锁了现场。林局长特别要求你前往调查，因为那里有只有你能解读的文字和符号。",
	},
	{
		id: "ability-awakening",
		title: "能力觉醒",
		desc: "你刚刚觉醒了描述系能力，正在学习如何控制它。第七局派人接触你，希望帮助你理解并掌握这种罕见的能力。",
	},
];

// 属性信息接口定义
interface AttributeInfo {
	name: string;
	description: string;
}

// 属性字典接口
interface AttributeDict {
	[key: string]: number;
}

// 属性信息字典接口
interface AttributeInfoDict {
	[key: string]: AttributeInfo;
}

// 在已有的变量定义下方添加属性相关的变量
const initialPoints = 50;
const baseAttributeValue = 5;
// 默认属性列表
const defaultAttributes = ["strength", "spirit", "agility", "intelligence", "charm"];
// 自定义属性键列表
const attributeKeys = ref<string[]>([...defaultAttributes]);
// 属性详细信息
const attributeInfo = ref<AttributeInfoDict>({
	strength: { name: "体质", description: "决定你的生命上限和物理抗性" },
	spirit: { name: "精神", description: "决定你的精神力和异能效果" },
	agility: { name: "敏捷", description: "决定你的行动速度和闪避能力" },
	intelligence: { name: "智力", description: "影响你的选择效果和对话反应" },
	charm: { name: "魅力", description: "影响NPC态度和特殊对话选项" },
});

// 动态属性相关
const showAddAttributeDialog = ref(false);
const newAttribute = ref({
	name: "",
	key: "",
	description: "",
});

// 玩家属性
const attributes = ref<AttributeDict>({
	strength: baseAttributeValue,
	spirit: baseAttributeValue,
	agility: baseAttributeValue,
	intelligence: baseAttributeValue,
	charm: baseAttributeValue,
});

// 计算剩余可分配点数
const remainingPoints = computed(() => {
	let usedPoints = 0;
	for (const key in attributes.value) {
		usedPoints += attributes.value[key] - baseAttributeValue;
	}
	return initialPoints - usedPoints;
});

// 添加初始金币值
const initialGold = ref(100);

// 计算衍生属性的函数
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

// 处理属性变化
const handleAttributeChange = () => {
	// 如果剩余点数为负，则回退最后一次变化
	if (remainingPoints.value < 0) {
		ElMessage.warning("属性点数已用完");
		// 给所有属性设置上限
		for (const key in attributes.value) {
			if (attributes.value[key] > 20) {
				attributes.value[key] = 20;
			}
		}
	}
};

// 增加属性值
const increaseAttribute = (attr: any) => {
	if (remainingPoints.value > 0 && attributes.value[attr] < 20) {
		attributes.value[attr]++;
	}
};

// 减少属性值
const decreaseAttribute = (attr: any) => {
	if (attributes.value[attr] > baseAttributeValue) {
		attributes.value[attr]--;
	}
};

// 添加新属性
const addAttribute = () => {
	if (!newAttribute.value.name || !newAttribute.value.key || !newAttribute.value.description) {
		ElMessage.warning("请完整填写属性信息");
		return;
	}

	// 检查属性键名是否已存在
	if (attributes.value.hasOwnProperty(newAttribute.value.key)) {
		ElMessage.warning("属性键名已存在，请更换");
		return;
	}

	// 添加到属性键列表
	attributeKeys.value.push(newAttribute.value.key);

	// 添加到属性信息
	attributeInfo.value[newAttribute.value.key] = {
		name: newAttribute.value.name,
		description: newAttribute.value.description,
	};

	// 添加到玩家属性
	attributes.value[newAttribute.value.key] = baseAttributeValue;

	// 重置新属性表单
	newAttribute.value = { name: "", key: "", description: "" };
	showAddAttributeDialog.value = false;

	ElMessage.success("自定义属性添加成功");
};

// 移除属性
const removeAttribute = (key: any) => {
	if (defaultAttributes.includes(key)) {
		ElMessage.warning("默认属性不能移除");
		return;
	}

	// 从属性键列表中移除
	const index = attributeKeys.value.indexOf(key);
	if (index !== -1) {
		attributeKeys.value.splice(index, 1);
	}

	// 移除属性
	delete attributes.value[key];
	delete attributeInfo.value[key];

	ElMessage.success("属性已移除");
};

// 选择预设背景
const selectBackground = (value: string) => {
	selectedBackground.value = value;
	playerBackground.value = value;
	isCustomBackground.value = false;
};

// 选择自定义背景
const selectCustomBackground = () => {
	isCustomBackground.value = true;
	selectedBackground.value = "";
	playerBackground.value = "";
};

// 处理背景输入
const handleBackgroundInput = () => {
	// 检查是否匹配预设背景
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

// 选择预设场景
const selectScenario = (id: string) => {
	selectedScenario.value = id;
	isCustomScenario.value = false;
};

// 切换自定义场景
const toggleCustomScenario = () => {
	isCustomScenario.value = !isCustomScenario.value;
	if (isCustomScenario.value) {
		selectedScenario.value = "custom";
	} else {
		selectedScenario.value = "deep-abyss";
	}
};

// NPC相关数据接口
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

// 自定义NPC表单
const newNpc = ref({
	name: "",
	role: "",
	appearance: "",
	personality: "",
	background: "",
});

// NPC选择相关变量
const showAddNpcDialog = ref(false);
const selectedNpcs = ref<string[]>([]);
const customNpcs = ref<NpcOption[]>([]);

// 预设NPC选项
const npcOptions = computed(() => {
	const presetNpcs: NpcOption[] = [
		{
			id: "li-yang",
			name: "李阳",
			role: "第七局-感知系能力者",
			description: "能够感知危险的能力者，对周围环境非常敏感，但战斗能力一般。",
			avatar: "",
		},
		{
			id: "ji-xiang",
			name: "季祥",
			role: "第七局-战斗系能力者",
			description: "强大的战斗系能力者，身经百战，能在危险中保护队友，性格沉稳。",
			avatar: "",
		},
		{
			id: "lin-director",
			name: "林局长",
			role: "第七局局长",
			description: "第七局的领导者，深谙政治，拥有丰富的异能管理经验和深不可测的能力。",
			avatar: "",
		},
		{
			id: "cheng-an",
			name: "成安",
			role: "第七局副局长",
			description: "有着激进处理异能事件倾向的副局长，能力强大但行事果断，有时略显冷酷。",
			avatar: "",
		},
		{
			id: "gu-qiu",
			name: "顾秋",
			role: "神秘人物",
			description: "身份成谜的神秘人物，似乎对深渊有着独特的了解，态度暧昧不明。",
			avatar: "",
		},
	];

	// 合并预设和自定义NPC
	return [...presetNpcs, ...customNpcs.value];
});

// 切换NPC选择状态
const toggleNpc = (npcId: string) => {
	const index = selectedNpcs.value.indexOf(npcId);
	if (index === -1) {
		selectedNpcs.value.push(npcId);
	} else {
		selectedNpcs.value.splice(index, 1);
	}
};

// 移除已选NPC
const removeNpc = (npcId: string) => {
	const index = selectedNpcs.value.indexOf(npcId);
	if (index !== -1) {
		selectedNpcs.value.splice(index, 1);
	}
};

// 获取NPC名称
const getNpcName = (npcId: string) => {
	const npc = npcOptions.value.find((n) => n.id === npcId);
	return npc ? npc.name : "未知NPC";
};

// 添加自定义NPC
const addCustomNpc = () => {
	if (!newNpc.value.name || !newNpc.value.role) {
		ElMessage.warning("请至少填写NPC名称和身份/职业");
		return;
	}

	// 生成唯一ID
	const customId = `custom-npc-${Date.now()}`;

	// 创建新的NPC对象
	const customNpc: NpcOption = {
		id: customId,
		name: newNpc.value.name,
		role: newNpc.value.role,
		description: `${newNpc.value.appearance ? "外观：" + newNpc.value.appearance.substring(0, 20) + "... " : ""}${
			newNpc.value.personality ? "性格：" + newNpc.value.personality.substring(0, 20) + "..." : ""
		}`,
		appearance: newNpc.value.appearance,
		personality: newNpc.value.personality,
		background: newNpc.value.background,
	};

	// 添加到自定义NPC列表
	customNpcs.value.push(customNpc);

	// 自动选中新添加的NPC
	selectedNpcs.value.push(customId);

	// 重置表单
	newNpc.value = {
		name: "",
		role: "",
		appearance: "",
		personality: "",
		background: "",
	};

	showAddNpcDialog.value = false;
	ElMessage.success("自定义NPC添加成功");
};

// 开始故事
const startStory = () => {
	if (!playerName.value) {
		ElMessage.warning("请输入你的名字");
		return;
	}

	if (!playerBackground.value) {
		ElMessage.warning("请选择或输入你的背景故事");
		return;
	}

	// 创建角色数据
	const playerData = {
		name: playerName.value,
		background: playerBackground.value,
		scenario:
			selectedScenario.value === "custom"
				? {
						id: "custom-scene",
						title: customScenarioTitle.value || "自定义场景",
						description: customScenarioDesc.value || "玩家创建的自定义场景",
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
					relationship: 50, // 初始关系度
					trust: 50, // 初始信任度
				};
			})
			.filter(Boolean),
	};

	// 保存到本地存储
	localStorage.setItem("playerData", JSON.stringify(playerData));

	// 导航到故事页面
	router.push("/chat/story");
};

// 页面加载时检查是否有保存的数据
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

			// 恢复属性
			if (data.attributes) {
				// 恢复自定义属性
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

				// 添加自定义属性到键列表
				for (const key of customAttrs) {
					if (!attributeKeys.value.includes(key)) {
						attributeKeys.value.push(key);
						attributes.value[key] = data.attributes[key];
					}
				}

				// 恢复默认属性值
				for (const key of defaultAttributes) {
					if (data.attributes[key]) {
						attributes.value[key] = data.attributes[key];
					}
				}

				// 恢复属性信息
				if (data.attributes.attributeInfo) {
					for (const key in data.attributes.attributeInfo) {
						attributeInfo.value[key] = data.attributes.attributeInfo[key];
					}
				}
			}
		} catch (error) {
			console.error("解析保存的数据出错:", error);
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

/* 自定义场景相关样式 */
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

/* NPC选择部分样式 */
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
