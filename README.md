# OnMe

**OnMe** is an AI-powered virtual try-on system built as a final-year dissertation project for the University of Liverpool (2025–2026). It lets users upload a photo of themselves and a garment image, then generates a photorealistic composite showing how the clothing would look when worn. What makes it technically interesting is the combination of latent diffusion models (CatVTON, OOTDiffusion) with classical computer vision preprocessing — CLAHE lighting normalisation, morphological mask refinement, and Reinhard colour transfer — orchestrated through a real-time pipeline whose progress is visualised node-by-node in the browser.

---

## Architecture

```
┌─────────────────┐        HTTP        ┌─────────────────┐       API       ┌──────────────────┐
│                 │  ──────────────►   │                 │  ───────────►  │                  │
│   SvelteKit     │                    │    FastAPI       │                │  Replicate       │
│   Frontend      │  ◄──────────────   │    Backend       │  ◄───────────  │  GPU Cloud       │
│                 │     JSON/SSE       │                 │    Result URL  │                  │
└─────────────────┘                    └────────┬────────┘                └──────────────────┘
                                                │
                                                │ SQL
                                                ▼
                                       ┌─────────────────┐
                                       │     SQLite       │
                                       │     Database     │
                                       └─────────────────┘
```

## Pipeline

```
Person Image ──► Validate ──► CLAHE Lighting ──┐
                                                ├──► VTON Inference ──► Colour Correction ──► Result
Garment Image ─► Validate ──► Resize ──────────┘
```

---

## Tech Stack

| Layer          | Technology                                                        |
| -------------- | ----------------------------------------------------------------- |
| Frontend       | SvelteKit, TypeScript, Tailwind CSS, @xyflow/svelte               |
| Backend        | Python 3.11, FastAPI                                              |
| Database       | SQLite (raw SQL + dataclasses)                                    |
| Inference      | Replicate (CatVTON, OOTDiffusion)                                |
| Preprocessing  | OpenCV (CLAHE, morphological ops, Reinhard colour transfer)       |
| Evaluation     | SSIM, PSNR, LPIPS, CLIP, FID                                     |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- A [Replicate API token](https://replicate.com/account/api-tokens)

### Backend

```bash
cd api
cp .env.example .env
# Edit .env and add your REPLICATE_API_TOKEN
uv sync
uv run uvicorn api.main:app --reload
```

The API will be available at `http://localhost:8000`.

### Frontend

```bash
cd web
cp .env.example .env
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`.

### Running Tests

```bash
cd api
uv run python -m pytest tests/ -v
```

---

## Evaluation

The `eval/` directory contains offline evaluation scripts that compute quantitative image quality metrics between generated try-on results and ground truth images. Metrics computed:

- **SSIM** — Structural Similarity Index (perceived quality)
- **PSNR** — Peak Signal-to-Noise Ratio (pixel-level fidelity)
- **LPIPS** — Learned Perceptual Image Patch Similarity (deep perceptual distance)
- **CLIP Similarity** — Semantic alignment between generated and reference images
- **FID** — Fréchet Inception Distance (distribution-level realism)

```bash
cd eval
uv sync
python compute_metrics.py --results-dir <path> --ground-truth-dir <path> --output-json metrics.json
python compute_fid.py --results-dir <path> --ground-truth-dir <path>
python aggregate.py --metrics-dir <path> --output-json summary.json
```

---

## Project Structure

```
onme/
├── api/                        # FastAPI backend
│   ├── main.py                 # Application entry point
│   ├── config.py               # Environment-based settings
│   ├── database.py             # SQLite connection and schema
│   ├── models.py               # Domain dataclasses
│   ├── repository.py           # Data access layer
│   ├── schemas.py              # Pydantic response models
│   ├── routes/
│   │   ├── health.py           # Health-check endpoint
│   │   └── tryon.py            # Upload and job status endpoints
│   ├── services/
│   │   ├── pipeline.py         # Background job orchestrator
│   │   ├── preprocessing.py    # CLAHE, resize, mask refinement
│   │   ├── inference.py        # Replicate API integration
│   │   └── postprocessing.py   # Reinhard colour transfer
│   └── tests/
│       ├── test_e2e.py         # End-to-end smoke tests
│       ├── test_routes.py      # Route unit tests
│       ├── test_repository.py  # Repository unit tests
│       ├── test_preprocessing.py
│       └── test_postprocessing.py
├── web/                        # SvelteKit frontend
│   ├── src/
│   │   ├── routes/
│   │   │   ├── +page.svelte    # Home / upload page
│   │   │   ├── tryon/+page.svelte   # Pipeline visualisation
│   │   │   └── metrics/+page.svelte # Evaluation dashboard
│   │   └── lib/
│   │       ├── api.ts          # Backend API client
│   │       ├── pipeline.ts     # Pipeline node definitions
│   │       ├── types.ts        # TypeScript interfaces
│   │       └── nodes/
│   │           └── ImageNode.svelte  # Custom flow node
│   └── static/
├── eval/                       # Offline evaluation scripts
│   ├── compute_metrics.py      # SSIM, PSNR, LPIPS, CLIP
│   ├── compute_fid.py          # FID computation
│   └── aggregate.py            # Aggregate results across runs
└── README.md
```

---

## Screenshots

Screenshots will be added after the evaluation phase.

---

## License

MIT
