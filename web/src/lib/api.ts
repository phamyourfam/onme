import type { JobStatus } from './types';

const API_BASE: string =
	(import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000';

/** Submit a virtual try-on job and return the initial status. */
export async function submitTryOn(
	person: File,
	garment: File,
	model: string
): Promise<JobStatus> {
	const form = new FormData();
	form.append('person', person);
	form.append('garment', garment);
	form.append('model', model);

	const res = await fetch(`${API_BASE}/tryon`, { method: 'POST', body: form });
	if (!res.ok) {
		const body = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(body.detail ?? 'Submission failed');
	}
	return res.json();
}

/** Poll the backend for a job's current status. */
export async function getJobStatus(id: string): Promise<JobStatus> {
	const res = await fetch(`${API_BASE}/tryon/${id}`);
	if (!res.ok) {
		const body = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(body.detail ?? 'Failed to fetch job status');
	}
	return res.json();
}

/** Build a full URL for an image path returned by the API. */
export function getImageUrl(path: string): string {
	return `${API_BASE}${path}`;
}
