<script lang="ts">
	import { onDestroy } from 'svelte';
	import { SvelteFlow, Background, Controls, Position } from '@xyflow/svelte';
	import type { Node, Edge } from '@xyflow/svelte';
	import '@xyflow/svelte/dist/style.css';

	import ImageNode from '$lib/nodes/ImageNode.svelte';
	import { createInitialNodes, pipelineEdges } from '$lib/pipeline';
	import { submitTryOn, getJobStatus, getImageUrl } from '$lib/api';
	import type { PipelineNodeData } from '$lib/types';

	const nodeTypes = { imageNode: ImageNode };

	let nodes: Node<PipelineNodeData>[] = $state(createInitialNodes());
	let edges: Edge[] = $state(pipelineEdges.map((e) => ({ ...e })));

	let personFile: File | null = $state(null);
	let garmentFile: File | null = $state(null);
	let personPreview: string | null = $state(null);
	let garmentPreview: string | null = $state(null);
	let selectedModel: string = $state('catvton');
	let jobId: string | null = $state(null);
	let polling = $state(false);
	let errorMsg: string | null = $state(null);

	let pollInterval: ReturnType<typeof setInterval> | null = null;

	function onPersonChange(e: Event) {
		const input = e.target as HTMLInputElement;
		const file = input.files?.[0] ?? null;
		personFile = file;
		if (personPreview) URL.revokeObjectURL(personPreview);
		personPreview = file ? URL.createObjectURL(file) : null;
		updateUploadNode('person_upload', personPreview);
	}

	function onGarmentChange(e: Event) {
		const input = e.target as HTMLInputElement;
		const file = input.files?.[0] ?? null;
		garmentFile = file;
		if (garmentPreview) URL.revokeObjectURL(garmentPreview);
		garmentPreview = file ? URL.createObjectURL(file) : null;
		updateUploadNode('garment_upload', garmentPreview);
	}

	function updateUploadNode(nodeId: string, url: string | null) {
		nodes = nodes.map((n) =>
			n.id === nodeId
				? { ...n, data: { ...n.data, imageUrl: url, status: url ? 'complete' : 'idle' } as PipelineNodeData }
				: n
		);
	}

	async function handleSubmit() {
		if (!personFile || !garmentFile) return;
		errorMsg = null;
		polling = true;

		// Reset processing nodes
		nodes = nodes.map((n) => {
			if (n.id !== 'person_upload' && n.id !== 'garment_upload') {
				return { ...n, data: { ...n.data, imageUrl: null, status: 'idle', elapsedMs: null } as PipelineNodeData };
			}
			return n;
		});

		// Animate edges
		edges = edges.map((e) => ({ ...e, animated: true }));

		try {
			const job = await submitTryOn(personFile, garmentFile, selectedModel);
			jobId = job.id;
			startPolling(job.id);
		} catch (err) {
			errorMsg = err instanceof Error ? err.message : 'Submission failed';
			polling = false;
			edges = edges.map((e) => ({ ...e, animated: false }));
		}
	}

	function startPolling(id: string) {
		pollInterval = setInterval(async () => {
			try {
				const job = await getJobStatus(id);
				updateNodesFromJob(job);

				if (job.status === 'complete' || job.status === 'failed') {
					stopPolling();
					if (job.status === 'failed') {
						errorMsg = job.error_message ?? 'Job failed';
					}
				}
			} catch {
				stopPolling();
				errorMsg = 'Lost connection to server';
			}
		}, 2000);
	}

	function stopPolling() {
		if (pollInterval) {
			clearInterval(pollInterval);
			pollInterval = null;
		}
		polling = false;
		edges = edges.map((e) => ({ ...e, animated: false }));
	}

	function updateNodesFromJob(job: import('$lib/types').JobStatus) {
		nodes = nodes.map((n) => {
			const d = n.data as PipelineNodeData;
			// Skip upload nodes — they keep their local previews
			if (n.id === 'person_upload' || n.id === 'garment_upload') return n;

			if (job.intermediates && d.stage in job.intermediates) {
				return {
					...n,
					data: {
						...d,
						status: 'complete',
						imageUrl: getImageUrl(job.intermediates[d.stage])
					} as PipelineNodeData
				};
			}
			if (job.current_stage === d.stage) {
				return { ...n, data: { ...d, status: 'processing' } as PipelineNodeData };
			}
			return n;
		});

		// Apply timing if available
		if (job.timing) {
			const timingMap: Record<string, number | null> = {
				clahe: job.timing.preprocessing_ms,
				garment_resize: job.timing.preprocessing_ms,
				inference: job.timing.inference_ms,
				colour_correct: job.timing.postprocessing_ms
			};
			nodes = nodes.map((n) => {
				if (n.id in timingMap) {
					return {
						...n,
						data: { ...n.data, elapsedMs: timingMap[n.id] } as PipelineNodeData
					};
				}
				return n;
			});
		}
	}

	onDestroy(() => {
		if (pollInterval) clearInterval(pollInterval);
		if (personPreview) URL.revokeObjectURL(personPreview);
		if (garmentPreview) URL.revokeObjectURL(garmentPreview);
	});
</script>

<h1 class="text-2xl font-bold mb-6">Virtual Try-On</h1>

<!-- Upload Controls -->
<div class="flex flex-col md:flex-row gap-4 mb-6">
	<label class="flex-1 block">
		<span class="text-sm font-medium text-gray-700">Your Photo</span>
		<input type="file" accept="image/*" onchange={onPersonChange} class="mt-1 block w-full text-sm" />
		{#if personPreview}
			<img src={personPreview} alt="Person preview" class="mt-2 w-24 h-24 object-cover rounded border" />
		{/if}
	</label>

	<label class="flex-1 block">
		<span class="text-sm font-medium text-gray-700">Garment</span>
		<input type="file" accept="image/*" onchange={onGarmentChange} class="mt-1 block w-full text-sm" />
		{#if garmentPreview}
			<img src={garmentPreview} alt="Garment preview" class="mt-2 w-24 h-24 object-cover rounded border" />
		{/if}
	</label>

	<div class="flex flex-col gap-2">
		<label class="block">
			<span class="text-sm font-medium text-gray-700">Model</span>
			<select bind:value={selectedModel} class="mt-1 block w-full rounded border-gray-300 text-sm">
				<option value="catvton">CatVTON</option>
				<option value="ootdiffusion">OOTDiffusion</option>
			</select>
		</label>

		<button
			onclick={handleSubmit}
			disabled={!personFile || !garmentFile || polling}
			class="mt-auto px-4 py-2 bg-gray-900 text-white rounded text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-700"
		>
			{polling ? 'Processing…' : 'Submit'}
		</button>
	</div>
</div>

{#if errorMsg}
	<p class="text-red-600 text-sm mb-4">{errorMsg}</p>
{/if}

<!-- Pipeline Visualisation -->
<div class="h-[500px] border rounded-lg overflow-hidden">
	<SvelteFlow
		{nodes}
		{edges}
		{nodeTypes}
		fitView
		nodesDraggable={false}
		nodesConnectable={false}
		elementsSelectable={false}
	>
		<Background />
		<Controls />
	</SvelteFlow>
</div>
