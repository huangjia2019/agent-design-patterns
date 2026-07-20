"""FastAPI entry point for the Composition Selection Workbench."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles
    from starlette.concurrency import run_in_threadpool
except ModuleNotFoundError as error:
    raise SystemExit(
        "Composition UI dependencies are missing. Run `uv sync --extra ui` first."
    ) from error


HERE = Path(__file__).parent
UI = HERE / "ui"
sys.path.insert(0, str(HERE))

from ui_service import LabBusy, meta, run  # noqa: E402


app = FastAPI(
    title="Pattern Composition Lab",
    description="Teaching API for pattern selection and architecture evidence.",
    version="1.0.0",
)
app.mount("/assets", StaticFiles(directory=UI), name="assets")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(UI / "index.html")


@app.get("/api/meta")
async def get_meta() -> dict:
    return meta()


@app.get("/api/state")
async def state(scenario: str = "independent") -> dict:
    try:
        return await run_in_threadpool(run, scenario)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="unknown scenario") from error


@app.post("/api/run/{scenario}")
async def run_experiment(scenario: str) -> dict:
    try:
        return await run_in_threadpool(run, scenario)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="unknown scenario") from error
    except LabBusy as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Start the Composition Selection Workbench."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8041)
    args = parser.parse_args()

    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
