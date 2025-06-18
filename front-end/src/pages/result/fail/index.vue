<script setup lang="ts">
import Result from "@/components/Result/index.vue";
</script>

<template>
	<Result status="error" title="Operation Failed" subtitle="Please check and modify the information before resubmitting.">
		<template #extra>
			<el-button type="primary"> Return to Modify </el-button>
			<el-button> Back to Home </el-button>
		</template>
	</Result>
</template>
