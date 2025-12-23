import json
from datetime import datetime

def update_profile(action, amount, entity=None):
    with open("dummy_bank/profile_state.json", "r+") as f:
        profile = json.load(f)

        if action in ("buy_gold", "transfer_money"):
            profile["balance"] -= amount

        if action == "pay_bill":
            profile["balance"] -= amount
            profile["bills"][entity] = 0

        profile["history"].append({
            "type": action,
            "amount": amount,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        })

        f.seek(0)
        json.dump(profile, f, indent=2)
        f.truncate()
