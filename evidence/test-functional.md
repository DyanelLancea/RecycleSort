# Test 1: Functional workflow

- **Objective:** A new user can register, log in, scan an item and receive points through the live load balancer.
- **Setup:** `rs-alb` in front of `rs-app-asg` (2 x t3.medium, Amazon Linux 2023, AMI `rs-app-ami-v1`), `rs-db` RDS PostgreSQL in private subnets. Repository commit `<paste latest commit hash>`. Test image: `tests/samples/can.jpg` (aluminium can).
- **Command/steps:** Run from AWS CloudShell (outside the VPC) against the ALB DNS name:
  1. `POST /api/auth/register` with a new synthetic email (`tester<timestamp>@example.com`)
  2. `POST /api/auth/login` with the same credentials to get a JWT
  3. `POST /api/upload` with `tests/samples/can.jpg` and the JWT
  4. `GET /api/profile` with the JWT
  5. `GET /api/logs/me` with the JWT

  Full commands and output: `evidence/raw/test1-functional-output.txt`.
- **Expected result:** Register returns a user with 0 points; login returns a token; upload of a can returns `metal`, recyclable, 5 points; profile shows 5 points; the scan appears in `/api/logs/me`.
- **Actual result:** All 5 steps matched. Register created user id 3 with 0 points. Login returned a 193-character token. Upload returned `predicted_class: "metal"`, `confidence: 1.0`, `is_recyclable: true`, `points_awarded: 5`, `total_points: 5`, `model_loaded: true`. Profile showed 5 points. `/api/logs/me` returned scan id 4 (`metal`, 5 points). **Result: PASS.**
- **Date/time:** 2026-10-10 22:30 SGT (14:30 UTC)
- **Artefact path:** `evidence/raw/test1-functional-output.txt`
- **Interpretation:** The full user workflow works end to end through the load balancer, the auto-scaled app servers, the ResNet50 model and the RDS database. The access token was redacted from the saved output. Note: the confidence of 1.0 is on a clear, well-lit photo; it does not show how the model handles messy real-world photos (see `evidence/test-data-ai.md`).
