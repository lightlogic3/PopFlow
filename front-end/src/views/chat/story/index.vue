<template>
	<div class="story-container">
		<!-- 顶部NPC头像列表区域 - 改为一列 -->
		<div class="npc-top-bar">
			<div
				v-for="npc in playerData?.npcs"
				:key="npc.id"
				:class="['npc-avatar-item', { active: currentNpc?.id === npc.id }]"
				@click="selectNpc(npc)"
			>
				<div
					class="npc-avatar"
					:style="{ backgroundImage: npc.avatar ? `url(${npc.avatar})` : 'none' }"
					:title="npc.name"
				>
					<div class="npc-hover-tooltip">{{ npc.name }}</div>
				</div>
			</div>
		</div>

		<div class="game-area">
			<div class="sidebar">
				<!-- 保留玩家属性面板 -->
				<div class="player-panel">
					<div class="panel-header" @click="togglePlayerPanel">
						<h3>{{ playerName }}的属性</h3>
						<i :class="['toggle-icon', isPlayerPanelOpen ? 'open' : '']"></i>
					</div>
					<div class="panel-content" v-show="isPlayerPanelOpen">
						<div class="player-level">
							<span>等级: {{ playerData?.attributes?.level || 1 }}</span>
							<span>经验: {{ playerData?.attributes?.experience || 0 }}/100</span>
						</div>
						<div class="player-stats">
							<div class="stat-group">
								<div class="stat-item">
									<span class="stat-name">生命值</span>
									<span class="stat-value"
										>{{ playerData?.attributes?.health || 0 }}/{{ playerData?.attributes?.maxHealth || 0 }}</span
									>
								</div>
								<div class="stat-item">
									<span class="stat-name">精神力</span>
									<span class="stat-value"
										>{{ playerData?.attributes?.mana || 0 }}/{{ playerData?.attributes?.maxMana || 0 }}</span
									>
								</div>
								<div class="stat-item">
									<span class="stat-name">攻击力</span>
									<span class="stat-value">{{ playerData?.attributes?.attack || 0 }}</span>
								</div>
								<div class="stat-item">
									<span class="stat-name">异能强度</span>
									<span class="stat-value">{{ playerData?.attributes?.ability || 0 }}</span>
								</div>
								<div class="stat-item">
									<span class="stat-name">金钱</span>
									<span class="stat-value">{{ playerData?.attributes?.gold || 0 }}</span>
								</div>
							</div>

							<div class="attributes-list">
								<div v-for="(value, key) in playerAttributes" :key="key" class="attribute-item">
									<span class="attribute-name">{{ getAttributeName(key) }}</span>
									<span class="attribute-value">{{ value }}</span>
								</div>
							</div>

							<div class="inventory" v-if="playerData?.attributes?.items?.length">
								<div class="inventory-title">物品</div>
								<div class="inventory-items">
									<div v-for="(item, index) in playerData.attributes.items" :key="index" class="inventory-item">
										{{ item }}
									</div>
								</div>
							</div>
						</div>
					</div>
				</div>

				<!-- NPC详细信息移到这里 -->
				<div class="npc-detail-panel" v-if="currentNpc">
					<div class="panel-header">
						<h3>{{ currentNpc.name }}</h3>
						<div class="npc-role-badge">{{ currentNpc.role }}</div>
					</div>
					<div class="panel-content">
						<div class="npc-description">{{ currentNpc.description }}</div>

						<div class="npc-stats">
							<div class="stat-item">
								<span class="stat-name">能力等级</span>
								<span class="stat-value">S+</span>
							</div>
							<div class="stat-item">
								<span class="stat-name">关系度</span>
								<span class="stat-value">{{ currentNpc.relationship || relationshipLevel }}</span>
							</div>
							<div class="stat-item">
								<span class="stat-name">信任度</span>
								<span class="stat-value">{{ currentNpc.trust || trustLevel }}%</span>
							</div>
							<div class="stat-item">
								<span class="stat-name">剧情进度</span>
								<span class="stat-value">{{ storyProgress }}</span>
							</div>
						</div>
					</div>
				</div>
			</div>

			<div class="chat-container">
				<div class="chat-messages" ref="chatMessagesRef">
					<div v-for="(message, index) in messages" :key="index" :class="['message', message.type]">
						<span v-if="message.type === 'system'" class="message-label">系统</span>
						<span v-else-if="message.type === 'character'" class="message-label">{{
							getNpcNameById(message.npcId)
						}}</span>
						<span v-else class="message-label">{{ playerName }}</span>

						{{ message.content }}
						<span v-if="message.type !== 'system'" class="message-time">{{ message.time }}</span>
					</div>

					<div v-if="isTyping" class="typing-indicator">
						<div class="message-label">{{ typingNpcName }}</div>
						<div class="typing-dot"></div>
						<div class="typing-dot"></div>
						<div class="typing-dot"></div>
					</div>
				</div>

				<div class="chat-input-container">
					<el-input
						v-model="messageInput"
						placeholder="输入消息..."
						@keyup.enter="sendMessage"
						:disabled="showChoices"
					/>
					<el-button class="send-btn" @click="sendMessage" :disabled="showChoices">发送</el-button>
				</div>
			</div>
		</div>

		<div class="status-bar">
			<div>位置：{{ currentLocation }}</div>
			<div>时间：{{ currentTime }}</div>
			<div>状态：{{ currentStatus }}</div>
		</div>

		<div v-if="showChoices" class="choices-container">
			<div class="choices-title">关键剧情选择</div>
			<div class="choices-list">
				<el-button
					v-for="(choice, index) in currentChoices"
					:key="index"
					class="choice-btn"
					@click="makeChoice(choice)"
				>
					{{ choice.text }}
				</el-button>
			</div>
			<div class="custom-choice">
				<el-input v-model="customChoice" placeholder="输入自定义选择..." />
				<el-button class="custom-choice-btn" @click="makeCustomChoice">确定</el-button>
			</div>
		</div>

		<div v-if="showNotification" class="story-notification">
			{{ notificationText }}
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick, watch, computed } from "vue";
import { useRouter } from "vue-router";

