let currentLevel = 0;
let currentPath = '';
let audioEnabled = false;
let login_page_idx = 0


// Konami Code Easter Egg
const konamiCode = [38, 38, 40, 40, 37, 39, 37, 39]; // ↑↑↓↓←→←→
let konamiInput = [];
let easterEggTriggered = false;
const audio = document.getElementById('audion-box');

// Emoji collections for explosion
const explosionEmojis = [
	'🎮', '🎯', '🎪', '🎊', '🎉', '✨', '⭐', '🌟', '💫', '🚀',
	'💎', '💰', '🏆', '🎁', '🎈', '🎆', '🎇', '⚡', '🔥', '💖',
	'🦄', '🌈', '🎭', '🎨', '🎵', '🎶', '🎸', '🎹', '🎺', '🥳',
	'🤖', '👾', '🕹️', '📱', '💻', '⌨️', '🖱️', '💿', '📀', '🎧'
];

// Initialize Konami Code detection
function initKonamiCode() {
	document.addEventListener('keydown', (e) => {
		// Add current key to input sequence
		konamiInput.push(e.keyCode);

		// Keep only the last 8 keys
		if (konamiInput.length > konamiCode.length) {
			konamiInput.shift();
		}

		// Check if sequence matches Konami Code
		if (konamiInput.length === konamiCode.length) {
			if (arraysEqual(konamiInput, konamiCode)) {
				if (!easterEggTriggered) {
					triggerEasterEgg();
					easterEggTriggered = true;
				}
			}
		}
	});
}

// Check if arrays are equal
function arraysEqual(a, b) {
	return a.length === b.length && a.every((val, index) => val === b[index]);
}

// Trigger the Easter Egg
function triggerEasterEgg() {
	const overlay = document.getElementById('easterEggOverlay');

	// Show overlay
	overlay.classList.add('easter-egg-active');

	// Create emoji explosion
	createEmojiExplosion();

	// Play sound effect (if audio enabled)
	if (audioEnabled) {
		playEasterEggSound();
	}

	// Reset Konami input after trigger
	konamiInput = [];

	// Disable body scroll
	document.body.style.overflow = 'hidden';
}

// Create massive emoji explosion
function createEmojiExplosion() {
	const overlay = document.getElementById('easterEggOverlay');
	const explosionCount = 100; // Number of emojis

	// Create multiple waves of explosions
	for (let wave = 0; wave < 5; wave++) {
		setTimeout(() => {
			for (let i = 0; i < explosionCount / 5; i++) {
				setTimeout(() => {
					createSingleEmoji(overlay);
				}, Math.random() * 500);
			}
		}, wave * 300);
	}
}

// Create single emoji explosion
function createSingleEmoji(container) {
	const emoji = document.createElement('div');
	emoji.className = 'emoji-explosion';

	// 20% chance for special effect
	if (Math.random() < 0.2) {
		emoji.classList.add('special');
	}

	emoji.textContent = explosionEmojis[Math.floor(Math.random() * explosionEmojis.length)];

	// Random starting position
	emoji.style.left = Math.random() * 100 + '%';
	emoji.style.top = Math.random() * 100 + '%';

	// Random size variation
	const size = 20 + Math.random() * 40;
	emoji.style.fontSize = size + 'px';

	// Random animation duration
	const duration = emoji.classList.contains('special') ? 4 : 2 + Math.random() * 2;
	emoji.style.animationDuration = duration + 's';

	// Random delay
	emoji.style.animationDelay = Math.random() * 0.5 + 's';

	// Random rotation direction
	const rotateDirection = Math.random() > 0.5 ? 1 : -1;
	emoji.style.setProperty('--rotate-direction', rotateDirection);

	container.appendChild(emoji);

	// Remove emoji after animation
	setTimeout(() => {
		if (emoji.parentNode) {
			emoji.parentNode.removeChild(emoji);
		}
	}, (duration + 0.5) * 1000);
}

