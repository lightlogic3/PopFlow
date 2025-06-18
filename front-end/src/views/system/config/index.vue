<template>
	<div class="system-config">
		<div class="header">
			<h1 class="title">System Configuration</h1>
			<el-button type="primary" @click="handleAdd">
				<el-icon>
					<Plus />
				</el-icon>
				Add Configuration
			</el-button>
		</div>

		<div class="search-box">
			<el-input
				v-model="searchQuery"
				placeholder="Search configuration items..."
				class="search-input"
				clearable
				@clear="handleSearch"
				@keyup.enter="handleSearch"
			>
				<template #prefix>
					<el-icon>
						<Search />
					</el-icon>
				</template>
			</el-input>
		</div>

		<el-tabs v-model="tabsValue">
			<el-tab-pane :label="use_typeList[key]" :name="key" v-for="(data, key) in tableData" :key="key">
				<el-table v-loading="loading" :data="data" style="width: 100%" border>
					<el-table-column prop="use_type" label="Usage Type" min-width="50">
						<template #default="{ row }">
							<el-tag>
								{{ use_typeList[row.use_type] || "System" }}
							</el-tag>
						</template>
					</el-table-column>
					<el-table-column prop="config_key" label="Config Key" min-width="100" />
					<el-table-column label="Config Value" min-width="200" show-overflow-tooltip>
						<template #default="{ row }">
							{{ formatConfigValue(row.config_value) || "Secret keys can only be modified, not viewed" }}
						</template>
					</el-table-column>
					<el-table-column prop="description" label="Description" min-width="150" show-overflow-tooltip />
					<el-table-column
						prop="update_time"
						label="Update Time"
						width="180"
						:formatter="(row: any, column: any, cellValue: any)=>formatDate(cellValue)"
					/>
					<el-table-column label="Actions" width="150" fixed="right">
						<template #default="{ row }">
							<el-button-group>
								<el-button type="primary" link @click="handleEdit(row)">
									<el-icon>
										<Edit />
									</el-icon>
									Edit
								</el-button>
								<el-button type="danger" link @click="handleDelete(row)">
									<el-icon>
										<Delete />
									</el-icon>
									Delete
								</el-button>
							</el-button-group>
						</template>
					</el-table-column>
				</el-table>
			</el-tab-pane>
		</el-tabs>

		<div class="pagination">
			<el-pagination
				v-model:current-page="currentPage"
				v-model:page-size="pageSize"
				:total="total"
				:page-sizes="[10, 20, 50, 100]"
				layout="total, sizes, prev, pager, next"
				@size-change="handleSizeChange"
				@current-change="handleCurrentChange"
			/>
		</div>

		<!-- Add/Edit Dialog -->
		<el-dialog v-model="dialogVisible" :title="dialogType === 'add' ? 'Add Configuration' : 'Edit Configuration'" width="800px">
			<el-form ref="formRef" :model="form" :rules="rules" label-width="100px" label-position="top">
				<FormItem label="Config Key" prop="config_key" tooltipKey="config_key">
					<el-input v-model="form.config_key" placeholder="Please enter config key" />
				</FormItem>
				<FormItem label="Usage Type" prop="use_type" tooltipKey="use_type">
					<el-select v-model="form.use_type">
						<el-option v-for="(value, key) in use_typeList" :key="key" :label="value" :value="key" />
					</el-select>
				</FormItem>
				<FormItem label="Field Type" prop="item_type" tooltipKey="item_type">
					<el-select v-model="form.item_type" @change="changeType">
						<el-option v-for="(value, key) in itemTypeList" :key="key" :label="value" :value="key" />
					</el-select>
				</FormItem>
				<FormItem label="Config Value" prop="config_value" tooltipKey="config_value">
					<div v-if="form.config_key === 'LLM_CONFIG'" style="width: 100%">
						<el-select style="width: 100%" v-model="form.config_value" placeholder="Please enter config value">
							<el-option
								v-for="provider in providers"
								:key="provider.id"
								:label="provider.provider_name"
								:value="provider.provider_name"
							/>
						</el-select>
					</div>
					<div v-else style="width: 100%">
						<el-input v-model="form.config_value" placeholder="Please enter config value" v-if="form.item_type === 'string'" />
						<el-input
							show-password
							type="password"
							v-model="form.config_value"
							placeholder="Please enter config value"
							v-else-if="form.item_type === 'password'"
						/>
						<el-input-number
							v-model="form.config_value"
							placeholder="Please enter config value"
							v-else-if="form.item_type === 'number'"
						/>
						<ModelCascader
							v-else-if="form.item_type === 'model'"
							v-model="form.config_value"
							style="width: 100%"
							class="model-task"
						/>
						<div v-else-if="form.item_type === 'json_object'" style="width: 100%">
							<div class="json-object">
								<div v-for="(value, key) in jsonObjectData" :key="key" class="json-property">
									<el-input
										v-model="jsonObjectKeys[key]"
										placeholder="Key name"
										class="key-input"
										@change="updateJsonObjectKey(key, jsonObjectKeys[key])"
									/>
									<el-input v-model="jsonObjectData[key]" placeholder="Value" class="value-input" />
									<el-button type="danger" size="small" @click="removeJsonObjectProperty(key)">
										<el-icon>
											<Delete />
										</el-icon>
									</el-button>
								</div>
								<div class="json-add-property">
									<el-button type="primary" size="small" @click="addJsonObjectProperty">
										<el-icon>
											<Plus />
										</el-icon>
										Add Property
									</el-button>
								</div>
							</div>
						</div>
						<div v-else-if="form.item_type === 'json_array'" style="width: 100%">
							<div v-for="(item, index) of json_object" :key="index" class="json-item">
								<div class="json-header">
									<span>Object #{{ index + 1 }}</span>
									<el-button type="danger" size="small" @click="removeJsonItem(index)">
										<el-icon>
											<Delete />
										</el-icon>
									</el-button>
								</div>
								<div v-for="(value, key) in item" :key="key" class="json-property">
									<el-input
										v-model="jsonKeys[index][key]"
										placeholder="Key name"
										class="key-input"
										@change="updateJsonKey(index, key, jsonKeys[index][key])"
									/>
									<el-input v-model="item[key]" placeholder="Value" class="value-input" />
									<el-button type="danger" size="small" @click="removeJsonProperty(index, key)">
										<el-icon>
											<Delete />
										</el-icon>
									</el-button>
								</div>
								<div class="json-add-property">
									<el-button type="primary" size="small" @click="addJsonProperty(index)">
										<el-icon>
											<Plus />
										</el-icon>
										Add Property
									</el-button>
								</div>
							</div>
							<div class="json-actions">
								<el-button type="primary" @click="addJsonItem">
									<el-icon>
										<Plus />
									</el-icon>
									Add Object
								</el-button>
							</div>
						</div>
					</div>
				</FormItem>
				<FormItem label="Description" prop="description" tooltipKey="description">
					<el-input v-model="form.description" type="textarea" placeholder="Please enter description" />
				</FormItem>
			</el-form>
			<template #footer>
				<span class="dialog-footer">
					<el-button @click="dialogVisible = false">Cancel</el-button>
					<el-button type="primary" @click="handleSubmit">Confirm</el-button>
				</span>
			</template>
		</el-dialog>
	</div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Plus, Search, Edit, Delete } from "@element-plus/icons-vue";
