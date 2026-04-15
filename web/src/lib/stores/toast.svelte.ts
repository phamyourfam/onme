/* ── Toast Store (Svelte 5 Runes) ───────────────────────────────── */

export type ToastType = 'error' | 'warning' | 'success' | 'info';

export interface Toast {
	id: string;
	message: string;
	type: ToastType;
	duration: number;
}

const DEFAULT_DURATION = 5000;

let toasts = $state<Toast[]>([]);

let _counter = 0;

export function getToasts(): Toast[] {
	return toasts;
}

export function addToast(
	message: string,
	type: ToastType = 'info',
	duration: number = DEFAULT_DURATION
): string {
	const id = `toast-${++_counter}-${Date.now()}`;
	const toast: Toast = { id, message, type, duration };

	toasts = [...toasts, toast];

	if (duration > 0) {
		setTimeout(() => {
			dismissToast(id);
		}, duration);
	}

	return id;
}

export function dismissToast(id: string): void {
	toasts = toasts.filter((t) => t.id !== id);
}

export function clearToasts(): void {
	toasts = [];
}