// Close Easter Egg
function closeEasterEgg() {
	const overlay = document.getElementById('easterEggOverlay');
	overlay.classList.remove('easter-egg-active');

	// Re-enable body scroll
	document.body.style.overflow = '';

	// Clear any remaining emojis
	const emojis = overlay.querySelectorAll('.emoji-explosion');
	emojis.forEach(emoji => {
		if (emoji.parentNode) {
			emoji.parentNode.removeChild(emoji);
		}
	});

	// Allow Easter egg to be triggered again after 10 seconds
	setTimeout(() => {
		easterEggTriggered = false;
	}, 10000);

	playClickSound();
}

// Play Easter Egg sound effect (simulated)
function playEasterEggSound() {
	// In a real implementation, you would play actual sound files
	console.log('🎵 Playing Easter Egg celebration sound!');

	// Create a series of beeps to simulate sound
	const frequencies = [523, 659, 784, 1047]; // C, E, G, C (major chord)
	frequencies.forEach((freq, index) => {
		setTimeout(() => {
			console.log(`🎵 Beep ${freq}Hz`);
		}, index * 200);
	});
}

// Path selection logic
function selectPath(path) {
	// Hide all path content
	document.querySelectorAll('.level-container').forEach(container => {
		container.classList.add('hidden');
	});

	// Show selected path
	document.getElementById(`path-${path}`).classList.remove('hidden');

	// Update path selector state
	document.querySelectorAll('.path-selector').forEach(selector => {
		selector.classList.remove('selected');
	});
	document.querySelector(`[data-path="${path}"]`).classList.add('selected');

	currentPath = path;
	window.scrollTo({
		top: 0,
		behavior: 'smooth'
	});
	playClickSound();
}

// Return to overview
function goToLevel(level) {
	if (level === 0) {
		// Return to main page
		document.querySelectorAll('.level-container').forEach(container => {
			container.classList.add('hidden');
		});
		document.getElementById('level-0').classList.remove('hidden');

		// Reset path selectors
		document.querySelectorAll('.path-selector').forEach(selector => {
			selector.classList.remove('selected');
		});

		currentPath = '';
		window.scrollTo({
			top: 0,
			behavior: 'smooth'
		});
		playClickSound();
	}
}

// Compatible with old nextLevel function
function nextLevel() {
	// Can be kept for special cases, or guide users to choose path
	console.log('Please choose your exploration path');
}

// Mouse trail effect
let mouseTrails = [];
let mousePositions = [];
const maxTrails = 12;
const maxPositions = 50; // Save more position points for trail following
let lastMouseX = 0,
	lastMouseY = 0;
let mouseSpeed = 0;

// Trail type configuration
const trailTypes = [{
		type: 'pixel',
		class: 'trail-pixel'
	},
	{
		type: 'star',
		class: 'trail-star'
	},
	{
		type: 'diamond',
		class: 'trail-diamond'
	},
	{
		type: 'heart',
		class: 'trail-heart'
	},
	{
		type: 'lightning',
		class: 'trail-lightning'
	},
	{
		type: 'emoji',
		class: 'trail-emoji',
		content: '✨'
	},
	{
		type: 'emoji',
		class: 'trail-emoji',
		content: '⭐'
	},
	{
		type: 'emoji',
		class: 'trail-emoji',
		content: '💫'
	},
	{
		type: 'emoji',
		class: 'trail-emoji',
		content: '🎮'
	},
	{
		type: 'emoji',
		class: 'trail-emoji',
		content: '🎯'
	},
	{
		type: 'emoji',
		class: 'trail-emoji',
		content: '🎪'
	},
	{
		type: 'emoji',
		class: 'trail-emoji',
		content: '🎊'
	},
	{
		type: 'emoji',
		class: 'trail-emoji',
		content: '💎'
	},
	{
		type: 'emoji',
		class: 'trail-emoji',
		content: '🚀'
	},
	{
		type: 'emoji',
		class: 'trail-emoji',
		content: '⚡'
	}
];

const trailColors = ['#FFE644', '#FF6B9E', '#64F0F0', '#8A64F0', '#64F064', '#FF8C42'];

