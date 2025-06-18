<template>
	<el-dialog v-model="dialogVisible" :title="isEdit ? '编辑盲盒' : '新建盲盒'" width="60%" @close="handleDialogClose">
		<el-form ref="formRef" :model="formData" :rules="formRules" label-width="120px">
			<el-row :gutter="20">
				<el-col :span="12">
					<el-form-item label="盲盒名称" prop="name">
						<el-input v-model="formData.name" placeholder="请输入盲盒名称" />
					</el-form-item>
				</el-col>
				<el-col :span="12">
					<el-form-item label="价格（积分）" prop="price">
						<el-input-number v-model="formData.price" placeholder="请输入价格" :min="0" style="width: 100%" />
					</el-form-item>
				</el-col>
			</el-row>
			<el-row :gutter="20">
				<el-col :span="12">
					<el-form-item label="保底次数" prop="guarantee_count">
						<el-input-number
							v-model="formData.guarantee_count"
							placeholder="请输入保底次数"
							:min="1"
							style="width: 100%"
						/>
					</el-form-item>
				</el-col>
				<el-col :span="12">
					<el-form-item label="保底稀有度" prop="guarantee_rarity">
						<el-select v-model="formData.guarantee_rarity" placeholder="请选择保底稀有度">
							<el-option
								v-for="item in guaranteeRarityChoices"
								:key="item.value"
								:label="item.label"
								:value="item.value"
							/>
						</el-select>
					</el-form-item>
				</el-col>
			</el-row>
			<el-form-item label="状态" prop="status">
				<el-radio-group v-model="formData.status">
					<el-radio :label="1">启用</el-radio>
					<el-radio :label="0">禁用</el-radio>
				</el-radio-group>
			</el-form-item>
			<el-form-item label="盲盒图片" prop="image_url">
				<FileUploader v-model="formData.image_url" folder="blind-box" accept="image/*" :max-size="5" />
			</el-form-item>
			<el-form-item label="描述信息" prop="description">
				<el-input v-model="formData.description" type="textarea" :rows="3" placeholder="请输入盲盒描述" />
			</el-form-item>

			<!-- 概率规则配置（可视化界面） -->
			<el-form-item label="概率规则">
				<el-card class="probability-rules-card">
					<el-tabs v-model="activeTab" type="border-card">
						<!-- 基本配置 -->
						<el-tab-pane label="基本配置" name="basic">
							<el-form-item label="概率类型" prop="probabilityType">
								<el-select v-model="probabilityRules.probability_type" placeholder="请选择概率类型" style="width: 100%">
									<el-option label="权重计算" value="weight_based" />
									<el-option label="固定概率" value="fixed_probability" />
								</el-select>
							</el-form-item>

							<el-divider>权重倍率配置</el-divider>

							<div class="rarity-multiplier">
								<el-form-item v-for="(rarity, index) in guaranteeRarityChoices" :key="index" :label="rarity.label">
									<el-input-number
										v-model="probabilityRules.weight_calculation.rarity_multiplier[rarity.value]"
										:precision="2"
										:step="0.01"
										:min="0"
										:max="10"
										style="width: 100%"
										@change="updateProbabilityRules"
									/>
								</el-form-item>
							</div>
						</el-tab-pane>

						<!-- 保底规则 -->
						<el-tab-pane label="保底规则" name="guarantee">
							<div class="guarantee-rule-config">
								<el-switch
									v-model="probabilityRules.guarantee_rule.enabled"
									active-text="启用保底"
									inactive-text="禁用保底"
									@change="updateProbabilityRules"
									style="margin-bottom: 15px"
								/>

								<template v-if="probabilityRules.guarantee_rule.enabled">
									<el-form-item label="保底类型">
										<el-select
											v-model="probabilityRules.guarantee_rule.type"
											placeholder="请选择保底类型"
											style="width: 100%"
										>
											<el-option label="渐进式" value="progressive" />
											<el-option label="硬保底" value="hard" />
										</el-select>
									</el-form-item>

									<el-divider>保底规则列表</el-divider>

									<div
										v-for="(rule, index) in probabilityRules.guarantee_rule.rules"
										:key="index"
										class="guarantee-rule-item"
									>
										<el-row :gutter="10" align="middle">
											<el-col :span="7">
												<el-form-item label="抽数">
													<el-input-number
														v-model="rule.count"
														:min="1"
														style="width: 100%"
														@change="updateProbabilityRules"
													/>
												</el-form-item>
											</el-col>
											<el-col :span="7">
												<el-form-item label="保底稀有度">
													<el-select v-model="rule.guarantee_rarity" placeholder="稀有度" style="width: 100%">
														<el-option
															v-for="item in guaranteeRarityChoices"
															:key="item.value"
															:label="item.label"
															:value="item.value"
														/>
													</el-select>
												</el-form-item>
											</el-col>
											<el-col :span="8">
												<el-form-item label="描述">
													<el-input v-model="rule.description" placeholder="描述" style="width: 100%" />
												</el-form-item>
											</el-col>
											<el-col :span="2">
												<el-button type="danger" circle @click="removeGuaranteeRule(index)">
													<el-icon><Delete /></el-icon>
												</el-button>
											</el-col>
										</el-row>
									</div>

									<el-button type="primary" @click="addGuaranteeRule" plain style="width: 100%">添加规则</el-button>
								</template>
							</div>
						</el-tab-pane>

						<!-- JSON编辑 -->
						<el-tab-pane label="JSON编辑" name="json">
							<el-alert
								title="警告：直接编辑JSON可能会覆盖可视化界面的配置"
								type="warning"
								:closable="false"
								show-icon
								style="margin-bottom: 15px"
							/>
							<el-input
								v-model="probabilityRulesText"
								type="textarea"
								:rows="10"
								placeholder="请输入JSON格式的概率规则"
								@blur="handleProbabilityRulesTextChange"
							/>
						</el-tab-pane>
					</el-tabs>
				</el-card>
			</el-form-item>
		</el-form>
		<template #footer>
			<div class="dialog-footer">
				<el-button @click="dialogVisible = false">取消</el-button>
				<el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
			</div>
		</template>
	</el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from "vue";
