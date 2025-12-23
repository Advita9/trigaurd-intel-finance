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
        # -------------------------------
        if step["action"] in ("confirm_payment", "submit_payment"):
            print("🟦 [Safety] Triggering Vision validation")

            screenshot = self.browser.screenshot()
            print("🟦 [Safety] Screenshot captured")

            vision_result = self.vision.verify_confirmation_screen(
                screenshot_bytes=screenshot,
                expected_amount=int(step.get("amount", 0)),
                expected_entity=step.get("entity", "digital_gold")
            )

            print("🟦 [Safety] Vision result:", vision_result)

            if not (
                vision_result.get("screen_valid")
                and vision_result.get("amount_match")
                and vision_result.get("entity_match")
            ):
                print("🟥 [Safety] Vision validation FAILED")
                return self._pause("Vision validation failed")

            print("🟩 [Safety] Vision validation PASSED")

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

