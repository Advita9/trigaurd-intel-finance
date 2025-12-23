# import json
# from services.redis_client import redis_client
# from typing import List, Dict, Any


# # -------------------------
# # Step Templates (Deterministic)
# # -------------------------

# PLAN_TEMPLATES = {
#     "buy_gold": [
#         {"action": "navigate", "page": "index"},
#         {"action": "click", "target": "invest_button"},
#         {"action": "click", "target": "digital_gold"},
#         {"action": "enter_amount", "requires": ["amount"]},
#         {"action": "click", "target": "proceed_button"},
#         # {"action": "navigate", "page": "gold_confirm"},

#         # 🔴 ONLY THIS STEP PAUSES
#         {"action": "pause_for_approval"},

#         # ✅ THIS EXECUTES AFTER APPROVAL
#         {"action": "confirm_payment"},

#         {"action": "wait_for_success"},
#         {"action": "capture_success"},
#         {"action": "log_completion"}
#     ],


#     "pay_bill": [
#         {"action": "navigate", "page": "index"},
#         {"action": "click", "target": "pay_bill_button"},
#         {"action": "select_biller", "requires": ["entity"]},
#         {"action": "enter_amount", "requires": ["amount"]},
#         {"action": "open_confirmation"},
#         {"action": "pause_for_approval", "risk": "high"},
#         {"action": "submit_payment", "risk": "high"}
#     ]
# }

# # -----------------------------------
# # Planner Agent
# # -----------------------------------

# class PlannerAgent:

#     def __init__(self):
#         pass

#     def load_intent(self) -> Dict[str, Any]:
#         intent = redis_client.get_intent()
#         if not intent:
#             raise ValueError("No intent available in Redis.")
#         return intent

#     def generate_plan(self, intent: dict) -> List[dict]:
#         action = intent["action"]

#         if action not in PLAN_TEMPLATES:
#             raise ValueError(f"No plan template found for action: {action}")

#         base_plan = PLAN_TEMPLATES[action]
#         plan = []

#         for idx, step in enumerate(base_plan, start=1):
#             step_obj = {
#                 "step_id": idx,
#                 "action": step["action"],
#             }

#             # Required parameters (amount, entity, etc.)
#             # if "requires" in step:
#             #     for required_key in step["requires"]:
#             #         if required_key not in intent:
#             #             raise ValueError(f"Missing required field '{required_key}' in intent.")
#             #         step_obj[required_key] = intent[required_key]
#             # Attach core transaction context to ALL steps
#             if "amount" in intent:
#                 step_obj["amount"] = intent["amount"]

#             if "entity" in intent:
#                 step_obj["entity"] = intent["entity"]

#             # Page navigation
#             if "page" in step:
#                 step_obj["page"] = step["page"]

#             # Target UI element
#             if "target" in step:
#                 step_obj["target"] = step["target"]

#             # Risk Annotation
#             if step.get("risk") == "high":
#                 step_obj["requires_pause"] = True
#             else:
#                 step_obj["requires_pause"] = False

#             plan.append(step_obj)

#         return plan

#     def validate_plan(self, plan: List[dict]):
#         """
#         Validate: 
#         - step order
#         - required fields
#         - no unknown actions
#         - no nulls
#         """
#         allowed_actions = {
#             "navigate",
#             "click",
#             "enter_amount",
#             "select_biller",
#             "open_confirmation",
#             "pause_for_approval",   # ✅ ADD THIS
#             "confirm_payment",
#             "submit_payment",
#             "wait_for_success",     # optional if already in plan
#             "capture_success",      # optional
#             "log_completion"        # optional
#         }

#         for step in plan:
#             if step["action"] not in allowed_actions:
#                 raise ValueError(f"Invalid action '{step['action']}' in plan.")

#             if "step_id" not in step:
#                 raise ValueError("Missing step_id in plan step.")

#         return True

#     def save_plan(self, plan: List[dict]):
#         redis_client.set("current_plan", json.dumps(plan))
#         redis_client.set("current_step", 0)

#     def process(self):
#         intent = self.load_intent()
#         plan = self.generate_plan(intent)
#         self.validate_plan(plan)

#         # Save to Redis for executor
#         redis_client.r.set("plan", json.dumps(plan))
#         redis_client.r.set("current_step", 0)

#         return plan


# planner_agent = PlannerAgent()


from pydantic import BaseModel
from pydantic_ai import Agent
from typing import Optional, List

# -------------------------
# Plan Schemas
# -------------------------

class PlanStep(BaseModel):
    action: str
    page: Optional[str] = None
    target: Optional[str] = None
    amount: Optional[int] = None
    requires_pause: bool = False


class ExecutionPlan(BaseModel):
    steps: List[PlanStep]


# -------------------------
# Planner Agent
# -------------------------

planner_agent = Agent(
    model="gpt-4o",
    result_type=ExecutionPlan,
    result_retries=2,
    system_prompt=(
        "You are a financial workflow planner.\n\n"
        "Given a validated intent, generate a deterministic execution plan.\n\n"
        "Rules:\n"
        "- Use ONLY supported actions\n"
        "- Mark irreversible steps with requires_pause=true\n"
        "- Do not hallucinate steps\n"
        "- Plans must be executable by a browser automation agent\n\n"
        "Supported actions:\n"
        "- navigate\n"
        "- click\n"
        "- enter_amount\n"
        "- select_biller\n"
        "- pause_for_approval\n"
        "- confirm_payment\n"
        "- wait_for_success\n"
        "- capture_success\n"
        "- log_completion"
    ),
)