import { ElMessage } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";
import { Delete } from "@element-plus/icons-vue";
import FileUploader from "@/components/FileUploader";
import {
	createBlindBox,
	updateBlindBox,
	getGuaranteeRarityChoices,
	type BlindBoxCreate,
	type BlindBoxUpdate,
	type GuaranteeRarityChoice,
} from "@/api/blind-box";

const props = defineProps({
	visible: {
		type: Boolean,
		default: false,
	},
	isEdit: {
		type: Boolean,
		default: false,
	},
	editData: {
		type: Object,
		default: () => ({}),
	},
});

const emit = defineEmits(["update:visible", "saved"]);

// 响应式数据
const dialogVisible = ref(false);
const submitting = ref(false);
const formRef = ref<FormInstance>();
const guaranteeRarityChoices = ref<GuaranteeRarityChoice[]>([]);
const probabilityRulesText = ref("{}");
const activeTab = ref("basic");
const probabilityRules = ref({
	probability_type: "weight_based",
	weight_calculation: {
		method: "card_weight",
		rarity_multiplier: {
			"1": 1.0,
			"2": 0.4,
			"3": 0.08,
			"4": 0.01,
		},
	},
	guarantee_rule: {
		enabled: true,
		type: "progressive",
		rules: [
			{ count: 10, guarantee_rarity: 2, description: "10抽必出稀有" },
			{ count: 50, guarantee_rarity: 3, description: "50抽必出史诗" },
			{ count: 100, guarantee_rarity: 4, description: "100抽必出传说" },
		],
	},
});

// 表单数据
const formData = reactive<BlindBoxCreate & { id?: number }>({
	name: "",
	description: "",
	image_url: "",
	price: undefined,
	probability_rules: "{}",
	guarantee_count: undefined,
	guarantee_rarity: undefined,
	status: 1,
});

// 表单验证规则
const formRules: FormRules = {
	name: [{ required: true, message: "请输入盲盒名称", trigger: "blur" }],
	probability_rules: [{ required: true, message: "请输入概率规则", trigger: "blur" }],
};

// 同步props.visible到本地
watch(
	() => props.visible,
	(newVal) => {
		dialogVisible.value = newVal;

		if (newVal) {
			fetchGuaranteeRarityChoices();

			if (props.isEdit && props.editData) {
				// 编辑模式，填充表单数据
				Object.assign(formData, props.editData);

				// 解析概率规则
				try {
					const rules = JSON.parse(props.editData.probability_rules || "{}");
					probabilityRulesText.value = props.editData.probability_rules || "{}";

					// 确保概率规则格式完整
					rules.probability_type = rules.probability_type || "weight_based";
					rules.weight_calculation = rules.weight_calculation || {
						method: "card_weight",
						rarity_multiplier: { "1": 1.0, "2": 0.4, "3": 0.08, "4": 0.01 },
					};
					rules.guarantee_rule = rules.guarantee_rule || { enabled: false, type: "progressive", rules: [] };

					probabilityRules.value = rules;
					// 确保formData中也有最新的probability_rules
					formData.probability_rules = probabilityRulesText.value;
				} catch (error) {
					console.error("Error parsing probability rules:", error);
					resetProbabilityRules();
					// 重置后确保formData中有正确的初始值
					formData.probability_rules = JSON.stringify(probabilityRules.value);
				}
			} else {
				// 创建模式，重置表单
				resetFormData();
				// 确保formData包含默认的probability_rules值
				formData.probability_rules = JSON.stringify(probabilityRules.value);
			}
		}
	},
);

