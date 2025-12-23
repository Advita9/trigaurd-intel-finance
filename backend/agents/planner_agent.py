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


from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from pydantic_ai import Agent

# =========================
# 1. STEP + PLAN SCHEMAS
# =========================

class PlanStep(BaseModel):
    step_id: int
    action: Literal[
        "navigate",
        "click",
        "enter_amount",
        "select_biller",
        "select_beneficiary",
        "pause_for_approval",
        "confirm_payment",
        "confirm_transfer",
        "submit_payment",
        "wait_for_success",
        "log_completion",
        "fetch_bill_amount",
        "deposit_funds"
    ]

    page: Optional[str] = None
    target: Optional[str] = None
    amount: Optional[int] = None
    entity: Optional[str] = None
    requires_pause: bool = False


class PlanOutput(BaseModel):
    steps: List[PlanStep]


# =========================
# 2. APPROVED PLAN TEMPLATES
# =========================

PLAN_TEMPLATES = {
    "buy_gold": [
        {"action": "navigate", "page": "index"},
        {"action": "click", "target": "invest_button"},
        # {"action": "click", "target": "digital_gold"},
        {"action": "enter_amount"},
        {"action": "click", "target": "proceed_button"},
        {"action": "pause_for_approval", "requires_pause": True},
        {"action": "confirm_payment"},
    ],

    "pay_bill": [
        {"action": "navigate", "page": "index"},
        {"action": "click", "target": "pay_bill_button"},
        {"action": "select_biller"},
        {"action": "fetch_bill_amount", "requires_pause": True},
        {"action": "enter_amount"},
        {"action": "click", "target": "proceed_button"},
        {"action": "click", "target": "submit_bill_button", "requires_pause": True},
        {"action": "log_completion"}
    ],



    "transfer_money": [
        {"action": "navigate", "page": "index"},
        {"action": "click", "target": "transfer_button"},
        {"action": "select_beneficiary"},
        {"action": "enter_amount"},
        {"action": "click", "target": "proceed_button"},
        {"action": "pause_for_approval", "requires_pause": True},
        {"action": "confirm_transfer", "requires_pause": True},
        {"action": "wait_for_success"},
        {"action": "log_completion"}
    ],

    "deposit_funds": [
        {"action": "deposit_funds"},
        {"action": "log_completion"}
    ]

}


# =========================
# 3. PLANNER AGENT
# =========================

planner_agent = Agent(
    "openai:gpt-4o-mini",
    output_type=PlanOutput,
    instructions="""
You are a FINANCIAL WORKFLOW PLANNER.

CRITICAL RULES (MUST FOLLOW):
1. You MUST choose one of the provided plan templates.
2. You MUST NOT add, remove, or reorder steps.
3. You MUST NOT invent navigation or actions.
4. You MAY ONLY fill in parameters:
   - amount
   - entity
5. All irreversible actions MUST have requires_pause=true.
6. Output MUST match the PlanOutput schema EXACTLY.
7. If intent is invalid, return an empty steps list.

This system is used in a banking environment.
Failure to follow rules is a critical error.
"""
)


# =========================
# 4. PLANNER RUN FUNCTION
# =========================

async def generate_plan(intent: dict) -> PlanOutput:
    """
    Deterministically generate a plan by:
    - selecting a predefined template
    - parameterizing it with intent data
    """

    action = intent.get("action")
    if action not in PLAN_TEMPLATES:
        return PlanOutput(steps=[])

    base_steps = PLAN_TEMPLATES[action]
    steps: List[PlanStep] = []

    for idx, base in enumerate(base_steps, start=1):
        step = PlanStep(
            step_id=idx,
            action=base["action"],
            page=base.get("page"),
            target=base.get("target"),
            requires_pause=base.get("requires_pause", False),
        )

        # Parameter injection (safe)
        if step.action == "enter_amount":
            step.amount = intent.get("amount")

        if step.action in ("select_biller", "select_beneficiary", "fetch_bill_amount"):
            step.entity = intent.get("entity")

        if step.action == "deposit_funds":
            step.amount = intent.get("amount")



        steps.append(step)

    return PlanOutput(steps=steps)
