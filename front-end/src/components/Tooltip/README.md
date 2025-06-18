# Tooltip 提示组件

这是一个增强版的提示组件，基于 Element Plus 的 el-tooltip 组件封装，支持从全局存储获取提示内容。

## 特性

- 支持通过 key 从全局存储获取提示内容
- 支持自定义提示内容
- 支持自定义提示图标
- 支持悬停提示和点击弹出层两种模式
- 继承 el-tooltip 的所有属性和事件

## 安装与初始化

在应用启动时，需要初始化提示数据：

```typescript
// 在应用入口文件（如 main.ts）中
import { createApp } from 'vue';
import App from './App.vue';
import { useTooltipStore } from '@/store/tooltip';

const app = createApp(App);
// ...其他初始化代码

// 初始化 pinia
const pinia = createPinia();
app.use(pinia);

// 初始化提示数据
const tooltipStore = useTooltipStore();
tooltipStore.fetchTooltipData();

app.mount('#app');
```

## 基本用法

### 悬停提示模式（默认）

```vue
<template>
  <!-- 通过 tooltipKey 从全局获取提示内容 -->
  <div class="form-item">
    <label>用户名：</label>
    <el-input v-model="username" />
    <Tooltip tooltipKey="username_tip" />
  </div>

  <!-- 直接指定提示内容 -->
  <div class="form-item">
    <label>密码：</label>
    <el-input v-model="password" type="password" />
    <Tooltip content="密码长度至少为8位，需包含字母和数字" />
  </div>

  <!-- 自定义图标 -->
  <div class="form-item">
    <label>邮箱：</label>
    <el-input v-model="email" />
    <Tooltip 
      tooltipKey="email_tip" 
      :iconSize="18" 
      iconColor="#409EFF" 
    />
  </div>

  <!-- 自定义提示内容插槽 -->
  <div class="form-item">
    <label>地址：</label>
    <el-input v-model="address" />
    <Tooltip>
      <template #content>
        <div>
          <h4>地址格式说明</h4>
          <p>请输入详细的地址信息，包括：</p>
          <ul>
            <li>省/市/区</li>
            <li>街道/小区</li>
            <li>门牌号</li>
          </ul>
        </div>
      </template>
    </Tooltip>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import Tooltip from '@/components/Tooltip/index.vue';

const username = ref('');
const password = ref('');
const email = ref('');
const address = ref('');
</script>

<style scoped>
.form-item {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

label {
  width: 80px;
  margin-right: 10px;
}
</style>
```

### 弹出层模式

```vue
<template>
  <!-- 点击显示弹出层 -->
  <div class="form-item">
    <label>用户名：</label>
    <el-input v-model="username" />
    <Tooltip 
      tooltipKey="username_tip" 
      :usePopover="true" 
      popoverTitle="用户名说明"
    />
  </div>

  <!-- 自定义弹出层宽度和关闭按钮 -->
  <div class="form-item">
    <label>详细说明：</label>
    <el-input v-model="description" type="textarea" />
    <Tooltip 
      content="这里是一段很长的说明文本，包含了详细的填写要求和注意事项..." 
      :usePopover="true" 
      popoverTitle="详细说明" 
      :popoverWidth="300"
      closeButtonText="我知道了"
      closeButtonType="success"
    />
  </div>
</template>
```

### 在FormItem中使用

```vue
<template>
  <!-- 悬停提示 -->
  <FormItem 
    label="角色ID" 
    prop="role_id" 
    tooltipKey="role_id"
  >
    <el-input v-model="form.role_id" />
  </FormItem>
  
  <!-- 点击弹出层 -->
  <FormItem 
    label="角色说明" 
    prop="role_desc" 
    tooltipContent="请详细描述该角色的权限范围和使用场景..."
    :usePopover="true"
    popoverTitle="角色说明填写指南"
  >
    <el-input v-model="form.role_desc" type="textarea" />
  </FormItem>
</template>
```

## 属性

| 属性名 | 说明 | 类型 | 默认值 |
| --- | --- | --- | --- |
| tooltipKey | 提示内容的键，用于从全局存储获取内容 | String | '' |
| content | 提示内容，优先级高于 tooltipKey | String | '' |
| showIcon | 是否显示图标 | Boolean | true |
| iconSize | 图标大小 | Number/String | 16 |
| iconColor | 图标颜色 | String | '#909399' |
| usePopover | 是否使用弹出层模式 | Boolean | false |
| popoverTitle | 弹出层标题 | String | '提示信息' |
| popoverWidth | 弹出层宽度 | Number/String | 260 |
| popoverTrigger | 弹出层触发方式 | String | 'click' |
| closeButtonText | 关闭按钮文本 | String | '关闭' |
| closeButtonType | 关闭按钮类型 | String | 'primary' |

此外，组件还支持 el-tooltip 的所有属性，如 effect、placement、trigger 等。

## 事件

| 事件名 | 说明 | 回调参数 |
| --- | --- | --- |
| before-show | 提示显示前触发 | - |
| before-hide | 提示隐藏前触发 | - |
| show | 提示显示后触发 | - |
| hide | 提示隐藏后触发 | - |
| popover-open | 弹出层打开时触发 | - |
| popover-close | 弹出层关闭时触发 | - |

## 插槽

| 插槽名 | 说明 |
| --- | --- |
| default | 触发提示的内容 |
| content | 自定义提示内容 |