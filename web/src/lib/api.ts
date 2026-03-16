/* ── Centralised API Client with JWT Injection ──────────────────── */

import type {
	LoginResponse,
	RegisterResponse,
	GarmentResponse,
	MoodboardSummary,
	MoodboardDetail,
	JobStatus,
	MetricsData
} from './types';

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

/* ── Core request helper ────────────────────────────────────────── */

interface RequestOptions {
	body?: unknown;
	formData?: FormData;
	urlEncoded?: URLSearchParams;
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
			window.dispatchEvent(new CustomEvent('onme:auth-expired'));
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

	return apiRequest<LoginResponse>('POST', '/auth/login', { urlEncoded: params });
}

export async function register(email: string, password: string): Promise<RegisterResponse> {
	return apiRequest<RegisterResponse>('POST', '/auth/register', {
		body: { email, password }
	});
}

/* ── Garment endpoints ──────────────────────────────────────────── */

export async function getGarments(category?: string): Promise<GarmentResponse[]> {
	const params = category ? `?category=${encodeURIComponent(category)}` : '';
	return apiRequest<GarmentResponse[]>('GET', `/garments${params}`);
}

/* ── Moodboard endpoints ────────────────────────────────────────── */

export async function getMoodboards(): Promise<MoodboardSummary[]> {
	return apiRequest<MoodboardSummary[]>('GET', '/moodboards');
}

export async function getMoodboard(id: string): Promise<MoodboardDetail> {
	return apiRequest<MoodboardDetail>('GET', `/moodboards/${id}`);
}

export async function createMoodboard(title?: string): Promise<MoodboardDetail> {
	return apiRequest<MoodboardDetail>('POST', '/moodboards', {
		body: title ? { title } : {}
	});
}

export async function updateMoodboardCanvas(
	id: string,
	canvasState: string
): Promise<MoodboardDetail> {
	return apiRequest<MoodboardDetail>('PUT', `/moodboards/${id}/canvas`, {
		body: { canvas_state: canvasState }
	});
}

export async function deleteMoodboard(id: string): Promise<void> {
	return apiRequest<void>('DELETE', `/moodboards/${id}`);
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
	form.append('model', modelName);

	return apiRequest<JobStatus>('POST', '/tryon', { formData: form });
}

export async function getJobStatus(id: string): Promise<JobStatus> {
	return apiRequest<JobStatus>('GET', `/tryon/${id}`);
}

export async function getJobHistory(): Promise<JobStatus[]> {
	return apiRequest<JobStatus[]>('GET', '/tryon/history');
}
