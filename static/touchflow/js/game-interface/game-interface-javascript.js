// NFT Data (15 NFTs for 3x5 grid)
const nftData = [{
		name: "Shiro",
		series: "Warriors",
		family: "Mochi",
		rarity: "legendary",
		desc_0: ["- 外观：纯白色圆形，黑点眼睛，小月牙嘴", "- 性格：天真无邪，什么都不懂但很治愈", "- 喜好：收集白色的小东西，喜欢在雪地里打滚，看云朵"],
		desc_1: ["- 经典台词： ", '  - "诶？这是什么呀～"', '  - "哇哦！好神奇！"'],
		imgurl: "../statics/game-interface/mochi/shiro.png",
		imgurl2: "../statics/game-interface/mochi/shiro.png",
		float: [200, 0], // x, y
		name_float: 130,
		zIndex: 1,
		picsize: 180,
		unlock: true
	},
	{
		name: "Cha",
		series: "Mystic",
		family: "Mochi",
		rarity: "rare",
		desc_0: ["- 外观：奶茶色圆角矩形，很踏实的感觉", "- 性格：稳重可靠，是大家的依靠", "- 喜好：做手工，整理房间，泡茶，照顾朋友，收集茶具"],
		desc_1: ["- 经典台词：", '  - "放心，交给我吧！"', '  - "稳稳的，不用担心～来杯茶吧～"'],
		imgurl: "../statics/game-interface/mochi/cha.png",
		imgurl2: "../statics/game-interface/mochi/cha.png",
		float: [165, -40], // x, y
		name_float: 90,
		zIndex: 0,
		picsize: 240,
		unlock: true
	},
	{
		name: "Niji",
		series: "Tech",
		family: "Mochi",
		rarity: "epic",
		desc_0: ["- 外观：渐变色半圆形，像小彩虹", "- 性格：变化多端，充满惊喜", "- 喜好：变魔术，画画，尝试新事物，收集颜料和彩色宝石"],
		desc_1: ["- 经典台词：", '  - "看我变个魔术！"', '  - "每天都要有新的色彩～变变变！"'],
		imgurl: "../statics/game-interface/mochi/niji.png",
		imgurl2: "../statics/game-interface/mochi/niji.png",
		imgurl_unlock: "../statics/game-interface/mochi/niji_hide.png",
		float: [112, -15], // x, y
		name_float: 150,
		zIndex: 1,
		picsize: 150,
		unlock: false
	},
	{
		name: "Orenji",
		series: "Legends",
		family: "Mochi",
		rarity: "legendary",
		desc_0: ["- 外观：蜜桃橙色心形，温暖感十足", "- 性格：热情温暖，是大家的小太阳", "- 喜好：烘焙，给朋友写信，组织聚会，收集爱心物件"],
		desc_1: ["- 经典台词：", '  - "大家一起来吧！"', '  - "爱就是要表达出来～心心相印！"'],
		imgurl: "../statics/game-interface/mochi/orenji.png",
		imgurl2: "../statics/game-interface/mochi/orenji.png",
		float: [55, -35], // x, y
		name_float: 110,
		zIndex: 0,
		picsize: 190,
		unlock: true
	},
	{
		name: "Momo",
		series: "Legends",
		family: "Mochi",
		rarity: "legendary",
		desc_0: ["- 外观：淡粉色椭圆，害羞时会变深粉", "- 性格：容易脸红，说话轻声细语", "- 喜好：看少女漫画，收集可爱贴纸，喜欢樱花和蝴蝶"],
		desc_1: ["- 经典台词：", '  - "那个...可以吗..."', '  - "羞羞啦～不要看我！"'],
		imgurl: "../statics/game-interface/mochi/momo.png",
		imgurl2: "../statics/game-interface/mochi/momo.png",
		float: [30, -25], // x, y
		name_float: 130,
		zIndex: 0,
		picsize: 180,
		unlock: true
	},
	{
		name: "Midori",
		series: "Cosmos",
		family: "Mochi",
		rarity: "common",
		desc_0: ["- 外观：淡绿色三角锥，顶端有小芽", "- 性格：自然系，喜欢晒太阳", "- 喜好：园艺，森林浴，和小动物聊天，收集种子"],
		desc_1: ["- 经典台词：", '  - "今天的阳光真棒～"', '  - "大自然最治愈了！一起种花吧～"'],
		imgurl: "../statics/game-interface/mochi/midori.png",
		imgurl2: "../statics/game-interface/mochi/midori.png",
		float: [0, -20], // x, y
		name_float: 120,
		zIndex: 1,
		picsize: 140,
		unlock: true
	},
	{
		name: "Ao",
		series: "Rebels",
		family: "Mochi",
		rarity: "epic",
		desc_0: ["- 外观：天蓝色水滴形状，表面有光泽", "- 性格：爱哭鬼，但眼泪是星星形状", "- 喜好：看感人电影，听雨声，收集手帕和眼泪瓶"],
		desc_1: ["- 经典台词：", '  - "呜呜呜～为什么..."', '  - "感动到哭了！星星眼泪好美～"'],
		imgurl: "../statics/game-interface/mochi/ao.png",
		imgurl2: "../statics/game-interface/mochi/ao.png",
		float: [-50, -50], // x, y
		name_float: 140,
		zIndex: 0,
		picsize: 150,
		unlock: true
	},

	{
		name: "Murasaki",
		series: "Mystic",
		family: "Mochi",
		rarity: "rare",
		desc_0: ["- 外观：薰衣草色云朵形，边缘模糊", "- 性格：爱做梦，总是飘飘然", "- 喜好：看星空，写梦境日记，收集羽毛和梦境瓶"],
		desc_1: ["- 经典台词：", '  - "我梦到了..."', '  - "在梦里什么都可能发生～飘飘然～"'],
		imgurl: "../statics/game-interface/mochi/murasaki.png",
		imgurl2: "../statics/game-interface/mochi/murasaki.png",
		float: [-80, -10], // x, y
		name_float: 30,
		zIndex: 0,
		picsize: 170,
		unlock: true
	},
	{
		name: "Ki",
		series: "Magic",
		family: "Mochi",
		rarity: "epic",
		desc_0: ["- 外观：鹅黄色椭圆，中间有小凹陷", "- 性格：温暖如阳光，给人能量", "- 喜好：做早餐，看日出，分享温暖的故事，收集太阳花"],
		desc_1: ["- 经典台词：", '  - "早安！今天也要加油哦～"', '  - "来，给你温暖的抱抱！"'],
		imgurl: "../statics/game-interface/mochi/ki.png",
		imgurl2: "../statics/game-interface/mochi/ki.png",
		float: [-100, -30], // x, y
		name_float: 80,
		zIndex: 1,
		picsize: 210,
		unlock: true
	},
	{
		name: "Hai",
		series: "Cosmos",
		family: "Mochi",
		rarity: "rare",
		desc_0: ["- 外观：浅灰色正方形，边角圆润", "- 性格：安静内敛，是倾听者", "- 喜好：读书，下雨天，独处的时光，收集书签和安静音乐"],
		desc_1: ["- 经典台词：", '  - "我在听...请继续说"', '  - "安静也是一种美好，嘘～"'],
		imgurl: "../statics/game-interface/mochi/hai.png",
		imgurl2: "../statics/game-interface/mochi/hai.png",
		float: [-140, -20], // x, y
		name_float: 120,
		zIndex: 1,
		picsize: 150,
		unlock: true
	}
];

