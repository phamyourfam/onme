<script lang="ts">
	import { Handle, Position } from '@xyflow/svelte';
	import type { NodeProps, Node } from '@xyflow/svelte';
	import type { PipelineNodeData } from '$lib/types';

	type ImageNodeType = Node<PipelineNodeData, 'imageNode'>;
	type $$Props = NodeProps<ImageNodeType>;

	let { data }: $$Props = $props();

	const borderColour: Record<PipelineNodeData['status'], string> = {
		idle: 'border-gray-300',
		processing: 'border-amber-400',
		complete: 'border-emerald-500',
		failed: 'border-red-500'
	};
</script>

<div
	class="rounded-lg border-2 bg-white p-2 shadow-sm {borderColour[data.status]}"
	class:animate-pulse={data.status === 'processing'}
>
	<p class="text-xs font-bold mb-1">{data.label}</p>

	{#if data.imageUrl}
		<img
			src={data.imageUrl}
			alt={data.label}
			class="w-24 h-24 object-cover rounded"
		/>
	{:else if data.status === 'processing'}
		<div class="w-24 h-24 rounded bg-gray-200 animate-pulse"></div>
	{:else}
		<div class="w-24 h-24 rounded bg-gray-100 flex items-center justify-center">
			<span class="text-[10px] text-gray-400">No image</span>
		</div>
	{/if}

	{#if data.elapsedMs != null}
		<p class="text-[10px] text-gray-500 mt-1">{data.elapsedMs}ms</p>
	{/if}

	<Handle type="target" position={Position.Left} />
	<Handle type="source" position={Position.Right} />
</div>
