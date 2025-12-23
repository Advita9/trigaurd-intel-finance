# import base64
# import re

# class VisionEngine:
#     """
#     Vision-based verification engine.
#     In production: replace `mock_vlm_verify` with Gemini Pro Vision / GPT-4o Vision.
#     """

#     def verify_confirmation_screen(
#         self,
#         screenshot_bytes: bytes,
#         expected_amount: int,
#         expected_entity: str,
#         expected_screen: str = "gold_confirm"
#     ) -> dict:
#         """
#         Returns structured verification result.
#         """

#         # ---- Deterministic heuristic checks (cheap & fast) ----
#         text_checks = self._heuristic_text_checks(
#             screenshot_bytes,
#             expected_amount,
#             expected_entity
#         )

#         # ---- ML-based reasoning (stubbed, replaceable) ----
#         ml_verdict = self._mock_vlm_verify(
#             screenshot_bytes,
#             expected_amount,
#             expected_entity,
#             expected_screen
#         )

#         # ---- Final decision ----
#         return {
#             "screen_valid": ml_verdict["screen_valid"] and text_checks["text_match"],
#             "amount_match": ml_verdict["amount_match"],
#             "entity_match": ml_verdict["entity_match"],
#             "notes": {
#                 "ml": ml_verdict,
#                 "heuristics": text_checks
#             }
#         }

#     # ----------------------------------------------------
#     # Heuristic checks (cheap, deterministic)
#     # ----------------------------------------------------
#     def _heuristic_text_checks(self, screenshot_bytes, amount, entity):
#         """
#         Simulated OCR-style text checks.
#         In production: use OCR or DOM text fallback.
#         """
#         # Since this is a dummy site, we simulate pass
#         return {
#             "text_match": True,
#             "detected_amount": amount,
#             "detected_entity": entity
#         }

#     # ----------------------------------------------------
#     # Mock VLM (replace with real Vision model)
#     # ----------------------------------------------------
#     def _mock_vlm_verify(self, screenshot_bytes, amount, entity, screen):
#         """
#         Replace this with Gemini Pro Vision / GPT-4o Vision call.
#         """
#         return {
#             "screen_valid": False,
#             "amount_match": False,
#             "entity_match": False
#         }
import base64
import google.generativeai as genai
import json
import os
import re

# genai.configure(api_key=os.getenv(""))
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


class VisionEngine:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-2.0-flash-lite-preview")

    def verify_confirmation_screen(
        self,
        screenshot_bytes: bytes,
        expected_amount: int,
        expected_entity: str,
        expected_screen: str = "gold_confirm"
    ) -> dict:
        print("🟦 [Vision] verify_confirmation_screen CALLED")

        image_b64 = base64.b64encode(screenshot_bytes).decode()

        print("🟦 [Vision] Screenshot size:", len(screenshot_bytes))
        print("🟦 [Vision] Expected amount:", expected_amount)
        print("🟦 [Vision] Expected entity:", expected_entity)

        try:
            response = self.model.generate_content(
                [
                    self._build_prompt(
                        expected_amount,
                        expected_entity,
                        expected_screen
                    ),
                    {
                        "mime_type": "image/png",
                        "data": image_b64
                    }
                ]
            )

            raw_text = response.text
            print("🟩 [Vision] Raw Gemini response:", raw_text)

            verdict = self._extract_json(raw_text)
            if verdict["screen_valid"] and verdict["amount_match"]:
                print("🟩 [Safety] Vision validation PASSED")



            return verdict


        except Exception as e:
            print("🟥 [Vision] ERROR:", str(e))

            return {
                "screen_valid": False,
                "amount_match": False,
                "entity_match": False,
                "notes": f"Vision exception: {e}"
            }



    def _extract_json(self, text: str) -> dict:
        # Extract first {...} block safely
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise ValueError("No JSON object found in Vision response")

        json_str = match.group(0)
        return json.loads(json_str)


    
    def _build_prompt(self, amount, entity, screen):
        return f"""
    You are a financial safety verification system.

    Expected:
    - Screen type: {screen}
    - Amount: ₹{amount}
    - Entity: {entity}

    Tasks:
    1. Is this a transaction confirmation screen?
    2. Does the displayed amount match ₹{amount} exactly?
    3. Does the entity match "{entity}"?
    4. Detect any anomalies, spoofing, or mismatches.

    Return ONLY valid JSON.
    Do NOT include markdown, comments, or explanations.

    {{
    "screen_valid": true/false,
    "amount_match": true/false,
    "entity_match": true/false,
    "notes": "short explanation"
    }}
    """



#     def verify_confirmation_screen(
#         self,
#         screenshot_bytes: bytes,
#         expected_amount: int,
#         expected_entity: str,
#         expected_screen: str = "gold_confirm"
#     ) -> dict:
#         """
#         Gemini Pro Vision verification.
#         Returns structured safety verdict.
#         """

#         image_b64 = base64.b64encode(screenshot_bytes).decode()

#         prompt = f"""
# You are a financial safety verification system.

# Expected:
# - Screen type: {expected_screen}
# - Amount: ₹{expected_amount}
# - Entity: {expected_entity}

# Tasks:
# 1. Verify this is a transaction confirmation screen.
# 2. Verify the amount matches exactly ₹{expected_amount}.
# 3. Verify the entity matches "{expected_entity}".
# 4. Detect any anomalies, spoofing, or mismatches.

# Respond ONLY in JSON:
# {{
#   "screen_valid": true/false,
#   "amount_match": true/false,
#   "entity_match": true/false,
#   "notes": "short explanation"
# }}
# """

#         response = self.model.generate_content(
#             [
#                 prompt,
#                 {
#                     "mime_type": "image/png",
#                     "data": image_b64
#                 }
#             ]
#         )

#         try:
#             text = response.text.strip()
#             verdict = json.loads(text)
#         except Exception:
#             # Fail closed — finance rule
#             verdict = {
#                 "screen_valid": False,
#                 "amount_match": False,
#                 "entity_match": False,
#                 "notes": "Vision parsing failure"
#             }

#         return verdict
