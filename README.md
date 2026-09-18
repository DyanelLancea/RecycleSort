# RecycleSort — Recycling Gamification Web App

University module **INF2006**. Users photograph a waste item, a classifier labels it as paper, plastic, or metal, the app states whether it is recyclable, and the user earns points for each scan.

## Problem statement

Campus bins are often contaminated because people cannot tell recyclable materials apart at the moment of disposal. RecycleSort turns that decision into a short, scored workflow so correct sorting is easier to practise.

## Team

Fill names and student IDs in `project_manifest.yaml` and `TEAM_CONTRIBUTIONS.md`. Roles:

| Role | Area |
| --- | --- |
| Developer 1 | Authentication and user management |
| Developer 2 | Image upload and input validation |
| Developer 3 | ML classification and recyclable logic |
| Developer 4 | Gamification, logging, and database |
| Developer 5 | Frontend |

## Quick start

### Backend (FastAPI)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r src/requirements.txt
cp src/.env.example src/.env
cd src
uvicorn app.main:app --reload --host 0.0.0.0 --port 43181
```

Health check for a load balancer: `GET http://127.0.0.1:43181/health`

### Frontend (React + Vite)

```bash
cd src/frontend
npm install
npm run dev -- --host 0.0.0.0 --port 43180
```

Open the Vite URL. API calls to `/api` and `/health` are proxied to the FastAPI process.

Local admin dashboard access uses `SSM_ADMIN_API_KEY` from `src/.env` (default in `.env.example`: `dev-admin-api-key-not-for-production`).

## Architecture

Target deployment is **AWS IaaS**: EC2 behind an Application Load Balancer, Auto Scaling, RDS (or DynamoDB), and secrets in **AWS Systems Manager Parameter Store**. Place the diagram at `evidence/architecture.png` (path declared in `project_manifest.yaml`).

## Tech stack

- Backend: Python, FastAPI, SQLAlchemy, JWT, bcrypt
- Frontend: React, TypeScript, Vite
- ML (current slice): mocked inference in `src/app/ml/`; training notes in `analytics/`
- Data: synthetic samples under `data/`
- Cloud (planned): AWS EC2, ELB, Auto Scaling, RDS/DynamoDB, Parameter Store

## Repository layout

```
src/          Runnable app, configuration, dependencies
data/         Sample data and data dictionary
analytics/    ML reproduction scripts
evidence/     Dated test outputs and diagrams
tests/        Automated tests
```

See `project_manifest.yaml` for required metadata, evidence paths, and run commands.
