from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .agent import FreeAIAgent

app = FastAPI(title="FreeAI Agent", version="0.2.0")
agent = FreeAIAgent()


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Conversation/session identifier")
    question: str


class ReviseRequest(BaseModel):
    session_id: str
    feedback: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>FreeAI Chat</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 0; background: #f6f7fb; color: #111827; }
    .container { max-width: 860px; margin: 24px auto; padding: 16px; }
    .card { background: white; border-radius: 12px; padding: 16px; box-shadow: 0 2px 10px rgba(0,0,0,.08); }
    textarea, input { width: 100%; padding: 10px; border: 1px solid #d1d5db; border-radius: 8px; margin-top: 8px; }
    button { background: #2563eb; color: white; border: 0; border-radius: 8px; padding: 10px 14px; cursor: pointer; }
    button.secondary { background: #4b5563; }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    pre { background: #0f172a; color: #e2e8f0; padding: 12px; border-radius: 8px; white-space: pre-wrap; }
    ul { padding-left: 18px; }
  </style>
</head>
<body>
  <div class="container">
    <h1>FreeAI Web Chat</h1>
    <p>Ask a question, then ask follow-ups with the same session ID to use memory.</p>

    <div class="card">
      <label>Session ID</label>
      <input id="sessionId" value="demo-user-1" />

      <label style="display:block;margin-top:10px;">Question</label>
      <textarea id="question" rows="4" placeholder="Ask anything..."></textarea>

      <div style="margin-top:12px; display:flex; gap:10px;">
        <button onclick="sendQuestion()">Ask</button>
      </div>
    </div>

    <div class="card" style="margin-top:14px;">
      <h3>Answer</h3>
      <pre id="answer">No answer yet.</pre>
      <h4>Sources</h4>
      <ul id="sources"></ul>
      <h4>Memory Context Used</h4>
      <ul id="context"></ul>
    </div>

    <div class="card" style="margin-top:14px;">
      <h3>Revise Last Answer</h3>
      <textarea id="feedback" rows="3" placeholder="e.g. Make it shorter and focus on practical steps"></textarea>
      <div style="margin-top:12px;">
        <button class="secondary" onclick="reviseAnswer()">Revise</button>
      </div>
    </div>
  </div>

  <script>
    async function sendQuestion() {
      const session_id = document.getElementById('sessionId').value.trim();
      const question = document.getElementById('question').value.trim();
      if (!session_id || !question) return;

      const res = await fetch('/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ session_id, question })
      });
      const data = await res.json();

      document.getElementById('answer').textContent = data.answer || 'No answer';

      const sources = document.getElementById('sources');
      sources.innerHTML = '';
      (data.sources || []).forEach((s) => {
        const li = document.createElement('li');
        li.innerHTML = `<a href="${s.url}" target="_blank" rel="noreferrer">${s.title}</a> — ${s.snippet || ''}`;
        sources.appendChild(li);
      });

      const context = document.getElementById('context');
      context.innerHTML = '';
      (data.context_used || []).forEach((c) => {
        const li = document.createElement('li');
        li.textContent = `Q: ${c.question} | A: ${(c.answer || '').slice(0, 120)}...`;
        context.appendChild(li);
      });
    }

    async function reviseAnswer() {
      const session_id = document.getElementById('sessionId').value.trim();
      const feedback = document.getElementById('feedback').value.trim();
      if (!session_id || !feedback) return;

      const res = await fetch('/revise', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ session_id, feedback })
      });
      const data = await res.json();
      document.getElementById('answer').textContent = data.revised_answer || 'No revised answer';
    }
  </script>
</body>
</html>
"""


@app.post("/chat")
def chat(req: ChatRequest) -> dict:
    result = agent.answer(req.session_id, req.question)
    return {
        "answer": result.answer,
        "confidence": result.confidence,
        "sources": [s.__dict__ for s in result.sources],
        "context_used": [c.__dict__ for c in result.context_used],
        "transparency_notes": result.transparency_notes,
    }


@app.post("/revise")
def revise(req: ReviseRequest) -> dict[str, str]:
    revised = agent.revise_last_answer(req.session_id, req.feedback)
    return {"revised_answer": revised}
