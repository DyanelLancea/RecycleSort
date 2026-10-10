# Threat-control map

Threats are taken from the Cloud Security Alliance "Notorious Nine" (Lecture 5). Every control was tested on 10 Oct 2026 (Test 2, `evidence/test-security.md`) or is shown in an exported configuration file (`evidence/config/`).

| # | Threat | Where | Control | Evidence | Tested result |
| --- | --- | --- | --- | --- | --- |
| 1 | Data breach | Database `rs-db` | RDS in private subnets with no route to the internet, Public access = No, `rs-db-sg` only allows PostgreSQL 5432 from `rs-app-sg` | `config/rds.json`, `config/security-groups.json`, Test 2e | Connection from outside the VPC BLOCKED |
| 2 | Data breach (data at rest) | RDS, EBS, S3, Parameter Store | Encryption with AWS KMS: RDS storage encrypted, EBS volumes encrypted, S3 default SSE-S3, secrets stored as SecureString | `config/rds.json` (Encrypted: true), `config/ami.json` (DiskEncrypted: true), `config/s3-encryption.json` (AES256), `config/ssm-parameter-names.json` (all SecureString) | All four confirmed encrypted in the exports (11 Oct 2026) |
| 3 | Data breach (data in transit) | App → database | Database URL uses `sslmode=require`, so the connection is TLS-encrypted | Parameter format in Phase 5 / 6.6 of the deployment record (value not shown) | App connects only with TLS |
| 4 | Data loss | Database | Automated daily RDS backups (1 day retention); app servers are stateless, so losing one loses no data | `config/rds.json` (BackupDays: 1), Test 4A | A server was terminated with no data loss |
| 5 | Account or service hijacking | Login | bcrypt password hashes, password policy (8+ chars, upper, lower, digit), login rate limit (5 per minute per server), equal-time check for unknown emails, JWT with pinned HS256 and required expiry | `src/app/auth/`, Test 2c | 401 for tries 1–9, 429 from try 10 |
| 6 | Insecure interfaces and APIs | `/api/upload`, `/api/profile`, `/api/logs/me` | JWT bearer token required | Test 2a | 401 without a token |
| 7 | Insecure interfaces and APIs | `/api/admin/*` | `X-Admin-Key` header compared with a secret from Parameter Store | Test 2d | 403 without the key |
| 8 | Malicious upload | `/api/upload` | File-type allow-list (JPEG/PNG/WebP), 5 MB limit, Pillow image verification, nginx 6 MB body limit | `src/app/upload/validation.py`, `src/infra/nginx-recyclesort.conf`, Test 2b | 400 "Corrupted or unreadable image" |
| 9 | Denial of service | Whole service | ALB spreads load; Auto Scaling 2–4 servers on CPU 60%; health checks replace failed servers | `config/asg.json`, `config/asg-policy.json`, Test 4 | Scaled 2 → 4 under 9,674 requests at 99.79% success |
| 10 | Bypassing the load balancer | App servers | `rs-app-sg` only accepts HTTP 80 from `rs-alb-sg`; no other inbound rule | `config/security-groups.json`, Test 2f | Direct request to a server's public IP timed out |
| 11 | Malicious insiders / misuse of credentials | Database | App connects as `rs_app` with only SELECT/INSERT/UPDATE on 2 tables; master user `rsadmin` used only for migrations | Deployment record, Phase 6.6 | App user cannot drop or alter tables |
| 12 | Leaked secrets | Code, images, evidence | All secrets in Parameter Store (SecureString); `.env` is git-ignored; secret file deleted before creating the AMI; tokens, account IDs and endpoints redacted from evidence | `config/ssm-parameter-names.json`, Test 2g | No secrets found in the repository |
| 13 | Server takeover | EC2 | No SSH port open (admin access through Session Manager only), IMDSv2 required, app runs as non-root user `recyclesort`, IAM instance profile instead of stored access keys | `config/launch-template.json` (HttpTokens: required), `config/security-groups.json`, `src/infra/recyclesort.service` | IMDSv2 required and no SSH rule confirmed in the exports |
| 14 | Abuse of cloud services / insufficient due diligence | AWS account | Least-privilege IAM policy written for the app (`src/infra/iam-least-privilege-policy.json`); monitoring and alerts on abnormal load | `evidence/monitoring.md` | See limitation below |

## Known limitations (honest gaps)

- **No HTTPS.** The Learner Lab has no domain or certificate, so the ALB listens on HTTP only and passwords and tokens are not encrypted between the browser and AWS. Production fix: an AWS Certificate Manager certificate, an HTTPS listener, and redirect from 80 to 443.
- **Broad IAM role.** The Learner Lab does not allow custom IAM roles, so servers use `LabRole`. The least-privilege policy the app actually needs is documented in `src/infra/iam-least-privilege-policy.json`.
- **Rate limit per server.** The login limiter keeps counts in each server's memory, so the effective limit grows with the number of servers (Test 2c). Production fix: a shared counter (ElastiCache Redis) or an AWS WAF rate-based rule.
- **No WAF or DDoS protection beyond AWS Shield Standard.** Production fix: AWS WAF managed rules in front of the ALB.