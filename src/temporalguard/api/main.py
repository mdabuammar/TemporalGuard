"""FastAPI backend for TemporalGuard."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from temporalguard.api.schemas import (
    AnalyzeRequest,
    BatchAnalyzeRequest,
    EvaluateRequest,
    HealthResponse,
    ReportRequest,
)
from temporalguard.evaluation.metrics import evaluate_pipeline_outputs
from temporalguard.pipeline.orchestrator import run_temporalguard_pipeline
from temporalguard.reporting.report_generator import generate_report
from temporalguard.utils.errors import make_error, safe_call


app = FastAPI(title="TemporalGuard API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(service="temporalguard-api", status="ok", version="0.1.0")


@app.post("/analyze")
def analyze(request: AnalyzeRequest) -> dict[str, Any]:
    result = safe_call(
        run_temporalguard_pipeline,
        question=request.question,
        base_answer=request.base_answer,
        llm_provider=None,
        search_provider=None,
        config=request.config,
        report_type=request.report_type,
        module="api.analyze",
        recoverable=False,
        error_type="pipeline_error",
    )
    if not result["ok"]:
        _raise_api_error(result["error"])
    return _json_object(result["result"])


@app.post("/batch-analyze")
def batch_analyze(request: BatchAnalyzeRequest) -> dict[str, Any]:
    outputs: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for item in request.items:
        result = safe_call(
            run_temporalguard_pipeline,
            question=item.question,
            base_answer=item.base_answer,
            llm_provider=None,
            search_provider=None,
            config=request.config,
            report_type=request.report_type,
            module="api.batch_analyze",
            recoverable=True,
            fallback=None,
            error_type="pipeline_error",
        )
        if result["ok"]:
            output = _json_object(result["result"])
            if item.example_id is not None:
                output["example_id"] = item.example_id
            outputs.append(output)
        else:
            error = dict(result["error"])
            error["details"] = dict(error.get("details") or {})
            error["details"]["example_id"] = item.example_id
            errors.append(error)
    return {
        "total_items": len(request.items),
        "successful_items": len(outputs),
        "failed_items": len(errors),
        "outputs": outputs,
        "errors": errors,
    }


@app.post("/report")
def report(request: ReportRequest) -> dict[str, Any]:
    result = safe_call(
        generate_report,
        request.pipeline_output,
        request.report_type,
        max_evidence_items=request.max_evidence_items,
        module="api.report",
        recoverable=False,
        error_type="report_error",
    )
    if not result["ok"]:
        _raise_api_error(result["error"])
    return _json_object(result["result"])


@app.post("/evaluate")
def evaluate(request: EvaluateRequest) -> dict[str, Any]:
    result = safe_call(
        evaluate_pipeline_outputs,
        request.benchmark_examples,
        request.system_outputs,
        module="api.evaluate",
        recoverable=False,
        error_type="evaluation_error",
    )
    if not result["ok"]:
        _raise_api_error(result["error"])
    return _json_object(result["result"])


def _raise_api_error(error: dict[str, Any] | None) -> None:
    detail = error or make_error("api_error", "Unknown API error.", "api", recoverable=False)
    raise HTTPException(status_code=500, detail=detail)


def _json_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {"result": value}
