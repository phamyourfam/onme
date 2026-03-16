<script lang="ts">
	import type { MetricsData } from '$lib/types';
	import { onMount } from 'svelte';

	let metrics = $state<MetricsData | null>(null);
	let loading = $state(true);

	onMount(async () => {
		try {
			const res = await fetch('/metrics.json');
			if (res.ok) {
				metrics = await res.json();
			} else {
				// API fallback if static file not found
				const apiRes = await fetch('/api/metrics');
				if (apiRes.ok) metrics = await apiRes.json();
			}
		} catch (error) {
			console.error('Failed to load metrics:', error);
		} finally {
			loading = false;
		}
	});

	// Helper to find best value in a column
	function isBest(
		val: number | null,
		key: keyof MetricsData['models'][0],
		lowerIsBetter: boolean
	): boolean {
		if (val === null || !metrics || !metrics.models) return false;
		
		const validVals = metrics.models
			.map((m) => m[key])
			.filter((v): v is number => v !== null);
			
		if (validVals.length < 2) return false; // Don't highlight if nothing to compare against
		
		const best = lowerIsBetter ? Math.min(...validVals) : Math.max(...validVals);
		return val === best;
	}

	// Calculate ablation delta
	function calcDelta(withVal: number | null, withoutVal: number | null): number | null {
		if (withVal === null || withoutVal === null) return null;
		return Number((withVal - withoutVal).toFixed(4));
	}
	
	// Determine delta color
	function getDeltaColor(delta: number | null, lowerIsBetter: boolean): string {
		if (delta === null || delta === 0) return 'text-pin-medium-gray';
		
		const isImprovement = lowerIsBetter ? delta < 0 : delta > 0;
		return isImprovement ? 'text-emerald-400' : 'text-red-400';
	}

	const allNull = $derived(
		metrics?.models.every(
			(m) =>
				m.fid === null &&
				m.lpips === null &&
				m.ssim === null &&
				m.psnr === null &&
				m.clip_score === null &&
				m.avg_latency_ms === null
		) ?? true
	);
</script>

