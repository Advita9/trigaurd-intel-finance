from fastapi import FastAPI
from agents.intent_agent import intent_agent
from services.redis_client import redis_client
from agents.planner_agent import planner_agent
from agents.executor_agent import ExecutorAgent
from services.redis_memory import redis_memory
from agents.intent_agent.agent import intent_agent
from agents.planner_agent.agent import planner_agent
from services.redis_memory import redis_memory

app = FastAPI()
executor = ExecutorAgent()

@app.post("/execute")
def execute_plan():
    print("DEBUG: /execute endpoint called")
    executor.run()
    print("DEBUG: executor.run() finished")
    return {"status": "execution_started"}
    
# @app.post("/plan")
# def create_plan():
#     plan = planner_agent.process()
#     return {"status": "ok", "plan": plan}

# @app.post("/intent")
# def parse_intent(payload: dict):
#     user_text = payload.get("text")
#     intent = intent_agent.process(user_text)
#     return {"status": "ok", "intent": intent}

from fastapi import APIRouter

router = APIRouter()

@router.post("/intent")
async def extract_intent(payload: dict):
    text = payload["text"]

    result = await intent_agent.run(text)

    redis_memory.set_intent(result.data.dict())
    return result.data
@router.post("/plan")
async def create_plan():
    intent = redis_memory.get_intent()

    result = await planner_agent.run(
        f"Create execution plan for intent: {intent}"
    )

    redis_memory.set_plan([step.dict() for step in result.data.steps])
    redis_memory.set_current_step(0)

    return result.data

@app.post("/approve")
def approve_action():
    """
    Called when user approves a paused high-risk action.
    """
    redis_memory.set_paused(False)
    redis_memory.clear_risk()
    redis_memory.push_log("User approved action")
    # redis_memory.increment_step()

    return {
        "status": "approved",
        "message": "Execution resumed"
    }

@app.post("/reject")
def reject_action():
    """
    User rejects the action → terminate workflow safely
    """
    redis_memory.set_paused(False)
    redis_memory.set_current_step(9999)  # force exit
    redis_memory.set_risk("User rejected transaction")

    return {
        "status": "rejected",
        "message": "Workflow terminated"
    }
@app.get("/state")
def get_state():
    return {
        "paused": redis_memory.is_paused(),
        "risk": redis_memory.get_risk(),
        "logs": redis_memory.get_logs(),
        "screenshot": redis_memory.get_screenshot()
    }


