<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { initAuth, getIsInitialised } from '$lib/stores/auth.svelte';
	import Toast from '$lib/components/Toast.svelte';

	let { children } = $props();

	onMount(async () => {
		await initAuth();
	});
</script>

<svelte:head>
	<title>OnMe — AI Virtual Fitting Room</title>
	<meta name="description" content="OnMe is an AI-powered virtual fitting room. Try on garments using state-of-the-art diffusion models." />
</svelte:head>

{#if !getIsInitialised()}
	<!-- Loading spinner while auth state initialises -->
	<div class="fixed inset-0 flex items-center justify-center bg-surface-primary">
		<div class="flex flex-col items-center gap-4">
			<div class="h-10 w-10 animate-spin rounded-full border-3 border-surface-hover border-t-pin-red"></div>
			<span class="text-sm text-pin-medium-gray">Loading...</span>
		</div>
	</div>
{:else}
	{@render children()}
{/if}

<Toast />
