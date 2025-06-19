let authToken = localStorage.getItem('admin-element-vue-token');
// 像素化按钮点击效果
function pixelClickEffect(element) {
	element.style.transform = 'scale(0.95)';
	element.style.filter = 'brightness(1.2)';

	setTimeout(() => {
		element.style.transform = '';
		element.style.filter = '';
	}, 150);
}

// 关闭模态框
document.querySelector('.login-panel-modal-close').addEventListener('click', () => {
	const modal = document.querySelector('.login-panel-background');
	modal.style.animation = 'pixelFadeOut 0.2s steps(8, end) forwards';
	setTimeout(() => {
		console.log('Modal closed');
		modal.style.visibility = "hidden"
	}, 500);
});

console.log()

// 表单提交
document.querySelector('.login-form').addEventListener('submit', (e) => {
	e.preventDefault();
	login(e)
});

document.querySelector('.register-form').addEventListener('submit', (e) => {
	e.preventDefault();
	register(e)
})

// 社交登录按钮
document.querySelectorAll('.login-panel-pixel-social-btn').forEach(btn => {
	btn.addEventListener('click', () => {
		const method = btn.textContent.trim();
		console.log('Social login:', method);
		pixelClickEffect(btn);
	});
});

// 输入框像素效果
document.querySelectorAll('.login-panel-form-input').forEach(input => {
	input.addEventListener('focus', () => {
		input.style.boxShadow = `
                    0 0 0 2px var(--dark-bg),
                    0 0 0 4px var(--primary-green),
                    inset 0 0 8px rgba(0, 255, 136, 0.2)
                `;
	});

	input.addEventListener('blur', () => {
		input.style.boxShadow = '';
	});
});

// 添加fadeOut动画
const style = document.createElement('style');
style.textContent = `
            @keyframes pixelFadeOut {
                from { opacity: 1; }
                to { opacity: 0; }
            }
        `;
document.head.appendChild(style);

// 键盘事件
document.addEventListener('keydown', (e) => {
	if (e.code === 'Enter' && e.target.tagName !== 'INPUT') {
		document.querySelector('.pixel-btn').click();
	}
	if (e.code === 'Escape') {
		document.querySelector('.login-panel-modal-close').click();
	}
});

// 初始化
document.addEventListener('DOMContentLoaded', () => {
	// createPixelParticles();

	// 启动音效模拟
	setTimeout(() => {
		console.log('🎵 Pixel login system activated');
	}, 500);
});

// 像素风格鼠标悬停效果
document.querySelectorAll('button, a, input').forEach(element => {
	element.addEventListener('mouseenter', () => {
		element.style.filter = 'brightness(1.1) contrast(1.1)';
	});

	element.addEventListener('mouseleave', () => {
		element.style.filter = '';
	});
});

// login
async function login(e) {
	const username = e.target.querySelector('input[type="text"]').value;
	const password = e.target.querySelector('input[type="password"]').value;

	const btn = document.querySelector('.login-panel-pixel-btn');
	btn.textContent = 'Connecting...';
	btn.style.background = 'var(--primary-cyan)';

	// 添加加载动画
	const loading = document.createElement('div');
	loading.className = 'pixel-loading';
	btn.appendChild(loading);
	loading.style.opacity = '1';
	btn.style.pointerEvents = "none"

	try {
		const response = await fetch(`${API_BASE_URL}/auth/login`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				username,
				password
			})
		});

		const data = await response.json();

		if (response.ok && data.code === 200) {
			// 保存token
			authToken = data.data.token;
			localStorage.setItem('authToken', authToken);

			btn.style.pointerEvents = null

			// 成功后的像素效果
			document.body.style.filter = 'brightness(1.2)';
			setTimeout(() => {
				document.body.style.filter = '';
				handleLogin()
			}, 200);

		} else {
			alert(`Login failed: ${data.message || data.detail || 'Unknown error'}`);
		}
		btn.style = null
		btn.textContent = 'Connect to Universe';
		loading.remove();
	} catch (error) {
		const btn = document.querySelector('.login-panel-pixel-btn');
		// console.error('Registration request failed:', error);
		alert('Login request failed. Please try again later.');
		btn.style = null
		btn.textContent = 'Connect to Universe';
		loading.remove();
	}
}

// register
async function register(e) {
	const username = e.target.querySelector('.username').value;
	const password = e.target.querySelector('.password').value;
	const cpassword = e.target.querySelector('.cpassword').value;
	const nickname = e.target.querySelector('.nickname').value;
	const email = e.target.querySelector('.email').value;
	const sex = e.target.querySelector('select').value;


	if (!(password == cpassword)) {
		alert("Passwords do not match")
	}

	const btn = document.querySelector('#login-panel-pixel-btn-id-register');
	btn.textContent = 'Loading...';
	btn.style.background = 'var(--primary-cyan)';
	// 添加加载动画
	// 添加加载动画
	const loading = document.createElement('div');
	loading.className = 'pixel-loading';
	btn.appendChild(loading);
	loading.style.opacity = '1';
	btn.style.pointerEvents = "none"

	try {
		const response = await fetch(`${API_BASE_URL}/auth/register`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				username,
				password,
				nickname,
				email: email || undefined,
				sex: 0, // 默认值
				status: 0 // 默认启用
			})
		});

		const data = await response.json();

		if (response.ok && data.code === 200) {
			showPixelPopup("Registration successful! You received 100 bonus points.")
			// 保存token
			authToken = data.data.token;
			localStorage.setItem('authToken', authToken);
			document.querySelector('.login-panel-modal-close').click()		// 点击关闭注册页面

			let timer = setInterval(() => {
				if (document.getElementById("pixel-myModal").style.display == "none") {
					handleLogin()
					clearInterval(timer)
				}
			}, 500)
		} else {
			alert(`Registration failed: ${data.message || data.detail || 'Unknown error'}`)
		}
		btn.style = null
		btn.textContent = 'register';
		loading.remove();
	} catch (error) {
		console.error('Registration request failed:', error);
		alert('Registration request failed. Please try again later.')
		btn.style = null
		btn.textContent = 'register';
		loading.remove();
	}
}

// logout
function logout() {
	fetch(`${API_BASE_URL}/auth/logout`, {
		method: 'POST',
		headers: {
			'Authorization': `Bearer ${authToken}`
		}
	}).finally(() => {
		// 无论成功失败都清除token
		localStorage.removeItem('authToken');
		window.location.href = '../index.html';
	});
}