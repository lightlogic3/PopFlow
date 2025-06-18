import { App } from "vue";
import ModelSelector from "./index.vue";

// 注册组件
ModelSelector.install = (app: App) => {
	app.component(ModelSelector.name, ModelSelector);
};

export default ModelSelector;
