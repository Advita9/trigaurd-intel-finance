import time
import base64
from services.redis_memory import redis_memory
from services.playwright_engine import PlaywrightEngine
from services.vision_engine import VisionEngine
from agents.safety_officer import SafetyOfficer
DUMMY_BANK_BASE_URL = "http://localhost:8000/dummy_bank"

class ExecutorAgent:
    def __init__(self):
        self.browser = PlaywrightEngine()
        self.vision = VisionEngine()
        self.safety = SafetyOfficer(self.browser)

        self.page = None

        # Map plan "targets" to CSS selectors (DOM-first approach)
        self.selector_map = {
            "invest_button": "button:nth-of-type(1)",
            "digital_gold": "button:nth-of-type(1)",   # gold.html from index
            "pay_bill_button": "button:nth-of-type(2)",
            "proceed_button": "button"
        }

    # ---------------------------------------------
    # MAIN EXECUTION LOOP
    # ---------------------------------------------
    def run(self):
        plan = redis_memory.get_plan()
        if not plan:
            raise ValueError("No plan found in Redis.")

        self.page = self.browser.launch()

        while True:
            step_id = redis_memory.get_current_step()
            paused = redis_memory.is_paused()

            print(f"DEBUG: Executor loop, step_id={step_id}, paused={paused}")

            # End condition
            if step_id >= len(plan):
                redis_memory.push_log("Workflow completed.")
                print("DEBUG: Workflow completed, exiting executor")
                break

            # If paused, just wait
            if paused:
                time.sleep(0.5)
                continue

            step = plan[step_id]
            redis_memory.push_log(f"About to execute step {step_id + 1}: {step}")

            # 🔴 PAUSE BEFORE EXECUTION
            if step.get("requires_pause"):
                self.trigger_pause(step)
                continue  # DO NOT execute yet

            # ✅ SAFE STEP — EXECUTE ONCE
            self.execute_step(step)

            # Move forward
            redis_memory.increment_step()

    # ---------------------------------------------
    # Step Executor
    # ---------------------------------------------
    def execute_step(self, step):
        action = step["action"]

        if action == "navigate":
            self.handle_navigate(step)
            time.sleep(1)

        elif action == "click":
            self.handle_click(step)
            time.sleep(1)


        elif action == "enter_amount":
            amt = step["amount"]

            # Always integer string for finance
            amt_str = str(int(float(amt)))

            self.browser.type_slow("input#amount", amt_str)

            # Blur like real user
            self.page.press("input#amount", "Tab")


            redis_memory.push_log(f"Typed amount (human-like): {amt_str}")

            time.sleep(0.3)



        elif action == "select_biller":
            self.browser.type_text("#biller", step["entity"])
            time.sleep(1)

        # elif action == "open_confirmation":
        #     # Dummy bank automatically opens confirmation on click
        #     pass

        elif action in ("confirm_payment", "submit_payment"):
            allowed = self.safety.evaluate(step)
            if not allowed:
                redis_memory.push_log("Execution paused by Safety Officer")
                return
            self.handle_final_submit()
            # self.handle_final_submit()
            time.sleep(1)
        elif action == "wait_for_success":
            # wait for success banner / confirmation text
            self.page.wait_for_selector("#success", timeout=5000)

        elif action == "capture_success":
            img = self.browser.screenshot()
            redis_memory.set_screenshot(base64.b64encode(img).decode())
            redis_memory.push_log("Captured success screenshot")

        elif action == "log_completion":
            redis_memory.push_log("Transaction completed successfully")

        elif action == "pause_for_approval":
            self.trigger_pause(step)
            return


        else:
            redis_memory.push_log(f"Unknown action: {action}")

    # ---------------------------------------------
    # Navigation Step
    # ---------------------------------------------
    def handle_navigate(self, step):
        page = step["page"]
        url = f"{DUMMY_BANK_BASE_URL}/{page}.html"
        self.browser.navigate(url)

    # ---------------------------------------------
    # Click Step (DOM → Vision fallback)
    # ---------------------------------------------
    def handle_click(self, step):
        target = step["target"]

        selector = self.selector_map.get(target)

        if selector and self.browser.selector_exists(selector):
            self.browser.click(selector)
            return

        # Fallback to Vision model
        screenshot = self.browser.screenshot()
        bbox = self.vision.locate_element(screenshot, target)

        if bbox:
            x, y = bbox
            self.page.mouse.click(x, y)
        else:
            redis_memory.push_log(f"Failed to locate {target}.")
            raise RuntimeError("Executor could not find element.")

    # ---------------------------------------------
    # Final irreversible click
    # ---------------------------------------------
    def handle_final_submit(self):
        # On gold_confirm.html or bill_confirm.html
        buttons = self.page.locator("button")
        buttons.nth(0).click()

    def trigger_pause(self, step):
        img = self.browser.screenshot()
        redis_memory.set_screenshot(base64.b64encode(img).decode())

        redis_memory.set_paused(True)
        redis_memory.set_risk("High-risk action requires approval")

        redis_memory.push_log(f"Paused before executing step: {step['action']}")
