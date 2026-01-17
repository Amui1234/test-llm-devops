from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
import json
import db
from llm import chat

app = FastAPI(title="Rabo WebApp for Containers")

class MessageIn(BaseModel):
    message: str

@app.on_event("startup")
def startup():
    db.init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/sessions")
def create_session():
    session_id = str(uuid.uuid4())
    db.create_session(session_id)
    return {"session_id": session_id}

@app.post("/sessions/{session_id}/message")
async def send_message(session_id: str, payload: MessageIn):
    if not db.session_is_active(session_id):
        raise HTTPException(status_code=404, detail="Session not found or ended")

    user_text = (payload.message or "").strip()

    if user_text.lower() in {"end", "exit"}:
        db.end_session(session_id)
        return {"ended": True, "assistant": {"answer": "Session ended.", "actions": [], "follow_up_questions": []}}

    db.add_message(session_id, "user", user_text)
    history = db.get_history(session_id, limit=20)

    try:
        model_content = await chat(history)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM failed: {type(e).__name__}")

    try:
        structured = json.loads(model_content)
        answer = structured.get("answer", "")
        actions = structured.get("actions", [])
        followups = structured.get("follow_up_questions", [])
    except Exception:
        answer, actions, followups = model_content, [], []

    db.add_message(session_id, "assistant", model_content)

    return {"ended": False, "assistant": {"answer": answer, "actions": actions, "follow_up_questions": followups}}
