"""FastAPI entry point for the Payroll Governance Lab teaching console."""
from __future__ import annotations

import argparse
import sys
from contextlib import asynccontextmanager
from pathlib import Path

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles
    from starlette.concurrency import run_in_threadpool
except ModuleNotFoundError as error:
    raise SystemExit(
        "Payroll UI dependencies are missing. Run `uv sync --extra ui` first."
    ) from error

HERE = Path(__file__).parent
UI = HERE / "ui"
sys.path.insert(0, str(HERE))

from governance_payroll_imports import load_local  # noqa: E402


bench = load_local("bench")
ui_service = load_local("ui_service")
LECTURES = ui_service.LECTURES
LabBusy = ui_service.LabBusy
reset = ui_service.reset
run_lecture = ui_service.run_lecture


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await run_in_threadpool(reset)
    yield


app = FastAPI(
    title="Payroll Governance Lab",
    description="Teaching API for Agent Design Patterns lectures 36-40.",
    version="1.0.0",
    lifespan=lifespan,
)
app.mount("/assets", StaticFiles(directory=UI), name="assets")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(UI / "index.html")


@app.get("/api/meta")
async def meta() -> dict:
    return {
        "title": "Payroll Governance Lab",
        "subtitle": "治理控制面教学工作台",
        "lectures": list(LECTURES.values()),
    }


@app.get("/api/state")
async def state() -> dict:
    return await run_in_threadpool(bench.state)


@app.get("/api/tables/{table}")
async def rows(table: str) -> dict:
    try:
        return {"table": table, "rows": await run_in_threadpool(bench.table_rows, table)}
    except KeyError as error:
        raise HTTPException(status_code=404, detail="unknown table") from error


@app.post("/api/reset")
async def reset_lab() -> dict:
    return await run_in_threadpool(reset)


@app.post("/api/run/{lecture}")
async def run(lecture: str, variant: bool = False) -> dict:
    try:
        return await run_in_threadpool(run_lecture, lecture, variant=variant)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="unknown lecture") from error
    except LabBusy as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


def main() -> None:
    parser = argparse.ArgumentParser(description="Start the Payroll Governance Lab UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8767)
    args = parser.parse_args()

    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
