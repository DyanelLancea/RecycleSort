# RecycleSort — Recycling Gamification Web App

University module **INF2006**. A student uploads a photo of a waste item. A ResNet50 classifier labels it as battery, biological, cardboard, clothes, glass, metal, paper, plastic, shoes, or trash, the app states whether it is recyclable, and the user earns points for each upload.

## Problem statement

Campus bins are often contaminated because people cannot tell recyclable materials apart at the moment of disposal. RecycleSort turns that decision into a short, scored workflow so correct sorting is easier to practise.

## Team

Names and student IDs are in `project_manifest.yaml` and `TEAM_CONTRIBUTIONS.md`.

| Role                             | Area                                        |
| -------------------------------- | ------------------------------------------- |
| Happy Calista                    | Authentication and user management          |
| Balandra Dyanel Lancea Estillore | Image upload and input validation           |
| Chia Ting Hui Wileen             | ML classification and recyclable logic      |
| Felicia Seah Yun Xin             | Gamification, logging, and database         |
| Leong Jia En Melissa             | Frontend and AWS deployment                 |




## Quick start



### Backend (FastAPI)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r src/requirements.txt
cp src/.env.example src/.env
cd src && uvicorn app.main:app --reload --host 0.0.0.0 --port 43181
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

Deployed on **AWS IaaS**. The running stack is VPC `rs-vpc`, Application Load Balancer `rs-alb`, Auto Scaling group `rs-app-asg` (2–4 t3.medium instances), RDS PostgreSQL `rs-db`, Parameter Store SecureStrings, and S3 for the model file. The full service list is in `project_manifest.yaml`. The diagram is `evidence/architecture.png`.

## Tech stack

- Backend: Python, FastAPI, SQLAlchemy, JWT, bcrypt
- Frontend: React, TypeScript, Vite
- ML: ResNet50 inference in `src/app/ml/`; evaluation tooling in `analytics/`
- Data: Kaggle Garbage Classification V2 test images under `data/testing_images/`; `data/sample_scans.csv` is a synthetic baseline only
- Cloud: AWS VPC, EC2, ALB, Auto Scaling, RDS PostgreSQL, S3, Parameter Store, CloudWatch, SNS (see `project_manifest.yaml`)



## Repository layout

```
src/          Runnable app, configuration, dependencies
data/         Sample data and data dictionary
analytics/    ML reproduction scripts
evidence/     Dated test outputs and diagrams
tests/        Automated tests
```

See `project_manifest.yaml` for required metadata, evidence paths, and run commands.