<script lang="ts">
	import { useUpdateNodeInternals, type NodeProps, Handle, Position } from '@xyflow/svelte';
	
	let { id, data, selected }: NodeProps = $props();
	
	let text = $state(data.text as string || '');
	const updateNodeInternals = useUpdateNodeInternals();

	function onChange(e: Event) {
		const target = e.target as HTMLTextAreaElement;
		text = target.value;
		data.text = text;
		updateNodeInternals(id);
	}
</script>

<div
	class="relative min-h-[100px] min-w-[200px] max-w-[400px] overflow-hidden rounded-xl bg-[#fff8e1] shadow-md transition-shadow"
	class:ring-2={selected}
	class:ring-pin-red={selected}
>
	<!-- Custom top handle -->
	<Handle
		type="target"
		position={Position.Top}
		class="!h-3 !w-3 !border-2 !border-white !bg-pin-red"
	/>

	<textarea
		class="nodrag block h-full min-h-[100px] w-full resize-y bg-transparent p-4 text-sm text-gray-800 focus:outline-none"
		placeholder="Type your notes here..."
		value={text}
		oninput={onChange}
	></textarea>

	<!-- Custom bottom handle -->
	<Handle
		type="source"
		position={Position.Bottom}
		class="!h-3 !w-3 !border-2 !border-white !bg-pin-red"
	/>
</div>