interface Message {
	type: "system" | "character" | "user";
	content: string;
	time?: string;
	npcId?: string;
}

interface Choice {
	text: string;
	consequence: string;
	trust: number;
	relationship: string;
	nextStatus?: string;
	nextLocation?: string;
	npcId?: string;
}

interface NPC {
	id: string;
	name: string;
	role: string;
	description: string;
	appearance?: string;
	personality?: string;
	background?: string;
	relationship?: string;
	trust?: number;
	avatar?: string;
}

const router = useRouter();

// 玩家数据
const playerData = ref<any>(null);
const playerName = ref("游客");
const isPlayerPanelOpen = ref(true);

// NPC相关
const currentNpc = ref<NPC | null>(null);
const defaultNpcId = ref("");
const typingNpcName = ref("");

// 计算玩家基础属性（不包括派生属性如health, mana等）
const playerAttributes = computed(() => {
	if (!playerData.value?.attributes) return {};

	const attributes: Record<string, number> = {};
	const derivedProps = [
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
	];

	for (const key in playerData.value.attributes) {
		if (!derivedProps.includes(key)) {
			attributes[key] = playerData.value.attributes[key];
		}
	}

	return attributes;
});

// 消息相关
const messages = ref<Message[]>([]);
const messageInput = ref("");
const isTyping = ref(false);
const chatMessagesRef = ref<HTMLElement | null>(null);

// 状态相关
const relationshipLevel = ref("友好");
const trustLevel = ref(65);
const storyProgress = ref("第一章");
const currentLocation = ref("城北公园");
const currentTime = ref("14:15");
const currentStatus = ref("调查中");

// 选择相关
const showChoices = ref(false);
const currentChoices = ref<Choice[]>([]);
const customChoice = ref("");

// 通知相关
const showNotification = ref(false);
const notificationText = ref("");

// 选择NPC
const selectNpc = (npc: NPC) => {
	currentNpc.value = npc;
};

// 获取NPC名称通过ID
const getNpcNameById = (npcId?: string): string => {
	if (!npcId) return "苏御";

	const npc = playerData.value?.npcs?.find((n: any) => n.id === npcId);
	return npc ? npc.name : "未知角色";
};

// 切换玩家面板显示
const togglePlayerPanel = () => {
	isPlayerPanelOpen.value = !isPlayerPanelOpen.value;
};

// 获取属性名称
const getAttributeName = (key: string): string => {
	if (playerData.value?.attributes?.attributeInfo?.[key]) {
		return playerData.value.attributes.attributeInfo[key].name;
	}
	return key;
};

// 从localStorage获取玩家数据
const loadPlayerData = () => {
	try {
		const savedData = localStorage.getItem("playerData");
		if (savedData) {
			playerData.value = JSON.parse(savedData);
			playerName.value = playerData.value.name || "游客";

			// 设置默认NPC（苏御）
			defaultNpcId.value = "su-yu";

			// 如果玩家数据中有NPC列表
			if (playerData.value.npcs && playerData.value.npcs.length > 0) {
				// 添加默认的苏御NPC如果不存在
				if (!playerData.value.npcs.some((npc: NPC) => npc.id === defaultNpcId.value)) {
					playerData.value.npcs.unshift({
						id: defaultNpcId.value,
						name: "苏御",
						role: "描述之厄异能拥有者",
						description: "第七局特级顾问",
						relationship: relationshipLevel.value,
						trust: trustLevel.value,
					});
				}
				// 设置当前NPC为第一个NPC（通常是苏御）
				currentNpc.value = playerData.value.npcs[0];
			} else {
				// 如果没有NPC列表，创建一个默认的包含苏御
				playerData.value.npcs = [
					{
						id: defaultNpcId.value,
						name: "苏御",
						role: "描述之厄异能拥有者",
						description: "第七局特级顾问",
						relationship: relationshipLevel.value,
						trust: trustLevel.value,
					},
				];
				currentNpc.value = playerData.value.npcs[0];
			}

			initStory();
		} else {
			// 没有保存的数据，重定向到设置页面
			router.push("/chat/setup");
		}
	} catch (error) {
		console.error("加载玩家数据出错:", error);
		router.push("/chat/setup");
	}
};

