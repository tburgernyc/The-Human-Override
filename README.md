# The Human Override
A faceless, premium-first “sleek dystopian” Shorts pipeline that turns episode YAML into:
- validation results
- shotlists + manifests
- render folder scaffolds
- a styled “minimal Apple-black glass” animatic MP4 (FFmpeg)

## Concept
- Channel: The Human Override
- Series: ONE CLICK
- Season 1: HOUSING MODE
- Runtime: 75–92s
- Engine: permission → consequence → A/B choice

## Repository map
- `/episodes` — YAML show-control files (S01E01–S01E10)
- `/tools/tho.py` — CLI: validate, shotlist, manifest, init-episode, animatic
- `/assets` — UI overlays (SVG sources + exported PNG), SFX buckets, VO
- `/renders` — per-episode outputs (created by CLI)
- `/scripts` — optional batch scripts (Inkscape export, whisper captions, final FFmpeg normalize/burn)

## Quickstart (Windows)
1) Copy `config.local.example.json` to `config.local.json` and set `"ffmpeg"` path.
2) Create venv + install:
   - `tools\\setup_venv_windows.bat`

3) Validate an episode:
   - `.venv\\Scripts\\python tools\\tho.py validate episodes\\season01_housing_mode\\ep01.yaml`

4) Initialize the render folder + outputs:
   - `.venv\\Scripts\\python tools\\tho.py init-episode S01E01 --episode-yaml episodes\\season01_housing_mode\\ep01.yaml`

5) Generate a “minimal glass” animatic MP4:
   - `.venv\\Scripts\\python tools\\tho.py animatic S01E01 --episode-yaml episodes\\season01_housing_mode\\ep01.yaml --run`

Outputs:
- `renders\\season01_housing_mode\\S01E01\\shotlist.md`
- `renders\\season01_housing_mode\\S01E01\\asset_manifest.json`
- `renders\\season01_housing_mode\\S01E01\\animatic.mp4`

## Notes
- UI overlays are optional. If `assets/ui/png/<ui_component>.png` exists, the animatic overlays it.
- VO is optional. If you place a WAV at `renders/.../vo_mix.wav`, you can pass `--vo` to `animatic`.

## Pre-flight Check
Before running the pipeline, verify your environment (FFmpeg, Inkscape, etc.) is correctly configured:
```bat
scripts\check_prereqs.bat
```

## One-Command Pipeline
Run the full production flow (SVG gen -> PNG export -> validation -> render -> thumb -> shorts):

```bat
scripts\make_all.bat episodes\season01_housing_mode\ep01.yaml S01E01
```

> **Note**: This pipeline requires **FFmpeg** and **Inkscape** to be installed and available in your PATH (or configured via `config.local.json` / ENV vars).
> To run in a dev/test environment without these tools, set `USE_MOCKS=1`:
> ```bat
> set USE_MOCKS=1
> scripts\make_all.bat ...
> ```

## Testing & Quality
Run the automated test suite to verify toolchain integrity:
```bat
python -m pytest tests/test_p0_suite.py
```

## Guardrails
- UI must be original. Do not copy real OS/bank screens 1:1.
- Scenarios are fictional; avoid naming real individuals or properties.