const nftData1 = [{
		name: "BATTERY",
		series: "Warriors",
		family: "punk",
		rarity: "legendary",
		desc_0: ["- 外观：纯白色圆形，黑点眼睛，小月牙嘴", "- 性格：天真无邪，什么都不懂但很治愈", "- 喜好：收集白色的小东西，喜欢在雪地里打滚，看云朵"],
		desc_1: ["- 经典台词： ", '  - "诶？这是什么呀～"', '  - "哇哦！好神奇！"'],
		imgurl: "../statics/game-interface/punk/BATTERY.png",
		imgurl2: "../statics/game-interface/punk/BATTERY.png",
		float: [110, 0], // x, y
		name_float: 150,
		zIndex: 1,
		picsize: 150,
		unlock: true
	},
	{
		name: "BULB",
		series: "Mystic",
		family: "punk",
		rarity: "rare",
		desc_0: ["- 外观：奶茶色圆角矩形，很踏实的感觉", "- 性格：稳重可靠，是大家的依靠", "- 喜好：做手工，整理房间，泡茶，照顾朋友，收集茶具"],
		desc_1: ["- 经典台词：", '  - "放心，交给我吧！"', '  - "稳稳的，不用担心～来杯茶吧～"'],
		imgurl: "../statics/game-interface/punk/BULB.png",
		imgurl2: "../statics/game-interface/punk/BULB.png",
		float: [70, -30], // x, y
		name_float: 90,
		zIndex: 0,
		picsize: 250,
		unlock: true
	},
	{
		name: "CLOCK",
		series: "Tech",
		family: "punk",
		rarity: "epic",
		desc_0: ["- 外观：渐变色半圆形，像小彩虹", "- 性格：变化多端，充满惊喜", "- 喜好：变魔术，画画，尝试新事物，收集颜料和彩色宝石"],
		desc_1: ["- 经典台词：", '  - "看我变个魔术！"', '  - "每天都要有新的色彩～变变变！"'],
		imgurl: "../statics/game-interface/punk/CLOCK.png",
		imgurl2: "../statics/game-interface/punk/CLOCK.png",
		float: [70, -20], // x, y
		name_float: 120,
		zIndex: 0,
		picsize: 250,
		unlock: true
	},
	{
		name: "GEAR",
		series: "Legends",
		family: "punk",
		rarity: "legendary",
		desc_0: ["- 外观：蜜桃橙色心形，温暖感十足", "- 性格：热情温暖，是大家的小太阳", "- 喜好：烘焙，给朋友写信，组织聚会，收集爱心物件"],
		desc_1: ["- 经典台词：", '  - "大家一起来吧！"', '  - "爱就是要表达出来～心心相印！"'],
		imgurl: "../statics/game-interface/punk/GEAR.png",
		imgurl2: "../statics/game-interface/punk/GEAR.png",
		imgurl_unlock: "../statics/game-interface/punk/GEAR_hide.png",
		float: [40, 0], // x, y
		name_float: 220,
		zIndex: 0,
		picsize: 170,
		unlock: false
	},
	{
		name: "HAMMER",
		series: "Legends",
		family: "punk",
		rarity: "legendary",
		desc_0: ["- 外观：淡粉色椭圆，害羞时会变深粉", "- 性格：容易脸红，说话轻声细语", "- 喜好：看少女漫画，收集可爱贴纸，喜欢樱花和蝴蝶"],
		desc_1: ["- 经典台词：", '  - "那个...可以吗..."', '  - "羞羞啦～不要看我！"'],
		imgurl: "../statics/game-interface/punk/HAMMER.png",
		imgurl2: "../statics/game-interface/punk/HAMMER.png",
		float: [0, 0], // x, y
		name_float: 190,
		zIndex: 1,
		picsize: 180,
		unlock: true
	},
	{
		name: "PIPE",
		series: "Legends",
		family: "punk",
		rarity: "legendary",
		desc_0: ["- 外观：淡粉色椭圆，害羞时会变深粉", "- 性格：容易脸红，说话轻声细语", "- 喜好：看少女漫画，收集可爱贴纸，喜欢樱花和蝴蝶"],
		desc_1: ["- 经典台词：", '  - "那个...可以吗..."', '  - "羞羞啦～不要看我！"'],
		imgurl: "../statics/game-interface/punk/PIPE.png",
		imgurl2: "../statics/game-interface/punk/PIPE.png",
		float: [0, -20], // x, y
		name_float: 130,
		zIndex: 0,
		picsize: 300,
		unlock: true
	},
	{
		name: "SPRING",
		series: "Legends",
		family: "punk",
		rarity: "legendary",
		desc_0: ["- 外观：淡粉色椭圆，害羞时会变深粉", "- 性格：容易脸红，说话轻声细语", "- 喜好：看少女漫画，收集可爱贴纸，喜欢樱花和蝴蝶"],
		desc_1: ["- 经典台词：", '  - "那个...可以吗..."', '  - "羞羞啦～不要看我！"'],
		imgurl: "../statics/game-interface/punk/SPRING.png",
		imgurl2: "../statics/game-interface/punk/SPRING.png",
		float: [-30, -10], // x, y
		name_float: 130,
		zIndex: 0,
		picsize: 160,
		unlock: true
	},
	{
		name: "VALVE",
		series: "Legends",
		family: "punk",
		rarity: "legendary",
		desc_0: ["- 外观：淡粉色椭圆，害羞时会变深粉", "- 性格：容易脸红，说话轻声细语", "- 喜好：看少女漫画，收集可爱贴纸，喜欢樱花和蝴蝶"],
		desc_1: ["- 经典台词：", '  - "那个...可以吗..."', '  - "羞羞啦～不要看我！"'],
		imgurl: "../statics/game-interface/punk/VALVE.png",
		imgurl2: "../statics/game-interface/punk/VALVE.png",
		float: [-60, -10], // x, y
		name_float: 150,
		zIndex: 0,
		picsize: 160,
		unlock: true
	},
	{
		name: "STEAM",
		series: "Legends",
		family: "punk",
		rarity: "legendary",
		desc_0: ["- 外观：淡粉色椭圆，害羞时会变深粉", "- 性格：容易脸红，说话轻声细语", "- 喜好：看少女漫画，收集可爱贴纸，喜欢樱花和蝴蝶"],
		desc_1: ["- 经典台词：", '  - "那个...可以吗..."', '  - "羞羞啦～不要看我！"'],
		imgurl: "../statics/game-interface/punk/STEAM.png",
		imgurl2: "../statics/game-interface/punk/STEAM.png",
		float: [-90, -20], // x, y
		name_float: 150,
		zIndex: 0,
		picsize: 220,
		unlock: true
	},
	{
		name: "SCREW",
		series: "Legends",
		family: "punk",
		rarity: "legendary",
		desc_0: ["- 外观：淡粉色椭圆，害羞时会变深粉", "- 性格：容易脸红，说话轻声细语", "- 喜好：看少女漫画，收集可爱贴纸，喜欢樱花和蝴蝶"],
		desc_1: ["- 经典台词：", '  - "那个...可以吗..."', '  - "羞羞啦～不要看我！"'],
		imgurl: "../statics/game-interface/punk/SCREW.png",
		imgurl2: "../statics/game-interface/punk/SCREW.png",
		float: [-140, -10], // x, y
		name_float: 160,
		zIndex: 0,
		picsize: 100,
		unlock: true
	}
];

