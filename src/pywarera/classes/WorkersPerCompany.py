from .WorkerPerCompany import WorkerPerCompany


class WorkersPerCompany:
    def __init__(self, data):
        self.items = [WorkerPerCompany(worker_per_company_data) for worker_per_company_data in data["workersPerCompany"]]