// 初始化故事
const initStory = () => {
	// 根据玩家选择的场景初始化不同的开场白
	messages.value = [];

	if (!playerData.value || !playerData.value.scenario) {
		addSystemMessage(`故事开始于一个平凡的下午，${playerName.value}正在城北公园散步，突然发现了一个奇怪的现象...`);
		setTimeout(() => {
			addCharacterMessage(
				"这种能量波动...不太寻常。你注意到那边的黑雾了吗？那不是自然现象，而是深渊的痕迹。",
				defaultNpcId.value,
			);
		}, 1000);
		return;
	}

	// 根据场景ID初始化不同的故事开场
	const scenarioId = playerData.value.scenario.id;

	switch (scenarioId) {
		case "deep-abyss":
			currentLocation.value = "城北公园";
			currentStatus.value = "调查中";
			addSystemMessage(`故事开始于一个平凡的下午，${playerName.value}正在城北公园散步，突然发现了一个奇怪的现象...`);
			setTimeout(() => {
				addCharacterMessage(
					"这种能量波动...不太寻常。你注意到那边的黑雾了吗？那不是自然现象，而是深渊的痕迹。",
					defaultNpcId.value,
				);
			}, 1000);
			break;

		case "seventh-bureau":
			currentLocation.value = "第七局总部";
			currentStatus.value = "任务简报";
			addSystemMessage(
				`今天是${playerName.value}加入第七局的第一天，作为新人的你被安排协助特级顾问苏御处理一起异常事件...`,
			);
			setTimeout(() => {
				addCharacterMessage(
					"欢迎加入第七局。我是苏御，描述系异能者。听说你是新来的，正好我这里有个案子需要协助。城东出现了异常能量波动，我们需要去调查一下。",
					defaultNpcId.value,
				);
			}, 1000);
			break;

		case "mysterious-relic":
			currentLocation.value = "S市郊外";
			currentStatus.value = "遗迹探索";
			addSystemMessage(`S市郊外发现了一处疑似远古异能者留下的遗迹，${playerName.value}和苏御一同被派往调查...`);
			setTimeout(() => {
				addCharacterMessage(
					"据说这处遗迹有上千年历史，远比我们现代记载的异能历史要古老。如果真如情报所说，里面可能藏有关于异能起源的秘密。我们需要小心行事。",
					defaultNpcId.value,
				);
			}, 1000);
			break;

		case "ability-awakening":
			currentLocation.value = "咖啡厅";
			currentStatus.value = "初次接触";
			addSystemMessage(
				`一周前，${playerName.value}突然发现自己拥有了不寻常的能力，正在惶恐不安时，遇到了自称是"第七局"的苏御...`,
			);
			setTimeout(() => {
				addCharacterMessage(
					"别担心，你不是唯一一个拥有特殊能力的人。我能感觉到你的能力还很不稳定，如果不学会控制，可能会伤害到你自己或他人。我可以帮助你。",
					defaultNpcId.value,
				);
			}, 1000);
			break;

		case "custom-scene":
			// 自定义场景
			currentLocation.value = "未知地点";
			currentStatus.value = "剧情进行中";
			addSystemMessage(playerData.value.scenario.description || "故事开始了...");
			setTimeout(() => {
				addCharacterMessage(
					"我是苏御，描述系异能者。很高兴与你相遇在这个特殊的场景中。接下来的旅程，希望我们能够合作顺利。",
					defaultNpcId.value,
				);
			}, 1000);
			break;

		default:
			// 默认场景
			addSystemMessage(`故事开始于一个平凡的下午，${playerName.value}正在城北公园散步，突然发现了一个奇怪的现象...`);
			setTimeout(() => {
				addCharacterMessage(
					"这种能量波动...不太寻常。你注意到那边的黑雾了吗？那不是自然现象，而是深渊的痕迹。",
					defaultNpcId.value,
				);
			}, 1000);
	}

	// 5秒后触发第一个选择
	setTimeout(() => {
		triggerFirstChoice();
	}, 5000);
};

// 添加系统消息
const addSystemMessage = (content: string) => {
	messages.value.push({
		type: "system",
		content,
	});
	scrollToBottom();
};

// 添加角色消息
const addCharacterMessage = (content: string, npcId?: string) => {
	isTyping.value = true;

	// 设置当前正在输入的NPC名称
	typingNpcName.value = getNpcNameById(npcId);

	setTimeout(() => {
		isTyping.value = false;
		const now = new Date();
		const timeStr = `${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")}`;

		messages.value.push({
			type: "character",
			content,
			time: timeStr,
			npcId: npcId || defaultNpcId.value,
		});

		scrollToBottom();
	}, 1500);
};

// 添加用户消息
const addUserMessage = (content: string) => {
	const now = new Date();
	const timeStr = `${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")}`;

	messages.value.push({
		type: "user",
		content,
		time: timeStr,
	});

	scrollToBottom();
};

// 发送消息
const sendMessage = () => {
	const content = messageInput.value.trim();
	if (!content || showChoices.value) return;

	addUserMessage(content);
	messageInput.value = "";

	// 模拟角色回复，使用当前选中的NPC ID
	simulateReply(content, currentNpc.value?.id);

	// 检查是否要触发选择
	if (shouldTriggerChoice(content)) {
		setTimeout(() => {
			showStoryChoices();
		}, 2000);
	}
};

