"""FastAPI application for TemporalGuard."""

from __future__ import annotations

from fastapi import FastAPI

from temporalguard.api.schemas import AnswerResponse, QuestionRequest
from temporalguard.pipeline.orchestrator import run_pipeline

app = FastAPI(title="TemporalGuard")


@app.post("/answer", response_model=AnswerResponse)
def answer(request: QuestionRequest) -> AnswerResponse:
    result = run_pipeline(request.question)
    return AnswerResponse(**result)
