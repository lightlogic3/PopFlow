# FormItem 表单项组件

这是一个增强版的表单项组件，基于 Element Plus 的 el-form-item 组件封装，内置了 Tooltip 提示功能。

## 特性

- 简化表单项中提示的使用
- 支持通过 tooltipKey 从全局存储获取提示内容
- 支持直接提供提示内容
- 支持自定义提示位置和效果
- 支持悬停提示和点击弹出层两种模式
- 继承 el-form-item 的所有属性和事件

## 基本用法

### 悬停提示模式（默认）

```vue
<template>
  <el-form :model="form" label-width="100px">
    <!-- 使用 tooltipKey 获取提示 -->
    <FormItem 
      label="角色ID" 
      prop="role_id" 
      tooltipKey="role_id"
    >
      <el-input v-model="form.role_id" placeholder="请输入角色ID(role0001)" />
    </FormItem>
    
    <!-- 直接提供提示内容 -->
    <FormItem 
      label="角色名称" 
      prop="role_name" 
      tooltipContent="请输入角色名称，长度不超过20个字符"
    >
      <el-input v-model="form.role_name" placeholder="请输入角色名称" />
    </FormItem>
    
    <!-- 自定义提示位置 -->
    <FormItem 
      label="角色标签" 
      prop="role_tags" 
      tooltipKey="role_tags"
      tooltipPlacement="right"
    >
      <el-select v-model="form.role_tags" multiple placeholder="请选择角色标签">
        <el-option label="管理员" value="admin" />
        <el-option label="普通用户" value="user" />
      </el-select>
    </FormItem>
    
    <!-- 自定义提示效果 -->
    <FormItem 
      label="角色描述" 
      prop="role_desc" 
      tooltipContent="请输入角色的详细描述信息"
      tooltipEffect="light"
    >
      <el-input v-model="form.role_desc" type="textarea" rows="2" />
    </FormItem>
    
    <!-- 不使用提示 -->
    <FormItem label="状态" prop="status">
      <el-switch v-model="form.status" />
    </FormItem>
  </el-form>
</template>

<script setup>
import { reactive } from 'vue';

const form = reactive({
  role_id: '',
  role_name: '',
  role_tags: [],
  role_desc: '',
  status: true
});
</script>
```

### 弹出层提示模式

```vue
<template>
  <el-form :model="form" label-width="100px">
    <!-- 点击提示图标显示弹出层 -->
    <FormItem 
      label="角色ID" 
      prop="role_id" 
      tooltipKey="role_id"
      :usePopover="true"
      popoverTitle="角色ID说明"
    >
      <el-input v-model="form.role_id" placeholder="请输入角色ID(role0001)" />
    </FormItem>
    
    <!-- 自定义弹出层宽度和关闭按钮 -->
    <FormItem 
      label="角色描述" 
      prop="role_desc" 
      tooltipContent="请详细描述该角色的权限范围和使用场景，包括可访问的模块、可执行的操作以及使用限制等。详细的描述有助于其他管理员理解该角色的用途。"
      :usePopover="true"
      popoverTitle="角色描述填写指南"
      :popoverWidth="300"
      closeButtonText="我知道了"
      closeButtonType="success"
    >
      <el-input v-model="form.role_desc" type="textarea" rows="4" />
    </FormItem>
  </el-form>
</template>
```

## 属性

| 属性名 | 说明 | 类型 | 默认值 |
| --- | --- | --- | --- |
| label | 表单项标签 | String | '' |
| tooltipKey | 提示内容的键，用于从全局存储获取内容 | String | '' |
| tooltipContent | 提示内容，优先级高于 tooltipKey | String | '' |
| tooltipPlacement | 提示位置 | String | 'top' |
| tooltipEffect | 提示效果 | String | 'dark' |
| usePopover | 是否使用弹出层模式 | Boolean | false |
| popoverTitle | 弹出层标题 | String | '提示信息' |
| popoverWidth | 弹出层宽度 | Number/String | 260 |
| popoverTrigger | 弹出层触发方式 | String | 'click' |
| closeButtonText | 关闭按钮文本 | String | '关闭' |
| closeButtonType | 关闭按钮类型 | String | 'primary' |

此外，组件还支持 el-form-item 的所有属性，如 prop、required、rules 等。

## 注意事项

- 需要先进行全局注册才能使用：`app.component("FormItem", FormItem);`
- 需要确保 Tooltip 组件已正确配置并初始化提示数据 