// 模拟角色回复
const simulateReply = (userMessage: string, npcId?: string) => {
	isTyping.value = true;
	typingNpcName.value = getNpcNameById(npcId);

	setTimeout(() => {
		isTyping.value = false;

		// 根据用户消息提供相应回复
		const responses = [
			"有趣的观点。作为一名异能者，我习惯了从不同角度思考问题。深渊的本质远比表面看起来复杂得多。",
			"你的直觉相当敏锐。普通人很难察觉到这些细微的能量波动，或许你也有成为异能者的潜质。",
			"我的'描述之厄'能力可以修改现实的描述，但每次使用都有代价。面对深渊，我需要谨慎选择干预的方式。",
			"第七局内部对处理深渊事件有不同派系。成安主张激进措施，林局长则更为保守。这种分歧影响着我们的每次行动。",
		];

		let responseIndex = Math.floor(Math.random() * responses.length);

		// 如果消息包含特定关键词，给出更针对性的回复
		if (userMessage.includes("深渊") || userMessage.includes("黑雾")) {
			responseIndex = 0;
		} else if (userMessage.includes("能力") || userMessage.includes("异能")) {
			responseIndex = 2;
		} else if (userMessage.includes("第七局") || userMessage.includes("组织")) {
			responseIndex = 3;
		}

		addCharacterMessage(responses[responseIndex], npcId);
	}, 1500);
};

// 检查是否应该触发选择
const shouldTriggerChoice = (message: string) => {
	const triggerKeywords = ["深渊", "黑雾", "危险", "遗迹", "能力", "帮助", "组织", "第七局"];
	return triggerKeywords.some((keyword) => message.includes(keyword));
};

// 触发第一个选择
const triggerFirstChoice = () => {
	// 根据不同场景提供不同的选择
	const scenarioId = playerData.value?.scenario?.id || "deep-abyss";

	switch (scenarioId) {
		case "deep-abyss":
			addSystemMessage("深渊黑雾突然剧烈扩散，情况变得危急...");
			currentChoices.value = [
				{
					text: "主动提出帮助苏御处理深渊裂缝",
					consequence: "你选择了同苏御一起调查深渊事件",
					trust: 15,
					relationship: "信赖",
					nextStatus: "调查深渊裂缝",
					nextLocation: "城北公园深处",
					npcId: defaultNpcId.value,
				},
				{
					text: "按照规定离开危险区域",
					consequence: "你选择了遵循规定离开现场",
					trust: 5,
					relationship: "尊重",
					nextStatus: "返回安全区域",
					nextLocation: "城北公园边缘",
					npcId: defaultNpcId.value,
				},
				{
					text: "询问更多关于深渊和第七局的信息",
					consequence: "你选择了了解更多背景信息",
					trust: 10,
					relationship: "好奇",
					nextStatus: "信息交流",
					nextLocation: "城北公园",
					npcId: defaultNpcId.value,
				},
				{
					text: "观察苏御如何处理这个异常现象",
					consequence: "你选择了观察苏御的行动",
					trust: 8,
					relationship: "观察",
					nextStatus: "旁观异常处理",
					nextLocation: "城北公园",
					npcId: defaultNpcId.value,
				},
			];
			break;

		case "seventh-bureau":
			addSystemMessage("苏御向你介绍了任务的详细情况，并询问你的想法...");
			currentChoices.value = [
				{
					text: "主动提出先行调查异常能量的来源",
					consequence: "你选择了主动承担任务",
					trust: 15,
					relationship: "赞赏",
					nextStatus: "实地调查",
					nextLocation: "城东异常区",
					npcId: defaultNpcId.value,
				},
				{
					text: "建议先查阅类似案例的档案资料",
					consequence: "你选择了谨慎的研究方法",
					trust: 10,
					relationship: "认可",
					nextStatus: "资料研究",
					nextLocation: "第七局档案室",
					npcId: defaultNpcId.value,
				},
				{
					text: "提出自己的能力特点，询问如何配合苏御",
					consequence: "你选择了寻求合作指导",
					trust: 12,
					relationship: "指导",
					nextStatus: "能力协同",
					nextLocation: "第七局训练场",
					npcId: defaultNpcId.value,
				},
				{
					text: "请求苏御先展示一下他的描述能力",
					consequence: "你选择了观摩学习",
					trust: 8,
					relationship: "见习",
					nextStatus: "能力展示",
					nextLocation: "第七局训练场",
					npcId: defaultNpcId.value,
				},
			];
			break;

		// 其他场景的选择...
		default:
			addSystemMessage("情况发生了变化，你需要做出选择...");
			currentChoices.value = [
				{
					text: "主动提出帮助苏御",
					consequence: "你选择了协助苏御",
					trust: 15,
					relationship: "信赖",
					nextStatus: "协作行动",
					nextLocation: currentLocation.value,
					npcId: defaultNpcId.value,
				},
				{
					text: "保持观望态度",
					consequence: "你选择了观察情况",
					trust: 5,
					relationship: "谨慎",
					nextStatus: "观察中",
					nextLocation: currentLocation.value,
					npcId: defaultNpcId.value,
				},
				{
					text: "询问更多信息",
					consequence: "你选择了了解更多背景",
					trust: 10,
					relationship: "好奇",
					nextStatus: "信息收集",
					nextLocation: currentLocation.value,
					npcId: defaultNpcId.value,
				},
				{
					text: "提出自己的想法",
					consequence: "你选择了分享你的见解",
					trust: 12,
					relationship: "开放",
					nextStatus: "思想交流",
					nextLocation: currentLocation.value,
					npcId: defaultNpcId.value,
				},
			];
	}

	showChoices.value = true;
};

