class Job:
    def __init__(self):
        self.id = None
        self.company_id = None
        self.title = None
        self.url = None
        self.description = None
        self.salary = None
        self.location = None
        self.active = None
        self.new = None
        self.remote = None
        self.insert_timestamp = None
        self.scrape_run_id = None

    def dump(self) -> dict:
        job = {
            "id": self.id,
            "company_id": self.company_id,
            "title": self.title,
            "url": self.url,
            "salary": self.salary,
            "location": self.location,
            "active": self.active,
            "new": self.new,
            "remote": self.remote,
        }
        return job
