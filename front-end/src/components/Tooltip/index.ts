import { App } from "vue";
import Tooltip from "./index.vue";

// 注册组件
Tooltip.install = (app: App) => {
	app.component("CustomTooltip", Tooltip);
};
// 组件列表
const components = [Tooltip];
// 定义安装方法
const install = (app: App): void => {
	// 注册组件
	components.forEach((component) => {
		app.component(component.name, component);
	});
};

// 默认导出
export default {
	install,
};

// 单独导出组件
export { Tooltip };
