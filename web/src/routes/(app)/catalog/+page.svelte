<script lang="ts">
	import { getGarments, getImageUrl } from '$lib/api';
	import type { GarmentResponse } from '$lib/types';
	import { onMount } from 'svelte';

	let activeCategory = $state('All');
	let allGarments = $state<GarmentResponse[]>([]);
	let loading = $state(true);
	let urlInput = $state('');

	let dynamicCategories = $derived(['All', ...new Set(allGarments.map(g => g.category).filter(Boolean))]);
	let filteredGarments = $derived(
		activeCategory === 'All'
			? allGarments
			: allGarments.filter(g => g.category === activeCategory)
	);

	async function loadGarments() {
		loading = true;
		try {
			allGarments = await getGarments();
		} catch (error) {
			console.error('Failed to load garments:', error);
			allGarments = [];
		} finally {
			loading = false;
		}
	}

	// Fetch initially when component mounts
	onMount(() => {
		loadGarments();
	});

	function handleTryOn(imageUrl: string) {
		console.log('Selected garment for Try On:', imageUrl);
		// Proceed to try-on flow (Epic 8)
	}

	function handleUrlSubmit(e: Event) {
		e.preventDefault();
		console.log('Submitted garment URL:', urlInput);
		urlInput = '';
	}

	function hideOnError(e: Event) {
		const target = e.currentTarget as HTMLImageElement;
		target.style.display = 'none';
	}
</script>

<svelte:head>
	<title>Catalog — OnMe</title>
</svelte:head>

<div class="relative min-h-[calc(100vh-4rem)] pb-24">
	<!-- CATEGORY TABS -->
	<div class="scrollbar-hide overflow-x-auto p-4">
		<div class="flex gap-2">
			{#each dynamicCategories as category}
				<button
					onclick={() => { activeCategory = category; }}
					class="whitespace-nowrap rounded-pill px-4 py-2 text-sm font-medium transition-colors
					{activeCategory === category
						? 'bg-white text-black'
						: 'bg-surface-card text-pin-medium-gray hover:bg-surface-hover'}"
				>
					{category}
				</button>
			{/each}
		</div>
	</div>

	<!-- MASONRY GRID -->
	{#if loading}
		<div class="columns-2 gap-3 p-4 sm:columns-3 md:columns-4">
			{#each Array(8) as _}
				<div class="mb-3 break-inside-avoid">
					<div
						class="animate-pulse rounded-2xl bg-surface-card"
						style="height: {Math.floor(Math.random() * (320 - 160 + 1) + 160)}px;"
					></div>
				</div>
			{/each}
		</div>
	{:else if filteredGarments.length === 0}
		<div class="flex flex-col items-center justify-center p-12 text-center">
			<svg xmlns="http://www.w3.org/2000/svg" class="mb-4 h-12 w-12 text-pin-medium-gray" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
			</svg>
			<h2 class="text-lg font-medium text-white">No garments found</h2>
			<p class="mt-2 text-sm text-pin-medium-gray">
				Try selecting a different category or adding a new garment URL below.
			</p>
		</div>
	{:else}
		<div class="columns-2 gap-3 p-4 sm:columns-3 md:columns-4">
			{#each filteredGarments as garment (garment.id)}
				<div class="group relative mb-3 break-inside-avoid cursor-pointer overflow-hidden rounded-2xl bg-surface-card">
					<!-- Garment Image -->
					<img
						src={getImageUrl(garment.image_url)}
						alt={garment.title}
						class="w-full object-cover"
						loading="lazy"
						onerror={hideOnError}
					/>

					<!-- Fallback label if image fails -->
					<div class="absolute inset-0 flex items-center justify-center p-4 text-center text-sm font-medium text-pin-medium-gray -z-10">
						{garment.title}
					</div>

					<!-- Hover Overlay -->
					<div class="absolute inset-0 flex flex-col justify-end bg-black/40 p-3 opacity-0 transition-opacity duration-200 group-hover:opacity-100">
						<!-- Optional: Source credit could go here -->
						{#if garment.source}
							<span class="mb-2 text-xs text-white/80">{garment.source}</span>
						{/if}
						
						<button
							onclick={() => handleTryOn(garment.image_url)}
							class="w-full rounded-pill bg-pin-red px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-pin-red-hover"
						>
							Try On
						</button>
					</div>
				</div>
			{/each}
		</div>
	{/if}

	<!-- FLOATING INPUT BAR -->
<<<<<<< HEAD
	<div class="pointer-events-none fixed inset-x-0 bottom-6 z-30 flex items-center justify-center px-4">
=======
	<div class="pointer-events-none fixed inset-x-0 md:left-72 bottom-6 z-30 flex items-center justify-center px-4">
>>>>>>> 43933ad (fix(web): center garment url input bar in catalog footer)
		<div class="pointer-events-auto w-full max-w-xl mx-auto flex items-center justify-center rounded-pill border border-white/10 bg-surface-card/80 shadow-2xl backdrop-blur-xl">
			<form
				onsubmit={handleUrlSubmit}
				class="flex w-full items-center justify-center gap-3 px-4 py-3"
			>
				<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 shrink-0 text-pin-medium-gray" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
				</svg>

				<input
					type="url"
					bind:value={urlInput}
					placeholder="Paste a garment URL or search..."
					class="min-w-0 flex-1 bg-transparent text-sm text-white placeholder-pin-medium-gray outline-none"
					required
				/>

				<button
					type="submit"
					class="shrink-0 rounded-pill bg-pin-red px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-pin-red-hover disabled:opacity-50"
					disabled={!urlInput.trim()}
				>
					Generate
				</button>
			</form>
		</div>
	</div>
</div>
