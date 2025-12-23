# from services.redis_memory import redis_memory

# class SafetyOfficer:
#     def evaluate(self, step):
#         """
#         Returns:
#         - True  → execution allowed
#         - False → execution must pause
#         """

#         # Rule 1: Explicit high-risk step
#         if step.get("requires_pause"):
#             self._pause("High-risk action requires approval")
#             return False

#         # Rule 2: Amount threshold
#         amount = step.get("amount")
#         if amount is not None and float(amount) > 1000:
#             self._pause("Amount exceeds configured safety limit")
#             return False

#         return True

#     def _pause(self, reason: str):

#         print(f"DEBUG: SafetyOfficer pausing execution → {reason}")
#         redis_memory.set_paused(True)
#         redis_memory.set_risk(reason)

import base64
from services.redis_memory import redis_memory
from services.vision_engine import VisionEngine

class SafetyOfficer:
    """
    Independent safety evaluator.
    Has authority to pause execution.
    """

    def __init__(self, browser):
        self.vision = VisionEngine()
        self.browser = browser

        # Configurable risk thresholds
        self.MAX_SAFE_AMOUNT = 1000

    def evaluate(self, step: dict) -> bool:
        """
        Returns True if execution may proceed.
        Returns False if execution must pause.
        """

        # -------------------------------
        # 1. High-risk step check
        # -------------------------------
        if step.get("requires_pause"):
            print("🟨 [Safety] Step marked requires_pause=True")

            return self._pause("High-risk action detected")

        # -------------------------------
        # 2. Amount threshold check
        # -------------------------------
        # amount = step.get("amount")
        # if amount and amount > self.MAX_SAFE_AMOUNT:
        #     return self._pause(f"Amount ₹{amount} exceeds safe threshold")
        amount = step.get("amount")
        if amount:
            print("🟨 [Safety] Amount detected:", amount)

        if amount and amount > self.MAX_SAFE_AMOUNT:
            print("🟥 [Safety] Amount exceeds threshold")
            return self._pause(f"Amount ₹{amount} exceeds safe limit")
        # -------------------------------
        # 3. Confirmation screen validation
        # -----------------------r--------
        if step["action"] in ("confirm_payment", "submit_payment"):
            redis_memory.push_narration(
                "I am verifying the confirmation screen using vision."
            )

            screenshot = self.browser.screenshot()

            vision_result = self.vision.verify_confirmation_screen(
                screenshot_bytes=screenshot,
                expected_amount=int(
                    step.get("amount") 
                    or redis_memory.get_intent().get("amount")
                ),
                expected_entity=step.get("entity") or "digital_gold",
            )

            redis_memory.push_log(f"Vision result: {vision_result}")

            if not vision_result.get("screen_valid"):
                redis_memory.push_narration(
                    "This does not appear to be a valid confirmation screen."
                )
                return self._pause("Invalid confirmation screen")

            if not vision_result.get("amount_match"):
                redis_memory.push_narration(
                    "The amount shown does not match your request."
                )
                return self._pause("Amount mismatch")

            if not vision_result.get("entity_match"):
                redis_memory.push_narration(
                    "The product shown does not match your request."
                )
                return self._pause("Entity mismatch")

            redis_memory.push_narration(
                "Vision verification passed. It is safe to proceed."
            )


        print("🟩 [Safety] Safety check passed")
        return True

    # ------------------------------------
    # Pause logic (single source of truth)
    # ------------------------------------
    def _pause(self, reason: str) -> bool:
        print("⛔ [Safety] PAUSING EXECUTION:", reason)

        img = self.browser.screenshot()
        redis_memory.set_screenshot(base64.b64encode(img).decode())

        redis_memory.set_paused(True)
        redis_memory.set_risk(reason)

        redis_memory.push_log(f"⛔ Safety pause: {reason}")
        return False