const nftData2 = [{
		name: "SPACE-SPEAKER",
		series: "Warriors",
		family: "pixel",
		rarity: "legendary",
		desc_0: ["- 外观：纯白色圆形，黑点眼睛，小月牙嘴", "- 性格：天真无邪，什么都不懂但很治愈", "- 喜好：收集白色的小东西，喜欢在雪地里打滚，看云朵"],
		desc_1: ["- 经典台词： ", '  - "诶？这是什么呀～"', '  - "哇哦！好神奇！"'],
		imgurl: "../statics/game-interface/pixel/SPACE-SPEAKER.png",
		imgurl2: "../statics/game-interface/pixel/SPACE-SPEAKER.png",
		float: [70, -20], // x, y
		name_float: 130,
		zIndex: 1,
		picsize: 190,
		unlock: true
	},
	{
		name: "SPACE-DONUT",
		series: "Mystic",
		family: "pixel",
		rarity: "rare",
		desc_0: ["- 外观：奶茶色圆角矩形，很踏实的感觉", "- 性格：稳重可靠，是大家的依靠", "- 喜好：做手工，整理房间，泡茶，照顾朋友，收集茶具"],
		desc_1: ["- 经典台词：", '  - "放心，交给我吧！"', '  - "稳稳的，不用担心～来杯茶吧～"'],
		imgurl: "../statics/game-interface/pixel/SPACE-DONUT.png",
		imgurl2: "../statics/game-interface/pixel/SPACE-DONUT.png",
		float: [70, -40], // x, y
		name_float: 90,
		zIndex: 0,
		picsize: 210,
		unlock: true
	},
	{
		name: "SPACE-BURGER",
		series: "Tech",
		family: "pixel",
		rarity: "epic",
		desc_0: ["- 外观：渐变色半圆形，像小彩虹", "- 性格：变化多端，充满惊喜", "- 喜好：变魔术，画画，尝试新事物，收集颜料和彩色宝石"],
		desc_1: ["- 经典台词：", '  - "看我变个魔术！"', '  - "每天都要有新的色彩～变变变！"'],
		imgurl: "../statics/game-interface/pixel/SPACE-BURGER.png",
		imgurl2: "../statics/game-interface/pixel/SPACE-BURGER.png",
		float: [60, 0], // x, y
		name_float: 150,
		zIndex: 1,
		picsize: 170,
		unlock: true
	},
	{
		name: "SPACE-DOG",
		series: "Legends",
		family: "pixel",
		rarity: "legendary",
		desc_0: ["- 外观：蜜桃橙色心形，温暖感十足", "- 性格：热情温暖，是大家的小太阳", "- 喜好：烘焙，给朋友写信，组织聚会，收集爱心物件"],
		desc_1: ["- 经典台词：", '  - "大家一起来吧！"', '  - "爱就是要表达出来～心心相印！"'],
		imgurl: "../statics/game-interface/pixel/SPACE-DOG.png",
		imgurl2: "../statics/game-interface/pixel/SPACE-DOG.png",
		imgurl_unlock: "../statics/game-interface/pixel/SPACE-DOG.png",
		float: [50, -20], // x, y
		name_float: 110,
		zIndex: 0,
		picsize: 200,
		unlock: true
	},
	{
		name: "JELLY-STAR",
		series: "Legends",
		family: "pixel",
		rarity: "legendary",
		desc_0: ["- 外观：淡粉色椭圆，害羞时会变深粉", "- 性格：容易脸红，说话轻声细语", "- 喜好：看少女漫画，收集可爱贴纸，喜欢樱花和蝴蝶"],
		desc_1: ["- 经典台词：", '  - "那个...可以吗..."', '  - "羞羞啦～不要看我！"'],
		imgurl: "../statics/game-interface/pixel/JELLY-STAR.png",
		imgurl2: "../statics/game-interface/pixel/JELLY-STAR.png",
		float: [0, -10], // x, y
		name_float: 130,
		zIndex: 0,
		picsize: 170,
		unlock: true
	},
	{
		name: "EYE-FLY",
		series: "Legends",
		family: "pixel",
		rarity: "legendary",
		desc_0: ["- 外观：淡粉色椭圆，害羞时会变深粉", "- 性格：容易脸红，说话轻声细语", "- 喜好：看少女漫画，收集可爱贴纸，喜欢樱花和蝴蝶"],
		desc_1: ["- 经典台词：", '  - "那个...可以吗..."', '  - "羞羞啦～不要看我！"'],
		imgurl: "../statics/game-interface/pixel/EYE-FLY.png",
		imgurl2: "../statics/game-interface/pixel/EYE-FLY.png",
		float: [-30, -25], // x, y
		name_float: 130,
		zIndex: 0,
		picsize: 170,
		unlock: true
	},
	{
		name: "CAT-ALIEN",
		series: "Legends",
		family: "pixel",
		rarity: "legendary",
		desc_0: ["- 外观：淡粉色椭圆，害羞时会变深粉", "- 性格：容易脸红，说话轻声细语", "- 喜好：看少女漫画，收集可爱贴纸，喜欢樱花和蝴蝶"],
		desc_1: ["- 经典台词：", '  - "那个...可以吗..."', '  - "羞羞啦～不要看我！"'],
		imgurl: "../statics/game-interface/pixel/CAT-ALIEN.png",
		imgurl2: "../statics/game-interface/pixel/CAT-ALIEN.png",
		float: [-70, 0], // x, y
		name_float: 130,
		zIndex: 0,
		picsize: 170,
		unlock: true
	},
	{
		name: "PIXEL-RABBIT",
		series: "Legends",
		family: "pixel",
		rarity: "legendary",
		desc_0: ["- 外观：淡粉色椭圆，害羞时会变深粉", "- 性格：容易脸红，说话轻声细语", "- 喜好：看少女漫画，收集可爱贴纸，喜欢樱花和蝴蝶"],
		desc_1: ["- 经典台词：", '  - "那个...可以吗..."', '  - "羞羞啦～不要看我！"'],
		imgurl: "../statics/game-interface/pixel/PIXEL-RABBIT.png",
		imgurl2: "../statics/game-interface/pixel/PIXEL-RABBIT.png",
		float: [-90, 0], // x, y
		name_float: 130,
		zIndex: 0,
		picsize: 170,
		unlock: true
	},
	{
		name: "SPACE-MONKEY",
		series: "Legends",
		family: "pixel",
		rarity: "legendary",
		desc_0: ["- 外观：淡粉色椭圆，害羞时会变深粉", "- 性格：容易脸红，说话轻声细语", "- 喜好：看少女漫画，收集可爱贴纸，喜欢樱花和蝴蝶"],
		desc_1: ["- 经典台词：", '  - "那个...可以吗..."', '  - "羞羞啦～不要看我！"'],
		imgurl: "../statics/game-interface/pixel/SPACE-MONKEY.png",
		imgurl2: "../statics/game-interface/pixel/SPACE-MONKEY.png",
		float: [-120, 0], // x, y
		name_float: 130,
		zIndex: 0,
		picsize: 170,
		unlock: true
	},
	{
		name: "SPACE-DUCK",
		series: "Legends",
		family: "pixel",
		rarity: "legendary",
		desc_0: ["- 外观：淡粉色椭圆，害羞时会变深粉", "- 性格：容易脸红，说话轻声细语", "- 喜好：看少女漫画，收集可爱贴纸，喜欢樱花和蝴蝶"],
		desc_1: ["- 经典台词：", '  - "那个...可以吗..."', '  - "羞羞啦～不要看我！"'],
		imgurl: "../statics/game-interface/pixel/SPACE-DUCK.png",
		imgurl2: "../statics/game-interface/pixel/SPACE-DUCK.png",
		float: [-140, 0], // x, y
		name_float: 130,
		zIndex: 0,
		picsize: 170,
		unlock: true
	}
];

