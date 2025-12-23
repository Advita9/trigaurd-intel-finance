from fastapi import APIRouter
from agents.intent_agent import intent_agent
from agents.planner_agent import planner_agent
from agents.executor_agent import ExecutorAgent
from services.redis_memory import redis_memory
from agents.planner_agent import generate_plan

router = APIRouter()
executor = ExecutorAgent()


# -----------------------------
# INTENT
# -----------------------------
@router.post("/intent")
async def extract_intent(payload: dict):
    text = payload.get("text")
    if not text:
        return {"error": "Missing text"}

    result = await intent_agent.run(text)

    redis_memory.set_intent(result.output.dict())
    redis_memory.push_log(f"Intent extracted: {result.output.dict()}")

    return result.output


# -----------------------------
# PLAN
# -----------------------------
@router.post("/plan")
async def create_plan():
    intent = redis_memory.get_intent()
    if not intent:
        return {"error": "No intent found"}

    result = await generate_plan(intent)

    redis_memory.set_plan([step.dict() for step in result.steps])
    redis_memory.set_current_step(0)

    return result


# -----------------------------
# EXECUTE
# -----------------------------
@router.post("/execute")
def execute_plan():
    redis_memory.set_screenshot("")
    redis_memory.push_log("Execution started")
    executor.run()
    return {"status": "execution_started"}


# -----------------------------
# APPROVE (Conscious Pause)
# -----------------------------
@router.post("/approve")
def approve_action():
    redis_memory.set_user_approved(True)
    redis_memory.set_paused(False)
    redis_memory.clear_risk()
    # redis_memory.increment_step()


    redis_memory.push_log("User approved action")

    return {
        "status": "approved",
        "message": "Execution resumed"
    }


# -----------------------------
# REJECT (Terminate)
# -----------------------------
@router.post("/reject")
def reject_action():
    redis_memory.set_paused(False)
    redis_memory.set_current_step(9999)  # force executor exit
    redis_memory.set_risk("User rejected transaction")
    redis_memory.push_log("User rejected transaction")

    return {
        "status": "rejected",
        "message": "Workflow terminated"
    }


# -----------------------------
# STATE (Dashboard polling)
# -----------------------------
@router.get("/state")
def get_state():

    return {
        "paused": redis_memory.is_paused(),
        "risk": redis_memory.get_risk(),
        "logs": redis_memory.get_logs(),
        "narration": redis_memory.get_narration(),
        "screenshot": redis_memory.get_screenshot(),
        "current_step": redis_memory.get_current_step()
    }

@router.get("/profile")
def get_profile():
    return redis_memory.get_profile()
