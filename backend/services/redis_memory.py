import redis
import json
from typing import Any, List, Optional

class RedisMemory:
    def __init__(self, host="localhost", port=6379):
        self.r = redis.Redis(host=host, port=port, decode_responses=True)

    # -------------------------
    # INTENT
    # -------------------------
    def set_intent(self, intent: dict):
        self.r.set("intent", json.dumps(intent))

    def get_intent(self) -> Optional[dict]:
        data = self.r.get("intent")
        return json.loads(data) if data else None

    # -------------------------
    # PLAN
    # -------------------------
    def set_plan(self, plan: List[dict]):
        self.r.set("plan", json.dumps(plan))

    def get_plan(self) -> Optional[List[dict]]:
        data = self.r.get("plan")
        return json.loads(data) if data else None

    # -------------------------
    # STEP TRACKING
    # -------------------------
    def set_current_step(self, step: int):
        self.r.set("current_step", step)

    def get_current_step(self) -> int:
        val = self.r.get("current_step")
        return int(val) if val else 0

    def increment_step(self):
        self.r.incr("current_step")

    # -------------------------
    # PAUSE STATE
    # -------------------------
    def set_paused(self, paused: bool):
        self.r.set("is_paused", "1" if paused else "0")

    def is_paused(self) -> bool:
        val = self.r.get("is_paused")
        return val == "1"

    # -------------------------
    # SAFETY FLAGS
    # -------------------------
    def set_risk(self, reason: str):
        self.r.set("risk_flag", reason)

    def get_risk(self) -> Optional[str]:
        return self.r.get("risk_flag")

    def clear_risk(self):
        self.r.delete("risk_flag")

    # -------------------------
    # SCREENSHOT STORAGE
    # -------------------------
    def set_screenshot(self, img_b64: str):
        self.r.set("latest_screenshot", img_b64)

    def get_screenshot(self) -> Optional[str]:
        return self.r.get("latest_screenshot")

    # -------------------------
    # LOGGING
    # -------------------------
    def push_log(self, text: str):
        self.r.lpush("logs", text)

    def get_logs(self, limit=50) -> List[str]:
        return self.r.lrange("logs", 0, limit)

    # -------------------------
    # EXECUTOR STATE
    # -------------------------
    def save_executor_state(self, data: dict):
        self.r.set("executor_state", json.dumps(data))

    def load_executor_state(self) -> Optional[dict]:
        data = self.r.get("executor_state")
        return json.loads(data) if data else None

    def set_user_approved(self, val: bool):
        self.r.set("user_approved", "1" if val else "0")

    def is_user_approved(self) -> bool:
        return self.r.get("user_approved") == "1"

    def clear_user_approved(self):
        self.r.delete("user_approved")

    def push_narration(self, text: str):
        self.r.rpush("narration", text)

    def get_narration(self):
        return self.r.lrange("narration", 0, -1)

    def clear_narration(self):
        self.r.delete("narration")

    def get_profile(self):
        data = self.r.get("profile")
        return json.loads(data) if data else {
            "balance": 100000,
            "bills": {
                "tata": 950,
                "adani": 1200
            },
            "history": []
        }

    def set_profile(self, profile: dict):
        self.r.set("profile", json.dumps(profile))

    def log_transaction(self, entry: dict):
        profile = self.get_profile()
        profile["history"].append(entry)
        self.set_profile(profile)

    # ---------------------------
    # TEMP VALUES (for workflows)
    # ---------------------------
    def set_temp(self, key: str, value):
        self.r.set(f"temp:{key}", value)

    def get_temp(self, key: str):
        val = self.r.get(f"temp:{key}")
        if val is None:
            return None
        try:
            return int(val)
        except ValueError:
            return val

    def clear_bill(self, biller: str):
        profile = self.get_profile()
        if not profile:
            return
        profile["bills"][biller] = 0
        self.set_profile(profile)






redis_memory = RedisMemory()
