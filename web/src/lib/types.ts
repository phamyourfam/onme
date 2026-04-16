/* ── API Contract Types ─────────────────────────────────────────── */

/** Authenticated user profile. */
export interface AuthUser {
	id: string;
	email: string;
	credits_remaining: number;
}

/** Virtual try-on job status (mirrors backend JobResponse). */
export interface JobStatus {
	id: string;
	status:
		| 'pending'
		| 'preprocessing'
		| 'inferring'
		| 'postprocessing'
		| 'complete'
		| 'failed';
	model_name: string;
	current_stage: string | null;
	created_at: string;
	completed_at: string | null;
	result_url: string | null;
	error_message: string | null;
	intermediates: Record<string, string> | null;
	timing: {
		preprocessing_ms: number | null;
		inference_ms: number | null;
		postprocessing_ms: number | null;
	} | null;
}

/** A garment returned by the catalog API. */
export interface GarmentResponse {
	id: string;
	title: string;
	image_url: string;
	category: string;
	source: string;
}

/** Moodboard list item (summary). */
export interface MoodboardSummary {
	id: string;
	title: string;
	updated_at: string;
}

/** Full moodboard detail with canvas state. */
export interface MoodboardDetail {
	id: string;
	title: string;
	canvas_state: string | null;
	created_at: string;
	updated_at: string;
}

/** Evaluation metrics data structure. */
export interface MetricsData {
	models: {
		name: string;
		fid: number | null;
		lpips: number | null;
		ssim: number | null;
		psnr: number | null;
		clip_score: number | null;
		avg_latency_ms: number | null;
		sample_count: number;
	}[];
	ablation: {
		with_clahe: { ssim: number | null; lpips: number | null; psnr: number | null };
		without_clahe: { ssim: number | null; lpips: number | null; psnr: number | null };
		with_colour_correction: { ssim: number | null; lpips: number | null; psnr: number | null };
		without_colour_correction: {
			ssim: number | null;
			lpips: number | null;
			psnr: number | null;
		};
	};
	last_updated: string | null;
}

/** Response from POST /auth/login. */
export interface LoginResponse {
	access_token: string;
	token_type: string;
}

/** Response from POST /auth/register. */
export interface RegisterResponse {
	id: string;
	email: string;
	token: string;
}
