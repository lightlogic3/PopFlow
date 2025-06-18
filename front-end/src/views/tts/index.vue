<template>
  <div class="tts-container">
    <div class="header">
      <h1 class="title">文本转语音</h1>
      <div class="actions">
        <el-button type="primary" @click="handleSyncVoices">
          <el-icon><Refresh /></el-icon>
          同步音色
        </el-button>
      </div>
    </div>

    <el-card class="tts-card">
      <div class="tts-form">
        <div class="voice-selector">
          <div class="selector-label">选择音色：</div>
          <el-select v-model="formData.speaker_id" placeholder="请选择音色" style="width: 100%">
            <el-option
                v-for="voice in voiceList"
                :key="voice.speaker_id"
                :label="voice.alias || voice.speaker_id"
                :value="voice.speaker_id"
                :disabled="voice.state !== 'active'"
            >
              <div class="voice-option">
                <span>{{ voice.alias || voice.speaker_id }}</span>
                <el-tag size="small" :type="voice.state === 'active' ? 'success' : 'danger'">
                  {{ voice.state === "active" ? "可用" : "不可用" }}
                </el-tag>
              </div>
            </el-option>
          </el-select>
        </div>

        <div class="text-input">
          <div class="input-label">输入文本：</div>
          <el-input
              v-model="formData.text"
              type="textarea"
              :rows="5"
              placeholder="请输入要转换的文本..."
              maxlength="500"
              show-word-limit
          ></el-input>
        </div>

        <div class="voice-params">
          <div class="params-label">语音参数：</div>
          <div class="params-sliders">
            <div class="param-item">
              <span class="param-name">语速：</span>
              <el-slider
                  v-model="formData.speed_ratio"
                  :min="0.5"
                  :max="2.0"
                  :step="0.1"
                  show-input
                  :format-tooltip="(val) => `${val}x`"
              ></el-slider>
            </div>
            <div class="param-item">
              <span class="param-name">音量：</span>
              <el-slider
                  v-model="formData.volume_ratio"
                  :min="0.5"
                  :max="2.0"
                  :step="0.1"
                  show-input
                  :format-tooltip="(val) => `${val}x`"
              ></el-slider>
            </div>
            <div class="param-item">
              <span class="param-name">音调：</span>
              <el-slider
                  v-model="formData.pitch_ratio"
                  :min="0.5"
                  :max="2.0"
                  :step="0.1"
                  show-input
                  :format-tooltip="(val) => `${val}x`"
              ></el-slider>
            </div>
          </div>
        </div>

        <div class="form-actions">
          <el-button type="primary" @click="handleGenerateSpeech" :loading="generating" :disabled="!canGenerate">
            生成语音
          </el-button>
          <el-button @click="handleResetForm">重置</el-button>
        </div>
      </div>

      <div v-if="audioData" class="audio-result">
        <div class="result-header">
          <div class="result-title">生成结果</div>
          <div class="result-actions">
            <el-button type="primary" plain size="small" @click="handlePlay">
              <el-icon><VideoPlay /></el-icon>
              播放
            </el-button>
            <el-button type="success" plain size="small" @click="handleDownload">
              <el-icon><Download /></el-icon>
              下载
            </el-button>
          </div>
        </div>
        <div class="audio-player">
          <audio ref="audioPlayer" controls :src="audioSrc"></audio>
        </div>
      </div>
    </el-card>

    <el-card class="voice-list-card">
      <template #header>
        <div class="card-header">
          <span>音色管理</span>
          <el-button
              type="primary"
              plain
              size="small"
              @click="handleActivateSelected"
              :disabled="selectedVoices.length === 0"
          >
            激活选中
          </el-button>
        </div>
      </template>
      <el-table v-loading="loading" :data="allVoices" style="width: 100%" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="Name" label="名称" min-width="120" />
        <el-table-column prop="SpeakerID" label="音色ID" min-width="150" />
        <el-table-column prop="Version" label="版本" width="100" />
        <el-table-column prop="Status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.Status === 'AVAILABLE' ? 'success' : 'danger'">
              {{ getStatusText(row.Status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button
                  type="primary"
                  link
                  size="small"
                  @click="handleActivateSingle(row)"
                  :disabled="row.Status === 'AVAILABLE'"
              >
                激活
              </el-button>
              <el-button
                  type="primary"
                  link
                  size="small"
                  @click="handlePreviewVoice(row)"
                  :disabled="row.Status !== 'AVAILABLE'"
              >
                试听
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted, watch } from "vue";
import { ElMessage } from "element-plus";
import { Refresh, VideoPlay, Download } from "@element-plus/icons-vue";
import { textToSpeech, getVoiceList, activateVoices, syncVoices, playAudio, downloadAudio } from "@/api/tts";

interface FormData {
  text: string;
  speaker_id: string;
  speed_ratio: number;
  volume_ratio: number;
  pitch_ratio: number;
}

interface Voice {
  alias: string;
  speaker_id: string;
  state: string;
}

// 表单数据
const formData = ref<FormData>({
  text: "今天的阳光真好啊！感觉整个人都充满了活力呢。",
  speaker_id: "",
  speed_ratio: 1.0,
  volume_ratio: 1.0,
  pitch_ratio: 1.0,
});

// 音色列表
const voiceList = ref<Voice[]>([]);
const allVoices = ref<any[]>([]);
const loading = ref(false);
const generating = ref(false);
const audioData = ref("");
const audioSrc = computed(() => {
  if (!audioData.value) return "";
  return audioData.value.startsWith("data:audio") ? audioData.value : `data:audio/mp3;base64,${audioData.value}`;
});
const audioPlayer = ref<HTMLAudioElement | null>(null);
const selectedVoices = ref<any[]>([]);

// 计算属性：是否可以生成语音
const canGenerate = computed(() => {
  return formData.value.text && formData.value.speaker_id;
});

// 获取音色列表
const fetchVoiceList = async () => {
  try {
    const res = [];
    voiceList.value = res.map((item: any) => ({
      alias: item.alias,
      speaker_id: item.speaker_id,
      state: item.state,
    }));
  } catch (error) {
    console.error("获取音色列表失败:", error);
    ElMessage.error("获取音色列表失败");
  }
};

// 获取系统音色列表
const fetchAllVoices = async () => {
  loading.value = true;
  try {
    const res = await getVoiceList();
    if (res.success) {
      allVoices.value = res.voices || [];
    }
  } catch (error) {
    console.error("获取系统音色列表失败:", error);
    ElMessage.error("获取系统音色列表失败");
  } finally {
    loading.value = false;
  }
};

// 同步音色
const handleSyncVoices = async () => {
  loading.value = true;
  try {
    const res = await syncVoices();
    if (res.success) {
      ElMessage.success(`音色同步成功，共${res.total}个音色`);
      fetchVoiceList();
      fetchAllVoices();
    }
  } catch (error) {
    console.error("同步音色失败:", error);
    ElMessage.error("同步音色失败");
  } finally {
    loading.value = false;
  }
};

// 生成语音
const handleGenerateSpeech = async () => {
  if (!canGenerate.value) {
    ElMessage.warning("请选择音色并输入文本");
    return;
  }

  generating.value = true;
  try {
    const res = await textToSpeech({
      text: formData.value.text,
      speaker_id: formData.value.speaker_id,
      speed_ratio: formData.value.speed_ratio,
      volume_ratio: formData.value.volume_ratio,
      pitch_ratio: formData.value.pitch_ratio,
      save_file: true,
    });

    if (res.success) {
      audioData.value = res.audio_data;
      setTimeout(() => {
        if (audioPlayer.value) {
          audioPlayer.value.play();
        }
      }, 500);
      ElMessage.success("语音生成成功");
    } else {
      ElMessage.error(res.error || "语音生成失败");
    }
  } catch (error) {
    console.error("生成语音失败:", error);
    ElMessage.error("生成语音失败");
  } finally {
    generating.value = false;
  }
};

// 重置表单
const handleResetForm = () => {
  formData.value = {
    text: "",
    speaker_id: "",
    speed_ratio: 1.0,
    volume_ratio: 1.0,
    pitch_ratio: 1.0,
  };
  audioData.value = "";
};

// 播放音频
const handlePlay = () => {
  if (!audioData.value) return;

  if (audioPlayer.value) {
    audioPlayer.value.play();
  } else {
    playAudio(audioData.value);
  }
};

// 下载音频
const handleDownload = () => {
  if (!audioData.value) return;

  const fileName = `tts_${new Date().getTime()}.mp3`;
  downloadAudio(audioData.value, fileName);
};

// 选择音色变化
const handleSelectionChange = (selection: any[]) => {
  selectedVoices.value = selection;
};

// 激活选中音色
const handleActivateSelected = async () => {
  if (selectedVoices.value.length === 0) return;

  loading.value = true;
  try {
    const speakerIds = selectedVoices.value.map((item) => item.SpeakerID);
    const res = await activateVoices({ speaker_ids: speakerIds });

    if (res.success) {
      ElMessage.success(res.message || "音色激活成功");
      fetchAllVoices();
      fetchVoiceList();
    } else {
      ElMessage.error(res.error || "音色激活失败");
    }
  } catch (error) {
    console.error("激活音色失败:", error);
    ElMessage.error("激活音色失败");
  } finally {
    loading.value = false;
  }
};

// 激活单个音色
const handleActivateSingle = async (row: any) => {
  loading.value = true;
  try {
    const res = await activateVoices({ speaker_ids: [row.SpeakerID] });

    if (res.success) {
      ElMessage.success(res.message || "音色激活成功");
      fetchAllVoices();
      fetchVoiceList();
    } else {
      ElMessage.error(res.error || "音色激活失败");
    }
  } catch (error) {
    console.error("激活音色失败:", error);
    ElMessage.error("激活音色失败");
  } finally {
    loading.value = false;
  }
};

// 试听音色
const handlePreviewVoice = async (row: any) => {
  generating.value = true;
  try {
    const res = await textToSpeech({
      text: "您好，这是一段音色试听示例，感谢您的使用。",
      speaker_id: row.SpeakerID,
      speed_ratio: 1.0,
      volume_ratio: 1.0,
      pitch_ratio: 1.0,
    });

    if (res.success) {
      playAudio(res.audio_data);
    } else {
      ElMessage.error(res.error || "音色试听失败");
    }
  } catch (error) {
    console.error("音色试听失败:", error);
    ElMessage.error("音色试听失败");
  } finally {
    generating.value = false;
  }
};

// 获取状态文本
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    AVAILABLE: "可用",
    UNAVAILABLE: "不可用",
    TRAINING: "训练中",
  };
  return statusMap[status] || status;
};

