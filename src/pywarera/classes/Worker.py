class Worker:
    def __init__(self, data):
        self.id = data.get("_id")
        self.user = data.get("user")
        self.company = data.get("company")
        self.wage = data.get("wage")
        self.joined_at = data.get("joinedAt")
        self.fidelity: int = data.get("fidelity")
        self.last_fidelity_increase_at = data.get("lastFidelityIncreaseAt")
        self.created_at = data.get("createdAt")
        self.updated_at = data.get("updatedAt")