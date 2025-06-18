<template>
	<div class="game-types-container">
		<div class="header">
			<div class="title">Game Type Management</div>
		</div>

		<div class="filter-container">
			<div class="filter">
				<div class="filter-item m-r10">
					<el-input v-model="filter.name" placeholder="Search game types..." @input="filterGameTypes">
						<template #prefix>
							<el-icon><Search /></el-icon>
						</template>
					</el-input>
				</div>
				<div class="filter-item m-r10">
					<el-select v-model="filter.status" placeholder="Status" clearable @change="filterGameTypes">
						<el-option :label="'Enabled'" :value="1" />
						<el-option :label="'Disabled'" :value="0" />
					</el-select>
				</div>
			</div>
			<div class="filter-item m-r10">
				<el-button type="primary" @click="createNewGameType" class="create-btn">
					<el-icon><Plus /></el-icon>
					Create Game Type
				</el-button>
			</div>
		</div>

		<div class="game-types-grid" v-loading="loading">
			<el-empty v-if="filteredGameTypes.length === 0" description="No game types" class="empty-game-types" />

			<div
				v-for="(gameType, index) in filteredGameTypes"
				:key="index"
				class="game-type-card"
				:class="{ disabled: gameType.status === 0 }"
			>
				<div class="game-type-header">
					<h3 class="game-type-title">{{ gameType.name }}</h3>
					<el-tag size="small" :type="gameType.status === 1 ? 'success' : 'info'" effect="dark">
						{{ gameType.status === 1 ? "Enabled" : "Disabled" }}
					</el-tag>
				</div>

				<div class="game-type-description">
					{{ gameType.description || "No description" }}
				</div>

				<div class="game-type-details">
					<div class="detail-item" v-if="gameType.player_count">
						<el-icon><User /></el-icon>
						<span>Player Count: {{ gameType.player_count }}</span>
					</div>
					<div class="detail-item" v-if="gameType.version">
						<el-icon><Document /></el-icon>
						<span>Version: {{ gameType.version }}</span>
					</div>
				</div>

				<div class="game-type-meta">
					<div class="meta-date">
						<el-icon><Calendar /></el-icon>
						<span>Created at {{ formatDate(gameType.created_at) }}</span>
					</div>

					<div class="meta-status" v-if="gameType.status === 0">
						<el-icon><WarningFilled /></el-icon>
						<span>Disabled</span>
					</div>
				</div>

				<div class="game-type-actions">
					<el-tooltip content="Preview" placement="top">
						<el-button circle class="action-button preview-button" @click="previewGameType(gameType)">
							<el-icon><View /></el-icon>
						</el-button>
					</el-tooltip>
					<el-tooltip content="Edit" placement="top">
						<el-button circle class="action-button edit-button" @click="editGameType(gameType)">
							<el-icon><Edit /></el-icon>
						</el-button>
					</el-tooltip>
					<el-tooltip content="Delete" placement="top">
						<el-button circle class="action-button delete-button" @click="deleteGameType(gameType)">
							<el-icon><Delete /></el-icon>
						</el-button>
					</el-tooltip>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { Plus, Calendar, User, View, Edit, Delete, Search, WarningFilled, Document } from "@element-plus/icons-vue";
import { getGamePlayTypes, deleteGamePlayType } from "@/api/gamePlayType";
import { formatDate } from "@/utils";

const router = useRouter();
const loading = ref(false);
const gameTypes = ref([]);

// Filter
const filter = reactive({
	name: "",
	status: null,
});

// Filtered game types
const filteredGameTypes = computed(() => {
	return gameTypes.value.filter((gameType) => {
		// Name filter
		if (
			filter.name &&
			!gameType.name.toLowerCase().includes(filter.name.toLowerCase()) &&
			!gameType.description?.toLowerCase().includes(filter.name.toLowerCase())
		) {
			return false;
		}

		// Status filter
		if (filter.status !== null && gameType.status !== filter.status) {
			return false;
		}

		return true;
	});
});

// Load game type data
const loadGameTypes = async () => {
	loading.value = true;
	try {
		const response = await getGamePlayTypes({
			skip: 0,
			limit: 100,
		});

		// Check if there is data, use mock data if none
		if (response && response.length > 0) {
			gameTypes.value = response;
		} else {
			console.log("Using mock data - no data returned");
		}
	} catch (error) {
		console.error("Failed to load game type data, using mock data", error);
	} finally {
		loading.value = false;
	}
};

// Filter game types
const filterGameTypes = () => {
	// Filter logic is automatically handled by computed property
};

// Create new game type
const createNewGameType = () => {
	router.push("/game-play-types/create");
};

// Edit game type
const editGameType = (gameType) => {
	// Mock data does not support editing, show prompt
	if (gameType.id.toString().startsWith("mock-")) {
		ElMessage.warning("This is mock data, editing is not supported");
		return;
	}
	router.push(`/game-play-types/${gameType.id}/edit`);
};

// Preview game type
const previewGameType = (gameType) => {
	router.push({
		path: `/chat/tasks/test/${gameType.id}`,
		query: {
			source: "gamePlayType",
			gameType: gameType.game_play_type,
		},
	});
};