let authToken = localStorage.getItem('admin-element-vue-token');
let userInfo = null;
let userDetail = null;
let session_id = null
let rewardDatas = null
let can_send_msg = 0
let challengeDatas = null;
let accumulatedScore = 0; // Track accumulated score across rounds

// Initialize page
window.onload = function() {
	if (!authToken) {
		window.location.href = '../index.html';
		return;
	}
	getUserInfomation() // get user datas
	generateStars();
	
	// Initialize challenge state
	resetChallengeSession();
};


// Generate stars background
function generateStars() {
	const starsBg = document.getElementById('starsBg');
	for (let i = 0; i < 150; i++) {
		const star = document.createElement('div');
		star.className = 'star';
		star.style.left = Math.random() * 100 + '%';
		star.style.top = Math.random() * 100 + '%';
		star.style.width = star.style.height = Math.random() * 3 + 1 + 'px';
		star.style.animationDelay = Math.random() * 2 + 's';
		starsBg.appendChild(star);
	}
}

// Generate NFT cards
function generateNFTCards(index) {
	const grid = document.getElementById('nftGrid' + index);
	grid.innerHTML = '';

	let _arr_tmp = [nftData, nftData1, nftData2][2 < index ? 0 : index]

	_arr_tmp.forEach((nft, idx) => {
		const card = document.createElement('div');
		card.className = 'nft-card';
		card.onclick = () => showNFTDetails(nft);

		// card.innerHTML = `
		//                   <div class="nft-image">
		//                       ${nft.emoji}
		//                       <div class="nft-rarity rarity-${nft.rarity}">
		//                           ${nft.rarity === 'legendary' ? '★' : nft.rarity === 'epic' ? '♦' : nft.rarity === 'rare' ? '●' : '○'}
		//                       </div>
		//                   </div>
		//                   <div class="nft-name">${nft.name}</div>
		//                   <div class="nft-series">${nft.series} Series</div>
		//                   <button class="challenge-btn" onclick="event.stopPropagation(); startChallenge('${nft.name}')">
		//                       CHALLENGE TO WIN
		//                   </button>
		//               `;

		card.innerHTML = `
			<div class="nft-card-panel">
				<div class="nft-card-panel-name" style="top: ${nft.name_float}px">${nft.unlock ? nft.name : '???'}</div>
				<img src="${nft.unlock ? nft.imgurl2 : nft.imgurl_unlock}" style="width: ${nft.picsize}%;"/>
			</div>
		`;
		card.style.left = `${nft.float[0]}px`
		card.style.top = `${nft.float[1]}px`
		card.style.zIndex = nft.zIndex

		// 添加事件
		card.addEventListener('mouseenter', () => {
			const panelName = card.getElementsByClassName("nft-card-panel-name")[0];
			if (panelName) {
				panelName.style.visibility = `visible`;
			}
		});
		card.addEventListener('mouseleave', () => {
			const panelName = card.getElementsByClassName("nft-card-panel-name")[0];
			if (panelName) {
				panelName.style.visibility = "hidden";
			}
		});

		grid.appendChild(card);
	});
}


