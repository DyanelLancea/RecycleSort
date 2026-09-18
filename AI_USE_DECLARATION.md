# AI use declaration

## Tools used

- **Cursor agent (Grok 4.6)** — scaffolded the INF2006 repository from `cursor_setup_instructions.md`: directory layout, `project_manifest.yaml`, FastAPI stubs for the five developer roles, React frontend views, and this documentation set.

## Sources

- Module setup brief (uploaded `cursor_setup_instructions.md`).
- FastAPI, SQLAlchemy, PyJWT, bcrypt, React, and Vite public documentation as applied by the agent during scaffolding.

## What the AI produced

- Repository skeleton and mandatory metadata files.
- Runnable stubs (not a production classifier or a live AWS deployment):
  - registration/login with bcrypt + JWT
  - upload validation
  - mock ML inference
  - SQLite-backed points and scan logs
  - frontend screens for auth, upload, results, profile, info, and admin

## Verification required of the team

The team must independently:

- Replace empty names, student IDs, and `group_id` in `project_manifest.yaml`.
- Review authentication, upload limits, and secret handling before any AWS deployment.
- Train and evaluate a real model using `analytics/` and record metrics under `evidence/`.
- Add architecture diagrams, functional/security/resilience tests, and a threat-control map in `evidence/`.
- Confirm no real credentials are committed (use Parameter Store in AWS; local values stay in `.env`, which is gitignored).

## Attribution

Human teammates remain authors of the submitted coursework. AI output is a starting stub and must be reviewed, extended, and verified before it is treated as assessed work.