{#snippet valueOrPending(val: number | null, decimals: number)}
	{#if val !== null}
		{val.toFixed(decimals)}
	{:else}
		<span class="italic text-pin-medium-gray text-xs">Pending</span>
	{/if}
{/snippet}

{#snippet latencyOrPending(val: number | null)}
	{#if val !== null}
		{Math.round(val).toLocaleString()}
	{:else}
		<span class="italic text-pin-medium-gray text-xs">Pending</span>
	{/if}
{/snippet}

{#snippet deltaCell(withVal: number | null, withoutVal: number | null, lowerIsBetter: boolean)}
	{@const delta = calcDelta(withVal, withoutVal)}
	<td class="px-4 py-4 text-center font-medium {getDeltaColor(delta, lowerIsBetter)}">
		{#if delta !== null}
			{delta > 0 ? '+' : ''}{delta}
		{:else}
			-
		{/if}
	</td>
{/snippet}

<svelte:head>
	<title>Metrics — OnMe</title>
</svelte:head>

<div class="mx-auto max-w-5xl py-8 px-4">
	<h1 class="mb-2 text-2xl font-bold text-white">Evaluation Metrics</h1>
	<p class="mb-8 text-sm text-pin-medium-gray">
		{#if metrics?.last_updated}
			Last updated: {new Date(metrics.last_updated).toLocaleString()}
		{:else}
			Quantitative evaluation results for virtual try-on models.
		{/if}
	</p>

	{#if loading}
		<div class="flex flex-col gap-8">
			<div class="h-64 animate-pulse rounded-2xl bg-surface-card"></div>
			<div class="h-48 animate-pulse rounded-2xl bg-surface-card"></div>
		</div>
	{:else if !metrics || allNull}
		<div class="flex min-h-[40vh] items-center justify-center rounded-2xl border border-white/10 bg-surface-card/50 p-12 text-center">
			<div>
				<svg xmlns="http://www.w3.org/2000/svg" class="mx-auto mb-4 h-12 w-12 text-pin-medium-gray" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
				</svg>
				<p class="text-pin-medium-gray italic">
					Evaluation metrics will appear here after running the eval suite.
				</p>
			</div>
		</div>
	{:else}
		<div class="flex flex-col gap-10">
			<!-- MODEL COMPARISON TABLE -->
			<section>
				<h2 class="mb-4 text-lg font-semibold text-white">Model Comparison</h2>
				<div class="overflow-x-auto rounded-2xl border border-white/5 bg-surface-card" style="scrollbar-width: thin;">
					<table class="w-full text-left text-sm">
						<thead>
							<tr class="border-b border-white/5 bg-black/20 text-xs uppercase tracking-wider text-pin-medium-gray">
								<th class="px-6 py-4 font-medium">Model</th>
								<th class="px-6 py-4 font-medium">FID <span class="text-[10px] normal-case opacity-70">(lower is better)</span></th>
								<th class="px-6 py-4 font-medium">LPIPS <span class="text-[10px] normal-case opacity-70">(lower is better)</span></th>
								<th class="px-6 py-4 font-medium">SSIM <span class="text-[10px] normal-case opacity-70">(higher is better)</span></th>
								<th class="px-6 py-4 font-medium">PSNR <span class="text-[10px] normal-case opacity-70">(higher is better)</span></th>
								<th class="px-6 py-4 font-medium">CLIP Score <span class="text-[10px] normal-case opacity-70">(higher is better)</span></th>
								<th class="px-6 py-4 font-medium">Latency <span class="text-[10px] normal-case opacity-70">(ms)</span></th>
							</tr>
						</thead>
						<tbody class="divide-y divide-white/5">
							{#each metrics.models as model, i}
								<tr class="transition-colors hover:bg-surface-hover/50 {i % 2 === 0 ? '' : 'bg-surface-primary/30'}">
									<td class="whitespace-nowrap px-6 py-4 font-medium text-white">
										{model.name}
										<span class="ml-2 rounded bg-white/10 px-1.5 py-0.5 text-[10px] text-pin-medium-gray">
											n={model.sample_count}
										</span>
									</td>
									<td class="px-6 py-4 {isBest(model.fid, 'fid', true) ? 'font-semibold text-emerald-400' : 'text-white'}">
										{@render valueOrPending(model.fid, 2)}
									</td>
									<td class="px-6 py-4 {isBest(model.lpips, 'lpips', true) ? 'font-semibold text-emerald-400' : 'text-white'}">
										{@render valueOrPending(model.lpips, 4)}
									</td>
									<td class="px-6 py-4 {isBest(model.ssim, 'ssim', false) ? 'font-semibold text-emerald-400' : 'text-white'}">
										{@render valueOrPending(model.ssim, 4)}
									</td>
									<td class="px-6 py-4 {isBest(model.psnr, 'psnr', false) ? 'font-semibold text-emerald-400' : 'text-white'}">
										{@render valueOrPending(model.psnr, 2)}
									</td>
									<td class="px-6 py-4 {isBest(model.clip_score, 'clip_score', false) ? 'font-semibold text-emerald-400' : 'text-white'}">
										{@render valueOrPending(model.clip_score, 4)}
									</td>
									<td class="px-6 py-4 {isBest(model.avg_latency_ms, 'avg_latency_ms', true) ? 'font-semibold text-emerald-400' : 'text-white'}">
										{@render latencyOrPending(model.avg_latency_ms)}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</section>

			<!-- ABLATION TABLE -->
			<section>
				<h2 class="mb-4 text-lg font-semibold text-white">Ablation Study</h2>
				<div class="overflow-x-auto rounded-2xl border border-white/5 bg-surface-card" style="scrollbar-width: thin;">
					<table class="w-full text-left text-sm">
						<thead>
							<tr class="border-b border-white/5 bg-black/20 text-xs uppercase tracking-wider text-pin-medium-gray">
								<th class="px-6 py-4 font-medium">Preprocessing Step</th>
								<th class="px-6 py-4 font-medium text-center" colspan="3">SSIM</th>
								<th class="px-6 py-4 font-medium text-center" colspan="3">LPIPS (lower is better)</th>
								<th class="px-6 py-4 font-medium text-center" colspan="3">PSNR</th>
							</tr>
							<tr class="border-b border-white/5 bg-black/10 text-[10px] uppercase tracking-wider text-pin-medium-gray">
								<th class="px-6 py-2"></th>
								<th class="px-4 py-2 text-center border-l border-white/5">With</th>
								<th class="px-4 py-2 text-center">Without</th>
								<th class="px-4 py-2 text-center">Delta</th>
								<th class="px-4 py-2 text-center border-l border-white/5">With</th>
								<th class="px-4 py-2 text-center">Without</th>
								<th class="px-4 py-2 text-center">Delta</th>
								<th class="px-4 py-2 text-center border-l border-white/5">With</th>
								<th class="px-4 py-2 text-center">Without</th>
								<th class="px-4 py-2 text-center">Delta</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-white/5">
							<!-- CLAHE -->
							<tr class="transition-colors hover:bg-surface-hover/50">
								<td class="whitespace-nowrap px-6 py-4 font-medium text-white">CLAHE Lighting</td>
								
								<!-- SSIM -->
								<td class="px-4 py-4 text-center text-white border-l border-white/5">{@render valueOrPending(metrics.ablation.with_clahe.ssim, 4)}</td>
								<td class="px-4 py-4 text-center text-white">{@render valueOrPending(metrics.ablation.without_clahe.ssim, 4)}</td>
								{@render deltaCell(metrics.ablation.with_clahe.ssim, metrics.ablation.without_clahe.ssim, false)}

								<!-- LPIPS -->
								<td class="px-4 py-4 text-center text-white border-l border-white/5">{@render valueOrPending(metrics.ablation.with_clahe.lpips, 4)}</td>
								<td class="px-4 py-4 text-center text-white">{@render valueOrPending(metrics.ablation.without_clahe.lpips, 4)}</td>
								{@render deltaCell(metrics.ablation.with_clahe.lpips, metrics.ablation.without_clahe.lpips, true)}

								<!-- PSNR -->
								<td class="px-4 py-4 text-center text-white border-l border-white/5">{@render valueOrPending(metrics.ablation.with_clahe.psnr, 2)}</td>
								<td class="px-4 py-4 text-center text-white">{@render valueOrPending(metrics.ablation.without_clahe.psnr, 2)}</td>
								{@render deltaCell(metrics.ablation.with_clahe.psnr, metrics.ablation.without_clahe.psnr, false)}
							</tr>

							<!-- Colour Correction -->
							<tr class="bg-surface-primary/30 transition-colors hover:bg-surface-hover/50">
								<td class="whitespace-nowrap px-6 py-4 font-medium text-white">Colour Correction</td>
								
								<!-- SSIM -->
								<td class="px-4 py-4 text-center text-white border-l border-white/5">{@render valueOrPending(metrics.ablation.with_colour_correction.ssim, 4)}</td>
								<td class="px-4 py-4 text-center text-white">{@render valueOrPending(metrics.ablation.without_colour_correction.ssim, 4)}</td>
								{@render deltaCell(metrics.ablation.with_colour_correction.ssim, metrics.ablation.without_colour_correction.ssim, false)}

								<!-- LPIPS -->
								<td class="px-4 py-4 text-center text-white border-l border-white/5">{@render valueOrPending(metrics.ablation.with_colour_correction.lpips, 4)}</td>
								<td class="px-4 py-4 text-center text-white">{@render valueOrPending(metrics.ablation.without_colour_correction.lpips, 4)}</td>
								{@render deltaCell(metrics.ablation.with_colour_correction.lpips, metrics.ablation.without_colour_correction.lpips, true)}

								<!-- PSNR -->
								<td class="px-4 py-4 text-center text-white border-l border-white/5">{@render valueOrPending(metrics.ablation.with_colour_correction.psnr, 2)}</td>
								<td class="px-4 py-4 text-center text-white">{@render valueOrPending(metrics.ablation.without_colour_correction.psnr, 2)}</td>
								{@render deltaCell(metrics.ablation.with_colour_correction.psnr, metrics.ablation.without_colour_correction.psnr, false)}
							</tr>
						</tbody>
					</table>
				</div>
			</section>
		</div>
	{/if}
</div>
