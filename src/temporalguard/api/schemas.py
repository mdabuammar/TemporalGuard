"""Pydantic request and response schemas for the TemporalGuard API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    question: str = Field(..., min_length=1)
    base_answer: str | None = None
    llm_provider: str | None = None
    model_name: str | None = None
    search_provider: str | None = None
    report_type: str = "dashboard"
    config: dict[str, Any] = Field(default_factory=dict)


class BatchAnalyzeItem(BaseModel):
    example_id: str | None = None
    question: str = Field(..., min_length=1)
    base_answer: str | None = None
    llm_provider: str | None = None
    model_name: str | None = None
    search_provider: str | None = None


class BatchAnalyzeRequest(BaseModel):
    items: list[BatchAnalyzeItem] = Field(..., min_length=1)
    llm_provider: str | None = None
    model_name: str | None = None
    search_provider: str | None = None
    report_type: str = "dashboard"
    config: dict[str, Any] = Field(default_factory=dict)


class ReportRequest(BaseModel):
    pipeline_output: dict[str, Any] = Field(default_factory=dict)
    report_type: str = "dashboard"
    max_evidence_items: int = Field(default=5, ge=0, le=50)


class EvaluateRequest(BaseModel):
    benchmark_examples: list[dict[str, Any]] = Field(default_factory=list)
    system_outputs: list[dict[str, Any]] = Field(default_factory=list)


class HealthResponse(BaseModel):
    service: str
    status: str
    version: str