import type { FormInstance } from "element-plus";
import { getSystemConfigList, createSystemConfig, updateSystemConfig, deleteSystemConfig } from "@/api/system";
import { getLLMProviderList } from "@/api/llm";
import type { LLMProvider } from "@/types/llm";
import { formatDate } from "@/utils";
import ModelCascader from "@/components/ModelCascader.vue";

interface SystemConfig {
	id: number;
	config_key: string;
	config_value: string;
	description: string;
	create_time: string;
	update_time: string;
	item_type: string;
	use_type: string;
}

interface FormData {
	id?: number;
	config_key: string;
	config_value: any;
	description: string;
	item_type: string;
	use_type: string;
}

// Data list
const loading = ref(false);
const tableData = ref<Record<string, SystemConfig[]>>({});
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(10);
const searchQuery = ref("");
const providers = ref<LLMProvider[]>([]);
// Form related
const dialogVisible = ref(false);
const dialogType = ref<"add" | "edit">("add");
const formRef = ref<FormInstance>();
const form = reactive<FormData>({
	config_key: "",
	config_value: "",
	description: "",
	item_type: "string",
	use_type: "system",
});

const tabsValue = ref("game");

const rules = {
	config_key: [{ required: true, message: "Please enter config key", trigger: "blur" }],
	config_value: [{ required: true, message: "Please enter config value", trigger: "blur" }],
	description: [{ required: true, message: "Please enter description", trigger: "blur" }],
};
const fetchProviders = async () => {
	try {
		// Try to call API to get data
		const response = await getLLMProviderList({ skip: 0, limit: 100 });
		providers.value = response;
	} catch (error) {
		console.error("Failed to get LLM provider list", error);
		ElMessage.error("Failed to get LLM provider list, showing mock data");
	}
};
// Format config value
const formatConfigValue = (value: string): string => {
	if (value.length > 20) {
		return `${value.substring(0, 4)}***${value.substring(value.length - 4)}`;
	}
	return value;
};

