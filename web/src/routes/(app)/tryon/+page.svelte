<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { submitTryOn, getJobStatus, getImageUrl, getMoodboards, createMoodboard } from '$lib/api';
	import { addToast } from '$lib/stores/toast.svelte';
	import { refreshUser } from '$lib/stores/auth.svelte';
	import type { JobStatus, MoodboardSummary } from '$lib/types';

	/* ── Form state ─────────────────────────────────────────────────── */
	let personFile = $state<File | null>(null);
	let garmentFile = $state<File | null>(null);
	let modelName = $state('catvton');
	let submitting = $state(false);

	/* ── Preview URLs ───────────────────────────────────────────────── */
	let personPreview = $state<string | null>(null);
	let garmentPreview = $state<string | null>(null);

	/* ── Job polling state ──────────────────────────────────────────── */
	let activeJob = $state<JobStatus | null>(null);
	let pollInterval: ReturnType<typeof setInterval> | null = null;

	/* ── Moodboard injection ────────────────────────────────────────── */
	let moodboards = $state<MoodboardSummary[]>([]);
	let showMoodboardPicker = $state(false);

	onMount(async () => {
		try {
			moodboards = await getMoodboards();
		} catch {
			// silently fail
		}
	});

	onDestroy(() => {
		stopPolling();
		if (personPreview) URL.revokeObjectURL(personPreview);
		if (garmentPreview && garmentPreview.startsWith('blob:')) URL.revokeObjectURL(garmentPreview);
	});

	/* ── Parameter mapping & state reset ────────────────────────────── */
	let lastProcessedUrl = $state<string | null>(null);

	$effect(() => {
		const paramGarment = $page.url.searchParams.get('garment_url');
		if (paramGarment && paramGarment !== lastProcessedUrl) {
			lastProcessedUrl = paramGarment;
			
			// Make sure try-on state is cleared for a new request
			activeJob = null;
			stopPolling();

			garmentPreview = paramGarment;
			
			// Automatically resolve the external image URL to a File object for the API handler
			fetch(paramGarment)
				.then((res) => res.blob())
				.then((blob) => {
					garmentFile = new File([blob], 'catalog-garment.jpg', { type: blob.type });
				})
				.catch((err) => {
					console.error('Failed to fetch garment blob:', err);
				});
		}
	});

	/* ── File handlers ──────────────────────────────────────────────── */

	function handlePersonChange(e: Event) {
		const input = e.target as HTMLInputElement;
		const file = input.files?.[0] ?? null;
		personFile = file;
		if (personPreview) URL.revokeObjectURL(personPreview);
		personPreview = file ? URL.createObjectURL(file) : null;
	}

	function handleGarmentChange(e: Event) {
		const input = e.target as HTMLInputElement;
		const file = input.files?.[0] ?? null;
		garmentFile = file;
		if (garmentPreview) URL.revokeObjectURL(garmentPreview);
		garmentPreview = file ? URL.createObjectURL(file) : null;
	}

	/* ── Submit ──────────────────────────────────────────────────────── */

	async function handleSubmit(e: Event) {
		e.preventDefault();
		if (!personFile || !garmentFile) {
			addToast('Please select both a person photo and a garment image.', 'warning');
			return;
		}

		submitting = true;
		try {
			const job = await submitTryOn(personFile, garmentFile, modelName);
			activeJob = job;
			startPolling(job.id);
			addToast('Try-on job submitted. Processing...', 'info', 3000);
		} catch {
			// toast already shown by API client
		} finally {
			submitting = false;
		}
	}

	/* ── Polling ─────────────────────────────────────────────────────── */

	function startPolling(jobId: string) {
		stopPolling();
		pollInterval = setInterval(async () => {
			try {
				const status = await getJobStatus(jobId);
				activeJob = status;

				if (status.status === 'complete' || status.status === 'failed') {
					stopPolling();
					await refreshUser(); // update credit count

					if (status.status === 'complete') {
						addToast('Try-on complete!', 'success');
					} else {
						addToast(status.error_message ?? 'Try-on job failed.', 'error');
					}
				}
			} catch {
				stopPolling();
			}
		}, 2000);
	}

	function stopPolling() {
		if (pollInterval) {
			clearInterval(pollInterval);
			pollInterval = null;
		}
	}

	/* ── Canvas injection ────────────────────────────────────────────── */

	async function injectIntoMoodboard(mbId: string) {
		if (!activeJob?.result_url) return;
		showMoodboardPicker = false;
		goto(`/moodboard/${mbId}?inject_image=${encodeURIComponent(activeJob.result_url)}&inject_label=${encodeURIComponent(`${modelName} result`)}`);
	}

	async function createAndInject() {
		try {
			const mb = await createMoodboard('Try-On Results');
			await injectIntoMoodboard(mb.id);
		} catch {
			addToast('Failed to create moodboard.', 'error');
		}
	}

	/* ── Stage label mapping ─────────────────────────────────────────── */

	function stageLabel(status: string, stage: string | null): string {
		if (status === 'complete') return 'Complete';
		if (status === 'failed') return 'Failed';
		if (stage === 'preprocessing') return 'Preprocessing images...';
		if (stage === 'inferring') return 'Running AI inference...';
		if (stage === 'postprocessing') return 'Applying colour correction...';
		if (status === 'pending') return 'Queued...';
		return 'Processing...';
	}

	function stageProgress(status: string, stage: string | null): number {
		if (status === 'complete') return 100;
		if (status === 'failed') return 100;
		if (stage === 'preprocessing') return 25;
		if (stage === 'inferring') return 55;
		if (stage === 'postprocessing') return 80;
		return 10;
	}
