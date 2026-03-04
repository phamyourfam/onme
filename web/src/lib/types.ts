/** Mirrors the backend JobResponse schema. */
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

/** Data stored in each pipeline visualisation node. */
export interface PipelineNodeData {
	label: string;
	stage: string;
	imageUrl: string | null;
	status: 'idle' | 'processing' | 'complete' | 'failed';
	elapsedMs: number | null;
}

/** Pre-computed evaluation metrics loaded from metrics.json. */
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