// Get list data
const getList = async (): Promise<void> => {
	loading.value = true;
	try {
		const params = {
			skip: (currentPage.value - 1) * pageSize.value,
			limit: pageSize.value,
			keyword: searchQuery.value,
		};
		const res = await getSystemConfigList(params);
		tableData.value = res;
		total.value = res.length;
	} catch (error) {
		console.error("Failed to get system configuration list:", error);
	} finally {
		loading.value = false;
	}
};

// Search
const handleSearch = (): void => {
	currentPage.value = 1;
	getList();
};

// Pagination
const handleSizeChange = (val: number): void => {
	pageSize.value = val;
	getList();
};

const handleCurrentChange = (val: number): void => {
	currentPage.value = val;
	getList();
};

// Add
const handleAdd = (): void => {
	dialogType.value = "add";
	form.id = undefined;
	form.config_key = "";
	form.config_value = "";
	form.description = "";
	form.item_type = "string";
	form.use_type = "system";
	dialogVisible.value = true;
};

// Edit
const handleEdit = (row: SystemConfig): void => {
	dialogType.value = "edit";
	form.id = row.id;
	form.config_key = row.config_key;
	form.config_value = row.config_value;
	form.description = row.description;
	form.item_type = row.item_type;
	form.use_type = row.use_type;
	dialogVisible.value = true;
	changeType(row.item_type);
	if (row.config_key === "LLM_CONFIG") {
		fetchProviders().then(() => {
			// form.config_value=response[0].provider_name;
		});
	}
};

// Delete
const handleDelete = (row: SystemConfig): void => {
	ElMessageBox.confirm("Are you sure you want to delete this configuration?", "Prompt", {
		type: "warning",
	}).then(async () => {
		try {
			await deleteSystemConfig(row.id);
			ElMessage.success("Delete successful");
			getList();
		} catch (error) {
			console.error("Failed to delete system configuration:", error);
		}
	});
};

// Submit form
const handleSubmit = async (): Promise<void> => {
	if (!formRef.value) return;

	// Ensure JSON content is updated to form.config_value before submission
	if (form.item_type === "json_array") {
		updateFormValue();
	} else if (form.item_type === "json_object") {
		updateJsonObjectFormValue();
	} else {
		form.config_value = form.config_value.toString();
	}

	await formRef.value.validate(async (valid) => {
		if (valid) {
			try {
				if (dialogType.value === "add") {
					await createSystemConfig(form);
					ElMessage.success("Add successful");
				} else if (form.id) {
					await updateSystemConfig(form.id, form);
					ElMessage.success("Update successful");
				}
				dialogVisible.value = false;
				getList();
			} catch (error) {
				console.error("Failed to submit system configuration:", error);
			}
		}
	});
};

onMounted(() => {
	getList();
});

const json_object = ref<any[]>([]);
const jsonKeys = ref<any[]>([]);

// JSON editor related methods
/**
 * Add a new JSON object to the array
 */
function addJsonItem(): void {
	const newItem = {};
	json_object.value.push(newItem);
	jsonKeys.value.push({});
	updateFormValue();
}

/**
 * Remove an object from the JSON array
 * @param {number} index - Index of the object to remove
 */
function removeJsonItem(index: number): void {
	json_object.value.splice(index, 1);
	jsonKeys.value.splice(index, 1);
	updateFormValue();
}

/**
 * Add a new property to the specified JSON object
 * @param {number} index - Index of the object in the array
 */
function addJsonProperty(index: number): void {
	const newKey = `property_${Object.keys(json_object.value[index]).length + 1}`;
	json_object.value[index][newKey] = "";
	jsonKeys.value[index][newKey] = newKey;
	updateFormValue();
}

/**
 * Delete a property from a JSON object
 * @param {number} index - Object index
 * @param {string} key - Property key name to delete
 */
function removeJsonProperty(index: number, key: any): void {
	delete json_object.value[index][key];
	delete jsonKeys.value[index][key];
	updateFormValue();
}

/**
 * Update JSON object's key name
 * @param {number} index - Object index
 * @param {string} oldKey - Old key name
 * @param {string} newKey - New key name
 */
