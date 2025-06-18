import { createApp } from "vue";
// 全局样式
import "@/assets/css/global.scss";
// ElementPlus UI组件
import ElementPlus from "element-plus";
// ElementPlus 英文语言包
import { en } from "element-plus/es/locale/index";
// App
import App from "@/App.vue";
// vue router
import router from "@/config/router";
// pinia store
import store from "@/config/store";
// 导入组件
import { Tooltip } from "@/components/Tooltip";
import FormItem from "@/components/FormItem/index.vue";
// Register icon sprite
import "virtual:svg-icons-register";

const app = createApp(App);
app.use(router);
app.use(store);
app.use(ElementPlus, {
  locale: en
});
// 全局注册组件
app.component("Tooltip", Tooltip);
app.component("FormItem", FormItem);

// 挂载应用
app.mount("#app");
