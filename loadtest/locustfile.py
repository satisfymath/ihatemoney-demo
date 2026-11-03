"""Simulated users for the demo copy: a few people browsing their projects, a client using the API.

    uvx --from locust locust -f loadtest/locustfile.py --headless -u 20 -r 5 -t 2m --host http://127.0.0.1:8000

Projects are the seed's (`demo-0001` ... `demo-0200`, private code `demo`). The web user signs in once (the session
cookie keeps it), then reads the bill list, the statistics and the settlement; now and then it adds a bill. The API
user authenticates with HTTP Basic on every call, as the API expects. Nothing here writes outside the demo projects.
"""

from __future__ import annotations

import random

from locust import HttpUser, between, task

PROJECTS = 200
PASSWORD = "demo"
THINGS = ["Groceries", "Dinner", "Fuel", "Train tickets", "Museum", "Coffee", "Taxi"]


def _project(rng: random.Random) -> str:
    return f"demo-{rng.randint(1, PROJECTS):04d}"


class WebUser(HttpUser):
    """A person in the browser: the pages a project shows after signing in."""

    weight = 3
    wait_time = between(2, 6)

    def on_start(self) -> None:
        self.rng = random.Random()
        self.project = _project(self.rng)
        self.client.post("/authenticate", data={"id": self.project, "password": PASSWORD}, name="/authenticate")
        self.members: list[int] = []

    @task(6)
    def bills(self) -> None:
        self.client.get(f"/{self.project}/", name="/{project}/")

    @task(2)
    def statistics(self) -> None:
        self.client.get(f"/{self.project}/statistics", name="/{project}/statistics")

    @task(2)
    def settle(self) -> None:
        self.client.get(f"/{self.project}/settle_bills", name="/{project}/settle_bills")

    @task(1)
    def history(self) -> None:
        self.client.get(f"/{self.project}/history", name="/{project}/history")


class ApiUser(HttpUser):
    """A client of the REST API: HTTP Basic auth with the project's id and private code."""

    weight = 1
    wait_time = between(1, 3)

    def on_start(self) -> None:
        self.rng = random.Random()
        self.project = _project(self.rng)
        self.auth = (self.project, PASSWORD)
        members = self.client.get(f"/api/projects/{self.project}/members", auth=self.auth, name="/api/.../members")
        self.members = [m["id"] for m in members.json()] if members.status_code == 200 else []

    @task(5)
    def list_bills(self) -> None:
        self.client.get(f"/api/projects/{self.project}/bills", auth=self.auth, name="/api/.../bills")

    @task(2)
    def project(self) -> None:
        self.client.get(f"/api/projects/{self.project}", auth=self.auth, name="/api/.../project")

    @task(2)
    def statistics(self) -> None:
        self.client.get(f"/api/projects/{self.project}/statistics", auth=self.auth, name="/api/.../statistics")

    @task(1)
    def add_bill(self) -> None:
        if len(self.members) < 2:
            return
        payer = self.rng.choice(self.members)
        owers = self.rng.sample(self.members, k=min(len(self.members), self.rng.randint(1, 3)))
        self.client.post(
            f"/api/projects/{self.project}/bills",
            auth=self.auth,
            data={
                "date": "2026-11-03",
                "what": self.rng.choice(THINGS),
                "payer": payer,
                "payed_for": owers,
                "amount": f"{self.rng.uniform(2, 120):.2f}",
            },
            name="/api/.../bills (POST)",
        )
