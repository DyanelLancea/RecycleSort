# Deployment record

All times are Singapore time (SGT, UTC+8) on 10–11 Oct 2026 unless marked UTC. Times before 22:00 are approximate (from the team's working notes). Resource names match the architecture diagram (`evidence/architecture.png`). Region: us-east-1. Account: AWS Academy Learner Lab.

## Timeline

| Time (SGT) | Phase | What was done | Problem found and fix |
| --- | --- | --- | --- |
| 10 Oct ~12:20 | Code | Pre-deployment fixes on branch `pre-aws-fixes` (commit `50f6813`): PostgreSQL driver and TensorFlow 2.18.0 added, `/health` returns 503 when the DB is down, tests added, docs aligned with the 10-class model, server config files added to `src/infra/` | – |
| ~12:30 | Code | PR #1 merged into `main` (commit `0ad07bb`). This is the code deployed in `rs-app-ami-v1` | – |
| ~12:40 | 0–1 | Learner Lab started; VPC `rs-vpc` (10.0.0.0/16) created with 2 public + 2 private subnets in us-east-1a/1b, internet gateway, S3 gateway endpoint, no NAT gateway | – |
| ~12:45 | 2 | Security groups `rs-alb-sg`, `rs-app-sg`, `rs-db-sg` created as a chain | – |
| ~12:50 | 3 | RDS database creation started | The Aurora engine was selected by mistake (it shows "cluster scalability type"); switched to plain RDS for PostgreSQL, single-AZ, micro instance, to match the code and the budget |
| ~13:00 | 3 | DB subnet group `rs-db-subnet-group` (2 private subnets); `rs-db` created: PostgreSQL, Public access No, encrypted, 1-day backups, initial database `recyclesort` | The subnet group was not listed in the RDS form until it was created and the VPC list refreshed |
| ~13:10 | 4 | S3 bucket created (Block Public Access on, versioning on, SSE-S3); `resnet50_final.keras` (about 225 MB) uploaded to `models/` | The model is in Git LFS, so a normal clone only contains a 134-byte placeholder; S3 is used to deliver the real file |
| ~13:15 | 5 | Parameter Store SecureStrings created under `/recyclesort/prod/`: `jwt_signing_key`, `admin_api_key`, `database_url_migrate` | – |
| ~13:25 | 6 | Build server `rs-build` launched (Amazon Linux 2023, t3.medium, 20 GiB encrypted gp3, LabInstanceProfile, no key pair); connected with Session Manager; temporary "My IP" rule added to `rs-app-sg` | – |
| ~13:40 | 6.4 | Software installed (Python 3.11, nginx, Node.js, PostgreSQL client); non-root user `recyclesort` created | Default Node.js was v18, too old for Vite 8; installed `nodejs22` and switched the default with `alternatives --config node` |
| ~13:45 | 6.5 | Code cloned with `GIT_LFS_SKIP_SMUDGE=1`; Python dependencies installed; model downloaded from S3; frontend built | – |
| ~13:50 | 6.6 | Alembic migrations created `users` and `scan_logs`; limited database user `rs_app` created; `/recyclesort/prod/database_url` added | First migration failed with `could not translate host name "<RDS endpoint>"`: the placeholder text had been saved in Parameter Store. Fixed by editing the parameter with the real endpoint and password |
| ~13:55 | 6.7–6.8 | `fetch-env.sh`, systemd unit and nginx config copied from `src/infra/`; services enabled | `curl http://localhost/health` returned nginx's default 404: Amazon Linux's sample server block answered on IPv6. Fixed by removing the default server block from `/etc/nginx/nginx.conf` (and adding `listen [::]:80` to our config) |
| ~13:58 | 6.8 | Health check `200 {"status":"ok","db":"connected"}` | – |
| ~14:00 | 6.9 | CloudWatch agent installed and configured | – |
| ~14:05 | 6.10 | Browser test: register, login and scan worked on `rs-build` | – |
| ~14:10 | 6.10 | `/etc/recyclesort.env` deleted and shell history cleared; AMI `rs-app-ami-v1` created; temporary security group rule removed | – |
| ~14:25 | 7.1–7.2 | Target group `rs-app-tg` (health check `/health`) and ALB `rs-alb` (2 public subnets, `rs-alb-sg`) created | The ALB form showed no target group to forward to; the target group was created first in the correct VPC and the list refreshed |
| ~14:35 | 7.3–7.4 | Launch template `rs-app-lt` (IMDSv2 required, detailed monitoring) and Auto Scaling group `rs-app-asg` created | First attempt failed: "Desired capacity 2 must be between min 1 and max 1". Fixed by setting min 2 / desired 2 / max 4 |
| ~14:45 | 7.5–7.6 | Site working through the ALB DNS name; 2 healthy targets in 2 AZs; `rs-build` terminated (its image lives on as the AMI) | – |
| ~14:50–15:05 | 8 | SNS topic `rs-alerts` with email subscription; alarms `rs-unhealthy-hosts`, `rs-target-5xx`, `rs-db-cpu-high` | `HTTPCode_Target_5XX_Count` could not be selected in the console because the metric did not exist yet; the alarm was created with the AWS CLI from CloudShell instead (`src/infra/create-alarms.sh`). A duplicate pending SNS subscription caused a harmless warning |
| ~15:15 | 8 | Dashboard `rs-dashboard` with 6 widgets | 5xx metrics were not available yet (no errors had occurred) |
| ~15:25 | 8 | Logs Insights query for uploads per 5 minutes run on `/recyclesort/nginx-access` | First run included all log groups and double-counted; scope limited to the nginx log group |
| ~15:35 | 9 | Paused to save credit: ASG set to 0/0/4, `rs-db` stopped, lab ended | – |
| ~22:10 | 9 | Resumed: lab started, `rs-db` started, ASG set back to 2/2/4 | Targets stayed "initial" for several minutes until the database was available, then turned healthy |
| 22:30 | Test 1 | Functional workflow test (PASS) | – |
| 22:43 | Test 2 | Security controls test (PASS) | Rate limiter blocked at attempt 10, not 6, because each of the 2 servers counts separately (documented as a finding) |
| 22:59 | Test 3 | Live AI validation, 10/10 correct (PASS) | First request on one server took 10.8 s while the model loaded (cold start) |
| 23:06 | Test 4A | Server terminated; 593/600 health checks OK; replacement launched automatically (PASS) | – |
| 23:27–01:01 | Test 4B | Load test 9,674 requests; scaled 2 → 4 → 2 (PASS) | The target-group page in the console showed stale counts; the AWS CLI confirmed 4 healthy targets |
| 01:11-01:23 | Export | AWS configuration exported to `evidence/config/` | – |
| 01:45 | 9 | Paused again: ASG to 0, `rs-db` stopped, lab ended | – |
| 11 Oct ~17:00 | Redeploy | Learner Lab resumed; `rs-db` started; ASG set back to 2/2/4 (v1 servers) | – |
| ~17:10 | Redeploy | Build server `rs-build-v2` launched from `rs-app-ami-v1`; `git pull` to commit `08831a0`; frontend rebuilt; `/health` OK; `/etc/recyclesort.env` removed; AMI `rs-app-ami-v2` created; build server terminated | `sudo -iu recyclesort` failed (service account has no login shell), and git reported "dubious ownership" because the code is owned by root; commands were run with `sudo` and `-c safe.directory=/opt/recyclesort` |
| ~17:20 | Redeploy | Launch template `rs-app-lt` version 2 (AMI `rs-app-ami-v2`) set as default | Instance refresh is blocked by the Learner Lab service control policy (changing the termination policy was also refused); instead desired capacity was raised to 4 and then lowered to 2, and the default termination policy removed the two v1 servers (confirmed in `evidence/raw/v2-deploy-check.txt`) |
| 17:38 | Check | 2 servers InService on `rs-app-ami-v2`, both healthy (`evidence/raw/v2-deploy-check.txt`) | – |
| 17:38 | Test 1 re-run | Functional workflow on v2: PASS (`evidence/raw/test1-functional-output-v2.txt`) | – |

## Lessons learned

1. **Placeholders are dangerous.** A copied example value (`<RDS endpoint>`) broke the first migration. Values are now checked with `aws ssm get-parameter` before use.
2. **Big model files need their own delivery path.** Git LFS placeholders look like real files. Storing the model in S3 made every new server identical and fast to build.
3. **Bake once, launch many.** Building one server by hand and saving it as an AMI meant every Auto Scaling instance came up working, without manual steps.
4. **Start dependencies in order.** App servers must start after the database is available, or they fail their health checks and get replaced.
