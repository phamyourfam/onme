/* ── Centralised API Client with JWT Injection ──────────────────── */

import type {
	LoginResponse,
	RegisterResponse,
	AuthUser,
	GarmentResponse,
	MoodboardSummary,
	MoodboardDetail,
	JobStatus
} from './types';
import { addToast } from './stores/toast.svelte';

const API_BASE: string =
	(import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000';

/* ── Error type ─────────────────────────────────────────────────── */

export class ApiError extends Error {
	status: number;
	detail: string;

	constructor(status: number, detail: string) {
		super(detail);
		this.name = 'ApiError';
		this.status = status;
		this.detail = detail;
	}
}

/* ── User-friendly error messages by status code ────────────────── */

function getToastMessage(status: number, detail: string): { message: string; type: 'error' | 'warning' } {
	switch (status) {
		case 429:
			return { message: detail || 'Too many requests. Please slow down.', type: 'warning' };
		case 403:
			return { message: detail || 'Access denied.', type: 'warning' };
		case 500:
			return { message: 'An unexpected server error occurred.', type: 'error' };
		case 504:
			return { message: 'The AI inference engine timed out.', type: 'error' };
		default:
			if (status >= 500) {
				return { message: 'A server error occurred. Please try again.', type: 'error' };
			}
			return { message: detail || 'Something went wrong.', type: 'error' };
	}
}

/* ── Core request helper ────────────────────────────────────────── */

interface RequestOptions {
	body?: unknown;
	formData?: FormData;
	urlEncoded?: URLSearchParams;
	/** If true, suppress automatic toast on error. */
	silent?: boolean;
}

async function apiRequest<T>(
	method: string,
	path: string,
	options: RequestOptions = {}
): Promise<T> {
	const token = localStorage.getItem('onme_token');

	const headers: Record<string, string> = {};
	if (token) {
		headers['Authorization'] = `Bearer ${token}`;
	}

	let body: BodyInit | undefined;

	if (options.formData) {
		// Multipart — let browser set Content-Type with boundary
		body = options.formData;
	} else if (options.urlEncoded) {
		headers['Content-Type'] = 'application/x-www-form-urlencoded';
		body = options.urlEncoded;
	} else if (options.body !== undefined) {
		headers['Content-Type'] = 'application/json';
		body = JSON.stringify(options.body);
	}

	const res = await fetch(`${API_BASE}${path}`, { method, headers, body });

	if (!res.ok) {
		const errorBody = await res.json().catch(() => ({ detail: res.statusText }));
		const detail = typeof errorBody.detail === 'string'
			? errorBody.detail
			: res.statusText;

		// Auto-logout on 401 (token expired)
		if (res.status === 401) {
			localStorage.removeItem('onme_token');
			localStorage.removeItem('onme_user');
			window.dispatchEvent(new CustomEvent('onme:auth-expired'));
		}

		// Show toast for non-silent requests (skip auth-related 401s)
		if (!options.silent && res.status !== 401) {
			const { message, type } = getToastMessage(res.status, detail);
			addToast(message, type);
		}

		throw new ApiError(res.status, detail);
	}

	// Handle 204 No Content
	if (res.status === 204) {
		return undefined as T;
	}

	return res.json();
}

/* ── Build a full URL for an image path returned by the API ───── */

export function getImageUrl(path: string): string {
	if (path.startsWith('http')) return path;
	return `${API_BASE}${path}`;
}

/* ── Auth endpoints ─────────────────────────────────────────────── */

export async function login(email: string, password: string): Promise<LoginResponse> {
	// OAuth2PasswordRequestForm expects form-encoded with "username" field
	const params = new URLSearchParams();
	params.append('username', email);
	params.append('password', password);

	return apiRequest<LoginResponse>('POST', '/api/auth/login', { urlEncoded: params });
}

export async function register(email: string, password: string): Promise<RegisterResponse> {
	return apiRequest<RegisterResponse>('POST', '/api/auth/register', {
		body: { email, password }
	});
}

export async function getMe(): Promise<AuthUser> {
	return apiRequest<AuthUser>('GET', '/api/auth/me', { silent: true });
}

/* ── Garment endpoints ──────────────────────────────────────────── */

export async function getGarments(): Promise<GarmentResponse[]> {
	return apiRequest<GarmentResponse[]>('GET', `/api/garments/catalog`);
}

/* ── Moodboard endpoints ────────────────────────────────────────── */

export async function getMoodboards(): Promise<MoodboardSummary[]> {
	return apiRequest<MoodboardSummary[]>('GET', '/api/moodboards/');
}

export async function getMoodboard(id: string): Promise<MoodboardDetail> {
	return apiRequest<MoodboardDetail>('GET', `/api/moodboards/${id}`);
}

export async function createMoodboard(title?: string): Promise<MoodboardDetail> {
	return apiRequest<MoodboardDetail>('POST', '/api/moodboards/', {
		body: title ? { title } : {}
	});
}

export async function updateMoodboardTitle(
	id: string,
	title: string
): Promise<{ id: string; title: string, updated_at: string }> {
	return apiRequest<{ id: string; title: string, updated_at: string }>('PUT', `/api/moodboards/${id}/title`, {
		body: { title }
	});
}

export async function createMoodboardNode(
	moodboardId: string,
	node: any
): Promise<any> {
	return apiRequest<any>('POST', `/api/moodboards/${moodboardId}/nodes`, {
		body: node
	});
}

export async function updateMoodboardCanvas(
	id: string,
	canvasState: string
): Promise<{ id: string; updated_at: string }> {
	return apiRequest<{ id: string; updated_at: string }>('PUT', `/api/moodboards/${id}/canvas`, {
		body: { canvas_state: canvasState }
	});
}

export async function deleteMoodboard(id: string): Promise<void> {
	return apiRequest<void>('DELETE', `/api/moodboards/${id}`);
}

export async function deleteMoodboardNode(moodboardId: string, nodeId: string): Promise<void> {
	return apiRequest<void>('DELETE', `/api/moodboards/${moodboardId}/nodes/${nodeId}`, { silent: true });
}

export async function updateMoodboardNode(moodboardId: string, nodeId: string, payload: { x: number, y: number, width?: number, height?: number }): Promise<void> {
	return apiRequest<void>('PATCH', `/api/moodboards/${moodboardId}/nodes/${nodeId}`, {
		body: payload,
		silent: true
	});
}

/* ── Try-on endpoints ───────────────────────────────────────────── */

export async function submitTryOn(
	personFile: File,
	garmentFile: File,
	modelName: string
): Promise<JobStatus> {
	const form = new FormData();
	form.append('person', personFile);
	form.append('garment', garmentFile);
	form.append('model_name', modelName);

	return apiRequest<JobStatus>('POST', '/api/tryon', { formData: form });
}

export async function getJobStatus(id: string): Promise<JobStatus> {
	return apiRequest<JobStatus>('GET', `/api/tryon/${id}`);
}

export async function getJobHistory(): Promise<JobStatus[]> {
	return apiRequest<JobStatus[]>('GET', '/api/tryon/history');
}