// Show NFT details modal
function showNFTDetails(nft) {
	if (!nft.unlock) return
	const modal = document.getElementById('nftModal');
	const details = document.getElementById('nftDetails');
	console.log(nft.id)
	// details.innerHTML = `
	//                <div class="nft-large-image">${nft.emoji}</div>
	//                <h2 style="color: var(--neon-yellow); margin-bottom: 10px;">${nft.name}</h2>
	//                <p style="color: var(--neon-cyan); font-size: 12px; margin-bottom: 20px;">
	//                    ${nft.series} Series • ${nft.family} Family • ${nft.rarity.toUpperCase()}
	//                </p>
	//                <div class="nft-story">
	//                    <h3 style="color: var(--neon-purple); margin-bottom: 15px;">📖 Character Story</h3>
	//                    <p style="color: white; font-size: 12px; line-height: 1.6;">${nft.story}</p>
	//                </div>
	//                <div style="margin-top: 20px;">
	//                    <button class="challenge-btn" style="padding: 15px 30px;" onclick="closeModal(); startChallenge('${nft.name}')">
	//                        🎯 CHALLENGE TO WIN THIS NFT
	//                    </button>
	//                </div>
	//            `;
	// <div></div>
	details.innerHTML = `
			<div class="nft-details-logo"><img src="../statics/logo.png"></div>
			<div class="nft-details-left-panel">
				<img src="${nft.imgurl}" />
			</div>
			<div class="nft-details-right-panel">
				<div class="nft-details-right-panel-top">
					<div class="role-name">${nft.name}</div>` +
		getRoleDesc0(nft.desc_0) +
		getRoleDesc1(nft.desc_1) +
		`</div>
			<div class="nft-details-right-panel-bottom">
				<button class="challenge-btn" style="width: 100%; padding: 15px 30px;">
					CHALLENGE TO WIN
				</button>
			</div>
		</div>
		`;
	const btn = details.querySelector('.challenge-btn');
	btn.addEventListener('click', () => challengeToWin(nft));

	modal.style.display = 'block';
}

// Close modal
function closeModal() {
	document.getElementById('nftModal').style.display = 'none';
}

// Show different sections
function showSection(sectionId) {
	// Hide all sections
	document.querySelectorAll('.page-section').forEach(section => {
		section.classList.remove('active');
	});

	// Remove active class from all nav buttons
	document.querySelectorAll('.nav-btn').forEach(btn => {
		btn.classList.remove('active');
	});

	// Show selected section
	document.getElementById(sectionId).classList.add('active');

	// Add active class to clicked button
	event.target.classList.add('active');
}

// Start AI challenge
function startChallenge(nftName) {
	showSection('challenge');
	document.querySelector('[onclick="showSection(\'challenge\')"]').classList.add('active');

	const chatContainer = document.getElementById('chatContainer');
	chatContainer.innerHTML = `
			<div class="chat-message ai">
				You've chosen to challenge for ${nftName}! Let's begin this epic battle of wits. Are you ready?
			</div>
		`;

	generateRandomChallenge();
}

// Start new challenge function
function startNewChallenge() {
	// Show loading state in overlay
	const overlay = document.getElementById('challengeOverlay');
	const startContent = overlay.querySelector('.challenge-start-content');
	startContent.innerHTML = `
		<h2>🎮 Starting Challenge...</h2>
		<div class="loading-spinner"></div>
		<p>Preparing your adventure, please wait...</p>
	`;
	
	// Clear chat container
	const chatContainer = document.getElementById('chatContainer');
	chatContainer.innerHTML = '';
	
	// Reset session
	session_id = null;
	can_send_msg = 0;
	
	// Start challenge with fixed card_id 46
	openChallenge({id: 46});
}

// Generate random challenge (deprecated, keeping for compatibility)
function generateRandomChallenge() {
	startNewChallenge();
}

// Reset challenge session and show overlay
function resetChallengeSession() {
	// Reset session variables
	session_id = null;
	can_send_msg = 0;
	accumulatedScore = 0; // Reset accumulated score
	
	// Hide game status info
	hideGameStatus();
	
	// Show overlay with initial content
	const overlay = document.getElementById('challengeOverlay');
	const startContent = overlay.querySelector('.challenge-start-content');
	startContent.innerHTML = `
		<h2>🎯 Ready for Challenge?</h2>
		<p>Test your skills and earn rewards!</p>
		<button class="challenge-btn" style="width: auto; padding: 15px 30px;" onclick="startNewChallenge()">🎲 New Random Challenge</button>
	`;
	overlay.style.display = 'flex';
	
	// Clear chat input
	document.getElementById('chatInput').value = '';
	
	// Update user info (refresh points)
	list('user');
}

// Show error state in overlay
function showOverlayError(message) {
	const overlay = document.getElementById('challengeOverlay');
	const startContent = overlay.querySelector('.challenge-start-content');
	startContent.innerHTML = `
		<h2>❌ Challenge Failed</h2>
		<p>${message}</p>
		<button class="challenge-btn" style="width: auto; padding: 15px 30px;" onclick="startNewChallenge()">🔄 Try Again</button>
	`;
	overlay.style.display = 'flex';
}

