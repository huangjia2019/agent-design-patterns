"""FastAPI entry point for the Payroll Reflection Lab teaching console."""
from __future__ import annotations

import argparse
from contextlib import asynccontextmanager
from pathlib import Path

try:
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles
    from starlette.concurrency import run_in_threadpool
except ModuleNotFoundError as error:
    raise SystemExit(
        "Payroll UI dependencies are missing. Run `uv sync --extra ui` first."
    ) from error

from ui_service import (
    LECTURES,
    LabBusy,
    LabError,
    LabUnavailable,
    database_state,
    prepare_month_end_state,
    reset_database,
    run_lecture,
    table_rows,
)


HERE = Path(__file__).parent
UI = HERE / "ui"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await run_in_threadpool(prepare_month_end_state)
    yield


app = FastAPI(
    title="Payroll Reflection Lab",
    description="Teaching API for Agent Design Patterns lectures 26-30.",
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
        "title": "Payroll Reflection Lab",
        "subtitle": "反思模块教学控制台",
        "lectures": list(LECTURES.values()),
    }


@app.get("/api/state")
async def state() -> dict:
    return await run_in_threadpool(database_state)


@app.get("/api/tables/{table}")
async def rows(
    table: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=5, le=100),
    search: str = Query("", max_length=80),
) -> dict:
    try:
        return await run_in_threadpool(
            table_rows,
            table,
            page=page,
            page_size=page_size,
            search=search,
        )
    except KeyError as error:
        raise HTTPException(status_code=404, detail="unknown table") from error


@app.post("/api/database/month-end")
async def month_end() -> dict:
    try:
        return await run_in_threadpool(prepare_month_end_state)
    except LabBusy as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except LabError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.post("/api/database/reset")
async def reset() -> dict:
    try:
        return await run_in_threadpool(reset_database)
    except LabBusy as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except LabError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.post("/api/run/{lecture}")
async def run(lecture: str, variant: bool = Query(False)) -> dict:
    try:
        return await run_in_threadpool(run_lecture, lecture, variant=variant)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="unknown lecture") from error
    except LabUnavailable as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except LabBusy as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except LabError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


def main() -> None:
    parser = argparse.ArgumentParser(description="Start the Payroll Reflection Lab UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()

    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
