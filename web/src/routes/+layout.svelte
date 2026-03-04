<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<nav class="bg-gray-900 text-white px-6 py-3 flex items-center justify-between">
	<a href="/" class="text-xl font-bold tracking-tight">OnMe</a>
	<div class="flex gap-6 text-sm">
		<a href="/" class="hover:text-gray-300">Gallery</a>
		<a href="/tryon" class="hover:text-gray-300">Try On</a>
		<a href="/metrics" class="hover:text-gray-300">Metrics</a>
	</div>
</nav>

<main class="max-w-6xl mx-auto px-6 py-8">
	{@render children()}
</main>
