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

from ui_service import (  # noqa: E402
    LabBusy,
    capstone_meta,
    meta,
    run,
    run_capstone_workbench,
    run_six_step,
    six_step_meta,
)


app = FastAPI(
    title="Pattern Composition Lab",
    description="Teaching API for pattern selection and architecture evidence.",
    version="1.0.0",
)
app.mount("/assets", StaticFiles(directory=UI), name="assets")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(UI / "index.html")


@app.get("/42", include_in_schema=False)
async def six_step_index() -> FileResponse:
    return FileResponse(UI / "six-step.html")


@app.get("/43", include_in_schema=False)
async def capstone_index() -> FileResponse:
    return FileResponse(UI / "capstone.html")


@app.get("/api/meta")
async def get_meta() -> dict:
    return meta()


@app.get("/api/42/meta")
async def get_six_step_meta() -> dict:
    return six_step_meta()


@app.get("/api/43/meta")
async def get_capstone_meta() -> dict:
    return capstone_meta()


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


@app.get("/api/42/state")
async def six_step_state(view: str = "seams") -> dict:
    try:
        return await run_in_threadpool(run_six_step, view)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="unknown view") from error


@app.post("/api/42/run/{view}")
async def run_six_step_experiment(view: str) -> dict:
    try:
        return await run_in_threadpool(run_six_step, view)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="unknown view") from error
    except LabBusy as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.get("/api/43/state")
async def capstone_state(mode: str = "bound") -> dict:
    try:
        return await run_in_threadpool(run_capstone_workbench, mode)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="unknown mode") from error


@app.post("/api/43/run/{mode}")
async def run_capstone_experiment(mode: str) -> dict:
    try:
        return await run_in_threadpool(run_capstone_workbench, mode)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="unknown mode") from error
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