// Delete game type
const deleteGameType = (gameType) => {
	// Mock data does not support deletion, show prompt
	if (gameType.id.toString().startsWith("mock-")) {
		ElMessage.warning("This is mock data, deletion is not supported");
		return;
	}

	ElMessageBox.confirm(`Are you sure you want to delete game type "${gameType.name}"? This operation cannot be undone.`, "Delete Confirmation", {
		confirmButtonText: "Confirm",
		cancelButtonText: "Cancel",
		type: "warning",
	})
		.then(async () => {
			try {
				await deleteGamePlayType(gameType.id);
				ElMessage.success("Game type deleted");
				loadGameTypes(); // Reload game type list
			} catch (error) {
				console.error("Failed to delete game type", error);
				ElMessage.error("Failed to delete game type");
			}
		})
		.catch(() => {
			// User cancelled operation
		});
};

// Load data when component is mounted
onMounted(() => {
	loadGameTypes();
});
</script>

<style scoped lang="scss">
.game-types-container {
	min-height: 100vh;
	padding: 30px;
	background-color: #121212;
	background-image: linear-gradient(to bottom, rgba(30, 30, 30, 0.9), rgba(10, 10, 10, 0.95)),
		url("https://img.freepik.com/free-photo/abstract-futuristic-background-with-colorful-glowing-neon-lights_181624-34728.jpg");
	background-size: cover;
	background-position: center;
	background-attachment: fixed;
	color: #f0f0f0;
}

.header {
	margin-bottom: 30px;
}

.title {
	font-size: 24px;
	color: #e91e63;
	text-shadow: 0 0 15px rgba(233, 30, 99, 0.5);
	letter-spacing: 2px;
}

.create-btn {
	display: block;
	width: 200px;
	height: 48px;
	margin: 0 auto 30px;
	background: linear-gradient(45deg, #e91e63, #9c27b0);
	border: none;
	border-radius: 24px;
	box-shadow: 0 5px 15px rgba(233, 30, 99, 0.3);
	transition: all 0.3s ease;
}

.create-btn:hover {
	transform: translateY(-3px);
	box-shadow: 0 8px 20px rgba(233, 30, 99, 0.5);
}

.filter-container {
	display: flex;
	gap: 15px;
	margin-bottom: 30px;
	justify-content: space-between;
	.filter {
		display: flex;
	}
	.m-r10 {
		margin-right: 10px;
	}
}

.filter-item {
	width: 200px;
}

.game-types-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
	gap: 25px;
	margin-top: 30px;
}

.game-type-card {
	position: relative;
	background: rgba(40, 40, 50, 0.7);
	border-radius: 15px;
	padding: 25px;
	box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
	transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
	overflow: hidden;
	display: flex;
	flex-direction: column;
	border-top: 3px solid transparent;
}

.game-type-card:hover {
	transform: translateY(-10px);
	box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
	background: rgba(50, 50, 60, 0.8);
}

.game-type-card.disabled {
	opacity: 0.7;
	border-top-color: #f56c6c;
}

.game-type-header {
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
	margin-bottom: 15px;
	margin-top: 10px;
}

.game-type-title {
	font-size: 20px;
	color: #fff;
	margin: 0;
	font-weight: 600;
	display: -webkit-box;
	-webkit-line-clamp: 2;
	-webkit-box-orient: vertical;
	overflow: hidden;
}

.game-type-description {
	color: #bbb;
	font-size: 14px;
	line-height: 1.6;
	margin-bottom: 20px;
	flex-grow: 1;
	overflow: hidden;
	display: -webkit-box;
	-webkit-line-clamp: 3;
	-webkit-box-orient: vertical;
}

.game-type-details {
	display: flex;
	flex-wrap: wrap;
	margin-bottom: 15px;
	gap: 10px;
}

.detail-item {
	display: flex;
	align-items: center;
	gap: 5px;
	background-color: rgba(60, 60, 70, 0.6);
	padding: 5px 10px;
	border-radius: 15px;
	font-size: 12px;
	color: #ddd;
}

.game-type-meta {
	display: flex;
	justify-content: space-between;
	margin-bottom: 20px;
	color: #999;
	font-size: 12px;
}

.meta-date,
.meta-status {
	display: flex;
	align-items: center;
	gap: 5px;
}

.meta-status {
	color: #f56c6c;
}

.game-type-actions {
	display: flex;
	justify-content: center;
	gap: 15px;
}

.action-button {
	width: 45px;
	height: 45px;
	flex-shrink: 0;
	transition: all 0.3s ease;
}

.action-button:hover {
	transform: scale(1.15);
}

.preview-button {
	background: linear-gradient(45deg, #00bcd4, #2196f3);
	border: none;
	color: white;
}

.edit-button {
	background: linear-gradient(45deg, #9c27b0, #673ab7);
	border: none;
	color: white;
}

.delete-button {
	background: linear-gradient(45deg, #f56c6c, #ff9500);
	border: none;
	color: white;
}

.empty-game-types {
	grid-column: 1 / -1;
	color: #999;
	padding: 100px 0;
}

@media (max-width: 768px) {
	.game-types-container {
		padding: 20px;
	}

	.game-types-grid {
		grid-template-columns: 1fr;
	}

	.filter-container {
		flex-direction: column;
		align-items: center;
	}

	.filter-item {
		width: 100%;
	}
}
</style>
