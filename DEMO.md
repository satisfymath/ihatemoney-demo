# This copy

A copy of [spiral-project/ihatemoney](https://github.com/spiral-project/ihatemoney) at `e66a767` (2026-08-07), kept
to try an engineering agent on an installed, running application. It is not the project: nothing here goes upstream,
and pull requests here are the agent's. The application's own code is unchanged.

What was added, and only this:

| File | What for |
|---|---|
| `docker-compose.yml` | the stack on one machine: the application and PostgreSQL 17, with health checks and a named volume (upstream's file was an SQLite example) |
| `conf/db-init/10-readonly.sh` | a read-only database role, `unbidden_ro`, created at the first start |
| `conf/seed_demo.py` | a realistic amount of data: 200 projects, 2 000 persons, 100 000 bills |
| `.github/workflows/deploy.yml` | a push to `main` deploys the stack on the demo machine (self-hosted runner, label `demo`) |
| `.env.example` | the three secrets the stack needs |

Removed: `.github/dependabot.yml` and `.github/workflows/dockerhub.yml` (they would open pull requests and push images
that are not this copy's to make). The upstream CI (`ci.yml`: lint, pytest against SQLite, PostgreSQL and MariaDB,
docs) is unchanged.

## Run

```sh
cp .env.example .env                                   # real values in it
docker compose up -d --build --wait
curl -fsS http://127.0.0.1:8000/healthcheck            # OK
docker compose exec app python /src/conf/seed_demo.py  # once; a second run adds nothing
```

The application answers at http://127.0.0.1:8000. Demo projects are `demo-0001` … `demo-0200`, password `demo`. The
database is not published on the host; read it inside its container (`docker compose exec db psql -U ihatemoney`) or
grant the `unbidden_ro` role to whatever must read it over the network.

## Deploy from GitHub

The `Deploy` workflow runs on a self-hosted runner on the demo machine, only on a push to `main`. The three secrets of
`.env.example` are repository secrets with the same names. Pull requests run upstream's CI on GitHub's runners and
never touch the demo machine.
