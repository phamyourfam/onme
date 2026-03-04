<script lang="ts">
	import { onMount } from 'svelte';
	import type { MetricsData } from '$lib/types';

	let metrics: MetricsData | null = $state(null);
	let loadError: string | null = $state(null);

	onMount(async () => {
		try {
			const res = await fetch('/metrics.json');
			if (!res.ok) throw new Error('Failed to load metrics');
			metrics = await res.json();
		} catch (err) {
			loadError = err instanceof Error ? err.message : 'Unknown error';
		}
	});

	/**
	 * Compare two nullable numbers and return which is better.
	 * Returns 'a', 'b', or 'none' if either is null or they are equal.
	 */
	function better(a: number | null, b: number | null, lowerIsBetter: boolean): 'a' | 'b' | 'none' {
		if (a == null || b == null) return 'none';
		if (a === b) return 'none';
		if (lowerIsBetter) return a < b ? 'a' : 'b';
		return a > b ? 'a' : 'b';
	}

	function fmt(v: number | null): string {
		if (v == null) return '—';
		return Number.isInteger(v) ? v.toString() : v.toFixed(4);
	}

	interface MetricRow {
		label: string;
		key: 'fid' | 'lpips' | 'ssim' | 'psnr' | 'clip_score' | 'avg_latency_ms';
		lowerIsBetter: boolean;
	}

	const metricRows: MetricRow[] = [
		{ label: 'FID', key: 'fid', lowerIsBetter: true },
		{ label: 'LPIPS', key: 'lpips', lowerIsBetter: true },
		{ label: 'SSIM', key: 'ssim', lowerIsBetter: false },
		{ label: 'PSNR', key: 'psnr', lowerIsBetter: false },
		{ label: 'CLIP Score', key: 'clip_score', lowerIsBetter: false },
		{ label: 'Avg Latency (ms)', key: 'avg_latency_ms', lowerIsBetter: true }
	];
</script>

<h1 class="text-2xl font-bold mb-6">Evaluation Metrics</h1>

{#if loadError}
	<p class="text-red-600">{loadError}</p>
{:else if !metrics}
	<p class="text-gray-500">Loading…</p>
{:else}
	<!-- Model Comparison -->
	<section class="mb-10">
		<h2 class="text-xl font-semibold mb-3">Model Comparison</h2>
		<div class="overflow-x-auto">
			<table class="w-full text-sm border-collapse">
				<thead>
					<tr class="border-b text-left">
						<th class="py-2 pr-4">Metric</th>
						<th class="py-2 pr-4">{metrics.models[0]?.name ?? 'Model A'}</th>
						<th class="py-2 pr-4">{metrics.models[1]?.name ?? 'Model B'}</th>
						<th class="py-2">Better</th>
					</tr>
				</thead>
				<tbody>
					{#each metricRows as row}
						{@const a = metrics.models[0]?.[row.key] ?? null}
						{@const b = metrics.models[1]?.[row.key] ?? null}
						{@const winner = better(a, b, row.lowerIsBetter)}
						<tr class="border-b even:bg-gray-50">
							<td class="py-2 pr-4 font-medium">{row.label}</td>
							<td class="py-2 pr-4" class:text-emerald-600={winner === 'a'}>
								{#if a == null}<span class="text-gray-400 italic">Pending</span>{:else}{fmt(a)}{/if}
							</td>
							<td class="py-2 pr-4" class:text-emerald-600={winner === 'b'}>
								{#if b == null}<span class="text-gray-400 italic">Pending</span>{:else}{fmt(b)}{/if}
							</td>
							<td class="py-2">
								{#if winner === 'a'}{metrics.models[0]?.name}
								{:else if winner === 'b'}{metrics.models[1]?.name}
								{:else}—{/if}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</section>

	<!-- Ablation Study -->
	<section class="mb-10">
		<h2 class="text-xl font-semibold mb-3">Ablation Study</h2>
		<div class="overflow-x-auto">
			<table class="w-full text-sm border-collapse">
				<thead>
					<tr class="border-b text-left">
						<th class="py-2 pr-4">Preprocessing Step</th>
						<th class="py-2 pr-4">SSIM With</th>
						<th class="py-2 pr-4">SSIM Without</th>
						<th class="py-2">Δ</th>
					</tr>
				</thead>
				<tbody>
					{#each [{ name: 'CLAHE', withData: metrics.ablation.with_clahe, withoutData: metrics.ablation.without_clahe }, { name: 'Colour Correction', withData: metrics.ablation.with_colour_correction, withoutData: metrics.ablation.without_colour_correction }] as row}
						{@const withVal = row.withData.ssim}
						{@const withoutVal = row.withoutData.ssim}
						{@const delta = withVal != null && withoutVal != null ? withVal - withoutVal : null}
						<tr class="border-b even:bg-gray-50">
							<td class="py-2 pr-4 font-medium">{row.name}</td>
							<td class="py-2 pr-4">
								{#if withVal == null}<span class="text-gray-400 italic">Pending</span>{:else}{fmt(withVal)}{/if}
							</td>
							<td class="py-2 pr-4">
								{#if withoutVal == null}<span class="text-gray-400 italic">Pending</span>{:else}{fmt(withoutVal)}{/if}
							</td>
							<td class="py-2" class:text-emerald-600={delta != null && delta > 0} class:text-red-600={delta != null && delta < 0}>
								{#if delta == null}—{:else}{delta > 0 ? '+' : ''}{fmt(delta)}{/if}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</section>

	<!-- Last Updated -->
	<p class="text-sm text-gray-500">
		{#if metrics.last_updated}
			Last updated: {metrics.last_updated}
		{:else}
			Not yet computed
		{/if}
	</p>
{/if}
