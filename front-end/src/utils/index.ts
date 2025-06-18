/**
 * 深拷贝对象
 * @param source 源对象
 * @returns 拷贝后的新对象
 */
export function deepClone<T>(source: T): T {
	if (source === null || typeof source !== "object") {
		return source;
	}

	// 处理Date对象
	if (source instanceof Date) {
		return new Date(source.getTime()) as unknown as T;
	}

	// 处理数组
	if (Array.isArray(source)) {
		return source.map((item) => deepClone(item)) as unknown as T;
	}

	// 处理普通对象
	const result = {} as T;
	for (const key in source) {
		if (Object.prototype.hasOwnProperty.call(source, key)) {
			result[key] = deepClone(source[key]);
		}
	}

	return result;
}

/**
 * 防抖函数
 * @param fn 需要防抖的函数
 * @param delay 延迟时间
 * @returns 防抖后的函数
 */
export function debounce<T extends (...args: any[]) => any>(fn: T, delay: number): (...args: Parameters<T>) => void {
	let timer: number | null = null;
	return function (this: any, ...args: Parameters<T>) {
		if (timer) {
			clearTimeout(timer);
		}
		timer = window.setTimeout(() => {
			fn.apply(this, args);
			timer = null;
		}, delay);
	};
}

/**
 * 节流函数
 * @param fn 需要节流的函数
 * @param delay 延迟时间
 * @returns 节流后的函数
 */
export function throttle<T extends (...args: any[]) => any>(fn: T, delay: number): (...args: Parameters<T>) => void {
	let lastTime = 0;
	return function (this: any, ...args: Parameters<T>) {
		const now = Date.now();
		if (now - lastTime >= delay) {
			fn.apply(this, args);
			lastTime = now;
		}
	};
}

/**
 * 格式化日期
 * @param date 日期对象或日期字符串
 * @param format 格式化字符串，默认为 'YYYY-MM-DD HH:mm:ss'
 * @returns 格式化后的日期字符串
 */
export function formatDate(date: Date | string, format: string = "YYYY/MM/DD HH:mm:ss"): string {
	if (!date) {
		return "";
	}
	const d = typeof date === "string" ? new Date(date) : date;

	const year = d.getFullYear();
	const month = d.getMonth() + 1;
	const day = d.getDate();
	const hour = d.getHours();
	const minute = d.getMinutes();
	const second = d.getSeconds();

	const padZero = (num: number): string => {
		return num < 10 ? `0${num}` : `${num}`;
	};

	return format
		.replace(/YYYY/g, `${year}`)
		.replace(/MM/g, padZero(month))
		.replace(/DD/g, padZero(day))
		.replace(/HH/g, padZero(hour))
		.replace(/mm/g, padZero(minute))
		.replace(/ss/g, padZero(second));
}

/**
 * Checks if a date or number of days is within the specified threshold from today
 * @param {string|number} input - Either a date string (ISO format) or number of days
 * @param {number} threshold - Number of days threshold (default: 7)
 * @return {boolean} - True if the date is within the threshold, false otherwise
 */
export function isWithinThreshold(input, threshold = 7) {
	const today = new Date();
	today.setHours(0, 0, 0, 0); // Reset time to start of day

	let targetDate;

	// Check if input is a number (days)
	if (typeof input === "number") {
		targetDate = new Date();
		targetDate.setDate(targetDate.getDate() + input);
		targetDate.setHours(0, 0, 0, 0); // Reset time to start of day
	}
	// Check if input is a date string
	else if (typeof input === "string") {
		targetDate = new Date(input);

		// Check if date is valid
		if (isNaN(targetDate.getTime())) {
			return false;
		}
	} else {
		return false;
	}

	// Calculate difference in days
	const diffTime = targetDate.getTime() - today.getTime();
	const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

	// Return true if within threshold
	return diffDays <= threshold;
}

// Examples:
// isWithinThreshold("2025-10-11T14:21:08", 180) - checks if the date is within 180 days from today。
// isWithinThreshold(5, 7) - checks if 5 days from today is within 7 days (should return true)
