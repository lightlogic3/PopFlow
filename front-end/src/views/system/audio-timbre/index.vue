<template>
	<div class="audio-timbre">
		<div class="header">
			<h1 class="title">Voice Timbre Management</h1>
			<el-button type="primary" @click="handleAdd" :disabled="disabled"> Sync Voice </el-button>
		</div>

		<div class="search-box">
			<el-select v-model="stateFilter" placeholder="Filter by status" clearable @change="handleSearch" class="filter-select">
				<el-option label="All" value="" />
				<el-option label="Active" value="active" />
				<el-option label="Inactive" value="inactive" />
			</el-select>
		</div>

		<el-table v-loading="loading" :data="tableData" style="width: 100%" border>
			<el-table-column prop="alias" label="Alias" min-width="120" />
			<el-table-column prop="speaker_id" label="Voice ID" min-width="150" />
			<el-table-column prop="version" label="Training Version" width="120" />
			<el-table-column prop="expire_time" label="Expiration Time" width="180">
				<template #default="scope">
					<div
						:style="{
							color: isWithinThreshold(scope.row.expire_time, 2) ? '#e45c5c' : '#e4bb5c',
						}"
						class="text-align-center"
					>
						{{ formatDate(scope.row.expire_time) }}
						<el-tooltip
							content="About to expire, needs to be handled at Volcano Engine"
							v-if="isWithinThreshold(scope.row.expire_time, 2)"
							placement="top"
						>
							<el-icon style="margin-left: 5px"><InfoFilled /></el-icon>
						</el-tooltip>
					</div>
				</template>
			</el-table-column>
			<el-table-column prop="state" label="Status" width="100">
				<template #default="{ row }">
					<el-tag :type="row.state === 'active' ? 'success' : 'danger'">
						{{ row.state === "active" ? "Active" : "Inactive" }}
					</el-tag>
				</template>
			</el-table-column>
			<el-table-column label="Listen" width="120">
				<template #default="{ row }">
					<el-button v-if="row.audition" type="primary" link @click="handleAudition(row)">
						<el-icon><Headset /></el-icon>
						Listen
					</el-button>
					<span v-else>No Audio</span>
				</template>
			</el-table-column>
			<el-table-column
				prop="create_time"
				label="Creation Time"
				width="180"
				:formatter="(row: any, column: any, cellValue: any)=>formatDate(cellValue)"
			/>
			<el-table-column
				prop="update_time"
				label="Update Time"
				width="180"
				:formatter="(row: any, column: any, cellValue: any)=>formatDate(cellValue)"
			/>
			<el-table-column label="Actions" width="150" fixed="right">
				<template #default="{ row }">
					<el-button-group>
						<!--						<el-button type="primary" link @click="handleEdit(row)">-->
						<!--							<el-icon><Edit /></el-icon>-->
						<!--							Edit-->
						<!--						</el-button>-->
						<el-button type="danger" link @click="handleDelete(row)">
							<el-icon><Delete /></el-icon>
							Delete
						</el-button>
					</el-button-group>
				</template>
			</el-table-column>
		</el-table>

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
		<el-dialog v-model="dialogVisible" :title="dialogType === 'add' ? 'Add Voice Timbre' : 'Edit Voice Timbre'" width="600px">
			<el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
				<FormItem label="Alias" prop="alias" tooltipKey="alias">
					<el-input v-model="form.alias" placeholder="Please enter alias" />
				</FormItem>
				<FormItem label="Voice ID" prop="speaker_id" tooltipKey="speaker_id">
					<el-input v-model="form.speaker_id" placeholder="Please enter voice ID" />
				</FormItem>
				<FormItem label="Training Version" prop="version" tooltipKey="version">
					<el-input v-model="form.version" placeholder="Please enter training version" />
				</FormItem>
				<FormItem label="Expiration Time" prop="expire_time" tooltipKey="expire_time">
					<el-date-picker
						v-model="form.expire_time"
						type="datetime"
						placeholder="Select expiration time"
						format="YYYY-MM-DD HH:mm:ss"
						value-format="YYYY-MM-DD HH:mm:ss"
						style="width: 100%"
					/>
				</FormItem>
				<FormItem label="Status" prop="state" tooltipKey="state">
					<el-select v-model="form.state" placeholder="Please select status" style="width: 100%">
						<el-option label="Active" value="active" />
						<el-option label="Inactive" value="inactive" />
					</el-select>
				</FormItem>
				<FormItem label="Listen" prop="audition" tooltipKey="audition">
					<el-button>Click to Listen</el-button>
				</FormItem>
			</el-form>
			<template #footer>
				<span class="dialog-footer">
					<el-button @click="dialogVisible = false">Cancel</el-button>
					<el-button type="primary" @click="handleSubmit">Confirm</el-button>
				</span>
			</template>
		</el-dialog>

		<!-- Audio Player Dialog -->
		<el-dialog v-model="auditionDialogVisible" title="Audio Playback" width="400px" center>
			<div class="audio-player-container">
				<audio v-if="currentAudition" :src="getAudioSrc(currentAudition)" controls autoplay></audio>
				<div v-else class="no-audio">No available audio</div>
			</div>
		</el-dialog>
	</div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Delete, Headset, InfoFilled } from "@element-plus/icons-vue";