// 显示故事选择
const showStoryChoices = () => {
	// 如果已经显示了选择，就不重复显示
	if (showChoices.value) return;

	showChoices.value = true;
};

// 做出选择
const makeChoice = (choice: Choice) => {
	addUserMessage(choice.text);
	showChoices.value = false;

	// 显示通知
	showNotification.value = true;
	notificationText.value = choice.consequence;

	// 更新状态
	if (choice.nextStatus) {
		currentStatus.value = choice.nextStatus;
	}

	if (choice.nextLocation) {
		currentLocation.value = choice.nextLocation;
	}

	// 更新时间
	updateTime();

	// 更新关系和信任度
	if (choice.npcId) {
		// 更新特定NPC的关系和信任度
		const npc = playerData.value?.npcs?.find((n: any) => n.id === choice.npcId);
		if (npc) {
			npc.relationship = choice.relationship;
			npc.trust = Math.min(npc.trust + choice.trust, 100);

			// 如果是当前选中的NPC，更新显示
			if (currentNpc.value && currentNpc.value.id === choice.npcId) {
				currentNpc.value = { ...npc };
			}
		}
	} else {
		// 默认更新全局关系变量
		relationshipLevel.value = choice.relationship;
		trustLevel.value = Math.min(trustLevel.value + choice.trust, 100);
	}

	// 隐藏通知
	setTimeout(() => {
		showNotification.value = false;
	}, 3000);

	// 模拟角色回复
	simulateChoiceResponse(choice);
};

// 自定义选择
const makeCustomChoice = () => {
	if (!customChoice.value.trim()) return;

	addUserMessage(customChoice.value);
	showChoices.value = false;

	// 显示通知
	showNotification.value = true;
	notificationText.value = "剧情分支已触发：自定义选择";

	// 更新时间
	updateTime();

	// 隐藏通知
	setTimeout(() => {
		showNotification.value = false;
	}, 3000);

	// 先添加系统旁白
	addSystemMessage("你选择了一条非常规路径，这可能会带来意想不到的发展...");

	// 延迟显示角色回复
	setTimeout(() => {
		// 模拟角色回复，使用当前选中的NPC
		const customResponse = `对于你的想法，我很感兴趣。这种非常规的思路可能会带来意想不到的效果。让我们试试看吧，${playerName.value}。`;
		simulateTypingAndReply(customResponse, currentNpc.value?.id);
	}, 2000);

	// 清空自定义选择
	customChoice.value = "";
};

// 模拟选择后的回复
const simulateChoiceResponse = (choice: Choice) => {
	// 先添加系统旁白，描述新的剧情走向
	addSystemMessage(`${choice.consequence}。情节向新的方向发展...`);

	// 延迟显示角色回复
	setTimeout(() => {
		let response = "";

		// 根据不同的选择和关系提供不同的回复
		if (choice.relationship === "信赖" || choice.relationship === "赞赏") {
			response = `很高兴你愿意协助我。这种情况确实需要我们共同面对，你的决定很明智，${playerName.value}。`;
		} else if (choice.relationship === "尊重" || choice.relationship === "谨慎") {
			response = "你的谨慎是有道理的。不过既然你已经接触到这个事件，可能已经被卷入其中了。我会尽量确保你的安全。";
		} else if (choice.relationship === "好奇" || choice.relationship === "观察") {
			response = "我理解你的好奇心。深渊现象确实令人着迷，但也充满危险。我可以告诉你更多，但要保持警惕。";
		} else {
			response = "你的选择很有意思。在我们合作的过程中，希望能够互相学习和支持。这次任务对我们都是挑战。";
		}

		// 奖励经验
		rewardExperience(10);

		// 模拟角色回复，使用选择中指定的NPC ID
		simulateTypingAndReply(response, choice.npcId);
	}, 2000); // 延迟2秒后显示NPC回复
};

