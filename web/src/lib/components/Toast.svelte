<script lang="ts">
	import { getToasts, dismissToast, type ToastType } from '$lib/stores/toast.svelte';

	function typeClasses(type: ToastType): string {
		switch (type) {
			case 'error':
				return 'bg-red-600/90 border-red-500/50';
			case 'warning':
				return 'bg-amber-600/90 border-amber-500/50';
			case 'success':
				return 'bg-emerald-600/90 border-emerald-500/50';
			case 'info':
			default:
				return 'bg-blue-600/90 border-blue-500/50';
		}
	}

	function typeIcon(type: ToastType): string {
		switch (type) {
			case 'error':
				return 'M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z';
			case 'warning':
				return 'M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z';
			case 'success':
				return 'M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z';
			case 'info':
			default:
				return 'm11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z';
		}
	}
</script>

{#if getToasts().length > 0}
	<div
		class="fixed bottom-6 right-6 z-[9999] flex flex-col-reverse gap-3"
		aria-live="polite"
		aria-label="Notifications"
	>
		{#each getToasts() as toast (toast.id)}
			<div
				class="flex min-w-72 max-w-sm items-start gap-3 rounded-2xl border px-4 py-3 shadow-2xl backdrop-blur-xl transition-all duration-300 animate-in slide-in-from-right {typeClasses(toast.type)}"
				role="alert"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
					stroke-width="1.5"
					stroke="currentColor"
					class="mt-0.5 h-5 w-5 shrink-0 text-white/90"
				>
					<path stroke-linecap="round" stroke-linejoin="round" d={typeIcon(toast.type)} />
				</svg>

				<p class="flex-1 text-sm font-medium text-white">{toast.message}</p>

				<button
					onclick={() => dismissToast(toast.id)}
					class="shrink-0 rounded-full p-0.5 text-white/70 transition-colors hover:text-white"
					aria-label="Dismiss notification"
				>
					<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
						<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
					</svg>
				</button>
			</div>
		{/each}
	</div>
{/if}

<style>
	@keyframes slide-in-from-right {
		from {
			opacity: 0;
			transform: translateX(100%);
		}
		to {
			opacity: 1;
			transform: translateX(0);
		}
	}

	.animate-in {
		animation: slide-in-from-right 0.3s ease-out;
	}
</style>
