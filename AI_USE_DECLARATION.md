# AI use declaration

## Tools used

- **Cursor agent (Grok 4.6)**: scaffolded the INF2006 repository from `cursor_setup_instructions.md`: directory layout, `project_manifest.yaml`, FastAPI stubs for the five developer roles, React frontend views, and this documentation set.
- **Claude (Anthropic)**: AWS hosting timeline plan, report and codebase review and suggestion. 

## Sources

- Module setup brief (uploaded `cursor_setup_instructions.md`).
- FastAPI, SQLAlchemy, PyJWT, bcrypt, React, and Vite public documentation as applied by the agent during scaffolding.

## What the AI produced

The AI wrote the first skeleton only. The list below is that first draft, not the finished app. The team replaced or extended every item.

- Folder layout, `project_manifest.yaml`, and the first documentation files.
- A first draft of register and login (bcrypt and JWT).
- A first draft of upload checks.
- A fake classifier. The team replaced it with the trained ResNet50 model.
- Points and scan logs saved in a local SQLite file. The deployed app uses RDS PostgreSQL instead.
- The first React pages for login, upload, results, profile, info, and admin.

## What the team added after the scaffold

- A 10-class ResNet50 model, evaluation in `analytics/`, and `evidence/test-data-ai.md`.
- Auth hardening, Alembic migrations, and upload checks beyond the stub.
- The AWS deployment (VPC, EC2, ALB, Auto Scaling, RDS PostgreSQL, S3, Parameter Store, CloudWatch, SNS) and the evidence pack under `evidence/`.
- Production secrets in Parameter Store SecureStrings. Local development still uses `src/.env`, which is gitignored.

## Attribution

Human teammates remain authors of the submitted coursework. The AI output was a starting stub. The deployed classifier, cloud stack, and test evidence were produced and checked by the team.
