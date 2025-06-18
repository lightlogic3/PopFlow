<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { getRagSessions, deleteRagSession, createChatSession } from "@/api/chat";

const router = useRouter();
const loading = ref(false);
const sessions = ref([]);

// 获取会话列表
const fetchSessions = async () => {
	loading.value = true;
	try {
		const response = await getRagSessions();
		if (response) {
			sessions.value = response;
		}
	} catch (error) {
		console.error("获取会话列表失败", error);
		ElMessage.error("获取会话列表失败");
	} finally {
		loading.value = false;
	}
};

// 打开会话
const openSession = (sessionId) => {
	router.push({
		path: "/chat/chat",
		query: { sessionId },
	});
};

// 创建新会话
const createNewChat = () => {
	createChatSession({
		user_id: "admin",
		session_name: "admin会话测试",
	}).then((res) => {
		router.push("/chat/chat?session_id=" + res.session_id);
	});
};

// 删除会话
const deleteSession = (sessionId) => {
	ElMessageBox.confirm("确定要删除该聊天会话吗？", "提示", {
		confirmButtonText: "确定",
		cancelButtonText: "取消",
		type: "warning",
	})
		.then(async () => {
			try {
				await deleteRagSession(sessionId);
				ElMessage.success("删除成功");
				// 刷新会话列表
				fetchSessions();
			} catch (error) {
				console.error("删除失败", error);
				ElMessage.error("删除失败");
			}
		})
		.catch(() => {
			// 用户取消操作
		});
};

// 格式化日期时间
const formatDate = (dateStr) => {
	if (!dateStr) return "";

	// 如果已经是格式化好的日期字符串，直接返回
	if (dateStr.includes("-") && dateStr.includes(":")) {
		return dateStr;
	}

	try {
		const date = new Date(dateStr);
		return date.toLocaleString("zh-CN", {
			year: "numeric",
			month: "2-digit",
			day: "2-digit",
			hour: "2-digit",
			minute: "2-digit",
		});
	} catch (e) {
		return dateStr;
	}
};

onMounted(() => {
	fetchSessions();
});
</script>

<template>
	<div class="chat-list-container">
		<div class="header">
			<h1 class="title">聊天会话列表</h1>
			<el-button type="primary" @click="createNewChat">
				<el-icon>
					<Plus />
				</el-icon>
				新建会话
			</el-button>
		</div>

		<div class="session-list" v-loading="loading">
			<el-empty v-if="sessions.length === 0" description="暂无聊天会话" />

			<el-card
				v-for="session in sessions"
				:key="session.session_id"
				class="session-card"
				shadow="hover"
				@click="openSession(session.session_id)"
			>
				<div class="session-header">
					<h3 class="session-title">
						{{ session.session_name }}
					</h3>
					<div class="session-actions">
						<el-button type="danger" size="small" circle @click.stop="deleteSession(session.session_id)">
							<el-icon>
								<Delete />
							</el-icon>
						</el-button>
					</div>
				</div>

				<div class="session-info">
					<!--					<div class="info-item">-->
					<!--						<span class="info-label">记忆类型</span>-->
					<!--						<el-tag size="small">{{ session.memory_type }}</el-tag>-->
					<!--					</div>-->
					<div class="info-item">
						<span class="info-label">消息数量</span>
						<span>{{ session.message_count || 0 }}</span>
					</div>
					<div class="info-item">
						<span class="info-label">创建时间</span>
						<span>{{ formatDate(session.created_at) }}</span>
					</div>
				</div>
			</el-card>
		</div>

		<el-pagination
			v-if="sessions.length > 0"
			class="pagination"
			:total="sessions.length"
			:page-size="10"
			layout="total, prev, pager, next"
		/>
	</div>
</template>

<style scoped>
.chat-list-container {
	padding: 20px;
}

.header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 20px;
}

.title {
	font-size: 24px;
	margin: 0;
}

.session-list {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
	gap: 20px;
	margin-bottom: 20px;
}

.session-card {
	cursor: pointer;
	height: 100%;
	transition: transform 0.2s;
}

.session-card:hover {
	transform: translateY(-5px);
}

.session-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 15px;
}

.session-title {
	margin: 0;
	font-size: 16px;
	font-weight: 600;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

.session-actions {
	flex-shrink: 0;
}

.session-info {
	border-top: 1px solid var(--el-border-color-lighter);
	padding-top: 10px;
}

.info-item {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 8px;
	font-size: 14px;
}

.info-label {
	color: var(--el-text-color-secondary);
}

.pagination {
	display: flex;
	justify-content: center;
	margin-top: 20px;
}
</style>
