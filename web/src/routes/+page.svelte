<script lang="ts">
	interface GalleryItem {
		id: string;
		caption: string;
		person: string;
		garment: string;
		catvton: string;
		ootd: string;
	}

	interface LimitationItem {
		id: string;
		caption: string;
		reason: string;
		person: string;
		garment: string;
		catvton: string;
		ootd: string;
	}

	const gallery: GalleryItem[] = [];

	const limitations: LimitationItem[] = [];

	function hideOnError(e: Event) {
		(e.currentTarget as HTMLImageElement).style.display = 'none';
	}
</script>

<!-- Hero -->
<section class="text-center py-16">
	<h1 class="text-5xl font-bold tracking-tight">OnMe</h1>
	<p class="mt-4 text-lg text-gray-600 max-w-2xl mx-auto">
		Virtual try-on powered by diffusion models, with real-time pipeline visualisation
		and quantitative evaluation.
	</p>
	<div class="mt-8 flex justify-center gap-4">
		<a
			href="/tryon"
			class="px-6 py-3 bg-gray-900 text-white rounded-lg font-medium hover:bg-gray-700"
		>
			Try It Yourself
		</a>
		<a
			href="/metrics"
			class="px-6 py-3 border border-gray-900 text-gray-900 rounded-lg font-medium hover:bg-gray-100"
		>
			View Metrics
		</a>
	</div>
</section>

<!-- Gallery -->
<section class="mt-12">
	<h2 class="text-2xl font-bold mb-6">Results Gallery</h2>

	{#if gallery.length === 0}
		<p class="text-gray-500 italic">Gallery will be populated during evaluation.</p>
	{:else}
		<div class="space-y-6">
			{#each gallery as item (item.id)}
				<div class="border rounded-lg p-4">
					<div class="grid grid-cols-2 md:grid-cols-4 gap-3">
						<div>
							<p class="text-xs text-gray-500 mb-1">Person</p>
							<img
								src={item.person}
								alt="Person"
								class="w-full aspect-square object-cover rounded"
								onerror={hideOnError}
							/>
						</div>
						<div>
							<p class="text-xs text-gray-500 mb-1">Garment</p>
							<img
								src={item.garment}
								alt="Garment"
								class="w-full aspect-square object-cover rounded"
								onerror={hideOnError}
							/>
						</div>
						<div>
							<p class="text-xs text-gray-500 mb-1">CatVTON</p>
							<img
								src={item.catvton}
								alt="CatVTON result"
								class="w-full aspect-square object-cover rounded"
								onerror={hideOnError}
							/>
						</div>
						<div>
							<p class="text-xs text-gray-500 mb-1">OOTDiffusion</p>
							<img
								src={item.ootd}
								alt="OOTDiffusion result"
								class="w-full aspect-square object-cover rounded"
								onerror={hideOnError}
							/>
						</div>
					</div>
					<p class="mt-3 text-sm text-gray-700">{item.caption}</p>
				</div>
			{/each}
		</div>
	{/if}
</section>

<!-- Known Limitations -->
<section class="mt-12 mb-12">
	<h2 class="text-2xl font-bold mb-6">Known Limitations</h2>

	{#if limitations.length === 0}
		<p class="text-gray-500 italic">Limitation cases will be documented during evaluation.</p>
	{:else}
		<div class="space-y-6">
			{#each limitations as item (item.id)}
				<div class="border-2 border-red-200 rounded-lg p-4">
					<div class="grid grid-cols-2 md:grid-cols-4 gap-3">
						<div>
							<p class="text-xs text-gray-500 mb-1">Person</p>
							<img
								src={item.person}
								alt="Person"
								class="w-full aspect-square object-cover rounded"
								onerror={hideOnError}
							/>
						</div>
						<div>
							<p class="text-xs text-gray-500 mb-1">Garment</p>
							<img
								src={item.garment}
								alt="Garment"
								class="w-full aspect-square object-cover rounded"
								onerror={hideOnError}
							/>
						</div>
						<div>
							<p class="text-xs text-gray-500 mb-1">CatVTON</p>
							<img
								src={item.catvton}
								alt="CatVTON result"
								class="w-full aspect-square object-cover rounded"
								onerror={hideOnError}
							/>
						</div>
						<div>
							<p class="text-xs text-gray-500 mb-1">OOTDiffusion</p>
							<img
								src={item.ootd}
								alt="OOTDiffusion result"
								class="w-full aspect-square object-cover rounded"
								onerror={hideOnError}
							/>
						</div>
					</div>
					<p class="mt-3 text-sm text-gray-700">{item.caption}</p>
					<p class="mt-1 text-sm text-red-600 font-medium">{item.reason}</p>
				</div>
			{/each}
		</div>
	{/if}
</section>