// 同步本地状态到父组件
watch(
	() => dialogVisible.value,
	(newVal) => {
		emit("update:visible", newVal);
	},
);

// 获取保底稀有度选项
const fetchGuaranteeRarityChoices = async () => {
	try {
		const response = await getGuaranteeRarityChoices();
		guaranteeRarityChoices.value = response || [];
	} catch (error) {
		console.error("Error fetching guarantee rarity choices:", error);
	}
};

// 处理概率规则文本改变
const handleProbabilityRulesTextChange = () => {
	try {
		const parsedRules = JSON.parse(probabilityRulesText.value);
		probabilityRules.value = parsedRules;
		// 更新formData中的probability_rules
		formData.probability_rules = probabilityRulesText.value;
	} catch (error) {
		ElMessage.warning("概率规则不是有效的JSON格式");
	}
};

// 提交表单
const handleSubmit = async () => {
	if (!formRef.value) return;

	try {
		await formRef.value.validate();

		// 验证概率规则JSON格式
		try {
			// 使用可视化界面配置的数据更新JSON
			const rulesJson = JSON.stringify(probabilityRules.value);
			probabilityRulesText.value = rulesJson;
			// 更新formData中的probability_rules字段
			formData.probability_rules = rulesJson;
		} catch (error) {
			ElMessage.error("概率规则必须是有效的JSON格式");
			return;
		}

		submitting.value = true;

		if (props.isEdit) {
			const updateData: BlindBoxUpdate = { ...formData };
			await updateBlindBox(formData.id!, updateData);
			ElMessage.success("更新成功");
		} else {
			await createBlindBox(formData);
			ElMessage.success("创建成功");
		}

		dialogVisible.value = false;
		emit("saved");
	} catch (error) {
		ElMessage.error(props.isEdit ? "更新失败" : "创建失败");
		console.error("Error submitting form:", error);
	} finally {
		submitting.value = false;
	}
};

// 处理对话框关闭
const handleDialogClose = () => {
	formRef.value?.clearValidate();
	resetFormData();
};

// 重置表单数据
const resetFormData = () => {
	Object.assign(formData, {
		name: "",
		description: "",
		image_url: "",
		price: undefined,
		probability_rules: "{}",
		guarantee_count: undefined,
		guarantee_rarity: undefined,
		status: 1,
	});
	resetProbabilityRules();
};

// 重置概率规则
const resetProbabilityRules = () => {
	probabilityRules.value = {
		probability_type: "weight_based",
		weight_calculation: {
			method: "card_weight",
			rarity_multiplier: {
				"1": 1.0,
				"2": 0.4,
				"3": 0.08,
				"4": 0.01,
			},
		},
		guarantee_rule: {
			enabled: true,
			type: "progressive",
			rules: [
				{ count: 10, guarantee_rarity: 2, description: "10抽必出稀有" },
				{ count: 50, guarantee_rarity: 3, description: "50抽必出史诗" },
				{ count: 100, guarantee_rarity: 4, description: "100抽必出传说" },
			],
		},
	};

	const rulesJson = JSON.stringify(probabilityRules.value);
	probabilityRulesText.value = rulesJson;
	// 确保formData中的probability_rules也被更新
	formData.probability_rules = rulesJson;
};

// 更新概率规则
const updateProbabilityRules = () => {
	const rulesJson = JSON.stringify(probabilityRules.value);
	probabilityRulesText.value = rulesJson;
	// 同步到formData
	formData.probability_rules = rulesJson;
};

// 添加保底规则
const addGuaranteeRule = () => {
	probabilityRules.value.guarantee_rule.rules.push({
		count: 1,
		guarantee_rarity: guaranteeRarityChoices.value[0].value,
		description: "",
	});
	updateProbabilityRules();
};

// 移除保底规则
const removeGuaranteeRule = (index: number) => {
	probabilityRules.value.guarantee_rule.rules.splice(index, 1);
	updateProbabilityRules();
};
</script>

<style lang="scss" scoped>
:deep(.el-dialog) {
	.el-dialog__header {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		padding: 20px;
		margin: 0;
		border-radius: 8px 8px 0 0;
	}

	.el-dialog__title {
		color: white;
		font-weight: bold;
	}

	.el-dialog__headerbtn .el-dialog__close {
		color: white;
	}

	.form-tip {
		font-size: 12px;
		color: #909399;
		margin-top: 5px;
	}
}

.probability-rules-card {
	margin-bottom: 20px;

	.el-tabs {
		min-height: 300px;
	}

	.guarantee-rule-item {
		border: 1px solid #ebeef5;
		border-radius: 4px;
		padding: 10px;
		margin-bottom: 10px;
	}

	.el-divider {
		margin: 15px 0;
	}

	.rarity-multiplier {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 15px;
	}

	.guarantee-rule-config {
		padding: 10px 0;
	}
}
</style>
