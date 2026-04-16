<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import {
		getIsAuthenticated,
		getAuthUser,
		logoutAction
	} from '$lib/stores/auth.svelte';
	import { getMoodboards, createMoodboard } from '$lib/api';
	import type { MoodboardSummary } from '$lib/types';

	import { invalidateAll } from '$app/navigation';

	let { children } = $props();

	let sidebarOpen = $state(false);
	let moodboards = $state<MoodboardSummary[]>([]);
	let loadingMoodboards = $state(false);

	// Reactive statement to re-fetch when page changes
	$effect(() => {
		if (getIsAuthenticated()) {
			fetchMoodboards();
		}

		const handleRefresh = () => fetchMoodboards();
		window.addEventListener('moodboards:refresh', handleRefresh);
		return () => window.removeEventListener('moodboards:refresh', handleRefresh);
	});

	// Redirect unauthenticated users
	$effect(() => {
		if (!getIsAuthenticated()) {
			goto('/');
		}
	});

	async function fetchMoodboards() {
		loadingMoodboards = true;
		try {
			moodboards = await getMoodboards();
		} catch {
			// Fail silently — empty list
			moodboards = [];
		} finally {
			loadingMoodboards = false;
		}
	}

	async function handleNewMoodboard() {
		try {
			const mb = await createMoodboard();
			goto(`/moodboard/${mb.id}`);
		} catch {
			// Could show error toast in future
		}
	}

	function handleLogout() {
		logoutAction();
		goto('/');
	}

	function closeSidebar() {
		sidebarOpen = false;
	}

	// Navigation items
	const navItems = [
		{
			label: 'Garment Catalog',
			href: '/catalog',
			icon: `<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"/></svg>`
		},
		{
			label: 'Try On',
			href: '/tryon',
			icon: `<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clip-rule="evenodd"/></svg>`
		},
		{
			label: 'Metrics',
			href: '/metrics',
			icon: `<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"/></svg>`
		}
	];

	function isActive(href: string): boolean {
		return page.url.pathname.startsWith(href);
	}
</script>

{#if getIsAuthenticated()}
	<div class="flex h-screen overflow-hidden bg-surface-primary text-white">
		<!-- MOBILE HAMBURGER -->
		<button
			id="sidebar-toggle"
			onclick={() => (sidebarOpen = !sidebarOpen)}
			class="fixed left-4 top-4 z-40 flex h-10 w-10 items-center justify-center rounded-gestalt bg-surface-card text-white shadow-gestalt md:hidden"
			aria-label="Toggle sidebar"
		>
			<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
				{#if sidebarOpen}
					<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
				{:else}
					<path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
				{/if}
			</svg>
		</button>

		<!-- MOBILE BACKDROP -->
		{#if sidebarOpen}
			<div
				class="fixed inset-0 z-40 bg-black/50 md:hidden"
				onclick={closeSidebar}
				onkeydown={(e) => e.key === 'Escape' && closeSidebar()}
				role="button"
				tabindex="-1"
				aria-label="Close sidebar"
			></div>
		{/if}

		<!-- LEFT SIDEBAR -->
		<aside
			class="fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-white/10 bg-surface-sidebar transition-transform duration-300 md:static md:translate-x-0
			{sidebarOpen ? 'translate-x-0' : '-translate-x-full'}"
		>
			<!-- SIDEBAR TOP -->
			<div class="p-4">
				<a href="/catalog" class="text-xl font-bold tracking-tight">OnMe</a>

				<button
					id="new-moodboard-btn"
					onclick={handleNewMoodboard}
					class="mt-4 flex w-full items-center justify-center gap-2 rounded-gestalt bg-surface-card py-3 text-sm font-medium transition-colors hover:bg-surface-hover"
				>
					<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
						<path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" />
					</svg>
					New Moodboard
				</button>
			</div>

			<!-- SIDEBAR MIDDLE -->
			<div class="flex-1 overflow-y-auto px-2 py-4">
				<!-- Navigation -->
				<nav class="mb-6 flex flex-col gap-1">
					{#each navItems as item}
						<a
							href={item.href}
							onclick={closeSidebar}
							class="flex items-center gap-3 rounded-gestalt px-3 py-2 text-sm transition-colors
							{isActive(item.href) ? 'bg-surface-hover text-white' : 'text-pin-medium-gray hover:bg-surface-hover hover:text-white'}"
						>
							{@html item.icon}
							{item.label}
						</a>
					{/each}
				</nav>

				<!-- Moodboard History -->
				<div>
					<h3 class="mb-2 px-3 text-xs uppercase tracking-wider text-pin-medium-gray">
						Recent
					</h3>

					{#if loadingMoodboards}
						<div class="flex flex-col gap-1 px-3">
							{#each Array(3) as _}
								<div class="h-8 animate-pulse rounded-gestalt bg-surface-card"></div>
							{/each}
						</div>
					{:else if moodboards.length === 0}
						<p class="px-3 text-xs italic text-pin-medium-gray">
							No moodboards yet
						</p>
					{:else}
						<div class="flex flex-col gap-0.5">
							{#each moodboards as mb (mb.id)}
								<a
									href="/moodboard/{mb.id}"
									onclick={closeSidebar}
									class="truncate rounded-gestalt px-3 py-2 text-sm text-pin-medium-gray transition-colors hover:bg-surface-hover hover:text-white"
								>
									{mb.title}
								</a>
							{/each}
						</div>
					{/if}
				</div>
			</div>

			<!-- SIDEBAR BOTTOM -->
			<div class="border-t border-white/10 p-4">
				{#if getAuthUser()}
					<p class="truncate text-sm text-pin-medium-gray">
						{getAuthUser()?.email}
					</p>
					<p class="mt-1 text-xs text-pin-medium-gray">
						Credits: {getAuthUser()?.credits_remaining ?? 0}
					</p>
				{/if}
				<button
					id="logout-btn"
					onclick={handleLogout}
					class="mt-3 text-sm text-pin-medium-gray transition-colors hover:text-white"
				>
					Log out
				</button>
			</div>
		</aside>

		<!-- MAIN VIEW -->
		<main class="flex-1 overflow-y-auto">
			{@render children()}
		</main>
	</div>
{/if}
