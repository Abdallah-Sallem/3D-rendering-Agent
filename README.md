# Render Pipeline Agent

This workspace contains a small Blender automation pipeline plus two AI-assisted generators for architectural and concept renders.

## What’s inside

- `pipeline_agent.py` runs a deterministic two-step Blender pipeline.
- `ai_coding_agent.py` asks Gemini to generate Blender Python for a user prompt.
- `bim_architect_agent.py` asks Mistral to turn architectural source data into Blender Python.
- `mcp_client.py` sends Blender Python over a local socket bridge on `localhost:9876`.

## Folder layout

- `input/` stores source SVG floor plans.
- `outbox/` stores generated scripts, `.blend` files, and rendered images.
- `comparison/` stores the BIM comparison output written by `bim_architect_agent.py`.

## Input files

- `input/compact-two-bedroom-house-plan.svg`
- `input/family-home-with-patio-deck.svg`
- `input/modern-u-shaped-house-plan.svg`

## Requirements

- Python 3.10+.
- Blender running with the MCP bridge listening on `localhost:9876`.
- `GEMINI_API_KEY` for `ai_coding_agent.py`.
- `MISTRAL_API_KEY` for `bim_architect_agent.py`.
- Internet access for the model-backed scripts.

## How the pipeline works

`pipeline_agent.py` generates a building script, runs it in Blender, then generates a render script and produces two renders:

- `outbox/step1_build.py`
- `outbox/step2_render.py`
- `outbox/auto_building.blend`
- `outbox/render_top.png`
- `outbox/render_persp.png`

`ai_coding_agent.py` follows the same build-then-render flow, but the Blender code is generated from a text prompt.

`bim_architect_agent.py` is designed for architectural inputs such as SVG, DXF, IFC, JSON, PNG, or PDF and writes its generated script to `outbox/bim_generated_build.py` before saving a `.blend` file in `comparison/`.

## Usage

Run the deterministic pipeline:

```bash
python pipeline_agent.py
```

Run the text-prompt generator:

```bash
python ai_coding_agent.py "Modern two-bedroom house with a courtyard"
```

Run the BIM-oriented generator against a source file or raw plan text:

```bash
python bim_architect_agent.py input/modern-u-shaped-house-plan.svg
```

## Notes

- The generated scripts are intentionally written into `outbox/` so the intermediate Blender code is easy to inspect.
- If you change the Blender bridge host or port, update `mcp_client.py`.