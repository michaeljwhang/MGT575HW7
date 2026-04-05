# Lecture deck → narrated video pipeline

Python pipeline that rasterizes **Lecture 17** slides (`Lecture_17_AI_screenplays.pdf`), runs agent steps (style profile, slide descriptions, premise, arc, per-slide narration), synthesizes speech, and muxes a single **MP4** with **ffmpeg**.

## Prerequisites

- Python 3.10+
- [ffmpeg](https://ffmpeg.org/) on your `PATH` (required for video mux/concat and for **pydub** when TTS responses are merged from chunks)
- API keys (see below)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Place **`Lecture_17_AI_screenplays.pdf`** in the repository root (assignment layout).

The repo includes a committed **`LectureTranscript`** (no extension) with enough sample text for the style step to run. Replace it with your **full** auto-generated transcript for the closest match to the instructor’s voice.

### Environment variables

Create a `.env` file (optional) or export variables in your shell.

| Variable | Purpose |
|----------|---------|
| `PIPELINE_LLM_PROVIDER` | `openai` (default) or `google` |
| `PIPELINE_TTS_PROVIDER` | `openai` (default), `elevenlabs`, or `gemini` (alias: `google`) |
| `OPENAI_API_KEY` | Required if using OpenAI for LLM or TTS |
| `OPENAI_MODEL` | Default `gpt-4o` |
| `OPENAI_TTS_MODEL` | Default `tts-1` |
| `OPENAI_TTS_VOICE` | Default `alloy` |
| `GOOGLE_API_KEY` | Required if `PIPELINE_LLM_PROVIDER=google` or `PIPELINE_TTS_PROVIDER=gemini` |
| `GOOGLE_MODEL` | Default `gemini-2.0-flash` |
| `GEMINI_TTS_MODEL` | Default `gemini-2.5-flash-preview-tts` ([Gemini TTS](https://ai.google.dev/gemini-api/docs/speech-generation)) |
| `GEMINI_TTS_VOICE` | Default `Kore` (see Google voice list for the TTS model) |
| `ELEVENLABS_API_KEY` | Required if `PIPELINE_TTS_PROVIDER=elevenlabs` |
| `ELEVENLABS_VOICE_ID` | Voice ID from ElevenLabs |
| `ELEVENLABS_MODEL` | Optional; default `eleven_multilingual_v2` |
| `PDF_RASTER_DPI` | Optional; default `150` |

## Run

From the repo root:

```bash
python run_lecture_pipeline.py
```

Options:

- `--pdf PATH` — override PDF location
- `--transcript PATH` — override transcript path
- `--skip-style` — skip regenerating `style.json` if it already exists

Each run creates `projects/project_YYYYMMDD_HHMMSS/` with JSON artifacts, `slide_images/`, `audio/`, and the final `<pdf_basename>.mp4` (e.g. `Lecture_17_AI_screenplays.mp4`).

## Repository layout

```
├── README.md
├── style.json                 # committed defaults; regenerated from LectureTranscript each run unless --skip-style
├── Lecture_17_AI_screenplays.pdf
├── LectureTranscript
├── requirements.txt
├── run_lecture_pipeline.py
├── lecture_agents/
└── projects/
    └── project_YYYYMMDD_HHMMSS/
        ├── premise.json
        ├── arc.json
        ├── slide_description.json
        ├── slide_description_narration.json
        ├── slide_images/      # generated; gitignored
        ├── audio/             # generated; gitignored
        └── Lecture_17_AI_screenplays.mp4
```

**Do not commit** generated PNG, MP3, or MP4 files; they are listed in `.gitignore`.

## Submitting

Initialize git, commit code and `Lecture_17_AI_screenplays.pdf` as required by the assignment, push to GitHub, and submit the repository URL.
