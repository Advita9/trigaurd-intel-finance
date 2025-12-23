import uuid
from typing import Annotated
from fastapi import FastAPI, Form
from google.adk.runners import Runner
from google.genai.types import Content, Part

from finagent_agent.agent import get_agent
from services.redis_memory import redis_memory

APP_NAME = "finagent_api"
app = FastAPI()

agent = get_agent()

@app.post("/chat")
async def chat(
    prompt: Annotated[str, Form()],
    session_id: Annotated[str | None, Form()] = None,
):
    session_id = session_id or str(uuid.uuid4())

    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=None,     # optional for now
        artifact_service=None,    # optional for now
    )

    new_message = Content(
        role="user",
        parts=[Part.from_text(text=prompt)]
    )

    final_text = ""

    async for event in runner.run_async(
        user_id="user",
        session_id=session_id,
        new_message=new_message,
    ):
        if event.is_final_response():
            for part in event.content.parts:
                if part.text:
                    final_text += part.text

    # Parse JSON from ADK
    result = json.loads(final_text)

    # Store in Redis
    redis_memory.set_intent(result["intent"])
    redis_memory.set_plan(result["plan"])
    redis_memory.set_current_step(0)

    return {
        "session_id": session_id,
        "intent": result["intent"],
        "plan": result["plan"],
        "status": "ready_to_execute"
    }