// 监听音频元素
watch(
    () => audioPlayer.value,
    (newPlayer) => {
      if (newPlayer && audioSrc.value) {
        newPlayer.src = audioSrc.value;
      }
    },
);

onMounted(() => {
  fetchVoiceList();
  fetchAllVoices();
});
</script>

<style lang="scss" scoped>
.tts-container {
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

  .tts-card {
    margin-bottom: 20px;
  }

  .tts-form {
    .voice-selector,
    .text-input,
    .voice-params {
      margin-bottom: 20px;
    }

    .selector-label,
    .input-label,
    .params-label {
      font-weight: bold;
      margin-bottom: 8px;
    }

    .voice-option {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .params-sliders {
      display: flex;
      flex-direction: column;
      gap: 15px;
    }

    .param-item {
      display: flex;
      align-items: center;

      .param-name {
        width: 60px;
        flex-shrink: 0;
      }
    }

    .form-actions {
      display: flex;
      gap: 10px;
    }
  }

  .audio-result {
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid #eee;

    .result-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 15px;

      .result-title {
        font-weight: bold;
        font-size: 16px;
      }

      .result-actions {
        display: flex;
        gap: 10px;
      }
    }

    .audio-player {
      audio {
        width: 100%;
      }
    }
  }

  .voice-list-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
  }
}
</style>
