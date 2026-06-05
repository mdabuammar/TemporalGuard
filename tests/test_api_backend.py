from temporalguard.api.schemas import AnswerResponse, QuestionRequest


def test_api_schema_round_trip():
    request = QuestionRequest(question="What is TemporalGuard?")
    response = AnswerResponse(question=request.question, status="scaffold", answer="ok")
    assert response.status == "scaffold"
