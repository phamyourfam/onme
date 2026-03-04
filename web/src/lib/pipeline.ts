import type { Node, Edge } from '@xyflow/svelte';
import type { PipelineNodeData } from './types';

/** Build a fresh set of pipeline nodes with idle status. */
export function createInitialNodes(): Node<PipelineNodeData>[] {
	return [
		{
			id: 'person_upload',
			type: 'imageNode',
			position: { x: 0, y: 0 },
			data: { label: 'Person Photo', stage: 'person_original', imageUrl: null, status: 'idle', elapsedMs: null }
		},
		{
			id: 'garment_upload',
			type: 'imageNode',
			position: { x: 0, y: 220 },
			data: { label: 'Garment', stage: 'garment_original', imageUrl: null, status: 'idle', elapsedMs: null }
		},
		{
			id: 'clahe',
			type: 'imageNode',
			position: { x: 280, y: 0 },
			data: { label: 'CLAHE Lighting', stage: 'person_clahe', imageUrl: null, status: 'idle', elapsedMs: null }
		},
		{
			id: 'garment_resize',
			type: 'imageNode',
			position: { x: 280, y: 220 },
			data: { label: 'Garment Resize', stage: 'garment_resized', imageUrl: null, status: 'idle', elapsedMs: null }
		},
		{
			id: 'inference',
			type: 'imageNode',
			position: { x: 560, y: 110 },
			data: { label: 'VTON Inference', stage: 'inference_raw', imageUrl: null, status: 'idle', elapsedMs: null }
		},
		{
			id: 'colour_correct',
			type: 'imageNode',
			position: { x: 840, y: 110 },
			data: { label: 'Colour Correction', stage: 'colour_corrected', imageUrl: null, status: 'idle', elapsedMs: null }
		}
	];
}

/** Static edge definitions connecting pipeline stages. */
export const pipelineEdges: Edge[] = [
	{ id: 'e-person-clahe', source: 'person_upload', target: 'clahe' },
	{ id: 'e-garment-resize', source: 'garment_upload', target: 'garment_resize' },
	{ id: 'e-clahe-inference', source: 'clahe', target: 'inference' },
	{ id: 'e-resize-inference', source: 'garment_resize', target: 'inference' },
	{ id: 'e-inference-colour', source: 'inference', target: 'colour_correct' }
];
