<script lang="ts">
	import { goto } from '$app/navigation';
	import { getIsAuthenticated } from '$lib/stores/auth.svelte';

	// Redirect if already authenticated
	$effect(() => {
		if (getIsAuthenticated()) {
			goto('/catalog');
		}
	});

	// Placeholder masonry items with varying heights
	const heights = ['h-48', 'h-64', 'h-80', 'h-96'];
	const masonryItems = Array.from({ length: 30 }, (_, i) => ({
		id: i,
		height: heights[i % heights.length]
	}));
</script>

<svelte:head>
	<title>OnMe — AI Virtual Fitting Room</title>
	<meta name="description" content="Try on any outfit instantly with OnMe's AI-powered virtual fitting room. Powered by state-of-the-art diffusion models." />
</svelte:head>

{#if !getIsAuthenticated()}
	<div class="relative min-h-screen overflow-hidden">
		<!-- BACKGROUND MASONRY GRID (z-0) -->
		<div class="absolute inset-0 z-0 columns-3 gap-2 p-2 opacity-60 sm:columns-4 md:columns-5">
			{#each masonryItems as item (item.id)}
				<div
					class="mb-2 break-inside-avoid rounded-2xl bg-surface-card {item.height}"
					style="background: linear-gradient(135deg, hsl({item.id * 12}, 15%, 18%), hsl({item.id * 12 + 30}, 10%, 22%));"
				></div>
			{/each}
		</div>

		<!-- GRADIENT OVERLAY (z-10) -->
		<div class="absolute inset-0 z-10 bg-gradient-to-t from-black via-black/70 to-transparent"></div>

		<!-- AUTH CONTENT (z-20) -->
		<div class="absolute inset-x-0 bottom-0 z-20 flex justify-center">
			<div class="w-full max-w-md px-6 pb-16">
				<!-- Logo -->
				<h1 class="mb-2 text-3xl font-bold tracking-tight text-white">OnMe</h1>

				<!-- Tagline -->
				<p class="mb-8 text-base text-pin-medium-gray">
					The AI-powered virtual fitting room. Try on any outfit instantly.
				</p>

				<!-- Auth Buttons -->
				<div class="flex flex-col gap-3">
					<a
						href="/auth/register"
						id="landing-signup-btn"
						class="flex w-full items-center justify-center rounded-pill bg-pin-red py-4 text-lg font-semibold text-white transition-colors duration-200 hover:bg-pin-red-hover"
					>
						Sign Up
					</a>

					<a
						href="/auth/login"
						id="landing-login-btn"
						class="flex w-full items-center justify-center rounded-pill bg-pin-light-gray py-4 text-lg font-semibold text-pin-dark-gray transition-colors duration-200 hover:bg-white"
					>
						Log In
					</a>
				</div>
			</div>
		</div>
	</div>
{/if}
