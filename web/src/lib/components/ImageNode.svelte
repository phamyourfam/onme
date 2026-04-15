<script lang="ts">
	import { Handle, Position } from '@xyflow/svelte';

	let { data } = $props<{
		data: {
			label?: string;
			imageUrl?: string;
			width?: number;
			height?: number;
		};
	}>();
</script>

<div class="image-node group relative overflow-hidden rounded-2xl border border-white/10 bg-surface-card shadow-gestalt transition-shadow hover:shadow-gestalt-hover">
	{#if data?.imageUrl}
		<img
			src={data.imageUrl}
			alt={data.label ?? 'Image'}
			class="block w-full object-cover"
			style="max-width: {data.width ?? 200}px; max-height: {data.height ?? 260}px;"
			draggable="false"
		/>
	{:else}
		<div
			class="flex items-center justify-center bg-surface-hover text-pin-medium-gray"
			style="width: {data?.width ?? 200}px; height: {data?.height ?? 150}px;"
		>
			<svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0 0 22.5 18.75V5.25A2.25 2.25 0 0 0 20.25 3H3.75A2.25 2.25 0 0 0 1.5 5.25v13.5A2.25 2.25 0 0 0 3.75 21Z" />
			</svg>
		</div>
	{/if}

	{#if data?.label}
		<div class="border-t border-white/5 bg-surface-card/90 px-3 py-2 text-xs font-medium text-pin-medium-gray backdrop-blur-sm">
			{data.label}
		</div>
	{/if}

	<Handle type="target" position={Position.Left} class="!bg-pin-red !border-none !w-3 !h-3" />
	<Handle type="source" position={Position.Right} class="!bg-pin-red !border-none !w-3 !h-3" />
</div>

<style>
	.image-node {
		min-width: 120px;
	}
</style>
