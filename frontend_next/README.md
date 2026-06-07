# TemporalGuard Next.js Frontend

Production-oriented React/Next.js frontend for TemporalGuard. The existing Streamlit app remains available as a legacy/demo frontend.

## Install

```bash
cd frontend_next
npm install
```

## Configure Backend URL

Create `.env.local` if you need a custom backend URL:

```text
NEXT_PUBLIC_TEMPORALGUARD_API_URL=http://127.0.0.1:8000
```

Do not put OpenRouter, Tavily, OpenAI, Gemini, Anthropic, or Brave keys in the frontend. Provider API keys stay in the backend `.env` only.

## Run

Start the TemporalGuard FastAPI backend:

```bash
uvicorn temporalguard.api.main:app --reload
```

Start the frontend:

```bash
cd frontend_next
npm run dev
```

Open:

```text
http://localhost:3000
```

## Demo Mode

Demo Mode runs in the browser with local mock results. It does not require the FastAPI backend.

Included demo cases:

- latest Python version
- binary search
- visa rule

## Backend Mode

Use `Local Pipeline` or `Backend + Model API` to call:

```text
POST http://127.0.0.1:8000/analyze
```

Request fields sent by the frontend:

- `question`
- `base_answer`
- `llm_provider`
- `model_name`
- `search_provider`
- `report_type`

If `Use my own answer` is enabled, the frontend sends `base_answer` and the backend does not call the model provider. If disabled, the selected model provider generates the first answer before TemporalGuard verifies it.

## Provider Notes

- OpenRouter, OpenAI, Gemini, Anthropic, Tavily, and Brave keys are read by the backend environment only.
- The frontend never asks for API keys.
- Evidence provider `None` is allowed, but fresh/current claims may receive low trust.

## Build

```bash
npm run build
```
