# support-desk

A small helpdesk backend for a technical support team, built with **Django, Django REST Framework and PostgreSQL**.
It covers the day-to-day of production support: a ticket queue, an incident log with root causes, and a knowledge base
of known problems and fixes.

![CI](https://github.com/daria-sobko-dev/support-desk/actions/workflows/ci.yml/badge.svg)

## Features

- **Tickets**: status, priority, channel (email, chat, portal), assignee; filter and search the queue; `resolve` action
- **Incidents**: severity (SEV1–SEV3), impact, root cause, linked tickets, duration
- **Knowledge base**: problem and solution articles with tags and search
- **REST API** with authentication and pagination, plus the Django admin for the support team
- **`/health/`** endpoint that checks the database, used by the Docker healthcheck
- **Database performance**: composite index for the support queue and a command that shows the query plan
- **Docker Compose** with PostgreSQL 16, **GitHub Actions** CI with lint, migration check, tests on PostgreSQL and image build

## Quick start (Docker)

```bash
cp .env.example .env          # then set DJANGO_SECRET_KEY and POSTGRES_PASSWORD
docker compose up -d --build
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py seed_demo --tickets 50000
curl localhost:8000/health/   # {"status": "ok", "database": "ok"}
```

- Admin: http://localhost:8000/admin/
- API: http://localhost:8000/api/

## Run without Docker

Without `POSTGRES_HOST` the app falls back to SQLite, so it runs with zero setup:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py createsuperuser
DJANGO_DEBUG=true python manage.py runserver
python manage.py test
```

## API

All endpoints require login (session or basic auth).

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/tickets/?status=open&priority=high` | support queue, newest first |
| GET | `/api/tickets/?q=checkout` | search by title or customer email |
| POST | `/api/tickets/` | create a ticket |
| POST | `/api/tickets/{id}/resolve/` | resolve a ticket |
| GET | `/api/incidents/?open=true` | ongoing incidents |
| POST | `/api/incidents/` | log an incident |
| GET | `/api/articles/?q=nginx` | search the knowledge base |
| GET | `/health/` | app and database health (no auth) |

```bash
curl -u admin:PASSWORD "localhost:8000/api/tickets/?status=open&priority=critical"
curl -u admin:PASSWORD -X POST localhost:8000/api/tickets/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Site returns 502", "customer_email": "client@example.com", "priority": "high"}'
```

## Database performance

The support queue runs one query all day: open tickets of a given priority, newest first.
A composite index `(status, priority, -created_at)` covers both the filter and the sort:

```bash
docker compose exec web python manage.py explain_queue
```

On 50,000 tickets PostgreSQL uses an index scan and returns the first page in well under a millisecond:

```
Limit  (actual time=0.033..0.049 rows=20 loops=1)
  ->  Index Scan using ticket_queue_idx on tickets_ticket
        Index Cond: ((status = 'open') AND (priority = 'high'))
Execution Time: 0.063 ms
```

## Troubleshooting runbook

| Symptom | Check |
| --- | --- |
| `/health/` returns 503 | `docker compose ps`, then `docker compose logs db`: is PostgreSQL healthy? |
| Web container restarts | `docker compose logs web`: usually a missing variable in `.env` or a failed migration |
| API returns 403 | the request is not authenticated |
| Queue is slow | `manage.py explain_queue`: the plan should show `ticket_queue_idx` |

## Project structure

```
config/                  settings, URLs, WSGI
tickets/models.py        Ticket, Incident, Article
tickets/views.py         API viewsets and the health check
tickets/management/      seed_demo and explain_queue commands
tickets/tests/           API tests
.github/workflows/ci.yml lint, tests on PostgreSQL, Docker build
```