function initCursorTrail() {
	// Create trail elements
	for (let i = 0; i < maxTrails; i++) {
		const trail = document.createElement('div');
		trail.className = 'cursor-trail';

		// Set opacity and size based on index for gradient effect
		const opacity = Math.pow((maxTrails - i) / maxTrails, 1.5) * 0.8;
		const scale = Math.pow((maxTrails - i) / maxTrails, 0.8);

		trail.style.opacity = opacity;
		trail.style.transform = `scale(${scale})`;
		trail.style.zIndex = 9999 - i;

		// Randomly select trail type
		const trailType = trailTypes[Math.floor(Math.random() * trailTypes.length)];
		const color = trailColors[Math.floor(Math.random() * trailColors.length)];

		if (trailType.type === 'emoji') {
			trail.innerHTML = trailType.content;
			trail.classList.add(trailType.class);
			trail.style.fontSize = (14 + i * 0.5) + 'px'; // Later trails slightly larger
		} else {
			const shape = document.createElement('div');
			shape.className = trailType.class;
			shape.style.setProperty('--trail-color', color);
			trail.appendChild(shape);
		}

		document.body.appendChild(trail);
		mouseTrails.push({
			element: trail,
			x: 0,
			y: 0,
			targetX: 0,
			targetY: 0,
			type: trailType.type,
			color: color,
			index: i
		});
	}

	// Mouse move event
	document.addEventListener('mousemove', (e) => {
		const currentX = e.clientX;
		const currentY = e.clientY;

		// Calculate mouse speed
		const deltaX = currentX - lastMouseX;
		const deltaY = currentY - lastMouseY;
		mouseSpeed = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

		// Save mouse position history
		mousePositions.unshift({
			x: currentX,
			y: currentY,
			speed: mouseSpeed
		});
		if (mousePositions.length > maxPositions) {
			mousePositions.pop();
		}

		lastMouseX = currentX;
		lastMouseY = currentY;
	});

	// Use animation frames to update trail positions
	function updateTrails() {
		mouseTrails.forEach((trail, index) => {
			// Adjust trail spacing based on speed
			const spacing = Math.max(2, Math.min(8, mouseSpeed * 0.1));
			const positionIndex = Math.floor(index * spacing);

			if (mousePositions[positionIndex]) {
				const targetPos = mousePositions[positionIndex];
				trail.targetX = targetPos.x;
				trail.targetY = targetPos.y;

				// Add some random offset based on speed
				const speedFactor = Math.min(targetPos.speed * 0.02, 2);
				const randomX = (Math.random() - 0.5) * speedFactor;
				const randomY = (Math.random() - 0.5) * speedFactor;

				trail.targetX += randomX;
				trail.targetY += randomY;
			}

			// Smooth interpolation to target position
			const lerp = 0.15 + (index * 0.01); // Later trails are slower
			trail.x += (trail.targetX - trail.x) * lerp;
			trail.y += (trail.targetY - trail.y) * lerp;

			// Update DOM position
			trail.element.style.left = (trail.x - 8) + 'px';
			trail.element.style.top = (trail.y - 8) + 'px';

			// Adjust opacity and size based on speed
			const speedBonus = Math.min(mouseSpeed * 0.01, 0.3);
			const baseOpacity = Math.pow((maxTrails - index) / maxTrails, 1.5) * 0.8;
			const finalOpacity = Math.min(baseOpacity + speedBonus, 1);

			const baseScale = Math.pow((maxTrails - index) / maxTrails, 0.8);
			const finalScale = baseScale + speedBonus * 0.5;

			trail.element.style.opacity = finalOpacity;
			trail.element.style.transform = `scale(${finalScale})`;
		});

		requestAnimationFrame(updateTrails);
	}

	updateTrails();

	// Periodically update trail types and colors based on mouse activity
	let updateTimer = 0;
	setInterval(() => {
		updateTimer++;

		mouseTrails.forEach((trail, index) => {
			// Decide whether to update based on mouse speed and time
			const shouldUpdate = (mouseSpeed > 5 && Math.random() < 0.2) ||
				(updateTimer > 10 && Math.random() < 0.1);

			if (shouldUpdate) {
				const newType = trailTypes[Math.floor(Math.random() * trailTypes.length)];
				const newColor = trailColors[Math.floor(Math.random() * trailColors.length)];

				// Clear original content
				trail.element.innerHTML = '';
				trail.element.className = 'cursor-trail';

				if (newType.type === 'emoji') {
					trail.element.innerHTML = newType.content;
					trail.element.classList.add(newType.class);
					trail.element.style.fontSize = (14 + index * 0.5) + 'px';
				} else {
					const shape = document.createElement('div');
					shape.className = newType.class;
					shape.style.setProperty('--trail-color', newColor);
					trail.element.appendChild(shape);
				}

				trail.type = newType.type;
				trail.color = newColor;
			}
		});

		if (updateTimer > 15) updateTimer = 0;
	}, 200); // More frequent checking

	// Gradually hide trails when mouse is idle
	let idleTimer = 0;
	setInterval(() => {
		if (mouseSpeed < 1) {
			idleTimer++;
			if (idleTimer > 10) {
				mouseTrails.forEach(trail => {
					const currentOpacity = parseFloat(trail.element.style.opacity) || 0;
					trail.element.style.opacity = Math.max(0, currentOpacity * 0.95);
				});
			}
		} else {
			idleTimer = 0;
		}
		mouseSpeed *= 0.9; // Gradually reduce speed value
	}, 100);
}

