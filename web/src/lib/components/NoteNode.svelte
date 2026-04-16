<script lang="ts">
	import { useUpdateNodeInternals, type NodeProps, Handle, Position, NodeResizer, NodeToolbar } from '@xyflow/svelte';
	import { useSvelteFlow } from '@xyflow/svelte';
	import { deleteMoodboardNode } from '$lib/api';
	
	let { id, data, selected }: NodeProps = $props();
	
	const updateNodeInternals = useUpdateNodeInternals();
	const { deleteElements } = useSvelteFlow();

	function onChange(e: Event) {
		const target = e.target as HTMLTextAreaElement;
		data.text = target.value;
		updateNodeInternals(id);
	}

	async function handleDelete() {
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

<div
	class="relative min-h-[100px] min-w-[200px] h-full w-full overflow-hidden rounded-xl bg-[#fff8e1] shadow-md transition-shadow"
	class:ring-2={selected}
	class:ring-pin-red={selected}
>
	<NodeResizer isVisible={selected} minWidth={200} minHeight={100} />

	<!-- Custom top handle -->
	<Handle
		type="target"
		position={Position.Top}
		class="!h-3 !w-3 !border-2 !border-white !bg-pin-red"
	/>

	<textarea
		class="nodrag block h-full min-h-[100px] w-full resize-none bg-transparent p-4 text-sm text-gray-800 focus:outline-none"
		placeholder="Type your notes here..."
		value={data.text as string || ''}
		oninput={onChange}
	></textarea>

	<!-- Custom bottom handle -->
	<Handle
		type="source"
		position={Position.Bottom}
		class="!h-3 !w-3 !border-2 !border-white !bg-pin-red"
	/>
</div>
