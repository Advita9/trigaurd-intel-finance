# from fastapi import FastAPI
# from agents.intent_agent import intent_agent
# from services.redis_client import redis_client
# from agents.planner_agent import planner_agent
# from agents.executor_agent import ExecutorAgent
# from services.redis_memory import redis_memory
# from agents.intent_agent import intent_agent
# from agents.planner_agent import planner_agent
# from services.redis_memory import redis_memory

# app = FastAPI()
# executor = ExecutorAgent()

# @app.post("/execute")
# def execute_plan():
#     print("DEBUG: /execute endpoint called")
#     executor.run()
#     print("DEBUG: executor.run() finished")
#     return {"status": "execution_started"}
    
# @app.post("/plan")
# def create_plan():
#     plan = planner_agent.process()
#     return {"status": "ok", "plan": plan}

# @app.post("/intent")
# def parse_intent(payload: dict):
#     user_text = payload.get("text")
#     intent = intent_agent.process(user_text)
#     return {"status": "ok", "intent": intent}




# @app.post("/approve")
# def approve_action():
#     """
#     Called when user approves a paused high-risk action.
#     """
#     redis_memory.set_paused(False)
#     redis_memory.clear_risk()
#     redis_memory.push_log("User approved action")
#     # redis_memory.increment_step()

#     return {
#         "status": "approved",
#         "message": "Execution resumed"
#     }

# @app.post("/reject")
# def reject_action():
#     """
#     User rejects the action → terminate workflow safely
#     """
#     redis_memory.set_paused(False)
#     redis_memory.set_current_step(9999)  # force exit
#     redis_memory.set_risk("User rejected transaction")

#     return {
#         "status": "rejected",
#         "message": "Workflow terminated"
#     }
# @app.get("/state")
# def get_state():
#     return {
#         "paused": redis_memory.is_paused(),
#         "risk": redis_memory.get_risk(),
#         "logs": redis_memory.get_logs(),
#         "screenshot": redis_memory.get_screenshot()
#     }

from fastapi import FastAPI
from routes import router
from fastapi.staticfiles import StaticFiles
from routes.api import router
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent                     # finagent/
DUMMY_BANK_DIR = PROJECT_ROOT / "dummy_bank" 

from fastapi.responses import HTMLResponse
import pathlib
from services.redis_memory import redis_memory

redis_memory.set_profile({
    "balance": 50000,
    "bills": {
        "adani": 1842,
        "tata": 950
    },
    "history": []
})

app = FastAPI()
app.mount(
    "/dummy_bank",
    StaticFiles(directory=DUMMY_BANK_DIR, html=True),
    name="dummy_bank"
)

@app.get("/")
def dashboard():
    html = pathlib.Path("dashboard.html").read_text()
    return HTMLResponse(html)

# app = FastAPI(title="FinAgent")

app.include_router(router)

