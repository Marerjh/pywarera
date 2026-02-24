from .Worker import Worker

class WorkerPerCompany:
    def __init__(self, data):
        company = data.get("company", {})
        self.company_id = company.get("_id")
        self.company_name = company.get("name")
        self.company_item_code = company.get("itemCode")
        self.workers = [Worker(worker_data) for worker_data in data.get("workers", [])]
