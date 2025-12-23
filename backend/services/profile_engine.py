from services.redis_memory import redis_memory

def apply_transaction(action: str, amount: int, entity=None):
    profile = redis_memory.get_profile()

    if action == "buy_gold":
        profile["balance"] -= amount
        profile["history"].append({
            "type": "buy_gold",
            "details": "Digital Gold",
            "amount": amount
        })

    elif action == "transfer_money":
        profile["balance"] -= amount
        profile["history"].append({
            "type": "transfer",
            "details": f"To {entity}",
            "amount": amount
        })

    elif action == "pay_bill":
        profile["balance"] -= amount
        profile["bills"][entity] = 0
        profile["history"].append({
            "type": "bill_payment",
            "details": entity,
            "amount": amount
        })

    redis_memory.set_profile(profile)