import type { FormInstance } from "element-plus";
import { createAudioTimbre, updateAudioTimbre, deleteAudioTimbre, listAudioTimbres } from "@/api/audio-timbre";
import { getVoiceList } from "@/api/tts";
import { formatDate, isWithinThreshold } from "@/utils";

interface AudioTimbre {
	id: number;
	alias: string;
	speaker_id: string;
	version: string;
	expire_time: string;
	state: string;
	audition: string;
	create_time: string;
	craete_at: string;
	update_time: string;
	update_at: string;
}

interface FormData {
	id?: number;
	alias: string;
	speaker_id: string;
	version: string;
	expire_time: string;
	state: string;
	audition: string;
}

// Data list
const loading = ref(false);
const tableData = ref<AudioTimbre[]>([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(10);
const stateFilter = ref("");
const disabled = ref(false);
// Form related
const dialogVisible = ref(false);
const dialogType = ref<"add" | "edit">("add");
const formRef = ref<FormInstance>();
const form = reactive<FormData>({
	alias: "",
	speaker_id: "",
	version: "",
	expire_time: "",
	state: "active",
	audition: "",
});

// Audio playback related
const auditionDialogVisible = ref(false);
const currentAudition = ref("");

const rules = {
	alias: [{ required: true, message: "Please enter alias", trigger: "blur" }],
	speaker_id: [{ required: true, message: "Please enter voice ID", trigger: "blur" }],
	state: [{ required: true, message: "Please select status", trigger: "change" }],
};

// Convert Base64 to audio URL
const getAudioSrc = (base64: string): string => {
	if (!base64) return "";
	if (base64.startsWith("data:audio")) return base64;
	return `data:audio/mp3;base64,${base64}`;
};

// Get data list
const getList = async (): Promise<void> => {
	loading.value = true;
	try {
		const res = await listAudioTimbres();
		tableData.value = res;
		total.value = res.length;
	} catch (error) {
		console.error("Failed to get voice timbre list:", error);
		ElMessage.error("Failed to get voice timbre list");
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
	disabled.value = true;
	getVoiceList({ sync_to_db: true }).then(() => {
		setTimeout(() => {
			getList();
			disabled.value = false;
		}, 2000);
	});
	// dialogType.value = "add";
	// form.id = undefined;
	// form.alias = "";
	// form.speaker_id = "";
	// form.version = "";
	// form.expire_time = "";
	// form.state = "active";
	// form.audition = "";
	// dialogVisible.value = true;
};

// Edit
// const handleEdit = (row: AudioTimbre): void => {
// 	dialogType.value = "edit";
// 	form.id = row.id;
// 	form.alias = row.alias;
// 	form.speaker_id = row.speaker_id;
// 	form.version = row.version;
// 	form.expire_time = row.expire_time;
// 	form.state = row.state;
// 	form.audition = row.audition;
// 	dialogVisible.value = true;
// };

// Delete
const handleDelete = (row: AudioTimbre): void => {
	ElMessageBox.confirm("Are you sure you want to delete this voice timbre?", "Prompt", {
		type: "warning",
	}).then(async () => {
		try {
			await deleteAudioTimbre(row.id);
			ElMessage.success("Delete successful");
			getList();
		} catch (error) {
			console.error("Failed to delete voice timbre:", error);
			ElMessage.error("Failed to delete voice timbre");
		}
	});
};

// Listen
const handleAudition = (row: AudioTimbre): void => {
	currentAudition.value = row.audition;
	auditionDialogVisible.value = true;
};

// Submit form
const handleSubmit = async (): Promise<void> => {
	if (!formRef.value) return;

	await formRef.value.validate(async (valid) => {
		if (valid) {
			try {
				if (dialogType.value === "add") {
					await createAudioTimbre({
						...form,
						craete_at: "admin", // Example, should actually be obtained from user information
					});
					ElMessage.success("Add successful");
				} else if (form.id) {
					await updateAudioTimbre(form.id, {
						...form,
						update_at: "admin", // Example, should actually be obtained from user information
					});
					ElMessage.success("Update successful");
				}
				dialogVisible.value = false;
				getList();
			} catch (error) {
				console.error("Failed to submit voice timbre:", error);
				ElMessage.error("Operation failed");
			}
		}
	});
};

onMounted(() => {
	getList();
});
</script>

<style lang="scss" scoped>
.audio-timbre {
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
		display: flex;
		gap: 10px;

		.filter-select {
			width: 200px;
		}
	}

	.pagination {
		margin-top: 20px;
		display: flex;
		justify-content: flex-end;
	}

	.audio-uploader {
		width: 100%;
	}

	.audio-preview {
		margin-top: 10px;

		audio {
			width: 100%;
		}
	}

	.audio-player-container {
		display: flex;
		justify-content: center;
		padding: 20px 0;

		audio {
			width: 100%;
		}

		.no-audio {
			color: #999;
			font-size: 16px;
		}
	}
}
</style>
