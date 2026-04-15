<script lang="ts">
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import {
		SvelteFlow,
		Background,
		Controls,
		MiniMap,
		BackgroundVariant,
		type Node,
		type Edge,
	} from '@xyflow/svelte';
	import '@xyflow/svelte/dist/style.css';

	import ImageNode from '$lib/components/ImageNode.svelte';
	import { getMoodboard, updateMoodboardCanvas, getImageUrl } from '$lib/api';
	import { addToast } from '$lib/stores/toast.svelte';
	import type { MoodboardDetail } from '$lib/types';

	const nodeTypes = { image: ImageNode };

	let moodboard = $state<MoodboardDetail | null>(null);
	let loading = $state(true);
	let saving = $state(false);
	let lastSaved = $state<string | null>(null);

	let nodes = $state.raw<Node[]>([]);
	let edges = $state.raw<Edge[]>([]);

	let _saveTimeout: ReturnType<typeof setTimeout> | null = null;

	const moodboardId = $derived(page.params.id as string);

	onMount(async () => {
		await loadMoodboard();
		checkForInjectedImage();
	});

	async function loadMoodboard() {
		loading = true;
		try {
			const mb = await getMoodboard(moodboardId);
			moodboard = mb;

			if (mb.canvas_state) {
				try {
					const parsed = JSON.parse(mb.canvas_state);
					nodes = parsed.nodes ?? [];
					edges = parsed.edges ?? [];
				} catch {
					nodes = [];
					edges = [];
				}
			}
		} catch {
			addToast('Failed to load moodboard.', 'error');
			goto('/catalog');
		} finally {
			loading = false;
		}
	}

	function checkForInjectedImage() {
		const injectUrl = page.url.searchParams.get('inject_image');
		const injectLabel = page.url.searchParams.get('inject_label');

		if (injectUrl) {
			const newNode: Node = {
				id: `img-${Date.now()}`,
				type: 'image',
				position: { x: 100 + Math.random() * 200, y: 100 + Math.random() * 200 },
				data: {
					label: injectLabel ?? 'Try-On Result',
					imageUrl: getImageUrl(injectUrl),
					width: 220,
					height: 280,
				},
			};
			nodes = [...nodes, newNode];

			// Clean up URL params without triggering navigation
			const cleanUrl = new URL(page.url);
			cleanUrl.searchParams.delete('inject_image');
			cleanUrl.searchParams.delete('inject_label');
			history.replaceState({}, '', cleanUrl.toString());

			// Auto-save after injection
			debouncedSave();
		}
	}

	async function saveCanvas() {
		if (!moodboardId) return;
		saving = true;
		try {
			const canvasState = JSON.stringify({ nodes, edges });
			const result = await updateMoodboardCanvas(moodboardId, canvasState);
			lastSaved = new Date(result.updated_at).toLocaleTimeString();
			addToast('Canvas saved.', 'success', 2000);
		} catch {
			addToast('Failed to save canvas.', 'error');
		} finally {
			saving = false;
		}
	}

	function debouncedSave() {
		if (_saveTimeout) clearTimeout(_saveTimeout);
		_saveTimeout = setTimeout(() => {
			saveCanvas();
		}, 1500);
	}

	function handleNodeDragStop() {
		debouncedSave();
	}

	function handleConnect() {
		debouncedSave();
	}

	function handleDelete() {
		debouncedSave();
	}

	function addTextNode() {
		const newNode: Node = {
			id: `note-${Date.now()}`,
			type: 'default',
			position: { x: 150 + Math.random() * 300, y: 150 + Math.random() * 200 },
			data: { label: 'New Note' },
		};
		nodes = [...nodes, newNode];
	}
</script>

<svelte:head>
	<title>{moodboard?.title ?? 'Moodboard'} — OnMe</title>
</svelte:head>

{#if loading}
	<div class="flex h-full items-center justify-center">
		<div class="flex flex-col items-center gap-4">
			<div class="h-10 w-10 animate-spin rounded-full border-3 border-surface-hover border-t-pin-red"></div>
			<span class="text-sm text-pin-medium-gray">Loading moodboard...</span>
		</div>
	</div>
{:else}
	<div class="flex h-full flex-col">
		<!-- TOOLBAR -->
		<div class="flex items-center justify-between border-b border-white/10 bg-surface-sidebar px-4 py-2">
			<div class="flex items-center gap-3">
				<a
					href="/catalog"
					class="flex items-center gap-1.5 rounded-gestalt px-2 py-1 text-sm text-pin-medium-gray transition-colors hover:bg-surface-hover hover:text-white"
				>
					<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
						<path fill-rule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clip-rule="evenodd" />
					</svg>
					Back
				</a>

				<h1 class="text-sm font-semibold text-white">
					{moodboard?.title ?? 'Untitled'}
				</h1>
			</div>

			<div class="flex items-center gap-2">
				{#if lastSaved}
					<span class="text-xs text-pin-medium-gray">
						Saved {lastSaved}
					</span>
				{/if}

				<button
					onclick={addTextNode}
					class="rounded-gestalt bg-surface-card px-3 py-1.5 text-xs font-medium text-pin-medium-gray transition-colors hover:bg-surface-hover hover:text-white"
				>
					+ Note
				</button>

				<button
					id="save-canvas-btn"
					onclick={saveCanvas}
					disabled={saving}
					class="rounded-gestalt bg-pin-red px-4 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-pin-red-hover disabled:opacity-50"
				>
					{saving ? 'Saving...' : 'Save'}
				</button>
			</div>
		</div>

		<!-- CANVAS -->
		<div class="flex-1">
			<SvelteFlow
				bind:nodes
				bind:edges
				{nodeTypes}
				fitView
				onnodedragstop={handleNodeDragStop}
				onconnect={handleConnect}
				ondelete={handleDelete}
				colorMode="dark"
			>
				<Background variant={BackgroundVariant.Dots} />
				<Controls />
				<MiniMap />
			</SvelteFlow>
		</div>
	</div>
{/if}
