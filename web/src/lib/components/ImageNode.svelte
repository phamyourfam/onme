<script lang="ts">
	import { Handle, Position, type NodeProps, NodeResizer, NodeToolbar } from '@xyflow/svelte';
	import { useSvelteFlow } from '@xyflow/svelte';
	import { deleteMoodboardNode } from '$lib/api';

	let { id, data, selected }: NodeProps = $props();

	const { deleteElements } = useSvelteFlow();

	async function handleDelete() {
		// Try deleting from backend first
		try {
			if (data.moodboardId) {
				await deleteMoodboardNode(data.moodboardId as string, id);
			}
			deleteElements({ nodes: [{ id }] });
		} catch (e) {
			console.error('Failed to delete node', e);
		}
	}
</script>

<NodeToolbar isVisible={selected} position={Position.Top} class="rounded-full border border-white/10 bg-surface-card px-2 py-1 flex gap-1 shadow-gestalt">
	<button
		onclick={handleDelete}
		class="rounded-full p-2 text-pin-medium-gray hover:bg-pin-red hover:text-white transition-colors flex items-center justify-center pointer-events-auto"
		title="Delete"
	>
		<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
			<path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
		</svg>
	</button>
</NodeToolbar>

<div class="image-node group relative overflow-hidden rounded-2xl border border-white/10 bg-surface-card shadow-gestalt transition-shadow hover:shadow-gestalt-hover {selected ? 'ring-2 ring-pin-red' : ''}">
	<NodeResizer isVisible={selected} minWidth={100} minHeight={100} />
	{#if data?.imageUrl}
		<img
			src={data.imageUrl as string}
			alt={(data.label as string) ?? 'Image'}
			class="block w-full h-full object-cover"
			style="width: 100%; height: 100%;"
			draggable="false"
		/>
	{:else}
		<div
			class="flex items-center justify-center bg-surface-hover text-pin-medium-gray w-full h-full"
		>
			<svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0 0 22.5 18.75V5.25A2.25 2.25 0 0 0 20.25 3H3.75A2.25 2.25 0 0 0 1.5 5.25v13.5A2.25 2.25 0 0 0 3.75 21Z" />
			</svg>
		</div>
	{/if}

	{#if data?.label}
		<div class="absolute bottom-0 left-0 right-0 border-t border-white/5 bg-surface-card/90 px-3 py-2 text-xs font-medium text-pin-medium-gray backdrop-blur-sm">
			{data.label}
		</div>
	{/if}

	<Handle type="target" position={Position.Left} class="!bg-pin-red !border-none !w-3 !h-3" />
	<Handle type="source" position={Position.Right} class="!bg-pin-red !border-none !w-3 !h-3" />
</div>

<style>
	.image-node {
		min-width: 120px;
		width: 100%;
		height: 100%;
	}
</style>