// Initialize starry background
function initStars() {
	const starsBg = document.getElementById('starsBg');
	const starCount = 50;

	for (let i = 0; i < starCount; i++) {
		const star = document.createElement('div');
		star.className = `star ${['small', 'medium', 'large'][Math.floor(Math.random() * 3)]}`;
		star.style.left = Math.random() * 100 + '%';
		star.style.top = Math.random() * 100 + '%';
		star.style.animationDelay = Math.random() * 2 + 's';
		starsBg.appendChild(star);
	}
}

// Initialize background decoration elements
function initBgDecorations() {
	const bgDecorations = document.getElementById('bgDecorations');

	// Decoration type configuration - reduced quantity
	const decorTypes = [
		// Blind box series
		{
			type: 'pixel-box',
			subtype: 'dog',
			count: 3
		},
		{
			type: 'pixel-box',
			subtype: 'cat',
			count: 3
		},
		{
			type: 'pixel-box',
			subtype: 'rabbit',
			count: 3
		},
		{
			type: 'pixel-box',
			subtype: 'robot',
			count: 3
		},

		// Small toy series
		{
			type: 'small-toy',
			subtype: 'dino',
			count: 2
		},
		{
			type: 'small-toy',
			subtype: 'ghost',
			count: 2
		},
		{
			type: 'small-toy',
			subtype: 'mushroom',
			count: 2
		},
		{
			type: 'small-toy',
			subtype: 'rocket',
			count: 2
		},

		// Flying decorations
		{
			type: 'flying-decor',
			subtype: 'bird',
			count: 2
		},
		{
			type: 'flying-decor',
			subtype: 'heart',
			count: 2
		},
		{
			type: 'flying-decor',
			subtype: 'diamond',
			count: 2
		},

		// Mystery elements
		{
			type: 'mystery-box',
			subtype: 'question',
			count: 2
		}
	];

	decorTypes.forEach(config => {
		for (let i = 0; i < config.count; i++) {
			const element = document.createElement('div');
			element.className = `bg-toy ${getAnimationClass()}`;

			// Random position
			element.style.left = Math.random() * 100 + '%';
			element.style.top = Math.random() * 100 + '%';
			element.style.animationDelay = Math.random() * 10 + 's';

			// Create specific decoration element
			const decorElement = createDecorElement(config.type, config.subtype);
			element.appendChild(decorElement);

			bgDecorations.appendChild(element);
		}
	});
}

// Create decoration element
function createDecorElement(type, subtype) {
	const element = document.createElement('div');

	if (type === 'pixel-box') {
		element.className = 'pixel-box';
		const border = document.createElement('div');
		border.className = `box-border box-${subtype}`;
		const character = document.createElement('div');
		character.className = `${subtype}-char`;
		border.appendChild(character);
		element.appendChild(border);
	} else if (type === 'small-toy') {
		element.className = `small-toy ${subtype}-toy`;
	} else if (type === 'flying-decor') {
		element.className = `flying-decor ${subtype}-toy`;
	} else if (type === 'mystery-box') {
		element.className = 'mystery-box';
	}

	return element;
}

