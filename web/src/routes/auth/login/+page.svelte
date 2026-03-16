<script lang="ts">
	import { goto } from '$app/navigation';
	import { loginAction, getIsAuthenticated } from '$lib/stores/auth.svelte';
	import { ApiError } from '$lib/api';

	let email = $state('');
	let password = $state('');
	let error = $state('');
	let loading = $state(false);

	// Redirect if already authenticated
	$effect(() => {
		if (getIsAuthenticated()) {
			goto('/catalog');
		}
	});

	async function handleSubmit(e: Event) {
		e.preventDefault();
		error = '';
		loading = true;

		try {
			await loginAction(email, password);
			goto('/catalog');
		} catch (err) {
			if (err instanceof ApiError) {
				error = err.detail;
			} else {
				error = 'An unexpected error occurred. Please try again.';
			}
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Log In — OnMe</title>
</svelte:head>

<div class="flex min-h-screen items-center justify-center bg-surface-primary px-4">
	<div class="w-full max-w-sm">
		<!-- Back / Logo -->
		<a
			href="/"
			class="mb-8 inline-flex items-center gap-2 text-sm text-pin-medium-gray transition-colors hover:text-white"
		>
			<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
				<path fill-rule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clip-rule="evenodd" />
			</svg>
			Back to OnMe
		</a>

		<!-- Heading -->
		<h1 class="mb-8 text-2xl font-bold text-white">Welcome back</h1>

		<!-- Form -->
		<form onsubmit={handleSubmit} class="flex flex-col gap-4">
			<div>
				<label for="login-email" class="mb-1 block text-sm text-pin-medium-gray">Email</label>
				<input
					id="login-email"
					type="email"
					bind:value={email}
					required
					placeholder="you@example.com"
					class="w-full rounded-gestalt bg-surface-card px-4 py-3 text-white placeholder-pin-medium-gray outline-none transition-all focus:ring-2 focus:ring-pin-red"
				/>
			</div>

			<div>
				<label for="login-password" class="mb-1 block text-sm text-pin-medium-gray">Password</label>
				<input
					id="login-password"
					type="password"
					bind:value={password}
					required
					placeholder="••••••••"
					class="w-full rounded-gestalt bg-surface-card px-4 py-3 text-white placeholder-pin-medium-gray outline-none transition-all focus:ring-2 focus:ring-pin-red"
				/>
			</div>

			{#if error}
				<p class="text-sm text-red-400">{error}</p>
			{/if}

			<button
				id="login-submit-btn"
				type="submit"
				disabled={loading}
				class="mt-2 flex w-full items-center justify-center rounded-pill bg-pin-red py-3 font-semibold text-white transition-colors hover:bg-pin-red-hover disabled:opacity-50 disabled:cursor-not-allowed"
			>
				{#if loading}
					<div class="mr-2 h-5 w-5 animate-spin rounded-full border-2 border-white/30 border-t-white"></div>
					Logging in...
				{:else}
					Log In
				{/if}
			</button>
		</form>

		<!-- Register link -->
		<p class="mt-6 text-center text-sm text-pin-medium-gray">
			Don't have an account?
			<a href="/auth/register" class="text-pin-red transition-colors hover:text-pin-red-hover">
				Sign up
			</a>
		</p>
	</div>
</div>