function updateJsonKey(index: number, oldKey: any, newKey: any): void {
	if (oldKey === newKey) return;

	const value = json_object.value[index][oldKey];
	delete json_object.value[index][oldKey];
	json_object.value[index][newKey] = value;

	delete jsonKeys.value[index][oldKey];
	jsonKeys.value[index][newKey] = newKey;

	updateFormValue();
}

/**
 * Update form config_value
 */
function updateFormValue(): void {
	form.config_value = JSON.stringify(json_object.value);
}

function changeType(type: string): void {
	if (type === "json_object") {
		try {
			jsonObjectData.value = JSON.parse(form.config_value || "{}");
			// Initialize jsonObjectKeys to track each key name
			jsonObjectKeys.value = {};
			Object.keys(jsonObjectData.value).forEach((key) => {
				jsonObjectKeys.value[key] = key;
			});
		} catch (error) {
			console.log("Conversion error");
			ElMessage.info("This field is not a JSON object");
			form.item_type = "string";
		}
	} else if (type === "json_array") {
		try {
			json_object.value = JSON.parse(form.config_value || "[]");
			// Initialize jsonKeys to track each object's key names
			jsonKeys.value = json_object.value.map((item) => {
				const keys = {};
				Object.keys(item).forEach((key) => {
					keys[key] = key;
				});
				return keys;
			});
		} catch (error) {
			console.log("Conversion error");
			ElMessage.info("This field is not a JSON array");
			form.item_type = "string";
		}
	}
}

const jsonObjectData = ref<Record<string, any>>({});
const jsonObjectKeys = ref<Record<string, string>>({});

/**
 * Add a new property to the JSON object
 */
function addJsonObjectProperty(): void {
	const newKey = `property_${Object.keys(jsonObjectData.value).length + 1}`;
	jsonObjectData.value[newKey] = "";
	jsonObjectKeys.value[newKey] = newKey;
	updateJsonObjectFormValue();
}

/**
 * Delete a property from the JSON object
 * @param {string} key - Property key name to delete
 */
function removeJsonObjectProperty(key: string): void {
	delete jsonObjectData.value[key];
	delete jsonObjectKeys.value[key];
	updateJsonObjectFormValue();
}

/**
 * Update JSON object's key name
 * @param {string} oldKey - Old key name
 * @param {string} newKey - New key name
 */
function updateJsonObjectKey(oldKey: string, newKey: string): void {
	if (oldKey === newKey) return;

	const value = jsonObjectData.value[oldKey];
	delete jsonObjectData.value[oldKey];
	jsonObjectData.value[newKey] = value;

	delete jsonObjectKeys.value[oldKey];
	jsonObjectKeys.value[newKey] = newKey;

	updateJsonObjectFormValue();
}

/**
 * Update form config_value
 */
function updateJsonObjectFormValue(): void {
	form.config_value = JSON.stringify(jsonObjectData.value);
}

const use_typeList = {
	system: "System",
	game: "Game",
	secretKey: "Secret Key",
	web_config: "Web Config",
};

const itemTypeList = {
	string: "Regular Type",
	number: "Number",
	password: "Password",
	json_object: "JSON Object",
	json_array: "JSON Array",
	special: "Special Config",
	model: "Large Model",
};
</script>

<style lang="scss" scoped>
.system-config {
	padding: 20px;
	background-color: #f5f6fa;
	min-height: 100%;

	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 20px;

		.title {
			font-size: 24px;
			color: #2c3e50;
			margin: 0;
		}
	}

	.search-box {
		margin-bottom: 20px;

		.search-input {
			width: 300px;
		}
	}

	.pagination {
		margin-top: 20px;
		display: flex;
		justify-content: flex-end;
	}

	.json-item {
		margin-bottom: 15px;
		padding: 15px;
		border: 1px solid #dcdfe6;
		border-radius: 4px;
		background-color: #f8f9fa;
	}

	.json-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 10px;
		font-weight: bold;
	}

	.json-property {
		display: flex;
		align-items: center;
		margin-bottom: 8px;
		gap: 8px;

		.key-input {
			width: 40%;
		}

		.value-input {
			width: 40%;
		}
	}

	.json-add-property {
		margin-top: 10px;
	}

	.json-actions {
		margin-top: 15px;
	}

	.json-object {
		margin-bottom: 15px;
		padding: 15px;
		border: 1px solid #dcdfe6;
		border-radius: 4px;
		background-color: #f8f9fa;
	}
}
</style>
