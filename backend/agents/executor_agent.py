import time
import base64
from services.redis_memory import redis_memory
from services.playwright_engine import PlaywrightEngine
from services.vision_engine import VisionEngine
from agents.safety_officer import SafetyOfficer
from services.profile_engine import apply_transaction

DUMMY_BANK_BASE_URL = "http://localhost:8000/dummy_bank"

class ExecutorAgent:
    def __init__(self):
        self.browser = PlaywrightEngine()
        self.vision = VisionEngine()
        self.safety = SafetyOfficer(self.browser)

        self.page = None

        # Map plan "targets" to CSS selectors (DOM-first approach)
        self.selector_map = {
            "invest_button": "#buy-gold-btn",
            "transfer_button": "#transfer-btn",
            "pay_bill_button": "#pay-bill-btn",
            "proceed_button": "#proceed-btn",
            "submit_bill_button": "#confirmBtn"
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

            # # 🔴 PAUSE BEFORE EXECUTION
            # # if step.get("requires_pause"):
            # #     self.trigger_pause(step)
            #     continue  # DO NOT execute yet

            # ✅ SAFE STEP — EXECUTE ONCE
            self.execute_step(step)

            # Move forward
            redis_memory.increment_step()

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

            if amt is None:
                amt = redis_memory.get_temp("current_bill_amount")

            if amt is None:
                raise RuntimeError("Unable to resolve bill amount")

            # Always integer string for finance
            amt_str = str(int(float(amt)))

            self.browser.type_slow("input#amount", amt_str)

            # Blur like real user
            self.page.press("input#amount", "Tab")


            redis_memory.push_log(f"Typed amount (human-like): {amt_str}")

            time.sleep(0.3)



        elif action == "select_biller":
            redis_memory.push_log(f"Selecting biller: {step['entity']}")
            self.browser.select("#biller", step["entity"])
            time.sleep(1)

        # elif action == "open_confirmation":
        #     # Dummy bank automatically opens confirmation on click
        #     pass

        elif action in ("confirm_payment", "submit_payment", "submit_bill_butoon"):
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
            amount = step.get("amount")
            profile = redis_memory.get_profile()
            intent = redis_memory.get_intent()
            biller=step.get("entity")
            biller = intent["entity"]


            redis_memory.set_profile(profile)

            redis_memory.log_transaction({
                "type": intent["action"],
                "amount": amount
            })
            if intent["action"] == "pay_bill":
                amount=profile["bills"][biller]
                profile["balance"] -= amount
                redis_memory.clear_bill(intent["entity"])
                redis_memory.set_profile(profile)
                redis_memory.log_transaction({
                    "type": "bill_payment",
                    "amount": amount
                })
                redis_memory.push_log(
                    f"✅ Bill for {intent['entity']} paid successfully"
                )

            if intent["action"] == "pay_bill":
                biller = intent["entity"]
                amount = redis_memory.get_temp("current_bill_amount")
                amount=profile["bills"][biller]

                profile["balance"] -= amount
                profile["bills"][biller] = 0

                redis_memory.set_profile(profile)

                redis_memory.log_transaction({
                    "type": "bill_payment",
                    "amount": amount
                })

            if intent["action"] == "buy_gold":
                amount=step.get("amount")
                profile["balance"] -= amount
                redis_memory.set_profile(profile)
                redis_memory.log_transaction({
                    "type": "gold_purchase",
                    "amount": amount
                })
                redis_memory.push_log(
                    f"✅ Bill for {intent['entity']} paid successfully"
                )
            redis_memory.set_profile(profile)

            redis_memory.push_log("Transaction completed successfully")

        elif action == "pause_for_approval":
            self.trigger_pause(step)
            return

        elif action == "select_beneficiary":
            self.browser.type_text("#recipient", step["entity"])

        elif action == "confirm_transfer":
            self.handle_final_submit()

        elif action == "fetch_bill_amount":
            biller = step.get("entity")

            profile = redis_memory.get_profile()
            bill = profile["bills"].get(biller)

            if bill is None:
                raise RuntimeError("Unable to resolve bill amount")

            redis_memory.set_temp("current_bill_amount", bill)

            redis_memory.push_log(
                f"📄 Found ₹{bill} due for {biller}. Awaiting user approval."
            )

            self.trigger_pause(step)
            return
        
        elif action == "deposit_funds":
            amount = step.get("amount")

            if not amount or amount <= 0:
                raise RuntimeError("Invalid deposit amount")

            profile = redis_memory.get_profile()

            profile["balance"] += amount

            redis_memory.set_profile(profile)

            redis_memory.log_transaction({
                "type": "deposit",
                "amount": amount
            })

            redis_memory.push_log(f"💰 Deposited ₹{amount} successfully")
            redis_memory.push_narration(
                f"I have deposited {amount} rupees into your account."
            )

            time.sleep(0.5)



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
            redis_memory.push_log(f"Clicking {target}")
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