// 奖励经验值
const rewardExperience = (amount: number) => {
	if (playerData.value && playerData.value.attributes) {
		playerData.value.attributes.experience = (playerData.value.attributes.experience || 0) + amount;

		// 检查是否升级
		if (playerData.value.attributes.experience >= 100) {
			playerData.value.attributes.level = (playerData.value.attributes.level || 1) + 1;
			playerData.value.attributes.experience = playerData.value.attributes.experience - 100;

			// 升级通知
			addSystemMessage(`恭喜！你的等级提升到了${playerData.value.attributes.level}级！`);

			// 增加基础属性
			for (const key in playerAttributes.value) {
				playerData.value.attributes[key] += 1;
			}

			// 更新派生属性
			playerData.value.attributes.maxHealth = 100 + (playerData.value.attributes.strength || 0) * 10;
			playerData.value.attributes.health = playerData.value.attributes.maxHealth;
			playerData.value.attributes.maxMana = 50 + (playerData.value.attributes.spirit || 0) * 10;
			playerData.value.attributes.mana = playerData.value.attributes.maxMana;
			playerData.value.attributes.attack =
				5 + (playerData.value.attributes.strength || 0) * 2 + (playerData.value.attributes.agility || 0);
			playerData.value.attributes.ability =
				5 + (playerData.value.attributes.intelligence || 0) * 2 + (playerData.value.attributes.spirit || 0);
		}

		// 保存更新后的数据
		localStorage.setItem("playerData", JSON.stringify(playerData.value));
	}
};

// 模拟输入和回复
const simulateTypingAndReply = (message: string, npcId?: string) => {
	isTyping.value = true;
	typingNpcName.value = getNpcNameById(npcId);

	setTimeout(() => {
		isTyping.value = false;
		addCharacterMessage(message, npcId);
	}, 1500);
};

// 更新时间
const updateTime = () => {
	const hours = parseInt(currentTime.value.split(":")[0]);
	const minutes = parseInt(currentTime.value.split(":")[1]);

	// 增加3-5分钟
	const newMinutes = minutes + 3 + Math.floor(Math.random() * 3);
	let newHours = hours;

	if (newMinutes >= 60) {
		newHours = (newHours + 1) % 24;
	}

	currentTime.value = `${newHours.toString().padStart(2, "0")}:${(newMinutes % 60).toString().padStart(2, "0")}`;
};

// 滚动到底部
const scrollToBottom = () => {
	nextTick(() => {
		if (chatMessagesRef.value) {
			chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight;
		}
	});
};

// 初始化
onMounted(() => {
	loadPlayerData();

	// 每15分钟提示玩家继续对话
	const inactivityTimer = setInterval(() => {
		if (
			!showChoices.value &&
			messages.value.length > 0 &&
			messages.value[messages.value.length - 1].type !== "system"
		) {
			addSystemMessage("周围的环境似乎有些变化，苏御看起来在等待你的回应...");
		}
	}, 15 * 60 * 1000);

	// 组件卸载时清除定时器
	onBeforeUnmount(() => {
		clearInterval(inactivityTimer);
	});
});

// 监听消息变化，自动滚动到底部
watch(messages, () => {
	scrollToBottom();
});
</script>

<style scoped>
.story-container {
	height: 84vh; /* 固定为屏幕高度 */
	background-color: #121212;
	color: #f0f0f0;
	display: flex;
	flex-direction: column;
	overflow: hidden; /* 防止出现滚动条 */
}

/* 新的顶部NPC头像栏样式 */
.npc-top-bar {
	display: flex;
	background-color: rgba(20, 20, 20, 0.8);
	border-bottom: 1px solid rgba(80, 80, 80, 0.3);
	height: 60px; /* 大幅减小高度 */
	align-items: center;
	padding: 0 15px;
	gap: 12px;
	flex-shrink: 0; /* 防止压缩 */
	overflow-x: auto;
	scrollbar-width: thin;
	scrollbar-color: #444 #222;
}

.npc-top-bar::-webkit-scrollbar {
	height: 4px;
}

.npc-top-bar::-webkit-scrollbar-track {
	background: #222;
}

.npc-top-bar::-webkit-scrollbar-thumb {
	background-color: #444;
	border-radius: 4px;
}

.npc-avatar-item {
	cursor: pointer;
	transition: all 0.2s ease;
	padding: 5px;
	border-radius: 50%;
	border: 2px solid transparent;
	position: relative; /* 添加相对定位 */
}

.npc-avatar-item:hover {
	transform: translateY(-2px);
}

.npc-avatar-item.active {
	border-color: #e91e63;
}

.npc-avatar {
	width: 36px; /* 更小的头像尺寸 */
	height: 36px; /* 更小的头像尺寸 */
	border-radius: 50%;
	background-color: #333;
	background-size: cover;
	background-position: center;
}

/* 添加自定义悬浮提示 */
.npc-hover-tooltip {
	position: absolute;
	top: -35px; /* 改为显示在头像上方 */
	left: 50%;
	transform: translateX(-50%);
	background-color: rgba(20, 20, 20, 0.9);
	color: #e91e63;
	padding: 4px 8px;
	border-radius: 4px;
	font-size: 12px;
	white-space: nowrap;
	opacity: 0;
	visibility: hidden;
	transition: opacity 0.2s, visibility 0.2s;
	z-index: 100; /* 提高z-index */
	pointer-events: none;
	box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
}

/* 确保头像有正确的定位上下文 */
.npc-avatar-item:hover .npc-hover-tooltip {
	opacity: 1;
	visibility: visible;
}

.game-area {
	display: flex;
	flex: 1;
	padding: 0 15px; /* 减少padding */
	margin: 6px 0; /* 减少margin */
	min-height: 0; /* 允许内容压缩 */
	overflow: hidden; /* 防止溢出 */
}