// Get random animation class
function getAnimationClass() {
	const animations = ['float-anim', 'bounce-anim', 'rotate-anim', 'pulse-anim'];
	return animations[Math.floor(Math.random() * animations.length)];
}

// Click confetti effect
function createConfetti(x, y) {
	const colors = ['#FFE644', '#FF6B9E', '#64F0F0', '#8A64F0', '#64F064'];
	const confettiCount = 12;

	for (let i = 0; i < confettiCount; i++) {
		const confetti = document.createElement('div');
		confetti.className = 'confetti';
		confetti.style.left = x + 'px';
		confetti.style.top = y + 'px';

		const piece = document.createElement('div');
		piece.className = 'confetti-piece';
		piece.style.background = colors[Math.floor(Math.random() * colors.length)];
		piece.style.transform = `rotate(${Math.random() * 360}deg)`;
		piece.style.animationDelay = Math.random() * 0.3 + 's';
		piece.style.animationDuration = (0.8 + Math.random() * 0.7) + 's';

		// Random direction
		const angle = (Math.PI * 2 * i) / confettiCount;
		const velocity = 50 + Math.random() * 50;
		const deltaX = Math.cos(angle) * velocity;
		const deltaY = Math.sin(angle) * velocity;

		piece.style.setProperty('--dx', deltaX + 'px');
		piece.style.setProperty('--dy', deltaY + 'px');

		confetti.appendChild(piece);
		document.body.appendChild(confetti);

		// Cleanup
		setTimeout(() => {
			document.body.removeChild(confetti);
		}, 1500);
	}
}

// Click events
function initClickEffects() {
	document.addEventListener('click', (e) => {
		createConfetti(e.clientX, e.clientY);
		playClickSound();
	});
}

// Initialize particle effects
function initParticles() {
	const containers = document.querySelectorAll('.particles');
	containers.forEach(container => {
		for (let i = 0; i < 10; i++) {
			const particle = document.createElement('div');
			particle.className = 'particle';
			particle.style.left = Math.random() * 100 + '%';
			particle.style.animationDelay = Math.random() * 6 + 's';
			container.appendChild(particle);
		}
	});
}

// Removed original progress update function as we now use path selection system
// function updateProgressLine() - deleted
// function goToLevel() - restructured for returning to overview

// Game interaction - adapted for new path system
function playGame() {
	const gameResult = document.getElementById('gameResult');

	if (gameResult) {
		// Show demo result
		gameResult.style.display = 'block';
		playClickSound();
	}
}

// Audio control
function toggleAudio() {
	audioEnabled = !audioEnabled;
	const audioIcon = document.getElementById('audioIcon');
	audioIcon.textContent = audioEnabled ? '🔊' : '🔇';
	playClickSound();
}

// Play click sound (simulated)
function playClickSound() {
	if (audioEnabled) {
		// Actual audio playback logic can be added here
		console.log('🔊 Playing click sound');
		audio.volume = 0.7
		audio.play()
	} else {
		audio.pause()
	}
}

// Level click events - updated for path selection events
document.addEventListener('DOMContentLoaded', () => {
	// Path selector click events
	document.querySelectorAll('.path-selector').forEach(selector => {
		selector.addEventListener('click', () => {
			const path = selector.getAttribute('data-path');
			selectPath(path);
		});
	});

	// Path card click events
	document.querySelectorAll('.path-card').forEach(card => {
		card.addEventListener('click', () => {
			const path = card.getAttribute('data-path');
			selectPath(path);
		});
	});

	// click to team
	document.querySelectorAll('.nav-team').forEach(card => {
		card.addEventListener('click', () => {
			const path = card.getAttribute('data-path');
			selectPath(path);
		});
	});

	// Other initializations
	initStars();
	initBgDecorations();
	initParticles();
	initCursorTrail();
	initClickEffects();
	initKonamiCode(); // Initialize Easter Egg
});

