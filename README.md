# FreeAI Agent

A lightweight internet-grounded AI assistant API that:

- answers questions using multiple web sources,
- retains past Q&A per session,
- supports follow-up questions with memory context,
- lets users revise/adjust previous answers,
- returns transparent evidence and confidence indicators.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn freeai_agent.app:app --reload
```

Open `http://127.0.0.1:8000/docs` for Swagger UI.

## API

### `POST /chat`

Request:

```json
{
  "session_id": "user-123",
  "question": "What are the health impacts of microplastics?"
}
```

Response includes:

- `answer`
- `confidence`
- `sources` (title, url, snippet)
- `context_used` (prior relevant Q&A)
- `transparency_notes`

### `POST /revise`

Allows the user to request answer changes.

```json
{
  "session_id": "user-123",
  "feedback": "Make this shorter and focus only on WHO guidance."
}
```

## Notes on limitations

- "Thinking ability" is implemented as explicit evidence fusion plus lightweight ranking logic.
- Bias cannot be fully eliminated; the agent mitigates it by requiring multiple independent sources and exposing evidence.
- "Openly reveal everything" is implemented as transparent source listing and confidence reporting.
