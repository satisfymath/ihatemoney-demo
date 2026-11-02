"""Fill the demo database with a realistic amount of data.

Run inside the application container, where the configuration file already points at the database:

    docker compose exec app python /src/conf/seed_demo.py [--projects 200] [--bills 100000]

Projects are named demo-0001 ... with the password "demo". Bills are inserted with the database's bulk path (one
INSERT per 10 000 rows, outside the ORM session so the versioning extension does not follow them); the id sequences
are moved past the inserted ids so the application can keep adding rows. Each step is skipped when its rows exist, so
running it twice adds nothing and an interrupted run resumes.
"""

from __future__ import annotations

import argparse
import datetime
import random
import sys

from sqlalchemy import func, select, text

from ihatemoney.models import Bill, BillType, Person, Project, billowers, db
from ihatemoney.utils import generate_password_hash
from ihatemoney.wsgi import application

FIRST_NAMES = [
    "Ada",
    "Bruno",
    "Carla",
    "Diego",
    "Elena",
    "Felipe",
    "Gala",
    "Hugo",
    "Ines",
    "Jorge",
    "Lucia",
    "Mateo",
]
THINGS = [
    "Groceries",
    "Dinner",
    "Fuel",
    "Train tickets",
    "Museum",
    "Rent",
    "Wine",
    "Coffee",
    "Taxi",
    "Pharmacy",
]
CHUNK = 10_000


def seed_projects(rng: random.Random, projects: int) -> None:
    session = db.session
    if session.get(Project, "demo-0001") is not None:
        print("projects exist: skipped")
        return
    password = generate_password_hash("demo")
    for n in range(1, projects + 1):
        pid = f"demo-{n:04d}"
        session.add(
            Project(
                id=pid,
                name=f"Trip {n}",
                password=password,
                contact_email=f"trip{n}@example.com",
                default_currency="XXX",
            )
        )
        session.add_all(
            [
                Person(project_id=pid, name=name, weight=1, activated=True)
                for name in rng.sample(FIRST_NAMES, 10)
            ]
        )
    session.commit()
    print(f"{projects} projects, {projects * 10} persons")


def seed_bills(rng: random.Random, bills: int) -> None:
    from sqlalchemy_continuum import versioning_manager

    # The versioning extension follows every INSERT into an association table (billowers) through the session's unit
    # of work; a bulk insert outside a session has none, so versioning is off while the data is written. The models
    # may carry their own manager (ihatemoney/monkeypath_continuum.py), so it is read from them.
    manager = getattr(Bill, "__versioning_manager__", versioning_manager)
    manager.options["versioning"] = False
    engine = db.engine
    with engine.connect() as conn:
        if (
            conn.execute(select(func.count()).select_from(Bill.__table__)).scalar() or 0
        ) > 0:
            print("bills exist: skipped")
            return
        members: dict[str, list[int]] = {}
        for pid, person_id in conn.execute(
            select(Person.project_id, Person.id).where(Person.project_id.like("demo-%"))
        ):
            members.setdefault(pid, []).append(person_id)
    project_ids = sorted(members)
    today = datetime.date.today()
    done = 0
    while done < bills:
        rows, owers = [], []
        for bill_id in range(1 + done, 1 + min(done + CHUNK, bills)):
            pid = rng.choice(project_ids)
            payer = rng.choice(members[pid])
            amount = round(rng.uniform(2, 400), 2)
            rows.append(
                {
                    "id": bill_id,
                    "payer_id": payer,
                    "amount": amount,
                    "date": today - datetime.timedelta(days=rng.randrange(0, 730)),
                    "creation_date": today,
                    "what": rng.choice(THINGS),
                    "bill_type": BillType.EXPENSE
                    if rng.random() < 0.93
                    else BillType.REIMBURSEMENT,
                    "external_link": "",
                    "original_currency": "XXX",
                    "converted_amount": amount,
                    "archive": None,
                }
            )
            for person in rng.sample(members[pid], rng.randint(1, 4)):
                owers.append({"bill_id": bill_id, "person_id": person})
        with engine.begin() as conn:
            conn.execute(Bill.__table__.insert(), rows)
            conn.execute(billowers.insert(), owers)
        done += len(rows)
        print(f"{done} bills", file=sys.stderr)
    if engine.dialect.name == "postgresql":
        with engine.begin() as conn:
            for table in ("bill", "person"):
                conn.execute(
                    text(
                        f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), (SELECT max(id) FROM {table}))"
                    )
                )
    print(f"{done} bills with their owers")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--projects", type=int, default=200)
    parser.add_argument("--bills", type=int, default=100_000)
    args = parser.parse_args()
    rng = random.Random(7)
    with application.app_context():
        seed_projects(rng, args.projects)
        seed_bills(rng, args.bills)
