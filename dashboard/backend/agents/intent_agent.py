# import json
# from services.redis_client import redis_client
# from pydantic import BaseModel, ValidationError
# from typing import Optional

# # -------------------------
# # 1. Intent Schema (Pydantic)
# # -------------------------

# class Intent(BaseModel):
#     action: str
#     amount: Optional[float] = None
#     entity: Optional[str] = None
#     metadata: dict = {}


# # -------------------------
# # 2. Intent Agent
# # -------------------------

# class IntentAgent:
#     def __init__(self, small_model, llm_pro):
#         self.small_model = small_model      # Gemini Flash / Llama3
#         self.llm_pro = llm_pro              # Gemini Pro (for refinement)

#     # ---- Layer 1: Cheap Extraction ----
#     def extract_raw_intent(self, user_text: str) -> dict:
#         prompt = f"""
#         Extract action, amount, entity from: "{user_text}"
#         Respond in JSON: {{"action": "...", "amount": ..., "entity": "..."}}
#         """
#         raw = self.small_model.generate(prompt)
#         return json.loads(raw)

#     # ---- Layer 2: ADK Refinement ----
#     def refine_intent(self, raw_dict: dict) -> dict:
#         prompt = f"""
#         You are a validation system. Given raw intent: {raw_dict}
#         Normalize action into canonical form:
#          - Buy Gold → buy_gold
#          - Pay Electricity Bill → pay_bill
#          - Invest in Gold → buy_gold
#         Ensure amount is numeric.
#         Ensure entity is normalized (digital_gold, adani_power, etc.)
#         Return a corrected JSON.
#         """
#         refined = self.llm_pro.generate(prompt)
#         return json.loads(refined)

#     # ---- Schema Validation ----
#     def validate_schema(self, refined_dict: dict) -> dict:
#         try:
#             intent = Intent(**refined_dict)
#             return intent.dict()
#         except ValidationError:
#             raise ValueError("Intent schema validation failed.")

#     # ---- Main Function ----
#     def process(self, user_text: str) -> dict:
#         raw = self.extract_raw_intent(user_text)
#         refined = self.refine_intent(raw)
#         valid = self.validate_schema(refined)

#         # Save to Redis
#         redis_client.set_intent(valid)
#         return valid


# # -------------------------
# # Initialize Agent (placeholder models)
# # -------------------------

# class DummyModel:
#     def generate(self, prompt):
#         # Stub model for dev testing
#         print("\nMODEL PROMPT:\n", prompt)
#         return json.dumps({
#             "action": "buy_gold",
#             "amount": 500,
#             "entity": "digital_gold"
#         })


# intent_agent = IntentAgent(
#     small_model=DummyModel(), 
#     llm_pro=DummyModel()
# )



from pydantic import BaseModel
from pydantic_ai import Agent

class IntentInput(BaseModel):
    text: str

class IntentOutput(BaseModel):
    action: str
    amount: int | None = None
    entity: str | None = None

intent_agent = Agent(
    model="gpt-4o-mini",
    deps_type=IntentInput,
    output_type=IntentOutput,
    instructions="""
    You extract structured financial intent.

    Allowed actions:
    - buy_gold
    - pay_bill

    Normalize:
    - Amount → integer INR
    - Entity → snake_case

    Return ONLY valid JSON.
    """
)

async def extract_intent(text: str) -> IntentOutput:
    result = await intent_agent.run(
        "Extract intent",
        deps=IntentInput(text=text)
    )
    return result.output