// Scroll navigation effect
window.addEventListener('scroll', () => {
	const nav = document.querySelector('.top-nav');
	if (window.scrollY > 100) {
		nav.style.padding = '10px 30px';
		nav.style.background = 'rgba(10, 10, 32, 0.98)';
	} else {
		nav.style.padding = '15px 30px';
		nav.style.background = 'rgba(10, 10, 32, 0.95)';
	}
});

// Keyboard shortcuts - simplified version
document.addEventListener('keydown', (e) => {
	if (e.key === 'Escape') {
		// If Easter egg is active, close it
		if (easterEggTriggered && document.getElementById('easterEggOverlay').classList.contains(
				'easter-egg-active')) {
			closeEasterEgg();
		} else {
			goToLevel(0); // ESC key returns to overview
		}
		e.preventDefault();
	}
});

function showAlert() {
	alert("🚀 Stay Tuned  🌠\n✨👽👾🎉");
}

// ******************** popup ********************
var modal = document.getElementById("myModal");
var show_pop1 = document.getElementById("show-pop1");
var show_pop2 = document.getElementById("show-pop2");
var span = document.getElementsByClassName("close")[0];


show_pop1.onclick = function() {
	modal.style.display = "block";
}
show_pop2.onclick = function() {
	modal.style.display = "block";
}

span.onclick = function() {
	modal.style.display = "none";
}

// 点击窗口外部时关闭模态框
window.onclick = function(event) {
	if (event.target == modal) {
		modal.style.display = "none";
	}
}


// content
const dynamicContent = "🚀 Stay Tuned 🌠<br>✨👽👾🎉"

const modalText = document.getElementById("modalText");

modalText.innerHTML = dynamicContent;
// ***********************************************

// ******************** pixel-popup ********************
var pixel_modal = document.getElementById("pixel-myModal");
var pixel_close_btn = document.getElementById("pixel-close")

pixel_close_btn.onclick = function() {
	pixel_modal.style.display = "none";
}

function showPixelPopup(str) {
	const pixel_modalText = document.getElementById("pixel-modalText");
	pixel_modalText.innerHTML = str;
	pixel_modal.style.display = "block";
}
// ***********************************************

// login
function loginOrNavigate() {
	console.log("--- authToken from localStorage ---", authToken);
	if (!authToken){
		authToken = localStorage.getItem('admin-element-vue-token');
	}
	if (authToken) {
		handleLogin()
	}
	
	let login_panel = document.getElementById("login-panel-id");
	login_panel.style = null
	login_panel.style.visibility = "visible"
	switchLoginPanel(0)		// 打开登陆界面
	// window.location.href='html/touchflow-game-interface.html'
}

function loginPenelClose() {
	let login_panel = document.getElementById("login-panel-id");
	login_panel.style.visibility = "hidden"
}

function handleLogin() {
	window.location.href = 'html/touchflow-game-interface.html'

	console.log("--- running login logic ---")
}

// 切换登陆 / 注册 界面
function switchLoginPanel(idx) {
	login_page_idx = idx // 初始化
	const doc = document.getElementsByClassName("login-panel-login-form")
	const doc2 = document.getElementsByClassName("login-panel-modal-footer")
	const welt = document.getElementsByClassName("login-panel-welcome-text")
	const line = document.getElementsByClassName("login-panel-pixel-divider")
	const social = document.getElementsByClassName("login-panel-social-login")
	
	if (login_page_idx == 0) { // login page
		doc[0].style.display = "block"
		doc[1].style.display = "none"
		
		doc2[0].style.display = "block"
		doc2[1].style.display = "none"
		
		welt[0].style.display = 'block'
		line[0].style.display = 'flex'
		social[0].style.display = 'grid'
	} 
	else if (login_page_idx == 1) {	// register page
		doc[1].style.display = "block"
		doc[0].style.display = "none"
		
		doc2[0].style.display = "none"
		doc2[1].style.display = "block"
		
		welt[0].style.display = 'none'
		line[0].style.display = 'none'
		social[0].style.display = 'none'
	}
}