.sidebar {
	width: 260px;
	margin-right: 15px;
	display: flex;
	flex-direction: column;
	gap: 15px;
	overflow-y: auto; /* 添加滚动条支持 */
	scrollbar-width: thin;
	scrollbar-color: #444 #222;
}

.sidebar::-webkit-scrollbar {
	width: 5px;
}

.sidebar::-webkit-scrollbar-track {
	background: #222;
}

.sidebar::-webkit-scrollbar-thumb {
	background-color: #444;
	border-radius: 4px;
}

/* NPC详细信息面板新样式 */
.npc-detail-panel {
	background-color: rgba(30, 30, 30, 0.7);
	border-radius: 10px;
	overflow: hidden;
}

.npc-role-badge {
	font-size: 12px;
	background-color: rgba(233, 30, 99, 0.2);
	color: #e91e63;
	padding: 3px 10px;
	border-radius: 10px;
	margin-left: 10px;
}

.npc-description {
	font-size: 13px;
	line-height: 1.5;
	margin-bottom: 15px;
	color: #ddd;
	background-color: rgba(0, 0, 0, 0.2);
	padding: 10px;
	border-radius: 8px;
}

.npc-stats {
	background-color: rgba(0, 0, 0, 0.3);
	border-radius: 8px;
	padding: 12px;
}

.player-panel {
	background-color: rgba(30, 30, 30, 0.7);
	border-radius: 10px;
	overflow: hidden;
}

.panel-header {
	padding: 10px 12px; /* 减小padding */
	background-color: rgba(40, 40, 40, 0.8);
	display: flex;
	justify-content: space-between;
	align-items: center;
	cursor: pointer;
}

.panel-header h3 {
	margin: 0;
	color: #e91e63;
	font-size: 16px;
}

.toggle-icon {
	width: 16px;
	height: 16px;
	position: relative;
}

.toggle-icon:before,
.toggle-icon:after {
	content: "";
	position: absolute;
	background-color: #e91e63;
	transition: all 0.3s;
}

.toggle-icon:before {
	width: 16px;
	height: 2px;
	top: 7px;
	left: 0;
}

.toggle-icon:after {
	width: 2px;
	height: 16px;
	top: 0;
	left: 7px;
}

.toggle-icon.open:after {
	transform: rotate(90deg);
	opacity: 0;
}

.panel-content {
	padding: 10px; /* 减小padding */
}

.player-level {
	display: flex;
	justify-content: space-between;
	margin-bottom: 12px;
	font-size: 13px;
	color: #ccc;
}

.player-stats {
	display: flex;
	flex-direction: column;
	gap: 15px;
}

.stat-group {
	background-color: rgba(20, 20, 20, 0.5);
	border-radius: 8px;
	padding: 10px;
}

.attributes-list {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 10px;
}

.attribute-item {
	background-color: rgba(20, 20, 20, 0.5);
	padding: 8px 10px;
	border-radius: 6px;
	display: flex;
	justify-content: space-between;
	font-size: 13px;
}

.attribute-name {
	color: #ccc;
}

.attribute-value {
	color: #e91e63;
	font-weight: bold;
}

.inventory {
	background-color: rgba(20, 20, 20, 0.5);
	border-radius: 8px;
	padding: 10px;
}

.inventory-title {
	margin-bottom: 8px;
	font-size: 14px;
	color: #ccc;
}

.inventory-items {
	display: flex;
	flex-wrap: wrap;
	gap: 8px;
}

.inventory-item {
	background-color: rgba(60, 60, 60, 0.5);
	border: 1px solid #555;
	border-radius: 4px;
	padding: 4px 8px;
	font-size: 12px;
}

.stat-item {
	display: flex;
	justify-content: space-between;
	margin-bottom: 10px;
}

.stat-item:last-child {
	margin-bottom: 0;
}

.stat-name {
	color: #aaa;
}

.stat-value {
	color: #e91e63;
	font-weight: bold;
}

.chat-container {
	flex: 1;
	display: flex;
	flex-direction: column;
	background-color: rgba(30, 30, 30, 0.7);
	border-radius: 10px;
	overflow: hidden;
	min-height: 0; /* 确保可以被压缩 */
}

.chat-messages {
	flex: 1;
	padding: 12px; /* 减小padding */
	overflow-y: auto;
	display: flex;
	flex-direction: column;
	scrollbar-width: thin;
	scrollbar-color: #444 #222;
	min-height: 130px; /* 减小最小高度 */
}

.chat-messages::-webkit-scrollbar {
	width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
	background: #222;
}

.chat-messages::-webkit-scrollbar-thumb {
	background-color: #444;
	border-radius: 4px;
}

.message {
	margin-bottom: 10px; /* 减小margin */
	padding: 8px 12px; /* 减小padding */
	border-radius: 10px;
	max-width: 80%;
	position: relative;
	animation: fadeIn 0.3s ease;
	padding-top: 22px; /* 减小padding-top */
}

