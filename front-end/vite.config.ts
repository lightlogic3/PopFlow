import { resolve } from "path";
import { defineConfig, loadEnv, PluginOption } from "vite";
import vue from "@vitejs/plugin-vue";
import eslintPlugin from "vite-plugin-eslint";
import viteCompression from "vite-plugin-compression";
import { createSvgIconsPlugin } from "vite-plugin-svg-icons";
import { visualizer } from "rollup-plugin-visualizer";
import { viteMockServe } from "vite-plugin-mock";
import fs from "fs";

// @see: https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => {
	const root = process.cwd();
	const env = loadEnv(mode, root);
	const {
		VITE_APP_PORT,
		VITE_APP_MOCK,
		VITE_APP_REPORT,
		VITE_APP_BUILD_GZIP,
		VITE_APP_OPEN,
		VITE_APP_API_URL_PROXY,
		VITE_APP_API_URL,
	} = env;

	const isBuild = command === "build";

	// 构建前清理dist目录
	if (isBuild) {
		const distPath = resolve(__dirname, "../dist");
		if (fs.existsSync(distPath)) {
			console.log("🗑️  正在清理旧的构建目录...");
			fs.rmSync(distPath, { recursive: true, force: true });
			console.log("✅ 构建目录清理完成");
		}
	}

	// vite 插件
	const vitePlugins: (PluginOption | PluginOption[])[] = [
		vue(),
		// 使用 svg 图标
		createSvgIconsPlugin({
			iconDirs: [resolve(__dirname, "./src/assets/iconsvg")],
			symbolId: "icon-[name]",
		}),
		// EsLint 报错信息显示在浏览器界面上
		eslintPlugin(),
	];

	// vite-plugin-compression gzip compress
	if (VITE_APP_BUILD_GZIP === "true") {
		vitePlugins.push(
			viteCompression({
				verbose: true,
				disable: false,
				threshold: 10240,
				algorithm: "gzip",
				ext: ".gz",
			}),
		);
	}

	// rollup-plugin-visualizer 是否生成包预览(分析依赖包大小,方便做优化处理)
	if (VITE_APP_REPORT === "true") {
		vitePlugins.push(visualizer());
	}

	// vite-plugin-mock
	if (VITE_APP_MOCK === "true") {
		vitePlugins.push(
			viteMockServe({
				mockPath: "mock",
				supportTs: true,
				watchFiles: true,
				localEnabled: !isBuild,
				prodEnabled: isBuild,
				logger: true,
			}),
		);
	}

	// proxy
	const proxy = {};
	if (!isBuild) {
		// 不是生产环境
		if (VITE_APP_API_URL_PROXY && VITE_APP_API_URL_PROXY !== "") {
			// VITE_APP_API_URL_PROXY存在，启用；如果VITE_APP_MOCK启用且mock中有相同url，则mock优先
			proxy[VITE_APP_API_URL] = {
				target: VITE_APP_API_URL_PROXY,
				rewrite: (path) => path.replace(VITE_APP_API_URL, ""),
				changeOrigin: true,
			};
		}
	}

	return {
		root,
		build: {
			outDir: '../dist',  // 指定编译输出目录
			assetsDir: 'assets',  // 指定静态资源目录
		},
		server: {
			host: "0.0.0.0",
			port: Number(VITE_APP_PORT || 3001),
			open: VITE_APP_OPEN === "true",
			cors: true,
			proxy,
		},
		base: '/', // 确保基础路径正确设置
		resolve: {
			alias: [
				{
					find: /^~/,
					replacement: `${resolve(__dirname, "./node_modules")}/`,
				},
				{
					find: /@\//,
					replacement: `${resolve(__dirname, "./src")}/`,
				},
			],
		},
		plugins: vitePlugins,
		css: {
			preprocessorOptions: {
				less: {
					javascriptEnabled: true,
				},
			},
		},
	};
});
