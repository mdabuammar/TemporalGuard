"""API schemas for TemporalGuard."""

from __future__ import annotations

from pydantic import BaseModel


class QuestionRequest(BaseModel):
    question: str


class AnswerResponse(BaseModel):
    question: str
    status: str
    answer: str