// Send message function
function sendMessage() {
	// Check if session_id exists and can send message
	if (!session_id || can_send_msg !== 1) {
		if (can_send_msg === 0) {
			aiReply('Please start a challenge first by clicking the "🎲 New Random Challenge" button.');
		} else if (can_send_msg === 2) {
			aiReply('Please wait, processing your challenge results...');
		} else {
			aiReply('No active challenge session. Please start a new challenge.');
		}
		return;
	}

	const input = document.getElementById('chatInput');
	const message = input.value.trim();

	if (!message) {
		return;
	}

	const chatContainer = document.getElementById('chatContainer');

	// Add user message
	chatContainer.innerHTML += `
		<div class="chat-message user">
			<strong>You:</strong> ${message}
		</div>
	`;

	input.value = '';
	can_send_msg = 2; // Set to waiting state

	// Send message to AI
	playerMsgToAI(message);

	chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Enter key to send message
document.getElementById('chatInput').addEventListener('keypress', function(e) {
	if (e.key === 'Enter') {
		sendMessage();
	}
});

// Close modal when clicking outside
window.onclick = function(event) {
	const modal = document.getElementById('nftModal');
	if (event.target === modal) {
		closeModal();
	}
}

// Jump to AI task
function challengeToWin(item) {
	setTimeout(() => {
		document.getElementsByClassName("nav-btn")[2].classList.add("active")
	}, 200)
	window.scroll(0, 0)
	showSection('challenge');
	closeModal();
	openChallenge(item)
}

function getRoleDesc0(arr) {
	let str = ''
	for (let i = 0; i < arr.length; i++) {
		str += `<div class="role-story">${arr[i]}</div>`
	}
	return str
}

function getRoleDesc1(arr) {
	let str = ''
	for (let i = 0; i < arr.length; i++) {
		str += `<div class="role-desc">${arr[i]}</div>`
	}
	return str
}

// logout
function logout() {
	fetch(`${API_BASE_URL}/auth/logout`, {
		method: 'POST',
		headers: {
			'Authorization': `Bearer ${authToken}`
		}
	}).finally(() => {
		localStorage.removeItem('authToken');
		window.location.href = '../index.html';
	});
}

function aiReply(str) {
	const chatContainer = document.getElementById('chatContainer');
	chatContainer.innerHTML += `
		<div class="chat-message ai">
		 ${str}
		</div>
	`;
	chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Update game status display
function updateGameStatus(currentRound, maxRounds, currentScore, targetScore) {
	const gameStatusInfo = document.getElementById('gameStatusInfo');
	const roundInfo = document.getElementById('roundInfo');
	const scoreInfo = document.getElementById('scoreInfo');
	
	if (gameStatusInfo && roundInfo && scoreInfo) {
		roundInfo.textContent = `${currentRound-1}/${maxRounds}`;
		scoreInfo.textContent = `${currentScore}/${targetScore}`;
		gameStatusInfo.style.display = 'flex';
	}
}

// Hide game status display
function hideGameStatus() {
	const gameStatusInfo = document.getElementById('gameStatusInfo');
	if (gameStatusInfo) {
		gameStatusInfo.style.display = 'none';
	}
}

async function getUserInfomation() {
	try {
		const userInfoResponse = await fetch(`${API_BASE_URL}/auth/user/info`, {
			headers: {
				'Authorization': `Bearer ${authToken}`
			}
		});

		if (!userInfoResponse.ok) {
			throw new Error('Failed to fetch user info');
		}

		const responseData = await userInfoResponse.json();

		if (responseData.code === 200 && responseData.data && responseData.data.user) {
			userInfo = responseData.data.user;
			userDetail = responseData.data.user_detail

			list('card')
			list('user')
		} else {
			throw new Error('Invalid response format when fetching user info');
		}
	} catch (error) {
		console.error('Login status check failed:', error);
		// 登录失败，清除token并跳转登录页
		localStorage.removeItem('authToken');
		window.location.href = '../index.html';
	}
}

async function list(type) {
	if (type == 'card') {
		const cardList = await fetch(`${API_BASE_URL}/card_game/series/`, {
			headers: {
				'Authorization': `Bearer ${authToken}`
			}
		});

		if (!cardList.ok) {
			throw new Error('Failed to fetch user info');
		}

		const responseData = await cardList.json();

		if (responseData.code === 200 && responseData.data) {
			cardDatas = responseData.data;

			let j = 0
			let _idxtemp = 0
			for (let i = 0; i < cardDatas.length; i++) {
				if (_idxtemp == 1) {
					for (const item of cardDatas[i].cards) {
						if (nftData1.length <= j) {
							j = 0
							_idxtemp += 1
							break
						}
						nftData1[j].id = item["id"]
						j += 1
					}
				} else if (_idxtemp == 2) {
					for (const item of cardDatas[i].cards) {
						if (nftData2.length <= j) {
							j = 0
							_idxtemp += 1
							break
						}
						nftData2[j].id = item["id"]
						j += 1
					}
				} else {
					for (const item of cardDatas[i].cards) {
						if (nftData.length <= j) {
							j = 0
							_idxtemp += 1
							break
						}
						nftData[j].id = item["id"]
						j += 1
					}
				}
			}

			generateNFTCards(0);
			generateNFTCards(1);
			generateNFTCards(2);
			generateNFTCards(3);
			generateNFTCards(4);
		} else {
			throw new Error('Invalid response format when fetching user info');
		}
	} else if ('user') {
		// 更新用户信息显示
		document.getElementById('game-nav-points').textContent =
		`💼 Points: ${userDetail.available_points}`; // 导航显示积分

		// 个人资料
		document.getElementById('stat-value-id-0').textContent = `${userDetail.available_points}`;
		document.getElementById('stat-value-id-1').textContent = `${userDetail.total_card_count}`;
		document.getElementById('stat-value-id-2').textContent = `${userDetail.total_ai_challenge_success_count}`;
		document.getElementById('stat-value-id-3').textContent =
			`${Math.round((userDetail.total_ai_challenge_success_count / userDetail.total_ai_challenge_count) * 1000) / 10}%`;
	}
}

async function openChallenge(item) {
	aiReply('A new challenge is about to begin. Loading...')
	can_send_msg = 2
	try {
		const ai = await fetch(`${API_BASE_URL}/card_game/challenge/chat/start?card_id=${item.id}`, {
			method: 'POST',
			headers: {
				'Authorization': `Bearer ${authToken}`,
				"Content-Type": 'application/json'
			},
			body: JSON.stringify({
				card_id: item.id
			})
		});

		if (!ai.ok) {
			throw new Error('Failed to fetch user info');
		}

		const responseData = await ai.json();

		if (responseData.code === 200 && responseData.data) {
			challengeDatas = responseData.data.data;
			session_id = challengeDatas.session_id
			
			// Hide overlay after successful session creation
			document.getElementById('challengeOverlay').style.display = 'none';
			
			// Reset accumulated score for new challenge
			accumulatedScore = 0;
			
			// Show game status info
			updateGameStatus(1, challengeDatas['task']['task']['max_rounds'], accumulatedScore, challengeDatas['task']['task']['target_score']);
			
			aiReply(
				`<br>Title: ${challengeDatas['task']['task']['title']}<br>Goal: ${challengeDatas['task']['task']['task_goal']}<br>Description: ${challengeDatas['task']['task']['description']}<br>Max Rounds: ${challengeDatas['task']['task']['max_rounds']}<br>Target Score: ${challengeDatas['task']['task']['target_score']}<br><br>${challengeDatas['task']['task']['prologues']}`
			)
			can_send_msg = 1
		} else {
			can_send_msg = 0
			aiReply('** Sorry, something seems to have gone wrong.')
			// Show error state in overlay
			showOverlayError('Failed to start challenge. Please try again.');
			throw new Error('Invalid response format when fetching user info');
		}
	} catch (err) {
		can_send_msg = 0
		aiReply('** Sorry, something seems to have gone wrong.')
		console.error('Runing Challenge Failed:', err);
	}
}

async function playerMsgToAI(msg) {
	try {
		const ai = await fetch(`${API_BASE_URL}/card_game/challenge/chat`, {
			method: 'POST',
			headers: {
				'Authorization': `Bearer ${authToken}`,
				"Content-Type": 'application/json'
			},
			body: JSON.stringify({
				message: `${msg}`,
				session_id: session_id
			})
		});

		if (!ai.ok) {
			can_send_msg = 1
			throw new Error('Failed');
		}

		const responseData = await ai.json();

		if (responseData.code === 200 && responseData.data) {
			console.log(responseData.data)
			aiReply(`${responseData.data.message}`)
			
			// Update game status with current round and score info
			if (challengeDatas && challengeDatas['task'] && challengeDatas['task']['task']) {
				const maxRounds = challengeDatas['task']['task']['max_rounds'];
				const targetScore = challengeDatas['task']['task']['target_score'];
				const currentRound = responseData.data.current_round || 1;
				// Extract current score change from tool_results if available
				if (responseData.data.tool_results) {
					try {
						const toolResults = JSON.parse(responseData.data.tool_results);
						if (toolResults && toolResults[0] && toolResults[0].content && toolResults[0].content.scoreChange !== undefined) {
							// Accumulate score changes
							accumulatedScore += toolResults[0].content.scoreChange;
						}
					} catch (e) {
						console.log('Could not parse tool results for score');
					}
				}
				updateGameStatus(currentRound, maxRounds, accumulatedScore, targetScore);
			}
			
			can_send_msg = 1
			if (responseData.data.is_win) {
				aiReply('Mission Complete! 🎉')
				getReward()
				can_send_msg = 0
				// Reset session and show overlay after reward
				setTimeout(() => {
					resetChallengeSession();
				}, 3000);
			}
			if (responseData.data.is_failed) {
				aiReply('Mission failed! 😞 Try again with a new challenge.')
				can_send_msg = 0
				// Reset session and show overlay
				setTimeout(() => {
					resetChallengeSession();
				}, 2000);
			}
			const chatContainer = document.getElementById('chatContainer');
			chatContainer.scrollTop = chatContainer.scrollHeight;
		} else {
			aiReply("Some errors detected. Retry later.")
			throw new Error('Some errors detected. Retry later.');
		}
	} catch (err) {
		can_send_msg = 0
		console.error('Challenge start failed:', err);
		aiReply("Some errors detected. Retry later.")
		// Show error state in overlay
		showOverlayError('Network error occurred. Please check your connection and try again.');
	}
}

async function getReward() {
	const _box_btn = document.getElementById('pixelBlindbox')
	const boxContent = document.getElementById('pixelBoxContent')
	// clear style for init
	_box_btn.style = null
	boxContent.textContent = '📦';
	document.getElementById('blind-box-main').style.display = `none`
	// *******************


	const ai_game_modal = document.getElementById('ai-game-modal-overlay-id')
	ai_game_modal.style = null
	ai_game_modal.style.display = 'flex'

	try {
		const request = await fetch(`${API_BASE_URL}/card_game/reward/challenge/${session_id}`, {
			headers: {
				'Authorization': `Bearer ${authToken}`
			}
		});

		if (!request.ok) {
			throw new Error('Failed');
		}
		const responseData = await request.json();

		if (responseData.code === 200 && responseData.data) {
			let _datas = responseData.data
			rewardDatas = responseData.data
			document.getElementsByClassName('ai-game-pixel-reward-amount')[1].textContent =
				`+${_datas.total_points}`
			const ai_game_modal = document.getElementById('ai-game-modal-overlay-id')
			ai_game_modal.style.display = 'flex'

			if (_datas.rewards) {
				for (const item of _datas.rewards) {
					if (item.type == 'blind_box') {
						document.getElementById('blind-box-main').style.display = `block`
					}
				}
			}
		} else {
			aiReply("Some errors detected. Retry later.")
			throw new Error('Some errors detected. Retry later.');
		}
	} catch (err) {
		console.error('Runing Failed:', err);
		aiReply("Some errors detected. Retry later.")
	}
}

// 像素盲盒开启动画
function openPixelBlindBox() {
	const blindbox = document.getElementById('pixelBlindbox');
	const boxContent = document.getElementById('pixelBoxContent');
	const boxText = document.getElementById('pixelBoxText');

	// 禁用点击
	blindbox.style.pointerEvents = 'none';
	boxText.textContent = 'Opening...';

	// 像素化震动效果
	let shakeCount = 0;
	const shakeDirections = [{
		x: 0,
		y: -4
	}, {
		x: 4,
		y: 0
	}, {
		x: 0,
		y: 4
	}, {
		x: -4,
		y: 0
	}];

	const shakeInterval = setInterval(() => {
		const direction = shakeDirections[shakeCount % 4];
		blindbox.style.transform = `translate(${direction.x}px, ${direction.y}px) scale(1.1)`;
		shakeCount++;

		if (shakeCount > 12) {
			clearInterval(shakeInterval);

			// 像素爆炸效果
			const rect = blindbox.getBoundingClientRect();
			const centerX = rect.left + rect.width / 2;
			const centerY = rect.top + rect.height / 2;

			// 改变盒子内容
			setTimeout(() => {
				let drawn_card;
				if (rewardDatas && rewardDatas.rewards) {
					for (const item of rewardDatas.rewards) {
						if (item.type == 'blind_box') {
							drawn_card = item
						}
					}
					boxContent.innerHTML = `<img src="${drawn_card.drawn_card.image_url}">`;
				}

				blindbox.style.transform = 'scale(1)';
				blindbox.style.animation = 'pixelBoxFloat 4s steps(16, end) infinite';
				boxText.textContent = 'Opened!';

				// 显示奖励
				const rewards = document.getElementById('pixelRewards');
				rewards.style.opacity = '1';

				// 像素化数字递增
				animatePixelNumbers();

				// 屏幕闪烁效果
				document.body.style.filter = 'brightness(1.5) contrast(1.2)';
				setTimeout(() => {
					document.body.style.filter = '';
				}, 200);

			}, 500);
		}
	}, 150);
}

// 像素化数字递增动画
function animatePixelNumbers() {
	const stats = [{
			element: document.getElementById('pixelTotalBoxes'),
			target: 12
		},
		{
			element: document.getElementById('pixelStreak'),
			target: 7
		},
		{
			element: document.getElementById('pixelLevel'),
			target: 15
		}
	];

	stats.forEach(stat => {
		let current = 0;
		const timer = setInterval(() => {
			current++;
			stat.element.textContent = current;

			// 像素化闪烁效果
			stat.element.style.color = current % 2 === 0 ? 'var(--primary-green)' :
				'var(--primary-cyan)';

			if (current >= stat.target) {
				clearInterval(timer);
				stat.element.style.color = 'var(--primary-green)';
			}
		}, 100);
	});
}

// 像素按钮点击效果
function pixelButtonClick(button) {
	button.style.transform = 'translate(2px, 2px)';
	button.style.filter = 'brightness(1.3)';

	setTimeout(() => {
		button.style.transform = '';
		button.style.filter = '';
	}, 150);
}

// 按钮事件
document.getElementById('pixelShareBtn').addEventListener('click', () => {
	const btn = document.getElementById('pixelShareBtn');
	pixelButtonClick(btn);

	btn.textContent = 'Shared!';
	btn.style.background = 'var(--primary-green)';
	btn.style.color = 'var(--dark-bg)';

	// 创建分享特效
	const rect = btn.getBoundingClientRect();
	createPixelExplosion(rect.left + rect.width / 2, rect.top + rect.height / 2);

	setTimeout(() => {
		btn.textContent = 'Share Victory';
		btn.style.background = 'transparent';
		btn.style.color = 'var(--primary-green)';
	}, 2000);
});

document.getElementById('pixelContinueBtn').addEventListener('click', () => {
	let _time = 0.8
	const btn = document.getElementById('pixelContinueBtn');
	pixelButtonClick(btn);

	const modal = document.querySelector('.ai-game-modal-overlay');
	modal.style.animation = `pixelOverlayFadeOut ${_time}s steps(8, end) forwards`;

	setTimeout(() => {
		const ai_game_modal = document.getElementById('ai-game-modal-overlay-id')
		modal.style.animation = null
		ai_game_modal.style.display = 'none'
		console.log('Continue to next quest');
	}, _time * 100);
});

// 关闭按钮
document.querySelector('.ai-game-modal-close').addEventListener('click', () => {
	let _time = 0.8
	const modal = document.querySelector('.ai-game-modal-overlay');
	modal.style.animation = `pixelOverlayFadeOut ${_time}s steps(8, end) forwards`;
	setTimeout(() => {
		const ai_game_modal = document.getElementById('ai-game-modal-overlay-id')
		modal.style.animation = null
		ai_game_modal.style.display = 'none'
	}, _time * 100)
});

// 盲盒点击事件
document.getElementById('pixelBlindbox').addEventListener('click', openPixelBlindBox);

// 添加fadeOut动画
const style = document.createElement('style');
style.textContent = `
	@keyframes pixelOverlayFadeOut {
		from { opacity: 1; }
		to { opacity: 0; }
	}
`;
document.head.appendChild(style);

// 键盘事件
document.addEventListener('keydown', (e) => {
	if (e.code === 'Space') {
		// 只有在不是输入框焦点时才阻止空格键默认行为
		const activeElement = document.activeElement;
		const isInputFocused = activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA');
		
		if (!isInputFocused) {
			e.preventDefault();
			if (document.getElementById('pixelBlindbox').style.pointerEvents !== 'none') {
				openPixelBlindBox();
			}
		}
	} else if (e.code === 'Enter') {
		// 只有在不是聊天输入框焦点时才触发继续按钮
		const activeElement = document.activeElement;
		if (activeElement && activeElement.id !== 'chatInput') {
			document.getElementById('pixelContinueBtn').click();
		}
	} else if (e.code === 'Escape') {
		document.querySelector('.modal-close').click();
	}
});

// 初始化
document.addEventListener('DOMContentLoaded', () => {
	// 像素化音效模拟
	console.log('🎵 8-bit reward system activated!');
});

// 像素化悬停效果
document.querySelectorAll('.ai-game-pixel-reward-item, .pixel-btn, .pixel-stat-item').forEach(element => {
	element.addEventListener('mouseenter', () => {
		element.style.filter = 'brightness(1.2) contrast(1.1)';
	});

	element.addEventListener('mouseleave', () => {
		element.style.filter = '';
	});
});