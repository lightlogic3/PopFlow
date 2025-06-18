<script lang="ts">
export default {
	name: "Home",
};
</script>
<script setup lang="ts"></script>

<template>
	<div>
		<!-- <el-empty description="Hello World ~(´•ω•̥` )" /> -->
		<div class="big-background"></div>
	</div>
</template>

<style scoped lang="scss">
	.big-background {
		width: 100%;
		height: 1000px;
		background-image: url('../../assets/big-ground.jpg');
		background-repeat: no-repeat;
		background-size: contain;
	}
</style>