.message-label {
	position: absolute;
	top: 5px;
	left: 10px;
	font-size: 11px;
	color: #888;
	background-color: rgba(0, 0, 0, 0.3);
	padding: 2px 8px;
	border-radius: 10px;
}

.message.system {
	background-color: rgba(0, 0, 0, 0.5);
	color: #e91e63;
	align-self: center;
	text-align: center;
	max-width: 90%;
	font-style: italic;
	padding: 28px 15px 8px;
	margin: 15px 0;
}

.message.system .message-label {
	left: 50%;
	transform: translateX(-50%);
}

.message.character {
	background-color: rgba(20, 20, 20, 0.9);
	color: #fff;
	align-self: flex-start;
	border-bottom-left-radius: 0;
}

.message.user {
	background-color: rgba(233, 30, 99, 0.2);
	color: #fff;
	align-self: flex-end;
	border-bottom-right-radius: 0;
}

.message.user .message-label {
	left: auto;
	right: 10px;
}

.message-time {
	font-size: 12px;
	color: #aaa;
	position: absolute;
	bottom: 5px;
	right: 10px;
}

.typing-indicator {
	display: flex;
	align-items: center;
	background-color: rgba(20, 20, 20, 0.9);
	border-radius: 10px;
	padding: 15px;
	padding-top: 28px;
	align-self: flex-start;
	margin-bottom: 15px;
	position: relative;
}

.typing-dot {
	width: 8px;
	height: 8px;
	background-color: #e91e63;
	border-radius: 50%;
	margin: 0 3px;
	animation: typingAnimation 1.5s infinite ease-in-out;
}

.typing-dot:nth-child(2) {
	animation-delay: 0s;
}

.typing-dot:nth-child(3) {
	animation-delay: 0.2s;
}

.typing-dot:nth-child(4) {
	animation-delay: 0.4s;
}

@keyframes typingAnimation {
	0%,
	60%,
	100% {
		transform: translateY(0);
	}
	30% {
		transform: translateY(-5px);
	}
}

.chat-input-container {
	display: flex;
	padding: 8px;
	background-color: rgba(20, 20, 20, 0.8);
	flex-shrink: 0; /* 防止输入区域被压缩 */
}

.send-btn {
	margin-left: 10px;
	background-color: #e91e63;
	color: white;
	border: none;
}

.status-bar {
	display: flex;
	justify-content: space-between;
	padding: 5px 15px; /* 减少padding */
	background-color: rgba(0, 0, 0, 0.6);
	color: #ccc;
	font-size: 12px; /* 减小字体 */
	flex-shrink: 0; /* 防止状态栏被压缩 */
}

.choices-container {
	position: fixed;
	bottom: 100px;
	left: 50%;
	transform: translateX(-50%);
	width: 90%;
	max-width: 600px;
	background-color: rgba(20, 20, 20, 0.95);
	border-radius: 15px;
	padding: 20px;
	box-shadow: 0 5px 25px rgba(0, 0, 0, 0.5);
	z-index: 100;
	animation: slideUp 0.5s ease;
}

@keyframes slideUp {
	from {
		transform: translate(-50%, 50px);
		opacity: 0;
	}
	to {
		transform: translate(-50%, 0);
		opacity: 1;
	}
}

.choices-title {
	text-align: center;
	color: #e91e63;
	font-size: 18px;
	margin-bottom: 15px;
}

.choices-list {
	display: flex;
	flex-direction: column;
	gap: 10px;
	margin-bottom: 15px;
}

.choice-btn {
	background-color: rgba(40, 40, 40, 0.9);
	text-align: left;
	color: #fff;
	padding: 12px 15px;
	border: 1px solid #555;
	transition: all 0.3s;
}

.choice-btn:hover {
	background-color: rgba(60, 60, 60, 0.9);
	border-color: #e91e63;
}

.custom-choice {
	display: flex;
	gap: 10px;
}

.custom-choice-btn {
	background-color: #e91e63;
	color: white;
	border: none;
}

.story-notification {
	position: fixed;
	top: 50px;
	left: 50%;
	transform: translateX(-50%);
	background-color: rgba(233, 30, 99, 0.8);
	color: white;
	padding: 12px 20px;
	border-radius: 8px;
	font-size: 16px;
	z-index: 200;
	animation: fadeInOut 3s ease;
}

@keyframes fadeInOut {
	0%,
	100% {
		opacity: 0;
	}
	10%,
	90% {
		opacity: 1;
	}
}

@keyframes fadeIn {
	from {
		opacity: 0;
	}
	to {
		opacity: 1;
	}
}

/* 响应式样式调整 */
@media (max-width: 992px) {
	.game-area {
		flex-direction: column;
	}

	.sidebar {
		width: 100%;
		margin-right: 0;
		margin-bottom: 20px;
	}

	.npc-stats {
		max-width: 100%;
	}
}

@media (max-width: 768px) {
	.npc-card {
		min-width: 150px;
	}
}

@media (max-width: 576px) {
	.npc-cards-container {
		padding: 10px;
	}

	.chat-input-container {
		flex-direction: column;
		gap: 10px;
	}

	.send-btn {
		margin-left: 0;
	}

	.status-bar {
		flex-direction: column;
		gap: 5px;
	}
}
</style>