</script>

<svelte:head>
	<title>Try On — OnMe</title>
</svelte:head>

<div class="mx-auto max-w-4xl px-4 py-8">
	<h1 class="mb-2 text-2xl font-bold text-white">Virtual Try-On</h1>
	<p class="mb-8 text-sm text-pin-medium-gray">
		Upload a photo of yourself and a garment image to see how it looks on you.
	</p>

	<div class="grid gap-8 lg:grid-cols-2">
		<!-- UPLOAD FORM -->
		<form onsubmit={handleSubmit} class="flex flex-col gap-6">
			<!-- Person Image -->
			<div>
				<label for="tryon-person" class="mb-2 block text-sm font-medium text-white">Your Photo</label>
				<label
					for="tryon-person"
					class="group flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-white/10 bg-surface-card p-6 transition-colors hover:border-pin-red/50 hover:bg-surface-hover"
				>
					{#if personPreview}
						<img src={personPreview} alt="Person preview" class="mb-2 max-h-48 rounded-xl object-contain" />
						<span class="text-xs text-pin-medium-gray">{personFile?.name}</span>
					{:else}
						<svg xmlns="http://www.w3.org/2000/svg" class="mb-2 h-10 w-10 text-pin-medium-gray transition-colors group-hover:text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
						</svg>
						<span class="text-sm text-pin-medium-gray">Click to upload your photo</span>
					{/if}
				</label>
				<input
					id="tryon-person"
					type="file"
					accept="image/jpeg,image/png,image/webp"
					onchange={handlePersonChange}
					class="hidden"
				/>
			</div>

			<!-- Garment Image -->
			<div>
				<label for="tryon-garment" class="mb-2 block text-sm font-medium text-white">Garment Image</label>
				<label
					for="tryon-garment"
					class="group flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-white/10 bg-surface-card p-6 transition-colors hover:border-pin-red/50 hover:bg-surface-hover"
				>
					{#if garmentPreview}
						<img src={garmentPreview} alt="Garment preview" class="mb-2 max-h-48 rounded-xl object-contain" />
						<span class="text-xs text-pin-medium-gray">{garmentFile?.name}</span>
					{:else}
						<svg xmlns="http://www.w3.org/2000/svg" class="mb-2 h-10 w-10 text-pin-medium-gray transition-colors group-hover:text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0 0 22.5 18.75V5.25A2.25 2.25 0 0 0 20.25 3H3.75A2.25 2.25 0 0 0 1.5 5.25v13.5A2.25 2.25 0 0 0 3.75 21Z" />
						</svg>
						<span class="text-sm text-pin-medium-gray">Click to upload a garment</span>
					{/if}
				</label>
				<input
					id="tryon-garment"
					type="file"
					accept="image/jpeg,image/png,image/webp"
					onchange={handleGarmentChange}
					class="hidden"
				/>
			</div>

			<!-- Model Selector -->
			<div>
				<label for="tryon-model" class="mb-2 block text-sm font-medium text-white">Model</label>
				<select
					id="tryon-model"
					bind:value={modelName}
					class="w-full rounded-gestalt bg-surface-card px-4 py-3 text-white outline-none transition-all focus:ring-2 focus:ring-pin-red"
				>
					<option value="catvton">CatVTON</option>
					<option value="ootdiffusion">OOTDiffusion</option>
				</select>
			</div>

			<!-- Submit -->
			<button
				id="tryon-submit-btn"
				type="submit"
				disabled={submitting || !personFile || !garmentFile || (!!activeJob && activeJob.status !== 'complete' && activeJob.status !== 'failed')}
				class="flex w-full items-center justify-center rounded-pill bg-pin-red py-3 font-semibold text-white transition-colors hover:bg-pin-red-hover disabled:cursor-not-allowed disabled:opacity-50"
			>
				{#if submitting}
					<div class="mr-2 h-5 w-5 animate-spin rounded-full border-2 border-white/30 border-t-white"></div>
					Submitting...
				{:else}
					Generate Try-On
				{/if}
			</button>
		</form>

		<!-- RESULT PANEL -->
		<div class="flex flex-col gap-4">
			{#if activeJob}
				<!-- Progress -->
				{#if activeJob.status !== 'complete' && activeJob.status !== 'failed'}
					<div class="rounded-2xl border border-white/10 bg-surface-card p-6">
						<div class="mb-4 flex items-center gap-3">
							<div class="h-6 w-6 animate-spin rounded-full border-2 border-pin-medium-gray border-t-pin-red"></div>
							<span class="text-sm font-medium text-white">
								{stageLabel(activeJob.status, activeJob.current_stage)}
							</span>
						</div>

						<!-- Progress bar -->
						<div class="h-2 overflow-hidden rounded-full bg-surface-hover">
							<div
								class="h-full rounded-full bg-pin-red transition-all duration-700 ease-out"
								style="width: {stageProgress(activeJob.status, activeJob.current_stage)}%"
							></div>
						</div>

						<p class="mt-3 text-xs text-pin-medium-gray">
							Job ID: {activeJob.id.slice(0, 8)}...
						</p>
					</div>
				{/if}

				<!-- Failed -->
				{#if activeJob.status === 'failed'}
					<div class="rounded-2xl border border-red-500/30 bg-red-900/20 p-6">
						<h3 class="mb-2 text-sm font-semibold text-red-400">Generation Failed</h3>
						<p class="text-sm text-red-300/80">{activeJob.error_message ?? 'An unknown error occurred.'}</p>
					</div>
				{/if}

				<!-- Complete -->
				{#if activeJob.status === 'complete' && activeJob.result_url}
					<div class="overflow-hidden rounded-2xl border border-white/10 bg-surface-card">
						<img
							src={getImageUrl(activeJob.result_url)}
							alt="Try-on result"
							class="w-full object-contain"
						/>
					</div>

					<!-- Timing info -->
					{#if activeJob.timing}
						<div class="flex gap-3 text-xs text-pin-medium-gray">
							{#if activeJob.timing.preprocessing_ms}
								<span>Preprocessing: {activeJob.timing.preprocessing_ms}ms</span>
							{/if}
							{#if activeJob.timing.inference_ms}
								<span>Inference: {activeJob.timing.inference_ms}ms</span>
							{/if}
							{#if activeJob.timing.postprocessing_ms}
								<span>Postprocessing: {activeJob.timing.postprocessing_ms}ms</span>
							{/if}
						</div>
					{/if}

					<!-- Add to Moodboard -->
					<div class="relative">
						<button
							id="add-to-moodboard-btn"
							onclick={() => (showMoodboardPicker = !showMoodboardPicker)}
							class="flex w-full items-center justify-center gap-2 rounded-pill bg-surface-card py-3 text-sm font-medium text-white transition-colors hover:bg-surface-hover"
						>
							<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
								<path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" />
							</svg>
							Add to Moodboard
						</button>

						{#if showMoodboardPicker}
							<div class="absolute bottom-full left-0 right-0 mb-2 overflow-hidden rounded-2xl border border-white/10 bg-surface-sidebar shadow-2xl">
								<div class="max-h-48 overflow-y-auto p-2">
									<button
										onclick={createAndInject}
										class="flex w-full items-center gap-2 rounded-gestalt px-3 py-2 text-sm text-emerald-400 transition-colors hover:bg-surface-hover"
									>
										<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
											<path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" />
										</svg>
										New Moodboard
									</button>

									{#each moodboards as mb (mb.id)}
										<button
											onclick={() => injectIntoMoodboard(mb.id)}
											class="flex w-full items-center gap-2 truncate rounded-gestalt px-3 py-2 text-sm text-pin-medium-gray transition-colors hover:bg-surface-hover hover:text-white"
										>
											{mb.title}
										</button>
									{/each}
								</div>
							</div>
						{/if}
					</div>
				{/if}
			{:else}
				<!-- Empty state -->
				<div class="flex min-h-64 items-center justify-center rounded-2xl border border-white/5 bg-surface-card/50 p-8 text-center">
					<div>
						<svg xmlns="http://www.w3.org/2000/svg" class="mx-auto mb-4 h-12 w-12 text-pin-medium-gray" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 0 0-2.455 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z" />
						</svg>
						<p class="text-sm text-pin-medium-gray">
							Upload your photo and a garment to generate a virtual try-on.
						</p>
					</div>
				</div>
			{/if}
		</div>
	</div>
</div>
