<script setup lang="ts">
import Result from "@/components/Result/index.vue";
</script>

<template>
	<Result status="success" title="Operation Successful" subtitle="Success result page is used to provide feedback on the results of a series of operational tasks">
		<template #extra>
			<el-button type="primary"> Back to List </el-button>
			<el-button> View Details </el-button>
		</template>
	</Result>
</template>
